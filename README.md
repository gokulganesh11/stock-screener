# Stock Research Platform

A Streamlit-based research workspace for sector screening, fundamental analysis, watchlists, history and alerts using public Screener.in data.

## Current architecture

- `home.py` — main Streamlit entry point
- `long_term_engine.py` — strict 10–20 year screening and candidate ranking
- `research_engine.py` — shared/general sector analysis workflow
- `screener.py` — sector-table retrieval and company URL mapping
- `company_scraper.py` — company fundamental, annual, quarterly and ownership extraction
- `score.py` — strict filter plus explainable long-term ranking
- `pages/` — Streamlit research modules
- `history_manager.py` / `storage.py` — saved research snapshots and watchlist persistence
- `alerts.py` — changes between snapshots

## 10–20 year screening rules

A company is eligible for the strict shortlist only when **all** of these are satisfied and the source data is available:

- ROE > 10%
- ROCE > 10%
- P/E < 50
- PEG < 1.5
- Debt / Equity < 1
- EPS > 10
- Promoter holding > 50%
- Pledged percentage < 10%
- Sales growth 5Y > 10%
- Profit growth 5Y > 10%
- Sales growth 3Y > 10%
- Profit growth 3Y > 10%
- Latest annual sales > preceding year sales
- Latest annual net profit > preceding year net profit
- Latest quarter sales > 0
- Latest quarter net profit > 0

PEG is derived as P/E divided by 5-year profit growth when both values are available. Missing pledge, cash-flow or other source fields are **not** assumed to be zero or positive.

## Additional long-term quality signals

The strict filter is followed by a separate research score that can reward:

- 10-year sales and profit growth
- 5-year average ROE/ROCE
- lower leverage, with extra credit below 0.5 debt/equity
- positive free cash flow in most of the last five years
- operating cash-flow evidence
- latest-quarter year-over-year sales/profit growth
- promoter ownership and low pledged holding
- reasonable P/E and PEG

These additions are screening heuristics for research. They do not establish that a stock will become a multibagger or predict future returns.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run home.py
```

Open `http://localhost:8501`.

## Design principles

1. Separate data collection from scoring and UI.
2. Never silently convert missing data into positive evidence.
3. Preserve failed-company information so users can assess data completeness.
4. Keep scoring transparent and explainable.
5. Treat scores as screening heuristics, not predictions or guarantees.
6. Never force a top-five list when fewer than five companies pass the strict screen.

## Data source

The current collector reads public Screener.in sector/company pages. Website structure and availability can change; scraping failures are surfaced in the UI.

## Development status

The project is being refactored from several standalone scripts into one maintainable Streamlit application. Changes are developed on the `codex/production-refactor` branch before merge to `main`.
