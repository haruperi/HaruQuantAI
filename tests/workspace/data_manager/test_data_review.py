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

    from app.core.data.market_storage import catalog_paths
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


def test_delete_dataset_removes_empty_dataset_directory(recorded_history):
    from pathlib import Path

    from app.core.data.market_storage import catalog_paths
    from app.workspace.data_manager.data.feature import Data

    gateway, identifier, _ = recorded_history
    record = DatasetReview(gateway, identifier).record
    dataset_dir = Path(record["path"]).resolve()
    paths = [Path(value) for value in catalog_paths(record)]

    assert all(path.exists() for path in paths)
    assert dataset_dir.exists() and dataset_dir.is_dir()

    res = Data(gateway).delete(identifier)
    assert res["success"]
    assert all(not path.exists() for path in paths)
    assert not dataset_dir.exists()


def test_delete_dataset_preserves_dataset_dir_if_unrelated_file_present(
    recorded_history,
):
    from pathlib import Path

    from app.core.data.market_storage import catalog_paths
    from app.workspace.data_manager.data.feature import Data

    gateway, identifier, _ = recorded_history
    record = DatasetReview(gateway, identifier).record
    dataset_dir = Path(record["path"]).resolve()
    paths = [Path(value) for value in catalog_paths(record)]

    unrelated = dataset_dir / "custom_notes.txt"
    unrelated.write_text("user notes")

    res = Data(gateway).delete(identifier)
    assert res["success"]
    assert all(not path.exists() for path in paths)
    assert dataset_dir.exists()
    assert unrelated.read_text() == "user notes"


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


def test_quality_long_history_bounds_expected_grid_and_issue_page(monkeypatch, caplog):
    import pandas as pd
    from app.workspace.data_manager.data import quality

    index = pd.DatetimeIndex(["2020-01-01", "2025-01-01"], tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": [1.0, 1.0],
            "High": [1.0, 1.0],
            "Low": [1.0, 1.0],
            "Close": [1.0, 1.0],
            "Volume": [1, 1],
        },
        index=index,
    )
    original = pd.date_range
    chunk_sizes = []

    def bounded(*args, **kwargs):
        chunk_sizes.append(kwargs["periods"])
        assert kwargs["periods"] <= quality.EXPECTED_CHUNK
        return original(*args, **kwargs)

    monkeypatch.setattr(pd, "date_range", bounded)
    with caplog.at_level("INFO"):
        result = quality.analyze_quality(frame, "M1", None, limit=3, offset=100)
    expected = int((index[-1] - index[0]) / pd.Timedelta(minutes=1)) + 1
    assert expected > 2_000_000
    assert result["counts"]["Gap"] == expected - 2
    assert result["issue_count"] == expected - 2
    assert len(result["issues"]) == 3
    assert result["issues"][0]["date"] == "2020-01-01T01:41:00+00:00"
    assert sum(day["expected"] for day in result["coverage"]) == expected
    assert sum(day["observed"] for day in result["coverage"]) == 2
    assert sum(day["issues"] for day in result["coverage"]) == expected - 2
    assert len(chunk_sizes) > 1
    assert "FR-DATA-QUALITY-bounded-analysis" in caplog.text


def test_quality_counts_percentages_and_independent_pagination():
    import pandas as pd
    from app.workspace.data_manager.data.quality import analyze_quality

    index = pd.DatetimeIndex(
        [
            "2025-01-01T00:00Z",
            "2025-01-01T00:01Z",
            "2025-01-01T00:03Z",
        ]
    )
    frame = pd.DataFrame(
        {"Open": [1, 1, 2], "High": [1, 0, 2], "Low": [1, 1, 2], "Close": [1, 1, 2]},
        index=index,
    )
    first = analyze_quality(frame, "M1", None, limit=1)
    second = analyze_quality(frame, "M1", None, limit=1, offset=1)
    assert first["counts"]["Bad OHLC"] == 1
    assert first["counts"]["Spike"] == 1
    assert first["counts"]["Gap"] == 1
    assert first["issue_count"] == 3
    assert first["percents"]["Gap"] == pytest.approx(100 / 3)
    assert first["issues"][0]["kind"] == "Bad OHLC"
    assert second["issues"][0]["kind"] == "Spike"
    assert first["coverage"] == second["coverage"]
    assert first["counts"] == second["counts"]
    assert analyze_quality(frame.iloc[:0], "M1", None)["issue_count"] == 0
    with pytest.raises(ValueError, match="pagination"):
        analyze_quality(frame, "M1", None, limit=1001)


def test_review_returns_storage_precision(recorded_history, caplog):
    gateway, identifier, _ = recorded_history
    with caplog.at_level("DEBUG"):
        result = DatasetReview(gateway, identifier).rows()
    assert result["price_digits"] == 4
    assert "FR-DATA-REVIEW-price-precision" in caplog.text


def test_review_prefers_linked_instrument_digits(recorded_history, caplog):
    gateway, identifier, _ = recorded_history
    review = DatasetReview(gateway, identifier)
    original = gateway.read_records
    review.record["symbol_definition_id"] = 12

    def records(table, **kwargs):
        if table == "datamgr_symbols":
            assert kwargs["filters"] == {"id": 12}
            return {"success": True, "data": {"records": [{"decimals": 5}]}}
        return original(table, **kwargs)

    from unittest.mock import patch

    with patch.object(gateway, "read_records", side_effect=records):
        with caplog.at_level("DEBUG"):
            assert review.rows()["price_digits"] == 5
    assert "instrument digits=5" in caplog.text


def test_quality_http_keeps_complete_counts_when_paging(recorded_history):
    from app.workspace.data_manager.data.review import register_review_routes
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    gateway, identifier, _ = recorded_history
    app = FastAPI()
    app.state.persistence = gateway
    router = APIRouter()
    register_review_routes(router)
    app.include_router(router)
    with TestClient(app) as client:
        first = client.get(f"/datasets/{identifier}/quality-details?limit=1").json()
        second = client.get(
            f"/datasets/{identifier}/quality-details?limit=1&offset=1"
        ).json()
        summary = client.get(f"/datasets/{identifier}/quality-summary").json()
        assert len(first["data"]["issues"]) == 1
        assert second["data"]["issues"] == []
        assert second["data"]["issue_count"] == 1
        assert summary["data"]["issues"] == []
        assert summary["data"]["counts"] == first["data"]["counts"]
        assert summary["data"]["coverage"] == first["data"]["coverage"]


def test_quality_ticks_duplicates_empty_page_and_unsupported_gap_frequency():
    import pandas as pd
    from app.workspace.data_manager.data.quality import analyze_quality

    index = pd.DatetimeIndex(["2025-01-01T00:00Z"] * 2)
    ticks = pd.DataFrame({"Bid": [1.0, 3.0], "Ask": [1.1, 2.0]}, index=index)
    result = analyze_quality(ticks, "TICK", None, offset=100)
    assert result["issues"] == []
    assert result["counts"]["Duplicate"] == 1
    assert result["counts"]["Invalid quote"] == 1
    assert result["counts"]["Spike"] == 1
    assert result["issue_count"] == 3
    bars = pd.DataFrame(
        {"Open": [1], "High": [1], "Low": [1], "Close": [1]}, index=index[:1]
    )
    assert analyze_quality(bars, "MN1", None)["issue_count"] == 0
    with pytest.raises(ValueError, match="timeframe"):
        analyze_quality(bars, "M0", None)
