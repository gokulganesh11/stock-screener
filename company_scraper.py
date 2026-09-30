"""Screener.in company-page scraper used by the stock analysis workflow."""

import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.screener.in"
DEFAULT_TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockScreener/1.0)"}


def clean_text(value):
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value)).strip()


def market_cap_to_cr(value):
    number = to_number(value)
    return number if number is not None else 0


def to_number(value):
    if value is None:
        return None
    text = clean_text(value)
    if not text or text.lower() in {"nan", "none", "-", "—", "n/a", "na"}:
        return None
    try:
        return float(
            text.replace("₹", "")
            .replace(",", "")
            .replace("Cr.", "")
            .replace("Cr", "")
            .replace("%", "")
            .strip()
        )
    except (TypeError, ValueError):
        return None


def _extract_top_ratios(soup, data):
    for ratio in soup.select("ul#top-ratios li"):
        name = ratio.select_one(".name")
        value = ratio.select_one(".value")
        if not name or not value:
            continue

        metric = clean_text(name.get_text(" "))
        metric_value = clean_text(value.get_text(" "))
        if not metric:
            continue

        mapping = {
            "ROE": "ROE",
            "ROCE": "ROCE",
            "Stock P/E": "PE",
            "Market Cap": "Market Cap",
            "Book Value": "Book Value",
            "Face Value": "Face Value",
            "Dividend Yield": "Dividend Yield",
            "Current Price": "Current Price",
            "High / Low": "High Low",
            "EPS": "EPS",
            "Debt": "Debt to Equity",
            "Debt to equity": "Debt to Equity",
            "Debt to Equity": "Debt to Equity",
        }
        key = mapping.get(metric)
        if key:
            data[key] = metric_value
            if key == "Market Cap":
                data["Market Cap Cr"] = market_cap_to_cr(metric_value)


def _extract_shareholding(soup, data):
    for row in soup.select("#shareholding table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        category = clean_text(cells[0].get_text(" ")) or ""
        value = clean_text(cells[-1].get_text(" "))
        if "Promoter" in category:
            data["Promoter Holding"] = value
        elif "FII" in category:
            data["FII Holding"] = value
        elif "DII" in category:
            data["DII Holding"] = value
        elif "Government" in category:
            data["Government Holding"] = value
        elif "Public" in category:
            data["Public Holding"] = value


def _extract_growth(page_text, data):
    sales = re.search(
        r"Compounded Sales Growth.*?5 Years:\s*([+-]?\d+(?:\.\d+)?%).*?3 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        page_text,
        re.DOTALL,
    )
    if sales:
        data["Sales Growth 5Y"], data["Sales Growth 3Y"] = sales.groups()

    profit = re.search(
        r"Compounded Profit Growth.*?5 Years:\s*([+-]?\d+(?:\.\d+)?%).*?3 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        page_text,
        re.DOTALL,
    )
    if profit:
        data["Profit Growth 5Y"], data["Profit Growth 3Y"] = profit.groups()


def get_company_details(company_url, session=None, timeout=DEFAULT_TIMEOUT):
    """Fetch and parse a Screener.in company page.

    Raises requests exceptions for network/HTTP failures so callers can report
    failed companies instead of silently treating them as successful analyses.
    """
    company_url = str(company_url).strip()
    if not company_url.startswith(BASE_URL + "/company/"):
        raise ValueError(f"Unsupported company URL: {company_url}")

    client = session or requests.Session()
    response = client.get(company_url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    data = {
        "Company URL": company_url,
        "ROE": None,
        "ROCE": None,
        "PE": None,
        "Market Cap": None,
        "Market Cap Cr": 0,
        "Book Value": None,
        "Face Value": None,
        "Dividend Yield": None,
        "EPS": None,
        "Debt to Equity": None,
        "Current Price": None,
        "High Low": None,
        "Promoter Holding": None,
        "FII Holding": None,
        "DII Holding": None,
        "Government Holding": None,
        "Public Holding": None,
        "Sales Growth 3Y": None,
        "Sales Growth 5Y": None,
        "Profit Growth 3Y": None,
        "Profit Growth 5Y": None,
    }

    _extract_top_ratios(soup, data)
    _extract_shareholding(soup, data)
    _extract_growth(clean_text(soup.get_text(" ")) or "", data)
    return data
