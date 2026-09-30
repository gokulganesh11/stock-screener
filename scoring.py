import pandas as pd


def apply_filter(
    df,
    max_pe=50,
    min_roce=10,
    min_market_cap=500,
    min_profit_growth=0,
    min_sales_growth=0
):

    df = df.copy()

    numeric_cols = [
        "P/E",
        "Mar Cap  Rs.Cr.",
        "Qtr Profit Var  %",
        "Qtr Sales Var  %",
        "ROCE  %"
    ]

    for col in numeric_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    filtered_df = df[
        (df["P/E"] <= max_pe)
        & (df["ROCE  %"] >= min_roce)
        & (df["Mar Cap  Rs.Cr."] >= min_market_cap)
        & (df["Qtr Profit Var  %"] >= min_profit_growth)
        & (df["Qtr Sales Var  %"] >= min_sales_growth)
    ].copy()

    filtered_df["Score"] = (
        (filtered_df["ROCE  %"] * 0.50)
        + (filtered_df["Qtr Profit Var  %"] * 0.20)
        + (filtered_df["Qtr Sales Var  %"] * 0.15)
        + ((50 - filtered_df["P/E"]) * 0.10)
        + ((10000 / filtered_df["Mar Cap  Rs.Cr."]) * 5)
    )

    filtered_df["Score"] = (
        filtered_df["Score"]
        .round(2)
    )

    # Potential

    filtered_df["Potential"] = "Low"

    filtered_df.loc[
        filtered_df["Score"] >= 60,
        "Potential"
    ] = "High"

    filtered_df.loc[
        (filtered_df["Score"] >= 40)
        & (filtered_df["Score"] < 60),
        "Potential"
    ] = "Medium"

    # Recommendation

    filtered_df["Recommendation"] = "Watch"

    filtered_df.loc[
        filtered_df["Score"] >= 60,
        "Recommendation"
    ] = "Strong Buy"

    filtered_df.loc[
        (filtered_df["Score"] >= 40)
        & (filtered_df["Score"] < 60),
        "Recommendation"
    ] = "Buy"

    # Risk

    filtered_df["Risk"] = "Low"

    filtered_df.loc[
        filtered_df["P/E"] > 40,
        "Risk"
    ] = "High"

    filtered_df.loc[
        (
            (filtered_df["P/E"] > 25)
            & (filtered_df["P/E"] <= 40)
        ),
        "Risk"
    ] = "Medium"

    # Reason

    def get_reason(row):

        reasons = []

        if row["ROCE  %"] > 40:
            reasons.append("High ROCE")

        if row["Qtr Profit Var  %"] > 30:
            reasons.append("Strong Profit Growth")

        if row["Qtr Sales Var  %"] > 20:
            reasons.append("Strong Sales Growth")

        if row["P/E"] < 25:
            reasons.append("Reasonable Valuation")

        return " + ".join(reasons)

    filtered_df["Reason"] = filtered_df.apply(
        get_reason,
        axis=1
    )

    filtered_df = filtered_df.sort_values(
        by="Score",
        ascending=False
    )

    return filtered_df