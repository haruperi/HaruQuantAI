"""Review and mutation operate on stored history rather than generated samples."""

import pytest
from app.workspace.data_manager.data.review import DatasetReview


def test_review_pagination_aggregation_and_gaps(recorded_history):
    gateway, identifier, _ = recorded_history
    review = DatasetReview(gateway, identifier)
    page = review.rows(2, 2)
    assert page["total"] == 6
    assert page["rows"][0]["date"].startswith("2025-01-06T09:02")
    hourly = review.frame(timeframe="H1")
    assert len(hourly) == 1
    assert hourly.Volume.iloc[0] == 78
    issues = review.quality()["issues"]
    assert {item["date"] for item in issues if item["kind"] == "Gap"} == {
        "2025-01-06T09:03:00+00:00"
    }


def test_review_edits_and_deletions_persist(recorded_history):
    gateway, identifier, _ = recorded_history
    review = DatasetReview(gateway, identifier)
    rows = review.rows()["rows"]
    review.save_changes(
        [{**rows[0], "close": 1.11}], [rows[1]["date"]], review.record["updated_at"]
    )
    saved = DatasetReview(gateway, identifier)
    assert saved.rows()["total"] == 5
    assert saved.rows()["rows"][0]["close"] == 1.11
    with pytest.raises(Exception, match="History changed"):
        review.save_changes([], [], review.record["updated_at"])


def test_rename_republishes_files_and_preserves_history(recorded_history):
    from app.workspace.data_manager.data.feature import Data

    gateway, identifier, _ = recorded_history
    before = DatasetReview(gateway, identifier).frame()
    saved = Data(gateway).edit(identifier, {"symbol": "RENAMED", "category": "CFD"})
    assert saved["symbol"] == "RENAMED" and saved["category"] == "CFD"
    assert "renamed" in saved["path"]
    after = DatasetReview(gateway, identifier).frame()
    import pandas as pd

    pd.testing.assert_frame_equal(before, after)


def test_clear_removes_owned_cache_and_preserves_unrelated_files(recorded_history):
    from pathlib import Path

    from app.include.market_storage import catalog_paths
    from app.workspace.data_manager.data.feature import Data

    gateway, identifier, root = recorded_history
    paths = [
        Path(value)
        for value in catalog_paths(DatasetReview(gateway, identifier).record)
    ]
    unrelated = root / "unrelated.parquet"
    unrelated.write_bytes(b"keep")
    assert Data(gateway).clear(identifier)["success"]
    assert all(not path.exists() for path in paths)
    assert unrelated.read_bytes() == b"keep"
    assert DatasetReview(gateway, identifier).rows()["total"] == 0


def test_saved_session_lunch_excludes_closed_market_gap(recorded_history):
    import json
    import sqlite3
    from contextlib import closing

    gateway, identifier, _ = recorded_history
    windows = [
        {
            "day_from": "Mon",
            "day_to": "Fri",
            "start_time": "09:00",
            "end_time": "09:02",
            "eod": False,
        },
        {
            "day_from": "Mon",
            "day_to": "Fri",
            "start_time": "09:04",
            "end_time": "17:00",
            "eod": False,
        },
    ]
    with closing(sqlite3.connect(gateway.database_path)) as connection:
        connection.execute(
            "CREATE TABLE datamgr_sessions (id INTEGER PRIMARY KEY, name TEXT, timezone TEXT, windows_json TEXT, holidays_json TEXT)"
        )
        connection.execute(
            "INSERT INTO datamgr_sessions VALUES (1, 'Lunch', 'UTC', ?, '[]')",
            (json.dumps(windows),),
        )
        connection.execute(
            "UPDATE datamgr_datasets SET session_id=1 WHERE id=?", (identifier,)
        )
        connection.commit()
    quality = DatasetReview(gateway, identifier).quality()
    assert quality["gap_policy"] == "saved session"
    assert quality["counts"].get("Gap", 0) == 0
