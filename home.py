import streamlit as st

st.set_page_config(page_title="Stock Research Platform", page_icon="📈", layout="wide")

pages = [
    st.Page("home_dashboard.py", title="Home", icon="🏠"),
    st.Page("app_v2.py", title="Stock Screener", icon="🔎"),
    st.Page("sector_compare_live.py", title="Sector Comparison", icon="📊"),
    st.Page("capital_markets.py", title="Capital Markets", icon="🏦"),
    st.Page("watchlist.py", title="Watchlist", icon="⭐"),
    st.Page("sector_history.py", title="History", icon="📈"),
    st.Page("alerts.py", title="Alerts", icon="🔔"),
]

pg = st.navigation(pages)
pg.run()
