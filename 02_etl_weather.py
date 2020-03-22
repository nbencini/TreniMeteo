#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from config import mysql_engine


max_data = mysql_engine.execute("SELECT MAX(data_ora) FROM rilevazioni_sensori").first()[0]

meteo = pd.read_csv("http://www.dati.lombardia.it/api/views/647i-nhxk/rows.csv?accessType=DOWNLOAD")
sensori = pd.read_sql_query("SELECT id FROM sensori", con=mysql_engine)

sensori.rename(columns={"id": "IdSensore"}, inplace=True)

# elimino i sensori che non misurano la pioggia e tolgo le colonne che non mi servono
meteo.drop(meteo[meteo['idOperatore'] != 4].index, inplace=True)
meteo.drop(columns=["idOperatore", "Stato"], inplace=True)

# tengo solo i sensori che mi interessano
meteo = meteo[meteo["IdSensore"].isin(sensori["IdSensore"])]

# converto le date in datetime
meteo["Data"] = pd.to_datetime(meteo["Data"], format="%d/%m/%Y %I:%M:%S %p")
meteo.rename(columns={"IdSensore":"id_sensore", "Data":"data_ora", "Valore":"valore"}, inplace=True)

meteo = meteo[meteo["data_ora"] > max_data]

meteo.to_sql("rilevazioni_sensori", con=mysql_engine, if_exists="append", index=False)