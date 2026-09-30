import random
import re
import time
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.screener.in"
SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(total=0, redirect=2)))
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 Version/18.6 Safari/605.1.15",
]


def _clean_url(value):
    match = re.search(r"https://www\.screener\.in/[^\s\"'<>]+", str(value))
    return match.group(0).rstrip(")].,;") if match else str(value).strip()


def _fetch(url):
    last_error = None
    for attempt in range(5):
        try:
            response = SESSION.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=30)
            if response.status_code == 429:
                time.sleep(min(20, 3 * (2 ** attempt)) + random.uniform(.2, .8))
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(min(10, 1.5 * (2 ** attempt)) + random.uniform(.1, .5))
    raise last_error or RuntimeError(f"Unable to fetch {url}")


def get_sector_stocks(sector_url):
    sector_url = _clean_url(sector_url)
    if not sector_url.startswith("http"):
        raise ValueError("A valid Screener.in sector URL is required")
    html = _fetch(sector_url).text
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError as exc:
        raise RuntimeError("No tabular data found on the Screener sector page") from exc
    if not tables:
        raise RuntimeError("No tables found on the Screener sector page")
    df = max(tables, key=len).copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(x) for x in c if str(x).lower() != "nan").strip() for c in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    if "Company" not in df.columns:
        raise RuntimeError("Could not find the Company column on the sector page")

    soup = BeautifulSoup(html, "html.parser")
    links, seen, company_to_url = [], set(), {}
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if "/company/" not in href: continue
        if href.startswith("/"): href = BASE_URL + href
        match = re.search(r"https://www\.screener\.in/company/[A-Za-z0-9\-/]+/?", href)
        if not match: continue
        url = match.group(0)
        if url not in seen: seen.add(url); links.append(url)
        name = " ".join(link.get_text(" ", strip=True).split())
        if name: company_to_url.setdefault(name.lower(), url)

    df["Company URL"] = None
    for idx, row in df.iterrows():
        name = str(row.get("Company", "")).strip()
        df.at[idx, "Company URL"] = company_to_url.get(name.lower()) or (links[idx] if idx < len(links) else None)
    return df.drop_duplicates(subset=["Company"], keep="first").reset_index(drop=True)
