"""Unit tests for cache, storage paths, database setup, and quarantine."""

from pathlib import Path
from unittest.mock import patch

import pytest
from app.services.data.storage import (
    clear_data_cache,
    db_helper,
    generate_cache_key,
    get_cached_data,
    load_local_dataset,
    save_market_data,
    set_cached_data,
    validate_storage_path,
)
from app.utils.errors import DataError, ValidationError


def test_path_validation_locks() -> None:
    """Verify that path check prevents outside root writes and traversal."""
    # Approved root
    valid_path = "data/raw/EURUSD_M1.csv"
    validate_storage_path(valid_path)

    # Traversal check
    with pytest.raises(ValidationError):
        validate_storage_path("data/raw/../../secret.env")

    # Outside approved root check
    with pytest.raises(ValidationError):
        validate_storage_path("tmp/data.csv")

    # Unsupported extension
    with pytest.raises(ValidationError):
        validate_storage_path("data/raw/EURUSD_M1.txt")


def test_atomic_file_write_and_quarantine() -> None:
    """Test save_market_data atomic creation and loading."""
    records = [
        {"timestamp": "2026-06-01T00:00:00Z", "symbol": "EURUSD", "close": 1.1000}
    ]
    target_file = "data/raw/temp_test_write.csv"

    # Save
    res = save_market_data(records, target_file, "csv", overwrite=True)
    assert res["record_count"] == 1
    assert "path" in res

    # Load
    loaded = load_local_dataset(target_file)
    assert len(loaded) == 1
    assert loaded[0]["symbol"] == "EURUSD"

    # Cleanup
    file_path = Path(target_file)
    if file_path.exists():
        file_path.unlink()


def test_database_helper_connection() -> None:
    """Test SQLite connection provider and WAL journaling status."""
    with db_helper.get_connection() as conn:
        cursor = conn.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal"


def test_cache_hits_and_misses() -> None:
    """Verify caching controls."""
    key = generate_cache_key("csv", "EURUSD", "M1", "2026-06-01", "2026-06-02")
    records = [
        {"timestamp": "2026-06-01T00:00:00Z", "symbol": "EURUSD", "close": 1.1000}
    ]

    # Initially cache miss
    cached = get_cached_data(key, "refresh_and_return")
    assert cached is None

    # Set cache with 10 seconds TTL
    set_cached_data(key, "csv", "EURUSD", "M1", "2026-06-01", "2026-06-02", records, 10)

    # Cache hit
    cached = get_cached_data(key, "refresh_and_return")
    assert cached is not None
    assert cached["records"][0]["symbol"] == "EURUSD"

    # Dry-run clearing
    clear_res = clear_data_cache("data_cache", dry_run=True)
    assert clear_res["matched_count"] > 0
    assert clear_res["cleared_count"] == 0

    # Delete clearing
    clear_res = clear_data_cache("data_cache", dry_run=False)
    assert clear_res["cleared_count"] > 0

    # Confirm cache is cleared
    cached_post = get_cached_data(key, "refresh_and_return")
    assert cached_post is None


def test_database_helper_migrations(tmp_path: Path) -> None:
    from app.services.data.storage import DatabaseHelper

    temp_db = str(tmp_path / "temp_migration_test.db")
    helper = DatabaseHelper(db_path=temp_db)
    # Check that database connection successfully resolved WAL journaling mode
    with helper.get_connection() as conn:
        cursor = conn.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal"


def test_validate_storage_path_errors() -> None:
    # Empty path
    with pytest.raises(ValidationError, match="Path cannot be empty"):
        validate_storage_path("")

    # Hidden folder
    with pytest.raises(ValidationError, match="Hidden files or directories"):
        validate_storage_path("data/raw/.hidden/file.csv")

    # Normalization error
    from unittest.mock import patch

    with patch("app.services.data.storage.normalize_path") as mock_norm:
        mock_norm.side_effect = Exception("Mock Normalization Error")
        with pytest.raises(ValidationError, match="Invalid path"):
            validate_storage_path("data/raw/invalid.csv")


def test_atomic_file_write_errors() -> None:
    # Empty list supplied
    with pytest.raises(ValidationError, match="No data records supplied"):
        save_market_data([], "data/raw/temp.csv", "csv")

    # Duplicate file without overwrite
    target_file = "data/raw/duplicate_check.csv"
    save_market_data([{"x": 1}], target_file, "csv", overwrite=True)
    with pytest.raises(ValidationError, match="File already exists"):
        save_market_data([{"x": 1}], target_file, "csv", overwrite=False)

    # Cleanup
    file_path = Path(target_file)
    if file_path.exists():
        file_path.unlink()

    # Unsupported format
    with pytest.raises(ValidationError, match="unsupported"):
        save_market_data([{"x": 1}], "data/raw/test.csv", "txt")


