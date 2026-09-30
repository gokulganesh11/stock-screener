import streamlit as st

st.title("📈 Stock Research Platform")
st.caption("A single workspace for screening, sector research, watchlists and historical analysis.")
st.info("Use the left navigation to open each module. The platform surfaces data-driven research signals; it does not predict or guarantee future returns.")
st.divider()

cards = [
    ("🔎 Stock Screener", "Run the strict 16-condition 10–20 year research screen and inspect the evidence behind each result."),
    ("📊 Sector Comparison", "Compare configured sectors and drill into company-level research scores."),
    ("⭐ Watchlist", "Maintain a lightweight research list and export snapshots."),
    ("📈 Historical Tracking", "Review saved sector snapshots and score changes over time."),
    ("🔔 Alerts", "Review material changes between saved research snapshots."),
]
cols = st.columns(3)
for i, (title, description) in enumerate(cards):
    with cols[i % 3]:
        st.subheader(title)
        st.write(description)

st.divider()
st.subheader("🎯 Recommended workflow")
steps = [
    "Stock Screener — choose a sector and run the strict filter.",
    "Company inspection — review every failed or unverified condition.",
    "Long-term score — compare quality, growth, valuation, ownership, consistency and cash flow.",
    "Watchlist — keep only names you want to research further.",
    "History / Alerts — revisit changes instead of relying on a single snapshot.",
]
for i, step in enumerate(steps, 1):
    st.write(f"**{i}.** {step}")
