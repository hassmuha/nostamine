
import requests
from bs4 import BeautifulSoup

def fetchscore(refreshTime):
    url = "http://static.cricinfo.com/rss/livescores.xml"
    while True:
        r = requests.get(url)
        while r.status_code is not 200:
            r = requests.get(url)
        soup = BeautifulSoup(r.text)
        data = soup.find_all("description")
        for d in data:
            stats = d.text.lower().strip(' ')
            if team1 in stats and team2 in stats:
                sendmessage("Score", d.text)
        sleep(refreshTime)

if __name__=='__main__':
    url = "http://static.cricinfo.com/rss/livescores.xml"

    r = requests.get(url)
    while r.status_code is not 200:
        r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    data = soup.find_all("description")
    for d in data:
        #if "karachi" in d.text.lower() and "peshawar" in d.text.lower():
        print d.text.lower()
