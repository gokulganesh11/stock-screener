from company_scraper import get_company_details
from score import calculate_stock_score


def get_recommendation(score):

    if score >= 13:
        return "STRONG BUY"

    elif score >= 10:
        return "BUY"

    elif score >= 7:
        return "HOLD"

    else:
        return "AVOID"


COMPANIES = [
    {
        "Company": "BSE",
        "URL": "https://www.screener.in/company/BSE/consolidated/"
    },
    {
        "Company": "MCX",
        "URL": "https://www.screener.in/company/MCX/consolidated/"
    },
    {
        "Company": "ICICI AMC",
        "URL": "https://www.screener.in/company/ICICIAMC/"
    }
]


results = []

for company in COMPANIES:

    print(
        f"\nAnalyzing {company['Company']}"
    )

    details = get_company_details(
        company["URL"]
    )

    score = calculate_stock_score(
        details
    )

    recommendation = get_recommendation(
        score
    )

    results.append(
        {
            "Company": company["Company"],
            "Score": score,
            "Recommendation": recommendation,
            "ROE": details["ROE"],
            "ROCE": details["ROCE"],
            "PE": details["PE"],
            "Market Cap": details["Market Cap"],
            "Market Cap Cr": details["Market Cap Cr"],
            "Dividend Yield": details["Dividend Yield"],
            "FII Holding": details["FII Holding"],
            "Promoter Holding": details["Promoter Holding"],
            "Sales Growth 3Y": details["Sales Growth 3Y"],
            "Sales Growth 5Y": details["Sales Growth 5Y"],
            "Profit Growth 3Y": details["Profit Growth 3Y"],
            "Profit Growth 5Y": details["Profit Growth 5Y"]
        }
    )

results.sort(
    key=lambda x: x["Score"],
    reverse=True
)

print("\n")
print("=" * 80)
print("TOP STOCKS")
print("=" * 80)

for stock in results:

    print(
        f"""
Company            : {stock['Company']}
Score              : {stock['Score']}
Recommendation     : {stock['Recommendation']}
ROE                : {stock['ROE']}
ROCE               : {stock['ROCE']}
PE                 : {stock['PE']}
Market Cap         : {stock['Market Cap']}
Dividend Yield     : {stock['Dividend Yield']}
FII Holding        : {stock['FII Holding']}
Promoter Holding   : {stock['Promoter Holding']}
Sales Growth 3Y    : {stock['Sales Growth 3Y']}
Sales Growth 5Y    : {stock['Sales Growth 5Y']}
Profit Growth 3Y   : {stock['Profit Growth 3Y']}
Profit Growth 5Y   : {stock['Profit Growth 5Y']}
"""
    )

print("=" * 80)