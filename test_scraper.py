from company_scraper import get_company_details
from score import calculate_stock_score

data = get_company_details(
    "https://www.screener.in/company/BSE/consolidated/"
)

score = calculate_stock_score(data)

print("\nStock Score:", score)

print(data)