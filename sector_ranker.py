import re

from screener import get_sector_stocks
from company_scraper import get_company_details
from score import calculate_stock_score


def rank_sector_stocks(sector_url):

    df = get_sector_stocks(
        sector_url
    )

    ranked_stocks = []

    for _, row in df.iterrows():

        try:

            company_name = str(
                row["Company"]
            )

            company_url = str(
                row["Company URL"]
            )

            match = re.search(
                r'https://www\.screener\.in/company/[^"\'> ]+',
                company_url
            )

            if match:
                company_url = match.group(0)
            else:
                continue

            print(
                f"\nAnalyzing: {company_name}"
            )

            print(
                f"URL: {company_url}"
            )

            details = get_company_details(
                company_url
            )

            score = calculate_stock_score(
                details
            )

            ranked_stocks.append(
                {
                    "Company Name": company_name,
                    "Company URL": company_url,
                    "Score": score,
                    "ROE": details["ROE"],
                    "ROCE": details["ROCE"],
                    "PE": details["PE"],
                    "Sales Growth 3Y": details["Sales Growth 3Y"],
                    "Sales Growth 5Y": details["Sales Growth 5Y"],
                    "Profit Growth 3Y": details["Profit Growth 3Y"],
                    "Profit Growth 5Y": details["Profit Growth 5Y"]
                }
            )

        except Exception as e:

            print(
                f"Error processing {company_name}: {e}"
            )

    ranked_stocks.sort(
        key=lambda x: x["Score"],
        reverse=True
    )

    return ranked_stocks


if __name__ == "__main__":

    results = rank_sector_stocks(
        "https://www.screener.in/market/IN05/IN0501/IN050103/"
    )

    print("\nTOP STOCKS\n")

    for stock in results[:10]:

        print(
            f"{stock['Company Name']} "
            f"| Score: {stock['Score']} "
            f"| ROE: {stock['ROE']} "
            f"| ROCE: {stock['ROCE']} "
            f"| PE: {stock['PE']}"
        )
