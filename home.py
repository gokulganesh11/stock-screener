import streamlit as st

st.set_page_config(
    page_title="Stock Research Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Stock Research Platform")
st.caption("A single workspace for screening, sector research, watchlists and historical analysis.")

st.info(
    "Use the navigation in the left sidebar to open each research module. "
    "The platform is designed to surface data-driven research signals; it does not predict future returns."
)

st.divider()

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("🔎 Stock Screener")
    st.write(
        "Analyze a Screener.in sector, collect company fundamentals, calculate a transparent score, "
        "and inspect the highest-ranked companies."
    )
    st.page_link("pages/01_Stock_Screener.py", label="Open Stock Screener", icon="🔎")

with c2:
    st.subheader("📊 Sector Comparison")
    st.write(
        "Compare configured sectors using their average stock scores and drill into the companies "
        "that drive each sector result."
    )
    st.page_link("pages/02_Sector_Comparison.py", label="Open Sector Comparison", icon="📊")

with c3:
    st.subheader("⭐ Watchlist")
    st.write(
        "Keep a lightweight research list with notes and export it whenever you need a snapshot."
    )
    st.page_link("pages/03_Watchlist.py", label="Open Watchlist", icon="⭐")

st.divider()

c4, c5 = st.columns(2)

with c4:
    st.subheader("📈 Historical Tracking")
    st.write("Review saved sector snapshots and compare score changes over time.")
    st.page_link("pages/04_History.py", label="Open History", icon="📈")

with c5:
    st.subheader("🔔 Alerts")
    st.write("Identify material changes between the latest two saved sector snapshots.")
    st.page_link("pages/05_Alerts.py", label="Open Alerts", icon="🔔")

st.divider()

st.subheader("🧭 Recommended workflow")
st.markdown(
    """
1. **Stock Screener** — choose a sector and run the analysis.
2. **Company Analysis** — inspect the score components and underlying metrics.
3. **Sector Comparison** — compare configured sectors when multiple sector URLs are available.
4. **Watchlist** — save companies that need further research.
5. **History / Alerts** — compare saved snapshots and investigate changes.

> Scores are screening aids, not guarantees of future performance. Always validate the underlying data and perform your own research.
"""
)

st.caption("Main entry point: `streamlit run home.py`")
