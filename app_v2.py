import re
from io import BytesIO

import pandas as pd
import streamlit as st

from company_scraper import get_company_details
from long_term_screen import evaluate_strict_screen, long_term_score
from screener import get_public_screen_stocks, get_sector_stocks

st.set_page_config(page_title="10–20 Year Multibagger Screener", page_icon="🔎", layout="wide")

STRICT_QUERY = (
    "Return on equity > 10 AND Return on capital employed > 10 AND Price to Earning < 50 "
    "AND PEG Ratio < 1.5 AND Debt to equity < 1 AND EPS > 10 AND Promoter holding > 50 "
    "AND Pledged percentage < 10 AND Sales growth 5Years > 10 AND Profit growth 5Years > 10 "
    "AND Sales growth 3Years > 10 AND Profit growth 3Years > 10 AND Sales > Sales preceding year "
    "AND Net Profit > Net Profit preceding year AND Sales latest quarter > 0 AND Net profit latest quarter > 0"
)

MIN_CANDIDATES = 5
ANALYSIS_BATCH = 10
MAX_DETAIL_COMPANIES = 50


def clean_company_url(value):
    match = re.search(r"https://www\.screener\.in/company/[A-Za-z0-9_\-/]+/?", str(value))
    return match.group(0) if match else str(value).strip()


def _number(value):
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _priority_score(row):
    """Pre-score only. It controls fetch order, never PASS/FAIL."""
    score = 0.0
    for col, weight in [("ROCE  %", 0.7), ("Qtr Profit Var  %", 0.15), ("Qtr Sales Var  %", 0.1)]:
        value = _number(row.get(col))
        if value is not None and value > 0:
            score += min(value, 50) * weight
    pe = _number(row.get("P/E"))
    if pe is not None and 0 < pe < 50:
        score += 20 + (5 if pe < 30 else 0)
    market_cap = _number(row.get("Mar Cap  Rs.Cr."))
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


def _prepare_source(df):
    df = df.copy()
    if df.empty:
        return df
    if "Company URL" not in df.columns:
        df["Company URL"] = None
    df["_priority"] = df.apply(_priority_score, axis=1)
    return df.sort_values("_priority", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=21600, show_spinner=False)
