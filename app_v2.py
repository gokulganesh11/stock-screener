import re
from io import BytesIO

import pandas as pd
import streamlit as st

from company_scraper import get_company_details
from long_term_screen import evaluate_strict_screen, long_term_score
from screener import get_sector_stocks

st.set_page_config(page_title="10–20 Year Multibagger Screener", page_icon="🔎", layout="wide")

SECTORS = {
    "Capital Markets": "https://www.screener.in/market/IN05/IN0501/IN050103/",
    "Custom URL": "",
}

MIN_RESEARCH_CANDIDATES = 5
MIN_NEAR_MATCH_CHECKS = 10
INITIAL_ANALYSIS_BATCH = 15
ANALYSIS_BATCH = 10
MAX_DETAIL_COMPANIES = 45


def clean_company_url(value):
    match = re.search(r"https://www\.screener\.in/company/[A-Za-z0-9\-/]+/?", str(value))
    return match.group(0) if match else str(value).strip()


def _number(value):
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _priority_score(row):
    """Cheap sector-page pre-score used only to choose the analysis order.

    It never determines PASS/FAIL. The complete company page is still checked
    against all 16 strict rules before a company can be marked PASS.
    """
    pe = _number(row.get("P/E"))
    roce = _number(row.get("ROCE  %"))
    q_profit = _number(row.get("Qtr Profit Var  %"))
    q_sales = _number(row.get("Qtr Sales Var  %"))
    market_cap = _number(row.get("Mar Cap  Rs.Cr."))

    score = 0.0
    if pe is not None and 0 < pe < 50:
        score += 20
        if pe < 30:
            score += 5
    if roce is not None and roce > 10:
        score += min(roce, 40) * 0.6
    if q_profit is not None and q_profit > 0:
        score += min(q_profit, 50) * 0.15
    if q_sales is not None and q_sales > 0:
        score += min(q_sales, 50) * 0.10
    if market_cap is not None and market_cap > 500:
        score += 3
    return score


def _analyse_company(row):
    company = str(row.get("Company", "Unknown")).strip()
    company_url = clean_company_url(row.get("Company URL", ""))
    if not company_url or company_url.lower() in {"none", "nan"}:
        return None, {"Company": company, "Company URL": company_url, "Error": "Company URL is missing"}

    try:
        details = get_company_details(company_url)
        strict = evaluate_strict_screen(details)
        score, parts = long_term_score(details)
        result = {
            "Company": company,
            "Company URL": company_url,
            "Strict Screen": "PASS" if strict["strict_pass"] else "FAIL",
            "Checks": f"{strict['passed_count']}/{strict['total_count']}",
            "Passed Checks": strict["passed_count"],
            "Long-Term Score": score,
            "Quality Score": parts["Quality"],
            "Growth Score": parts["Growth"],
            "Balance Sheet Score": parts["Balance Sheet"],
            "Valuation Score": parts["Valuation"],
            "Ownership Score": parts["Ownership"],
            "Consistency Score": parts["Consistency"],
            "Cash Flow Score": parts["Cash Flow"],
            "Data Completeness": details.get("Data Completeness"),
            "ROE": details.get("ROE"),
            "ROCE": details.get("ROCE"),
            "PE": details.get("PE"),
            "PEG Ratio": details.get("PEG Ratio"),
            "PEG Source": details.get("PEG Source"),
            "EPS": details.get("EPS"),
            "Debt to Equity": details.get("Debt to Equity"),
            "Promoter Holding": details.get("Promoter Holding"),
            "Pledged Percentage": details.get("Pledged Percentage"),
            "Sales Growth 3Y": details.get("Sales Growth 3Y"),
            "Sales Growth 5Y": details.get("Sales Growth 5Y"),
            "Profit Growth 3Y": details.get("Profit Growth 3Y"),
            "Profit Growth 5Y": details.get("Profit Growth 5Y"),
            "Sales Latest Quarter": details.get("Sales Latest Quarter"),
            "Net Profit Latest Quarter": details.get("Net Profit Latest Quarter"),
            "Sales Latest Year vs Preceding": details.get("Sales Latest Year vs Preceding"),
            "Profit Latest Year vs Preceding": details.get("Profit Latest Year vs Preceding"),
            "Free Cash Flow": details.get("Free Cash Flow"),
            "CFO/OP": details.get("CFO/OP"),
            "Failure Reasons": "; ".join(strict["failed_or_unverified"]),
        }
        return result, None
    except Exception as exc:
        return None, {"Company": company, "Company URL": company_url, "Error": str(exc)}


