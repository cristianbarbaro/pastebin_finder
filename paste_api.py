import requests
from config import config
import time
import sys

query = sys.argv[1]

api_key = config.API_KEY

cx_id = config.CX_ID

def get_results(start_index):
    url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&q={2}&start={3}".format(api_key, cx_id, query, start_index)
    return requests.get(url).json()


flag = True
results = get_results("1")

while flag:
    for result in results["items"]:
        print("Title: " + result["title"])
        print("\tLink: " + result["link"])

    if "nextPage" in results["queries"]:
        start_index = results["queries"]["nextPage"][0]["startIndex"]
        time.sleep(1)
        results = get_results(start_index)
        print(start_index)
    else:
        flag = False

