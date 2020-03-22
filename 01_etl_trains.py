#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime
import pandas as pd
import logging

from viaggiatreno.viaggiatreno import ViaggiaTreno
from config import mysql_engine

time = datetime.datetime.now()

logging.basicConfig(level=logging.INFO)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
logging.getLogger("ViaggiaTreno").setLevel(logging.INFO)

logger = logging.getLogger("numeri_treni")
logger.setLevel(logging.INFO)

logger.info("*** START at {}".format(time.strftime("%a %d/%m/%y, %H:%M:%S")))


# Read from source table
stazioni = pd.read_sql_query("SELECT id, nome FROM stazioni_lombardia, stazioni_api WHERE id=id_stazione", con=mysql_engine)

treni = []

for index, stazione in stazioni.iterrows():
    logger.debug("{} - PARTENZE - {}".format(stazione['nome'], datetime.datetime.now().strftime("%a %d/%m/%y, %H:%M:%S")))
    partenze = ViaggiaTreno.numeri_partenze_stazione(stazione['id'])
    logger.debug("{} - ARRIVI - {}".format(stazione['nome'], datetime.datetime.now().strftime("%a %d/%m/%y, %H:%M:%S")))
    arrivi = ViaggiaTreno.numeri_arrivi_stazione(stazione['id'])

    treni.extend(partenze)
    treni.extend(arrivi)


treni = pd.DataFrame(treni)
treni.drop_duplicates(inplace=True)
treni.sort_values("numero", inplace=True) # ordino per numero treno
treni.set_index("numero", inplace=True)
treni.drop(columns=["stazione_rilevamento", "categoria", "origine", "destinazione"], inplace=True)
treni.drop(treni[treni.codice_cliente != 63].index, inplace=True) # tolgo i treni non-trenord
treni.drop(columns='codice_cliente', inplace=True) # codice_cliente non mi serve più


# aggrego le righe unendo in una sola riga i dati di origine e destinazione se disponibili
def replace_nan_func(x):
    x = x[~pd.isnull(x)]
    if len(x) > 0:
        return x.iloc[0]
    else:
        return None


treni = treni.groupby(by='numero').agg(dict.fromkeys(treni.columns[0:], replace_nan_func))

treni['data_rilevazione'] = time

# Write to target table
treni.to_sql("treni_stazioni", con=mysql_engine, if_exists="append")

time_end = datetime.datetime.now()
logger.info("*** END at {}. Elapsed: {}".format(time_end.strftime("%a %d/%m/%y, %H:%M:%S"), time_end-time))