def test_load_local_dataset_errors() -> None:
    # Non-existent file
    with pytest.raises(ValidationError, match="Local file not found"):
        load_local_dataset("data/raw/non_existent.csv")

    # Unsupported extension
    with pytest.raises(ValidationError, match=r"[Ee]xtension"):
        load_local_dataset("data/raw/unsupported.txt")


def test_cache_expiration_and_errors() -> None:
    from app.services.data.storage import get_cached_data, set_cached_data

    key = generate_cache_key("csv", "EURUSD", "M1", "2026-06-01", "2026-06-03")
    records = [{"close": 1.10}]

    # Set cache with negative TTL (already expired)
    set_cached_data(
        key, "csv", "EURUSD", "M1", "2026-06-01", "2026-06-03", records, -10
    )

    # Get cache with refresh_and_return should miss/return None
    assert get_cached_data(key, "refresh_and_return") is None

    # Get cache with return_stale should return stale warn
    stale_res = get_cached_data(key, "return_stale")
    assert stale_res is not None
    assert stale_res["metadata"]["warning"] == "Data returned is stale from cache."

    # Force invalid JSON decode path in DB
    with db_helper.get_connection() as conn:
        conn.execute(
            "UPDATE data_cache SET records_json = 'invalid_json' WHERE key = ?;",
            (key,),
        )
    assert get_cached_data(key, "return_stale") is None

    # Database exceptions paths
    from unittest.mock import patch

    with patch("app.services.data.storage.db_helper.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("DB Cache Error")
        assert get_cached_data(key, "return_stale") is None


def test_clear_data_cache_errors() -> None:
    # Invalid namespace
    with pytest.raises(ValidationError, match="Only 'data_cache' namespace"):
        clear_data_cache("invalid_ns")

    # Database exceptions paths
    from unittest.mock import patch

    with patch("app.services.data.storage.db_helper.get_connection") as mock_conn:
        mock_conn.side_effect = Exception("DB Clear Error")
        with pytest.raises(ValidationError, match="Failed to clear cache"):
            clear_data_cache("data_cache", dry_run=False)


def test_load_local_dataset_exception_handling(tmp_path: Path) -> None:
    # Cause pandas read_csv to throw exception
    corrupt_file = tmp_path / "corrupt.csv"
    corrupt_file.write_text("invalid,csv,data\n1,2", encoding="utf-8")
    # This should trigger DataError inside load_local_dataset
    from app.services.data.storage import load_local_dataset

    with (
        patch(
            "app.services.data.storage.validate_storage_path", return_value=corrupt_file
        ),
        patch("pandas.read_csv", side_effect=Exception("Read CSV Error")),
        pytest.raises(DataError),
    ):
        load_local_dataset("data/raw/corrupt.csv")


def test_load_ohlcv_csv_errors(tmp_path: Path) -> None:
    from app.services.data.storage import load_ohlcv_csv

    # Empty raw records
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("open,high,low,close\n", encoding="utf-8")
    with (
        patch("app.services.data.storage.load_local_dataset", return_value=[]),
        pytest.raises(ValueError, match="At least one OHLCV bar is required"),
    ):
        load_ohlcv_csv("data/raw/empty.csv")

    # Missing time column
    records_no_time = [{"open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0}]
    with (
        patch(
            "app.services.data.storage.load_local_dataset", return_value=records_no_time
        ),
        pytest.raises(ValueError, match="CSV needs one of timestamp columns"),
    ):
        load_ohlcv_csv("data/raw/missing_time.csv")

    # Naive timestamp (no timezone)
    records_naive_time = [
        {
            "timestamp": "2026-06-23T12:00:00",
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.0,
        }
    ]
    with (
        patch(
            "app.services.data.storage.load_local_dataset",
            return_value=records_naive_time,
        ),
        pytest.raises(ValueError, match="Invalid OHLCV row"),
    ):
        load_ohlcv_csv("data/raw/naive_time.csv")

    # Invalid price row (e.g. ValueError during float conversion)
    records_bad_row = [
        {
            "timestamp": "2026-06-23T12:00:00Z",
            "open": "not_a_float",
            "high": 1.1,
            "low": 0.9,
            "close": 1.0,
        }
    ]
    with (
        patch(
            "app.services.data.storage.load_local_dataset", return_value=records_bad_row
        ),
        pytest.raises(ValueError, match="Invalid OHLCV row"),
    ):
        load_ohlcv_csv("data/raw/bad_row.csv")
