import requests
import sqlite3
from sqlite3 import Error
from datetime import datetime
import config
import hashlib
import json
import time
import sys
import re

paste_query = sys.argv[1]

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


def create_connection(db_file):
    conn = None
    try: 
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def insert_paste(conn, paste):
    sql = """ INSERT INTO pastes(title, paste_query_id, link, body_text, body_hash, create_date)
              VALUES(?,?,?,?,?,?) """
    cursor = conn.cursor()
    cursor.execute(sql, paste)
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def insert_query(conn, paste_query):
    sql = """ INSERT INTO Queries(paste_query)
              VALUES(?) """
    cursor = conn.cursor()
    cursor.execute(sql, (paste_query,))
    conn.commit()
    #cursor.close()
    return cursor.lastrowid


def get_results(start_index):
    url = "https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&gss=.com&start={0}&cselibv={1}&cx={2}&q={3}&safe=off&cse_tok={4}&sort=date&exp=csqr,cc&callback={5}".format(start_index, cselibv, cx_id, paste_query, cse_tok, api_google_name)
    #url = "https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&gss=.com&start={0}&cx={1}&q={2}&safe=off&cse_tok={3}&sort=date&exp=csqr,cc&callback=google.search.cse.api11552".format(start_index, cx_id, query, cse_tok)
    results = requests.get(url)
    #print(url)
    # Necesito quitar del resultado información de google para quedarme solamente con el json.
    results = results.text.strip("/*O_o*/\ngoogle.search.cse." + api_google_name + "(").strip(");")
    return json.loads(results)


def check_exists_paste(conn, body_hash):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pastes WHERE body_hash=?", (body_hash,))
    return cursor.fetchall()


def check_exists_query(conn, paste_query):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Queries WHERE paste_query=?", (paste_query,))
    return cursor.fetchall()


# Acá debo configurar los parámetros restantes para poder usar el buscador de Google.
# Se actualizan cada vez que ejecuto el script.
cse_tok, cselibv = get_parameters("http://cse.google.com/cse.js?hpg=1&cx=" + cx_id)


# Paginación de resultados obtenidos para la búsqueda hecha:
r_json = r_json = get_results(0)
pages = r_json["cursor"]["pages"]

# Me conecto a la base de datos
conn  = create_connection(db_file)

# Verifico si existe la búsqueda en la base de datos y seteo el id de la búsqueda, si no existe, la creo.
paste_query_obj = check_exists_query(conn, paste_query)

if not paste_query_obj:
    paste_query_id = insert_query(conn, paste_query)
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
            if not check_exists_paste(conn, body_hash):
                print("Línea de pastebin nueva, se inserta en la base de datos...")
                print(paste)
                insert_paste(conn, paste)
            else:
                print("Información ya existe en la base de datos... No se inserta.")
        time.sleep(2)
