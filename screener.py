import os
import random
import re
import time
from io import StringIO
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.screener.in"
REQUEST_DELAY = float(os.getenv("SCREENER_SECTOR_DELAY", "1.5"))
TIMEOUT = int(os.getenv("SCREENER_TIMEOUT", "30"))
MAX_PAGES = int(os.getenv("SCREENER_MAX_SECTOR_PAGES", "10"))

SESSION = requests.Session()
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(total=0, redirect=2)))
SESSION.headers.update(
    {
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": BASE_URL + "/",
    }
)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 Version/18.6 Safari/605.1.15",
]
LAST_REQUEST = 0.0


def _clean_url(value):
    match = re.search(r"https://www\.screener\.in/[^\s\"'<>]+", str(value))
    return match.group(0).rstrip(")].,;") if match else str(value).strip()


def _page_url(url, page):
    parts = urlsplit(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    query["page"] = [str(page)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))


def _limit():
    global LAST_REQUEST
    wait = REQUEST_DELAY - (time.monotonic() - LAST_REQUEST)
    if wait > 0:
        time.sleep(wait)
    LAST_REQUEST = time.monotonic()


def _fetch(url):
    last_error = None
    for attempt in range(5):
        _limit()
        try:
            response = SESSION.get(
                url,
                headers={"User-Agent": random.choice(USER_AGENTS)},
                timeout=TIMEOUT,
            )
            if response.status_code == 429:
                time.sleep(min(30, 4 * (2**attempt)) + random.uniform(0.5, 1.5))
                last_error = RuntimeError(f"429 Too Many Requests for {url}")
                continue
            if response.status_code in {500, 502, 503, 504}:
                time.sleep(min(15, 2 * (2**attempt)) + random.uniform(0.2, 0.8))
                last_error = RuntimeError(f"HTTP {response.status_code} for {url}")
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(min(12, 2 * (2**attempt)) + random.uniform(0.2, 0.8))
    raise last_error or RuntimeError(f"Unable to fetch {url}")


def _normalise_table(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            " ".join(str(x) for x in c if str(x).lower() != "nan").strip()
            for c in df.columns
        ]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _company_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links, seen, company_to_url = [], set(), {}
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if "/company/" not in href:
            continue
        if href.startswith("/"):
            href = BASE_URL + href
        match = re.search(r"https://www\.screener\.in/company/[A-Za-z0-9\-/]+/?", href)
        if not match:
            continue
        url = match.group(0)
        if url not in seen:
            seen.add(url)
            links.append(url)
        name = " ".join(link.get_text(" ", strip=True).split())
        if name:
            company_to_url.setdefault(name.lower(), url)
    return links, company_to_url


def _parse_page(html):
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError:
        return pd.DataFrame(), {}, []
    if not tables:
        return pd.DataFrame(), {}, []

    candidates = []
    for table in tables:
        table = _normalise_table(table)
        if "Company" in table.columns or "Name" in table.columns:
            candidates.append(table)
    if not candidates:
        return pd.DataFrame(), {}, []

    df = max(candidates, key=len).copy()
    if "Company" not in df.columns and "Name" in df.columns:
        df = df.rename(columns={"Name": "Company"})

    links, company_to_url = _company_links(html)
    return df, company_to_url, links


def get_sector_stocks(sector_url):
    """Return all companies across the paginated Screener sector listing.

    The previous implementation only read page 1, which silently limited
    Capital Markets to roughly 25 companies even though Screener currently
    exposes multiple pages. This implementation follows pagination and
    de-duplicates companies by name.
    """
    sector_url = _clean_url(sector_url)
    if not sector_url.startswith("http"):
        raise ValueError("A valid Screener.in sector URL is required")

    all_frames = []
    global_seen = set()
    total_hint = None

    for page in range(1, MAX_PAGES + 1):
        url = _page_url(sector_url, page)
        html = _fetch(url).text
        df, company_to_url, links = _parse_page(html)
        if df.empty:
            break

        if total_hint is None:
            match = re.search(r"([\d,]+)\s+results found", BeautifulSoup(html, "html.parser").get_text(" "))
            if match:
                total_hint = int(match.group(1).replace(",", ""))

        page_urls = []
        for idx, row in df.iterrows():
            name = str(row.get("Company", "")).strip()
            if not name or name.lower() in {"nan", "company"}:
                continue
            key = name.casefold()
            if key in global_seen:
                continue
            global_seen.add(key)
            company_url = company_to_url.get(key)
            if not company_url and idx < len(links):
                company_url = links[idx]
            page_urls.append(company_url)
            row_copy = row.copy()
            row_copy["Company"] = name
            row_copy["Company URL"] = company_url
            all_frames.append(row_copy.to_dict())

        if not page_urls:
            break
        if total_hint is not None and len(all_frames) >= total_hint:
            break

        # Screener currently shows 25 rows per page. Stop when a short page is
        # returned; this also protects against looping forever on a custom URL.
        if len(page_urls) < 25:
            # There may still be a final page if the site changes page size, so
            # continue once more only when a total-count hint says more exist.
            if total_hint is None or len(all_frames) >= total_hint:
                break

    result = pd.DataFrame(all_frames)
    if result.empty:
        raise RuntimeError("No company table found on the Screener sector page")

    result = result.drop_duplicates(subset=["Company"], keep="first").reset_index(drop=True)
    return result
