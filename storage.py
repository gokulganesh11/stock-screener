"""Small local persistence layer for research snapshots and watchlists."""

from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

DATA_DIR = Path(".data")
HISTORY_DIR = DATA_DIR / "history"
WATCHLIST_FILE = DATA_DIR / "watchlist.csv"


def ensure_data_dirs():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_watchlist():
    ensure_data_dirs()
    if WATCHLIST_FILE.exists():
        return pd.read_csv(WATCHLIST_FILE)
    return pd.DataFrame(columns=["Stock", "Notes", "Date Added"])


def save_watchlist(df):
    ensure_data_dirs()
    df.to_csv(WATCHLIST_FILE, index=False)


def save_snapshot(df, name="sector_snapshot"):
    ensure_data_dirs()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = HISTORY_DIR / f"{name}_{timestamp}.csv"
    df.to_csv(path, index=False)
    return path


def list_snapshots():
    ensure_data_dirs()
    return sorted(HISTORY_DIR.glob("*.csv"), reverse=True)


def load_snapshot(path):
    return pd.read_csv(path)


def compare_snapshots(old_df, new_df):
    if old_df.empty or new_df.empty or "Sector" not in old_df or "Sector" not in new_df:
        return pd.DataFrame()
    old = old_df[["Sector", "Average Score"]].copy()
    new = new_df[["Sector", "Average Score"]].copy()
    result = old.merge(new, on="Sector", suffixes=(" Old", " New"))
    result["Score Change"] = result["Average Score New"] - result["Average Score Old"]
    return result.sort_values("Score Change", ascending=False)
