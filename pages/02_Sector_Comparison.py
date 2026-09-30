import streamlit as st
import pandas as pd

from sector_urls import SECTOR_URLS
from research_engine import analyze_sector
from storage import save_snapshot

st.set_page_config(page_title="Sector Comparison", page_icon="📊", layout="wide")
st.title("📊 Sector Comparison")
st.caption("Compare configured sectors using the same transparent stock scoring engine.")

configured = {name: url for name, url in SECTOR_URLS.items() if str(url).strip()}
if not configured:
    st.warning("No sector URLs are configured yet.")
    st.stop()

selected = st.multiselect("Sectors to compare", list(configured), default=list(configured))
if not selected:
    st.info("Select at least one sector.")
    st.stop()

if st.button("🚀 Compare Sectors", type="primary", use_container_width=True):
    rows = []
    failures = []
    progress = st.progress(0)

    for index, name in enumerate(selected, start=1):
        try:
            result, failed, source = analyze_sector(configured[name], progress_callback=None)
            if result.empty:
                raise ValueError("No companies could be analyzed")
            rows.append({
                "Sector": name,
                "Average Score": round(result["Total Score"].mean(), 2),
                "Highest Score": int(result["Total Score"].max()),
                "Companies Analyzed": len(result),
                "Companies Failed": len(failed),
                "Top Company": result.iloc[0]["Company"],
                "High Confidence": int((result["Confidence"] == "High").sum()),
            })
        except Exception as exc:
            failures.append({"Sector": name, "Error": str(exc)})
        progress.progress(index / len(selected))

    comparison = pd.DataFrame(rows).sort_values("Average Score", ascending=False) if rows else pd.DataFrame()
    st.session_state["sector_comparison"] = comparison
    st.session_state["sector_failures"] = pd.DataFrame(failures)

comparison = st.session_state.get("sector_comparison")
failures = st.session_state.get("sector_failures")

if comparison is None:
    st.info("Select sectors and click **Compare Sectors**.")
    st.stop()

if comparison.empty:
    st.error("No sectors could be analyzed.")
    st.stop()

st.subheader("🏆 Sector ranking")
st.dataframe(comparison, use_container_width=True, hide_index=True)

best = comparison.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sectors", len(comparison))
c2.metric("Top sector", best["Sector"])
c3.metric("Top average score", best["Average Score"])
c4.metric("Companies analyzed", int(comparison["Companies Analyzed"].sum()))

st.subheader("🔎 Sector drilldown")
sector = st.selectbox("Select sector", comparison["Sector"])
url = configured[sector]
detail, failed, source = analyze_sector(url)
if not detail.empty:
    st.dataframe(detail.head(20), use_container_width=True, hide_index=True)

if st.button("💾 Save this comparison as a snapshot"):
    save_snapshot(comparison, "sector_comparison")
    st.success("Snapshot saved. Open History or Alerts to compare it later.")

if failures is not None and not failures.empty:
    st.subheader("⚠️ Sector failures")
    st.dataframe(failures, use_container_width=True, hide_index=True)
