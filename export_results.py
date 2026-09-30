import pandas as pd

from mvp_ranker import results

df = pd.DataFrame(results)

df.to_excel(
    "stock_ranking.xlsx",
    index=False
)

print("Excel exported")