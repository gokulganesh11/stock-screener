import pandas as pd
import requests
import re

from io import StringIO
from bs4 import BeautifulSoup


def get_sector_stocks(sector_url):

    sector_url = str(sector_url)

    # -----------------------------------
    # Clean Screener URL
    # -----------------------------------

    match = re.search(
        r'https://www\.screener\.in/[^\s"\']+',
        sector_url
    )

    if match:
        sector_url = match.group(0)

    print(f"SECTOR URL: {sector_url}")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        sector_url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    html = response.text

    # -----------------------------------
    # Read Screener Table
    # -----------------------------------

    tables = pd.read_html(
        StringIO(html)
    )

    if len(tables) == 0:

        raise Exception(
            "No tables found on page"
        )

    df = tables[0]

    # -----------------------------------
    # Flatten MultiIndex Columns
    # -----------------------------------

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        df.columns = [
            " ".join(
                str(x)
                for x in col
                if str(x) != "nan"
            ).strip()
            for col in df.columns
        ]

    # -----------------------------------
    # Clean Column Names
    # -----------------------------------

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # -----------------------------------
    # Extract Company URLs
    # -----------------------------------

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    company_links = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link["href"]

        if "/company/" in href:

            if href.startswith("/"):

                href = (
                    "https://www.screener.in"
                    + href
                )

            # Extract only clean company URL
            match = re.search(
                r'https://www\.screener\.in/company/[A-Za-z0-9\-/]+/?',
                href
            )

            if match:

                href = match.group(0)

                company_links.append(
                    href
                )

    # -----------------------------------
    # Remove Duplicates
    # -----------------------------------

    seen = set()

    unique_links = []

    for url in company_links:

        if url not in seen:

            seen.add(url)

            unique_links.append(url)

    company_links = unique_links

    # -----------------------------------
    # Add Company URL Column
    # -----------------------------------

    df["Company URL"] = None

    row_count = min(
        len(df),
        len(company_links)
    )

    for i in range(row_count):

        df.loc[
            i,
            "Company URL"
        ] = company_links[i]

    # -----------------------------------
    # Debug
    # -----------------------------------

    print("\n===== FIRST 5 COMPANY URLS =====")

    for url in company_links[:5]:

        print(url)

    print("===============================\n")

    print(
        f"Rows Found: {len(df)}"
    )

    return df