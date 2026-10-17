"""Unit tests for Data Manager Home service, CLI formatting, and package facade."""

from __future__ import annotations

import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.services.include.contracts import DataInfo
from app.workspace.data_manager import Home, HomeCLI
from app.workspace.data_manager.home import (
    MAX_UNDERLYING_DISPLAY_LEN,
    TRUNCATE_LEN,
    _Config,
    format_dataset_table,
    format_home_dashboard,
)


@pytest.fixture
def test_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing initialized isolated SQLite database file path."""
    db_file = tmp_path / "test_datamgr_home.db"
    with resolve_connection(db_file) as conn:
        create_schema(conn)
    monkeypatch.setattr("app.host.persistence.create.DEFAULT_DB_PATH", db_file)
    return db_file


def test_config_dataclass_to_dict() -> None:
    """Test _Config default construction and dictionary representation."""
    config = _Config(
        datasets_count=5,
        instruments_count=3,
        sessions_count=2,
        baskets_count=1,
        active_providers_count=4,
        total_bars=1000,
        storage_bytes=2048,
        parquet_files_count=10,
    )
    data = config.to_dict()
    assert data["datasets_count"] == 5
    assert data["instruments_count"] == 3
    assert data["sessions_count"] == 2
    assert data["baskets_count"] == 1
    assert data["active_providers_count"] == 4
    assert data["total_bars"] == 1000
    assert data["storage_bytes"] == 2048
    assert data["parquet_files_count"] == 10


def test_home_service_overview(test_db_path: Path) -> None:
    """Test Home.get_overview with populated SQLite tables and callback."""
    now_iso = datetime.now(UTC).isoformat()
    with resolve_connection(test_db_path) as conn:
        conn.execute(
            "INSERT INTO datamgr_instruments (symbol, description, data_type, "
            "tick_size, point_value, decimals, created_at_utc, updated_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("EURUSD", "EURUSD Pair", "Forex", 0.00001, 100000.0, 5, now_iso, now_iso),
        )
        conn.execute(
            "INSERT INTO datamgr_instruments (symbol, description, data_type, "
            "tick_size, point_value, decimals, created_at_utc, updated_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("AAPL", "Apple Inc.", "Stocks", 0.01, 1.0, 2, now_iso, now_iso),
        )
        conn.execute(
            "INSERT INTO datamgr_sessions (name, timezone, description) "
            "VALUES (?, ?, ?)",
            ("Forex 24/5", "UTC", "Standard 24/5 trading session"),
        )
        conn.execute(
            "INSERT INTO datamgr_stock_group (NAME, SYSTEM, DESC, description) "
            "VALUES (?, ?, ?, ?)",
            ("Tech Basket", 1, "Tech stocks", "Tech stocks"),
        )
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, broker, "
            "broker_name, timezone, category, date_from, date_to, bars, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds:1",
                "dukascopy",
                "EURUSD",
                "EURUSD",
                "EURUSD",
                "M1",
                "dukascopy",
                "Dukascopy Broker",
                "UTC",
                "Forex",
                "2026-01-01",
                "2026-01-02",
                500,
                now_iso,
                now_iso,
            ),
        )
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, broker, "
            "broker_name, timezone, category, date_from, date_to, bars, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds:2",
                "sq_equity",
                "AAPL",
                "AAPL",
                "AAPL",
                "D1",
                "sq_equity",
                "SQ Equity",
                "UTC",
                "Stocks",
                "2026-01-01",
                "2026-01-02",
                250,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()

    # Case 1: Custom active_providers_getter
    home_service = Home(active_providers_getter=lambda: 3)
    overview = home_service.get_overview()
    assert overview["datasets_count"] == 2
    assert overview["instruments_count"] == 2
    assert overview["sessions_count"] == 1
    assert overview["baskets_count"] == 1
    assert overview["active_providers_count"] == 3
    assert overview["total_bars"] == 750
    assert overview["storage_bytes"] == 0
    assert overview["parquet_files_count"] == 0

    # Case 2: Default active_providers_getter (None)
    home_default = Home()
    overview_default = home_default.get_overview()
    assert overview_default["active_providers_count"] == 0


def test_home_service_saved_datasets(test_db_path: Path) -> None:
    """Test Home.get_saved_datasets across valid, invalid, and empty dates."""
    now_iso = datetime.now(UTC).isoformat()
    with resolve_connection(test_db_path) as conn:
        # Row 1: Valid date range with standard format
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, broker, "
            "broker_name, timezone, category, date_from, date_to, bars, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds:1",
                "dukascopy",
                "EURUSD",
                "EUR/USD Spot",
                "EURUSD",
                "M1",
                "dukascopy",
                "Dukascopy Broker",
                "UTC",
                "Forex",
                "2026-01-01",
                "2026-01-11",
                5000,
                now_iso,
                now_iso,
            ),
        )
        # Row 2: Invalid date format triggering ValueError fallback
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, broker, "
            "broker_name, timezone, category, date_from, date_to, bars, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds:2",
                "manual",
                "INVALID_DATE",
                "Underlying",
                "INV",
                "D1",
                "custom",
                "Custom Broker",
                "UTC",
                "Crypto",
                "not-a-date",
                "also-invalid",
                100,
                now_iso,
                now_iso,
            ),
        )
        # Row 3: Missing date_from and date_to
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, broker, "
            "broker_name, timezone, category, date_from, date_to, bars, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds:3",
                "manual",
                "NO_DATES",
                "Underlying",
                "ND",
                "H1",
                "custom",
                "Custom Broker",
                "UTC",
                "Futures",
                "",
                "",
                50,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()

    home_service = Home()
    datasets = home_service.get_saved_datasets()
    assert len(datasets) == 3

    # Validate Row 1 (valid range: 10 days)
    ds1 = datasets[0]
    assert isinstance(ds1, DataInfo)
    assert ds1.id == "ds:1"
    assert ds1.symbol == "EURUSD"
    assert ds1.instrument == "EURUSD"
    assert ds1.broker == "dukascopy"
    assert ds1.broker_name == "Dukascopy Broker"
    assert ds1.underlying == "EUR/USD Spot"
    assert ds1.timeframe == "M1"
    assert ds1.timezone == "UTC"
    assert ds1.date_from == "2026-01-01"
    assert ds1.date_to == "2026-01-11"
    assert ds1.total_days == 10
    assert ds1.total_records == 5000
    assert ds1.bars == 5000
    assert ds1.rows == 5000
    assert ds1.source == "dukascopy"
    assert ds1.connection == "dukascopy"
    assert ds1.data_type == "Forex"
    assert ds1.category == "Forex"

    # Validate Row 2 (invalid dates -> total_days == 0)
    ds2 = datasets[1]
    assert ds2.symbol == "INVALID_DATE"
    assert ds2.total_days == 0

    # Validate Row 3 (empty dates -> total_days == 0)
    ds3 = datasets[2]
    assert ds3.symbol == "NO_DATES"
    assert ds3.total_days == 0


def test_home_cli_formatting() -> None:
    """Test HomeCLI and standalone table formatting functions."""
    long_underlying = "VERY_LONG_UNDERLYING_INSTRUMENT_EXCEEDING_LIMIT"
    datasets = [
        DataInfo(
            symbol="EURUSD",
            instrument="EURUSD",
            broker="dukascopy",
            underlying="EUR/USD Spot",
            timeframe="M1",
            timezone="UTC",
            date_from="2026-01-01",
            date_to="2026-01-10",
            total_days=9,
            total_records=1234,
            source="dukascopy",
            data_type="Forex",
        ),
        DataInfo(
            symbol="LONG_SYM",
            instrument="LONG_INST",
            broker="broker_x",
            underlying=long_underlying,
            timeframe="D1",
            timezone="UTC",
            date_from="2025-01-01",
            date_to="2025-12-31",
            total_days=364,
            total_records=250,
            source="manual",
            data_type="Stocks",
        ),
    ]

    # Test format_dataset_table standalone and through HomeCLI
    table_standalone = format_dataset_table(datasets)
    table_cli = HomeCLI.format_dataset_table(datasets)
    assert table_standalone == table_cli
    assert "=== Saved Datasets Catalog (2 items) ===" in table_cli
    assert "EURUSD" in table_cli
    assert "LONG_SYM" in table_cli

    # Verify long underlying string is truncated with ellipsis
    expected_truncated = long_underlying[:TRUNCATE_LEN] + ".."
    assert expected_truncated in table_cli
    assert len(long_underlying) > MAX_UNDERLYING_DISPLAY_LEN

    # Test format_home_dashboard standalone and through HomeCLI
    overview = {
        "datasets_count": 2,
        "instruments_count": 5,
        "sessions_count": 3,
        "baskets_count": 1,
        "active_providers_count": 2,
        "total_bars": 1484,
    }
    dashboard_standalone = format_home_dashboard(overview, datasets)
    dashboard_cli = HomeCLI.format_home_dashboard(overview, datasets)
    assert dashboard_standalone == dashboard_cli
    assert "=== Data Manager Home: Live Database Overview ===" in dashboard_cli
    assert "Total Datasets:       2" in dashboard_cli
    assert "Historical Bars:      1,484" in dashboard_cli
    assert "Active Providers:     2" in dashboard_cli
    assert "=== Saved Datasets Catalog (2 items) ===" in dashboard_cli


def test_home_cli_empty_table() -> None:
    """Test format_dataset_table with empty dataset list."""
    empty_table = HomeCLI.format_dataset_table([])
    assert "=== Saved Datasets Catalog (0 items) ===" in empty_table
    assert "| Symbol Name" in empty_table


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_home_main_execution(
    test_db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test running home.py standalone under __main__."""
    now_iso = datetime.now(UTC).isoformat()
    with resolve_connection(test_db_path) as conn:
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, broker, "
            "broker_name, timezone, category, date_from, date_to, bars, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds:main",
                "source_x",
                "MAIN_TEST",
                "MAIN_UND",
                "MAIN_INST",
                "M1",
                "broker_main",
                "Main Broker",
                "UTC",
                "Forex",
                "2026-01-01",
                "2026-01-02",
                42,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()

    runpy.run_module("app.workspace.data_manager.home", run_name="__main__")
    captured = capsys.readouterr()
    assert "=== Data Manager Home: Live Database Overview ===" in captured.out
    assert "MAIN_TEST" in captured.out
    assert "Total Datasets:       1" in captured.out


def test_data_manager_package_facade_exports() -> None:
    """Test app.workspace.data_manager package facade re-exports Home and HomeCLI."""
    import app.workspace.data_manager as dm

    assert dm.__all__ == [
        "DataManagerWorkspace",
        "Home",
        "HomeCLI",
        "create_data_manager_router",
    ]