@st.cache_data(ttl=21600, show_spinner=False)
def run_sector_analysis(url):
    """Analyse enough of the sector to reliably produce five research rows.

    Strict PASS remains strict. If fewer than five companies pass all 16 rules,
    the UI shows five closest matches ranked by passed conditions + research
    score. It never relabels a FAIL as PASS.
    """
    sector_df = get_sector_stocks(url).copy()
    if sector_df.empty:
        return pd.DataFrame(), pd.DataFrame(), 0

    sector_df["_priority"] = sector_df.apply(_priority_score, axis=1)
    sector_df = sector_df.sort_values("_priority", ascending=False).reset_index(drop=True)

    results, failures = [], []
    analysed = 0
    target = min(INITIAL_ANALYSIS_BATCH, len(sector_df), MAX_DETAIL_COMPANIES)
    next_index = 0

    while next_index < target:
        batch = sector_df.iloc[next_index:target]
        for _, row in batch.iterrows():
            result, failure = _analyse_company(row)
            analysed += 1
            if result is not None:
                results.append(result)
            elif failure is not None:
                failures.append(failure)
        next_index = target

        if len(results) >= MIN_RESEARCH_CANDIDATES:
            result_df = pd.DataFrame(results)
            near_count = int((result_df["Passed Checks"] >= MIN_NEAR_MATCH_CHECKS).sum())
            # Once we have five usable rows, stop after the initial batch unless
            # fewer than five are reasonably close to the strict rules.
            if analysed >= INITIAL_ANALYSIS_BATCH and near_count >= MIN_RESEARCH_CANDIDATES:
                break
            if analysed >= INITIAL_ANALYSIS_BATCH and next_index >= len(sector_df):
                break

        if next_index >= len(sector_df) or next_index >= MAX_DETAIL_COMPANIES:
            break
        target = min(next_index + ANALYSIS_BATCH, len(sector_df), MAX_DETAIL_COMPANIES)

    result_df = pd.DataFrame(results)
    failures_df = pd.DataFrame(failures)
    if not result_df.empty:
        result_df["Candidate Tier"] = "Research candidate"
        result_df.loc[result_df["Strict Screen"] == "PASS", "Candidate Tier"] = "Strict PASS"
        result_df.loc[result_df["Passed Checks"] >= MIN_NEAR_MATCH_CHECKS, "Candidate Tier"] = "Near match"
        result_df.loc[result_df["Strict Screen"] == "PASS", "Candidate Tier"] = "Strict PASS"

        result_df = result_df.sort_values(
            ["Strict Screen", "Passed Checks", "Long-Term Score", "Data Completeness"],
            ascending=[False, False, False, False],
        ).reset_index(drop=True)
        result_df.insert(0, "Rank", range(1, len(result_df) + 1))

    return result_df, failures_df, analysed


st.title("🔎 10–20 Year Multibagger Screener")
st.caption(
    "Strict fundamentals first, then a transparent long-term research score. "
    "PASS means every required rule was satisfied with available data; it is not a forecast or guarantee."
)

