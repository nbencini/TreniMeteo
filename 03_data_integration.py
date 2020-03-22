#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pandas as pd
from pandas.io.json import json_normalize

from config import mongo, mysql_engine

from pandasql import sqldf
pysqldf = lambda q: sqldf(q, globals())


#   TRENI
query = "SELECT ritardi_medi.data_ora, " \
            "ROUND(AVG(ritardi_medi.rit), 2) AS ritardo_medio, " \
            "SUM(ritardi_medi.rit) AS somma_ritardi, " \
            "COUNT(ritardi_medi.numero) AS num_treni " \
        "FROM (SELECT date_format(treni_stazioni.data_rilevazione,'%Y-%m-%d %H:00') AS data_ora, " \
                    "treni_stazioni.numero, " \
                    "ROUND(AVG(treni_stazioni.ritardo)) AS rit " \
                "FROM treni_stazioni " \
                "GROUP BY data_ora, treni_stazioni.numero " \
                "ORDER BY NULL) AS ritardi_medi " \
        "GROUP BY ritardi_medi.data_ora " \
        "ORDER BY NULL;"
treni = pd.read_sql_query(query, con=mysql_engine)
treni["data_ora"] = pd.to_datetime(treni['data_ora'], format='%Y-%m-%d %H:%M')
treni["data_ora"] = treni['data_ora'].apply(lambda x: x+timedelta(hours=1))


#   TWEETS
tweets_db = mongo.tweets_db
tweets_collection = tweets_db.tweets

pipeline = [{ "$project": {
                    "y": { "$year": "$created_at" },
                    "m": { "$month": "$created_at" },
                    "d": { "$dayOfMonth": "$created_at" },
                    "h": { "$hour": "$created_at" },
                    "disagio": 1 }},
            { "$group": {
                    "_id": { "year": "$y", "month": "$m", "day": "$d", "hour": "$h" },
                    "somma_disagio": { "$sum": "$disagio" },
                    "media_disagio": { "$avg": "$disagio" },
                    "num_tweets": { "$sum": 1 }}}]

tweets = tweets_collection.aggregate(pipeline)
tweets = pd.DataFrame(json_normalize(list(tweets)))
tweets['data_ora'] = ""

for index, row in tweets.iterrows():
    tweets.loc[index, 'data_ora'] = datetime.strptime(str(row["_id.year"]) + '-' +
                                                      str(row['_id.month']) + '-' +
                                                      str(row['_id.day']) + ' ' +
                                                      str(row['_id.hour']),
                                                      '%Y-%m-%d %H')
tweets['data_ora'] = pd.to_datetime(tweets['data_ora'])
tweets.drop(columns=["_id.year", "_id.month", "_id.day", "_id.hour"], inplace=True)

# arrotondo la media disagio a 2 decimali
tweets['media_disagio'] = tweets['media_disagio'].apply(lambda x: round(x, 2))


#   METEO
query = "SELECT DATE_FORMAT(data_ora,'%Y-%m-%d %H:00') AS data_ora, " \
            "id_sensore, " \
            "SUM(valore) as mm_pioggia, " \
            "provincia " \
        "FROM rilevazioni_sensori " \
        "JOIN sensori ON sensori.id = rilevazioni_sensori.id_sensore " \
        "GROUP BY data_ora, id_sensore;"
meteo = pd.read_sql_query(query, con=mysql_engine)
meteo["data_ora"] = pd.to_datetime(meteo["data_ora"], format="%Y-%m-%d %H:%M")

# IdSensore deve essere trattato come stringa e non come numero intero
meteo = meteo.astype({"id_sensore": str})

# media semplice (non pesata)
meteo = pysqldf("""SELECT data_ora, ROUND(AVG(mm_pioggia), 1) AS mm_pioggia FROM meteo GROUP BY data_ora""")
meteo["data_ora"] = pd.to_datetime(meteo["data_ora"], format="%Y-%m-%d %H:%M")


#   DATA INTEGRATION
dati = pd.merge(treni, tweets[['data_ora', 'somma_disagio','media_disagio', 'num_tweets']], on='data_ora', how='left')
giorni = dati["data_ora"].apply(lambda x: x.date()).unique()
dati['num_tweets'].fillna(0, inplace=True)

dati['somma_disagio'].fillna(0, inplace=True)
dati['media_disagio'].fillna(0, inplace=True)

dati = dati.astype({"num_tweets": int})

# join con dati meteo
dati = pd.merge(dati, meteo[["data_ora", "mm_pioggia"]], on="data_ora", how="left")


# salvo il dataset integrato in un csv (per tableau)
dati.to_csv("/mnt/volume_fra1_01/dati_integrati.csv")