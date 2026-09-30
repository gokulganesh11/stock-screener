import re
from io import BytesIO

import pandas as pd
import streamlit as st

from company_scraper import get_company_details
from long_term_screen import evaluate_strict_screen, long_term_score
from screener import get_sector_stocks

st.set_page_config(page_title="10–20 Year Multibagger Screener", page_icon="🔎", layout="wide")

SECTORS = {"Capital Markets": "https://www.screener.in/market/IN05/IN0501/IN050103/", "Custom URL": ""}


def clean_company_url(value):
    match = re.search(r"https://www\.screener\.in/company/[A-Za-z0-9\-/]+/?", str(value))
    return match.group(0) if match else str(value).strip()


@st.cache_data(ttl=21600, show_spinner=False)
def run_sector_analysis(url):
    sector_df = get_sector_stocks(url)
    results, failures = [], []
    for _, row in sector_df.iterrows():
        company = str(row.get("Company", "Unknown")).strip()
        company_url = clean_company_url(row.get("Company URL", ""))
        if not company_url or company_url.lower() in {"none", "nan"}:
            failures.append({"Company": company, "Company URL": company_url, "Error": "Company URL is missing"})
            continue
        try:
            details = get_company_details(company_url)
            strict = evaluate_strict_screen(details)
            score, parts = long_term_score(details)
            results.append({
                "Company": company, "Company URL": company_url,
                "Strict Screen": "PASS" if strict["strict_pass"] else "FAIL",
                "Strict Rank": 1 if strict["strict_pass"] else 0,
                "Checks": f"{strict['passed_count']}/{strict['total_count']}",
                "Passed Checks": strict["passed_count"], "Long-Term Score": score,
                "Quality Score": parts["Quality"], "Growth Score": parts["Growth"],
                "Balance Sheet Score": parts["Balance Sheet"], "Valuation Score": parts["Valuation"],
                "Ownership Score": parts["Ownership"], "Consistency Score": parts["Consistency"],
                "Cash Flow Score": parts["Cash Flow"], "Data Completeness": details.get("Data Completeness"),
                "ROE": details.get("ROE"), "ROCE": details.get("ROCE"), "PE": details.get("PE"),
                "PEG Ratio": details.get("PEG Ratio"), "PEG Source": details.get("PEG Source"),
                "EPS": details.get("EPS"), "Debt to Equity": details.get("Debt to Equity"),
                "Promoter Holding": details.get("Promoter Holding"), "Pledged Percentage": details.get("Pledged Percentage"),
                "Sales Growth 3Y": details.get("Sales Growth 3Y"), "Sales Growth 5Y": details.get("Sales Growth 5Y"),
                "Profit Growth 3Y": details.get("Profit Growth 3Y"), "Profit Growth 5Y": details.get("Profit Growth 5Y"),
                "Sales Latest Quarter": details.get("Sales Latest Quarter"), "Net Profit Latest Quarter": details.get("Net Profit Latest Quarter"),
                "Sales Latest Year vs Preceding": details.get("Sales Latest Year vs Preceding"),
                "Profit Latest Year vs Preceding": details.get("Profit Latest Year vs Preceding"),
                "Free Cash Flow": details.get("Free Cash Flow"), "CFO/OP": details.get("CFO/OP"),
                "Failure Reasons": "; ".join(strict["failed_or_unverified"]),
            })
        except Exception as exc:
            failures.append({"Company": company, "Company URL": company_url, "Error": str(exc)})
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(["Strict Rank", "Passed Checks", "Long-Term Score", "Data Completeness"], ascending=[False, False, False, False]).reset_index(drop=True)
        result_df.insert(0, "Rank", range(1, len(result_df) + 1))
    return result_df, pd.DataFrame(failures)


st.title("🔎 10–20 Year Multibagger Screener")
st.caption("Strict fundamentals first, then a transparent long-term research score. PASS means the required data was available and every rule was satisfied; it is not a forecast or guarantee.")

with st.sidebar:
    st.header("⚙️ Research Settings")
    st.info("The first run may take time because requests are deliberately spaced to reduce Screener 429 errors. Results are cached for 6 hours.")
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
st.markdown("**ROE > 10% · ROCE > 10% · PE < 50 · PEG < 1.5 · Debt/Equity < 1 · EPS > 10 · Promoter > 50% · Pledged < 10% · Sales/Profit growth 3Y & 5Y > 10% · Sales & profit latest year > preceding year · latest-quarter sales & profit > 0**")

if st.button("🚀 Analyze Sector", type="primary", use_container_width=True):
    if not sector_url.strip():
        st.error("Please provide a Screener.in sector URL.")
        st.stop()
    with st.spinner("Collecting sector companies and analyzing fundamentals…"):
        result_df, failures_df = run_sector_analysis(sector_url)
    st.session_state["lt_results"] = result_df
    st.session_state["lt_failures"] = failures_df

