import requests
from bs4 import BeautifulSoup

url = "https://www.screener.in/market/IN05/IN0501/IN050103/"

html = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
).text

soup = BeautifulSoup(
    html,
    "html.parser"
)

count = 0

for link in soup.find_all("a", href=True):

    href = link["href"]

    if "/company/" in href:

        print(repr(href))

        count += 1

        if count == 10:
            break