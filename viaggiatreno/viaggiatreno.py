#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import datetime, random
import logging


# PROXY SETTINGS
# If you need to use a (or many) proxy, just set USE_PROXY as True and add the 
# proxy IP address and port in the 'proxy_addresses' list. 
# If you add more than one IP address, random IP rotation will automatically be used
USE_PROXY = False
proxy_addresses = [ ]


base_url = "http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/"
partenze_url = "partenze/{}/{}"
arrivi_url = "arrivi/{}/{}"
treno_url = "andamentoTreno/{}/{}"
cercaNumeroTreno_url = "cercaNumeroTreno/{}"


class ViaggiaTreno:
    """Classe wrapper per il consumo delle API Viaggiatreno"""

    _logger = logging.getLogger("ViaggiaTreno")

    @staticmethod
    def __get_proxy_settings():
        if USE_PROXY == False or len(proxy_addresses) == 0:
            return None

        # handle IP rotation (select a random proxy address)
        proxy_index = random.randint(0, len(proxy_addresses) - 1)

        return { "http": proxy_addresses(proxy_index), "https": proxy_addresses(proxy_index) }


    @staticmethod
    def __handle_invalid_response(response, num_treno, fail_if_204=True, do_if_204=None):
        if response.status_code == 204:
            if fail_if_204:
                error_string = "Non è stato trovato un treno con numero {} (HTTP Status {})".format(num_treno, response.status_code)
                ViaggiaTreno._logger.error(error_string)
                raise ValueError(error_string)
            else:
                return do_if_204(num_treno)
        elif response.status_code == 403:
            error_string = "API blocked (HTTP status 403). Treno {}".format(num_treno)
            ViaggiaTreno._logger.error(error_string)
            raise Exception(error_string)
        else:
            error_string = "HTTP status {} - Treno {}".format(response.status_code, num_treno)
            ViaggiaTreno._logger.error(error_string)
            raise Exception(error_string)
        

    @staticmethod
    def _cerca_id_origine(num_treno):
        """Restituisce il codice origine in base al numero del treno"""
        response = requests.get(base_url + cercaNumeroTreno_url.format(num_treno),
                                proxies=ViaggiaTreno.__get_proxy_settings())

        if response.status_code != 200:
            ViaggiaTreno.__handle_invalid_response(response, num_treno)

        return response.json()['codLocOrig']


    @staticmethod
    def cerca_treno(num_treno, id_origine=None):
        """Restituisce tutte le informazioni di un treno"""
        if id_origine == None:
            id_origine = ViaggiaTreno._cerca_id_origine(num_treno)

        response = requests.get(base_url + treno_url.format(id_origine, num_treno),
                                proxies=ViaggiaTreno.__get_proxy_settings())

        if response.status_code != 200:
            ViaggiaTreno._logger.debug(
                "Treno {} non trovato, provo a cercare l'origine del treno (forse è sbagliata)".format(num_treno))

            # Se non viene trovato il treno (status 204), provo a cercare l'origine del treno (forse è sbagliata)
            # quindi ricerco il treno con la nuova origine
            # se invece la response ha un altro status code allora fallisco
            def cerca_origine_e_treno(num_treno):
                id_origine = ViaggiaTreno._cerca_id_origine(num_treno)
                return requests.get(base_url + treno_url.format(id_origine, num_treno),
                                    proxies=ViaggiaTreno.__get_proxy_settings())

            response = ViaggiaTreno.__handle_invalid_response(response, num_treno,
                                                              fail_if_204=False,
                                                              do_if_204=cerca_origine_e_treno)

            # se ancora non si trova allora fallisco
            if response is not None and response.status_code != 200:
                ViaggiaTreno.__handle_invalid_response(response, num_treno)
        
        treno = response.json()

        dati = {
                'categoria': treno['categoria'],
                'numero': treno['numeroTreno'],
                'origine': treno['origine'],
                'destinazione': treno['destinazione'],
                'id_origine': treno['idOrigine'],
                'id_destinazione': treno['idDestinazione'],
                'ritardo': treno['ritardo'],
                'orario_partenza': treno['compOrarioPartenza'],
                'orario_partenza_effettivo': treno['compOrarioPartenzaZeroEffettivo']
            }

        return Treno(id_origine, num_treno, dati)

    
    @staticmethod
    def partenze_stazione(stazione, data=datetime.datetime.now()):
        """Restituisce la lista dei treni in partenza da una determinata stazione in un determinato orario (default: now) come oggetti della classe Treno"""
        
        response = requests.get(base_url + partenze_url.format(stazione, data.strftime("%a %b %-d %Y %H:%M")),
                                proxies=ViaggiaTreno.__get_proxy_settings())
        treni = response.json()

        treni_list = []
        for treno in treni:
            try:
                treni_list.append(ViaggiaTreno.cerca_treno(treno['numeroTreno'], treno['codOrigine']))
            except ValueError:
                # Se ci sono problemi con qualche treno non mi interessa. Lo ignoro e continuo con gli altri
                continue
            except Exception:
                # ci sono problemi con l'API (al 99% è errore 403 e serve un proxy)
                continue

        return treni_list


    @staticmethod
    def arrivi_stazione(stazione, data=datetime.datetime.now()):
        """Restituisce la lista dei treni in arrivo in una determinata stazione in un determinato orario (default: now) come oggetti della classe Treno"""
        response = requests.get(base_url + arrivi_url.format(stazione, data.strftime("%a %b %-d %Y %H:%M")),
                                proxies=ViaggiaTreno.__get_proxy_settings())
        treni = response.json()

        treni_list = []
        for treno in treni:
            try:
                treni_list.append(ViaggiaTreno.cerca_treno(treno['numeroTreno'], treno['codOrigine']))
            except ValueError:
                # Se ci sono problemi con qualche treno non mi interessa. Lo ignoro e continuo con gli altri
                continue
            except Exception:
                # ci sono problemi con l'API (al 99% è errore 403 e serve un proxy)
                continue

        return treni_list

    
    
    @staticmethod
    def numeri_partenze_stazione(stazione, data=datetime.datetime.now()):
        """Restituisce la lista dei treni in partenza da una determinata stazione in un determinato orario (default: now) sotto forma di oggetto Python"""
        response = requests.get(base_url + partenze_url.format(stazione, data.strftime("%a %b %-d %Y %H:%M")),
                                proxies=ViaggiaTreno.__get_proxy_settings())
        
        if response.status_code != 200:
            error_string = "HTTP status {} - Stazione {}".format(response.status_code, stazione)
            ViaggiaTreno._logger.error(error_string)
            raise Exception(error_string)

        treni = response.json()

        treni_list = []
        for treno in treni:
            treni_list.append({
                "categoria": treno['categoria'],
                "numero": treno['numeroTreno'],
                "id_origine": treno['codOrigine'],
                "origine": treno['origine'],
                "destinazione": treno['destinazione'],
                "ritardo": treno['ritardo'],
                "stazione_rilevamento": stazione,
                'codice_cliente': treno['codiceCliente']
                })
        
        return treni_list


    
    @staticmethod
    def numeri_arrivi_stazione(stazione, data=datetime.datetime.now()):
        """Restituisce la lista dei treni in arrivo in una determinata stazione in un determinato orario (default: now) sotto forma di oggetto Python"""        
        response = requests.get(base_url + arrivi_url.format(stazione, data.strftime("%a %b %-d %Y %H:%M")),
                                proxies=ViaggiaTreno.__get_proxy_settings())
        
        if response.status_code != 200:
            raise Exception("HTTP status {} - Stazione {}".format(response.status_code, stazione))

        treni = response.json()

        treni_list = []
        for treno in treni:
            treni_list.append({
                "categoria": treno['categoria'],
                "numero": treno['numeroTreno'],
                "id_origine": treno['codOrigine'],
                "origine": treno['origine'],
                "destinazione": treno['destinazione'],
                "ritardo": treno['ritardo'],
                "stazione_rilevamento": stazione,
                'codice_cliente': treno['codiceCliente']
                })
        
        return treni_list


class Treno:
    def __init__(self, id_origine, numero, dati):
        self.numero = numero
        self.id_origine = id_origine

        self.categoria = dati['categoria']
        self.origine = dati['origine']
        self.destinazione = dati['destinazione']
        self.id_destinazione = dati['id_destinazione']
        self.ritardo = dati['ritardo']


    def aggiorna(self):
        t = ViaggiaTreno.cerca_treno(self.id_origine, self.numero)

        self.ritardo = t['ritardo']