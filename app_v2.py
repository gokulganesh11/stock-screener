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
    page_title="Multibagger Sector Screener V2",
    page_icon="📈",
    layout="wide"
)

# ==================================================
# HELPERS
# ==================================================

def get_recommendation(score):

    if score >= 14:
        return "🟢 STRONG BUY"

    elif score >= 10:
        return "🟡 BUY"

    elif score >= 7:
        return "🟠 HOLD"

    return "🔴 AVOID"


@st.cache_data(ttl=3600)
def cached_sector_stocks(url):

    return get_sector_stocks(url)


# ==================================================
# HEADER
# ==================================================

st.title("📈 Multibagger Sector Screener V2")

st.markdown(
    """
Advanced stock ranking dashboard with score breakdown,
recommendations and sector analytics.
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
        value=sector_url,
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

    try:

        with st.spinner(
            "Analyzing companies..."
        ):

            sector_df = cached_sector_stocks(
                sector_url
            )

            results = []

            progress = st.progress(0)

            total_rows = len(
                sector_df
            )

            for idx, row in sector_df.iterrows():

                try:

                    company_name = str(
                        row["Company"]
                    )

                    company_url = str(
                        row["Company URL"]
                    )

                    if company_url in [
                        "None",
                        "nan"
                    ]:
                        continue

                    details = get_company_details(
                        company_url
                    )

                    score_data = (
                        calculate_stock_score(
                            details
                        )
                    )

                    total_score = (
                        score_data[
                            "Total Score"
                        ]
                    )

                    results.append(
                        {
                            "Company": company_name,

                            "Total Score":
                                total_score,

                            "Recommendation":
                                get_recommendation(
                                    total_score
                                ),

                            "Quality Score":
                                score_data[
                                    "Quality Score"
                                ],

                            "Growth Score":
                                score_data[
                                    "Growth Score"
                                ],

                            "Valuation Score":
                                score_data[
                                    "Valuation Score"
                                ],

                            "Ownership Score":
                                score_data[
                                    "Ownership Score"
                                ],

                            "Risk Score":
                                score_data[
                                    "Risk Score"
                                ],

                            "ROE":
                                details["ROE"],

                            "ROCE":
                                details["ROCE"],

                            "PE":
                                details["PE"],

                            "Market Cap":
                                details["Market Cap"],

                            "Dividend Yield":
                                details[
                                    "Dividend Yield"
                                ],

                            "Promoter Holding":
                                details[
                                    "Promoter Holding"
                                ],

                            "FII Holding":
                                details[
                                    "FII Holding"
                                ],

                            "Sales Growth 3Y":
                                details[
                                    "Sales Growth 3Y"
                                ],

                            "Sales Growth 5Y":
                                details[
                                    "Sales Growth 5Y"
                                ],

                            "Profit Growth 3Y":
                                details[
                                    "Profit Growth 3Y"
                                ],

                            "Profit Growth 5Y":
                                details[
                                    "Profit Growth 5Y"
                                ]
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
                "Total Score",
                ascending=False
            )

            result_df.insert(
                0,
                "Rank",
                range(
                    1,
                    len(result_df) + 1
                )
            )

        # ==================================================
        # OVERVIEW
        # ==================================================

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
            result_df[
                "Total Score"
            ].max()
        )

        c3.metric(
            "Strong Buy Count",
            len(
                result_df[
                    result_df[
                        "Recommendation"
                    ]
                    == "🟢 STRONG BUY"
                ]
            )
        )

        # ==================================================
        # TOP RANKINGS
        # ==================================================

        st.subheader(
            "🏆 Top Ranked Stocks"
        )

        st.dataframe(
            result_df.head(top_n),
            use_container_width=True
        )

        # ==================================================
        # STRONG BUY
        # ==================================================

        strong_buy = result_df[
            result_df[
                "Recommendation"
            ]
            == "🟢 STRONG BUY"
        ]

        if not strong_buy.empty:

            st.subheader(
                "🔥 Strong Buy Candidates"
            )

            st.dataframe(
                strong_buy,
                use_container_width=True
            )

        # ==================================================
        # BEST OPPORTUNITY
        # ==================================================

        best_stock = result_df.iloc[0]

        st.subheader(
            "⭐ Best Opportunity"
        )

        st.success(
            f"""
Company: {best_stock['Company']}

Rank: #{best_stock['Rank']}

Recommendation: {best_stock['Recommendation']}

Total Score: {best_stock['Total Score']}
"""
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Quality",
            best_stock[
                "Quality Score"
            ]
        )

        c2.metric(
            "Growth",
            best_stock[
                "Growth Score"
            ]
        )

        c3.metric(
            "Valuation",
            best_stock[
                "Valuation Score"
            ]
        )

        c4.metric(
            "Ownership",
            best_stock[
                "Ownership Score"
            ]
        )

        c5.metric(
            "Risk",
            best_stock[
                "Risk Score"
            ]
        )

        # ==================================================
        # COMPANY ANALYSIS
        # ==================================================

        st.subheader(
            "🔎 Company Analysis"
        )

        selected_company = (
            st.selectbox(
                "Select Company",
                result_df[
                    "Company"
                ]
            )
        )

        selected_row = result_df[
            result_df[
                "Company"
            ]
            == selected_company
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

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Quality",
            selected_row[
                "Quality Score"
            ]
        )

        c2.metric(
            "Growth",
            selected_row[
                "Growth Score"
            ]
        )

        c3.metric(
            "Valuation",
            selected_row[
                "Valuation Score"
            ]
        )

        c4.metric(
            "Ownership",
            selected_row[
                "Ownership Score"
            ]
        )

        c5.metric(
            "Risk",
            selected_row[
                "Risk Score"
            ]
        )

        st.dataframe(
            pd.DataFrame(
                [selected_row]
            ),
            use_container_width=True
        )

        # ==================================================
        # SECTOR HEALTH
        # ==================================================

        st.subheader(
            "🏥 Sector Health"
        )

        sector_avg = round(
            result_df[
                "Total Score"
            ].mean(),
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

        # ==================================================
        # DOWNLOADS
        # ==================================================

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
            "📥 Download Excel",
            output.getvalue(),
            "sector_ranking_v2.xlsx"
        )

        csv = result_df.to_csv(
            index=False
        )

        st.download_button(
            "📥 Download CSV",
            csv,
            "sector_ranking_v2.csv"
        )

        # ==================================================
        # RAW DATA
        # ==================================================

        if show_raw:

            st.subheader(
                "Raw Sector Data"
            )

            st.dataframe(
                sector_df,
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"Error: {str(e)}"
        )