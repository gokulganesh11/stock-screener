import streamlit as st
import pandas as pd
from io import BytesIO

from sector_urls import SECTOR_URLS
from sector_analyzer import analyze_all_sectors
from screener import get_sector_stocks
from company_scraper import get_company_details
from score import calculate_stock_score
from history_manager import save_sector_history

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Live Sector Comparison",
    page_icon="📊",
    layout="wide"
)

# ==================================================
# LIVE DATA
# ==================================================

from history_manager import save_sector_history

with st.spinner(
    "Analyzing sectors..."
):

    df = analyze_all_sectors(
        SECTOR_URLS
    )

save_sector_history(df)

if df.empty:

    st.error(
        "No sector data available."
    )

    st.stop()

# ==================================================
# HELPERS
# ==================================================

def get_priority(score):

    if score >= 12:
        return "High"

    elif score >= 10:
        return "Medium"

    return "Low"


def get_sector_top_stocks(
    sector_name
):

    if sector_name not in SECTOR_URLS:

        return pd.DataFrame()

    try:

        sector_df = get_sector_stocks(
            SECTOR_URLS[sector_name]
        )

        return sector_df.head(10)

    except Exception:

        return pd.DataFrame()


def get_stock_analysis(
    company_url
):

    try:

        details = get_company_details(
            company_url
        )

        score_data = (
            calculate_stock_score(
                details
            )
        )

        return details, score_data

    except Exception:

        return None, None


df["Research Priority"] = (
    df["Average Score"]
    .apply(get_priority)
)

# ==================================================
# HEADER
# ==================================================

st.title(
    "📊 Live Sector Comparison Dashboard"
)

st.caption(
    "Compare sector strength, opportunity level and leadership across the market."
)

# ==================================================
# MARKET OVERVIEW
# ==================================================

st.subheader(
    "📈 Market Overview"
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Sectors Compared",
    len(df)
)

c2.metric(
    "Best Sector",
    df.iloc[0]["Sector"]
)

c3.metric(
    "Best Stock",
    df.iloc[0]["Top Stock"]
)

c4.metric(
    "Highest Avg Score",
    round(
        df.iloc[0]["Average Score"],
        2
    )
)

c5.metric(
    "Companies Analyzed",
    int(
        df["Companies Analyzed"].sum()
    )
)

# ==================================================
# LEADERBOARD
# ==================================================

st.subheader(
    "🏆 Sector Leaderboard"
)

cols = st.columns(
    min(
        len(df),
        5
    )
)

for idx, row in enumerate(
    df.head(5).itertuples()
):

    cols[idx].metric(
        row.Sector,
        row._3
    )

# ==================================================
# SECTOR RANKINGS
# ==================================================

st.subheader(
    "📋 Sector Rankings"
)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# SECTOR DRILLDOWN
# ==================================================

st.subheader(
    "🔎 Sector Drilldown"
)

selected_sector = st.selectbox(
    "Select Sector",
    df["Sector"]
)

top_stocks_df = get_sector_top_stocks(
    selected_sector
)

if not top_stocks_df.empty:

    st.success(
        f"Top companies in {selected_sector}"
    )

    st.dataframe(
        top_stocks_df,
        use_container_width=True
    )

else:

    st.warning(
        "No company data available."
    )

# ==================================================
# STOCK DRILLDOWN
# ==================================================

if (
    not top_stocks_df.empty
    and "Company" in top_stocks_df.columns
    and "Company URL" in top_stocks_df.columns
):

    st.subheader(
        "📊 Stock Drilldown"
    )

    selected_company = st.selectbox(
        "Select Company",
        top_stocks_df["Company"]
    )

    company_row = top_stocks_df[
        top_stocks_df["Company"]
        == selected_company
    ].iloc[0]

    company_url = company_row[
        "Company URL"
    ]

    details, score_data = (
        get_stock_analysis(
            company_url
        )
    )

    if details and score_data:

        st.success(
            f"""
Company: {selected_company}

Total Score: {score_data['Total Score']}
"""
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Quality",
            score_data[
                "Quality Score"
            ]
        )

        c2.metric(
            "Growth",
            score_data[
                "Growth Score"
            ]
        )

        c3.metric(
            "Valuation",
            score_data[
                "Valuation Score"
            ]
        )

        c4.metric(
            "Ownership",
            score_data[
                "Ownership Score"
            ]
        )

        c5.metric(
            "Risk",
            score_data[
                "Risk Score"
            ]
        )

        st.subheader(
            "📈 Financial Metrics"
        )

        f1, f2, f3 = st.columns(3)

        f1.metric(
            "ROE",
            details["ROE"]
        )

        f2.metric(
            "ROCE",
            details["ROCE"]
        )

        f3.metric(
            "PE",
            details["PE"]
        )

        g1, g2 = st.columns(2)

        with g1:

            st.markdown(
                "### Growth Metrics"
            )

            st.write(
                f"Sales Growth 3Y: {details['Sales Growth 3Y']}"
            )

            st.write(
                f"Sales Growth 5Y: {details['Sales Growth 5Y']}"
            )

            st.write(
                f"Profit Growth 3Y: {details['Profit Growth 3Y']}"
            )

            st.write(
                f"Profit Growth 5Y: {details['Profit Growth 5Y']}"
            )

        with g2:

            st.markdown(
                "### Ownership Metrics"
            )

            st.write(
                f"Promoter Holding: {details['Promoter Holding']}"
            )

            st.write(
                f"FII Holding: {details['FII Holding']}"
            )

            st.write(
                f"Dividend Yield: {details['Dividend Yield']}"
            )

            st.write(
                f"Market Cap: {details['Market Cap']}"
            )

# ==================================================
# BEST VS WEAKEST
# ==================================================

best_sector = df.iloc[0]
worst_sector = df.iloc[-1]

st.subheader(
    "⚔️ Best vs Weakest Sector"
)

col1, col2 = st.columns(2)

with col1:

    st.success(
        f"""
### 🥇 Best Sector

Sector: {best_sector['Sector']}

Average Score: {best_sector['Average Score']}

Strong Buy Count: {best_sector['Strong Buy Count']}

Top Stock: {best_sector['Top Stock']}
"""
    )

with col2:

    st.error(
        f"""
### 📉 Weakest Sector

Sector: {worst_sector['Sector']}

Average Score: {worst_sector['Average Score']}

Strong Buy Count: {worst_sector['Strong Buy Count']}

Top Stock: {worst_sector['Top Stock']}
"""
    )

# ==================================================
# EXPORT
# ==================================================

st.subheader(
    "📥 Export Sector Rankings"
)

output = BytesIO()

df.to_excel(
    output,
    index=False,
    engine="openpyxl"
)

st.download_button(
    label="📥 Download Excel",
    data=output.getvalue(),
    file_name="sector_rankings.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

csv = df.to_csv(
    index=False
)

st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name="sector_rankings.csv",
    mime="text/csv"
)

# ==================================================
# FINAL RECOMMENDATION
# ==================================================

st.subheader(
    "🚀 Strategic Recommendation"
)

st.success(
    """
1. Start stock discovery from top-ranked sectors.

2. Prioritize sectors with higher average scores.

3. Focus on sectors with more Strong Buy opportunities.

4. Use Stock Drilldown before making investment decisions.

5. Review rankings periodically to identify sector rotation.
"""
)