from screener import get_sector_stocks
from company_scraper import get_company_details
from score import calculate_stock_score


def get_recommendation(score):

    if score >= 14:
        return "STRONG BUY"

    elif score >= 10:
        return "BUY"

    elif score >= 7:
        return "HOLD"

    else:
        return "AVOID"


SECTOR_URL = (
    "https://www.screener.in/market/IN05/IN0501/IN050103/"
)

df = get_sector_stocks(
    SECTOR_URL
)

results = []

for _, row in df.iterrows():

    try:

        company_name = row["Company"]

        company_url = row["Company URL"]

        print(
            f"\nAnalyzing {company_name}"
        )

        details = get_company_details(
            company_url
        )

        score = calculate_stock_score(
            details
        )

        recommendation = get_recommendation(
            score
        )

        results.append(
            {
                "Company": company_name,
                "Score": score,
                "Recommendation": recommendation,
                "ROE": details["ROE"],
                "ROCE": details["ROCE"],
                "PE": details["PE"],
                "Market Cap": details["Market Cap"]
            }
        )

    except Exception as e:

        print(
            f"Error: {company_name}: {e}"
        )

results.sort(
    key=lambda x: x["Score"],
    reverse=True
)

print("\n")
print("=" * 80)
print("TOP FINANCIAL SERVICES STOCKS")
print("=" * 80)

for index, stock in enumerate(
    results[:10],
    start=1
):

    print(
        f"{index}. "
        f"{stock['Company']} "
        f"| Score: {stock['Score']} "
        f"| {stock['Recommendation']}"
    )