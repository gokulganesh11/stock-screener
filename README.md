# Stock Research Platform

A Streamlit-based stock research workspace focused on sector screening, long-term fundamental research, watchlists and historical tracking.

## Main application

Run:

```powershell
python -m streamlit run home.py
```

## Long-term screener

The **Stock Screener** page applies the requested 16-condition strict filter:

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

Missing data is **unverified**, not a pass. The application therefore does not manufacture five candidates when fewer than five stocks satisfy the complete screen.

After the strict filter, a separate 0–100 research score considers quality, growth, balance sheet, valuation, ownership, consistency and cash-flow evidence. It is a research ranking, not a return prediction.

## Screener reliability

Screener requests are deliberately paced, cached and retried for transient failures. This reduces the `429 Too Many Requests` problem seen when a whole sector is scanned.

Optional environment variables:

```powershell
$env:SCREENER_REQUEST_DELAY="1.2"
$env:SCREENER_TIMEOUT="30"
```

Increase the delay if Screener continues returning 429 responses.

## Installation

Activate the virtual environment and install the project dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Important runtime packages include `streamlit`, `beautifulsoup4`, `lxml`, `pandas`, `requests` and `openpyxl`.

## Project structure

- `home.py` — multi-page Streamlit entry point
- `home_dashboard.py` — home dashboard
- `app_v2.py` — strict long-term stock screener
- `long_term_screen.py` — strict rules and research score
- `screener.py` — sector/company URL collection
- `company_scraper.py` — company fundamentals extraction, caching and rate limiting
- `sector_compare_live.py` — sector comparison
- `watchlist.py` — watchlist module
- `sector_history.py` — historical snapshots
- `alerts.py` — change alerts

## Data caveat

The application depends on data exposed by the source website. PEG may be derived when a direct PEG field is unavailable, and missing pledged-share data remains unverified. Always inspect the underlying company data before making an investment decision.
