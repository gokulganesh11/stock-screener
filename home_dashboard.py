import streamlit as st

st.title("📈 Stock Research Platform")
st.caption("A single workspace for screening, sector research, company research, watchlists and history.")
st.info("The platform organizes evidence for 10–20 year research. Scores are comparison aids, not forecasts, guarantees or automatic buy/sell instructions.")
st.divider()

cards = [
    ("🔎 Stock Screener", "Run the strict 16-condition screen and inspect the evidence behind each candidate."),
    ("📊 Sector Comparison", "Scan the complete live Screener industry universe and drill into any industry."),
    ("🏦 Capital Markets", "Run the dedicated capital-markets compounder model and produce a top-5 research shortlist."),
    ("⭐ Watchlist", "Maintain a lightweight research list and export snapshots."),
    ("📈 Historical Tracking", "Review saved sector score changes over time."),
    ("🔔 Alerts", "Review material changes between saved research snapshots."),
]
cols = st.columns(3)
for i, (title, description) in enumerate(cards):
    with cols[i % 3]:
        st.subheader(title)
        st.write(description)

st.divider()
st.subheader("🎯 Recommended 10–20 year workflow")
steps = [
    "Universe — scan all companies returned by Screener and keep the source data visible.",
    "Sector — compare industries before drilling into individual businesses.",
    "Company — verify quality, growth, balance sheet, ownership and recent consistency.",
    "Valuation — check PE/PEG and compare the price with the business evidence; a great company can still be expensive.",
    "Confidence — do not treat missing data as a pass; verify important gaps from filings/company disclosures.",
    "Watchlist — track the shortlist and revisit the thesis as new results arrive.",
]
for i, step in enumerate(steps, 1):
    st.write(f"**{i}.** {step}")
