# Stock Research Platform

A Streamlit-based stock research workspace for sector discovery, strict fundamental screening, long-term research scoring, watchlists and historical tracking.

## Run locally

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run home.py
```

## What was fixed

### 1. Exact 16-condition long-term screen

The Stock Screener uses the requested rules:

- ROE > 10%
- ROCE > 10%
- PE < 50
- PEG < 1.5
- Debt/Equity < 1
- EPS > 10
- Promoter holding > 50%
- Pledged percentage < 10%
- Sales growth 3Y and 5Y > 10%
- Profit growth 3Y and 5Y > 10%
- Latest annual sales > preceding year
- Latest annual net profit > preceding year
- Latest-quarter sales > 0
- Latest-quarter net profit > 0

Missing data is **unverified**, never silently treated as a pass.

### 2. Exact Screener query support

The app can now read a public saved Screener query from its `/screens/...` URL and paginate through all result pages. This is important when the browser shows hundreds of query results: an unsaved query is tied to the browser session and cannot reliably be reproduced by a separate Streamlit process.

Save the query on Screener.in and paste its public URL into the Stock Screener page.

### 3. Five-stock shortlist

The app attempts to read enough company pages to produce a minimum five-row **research shortlist**. If five stocks do not satisfy every strict rule, the app shows the closest research candidates and clearly keeps their status as FAIL. It never fabricates a strict PASS.

### 4. Screener 429 protection

Requests are spaced, retried with exponential backoff, cached and processed in batches. This reduces `429 Too Many Requests` errors.

### 5. Complete live sector catalogue

Sector Comparison now reads Screener's live **Industries Overview** instead of using a stale five/ten-sector hardcoded list. The page includes all industries returned by Screener, with live company count, median P/E, sales growth, OPM, ROCE and 1Y return data.

A transparent **Research Priority Score** orders industries using profitability, growth, operating margin, valuation and breadth. It is a research ordering tool, not a forecast of 10–20 year returns.

### 6. Company drilldown

Any industry can be opened to read its companies and then inspect a company against the same 16 strict rules and the long-term research score.

## Research score

After the strict screen, a separate 0–100 research score considers:

- Quality
- Multi-year growth
- Balance sheet
- Valuation
- Ownership
- Consistency
- Cash flow

This score is deliberately separate from the strict screen and is not a prediction of future returns.

## Reliability settings

Optional environment variables:

```powershell
$env:SCREENER_REQUEST_DELAY="1.8"
$env:SCREENER_TIMEOUT="30"
$env:SCREENER_MAX_SECTOR_PAGES="20"
```

If Screener continues returning 429 responses, increase `SCREENER_REQUEST_DELAY`.

## Project structure

- `home.py` — multi-page Streamlit entry point
- `home_dashboard.py` — home dashboard
- `app_v2.py` — strict 10–20 year research screener
- `long_term_screen.py` — strict rules and research score
- `screener.py` — paginated sector and public-screen reader
- `company_scraper.py` — company fundamentals extraction, caching and rate limiting
- `sector_urls.py` — live Screener industry catalogue
- `sector_compare_live.py` — complete sector comparison and drilldown
- `watchlist.py` — watchlist module
- `sector_history.py` — historical snapshots
- `alerts.py` — change alerts

## Important data caveats

The application depends on data exposed by the source website. PEG may be derived as `PE / 5Y profit growth` when a direct PEG field is unavailable, and the app labels that source. Pledged percentage is treated as zero only when the shareholding table exists and no pledge is reported; otherwise it remains unverified.

Always inspect the underlying company data and use your own investment judgement. A screen or research score cannot guarantee multibagger returns over 10–20 years.
