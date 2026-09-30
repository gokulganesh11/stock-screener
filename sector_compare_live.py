import re
from io import BytesIO, StringIO

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from company_scraper import get_company_details
from long_term_screen import evaluate_strict_screen, long_term_score
from screener import get_sector_stocks

st.set_page_config(page_title="Sector Comparison", page_icon="📊", layout="wide")

BASE_URL = "https://www.screener.in"
MARKET_URL = f"{BASE_URL}/market/"
EXPECTED_NUMERIC = [
    "No. of Companies", "Total Market Cap.", "Median Market Cap.", "Median P/E",
    "Wtd. Avg Sales Growth", "Wtd. Avg OPM", "Wtd. Avg ROCE", "Median 1Y Return"
]


def _num(value):
    try:
        text = str(value).replace(",", "").replace("%", "").strip()
        if text.lower() in {"nan", "none", "n/a", "-", "--", ""}:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _load_industries():
    response = requests.get(
        MARKET_URL,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-IN,en;q=0.9"},
        timeout=30,
    )
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        name = " ".join(a.get_text(" ", strip=True).split())
        href = a.get("href", "")
        if name and "/market/" in href and name != "Industry":
            if href.startswith("/"):
                href = BASE_URL + href
            if re.match(r"https://www\.screener\.in/market/[^\s]+/?$", href):
                links[name] = href

    tables = pd.read_html(StringIO(html))
    if not tables:
        raise RuntimeError("No industry table returned by Screener")
    df = max(tables, key=len).copy()
    df.columns = [str(c).strip() for c in df.columns]
    industry_col = next((c for c in df.columns if c.lower() == "industry"), None)
    if industry_col is None:
        raise RuntimeError(f"Screener industry table has no Industry column. Columns: {list(df.columns)}")
    df = df.rename(columns={industry_col: "Sector"})
    df["Sector"] = df["Sector"].astype(str).str.strip()
    df["URL"] = df["Sector"].map(links)
    for col in EXPECTED_NUMERIC:
        if col not in df.columns:
            df[col] = None
        df[col] = df[col].map(_num)
    df = df[df["URL"].notna()].drop_duplicates("Sector").reset_index(drop=True)
    return df


@st.cache_data(ttl=21600, show_spinner=False)
def load_industries():
    return _load_industries()


def _clip(value, low, high):
    if value is None:
        return None
    return max(low, min(high, value))


def research_priority(row):
    """Transparent industry-level research score; not a return forecast."""
    roce = _clip(_num(row.get("Wtd. Avg ROCE")), 0, 40)
    growth = _clip(_num(row.get("Wtd. Avg Sales Growth")), 0, 40)
    opm = _clip(_num(row.get("Wtd. Avg OPM")), 0, 50)
    pe = _num(row.get("Median P/E"))
    companies = _num(row.get("No. of Companies"))

    score = 0.0
    weights = 0.0
    if roce is not None:
        score += roce / 40 * 35
        weights += 35
    if growth is not None:
        score += growth / 40 * 30
        weights += 30
    if opm is not None:
        score += opm / 50 * 20
        weights += 20
    if pe is not None and pe > 0:
        valuation = 100 if pe <= 15 else 80 if pe <= 25 else 60 if pe <= 40 else 35 if pe <= 60 else 15
        score += valuation / 100 * 10
        weights += 10
    if companies is not None:
        score += min(companies / 50, 1) * 5
        weights += 5
    return round(score / weights * 100 if weights else 0, 1)


def classify(score):
    if score >= 70:
        return "High research priority"
    if score >= 50:
        return "Medium research priority"
    return "Watch"


st.title("📊 Sector Comparison")
st.caption(
    "Live Screener industry universe. All returned industries are displayed. "
    "The research score is a transparent comparison aid, not a prediction of 10–20 year returns."
)

with st.sidebar:
    st.header("⚙️ Sector Research")
    if st.button("🔄 Refresh live industry data", use_container_width=True):
        load_industries.clear()
        st.rerun()
    st.info("Industry data is cached for 6 hours to reduce repeated requests to Screener.")

try:
    df = load_industries().copy()
except Exception as exc:
    st.error(f"Unable to load the live Screener industry catalogue: {exc}")
    st.stop()

if df.empty:
    st.warning("No industries were returned by Screener.")
    st.stop()

