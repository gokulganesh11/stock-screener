"""Capital Markets — 10–20 year compounder research.

The page keeps the existing screener and sector pages intact and adds a dedicated
research workflow for the Capital Markets industry universe.
"""

from io import BytesIO
import re

import pandas as pd
import streamlit as st

from company_scraper import get_company_details
from compounder_engine import compounder_score, evaluate_capital_markets_screen
from screener import get_sector_stocks

st.set_page_config(page_title="Capital Markets Research", page_icon="🏦", layout="wide")

CAPITAL_MARKETS_URL = "https://www.screener.in/market/IN05/IN0501/IN050103/"
DETAIL_LIMIT = 25


def _num(value):
    try:
        text = str(value).replace(",", "").replace("%", "").strip()
        return float(text) if text and text.lower() not in {"nan", "none", "-"} else None
    except (TypeError, ValueError):
        return None


def _source_priority(row):
    """Cheap ordering only; never used as the final research score."""
    score = 0.0
    roce = _num(row.get("ROCE  %"))
    q_profit = _num(row.get("Qtr Profit Var  %"))
    q_sales = _num(row.get("Qtr Sales Var  %"))
    pe = _num(row.get("P/E"))
    if roce is not None:
        score += min(max(roce, 0), 60) * 0.7
    if q_profit is not None:
        score += min(max(q_profit, 0), 80) * 0.2
    if q_sales is not None:
        score += min(max(q_sales, 0), 80) * 0.1
    if pe is not None and 0 < pe < 50:
        score += 10
    return score


def _clean_url(value):
    match = re.search(r"https://www\.screener\.in/company/[A-Za-z0-9_\-/]+/?", str(value))
    return match.group(0) if match else str(value).strip()


@st.cache_data(ttl=21600, show_spinner=False)
def load_capital_market_universe():
    return get_sector_stocks(CAPITAL_MARKETS_URL, max_pages=20)


def analyse_universe(df: pd.DataFrame, detail_limit: int = DETAIL_LIMIT):
    work = df.copy()
    work["_priority"] = work.apply(_source_priority, axis=1)
    work = work.sort_values("_priority", ascending=False).reset_index(drop=True)

    results, failures = [], []
    for _, row in work.head(detail_limit).iterrows():
        company = str(row.get("Company", "Unknown")).strip()
        url = _clean_url(row.get("Company URL", ""))
        if not url or url.lower() in {"none", "nan"}:
            failures.append({"Company": company, "Error": "Missing company URL"})
            continue
        try:
            details = get_company_details(url)
            screen = evaluate_capital_markets_screen(details)
            research = compounder_score(details, "Capital Markets")
            results.append({
                "Company": company,
                "Company URL": url,
                "Research Score": research["Score"],
                "Research Status": research["Status"],
                "Data Confidence": research["Data Confidence"],
                "Screen Checks": f"{screen['passed_count']}/{screen['total_count']}",
                "Screen Pass": "PASS" if screen["strict_pass"] else "FAIL",
                "ROE": details.get("ROE"),
                "ROCE": details.get("ROCE"),
                "PE": details.get("PE"),
                "PEG": details.get("PEG Ratio"),
                "EPS": details.get("EPS"),
                "Debt/Equity": details.get("Debt to Equity"),
                "Promoter %": details.get("Promoter Holding"),
                "Pledged %": details.get("Pledged Percentage"),
                "Sales Growth 3Y": details.get("Sales Growth 3Y"),
                "Sales Growth 5Y": details.get("Sales Growth 5Y"),
                "Profit Growth 3Y": details.get("Profit Growth 3Y"),
                "Profit Growth 5Y": details.get("Profit Growth 5Y"),
                "Valuation": research["Valuation"]["status"],
                "Red Flags": "; ".join(research["Red Flags"]),
            })
        except Exception as exc:
            failures.append({"Company": company, "Error": str(exc)})

    out = pd.DataFrame(results)
    if not out.empty:
        out = out.sort_values(["Research Score", "Data Confidence", "Screen Checks"], ascending=[False, False, False]).reset_index(drop=True)
        out.insert(0, "Rank", range(1, len(out) + 1))
    return out, pd.DataFrame(failures)


st.title("🏦 Capital Markets — 10–20 Year Compounder Research")
st.caption(
    "Complete Screener universe → evidence-based company inspection → quality/growth/valuation review. "
    "The output is a research shortlist, not a promise that any stock will become a multibagger."
)

with st.sidebar:
    st.header("Research controls")
    detail_limit = st.slider("Detailed pages to inspect", 10, 50, DETAIL_LIMIT, 5)
    if st.button("🔄 Refresh Capital Markets data", use_container_width=True):
        load_capital_market_universe.clear()
        st.cache_data.clear()
        st.rerun()

try:
    universe = load_capital_market_universe().copy()
except Exception as exc:
    st.error(f"Unable to load Capital Markets from Screener: {exc}")
    st.stop()

if universe.empty:
    st.warning("No Capital Markets companies were returned.")
    st.stop()

u1, u2, u3 = st.columns(3)
u1.metric("Capital Markets universe", len(universe))
u2.metric("Pages selected for deep research", min(detail_limit, len(universe)))
u3.metric("Required shortlist", 5)

st.info(
    "Important: a stock can score highly because of growth and returns on capital while still being too expensive. "
    "The app therefore shows business score and valuation status separately."
)

