"""Core sector research workflow shared by the Streamlit pages."""

from io import BytesIO

import pandas as pd
import requests

from company_scraper import get_company_details
from score import calculate_stock_score
from screener import get_sector_stocks

DEFAULT_TIMEOUT = 20

SECTORS = {
    "Capital Markets": "https://www.screener.in/market/IN05/IN0501/IN050103/",
}


def recommendation(score):
    """Compatibility label for the existing UI; not an investment prediction."""
    if score >= 14:
        return "High score"
    if score >= 10:
        return "Positive score"
    if score >= 7:
        return "Middle score"
    return "Low score"


def analyze_sector(url, progress_callback=None, timeout=DEFAULT_TIMEOUT):
    """Analyze all companies returned by a sector page.

    Returns (results_df, failures, source_df). Failures are retained so the UI
    can distinguish unavailable data from genuinely low-scoring companies.
    """
    if not str(url).strip():
        raise ValueError("A Screener.in sector URL is required.")

    source_df = get_sector_stocks(url)
    if source_df is None or source_df.empty:
        raise ValueError("No companies were found for this sector.")

    session = requests.Session()
    results = []
    failures = []
    total = len(source_df)

    for position, (_, row) in enumerate(source_df.iterrows(), start=1):
        company = str(row.get("Company", "Unknown")).strip()
        company_url = str(row.get("Company URL", "")).strip()

        try:
            if not company_url or company_url.lower() in {"none", "nan"}:
                raise ValueError("Company URL is missing")

            details = get_company_details(
                company_url,
                session=session,
                timeout=timeout,
            )
            scored = calculate_stock_score(details)

            result = {
                "Company": company,
                "Company URL": company_url,
                "Total Score": scored["Total Score"],
                "Recommendation": recommendation(scored["Total Score"]),
                "Confidence": scored["Confidence"],
                "Data Completeness": scored["Data Completeness"],
                "Quality Score": scored["Quality Score"],
                "Growth Score": scored["Growth Score"],
                "Valuation Score": scored["Valuation Score"],
                "Ownership Score": scored["Ownership Score"],
                "Risk Score": scored["Risk Score"],
                "Reasons": "; ".join(scored["Reasons"]),
                "Warnings": "; ".join(scored["Warnings"]),
            }
            result.update({
                key: details.get(key)
                for key in [
                    "ROE", "ROCE", "PE", "Market Cap", "Market Cap Cr",
                    "Dividend Yield", "Promoter Holding", "FII Holding",
                    "Sales Growth 3Y", "Sales Growth 5Y",
                    "Profit Growth 3Y", "Profit Growth 5Y",
                ]
            })
            results.append(result)
        except Exception as exc:
            failures.append({
                "Company": company,
                "Company URL": company_url,
                "Error": str(exc),
            })

        if progress_callback:
            progress_callback(position / total)

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(
            ["Total Score", "Data Completeness"],
            ascending=[False, False],
        ).reset_index(drop=True)
        result_df.insert(0, "Rank", range(1, len(result_df) + 1))

    return result_df, pd.DataFrame(failures), source_df


def dataframe_to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    return output.getvalue()
