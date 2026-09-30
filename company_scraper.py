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


def market_cap_to_cr(value):
    number = to_number(value)
    return number if number is not None else 0


def _extract_top_ratios(soup, data):
    for ratio in soup.select("ul#top-ratios li"):
        name = ratio.select_one(".name")
        value = ratio.select_one(".value")
        if not name or not value:
            continue

        metric = clean_text(name.get_text(" "))
        metric_value = clean_text(value.get_text(" "))
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
        }
        key = mapping.get(metric)
        if key:
            data[key] = metric_value
            if key == "Market Cap":
                data["Market Cap Cr"] = market_cap_to_cr(metric_value)


def _extract_shareholding(soup, data):
    """Extract the latest promoter/institutional holdings from shareholding tables."""
    for table in soup.select("#shareholding table"):
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            category = clean_text(cells[0].get_text(" ")) or ""
            # Screener displays periods from oldest -> newest, so the last
            # value is the latest reported holding.
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


def _find_section_table(soup, title):
    title = title.lower()
    heading = next(
        (
            tag
            for tag in soup.find_all(["h2", "h3"])
            if title in clean_text(tag.get_text(" ")).lower()
        ),
        None,
    )
    return heading.find_next("table") if heading else None


def _table_rows(table):
    """Return table rows in the same chronological order as Screener.in."""
    if table is None:
        return {}, []

    rows = table.find_all("tr")
    if not rows:
        return {}, []

    header_cells = rows[0].find_all(["th", "td"])
    headers = [clean_text(cell.get_text(" ")) for cell in header_cells][1:]
    result = {}

    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label = clean_text(cells[0].get_text(" "))
        if not label:
            continue
        label = label.replace(" +", "").strip()
        values = [clean_text(cell.get_text(" ")) for cell in cells[1:]]
        result[label] = values

    return result, headers


def _numeric_series(row):
    return [to_number(value) for value in row or []]


def _latest_annual_pair(rows, headers, label):
    """Return latest completed FY and preceding FY, excluding TTM."""
    values = _numeric_series(rows.get(label, []))
    if not values:
        return None, None

    # Screener annual tables normally end with TTM. Use the last Mar/FY
    # column rather than accidentally comparing TTM with the latest FY.
    annual_count = len(values)
    if headers and clean_text(headers[-1]).upper() == "TTM":
        annual_count -= 1

    if annual_count <= 0:
        return None, None

    latest = values[annual_count - 1]
    previous = values[annual_count - 2] if annual_count >= 2 else None
    return latest, previous


def _latest_yoy_quarter(rows, label):
    """Return latest quarter and the same quarter one year earlier."""
    values = _numeric_series(rows.get(label, []))
    if not values:
        return None, None
    latest = values[-1]
    yoy = values[-5] if len(values) >= 5 else None
    return latest, yoy


def _extract_financial_tables(soup, data):
    quarterly = _find_section_table(soup, "Quarterly Results")
    q_rows, q_headers = _table_rows(quarterly)

    annual = _find_section_table(soup, "Profit & Loss")
    annual_rows, annual_headers = _table_rows(annual)

    cashflow = _find_section_table(soup, "Cash Flows")
    cash_rows, cash_headers = _table_rows(cashflow)

    ratios = _find_section_table(soup, "Ratios")
    ratio_rows, ratio_headers = _table_rows(ratios)

    sales, sales_prev = _latest_annual_pair(annual_rows, annual_headers, "Sales")
    profit, profit_prev = _latest_annual_pair(annual_rows, annual_headers, "Net Profit")
    q_sales, q_sales_yoy = _latest_yoy_quarter(q_rows, "Sales")
    q_profit, q_profit_yoy = _latest_yoy_quarter(q_rows, "Net Profit")
    q_eps, _ = _latest_yoy_quarter(q_rows, "EPS in Rs")

    data.update(
        {
            "EPS": data.get("EPS") or q_eps,
            "EPS Latest Quarter": q_eps,
            "Sales Latest": sales,
            "Sales Previous Year": sales_prev,
            "Net Profit Latest": profit,
            "Net Profit Previous Year": profit_prev,
            "Sales Latest Quarter": q_sales,
            "Sales Preceding Year Quarter": q_sales_yoy,
            "Net Profit Latest Quarter": q_profit,
            "Net Profit Preceding Year Quarter": q_profit_yoy,
            "Sales YoY Quarter Growth": (
                (q_sales / q_sales_yoy - 1) * 100
                if q_sales is not None and q_sales_yoy not in (None, 0)
                else None
            ),
            "Profit YoY Quarter Growth": (
                (q_profit / q_profit_yoy - 1) * 100
                if q_profit is not None and q_profit_yoy not in (None, 0)
                else None
            ),
        }
    )

    roce_values = _numeric_series(ratio_rows.get("ROCE %", []))
    roce_values = [v for v in roce_values if v is not None]
    data["ROCE 5Y Average"] = round(sum(roce_values[-5:]) / min(5, len(roce_values)), 2) if roce_values else None

    fcf_values = _numeric_series(cash_rows.get("Free Cash Flow", []))
    fcf_values = [v for v in fcf_values if v is not None]
    last_five_fcf = fcf_values[-5:]
    data["FCF Positive Years 5Y"] = sum(v > 0 for v in last_five_fcf) if last_five_fcf else None

    cfo_op_values = _numeric_series(cash_rows.get("CFO/OP", []))
    cfo_op_values = [v for v in cfo_op_values if v is not None]
    last_five_cfo = cfo_op_values[-5:]
    data["CFO/OP 5Y Average"] = round(sum(last_five_cfo) / len(last_five_cfo), 2) if last_five_cfo else None


