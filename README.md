# Stock Research Platform

A Streamlit-based research workspace for sector screening, fundamental analysis, watchlists, history and alerts using public Screener.in data.

## Current architecture

- `home.py` — main Streamlit entry point
- `research_engine.py` — shared sector analysis workflow
- `screener.py` — sector-table retrieval and company URL mapping
- `company_scraper.py` — company fundamental extraction
- `score.py` — explainable scoring heuristic
- `pages/` — Streamlit research modules
- `history_manager.py` — saved screening snapshots
- `alerts.py` — changes between snapshots
- `watchlist.py` — watchlist persistence/export

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
6. Avoid hard-coding conclusions about future stock performance.

## Data source

The current collector reads public Screener.in sector/company pages. Website structure and availability can change; scraping failures are surfaced in the UI.

## Development status

The project is being refactored from several standalone scripts into one maintainable Streamlit application. Changes are developed on the `codex/production-refactor` branch before merge to `main`.
