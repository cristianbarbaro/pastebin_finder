import argparse
import requester
from finder_utils import config
from finder_utils import database
from finder_utils import send_email
from datetime import datetime
import json
import sys 
import time
import hashlib
import logging
from pprint import pprint


class Finder():

    def __init__(self, query, site, email, api, csv, json):
        self.cx_id = config.CX_ID
        self.db_file = config.DB
        self.api_key = config.API_KEY
        self.query = query
        self.site = site
        self.email = email
        self.api = api
        self.csv = csv
        self.json = json
        self.cse_tok, self.cselibv = requester.get_parameters_web("http://cse.google.com/cse.js?hpg=1&cx=" + self.cx_id)
        self.results_json = {
                "query": query,
                "site": site,
                "results": []
            }   

        self.conn  = database.create_connection(config.DB)
        self.query_id = self.__check_query()
        self.query_site, self.site_id = self.__check_site()

        logging.basicConfig(format='%(asctime)s: %(message)s',filename=config.LOGFILE,level=logging.DEBUG)


    def __check_query(self):
        # Se verifica si existe la base de datos para agregar el nuevo query si corresponde.
        query_obj = database.check_exists_query(self.conn, self.query)

        if not query_obj:
            query_id = database.insert_query(self.conn, self.query)
        else:
            query_id = query_obj[0][0]

        return query_id


    def __check_site(self):
        # Si se ingresa un sitio, tengo verificar si existe en la base de datos para agregarlo y concatenar con la búsqueda para que solo devuelva resultados de dicho sitio.
        query_site = "\"{0}\"".format(self.query)
        site_id = ""
        if self.site:
            query_site = query_site + " site:" + self.site

            site_obj = database.check_exists_site(self.conn, self.site)

            if not site_obj:
                site_id = database.insert_site(self.conn, self.site)
            else:
                site_id = site_obj[0][0]

        return (query_site, site_id)


    def __sendemail(self, title, link, body_text):
        if self.email:
            msg = """Se ha detectado un nuevo resultado para {0}.\n
Título: {1}.
Enlace: {2}.
Mensaje: {3}
            """.format(self.query, title, link, body_text)
            subject = "Se ha detectado un nuevo resultado para {0} en el sitio {1}".format(self.query, self.site)
            send_email.send_email(msg, subject)
            logging.info("Enviando correo electrónico.")


    def __write_to_csv(self, title, link, body_text):
        if self.csv:
            csv_file = open(self.csv, "a+")
            csv_file.write("\"{0}\",\"{1}\",\"{2}\"\n".format(title,link,body_text))
            logging.info("Escribiendo datos a archivo CSV.")
            csv_file.close()


    def __write_to_json(self):
        if self.json:
            with open(self.json, "w") as f:
                logging.info("Escribiendo datos a archivo JSON.")
                json.dump(self.results_json, f)


    def check_result(self, result, api=False):
        
        if api:
            title = result["title"]
            link = result["link"]
            body_text = result["snippet"]
        else:
            title = result["title"]
            link = result["url"]
            body_text = result["contentNoFormatting"]
        body_hash = title + body_text 
        body_hash = hashlib.sha256(body_hash.encode()).hexdigest()
        create_date = datetime.now()
        found = (title, self.query_id, self.site_id, link, body_text, body_hash, create_date)

        logging.debug("Found: " + str(found))

        self.__write_to_csv(title, link, body_text)

        if not database.check_exists_found(self.conn, body_hash):
            logging.info("Se ha detectado un nuevo resultado. Se inserta en la base de datos.")
            database.insert_found(self.conn, found)
            self.__sendemail(title, link, body_text)

        # Retorno el Json para todos los resultados obtenidos
        self.results_json["results"].append({
            "title": title,
            "body": body_text,
            "link": link
        })

        return self.results_json


    def get_results(self):

        if self.csv:
            csv_file = open(self.csv, "w+")
            csv_file.write("TITLE,LINK,TEXT\n")
            csv_file.close()

        with self.conn:
            try:
                if args.api:
                    flag = True
                    results = requester.get_results_api("1", self.api_key, self.cx_id, self.query_site)
                    while flag:
                        for result in results["items"]:
                            self.check_result(result, True)
                            time.sleep(1)
                        if "nextPage" in results["queries"]:
                            start_index = results["queries"]["nextPage"][0]["startIndex"]
                            results = requester.get_results_api(start_index, self.api_key, self.cx_id, self.query)
                        else:
                            flag = False                  
                else:
                    results =  requester.get_results_web(0, self.cselibv, self.cx_id, self.query_site, self.cse_tok)
                    pages = results["cursor"]["pages"]
                    for page in pages:
                        start_index = page["start"]
                        results = requester.get_results_web(start_index, self.cselibv, self.cx_id, self.query_site, self.cse_tok)
                        if "results" in results:
                            for result in results["results"]:
                                self.check_result(result)
                                time.sleep(1)
            
            except Exception as e:
                logging.warning("Ha ocurrido un error: " + str(e))

            self.__write_to_json()

        return self.results_json


if __name__ == "__main__":

    # OPCIONES DE MENÚ
    parser = argparse.ArgumentParser(description='Este script busca en el sitio que se ingresa como argumento. Debe configurarse en el CSE de Google.')
    parser.add_argument("-q", "--query", help="Consulta que se quiere hacer.", required=True)
    parser.add_argument("--site",
                            help="Sitio sobre el cual se desea buscar. Debe estar configurado en CSE.")
    parser.add_argument("--email", type=bool, nargs='?',
                            const=True, default=False,
                            help="Permite enviar emails. Debe configurarse los destinatarios en recipients.txt.")
    parser.add_argument("--api", type=bool, nargs='?',
                            const=True, default=False,
                            help="Las operaciones se realizan mediante la API de Google. Es necesario contar con una API KEY de una app de Google.")
    parser.add_argument("--csv",
                            help="Nombre del archivo csv donde se guardan los resultados.")
    parser.add_argument("--json",
                            help="Nombre del archivo json donde se guardan los resultados.")


    args = parser.parse_args()

    finder = Finder(args.query, args.site, args.email, args.api, args.csv, args.json)

    pprint(finder.get_results())