def run_analysis(source_url, source_kind, max_detail=MAX_DETAIL_COMPANIES):
    if source_kind == "Exact saved Screener query":
        source_df = get_public_screen_stocks(source_url)
    else:
        source_df = get_sector_stocks(source_url)
    source_df = _prepare_source(source_df)

    results, failures = [], []
    for start in range(0, min(len(source_df), max_detail), ANALYSIS_BATCH):
        batch = source_df.iloc[start:start + ANALYSIS_BATCH]
        for _, row in batch.iterrows():
            result, failure = _analyse_company(row)
            if result is not None:
                results.append(result)
            elif failure is not None:
                failures.append(failure)

        # Five candidates are guaranteed as soon as five company pages are
        # successfully readable. Strict PASS remains strict; FAIL is never relabelled.
        if len(results) >= MIN_CANDIDATES and start + ANALYSIS_BATCH >= MIN_CANDIDATES * 2:
            break

    result_df = pd.DataFrame(results)
    failures_df = pd.DataFrame(failures)
    if result_df.empty:
        return result_df, failures_df, 0, len(source_df)

    result_df["Candidate Tier"] = "Research candidate"
    result_df.loc[result_df["Passed Checks"] >= 14, "Candidate Tier"] = "Very close"
    result_df.loc[result_df["Strict Screen"] == "PASS", "Candidate Tier"] = "Strict PASS"
    result_df = result_df.sort_values(
        ["Strict Screen", "Passed Checks", "Long-Term Score", "Data Completeness"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
    result_df.insert(0, "Rank", range(1, len(result_df) + 1))
    return result_df, failures_df, len(result_df), len(source_df)


st.title("🔎 10–20 Year Multibagger Screener")
st.caption(
    "Exact 16-condition screen + transparent long-term research score. "
    "A PASS means every required field was available and satisfied; it is not a forecast or guarantee."
)

with st.sidebar:
    st.header("⚙️ Research Settings")
    mode = st.radio("Data source", ["Exact saved Screener query", "Sector page"], index=0)
    st.info(
        "For the exact Screener query, save your query on Screener.in and paste its public /screens/... URL. "
        "This is the only reliable way for the app to reproduce the same 204-result query you see in your browser."
    )
    if st.button("🧹 Clear cached market data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if mode == "Exact saved Screener query":
    source_url = st.text_input(
        "Public Screener query URL",
        placeholder="https://www.screener.in/screens/123456/your-screen/",
    )
    st.markdown("**Your exact 16-condition query**")
    st.code(STRICT_QUERY, language="text")
    st.caption("Save this query in Screener.in, then paste the public URL above. The app will read all result pages, not only page 1.")
else:
    source_url = st.text_input(
        "Screener.in sector URL",
        value="https://www.screener.in/market/",
    )

c1, c2, c3 = st.columns(3)
with c1:
    max_detail = st.slider("Detailed company pages to inspect", 10, 50, 30, 5)
with c2:
    show_failures = st.checkbox("Show analysis failures", value=True)
with c3:
    st.metric("Required shortlist", "5")

st.subheader("🎯 Strict 16-condition filter")
st.markdown(
    "**ROE > 10% · ROCE > 10% · PE < 50 · PEG < 1.5 · Debt/Equity < 1 · EPS > 10 · "
    "Promoter > 50% · Pledged < 10% · Sales/Profit growth 3Y & 5Y > 10% · "
    "Sales & profit latest year > preceding year · latest-quarter sales & profit > 0**"
)

if st.button("🚀 Analyze", type="primary", use_container_width=True):
    if not source_url.strip():
        st.error("Please provide a source URL.")
        st.stop()
    if mode == "Exact saved Screener query" and "/screens/" not in source_url:
        st.error("Please paste a public saved Screener URL containing /screens/.")
        st.stop()
    with st.spinner("Reading all result pages and analysing company pages in throttled batches…"):
        result_df, failures_df, analysed_count, source_count = run_analysis(source_url, mode, max_detail)
    st.session_state.update({"lt_results": result_df, "lt_failures": failures_df, "lt_analysed": analysed_count, "lt_source_count": source_count})

result_df = st.session_state.get("lt_results", pd.DataFrame())
failures_df = st.session_state.get("lt_failures", pd.DataFrame())
analysed_count = st.session_state.get("lt_analysed", 0)
source_count = st.session_state.get("lt_source_count", 0)

if result_df.empty:
    st.info("Run the analysis to see candidates. No fake five-row result is generated when source pages cannot be read.")
    st.stop()

strict_pass_df = result_df[result_df["Strict Screen"] == "PASS"].copy()
near_pass_df = result_df[result_df["Strict Screen"] != "PASS"].copy()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Source results", source_count)
m2.metric("Detailed pages read", analysed_count)
m3.metric("Strict PASS", len(strict_pass_df))
m4.metric("Fetch failures", len(failures_df))

if len(strict_pass_df) >= MIN_CANDIDATES:
    st.success(f"{len(strict_pass_df)} companies satisfy all 16 strict conditions in the inspected set.")
    st.subheader("🎯 Top 5 strict-pass candidates")
    top_candidates = strict_pass_df.head(5)
else:
    st.warning(
        f"Only {len(strict_pass_df)} inspected companies pass all 16 conditions. "
        "The app will not falsely label five companies as strict PASS."
    )
    st.subheader("🎯 Top 5 closest research candidates")
    st.caption("FAIL remains FAIL. These are research candidates ranked by passed conditions and the long-term research score.")
    top_candidates = near_pass_df.head(MIN_CANDIDATES)

if len(top_candidates) < MIN_CANDIDATES:
    st.error(
        f"Only {len(top_candidates)} company pages were successfully read. "
        "Increase 'Detailed company pages to inspect' or retry later if Screener is throttling requests."
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

st.subheader("📊 All inspected companies")
view_cols = [
    "Rank", "Company", "Candidate Tier", "Strict Screen", "Checks", "Long-Term Score",
    "Data Completeness", "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity",
    "Promoter Holding", "Pledged Percentage", "Sales Growth 3Y", "Sales Growth 5Y",
    "Profit Growth 3Y", "Profit Growth 5Y", "Failure Reasons", "Company URL",
]
st.dataframe(
    result_df[[c for c in view_cols if c in result_df.columns]],
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
        st.caption("PEG is derived as PE ÷ 5-year profit growth because a direct PEG field was unavailable; treat it as a proxy.")

st.subheader("📥 Export")
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    result_df.to_excel(writer, index=False, sheet_name="Screened Companies")
    if not failures_df.empty:
        failures_df.to_excel(writer, index=False, sheet_name="Failures")
st.download_button("📥 Download Excel", excel_buffer.getvalue(), "long_term_screener.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("📥 Download CSV", result_df.to_csv(index=False), "long_term_screener.csv", "text/csv")

if show_failures and not failures_df.empty:
    st.subheader("⚠️ Companies that could not be analysed")
    st.dataframe(failures_df, use_container_width=True, hide_index=True)

with st.expander("ℹ️ Why the app now uses a saved Screener query"):
    st.write(
        "The Screener page shown in your browser can contain hundreds of results, but an unsaved browser query is tied to your browser session. "
        "A Streamlit app cannot reliably reproduce that private unsaved query. Save it on Screener.in and paste the public /screens/ URL. "
        "The app then reads every result page, orders candidates for detailed inspection, and verifies the same 16 conditions independently."
    )
