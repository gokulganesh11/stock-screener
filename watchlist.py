import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from datetime import datetime

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="My Watchlist",
    page_icon="⭐",
    layout="wide"
)

# ==================================================
# CONFIG
# ==================================================

WATCHLIST_FILE = "watchlist.csv"

# ==================================================
# HELPERS
# ==================================================

def load_watchlist():

    if Path(WATCHLIST_FILE).exists():

        return pd.read_csv(
            WATCHLIST_FILE
        )

    return pd.DataFrame(
        columns=[
            "Stock",
            "Notes",
            "Date Added"
        ]
    )


def save_watchlist(df):

    df.to_csv(
        WATCHLIST_FILE,
        index=False
    )


# ==================================================
# LOAD
# ==================================================

watchlist_df = load_watchlist()

# ==================================================
# HEADER
# ==================================================

st.title(
    "⭐ My Watchlist"
)

st.caption(
    "Track stocks for future research and investment opportunities."
)

# ==================================================
# ADD STOCK
# ==================================================

st.subheader(
    "➕ Add Stock"
)

col1, col2 = st.columns(2)

with col1:

    stock_name = st.text_input(
        "Stock Name"
    )

with col2:

    notes = st.text_input(
        "Notes"
    )

if st.button(
    "⭐ Add To Watchlist",
    use_container_width=True
):

    stock_name = stock_name.strip()

    if not stock_name:

        st.warning(
            "Enter a stock name."
        )

    else:

        exists = (
            stock_name.lower()
            in watchlist_df["Stock"]
            .astype(str)
            .str.lower()
            .tolist()
        )

        if exists:

            st.warning(
                "Stock already exists."
            )

        else:

            new_row = pd.DataFrame(
                {
                    "Stock":
                    [stock_name],

                    "Notes":
                    [notes],

                    "Date Added":
                    [
                        datetime.now()
                        .strftime(
                            "%Y-%m-%d"
                        )
                    ]
                }
            )

            watchlist_df = pd.concat(
                [
                    watchlist_df,
                    new_row
                ],
                ignore_index=True
            )

            save_watchlist(
                watchlist_df
            )

            st.success(
                f"{stock_name} added successfully."
            )

# ==================================================
# SEARCH
# ==================================================

st.subheader(
    "🔍 Search"
)

search_text = st.text_input(
    "Search Stock"
)

filtered_df = watchlist_df.copy()

if search_text:

    filtered_df = filtered_df[
        filtered_df["Stock"]
        .str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

# ==================================================
# SUMMARY
# ==================================================

st.subheader(
    "📊 Watchlist Summary"
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Total Stocks",
    len(watchlist_df)
)

c2.metric(
    "Displayed Stocks",
    len(filtered_df)
)

c3.metric(
    "Latest Addition",
    (
        watchlist_df.iloc[-1]["Stock"]
        if len(watchlist_df)
        else "-"
    )
)

# ==================================================
# WATCHLIST TABLE
# ==================================================

st.subheader(
    "📋 Watchlist"
)

if filtered_df.empty:

    st.info(
        "No stocks available."
    )

else:

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

# ==================================================
# REMOVE STOCK
# ==================================================

if not watchlist_df.empty:

    st.subheader(
        "❌ Remove Stock"
    )

    remove_stock = st.selectbox(
        "Choose Stock",
        watchlist_df["Stock"]
    )

    if st.button(
        "Remove Selected Stock"
    ):

        watchlist_df = (
            watchlist_df[
                watchlist_df["Stock"]
                != remove_stock
            ]
        )

        save_watchlist(
            watchlist_df
        )

        st.success(
            f"{remove_stock} removed."
        )

# ==================================================
# CLEAR WATCHLIST
# ==================================================

if not watchlist_df.empty:

    if st.button(
        "🗑️ Clear Entire Watchlist"
    ):

        watchlist_df = pd.DataFrame(
            columns=[
                "Stock",
                "Notes",
                "Date Added"
            ]
        )

        save_watchlist(
            watchlist_df
        )

        st.success(
            "Watchlist cleared."
        )

# ==================================================
# EXPORT
# ==================================================

st.subheader(
    "📥 Export Watchlist"
)

output = BytesIO()

watchlist_df.to_excel(
    output,
    index=False,
    engine="openpyxl"
)

st.download_button(
    "📥 Download Excel",
    output.getvalue(),
    "watchlist.xlsx"
)

csv_data = (
    watchlist_df.to_csv(
        index=False
    )
)

st.download_button(
    "📥 Download CSV",
    csv_data,
    "watchlist.csv"
)

# ==================================================
# INSIGHTS
# ==================================================

st.subheader(
    "💡 Usage Tips"
)

st.info(
    """
✅ Add promising stocks discovered from Sector Comparison.

✅ Add notes explaining why the stock was shortlisted.

✅ Review the watchlist weekly.

✅ Remove stocks that no longer meet your criteria.

✅ Export before major portfolio reviews.
"""
)