if st.button("🔬 Run 10–20 year research", type="primary", use_container_width=True):
    with st.spinner(f"Reading up to {detail_limit} company pages with throttled requests…"):
        results, failures = analyse_universe(universe, detail_limit)
    st.session_state["cm_results"] = results
    st.session_state["cm_failures"] = failures

results = st.session_state.get("cm_results", pd.DataFrame())
failures = st.session_state.get("cm_failures", pd.DataFrame())

if results.empty:
    st.info("Run the research scan to generate the Capital Markets shortlist.")
    st.stop()

strict_pass = int((results["Screen Pass"] == "PASS").sum())
confident = int((results["Data Confidence"] >= 75).sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Deeply researched", len(results))
m2.metric("Screen PASS", strict_pass)
m3.metric("Confidence ≥75%", confident)
m4.metric("Fetch failures", len(failures))

st.subheader("🎯 Top 5 research candidates")
st.caption(
    "Ranked by a transparent 100-point compounder research model. This ranking does not predict future returns. "
    "A PASS is not a buy instruction; inspect valuation and red flags before any decision."
)

top5 = results.head(5)
cols = ["Rank", "Company", "Research Score", "Research Status", "Data Confidence", "Screen Checks", "Screen Pass", "ROE", "ROCE", "PE", "PEG", "Promoter %", "Pledged %", "Valuation", "Red Flags", "Company URL"]
st.dataframe(
    top5[[c for c in cols if c in top5.columns]],
    use_container_width=True,
    hide_index=True,
    column_config={"Company URL": st.column_config.LinkColumn("Screener")},
)

st.subheader("🧭 How to interpret the score")
explain = pd.DataFrame([
    ["Quality", "ROE/ROCE and operating economics", "Durability of the business engine"],
    ["Growth", "3Y + 5Y sales/profit growth", "Evidence of compounding capacity"],
    ["Balance & Cash", "Leverage, FCF/CFO where available", "Ability to fund growth without excessive balance-sheet risk"],
    ["Valuation", "PE + PEG", "Price paid relative to current earnings/growth"],
    ["Ownership", "Promoter holding + pledge", "Alignment and pledge risk"],
    ["Consistency", "Annual + latest-quarter direction", "Recent confirmation of the long-term record"],
])
st.dataframe(explain.rename(columns={0: "Dimension", 1: "Evidence", 2: "Why it matters"}), use_container_width=True, hide_index=True)

st.subheader("🔎 Company deep dive")
selected_name = st.selectbox("Select a company", results["Company"].tolist())
selected = results[results["Company"] == selected_name].iloc[0]

try:
    details = get_company_details(selected["Company URL"])
    screen = evaluate_capital_markets_screen(details)
    research = compounder_score(details, "Capital Markets")
except Exception as exc:
    st.error(f"Unable to load company details: {exc}")
else:
    a, b, c, d = st.columns(4)
    a.metric("Research score", f"{research['Score']}/100")
    b.metric("Data confidence", f"{research['Data Confidence']}%")
    c.metric("Capital-market screen", f"{screen['passed_count']}/{screen['total_count']}")
    d.metric("Valuation", research["Valuation"]["status"])

    if research["Red Flags"]:
        st.warning("; ".join(research["Red Flags"]))
    else:
        st.success("No red flag was triggered by the available fields. This does not remove business, regulatory or valuation risk.")

    st.markdown("### Score breakdown")
    st.dataframe(pd.DataFrame([research["Breakdown"]]), use_container_width=True, hide_index=True)

    st.markdown("### Evidence")
    evidence_cols = [
        "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity", "Promoter Holding", "Pledged Percentage",
        "Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y", "Profit Growth 5Y",
        "Sales Latest Quarter", "Net Profit Latest Quarter", "Sales Latest Year vs Preceding", "Profit Latest Year vs Preceding",
        "Data Completeness",
    ]
    st.dataframe(pd.DataFrame([{c: details.get(c) for c in evidence_cols}]), use_container_width=True, hide_index=True)

    if screen["failed_or_unverified"]:
        st.warning("Screen exceptions: " + "; ".join(screen["failed_or_unverified"]))
    else:
        st.success("All Capital Markets screen checks pass with available data.")

st.subheader("📋 All deeply researched companies")
st.dataframe(results.drop(columns=["Company URL"], errors="ignore"), use_container_width=True, hide_index=True)

st.subheader("📥 Export")
excel = BytesIO()
with pd.ExcelWriter(excel, engine="openpyxl") as writer:
    results.to_excel(writer, index=False, sheet_name="Capital Markets")
    universe.to_excel(writer, index=False, sheet_name="Universe")
    if not failures.empty:
        failures.to_excel(writer, index=False, sheet_name="Failures")
st.download_button("📥 Download Excel", excel.getvalue(), "capital_markets_research.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("📥 Download CSV", results.to_csv(index=False), "capital_markets_research.csv", "text/csv")

with st.expander("ℹ️ Research rules"):
    st.write(
        "This page does not use a generic BUY/SELL label. It separates research score, screen checks, data confidence and valuation. "
        "Capital-markets businesses are treated differently from industrial companies for leverage because AMCs, exchanges and distributors "
        "can have structurally different balance sheets. Missing information lowers confidence rather than being silently treated as a pass."
    )
