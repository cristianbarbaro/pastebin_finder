from datetime import datetime
import requests
import hashlib
import json
import sys
import time
from paste_utils import send_email
from paste_utils import config
from paste_utils import database
import argparse


cx_id = config.CX_ID
db_file = config.DB
# El nombre de la api google es necesaria para decirle a Google que hacemos callback y para parsear los resultados obtenidos de las búsquedas.
api_google_name = "google.search.cse.api0001" 


def get_parameters(url):
    """ Obtengo los parámetros cse_token y cselibv necesarios para hacer las consultas a nuestro CSE.
        Estos valores se agregan a la URL de consulta del CSE.
        Parámetros:
            url: dirección del javascript que contiene la información necesaria (ej., http://cse.google.com/cse.js?hpg=1&cx=CX_VALUE).
    """
    results = requests.get(url).text.split(",")
    for line in results:
        if "cse_token" in line:
            cse_tok = line.split(" ")[3].replace('"','')
        elif "cselibVersion\":" in line:
            cselibv= line.split(" ")[3].replace('"','')
    return (cse_tok, cselibv)


def get_results(start_index):
    """ Retorna el json con los resultados obtenidos a partir de la búsqueda. 
        Toma los valores de las variables definidas globalmente.
        Parámetros:
            start_index: índice o página de las búsquedas obtenidas.
    """
    url = "https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&gss=.com&start={0}&cselibv={1}&cx={2}&q={3}&safe=off&cse_tok={4}&sort=date&exp=csqr,cc&callback={5}".format(start_index, cselibv, cx_id, query_site, cse_tok, api_google_name)
    results = requests.get(url)
    # Necesito quitar del resultado información de google para quedarme solamente con el json.
    results = results.text.strip("/*O_o*/\ngoogle.search.cse." + api_google_name + "(").strip(");")
    return json.loads(results)


# OPCIONES DE MENÚ
parser = argparse.ArgumentParser(description='Realiza búsquedas en Pastebin, almacena en base de datos e informa cuando haya un nuevo pastebin.')
parser.add_argument("-q", "--query", help="Consulta a Pastebin", required=True)
parser.add_argument("--site",
                        help="Sitio sobre el cual se desea hacer la búsqueda. Debe estar configurado en CSE.")
parser.add_argument("--email", type=bool, nargs='?',
                        const=True, default=False,
                        help="Habilita el envío de email. Debe configurarse los destinatarios en recipients.txt.")
parser.add_argument("--csv",
                        help="Nombre del archivo csv donde se guardan los resultados.")
parser.add_argument("--json",
                        help="Nombre del archivo json donde se guardan los resultados.")

args = parser.parse_args()

query = args.query

query_site = query

site = ""

# Acá debo configurar los parámetros restantes para poder usar el buscador de Google.
# Se actualizan cada vez que ejecuto el script.
cse_tok, cselibv = get_parameters("http://cse.google.com/cse.js?hpg=1&cx=" + cx_id)


# Paginación de resultados obtenidos para la búsqueda hecha:
r_json = r_json = get_results(0)
pages = r_json["cursor"]["pages"]

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


with conn:
    for page in pages:
        start_index = page["start"]
        r_json = get_results(start_index)
        results_json = {
                "query": query,
                "site": site,
                "results": []
        }
        
        for result in r_json["results"]:
            title = result["title"]
            link = result["url"]
            body_text = result["contentNoFormatting"]
            body_hash = hashlib.sha256(body_text.encode()).hexdigest()
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
                print("Se ha detectado un nuevo pastebin.")
                database.insert_paste(conn, paste)

                if args.email:
                    msg = """Se ha detectado un nuevo Pastebin para {0}.\n
    Título: {1}.
    Enlace: {2}.
    Mensaje: {3}
                    """.format(query, title, link, body_text)
                    subject = "Se ha detectado un nuevo Pastebin para {0}".format(query)
                    send_email.send_email(msg, subject)
                
                time.sleep(1)

        # Debo imprimir el json a un archivo:
        if args.json:
            with open(args.json, "w") as f:
                json.dump(results_json, f)

        time.sleep(1)
