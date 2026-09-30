"""Sector-table scraper for Screener.in."""

import re
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.screener.in"
DEFAULT_TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockScreener/1.0)"}


def _clean_company_url(href):
    match = re.search(
        r"https://www\.screener\.in/company/[A-Za-z0-9_\-/]+/?",
        href,
    )
    return match.group(0).rstrip("/") + "/" if match else None


def get_sector_stocks(sector_url, session=None, timeout=DEFAULT_TIMEOUT):
    """Return the first Screener table and map URLs by company name.

    Mapping is based on the company name shown in each table row rather than
    the incidental order of all links in the HTML document.
    """
    sector_url = str(sector_url).strip()
    if not sector_url.startswith(BASE_URL + "/"):
        raise ValueError(f"Unsupported sector URL: {sector_url}")

    client = session or requests.Session()
    response = client.get(sector_url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    html = response.text

    tables = pd.read_html(StringIO(html))
    if not tables:
        raise ValueError("No tables found on Screener page")

    df = tables[0].copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            " ".join(str(x) for x in col if str(x) != "nan").strip()
            for col in df.columns
        ]
    df.columns = [str(col).strip() for col in df.columns]

    soup = BeautifulSoup(html, "html.parser")
    links_by_name = {}
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/company/" not in href:
            continue
        if href.startswith("/"):
            href = BASE_URL + href
        url = _clean_company_url(href)
        name = " ".join(link.stripped_strings)
        if url and name:
            links_by_name.setdefault(name.casefold(), url)

    df["Company URL"] = None
    name_column = next(
        (column for column in df.columns if column.casefold() in {"name", "company"}),
        None,
    )
    if name_column:
        df["Company URL"] = df[name_column].map(
            lambda value: links_by_name.get(str(value).strip().casefold())
        )

    return df
