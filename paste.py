import argparse
import requester
from paste_utils import config
from paste_utils import database
from paste_utils import send_email
from datetime import datetime
import json
import sys 
import time
import hashlib


def check_results(r_json, results_json,api=False):
    
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
    paste = (title, query_id, site_id, link, body_text, body_hash, create_date)

    print(paste)
    # Retorno el Json para todos los resultados obtenidos (sin tener en cuenta si hay alguno nuevo)
    if args.json:
        results_json["results"].append({
            "title": title,
            "body": body_text,
            "link": link
        })

    # Escribimos a un csv
    if args.csv:
        pass

    if not database.check_exists_paste(conn, body_hash):
        print("Se ha detectado un nuevo resultado. Se insertará en la base de datos.")
        database.insert_paste(conn, paste)

        if args.email:
            msg = """Se ha detectado un nuevo Pastebin para {0}.\n
Título: {1}.
Enlace: {2}.
Mensaje: {3}
            """.format(query, title, link, body_text)
            subject = "Se ha detectado un nuevo resultado para {0} en el sitio {1}".format(query, site)
            send_email.send_email(msg, subject)

    return results_json


if __name__ == "__main__":

    cx_id = config.CX_ID
    db_file = config.DB
    api_key = config.API_KEY


    # OPCIONES DE MENÚ
    parser = argparse.ArgumentParser(description='Realiza búsquedas en Pastebin, almacena en base de datos e informa cuando haya un nuevo pastebin.')
    parser.add_argument("-q", "--query", help="Consulta a Pastebin", required=True)
    parser.add_argument("--site",
                            help="Sitio sobre el cual se desea hacer la búsqueda. Debe estar configurado en CSE.")
    parser.add_argument("--email", type=bool, nargs='?',
                            const=True, default=False,
                            help="Habilita el envío de email. Debe configurarse los destinatarios en recipients.txt.")
    parser.add_argument("--api", type=bool, nargs='?',
                            const=True, default=False,
                            help="Las operaciones se realizan mediante la API de Google. Es necesario contar con una API KEY de una aplicación.")
    parser.add_argument("--csv",
                            help="Nombre del archivo csv donde se guardan los resultados.")
    parser.add_argument("--json",
                            help="Nombre del archivo json donde se guardan los resultados.")


    args = parser.parse_args()
    query = args.query
    query_site = query
    site = ""


    # Me conecto a la base de datos
    conn  = database.create_connection(db_file)

    # Verifico si existe la búsqueda en la base de datos y seteo el id de la búsqueda, si no existe, la creo.
    query_obj = database.check_exists_query(conn, query)

    if not query_obj:
        query_id = database.insert_query(conn, query)
    else:
        query_id =query_obj[0][0]


    if args.site:
        site = args.site
        query_site = query_site + " site:" + site

        site_obj = database.check_exists_site(conn, site)

        if not site_obj:
            site_id = database.insert_site(conn, site)
        else:
            site_id = site_obj[0][0]


    # Acá debo configurar los parámetros restantes para poder usar el buscador de Google.
    # Se actualizan cada vez que ejecuto el script.
    cse_tok, cselibv = requester.get_parameters_web("http://cse.google.com/cse.js?hpg=1&cx=" + cx_id)
    r_json =  requester.get_results_web(0, cselibv, cx_id, query_site, cse_tok)

    pages = r_json["cursor"]["pages"]

    results_json = {
            "query": query,
            "site": site,
            "results": []
    }

    with conn:
        try:
            if args.api:
                flag = True
                results = requester.get_results_api("1", api_key, cx_id, query_site)
                while flag:
                    for result in results["items"]:
                        results_json = check_results(result, results_json, True)
                        time.sleep(1)
                    if "nextPage" in results["queries"]:
                        start_index = results["queries"]["nextPage"][0]["startIndex"]
                        results = requester.get_results_api(start_index, api_key, cx_id, query_site)
                    else:
                        flag = False
                    
                    
            else:
                for page in pages:
                    start_index = page["start"]
                    r_json = requester.get_results_web(start_index, cselibv, cx_id, query_site, cse_tok)
                    if "results" in r_json:
                        for result in r_json["results"]:
                            results_json = check_results(result, results_json)
                            time.sleep(1)
        
        except Exception as e:
            print("Ha ocurrido una excepción: " + str(e))

        if args.json:
            with open(args.json, "w") as f:
                json.dump(results_json, f)