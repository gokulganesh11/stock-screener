from screener import get_sector_stocks

df = get_sector_stocks(
    "https://www.screener.in/market/IN05/IN0501/IN050103/"
)

print(
    df[
        ["Company URL"]
    ].head(10)
)

print(df.head())
print(df.columns)