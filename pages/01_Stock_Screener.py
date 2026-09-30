import streamlit as st
import pandas as pd

from research_engine import SECTORS, analyze_sector, dataframe_to_excel
from storage import save_snapshot

st.set_page_config(page_title="Stock Screener", page_icon="🔎", layout="wide")

st.title("🔎 Stock Screener")
st.caption("Transparent fundamental screening from Screener.in data. Scores are research aids, not forecasts.")

selected_sector = st.selectbox("Sector", [*SECTORS.keys(), "Custom URL"])
if selected_sector == "Custom URL":
    sector_url = st.text_input("Screener.in sector URL")
else:
    sector_url = SECTORS[selected_sector]

col1, col2 = st.columns(2)
with col1:
    top_n = st.slider("Stocks to display", 5, 50, 15)
with col2:
    show_failures = st.checkbox("Show analysis failures", value=True)

if st.button("🚀 Analyze Sector", type="primary", use_container_width=True):
    if not sector_url.strip():
        st.error("Enter a sector URL first.")
        st.stop()

    progress = st.progress(0)
    status = st.empty()
    try:
        status.info("Reading sector table...")
        result_df, failures_df, source_df = analyze_sector(
            sector_url,
            progress_callback=progress.progress,
        )
        st.session_state["screen_result"] = result_df
        st.session_state["screen_failures"] = failures_df
        st.session_state["screen_source"] = source_df
        st.session_state["screen_sector_name"] = selected_sector
        status.success("Analysis completed.")
    except Exception as exc:
        status.empty()
        st.error(f"Analysis failed: {exc}")
        st.stop()

result_df = st.session_state.get("screen_result")
failures_df = st.session_state.get("screen_failures")
source_df = st.session_state.get("screen_source")

if result_df is None:
    st.info("Choose a sector and click **Analyze Sector** to begin.")
    st.stop()

if result_df.empty:
    st.warning("No companies could be analyzed. Check the source page and data availability.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Companies found", len(source_df))
c2.metric("Successfully analyzed", len(result_df))
c3.metric("Failed", len(failures_df))
c4.metric("Average score", round(result_df["Total Score"].mean(), 2))

st.subheader("🏆 Ranked results")
st.dataframe(result_df.head(top_n), use_container_width=True, hide_index=True)

selected = st.selectbox("Inspect company", result_df["Company"].tolist())
row = result_df.loc[result_df["Company"] == selected].iloc[0]

st.subheader(f"🔎 {selected}")
metric_cols = st.columns(6)
for column, label in zip(metric_cols, ["Total", "Quality", "Growth", "Valuation", "Ownership", "Risk"]):
    key = {"Total": "Total Score", "Quality": "Quality Score", "Growth": "Growth Score", "Valuation": "Valuation Score", "Ownership": "Ownership Score", "Risk": "Risk Score"}[label]
    column.metric(label, row[key])

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Why it scored this way**")
    st.write(row.get("Reasons", "") or "No positive scoring reasons recorded.")
with c2:
    st.markdown("**Warnings / data limitations**")
    st.write(row.get("Warnings", "") or "No scoring warnings recorded.")

st.write(f"**Confidence:** {row['Confidence']}  ·  **Data completeness:** {row['Data Completeness']}%")

fundamental_columns = ["ROE", "ROCE", "PE", "Market Cap", "Dividend Yield", "Promoter Holding", "FII Holding", "Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y", "Profit Growth 5Y"]
st.dataframe(pd.DataFrame([row[fundamental_columns]]), use_container_width=True, hide_index=True)

st.subheader("💾 Research snapshot")
if st.button("Save current sector snapshot"):
    snapshot = pd.DataFrame([{
        "Sector": st.session_state.get("screen_sector_name", selected_sector),
        "Average Score": round(result_df["Total Score"].mean(), 2),
        "Highest Score": int(result_df["Total Score"].max()),
        "Companies Analyzed": len(result_df),
        "Companies Failed": len(failures_df),
        "Top Company": result_df.iloc[0]["Company"],
    }])
    path = save_snapshot(snapshot, "sector_snapshot")
    st.success(f"Snapshot saved: {path.name}")

st.subheader("📥 Export")
st.download_button("Download Excel", dataframe_to_excel(result_df), "stock_screening_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("Download CSV", result_df.to_csv(index=False), "stock_screening_results.csv", "text/csv")

if show_failures and not failures_df.empty:
    st.subheader("⚠️ Companies that could not be analyzed")
    st.dataframe(failures_df, use_container_width=True, hide_index=True)
