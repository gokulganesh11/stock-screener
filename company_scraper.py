import os
import random
import re
import threading
import time
from functools import lru_cache
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.screener.in"
DELAY = float(os.getenv("SCREENER_REQUEST_DELAY", "1.8"))
TIMEOUT = int(os.getenv("SCREENER_TIMEOUT", "30"))
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 Version/18.6 Safari/605.1.15",
]
SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(total=0, redirect=2)))
SESSION.headers.update({"Accept-Language": "en-IN,en;q=0.9", "Accept": "text/html,application/xhtml+xml"})
LOCK = threading.Lock()
LAST_REQUEST = 0.0


def clean_text(value):
    if value is None:
        return None
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value or None


def to_number(value):
    if value is None:
        return None
    text = clean_text(value)
    if not text or text.lower() in {"none", "nan", "n/a", "na", "-", "--"}:
        return None
    text = text.replace(",", "").replace("₹", "").replace("%", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def _limit():
    global LAST_REQUEST
    with LOCK:
        wait = DELAY - (time.monotonic() - LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        LAST_REQUEST = time.monotonic()


def _get(url):
    last = None
    for attempt in range(6):
        _limit()
        try:
            response = SESSION.get(
                url,
                headers={"User-Agent": random.choice(USER_AGENTS)},
                timeout=TIMEOUT,
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = min(45, 5 * (2**attempt))
                time.sleep(delay + random.uniform(0.5, 1.5))
                last = RuntimeError(f"429 Too Many Requests for {url}")
                continue
            if response.status_code in {500, 502, 503, 504}:
                time.sleep(min(20, 2 * (2**attempt)) + random.uniform(0.3, 1.0))
                last = RuntimeError(f"HTTP {response.status_code} for {url}")
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last = exc
            time.sleep(min(15, 2 * (2**attempt)) + random.uniform(0.2, 0.8))
    raise last or RuntimeError(f"Unable to fetch {url}")


def _flat(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(x) for x in c if str(x).lower() != "nan").strip() for c in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _tables(html):
    try:
        return [_flat(t) for t in pd.read_html(StringIO(html))]
    except (ValueError, ImportError):
        return []


def _find_table(tables, pattern, min_cols=1):
    rx = re.compile(pattern, re.I)
    candidates = []
    for df in tables:
        if df.empty or len(df.columns) - 1 < min_cols:
            continue
        if df.iloc[:, 0].astype(str).str.contains(rx, regex=True, na=False).any():
            candidates.append(df)
    return max(candidates, key=lambda x: len(x.columns)) if candidates else pd.DataFrame()


def _row_values(df, label_pattern):
    if df.empty:
        return []
    rx = re.compile(label_pattern, re.I)
    for _, row in df.iterrows():
        if rx.search(clean_text(row.iloc[0]) or ""):
            values = [to_number(row[c]) for c in df.columns[1:]]
            return [v for v in values if v is not None]
    return []


def _extract_ratios(soup, data):
    for li in soup.select("ul#top-ratios li"):
        name, value = li.select_one(".name"), li.select_one(".value")
        if not name or not value:
            continue
        metric = (clean_text(name.get_text(" ", strip=True)) or "").lower()
        raw = clean_text(value.get_text(" ", strip=True))
        if metric == "roe":
            data["ROE"] = to_number(raw)
        elif metric == "roce":
            data["ROCE"] = to_number(raw)
        elif metric == "stock p/e":
            data["PE"] = to_number(raw)
        elif metric == "eps" and data["EPS"] is None:
            data["EPS"] = to_number(raw)
        elif metric == "market cap":
            data["Market Cap"] = raw
            data["Market Cap Cr"] = to_number(raw) or 0
        elif metric == "book value":
            data["Book Value"] = raw
        elif metric == "face value":
            data["Face Value"] = raw
        elif metric == "dividend yield":
            data["Dividend Yield"] = to_number(raw)
        elif metric == "current price":
            data["Current Price"] = raw
        elif metric == "high / low":
            data["High Low"] = raw
        elif "debt to equity" in metric:
            data["Debt to Equity"] = to_number(raw)
        elif "peg" in metric:
            data["PEG Ratio"] = to_number(raw)
            data["PEG Source"] = "Screener ratio"


def _extract_shareholding(soup, data):
    for table in soup.select("#shareholding table"):
        try:
            df = _flat(pd.read_html(StringIO(str(table)))[0])
        except ValueError:
            continue
        if df.empty:
            continue
        for _, row in df.iterrows():
            label = (clean_text(row.iloc[0]) or "").lower()
            vals = [to_number(row[c]) for c in df.columns[1:]]
            vals = [v for v in vals if v is not None]
            if not vals:
                continue
            value = vals[-1]
            if "promoter" in label:
                data["Promoter Holding"] = value
            elif "fii" in label or "fpis" in label:
                data["FII Holding"] = value
            elif "dii" in label:
                data["DII Holding"] = value
            elif "government" in label:
                data["Government Holding"] = value
            elif "public" in label:
                data["Public Holding"] = value
            elif "pledge" in label:
                data["Pledged Percentage"] = value
                data["Pledged Source"] = "shareholding table"


def _extract_financials(tables, data):
    quarterly = _find_table(tables, r"^Sales\s*\+?$|^Net Profit\s*\+?$", 2)
    annual = _find_table(tables, r"^Sales\s*\+?$|^Net Profit\s*\+?$|^EPS in Rs", 6)
    sales_q = _row_values(quarterly, r"^Sales\s*\+?$")
    profit_q = _row_values(quarterly, r"^Net Profit\s*\+?$")
    sales_y = _row_values(annual, r"^Sales\s*\+?$")
    profit_y = _row_values(annual, r"^Net Profit\s*\+?$")
    eps_y = _row_values(annual, r"^EPS in Rs")
    if sales_q:
        data["Sales Latest Quarter"] = sales_q[-1]
    if profit_q:
        data["Net Profit Latest Quarter"] = profit_q[-1]
    if len(sales_y) > 1:
        data["Sales Latest Year"] = sales_y[-1]
        data["Sales Preceding Year"] = sales_y[-2]
        data["Sales Latest Year vs Preceding"] = sales_y[-1] - sales_y[-2]
    if len(profit_y) > 1:
        data["Net Profit Latest Year"] = profit_y[-1]
        data["Net Profit Preceding Year"] = profit_y[-2]
        data["Profit Latest Year vs Preceding"] = profit_y[-1] - profit_y[-2]
    if eps_y:
        data["EPS"] = eps_y[-1]


def _growth(text, label):
    m = re.search(
        rf"{re.escape(label)}.*?5 Years:\s*(-?\d+(?:\.\d+)?)%.*?3 Years:\s*(-?\d+(?:\.\d+)?)%",
        text,
        re.I | re.S,
    )
    return (float(m.group(2)), float(m.group(1))) if m else (None, None)


def _pledge(text):
    for pattern in [
        r"pledged\s+(?:about\s+)?(\d+(?:\.\d+)?)%",
        r"pledged\s+(\d+(?:\.\d+)?)%",
    ]:
        match = re.search(pattern, text, re.I)
        if match:
            return float(match.group(1))
    return None


@lru_cache(maxsize=512)
def get_company_details(company_url):
    url = str(company_url).strip()
    if not url or url.lower() in {"none", "nan"}:
        raise ValueError("Company URL is missing")
    if url.startswith("/"):
        url = BASE_URL + url
    if not url.startswith("http"):
        url = BASE_URL + "/" + url.lstrip("/")

    html = _get(url).text
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "Company URL": url,
        "ROE": None, "ROCE": None, "PE": None, "PEG Ratio": None, "PEG Source": None,
        "Market Cap": None, "Market Cap Cr": 0, "Book Value": None, "Face Value": None,
        "Dividend Yield": None, "EPS": None, "Debt to Equity": None, "Current Price": None,
        "High Low": None, "Promoter Holding": None, "FII Holding": None, "DII Holding": None,
        "Government Holding": None, "Public Holding": None, "Pledged Percentage": None,
        "Pledged Source": None, "Sales Growth 3Y": None, "Sales Growth 5Y": None,
        "Profit Growth 3Y": None, "Profit Growth 5Y": None, "Sales Latest Quarter": None,
        "Net Profit Latest Quarter": None, "Sales Latest Year": None, "Sales Preceding Year": None,
        "Net Profit Latest Year": None, "Net Profit Preceding Year": None,
        "Sales Latest Year vs Preceding": None, "Profit Latest Year vs Preceding": None,
        "Free Cash Flow": None, "CFO/OP": None,
    }

    _extract_ratios(soup, data)
    _extract_shareholding(soup, data)
    _extract_financials(_tables(html), data)

    text = clean_text(soup.get_text(" ")) or ""
    data["Sales Growth 3Y"], data["Sales Growth 5Y"] = _growth(text, "Compounded Sales Growth")
    data["Profit Growth 3Y"], data["Profit Growth 5Y"] = _growth(text, "Compounded Profit Growth")

    if data["Pledged Percentage"] is None:
        pledge = _pledge(text)
        if pledge is not None:
            data["Pledged Percentage"] = pledge
            data["Pledged Source"] = "page text"

    # Screener commonly omits the pledge row when the disclosed pledge is zero.
    # Only infer zero when a shareholding table is present; otherwise keep it unknown.
    if data["Pledged Percentage"] is None and soup.select("#shareholding table"):
        data["Pledged Percentage"] = 0.0
        data["Pledged Source"] = "shareholding table: no pledge reported"

    if data["PEG Ratio"] is None and data["PE"] is not None and data["Profit Growth 5Y"] not in (None, 0):
        data["PEG Ratio"] = round(data["PE"] / data["Profit Growth 5Y"], 3)
        data["PEG Source"] = "Derived: PE / 5Y profit growth"

    tracked = [
        "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity", "Promoter Holding",
        "Pledged Percentage", "Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y",
        "Profit Growth 5Y", "Sales Latest Quarter", "Net Profit Latest Quarter",
        "Sales Latest Year vs Preceding", "Profit Latest Year vs Preceding",
    ]
    data["Data Completeness"] = round(sum(data.get(k) is not None for k in tracked) / len(tracked) * 100, 1)
    return data
