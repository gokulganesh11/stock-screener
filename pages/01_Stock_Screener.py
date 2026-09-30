import streamlit as st
import pandas as pd

from long_term_engine import SECTORS, analyze_long_term_sector, dataframe_to_excel
from storage import save_snapshot

st.set_page_config(page_title="Stock Screener", page_icon="🔎", layout="wide")
st.title("🔎 10–20 Year Multibagger Screener")
st.caption("Strict fundamental filter first, then a transparent long-term research score. A PASS means every required condition was available and satisfied; it is not a forecast or guarantee.")

selected_sector = st.selectbox("Sector", [*SECTORS.keys(), "Custom URL"])
sector_url = st.text_input("Screener.in sector URL", value="" if selected_sector == "Custom URL" else SECTORS[selected_sector])

c1, c2 = st.columns(2)
with c1:
    top_n = st.slider("Stocks to display", 5, 50, 15)
with c2:
    show_failures = st.checkbox("Show analysis failures", value=True)

if st.button("🚀 Analyze Sector", type="primary", use_container_width=True):
    if not sector_url.strip():
        st.error("Enter a sector URL first."); st.stop()
    progress = st.progress(0); status = st.empty()
    try:
        status.info("Collecting company fundamentals and applying the strict 16-condition screen...")
        result_df, failures_df, source_df = analyze_long_term_sector(sector_url, progress_callback=progress.progress)
        st.session_state["screen_result"] = result_df
        st.session_state["screen_failures"] = failures_df
        st.session_state["screen_source"] = source_df
        st.session_state["screen_sector_name"] = selected_sector
        status.success("Analysis completed.")
    except Exception as exc:
        status.empty(); st.error(f"Analysis failed: {exc}"); st.stop()

result_df = st.session_state.get("screen_result")
failures_df = st.session_state.get("screen_failures")
source_df = st.session_state.get("screen_source")
if result_df is None:
    st.info("Choose a sector and click **Analyze Sector** to begin."); st.stop()
if result_df.empty:
    st.warning("No companies could be analyzed."); st.stop()

qualified = result_df[result_df["Strict Screen"] == "PASS"].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Companies found", len(source_df))
c2.metric("Analyzed", len(result_df))
c3.metric("Strict PASS", len(qualified))
c4.metric("Failures", len(failures_df))

st.subheader("🎯 Top 5 long-term candidates")
if qualified.empty:
    st.warning("No company passed all 16 required conditions in this sector. The app will not force five names.")
    st.caption("Review the failed conditions below. Missing source data is treated as unverified, not as a pass.")
else:
    top5 = qualified.head(5)
    st.dataframe(top5[["Multibagger Rank", "Company", "Long-Term Score", "Checks", "Confidence", "Data Completeness", "ROE", "ROCE", "PE", "PEG Ratio", "Debt to Equity", "EPS", "Promoter Holding", "Pledged Percentage", "Sales Growth 5Y", "Profit Growth 5Y"]], use_container_width=True, hide_index=True)

st.subheader("📊 All screened companies")
st.dataframe(result_df.head(top_n), use_container_width=True, hide_index=True)

selected = st.selectbox("Inspect company", result_df["Company"].tolist())
row = result_df.loc[result_df["Company"] == selected].iloc[0]

st.subheader(f"🔎 {selected}")
status_cols = st.columns(4)
status_cols[0].metric("Strict screen", row["Strict Screen"])
status_cols[1].metric("Conditions", row["Checks"])
status_cols[2].metric("Long-term score", row["Long-Term Score"])
status_cols[3].metric("Confidence", row["Confidence"])

if row["Strict Screen"] == "PASS":
    st.success("All required screening conditions passed.")
else:
    st.error("This company does not currently pass the complete strict screen.")
    st.write("**Failed / unverified conditions:**", row["Failed Conditions"] or "None")

fundamental_columns = [
    "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity", "Promoter Holding", "Pledged Percentage",
    "Sales Growth 3Y", "Sales Growth 5Y", "Sales Growth 10Y", "Profit Growth 3Y", "Profit Growth 5Y", "Profit Growth 10Y",
    "Sales Latest", "Sales Previous Year", "Net Profit Latest", "Net Profit Previous Year",
    "Sales Latest Quarter", "Net Profit Latest Quarter", "Sales YoY Quarter Growth", "Profit YoY Quarter Growth",
    "FCF Positive Years 5Y", "CFO/OP 5Y Average", "ROE 5Y Average", "ROCE 5Y Average",
]
existing = [c for c in fundamental_columns if c in row.index]
st.dataframe(pd.DataFrame([row[existing]]), use_container_width=True, hide_index=True)

st.markdown("**Long-term quality signals**")
st.write(row["Reasons"] or "No additional positive signals recorded.")

st.subheader("💾 Research snapshot")
if st.button("Save current sector snapshot"):
    snapshot = pd.DataFrame([{
        "Sector": st.session_state.get("screen_sector_name", selected_sector),
        "Companies Analyzed": len(result_df), "Strict Pass": len(qualified),
        "Top Candidate": qualified.iloc[0]["Company"] if not qualified.empty else "None",
        "Top Score": qualified.iloc[0]["Long-Term Score"] if not qualified.empty else None,
    }])
    path = save_snapshot(snapshot, "long_term_sector_snapshot")
    st.success(f"Snapshot saved: {path.name}")

st.subheader("📥 Export")
st.download_button("Download Excel", dataframe_to_excel(result_df), "long_term_screening_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("Download CSV", result_df.to_csv(index=False), "long_term_screening_results.csv", "text/csv")

if show_failures and not failures_df.empty:
    st.subheader("⚠️ Companies that could not be analyzed")
    st.dataframe(failures_df, use_container_width=True, hide_index=True)
