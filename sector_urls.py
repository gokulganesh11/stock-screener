"""Dynamic Screener industry catalogue.

Screener maintains the live industry list at /market/. We read that page so the
app does not depend on a stale hand-written list of sector URLs.
"""

import re
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.screener.in"
INDUSTRY_URL = f"{BASE_URL}/market/"

# Friendly names used in the UI. The live catalogue may contain finer-grained
# industries (for example Asset Management Company instead of Capital Markets).
ALIASES = {
    "Capital Markets": ["Capital Market", "Asset Management Company", "Exchange and Data Platform", "Financial Products Distributor"],
    "Banks": ["Bank", "Other Bank"],
    "IT - Services": ["Computers - Software & Consulting", "IT Enabled Services", "Data Processing Services"],
    "IT - Hardware": ["Computers Hardware & Equipments"],
    "Pharmaceuticals & Biotechnology": ["Pharmaceuticals", "Biotechnology"],
    "Automobiles": ["2/3 Wheelers", "Commercial Vehicles", "Passenger Cars & Utility Vehicles", "Auto Components & Equipments"],
    "Power": ["Integrated Power Utilities", "Power Generation", "Power Transmission"],
    "Chemicals & Petrochemicals": ["Commodity Chemicals", "Specialty Chemicals", "Petrochemicals"],
    "Healthcare": ["Hospital", "Healthcare Service Provider", "Medical Equipment & Supplies", "Healthcare Research, Analytics & Technology"],
    "Financial Services": ["Non Banking Financial Company (NBFC)", "Financial Institution", "Other Financial Services", "Financial Technology (Fintech)"],
}


def _num(text):
    try:
        return float(str(text).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _industry_links(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        name = " ".join(a.get_text(" ", strip=True).split())
        if not name or "/market/" not in href or name in {"Industry", "No. of Companies"}:
            continue
        if href.startswith("/"):
            href = BASE_URL + href
        if re.match(r"https://www\.screener\.in/market/[^\s]+/?$", href):
            out[name] = href
    return out


def get_industry_catalog(timeout=30):
    """Return all live Screener industries with overview metrics and URLs."""
    response = requests.get(
        INDUSTRY_URL,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-IN,en;q=0.9"},
        timeout=timeout,
    )
    response.raise_for_status()
    html = response.text
    links = _industry_links(html)
    tables = pd.read_html(StringIO(html))
    if not tables:
        raise RuntimeError("Screener industry overview returned no table")
    df = max(tables, key=len).copy()
    df.columns = [str(c).strip() for c in df.columns]
    industry_col = next((c for c in df.columns if str(c).strip().lower() == "industry"), df.columns[1])
    df = df.rename(columns={industry_col: "Industry"})
    df["Industry"] = df["Industry"].astype(str).str.strip()
    df["URL"] = df["Industry"].map(links)
    for col in ["No. of Companies", "Total Market Cap.", "Median Market Cap.", "Median P/E", "Wtd. Avg Sales Growth", "Wtd. Avg OPM", "Wtd. Avg ROCE", "Median 1Y Return"]:
        if col in df.columns:
            df[col] = df[col].map(_num)
    df = df[df["URL"].notna()].drop_duplicates("Industry").reset_index(drop=True)
    return df


def build_friendly_catalog(raw_df):
    """Return the full live catalogue plus optional friendly groups."""
    rows = []
    for _, row in raw_df.iterrows():
        item = row.to_dict()
        item["Sector"] = item.get("Industry")
        item["Group"] = next((group for group, names in ALIASES.items() if item.get("Industry") in names), item.get("Industry"))
        rows.append(item)
    return pd.DataFrame(rows)


# Backward-compatible object: the app can import it without doing a network call.
SECTOR_URLS = {}
