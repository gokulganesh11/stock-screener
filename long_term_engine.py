"""Long-horizon sector screening engine.

The strict filter is intentionally separate from the ranking score. A company
must pass every user-required condition before it can appear in the top-5
long-term shortlist. Missing data is treated as unverified, never as a pass.
"""
from io import BytesIO
import pandas as pd
import requests
from company_scraper import get_company_details
from score import evaluate_multibagger_screen, calculate_long_term_score
from screener import get_sector_stocks

DEFAULT_TIMEOUT = 20

SECTORS = {
    "Capital Markets": "https://www.screener.in/market/IN05/IN0501/IN050103/",
}

REQUIRED_FIELDS = [
    "ROE", "ROCE", "PE", "PEG Ratio", "Debt to Equity", "EPS",
    "Promoter Holding", "Pledged Percentage", "Sales Growth 5Y", "Profit Growth 5Y",
    "Sales Growth 3Y", "Profit Growth 3Y", "Sales Latest", "Sales Previous Year",
    "Net Profit Latest", "Net Profit Previous Year", "Sales Latest Quarter",
    "Net Profit Latest Quarter",
]

DISPLAY_FIELDS = REQUIRED_FIELDS + [
    "Sales Growth 10Y", "Profit Growth 10Y", "ROE 5Y Average", "ROCE 5Y Average",
    "FCF Positive Years 5Y", "CFO/OP 5Y Average", "Sales YoY Quarter Growth",
    "Profit YoY Quarter Growth", "Market Cap", "Dividend Yield", "FII Holding",
]


def _confidence(data):
    available = sum(data.get(key) is not None for key in REQUIRED_FIELDS)
    pct = round(available / len(REQUIRED_FIELDS) * 100)
    return pct, "High" if pct >= 95 else "Medium" if pct >= 75 else "Low"


def analyze_long_term_sector(url, progress_callback=None, timeout=DEFAULT_TIMEOUT):
    source_df = get_sector_stocks(url)
    if source_df is None or source_df.empty:
        raise ValueError("No companies were found for this sector.")

    session = requests.Session()
    rows, failures = [], []

    for position, (_, source_row) in enumerate(source_df.iterrows(), 1):
        company = str(source_row.get("Company", "Unknown")).strip()
        company_url = str(source_row.get("Company URL", "")).strip()
        try:
            if not company_url or company_url.lower() in {"none", "nan"}:
                raise ValueError("Company URL is missing")
            data = get_company_details(company_url, session=session, timeout=timeout)
            screen = evaluate_multibagger_screen(data)
            long_score, reasons = calculate_long_term_score(data)
            completeness, confidence = _confidence(data)
            rows.append({
                "Company": company,
                "Company URL": company_url,
                "Strict Screen": "PASS" if screen["Strict Screen Pass"] else "FAIL",
                "Checks": f'{screen["Screen Checks Passed"]}/{screen["Screen Checks Total"]}',
                "Long-Term Score": long_score,
                "Confidence": confidence,
                "Data Completeness": completeness,
                "Reasons": "; ".join(reasons),
                "Failed Conditions": "; ".join(screen["Screen Failures"]),
                **{key: data.get(key) for key in DISPLAY_FIELDS},
            })
        except Exception as exc:
            failures.append({"Company": company, "Company URL": company_url, "Error": str(exc)})
        if progress_callback:
            progress_callback(position / len(source_df))

    result = pd.DataFrame(rows)
    if not result.empty:
        result["Strict Sort"] = result["Strict Screen"].eq("PASS").astype(int)
        result = result.sort_values(["Strict Sort", "Long-Term Score", "Data Completeness"], ascending=[False, False, False]).drop(columns=["Strict Sort"]).reset_index(drop=True)
        result.insert(0, "Rank", range(1, len(result) + 1))
        result["Multibagger Rank"] = 0
        qualified = result["Strict Screen"].eq("PASS")
        result.loc[qualified, "Multibagger Rank"] = range(1, int(qualified.sum()) + 1)

    return result, pd.DataFrame(failures), source_df


def dataframe_to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    return output.getvalue()
