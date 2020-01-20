import requests
import json


# El nombre de la api google es necesaria para decirle a Google que hacemos callback y para parsear los resultados obtenidos de las búsquedas.
api_google_name = "google.search.cse.api0001" 


def get_parameters_web(url):
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


def get_results_web(start_index, cselibv, cx_id, query_site, cse_tok):
    """ Retorna el json con los resultados obtenidos a partir de la búsqueda haciendo consultas a la opción web.
        Parámetros:
            start_index: índice o página de las búsquedas obtenidas.
            cselibv: versión de librería de CSE, este valor se obtiene de manera dinámica parseando un archivo JS.
            cx_id: identificador del CSE.
            query_site: consulta para el buscador.
            cse_tok: token obtenido de manera dinámica similar a cselibv.
    """
    #url = "https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&gss=.com&start={0}&cselibv={1}&cx={2}&q={3}&safe=off&cse_tok={4}&sort=date&exp=csqr,cc&callback={5}".format(start_index, cselibv, cx_id, query_site, cse_tok, api_google_name)
    url = "https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=en&source=gcsc&gss=.com&start={0}&cselibv={1}&cx={2}&q={3}&safe=off&cse_tok={4}&exp=csqr,cc&callback={5}".format(start_index, cselibv, cx_id, query_site, cse_tok, api_google_name)
    results = requests.get(url)
    # Necesito quitar del resultado información de google para quedarme solamente con el json.
    results = results.text.strip("/*O_o*/\ngoogle.search.cse." + api_google_name + "(").strip(");")
    return json.loads(results)


def get_results_api(start_index, api_key, cx_id, query_site):
    """Retorna el JSON con los resultados obtenidos a partir de la búsuqeda haciendo consultas a la opción API.
       Parámetros:
        start_index: índice o página de las búsquedas obtenidas.
        api_key: API KEY de la aplicación de Google.
        cx_id: identificador del CSE.
        query_site: consulta para el buscador.
    """
    url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&q={2}&start={3}".format(api_key, cx_id, query_site, start_index)
    ret = requests.get(url).json()
    return ret

