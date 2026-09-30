import pandas as pd

from full_sector_ranker import results

df = pd.DataFrame(results)

df.to_excel(
    "financial_services_ranking.xlsx",
    index=False
)

print(
    "Excel report generated"
)