def _extract_growth(page_text, data):
    patterns = {
        "Sales Growth 10Y": r"Compounded Sales Growth.*?10 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "Sales Growth 5Y": r"Compounded Sales Growth.*?5 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "Sales Growth 3Y": r"Compounded Sales Growth.*?3 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "Profit Growth 10Y": r"Compounded Profit Growth.*?10 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "Profit Growth 5Y": r"Compounded Profit Growth.*?5 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "Profit Growth 3Y": r"Compounded Profit Growth.*?3 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "ROE 10Y Average": r"Return on Equity.*?10 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "ROE 5Y Average": r"Return on Equity.*?5 Years:\s*([+-]?\d+(?:\.\d+)?%)",
        "ROE 3Y Average": r"Return on Equity.*?3 Years:\s*([+-]?\d+(?:\.\d+)?%)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, page_text, re.DOTALL)
        if match:
            data[key] = match.group(1)


def _extract_promoter_pledge(page_text, data):
    # Pledge is not always present in the shareholding table. If Screener
    # publishes it in the page text, capture it. Otherwise leave it unknown.
    patterns = [
        r"pledged\s+([0-9]+(?:\.[0-9]+)?)%\s+of\s+their\s+holding",
        r"pledged\s+percentage\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%?",
        r"pledged\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)%",
    ]
    for pattern in patterns:
        match = re.search(pattern, page_text, re.I)
        if match:
            data["Pledged Percentage"] = match.group(1)
            return


def _derive_peg(data):
    pe = to_number(data.get("PE"))
    growth = to_number(data.get("Profit Growth 5Y"))
    if pe is None or growth is None or growth <= 0:
        return None
    return round(pe / growth, 2)


def _derive_debt_to_equity(soup, data):
    balance_sheet = _find_section_table(soup, "Balance Sheet")
    rows, _ = _table_rows(balance_sheet)
    borrowings = _numeric_series(rows.get("Borrowings", []))
    equity = _numeric_series(rows.get("Equity Capital", []))
    reserves = _numeric_series(rows.get("Reserves", []))
    if borrowings and equity and reserves:
        b = borrowings[-1]
        e = equity[-1] + reserves[-1]
        if b is not None and e not in (None, 0):
            data["Debt to Equity"] = round(b / e, 3)


def get_company_details(company_url, session=None, timeout=DEFAULT_TIMEOUT):
    """Fetch and parse a Screener.in company page."""
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
        "PEG Ratio": None,
        "Market Cap": None,
        "Market Cap Cr": 0,
        "Book Value": None,
        "Face Value": None,
        "Dividend Yield": None,
        "EPS": None,
        "EPS Latest Quarter": None,
        "Debt to Equity": None,
        "Current Price": None,
        "High Low": None,
        "Promoter Holding": None,
        "Pledged Percentage": None,
        "FII Holding": None,
        "DII Holding": None,
        "Government Holding": None,
        "Public Holding": None,
        "Sales Growth 10Y": None,
        "Sales Growth 3Y": None,
        "Sales Growth 5Y": None,
        "Profit Growth 10Y": None,
        "Profit Growth 3Y": None,
        "Profit Growth 5Y": None,
        "ROE 10Y Average": None,
        "ROE 5Y Average": None,
        "ROE 3Y Average": None,
        "ROCE 5Y Average": None,
        "FCF Positive Years 5Y": None,
        "CFO/OP 5Y Average": None,
        "Sales Latest": None,
        "Sales Previous Year": None,
        "Net Profit Latest": None,
        "Net Profit Previous Year": None,
        "Sales Latest Quarter": None,
        "Sales Preceding Year Quarter": None,
        "Net Profit Latest Quarter": None,
        "Net Profit Preceding Year Quarter": None,
        "Sales YoY Quarter Growth": None,
        "Profit YoY Quarter Growth": None,
    }

    _extract_top_ratios(soup, data)
    _extract_shareholding(soup, data)
    page_text = clean_text(soup.get_text(" ")) or ""
    _extract_growth(page_text, data)
    _extract_promoter_pledge(page_text, data)
    _extract_financial_tables(soup, data)
    _derive_debt_to_equity(soup, data)
    data["PEG Ratio"] = _derive_peg(data)
    return data
