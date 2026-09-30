import pandas as pd

import storage


def test_snapshot_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / ".data")
    monkeypatch.setattr(storage, "HISTORY_DIR", tmp_path / ".data" / "history")
    monkeypatch.setattr(storage, "WATCHLIST_FILE", tmp_path / ".data" / "watchlist.csv")

    df = pd.DataFrame([
        {"Sector": "Capital Markets", "Average Score": 12.5},
        {"Sector": "Power", "Average Score": 9.0},
    ])
    path = storage.save_snapshot(df, "test")
    loaded = storage.load_snapshot(path)

    pd.testing.assert_frame_equal(loaded, df)


def test_compare_snapshots():
    old = pd.DataFrame([
        {"Sector": "A", "Average Score": 10.0},
        {"Sector": "B", "Average Score": 8.0},
    ])
    new = pd.DataFrame([
        {"Sector": "A", "Average Score": 12.0},
        {"Sector": "B", "Average Score": 7.0},
    ])
    result = storage.compare_snapshots(old, new)
    assert result.iloc[0]["Sector"] == "A"
    assert result.iloc[0]["Score Change"] == 2.0
