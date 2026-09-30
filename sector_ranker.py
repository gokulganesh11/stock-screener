"""Legacy-compatible sector ranker.

The main Streamlit app uses long_term_engine.py. This module remains for older
scripts/tests and now consumes the dictionary returned by calculate_stock_score.
"""
import re

from screener import get_sector_stocks
from company_scraper import get_company_details
from score import calculate_stock_score


def rank_sector_stocks(sector_url):
    df = get_sector_stocks(sector_url)
    ranked_stocks = []

    for _, row in df.iterrows():
        company_name = str(row.get("Company", "Unknown"))
        try:
            company_url = str(row.get("Company URL", ""))
            match = re.search(r'https://www\\.screener\\.in/company/[^"\'> ]+', company_url)
            if match:
                company_url = match.group(0)
            else:
                continue

            print(f"\nAnalyzing: {company_name}")
            print(f"URL: {company_url}")

            details = get_company_details(company_url)
            score_result = calculate_stock_score(details)
            score = score_result["Total Score"]

            ranked_stocks.append({
                "Company Name": company_name,
                "Company URL": company_url,
                "Score": score,
                "ROE": details.get("ROE"),
                "ROCE": details.get("ROCE"),
                "PE": details.get("PE"),
                "Sales Growth 3Y": details.get("Sales Growth 3Y"),
                "Sales Growth 5Y": details.get("Sales Growth 5Y"),
                "Profit Growth 3Y": details.get("Profit Growth 3Y"),
                "Profit Growth 5Y": details.get("Profit Growth 5Y"),
            })
        except Exception as exc:
            print(f"Error processing {company_name}: {exc}")

    ranked_stocks.sort(key=lambda x: x["Score"], reverse=True)
    return ranked_stocks


if __name__ == "__main__":
    results = rank_sector_stocks("https://www.screener.in/market/IN05/IN0501/IN050103/")
    print("\nTOP STOCKS\n")
    for stock in results[:10]:
        print(
            f"{stock['Company Name']} | Score: {stock['Score']} "
            f"| ROE: {stock['ROE']} | ROCE: {stock['ROCE']} | PE: {stock['PE']}"
        )
