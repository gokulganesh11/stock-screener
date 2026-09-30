import pandas as pd
import requests

from io import StringIO

url = "https://www.screener.in/market/IN05/IN0501/IN050103/"

html = requests.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
).text

tables = pd.read_html(
    StringIO(html)
)

df = tables[0]

print(df.columns)

print("\nFIRST ROW:\n")

print(df.iloc[0])