with st.sidebar:
    st.header("⚙️ Research Settings")
    st.info(
        "The screener reads all sector pages, then analyses companies in batches. "
        "Requests are deliberately spaced to reduce Screener 429 errors and successful results are cached for 6 hours."
    )
    if st.button("🧹 Clear cached market data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

selected_sector = st.selectbox("Sector", list(SECTORS))
if selected_sector == "Custom URL":
    sector_url = st.text_input("Screener.in sector URL")
else:
    sector_url = SECTORS[selected_sector]
    st.text_input("Screener.in sector URL", value=sector_url, disabled=True)

c1, c2 = st.columns([1, 1])
with c1:
    top_n = st.slider("Stocks to display", 5, 25, 15)
with c2:
    show_failures = st.checkbox("Show analysis failures", value=True)

st.subheader("🎯 Strict 16-condition filter")
st.markdown(
    "**ROE > 10% · ROCE > 10% · PE < 50 · PEG < 1.5 · Debt/Equity < 1 · EPS > 10 · "
    "Promoter > 50% · Pledged < 10% · Sales/Profit growth 3Y & 5Y > 10% · "
    "Sales & profit latest year > preceding year · latest-quarter sales & profit > 0**"
)

if st.button("🚀 Analyze Sector", type="primary", use_container_width=True):
    if not sector_url.strip():
        st.error("Please provide a Screener.in sector URL.")
        st.stop()
    with st.spinner("Reading the full sector and analysing companies in safe batches…"):
        result_df, failures_df, analysed_count = run_sector_analysis(sector_url)
    st.session_state["lt_results"] = result_df
    st.session_state["lt_failures"] = failures_df
    st.session_state["lt_analysed"] = analysed_count

result_df = st.session_state.get("lt_results", pd.DataFrame())
failures_df = st.session_state.get("lt_failures", pd.DataFrame())
analysed_count = st.session_state.get("lt_analysed", len(result_df))
if result_df.empty:
    st.info("Run the analysis to see the strict screen and long-term research ranking.")
    st.stop()

strict_pass_df = result_df[result_df["Strict Screen"] == "PASS"].copy()
near_pass_df = result_df[result_df["Strict Screen"] != "PASS"].copy()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Sector companies", len(result_df) + len(failures_df))
m2.metric("Analysed", analysed_count)
m3.metric("Strict PASS", len(strict_pass_df))
m4.metric("Fetch failures", len(failures_df))

if len(strict_pass_df) >= MIN_RESEARCH_CANDIDATES:
    st.success(f"{len(strict_pass_df)} companies currently satisfy all 16 strict conditions.")
    st.subheader("🎯 Top 5 strict-pass candidates")
    top_candidates = strict_pass_df.head(5)
else:
    st.warning(
        f"Only {len(strict_pass_df)} companies pass all 16 conditions. "
        "The screen will not falsely label five companies as strict passes."
    )
    st.subheader("🎯 Top 5 closest research candidates")
    st.caption(
        "These five are ranked by the number of strict conditions passed, then the transparent long-term score. "
        "A FAIL remains a FAIL and must be manually researched before any investment decision."
    )
    top_candidates = near_pass_df.head(5)

if len(top_candidates) < MIN_RESEARCH_CANDIDATES:
    st.error(
        f"Only {len(top_candidates)} companies could be analysed successfully. "
        "The app will not invent missing data just to reach five."
    )

candidate_cols = [
    "Rank", "Company", "Candidate Tier", "Strict Screen", "Checks", "Long-Term Score",
    "Data Completeness", "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity",
    "Promoter Holding", "Pledged Percentage", "Failure Reasons", "Company URL",
]
st.dataframe(
    top_candidates[[c for c in candidate_cols if c in top_candidates.columns]],
    use_container_width=True,
    hide_index=True,
    column_config={"Company URL": st.column_config.LinkColumn("Company URL")},
)

st.subheader("📊 All analysed companies")
view_cols = [
    "Rank", "Company", "Candidate Tier", "Strict Screen", "Checks", "Long-Term Score",
    "Data Completeness", "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity",
    "Promoter Holding", "Pledged Percentage", "Sales Growth 3Y", "Sales Growth 5Y",
    "Profit Growth 3Y", "Profit Growth 5Y", "Failure Reasons", "Company URL",
]
st.dataframe(
    result_df[[c for c in view_cols if c in result_df.columns]].head(top_n),
    use_container_width=True,
    hide_index=True,
    column_config={"Company URL": st.column_config.LinkColumn("Company URL")},
)

st.subheader("🔎 Company inspection")
selected_company = st.selectbox("Select company", result_df["Company"].tolist())
selected = result_df[result_df["Company"] == selected_company].iloc[0]
try:
    details = get_company_details(selected["Company URL"])
    strict = evaluate_strict_screen(details)
    score, parts = long_term_score(details)
except Exception as exc:
    st.error(f"Unable to load company details: {exc}")
else:
    a, b, c, d = st.columns(4)
    a.metric("Strict screen", "PASS" if strict["strict_pass"] else "FAIL")
    b.metric("Conditions", f"{strict['passed_count']}/{strict['total_count']}")
    c.metric("Long-term score", f"{score}/100")
    d.metric("Data completeness", f"{details.get('Data Completeness', 0)}%")
    if strict["failed_or_unverified"]:
        st.error("Failed / unverified: " + "; ".join(strict["failed_or_unverified"]))
    else:
        st.success("All 16 strict conditions are currently satisfied with available data.")

    st.markdown("### Long-term research score")
    st.write(parts)
    metric_cols = [
        "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity", "Promoter Holding",
        "Pledged Percentage", "Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y",
        "Profit Growth 5Y", "Sales Latest Quarter", "Net Profit Latest Quarter",
        "Sales Latest Year vs Preceding", "Profit Latest Year vs Preceding", "Free Cash Flow", "CFO/OP",
    ]
    st.dataframe(pd.DataFrame([{k: details.get(k) for k in metric_cols}]), use_container_width=True, hide_index=True)
    if details.get("PEG Source") == "Derived: PE / 5Y profit growth":
        st.caption("PEG is derived as PE ÷ 5-year profit growth because a direct PEG field was unavailable. Treat it as a proxy.")
    if details.get("Pledged Percentage") is None:
        st.caption("Pledged percentage is unavailable, so the strict rule remains unverified rather than being treated as a pass.")

st.subheader("📥 Export")
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    result_df.to_excel(writer, index=False, sheet_name="Screened Companies")
    if not failures_df.empty:
        failures_df.to_excel(writer, index=False, sheet_name="Failures")
st.download_button(
    "📥 Download Excel",
    excel_buffer.getvalue(),
    "long_term_screener.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.download_button("📥 Download CSV", result_df.to_csv(index=False), "long_term_screener.csv", "text/csv")

if show_failures and not failures_df.empty:
    st.subheader("⚠️ Companies that could not be analysed")
    st.dataframe(failures_df, use_container_width=True, hide_index=True)

with st.expander("ℹ️ How the five-candidate rule works"):
    st.write(
        "The 16 conditions are always evaluated strictly. The app now reads all pages of the selected sector and analyses companies in batches. "
        "If five strict PASS companies exist, only those are shown as strict-pass candidates. If fewer than five pass, the app shows five closest research candidates based on passed-condition count and the long-term score. "
        "This guarantees a useful five-row research shortlist when at least five company pages can be fetched, without pretending that a FAIL is a PASS."
    )