result_df = st.session_state.get("lt_results", pd.DataFrame())
failures_df = st.session_state.get("lt_failures", pd.DataFrame())
if result_df.empty:
    st.info("Run the analysis to see the strict screen and long-term research ranking.")
    st.stop()

strict_pass_df = result_df[result_df["Strict Screen"] == "PASS"].copy()
near_pass_df = result_df[result_df["Strict Screen"] == "FAIL"].copy()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Companies found", len(result_df) + len(failures_df)); m2.metric("Analyzed", len(result_df)); m3.metric("Strict PASS", len(strict_pass_df)); m4.metric("Failures", len(failures_df))

if not strict_pass_df.empty:
    st.success(f"{len(strict_pass_df)} companies currently satisfy all 16 strict conditions.")
    st.subheader("🎯 Top 5 strict-pass candidates")
    st.dataframe(strict_pass_df.head(5), use_container_width=True, hide_index=True, column_config={"Company URL": st.column_config.LinkColumn("Company URL")})
else:
    st.warning("No company passed all 16 conditions. The app will not falsely label five stocks as strict passes.")
    st.subheader("🧭 Closest matches for manual research")
    st.caption("These names fail or have unverified conditions. They are shown only to help investigate why the strict filter is empty.")
    st.dataframe(near_pass_df.sort_values(["Passed Checks", "Long-Term Score"], ascending=False).head(5), use_container_width=True, hide_index=True, column_config={"Company URL": st.column_config.LinkColumn("Company URL")})

st.subheader("📊 All screened companies")
view_cols = ["Rank", "Company", "Strict Screen", "Checks", "Long-Term Score", "Data Completeness", "ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity", "Promoter Holding", "Pledged Percentage", "Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y", "Profit Growth 5Y", "Failure Reasons", "Company URL"]
st.dataframe(result_df[[c for c in view_cols if c in result_df.columns]].head(top_n), use_container_width=True, hide_index=True, column_config={"Company URL": st.column_config.LinkColumn("Company URL")})

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
    a.metric("Strict screen", "PASS" if strict["strict_pass"] else "FAIL"); b.metric("Conditions", f"{strict['passed_count']}/{strict['total_count']}"); c.metric("Long-term score", f"{score}/100"); d.metric("Data completeness", f"{details.get('Data Completeness', 0)}%")
    if strict["failed_or_unverified"]:
        st.error("Failed / unverified: " + "; ".join(strict["failed_or_unverified"]))
    else:
        st.success("All 16 strict conditions are currently satisfied with available data.")
    st.markdown("### Long-term research score"); st.write(parts)
    metric_cols = ["ROE", "ROCE", "PE", "PEG Ratio", "EPS", "Debt to Equity", "Promoter Holding", "Pledged Percentage", "Sales Growth 3Y", "Sales Growth 5Y", "Profit Growth 3Y", "Profit Growth 5Y", "Sales Latest Quarter", "Net Profit Latest Quarter", "Sales Latest Year vs Preceding", "Profit Latest Year vs Preceding", "Free Cash Flow", "CFO/OP"]
    st.dataframe(pd.DataFrame([{k: details.get(k) for k in metric_cols}]), use_container_width=True, hide_index=True)
    if details.get("PEG Source") == "Derived: PE / 5Y profit growth": st.caption("PEG is derived as PE ÷ 5-year profit growth because a direct PEG field was unavailable. Treat it as a proxy.")
    if details.get("Pledged Percentage") is None: st.caption("Pledged percentage is unavailable, so the strict rule remains unverified rather than being treated as a pass.")

st.subheader("📥 Export")
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    result_df.to_excel(writer, index=False, sheet_name="Screened Companies")
    if not failures_df.empty: failures_df.to_excel(writer, index=False, sheet_name="Failures")
st.download_button("📥 Download Excel", excel_buffer.getvalue(), "long_term_screener.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("📥 Download CSV", result_df.to_csv(index=False), "long_term_screener.csv", "text/csv")
if show_failures and not failures_df.empty:
    st.subheader("⚠️ Companies that could not be analyzed")
    st.dataframe(failures_df, use_container_width=True, hide_index=True)

with st.expander("ℹ️ Why the app may show fewer than five strict candidates"):
    st.write("The screen is intentionally strict. Missing source data is treated as unverified, not as a pass. This prevents the application from inventing PEG, pledge, EPS or growth values just to produce five names. The long-term score adds quality, growth, balance-sheet, valuation, ownership, consistency and cash-flow evidence after the strict filter.")
