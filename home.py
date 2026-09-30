import streamlit as st

st.set_page_config(
    page_title="Stock Research Platform",
    page_icon="📈",
    layout="wide"
)

st.title(
    "📈 Stock Research Platform"
)

st.markdown(
    """
A complete stock research platform with:

✅ Stock Screener

✅ Sector Comparison

✅ Watchlist

✅ Historical Tracking
"""
)

st.divider()

col1, col2 = st.columns(2)

with col1:

    st.subheader(
        "📊 Analysis Tools"
    )

    st.info(
        """
Stock Screener

Run:
streamlit run app_v2.py
"""
    )

    st.info(
        """
Live Sector Comparison

Run:
streamlit run sector_compare_live.py
"""
    )

with col2:

    st.subheader(
        "⭐ Portfolio Tools"
    )

    st.info(
        """
Watchlist

Run:
streamlit run watchlist.py
"""
    )

    st.info(
        """
Sector History

Run:
streamlit run sector_history.py
"""
    )

st.divider()

st.success(
    """
Project Status

✅ Stock Analysis

✅ Sector Analysis

✅ Historical Tracking

✅ Watchlist Management

✅ Export Features
"""
)