df["Research Priority Score"] = df.apply(research_priority, axis=1)
df["Research Tier"] = df["Research Priority Score"].apply(classify)
df = df.sort_values(
    ["Research Priority Score", "Wtd. Avg ROCE", "Wtd. Avg Sales Growth"],
    ascending=False,
    na_position="last",
).reset_index(drop=True)
df.insert(0, "Rank", range(1, len(df) + 1))

c1, c2, c3 = st.columns(3)
c1.metric("Industries", len(df))
c2.metric("Highest research score", f"{df.iloc[0]['Research Priority Score']}/100")
valid_roce = df.dropna(subset=["Wtd. Avg ROCE"])
c3.metric("Industries with ROCE data", len(valid_roce))

st.subheader("🏆 10–20 Year Research Priority — sector/industry level")
st.dataframe(
    df[["Rank", "Sector", "Research Priority Score", "Research Tier", "No. of Companies", "Median P/E", "Wtd. Avg Sales Growth", "Wtd. Avg OPM", "Wtd. Avg ROCE", "Median 1Y Return"]],
    use_container_width=True,
    hide_index=True,
)

st.subheader("🔎 Sector / Industry Drilldown")
selected_sector = st.selectbox("Select any industry", df["Sector"].tolist())
selected_row = df[df["Sector"] == selected_sector].iloc[0]

x1, x2, x3, x4 = st.columns(4)
x1.metric("Companies", int(selected_row["No. of Companies"]) if pd.notna(selected_row["No. of Companies"]) else "N/A")
x2.metric("ROCE", f"{selected_row['Wtd. Avg ROCE']:.1f}%" if pd.notna(selected_row["Wtd. Avg ROCE"]) else "N/A")
x3.metric("Sales growth", f"{selected_row['Wtd. Avg Sales Growth']:.1f}%" if pd.notna(selected_row["Wtd. Avg Sales Growth"]) else "N/A")
x4.metric("Research score", f"{selected_row['Research Priority Score']}/100")

if st.button("🔬 Load companies in this industry", use_container_width=True):
    with st.spinner("Reading the selected industry page…"):
        try:
            companies = get_sector_stocks(selected_row["URL"], max_pages=20)
            st.session_state["sector_companies"] = companies
            st.session_state["sector_name"] = selected_sector
        except Exception as exc:
            st.error(f"Unable to load companies: {exc}")

companies = st.session_state.get("sector_companies", pd.DataFrame())
if not companies.empty and st.session_state.get("sector_name") == selected_sector:
    st.success(f"Loaded {len(companies)} companies from {selected_sector}.")
    display_cols = [c for c in ["Company", "P/E", "Mar Cap  Rs.Cr.", "Qtr Profit Var  %", "Qtr Sales Var  %", "ROCE  %", "Company URL"] if c in companies.columns]
    st.dataframe(companies[display_cols], use_container_width=True, hide_index=True, column_config={"Company URL": st.column_config.LinkColumn("Company URL")})

    if "Company URL" in companies.columns:
        st.markdown("### Company research")
        selected_company = st.selectbox("Select company", companies["Company"].tolist())
        row = companies[companies["Company"] == selected_company].iloc[0]
        try:
            details = get_company_details(row["Company URL"])
            strict = evaluate_strict_screen(details)
            score, parts = long_term_score(details)
            a, b, c, d = st.columns(4)
            a.metric("Strict conditions", f"{strict['passed_count']}/{strict['total_count']}")
            b.metric("Long-term research score", f"{score}/100")
            c.metric("ROE", details.get("ROE"))
            d.metric("ROCE", details.get("ROCE"))
            if strict["strict_pass"]:
                st.success("All 16 strict conditions currently pass with available data.")
            else:
                st.warning("Not a strict pass: " + "; ".join(strict["failed_or_unverified"]))
            st.write(parts)
        except Exception as exc:
            st.error(f"Company analysis failed: {exc}")

st.subheader("📥 Export all sector rankings")
output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Sector Rankings")
st.download_button("📥 Download Excel", output.getvalue(), "sector_rankings.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("📥 Download CSV", df.to_csv(index=False), "sector_rankings.csv", "text/csv")

with st.expander("ℹ️ Scoring methodology"):
    st.write(
        "Research Priority Score uses available industry-level Wtd. Avg ROCE (35%), Wtd. Avg Sales Growth (30%), "
        "Wtd. Avg OPM (20%), median P/E (10%) and company-count breadth (5%). Missing components are excluded from "
        "the denominator. Missing columns are created as blank fields so a Screener schema change does not crash the page."
    )
