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

api_key = config.API_KEY
cx_id = config.CX_ID
db_file = config.DB

#cselibv = "8b2252448421acb3"
#cse_tok = "AKaTTZh7iKf_9DQIBHiu3XBf5MNS:1579197463648" # Esto cambia, hay que tenerlo en cuenta

api_google_name = "google.search.cse.api0001" # Esos numeros parecen no tener importancia.


def get_parameters(url):
    results = requests.get(url)
    results = results.text.split(",")
    for line in results:
        if "cse_token" in line:
            #print(line)
            cse_tok = line.split(" ")[3].replace('"','')
        elif "cselibVersion\":" in line:
            #print(line)
            cselibv= line.split(" ")[3].replace('"','')
    return (cse_tok, cselibv)


def get_results(start_index):
    url = "https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&gss=.com&start={0}&cselibv={1}&cx={2}&q={3}&safe=off&cse_tok={4}&sort=date&exp=csqr,cc&callback={5}".format(start_index, cselibv, cx_id, paste_query, cse_tok, api_google_name)
    results = requests.get(url)
    # Necesito quitar del resultado información de google para quedarme solamente con el json.
    results = results.text.strip("/*O_o*/\ngoogle.search.cse." + api_google_name + "(").strip(");")
    return json.loads(results)


# OPCIONES DE MENÚ
parser = argparse.ArgumentParser(description='Realiza búsquedas en Pastebin, almacena en base de datos e informa cuando haya un nuevo pastebin.')
parser.add_argument("-q", "--query", help="Consulta a Pastebin", required=True)
parser.add_argument("--email", type=bool, nargs='?',
                        const=True, default=False,
                        help="Habilita el envío de email. Debe configurarse los destinatarios en recipients.txt.")
parser.add_argument("--csv",
                        help="Nombre del archivo csv donde se guardan los resultados.")

args = parser.parse_args()

paste_query = args.query

# Acá debo configurar los parámetros restantes para poder usar el buscador de Google.
# Se actualizan cada vez que ejecuto el script.
cse_tok, cselibv = get_parameters("http://cse.google.com/cse.js?hpg=1&cx=" + cx_id)


# Paginación de resultados obtenidos para la búsqueda hecha:
r_json = r_json = get_results(0)
pages = r_json["cursor"]["pages"]

# Me conecto a la base de datos
conn  = database.create_connection(db_file)

# Verifico si existe la búsqueda en la base de datos y seteo el id de la búsqueda, si no existe, la creo.
paste_query_obj = database.check_exists_query(conn, paste_query)

if not paste_query_obj:
    paste_query_id = database.insert_query(conn, paste_query)
else:
    paste_query_id = paste_query_obj[0][0]


with conn:
    for page in pages:
        start_index = page["start"]
        r_json = get_results(start_index)
        for result in r_json["results"]:
            title = result["title"]
            link = result["url"]
            body_text = result["contentNoFormatting"]
            body_hash = hashlib.sha256(body_text.encode()).hexdigest()
            create_date = datetime.now()
            paste = (title, paste_query_id, link, body_text, body_hash, create_date)
            
            if not database.check_exists_paste(conn, body_hash):
                print("Se ha detectado un nuevo pastebin.")
                database.insert_paste(conn, paste)

                if args.email:
                    msg = """Se ha detectado un nuevo Pastebin para {0}.\n
    Título: {1}.
    Enlace: {2}.
    Mensaje: {3}
                    """.format(paste_query, title, link, body_text)
                    subject = "Se ha detectado un nuevo Pastebin para {0}".format(paste_query)
                    send_email.send_email(msg, subject)
                
                time.sleep(1)

                if args.csv:
                    pass

        time.sleep(1)
