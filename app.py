import streamlit as st
import pandas as pd
from io import BytesIO

from screener import get_sector_stocks
from company_scraper import get_company_details
from score import calculate_stock_score

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Multibagger Sector Screener",
    page_icon="📈",
    layout="wide"
)

# ==================================================
# HELPERS
# ==================================================

def get_recommendation(score):

    if score >= 14:
        return "STRONG BUY"

    elif score >= 10:
        return "BUY"

    elif score >= 7:
        return "HOLD"

    else:
        return "AVOID"


# ==================================================
# HEADER
# ==================================================

st.title("📈 Multibagger Sector Screener")

st.markdown(
    """
Analyze an entire sector, score stocks automatically,
and discover potential multibagger opportunities.
"""
)

# ==================================================
# SECTORS
# ==================================================

SECTORS = {

    "Capital Markets":
        "https://www.screener.in/market/IN05/IN0501/IN050103/",

    "Custom URL":
        ""
}

selected_sector = st.selectbox(
    "Select Sector",
    list(SECTORS.keys())
)

if selected_sector == "Custom URL":

    sector_url = st.text_input(
        "Enter Screener Sector URL"
    )

else:

    sector_url = SECTORS[selected_sector]

    st.text_input(
        "Sector URL",
        sector_url,
        disabled=True
    )

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("⚙️ Settings")

top_n = st.sidebar.slider(
    "Top Stocks To Display",
    5,
    25,
    10
)

show_raw = st.sidebar.checkbox(
    "Show Raw Sector Data"
)

# ==================================================
# ANALYZE
# ==================================================

if st.button("🚀 Analyze Sector"):

    if not sector_url:

        st.warning(
            "Please provide a valid sector URL."
        )

        st.stop()

    try:

        with st.spinner(
            "Downloading sector and analyzing companies..."
        ):

            sector_df = get_sector_stocks(
                sector_url
            )

            results = []

            progress = st.progress(0)

            total_rows = len(sector_df)

            for idx, row in sector_df.iterrows():

                try:

                    company_name = str(
                        row["Company"]
                    )

                    company_url = str(
                        row["Company URL"]
                    )

                    if company_url == "None":
                        continue

                    if company_url == "nan":
                        continue

                    details = get_company_details(
                        company_url
                    )

                    score = calculate_stock_score(
                        details
                    )

                    recommendation = (
                        get_recommendation(
                            score
                        )
                    )

                    results.append(
                        {
                            "Company": company_name,
                            "Score": score,
                            "Recommendation": recommendation,
                            "ROE": details["ROE"],
                            "ROCE": details["ROCE"],
                            "PE": details["PE"],
                            "Market Cap": details["Market Cap"],
                            "Dividend Yield": details["Dividend Yield"],
                            "Promoter Holding": details["Promoter Holding"],
                            "FII Holding": details["FII Holding"],
                            "Sales Growth 3Y": details["Sales Growth 3Y"],
                            "Sales Growth 5Y": details["Sales Growth 5Y"],
                            "Profit Growth 3Y": details["Profit Growth 3Y"],
                            "Profit Growth 5Y": details["Profit Growth 5Y"]
                        }
                    )

                except Exception:
                    pass

                progress.progress(
                    (idx + 1) / total_rows
                )

            result_df = pd.DataFrame(
                results
            )

            result_df = result_df.sort_values(
                by="Score",
                ascending=False
            )

        # ==========================================
        # KPIs
        # ==========================================

        st.subheader(
            "📊 Overview"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Companies Analyzed",
            len(result_df)
        )

        c2.metric(
            "Top Score",
            result_df["Score"].max()
        )

        c3.metric(
            "Strong Buy Count",
            len(
                result_df[
                    result_df[
                        "Recommendation"
                    ] == "STRONG BUY"
                ]
            )
        )

        # ==========================================
        # TOP STOCKS
        # ==========================================

        st.subheader(
            "🏆 Top Ranked Stocks"
        )
        
        st.dataframe(
            result_df.head(top_n),
            use_container_width=True
        )

        # ==========================================
        # STRONG BUY
        # ==========================================

        strong_buy = result_df[
            result_df["Recommendation"]
            == "STRONG BUY"
        ]

        if not strong_buy.empty:

            st.subheader(
                "🔥 Strong Buy Candidates"
            )

            st.dataframe(
                strong_buy,
                use_container_width=True
            )

            cols = st.columns(
                min(len(strong_buy), 4)
            )

            for idx, (_, row) in enumerate(
                strong_buy.head(4).iterrows()
            ):
                cols[idx].metric(
                    row["Company"],
                    row["Score"]
                )

        # ==========================================
        # TOP PICK
        # ==========================================

        st.subheader(
            "⭐ Best Opportunity"
        )

        best_stock = result_df.iloc[0]

        st.success(
            f"""
        Company: {best_stock['Company']}

        Score: {best_stock['Score']}

        Recommendation: {best_stock['Recommendation']}

        ROE: {best_stock['ROE']}

        ROCE: {best_stock['ROCE']}

        PE: {best_stock['PE']}
        """
        )

        st.subheader(
            "🔎 Company Analysis"
        )

        selected_company = st.selectbox(
            "Select Company",
            result_df["Company"]
        )

        selected_row = result_df[
            result_df["Company"] == selected_company
        ].iloc[0]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "ROE",
            selected_row["ROE"]
        )

        c2.metric(
            "ROCE",
            selected_row["ROCE"]
        )

        c3.metric(
            "PE",
            selected_row["PE"]
        )

        st.dataframe(
            pd.DataFrame([selected_row]),
            use_container_width=True
        )


        # ==========================================
        # DOWNLOAD EXCEL
        # ==========================================
        
        st.subheader(
            "🏥 Sector Health"
        )

        sector_avg = round(
            result_df["Score"].mean(),
            2
        )

        if sector_avg >= 12:

            st.success(
                f"Sector Health Score: {sector_avg} (Strong)"
            )

        elif sector_avg >= 8:

            st.warning(
                f"Sector Health Score: {sector_avg} (Average)"
            )

        else:

            st.error(
                f"Sector Health Score: {sector_avg} (Weak)"
            )


        st.subheader(
            "📥 Download Results"
        )

        output = BytesIO()

        result_df.to_excel(
            output,
            index=False,
            engine="openpyxl"
        )

        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name="sector_ranking.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        csv = result_df.to_csv(
            index=False
        )

        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="sector_ranking.csv",
            mime="text/csv"
        )

        # ==========================================
        # RAW DATA
        # ==========================================

        if show_raw:

            st.subheader(
                "Raw Sector Table"
            )

            st.dataframe(
                sector_df,
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"Error: {str(e)}"
        )