"""Tests for Data Manager Command-Line Interface."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pyarrow as pa  # type: ignore[import-untyped]
import pytest
from app.persistence.market import (
    M1_SCHEMA,
    create_isolated_schema,
    log_datamgr_operation,
)
from scripts.data_manager_cli import (
    cmd_broker_profiles,
    cmd_clear,
    cmd_clear_log,
    cmd_data,
    cmd_delete,
    cmd_instruments,
    cmd_log,
    cmd_sessions,
    cmd_stock_groups,
    main,
)


def _setup_full_test_db(db_path: Path) -> None:
    """Set up all Data Manager tables in an isolated SQLite database."""
    create_isolated_schema(db_path)
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_instruments ("
            "id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, description TEXT, "
            "broker_id INTEGER DEFAULT 1, decimals INTEGER DEFAULT 5, "
            "point_value REAL, tick_size REAL, default_spread REAL, "
            "min_volume REAL, max_volume REAL, margin_rate REAL, data_type TEXT)"
        )
        conn.execute(
            "INSERT INTO datamgr_instruments VALUES "
            "(1, 'EURUSD', 'Euro / US Dollar', 1, 5, 100000.0, 0.00001, 0.00010, 0.01, 100.0, 0.05, 'Forex')"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_sessions ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL, timezone TEXT NOT NULL, "
            "windows_json TEXT, is_default INTEGER, description TEXT)"
        )
        windows = [
            {"day_of_week": 0, "open_time": "00:00", "close_time": "23:59"},
            {"day_of_week": 4, "open_time": "00:00", "close_time": "23:59"},
        ]
        conn.execute(
            "INSERT INTO datamgr_sessions VALUES "
            "(1, '24/5 Forex', 'UTC', ?, 1, 'Standard Forex')",
            (json.dumps(windows),),
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_stock_group ("
            "ID INTEGER PRIMARY KEY, NAME TEXT NOT NULL, SYSTEM INTEGER, DESC TEXT)"
        )
        conn.execute(
            "INSERT INTO datamgr_stock_group VALUES (1, '[[S&P 500]]', 1, 'Index basket')"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_broker ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL, postfix TEXT, "
            "server_timezone TEXT, mt_use INTEGER, stockpicker_use INTEGER, enabled INTEGER)"
        )
        conn.execute(
            "INSERT INTO datamgr_broker VALUES (3, 'Dukascopy', '_dukascopy', 'EETUS', 1, 0, 1)"
        )


def test_main_help_and_no_args(capsys: pytest.CaptureFixture[str]) -> None:
    """Running main with no args prints help and returns 0."""
    result = main([])
    assert result == 0
    captured = capsys.readouterr()
    assert "HaruQuantAI Data Manager CLI" in captured.out


def test_missing_database_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Passing a non-existent database file returns error code 1."""
    missing_db = tmp_path / "nonexistent.db"
    assert cmd_instruments(missing_db) == 1
    assert cmd_sessions(missing_db) == 1
    assert cmd_stock_groups(missing_db) == 1
    assert cmd_broker_profiles(missing_db) == 1
    assert cmd_data(missing_db, tmp_path) == 1
    assert cmd_log(missing_db) == 1
    assert cmd_clear_log(missing_db) == 1
    assert cmd_delete(missing_db, tmp_path, "EURUSD") == 1
    assert cmd_clear(missing_db, tmp_path, "EURUSD") == 1


def test_tab_flags_render_tables(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """All 5 display tabs render valid tables from database records."""
    db_path = tmp_path / "database" / "haruquantai.db"
    _setup_full_test_db(db_path)

    # 1. Instruments Tab
    assert main(["--instruments", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "EURUSD" in out
    assert "Euro / US Dollar" in out
    assert "100,000.0" in out

    # 2. Sessions Tab
    assert main(["--sessions", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "24/5 Forex" in out
    assert "Mon-Fri 00:00-23:59" in out

    # 3. Stock Groups Tab
    assert main(["--stock-groups", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "[[S&P 500]]" in out
    assert "Index basket" in out

    # 4. Broker Profiles Tab
    assert main(["--broker-profiles", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "Dukascopy" in out
    assert "_dukascopy" in out
    assert "EETUS" in out

    # 5. Data Tab
    assert main(["--data", "--db", str(db_path), "--data-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "[Data] Tab - Symbol Catalog" in out


def test_log_and_clear_log(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Logging operational events and clearing them works through CLI."""
    db_path = tmp_path / "database" / "haruquantai.db"
    _setup_full_test_db(db_path)

    # Empty log initially
    assert main(["--log", "--db", str(db_path)]) == 0
    assert "No events recorded" in capsys.readouterr().out

    # Log an operation
    log_datamgr_operation(
        db_path, "EURUSD_dukascopy", "download", "succeeded", "Test message"
    )

    assert main(["--log", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "EURUSD_dukascopy" in out
    assert "download" in out
    assert "Test message" in out

    # Clear log
    assert main(["--clear-log", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "Operational progress log cleared (1 events removed)" in out

    assert main(["--log", "--db", str(db_path)]) == 0
    assert "No events recorded" in capsys.readouterr().out


def test_delete_and_clear_actions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """'delete' and 'clear' subcommands operate correctly on symbols and files."""
    db_path = tmp_path / "database" / "haruquantai.db"
    data_root = tmp_path / "data"
    _setup_full_test_db(db_path)

    fake_file = data_root / "market" / "dukascopy" / "m1" / "gbpusd" / "2024.parquet"
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_text("dummy")

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, "
            "broker, broker_name, timezone, category, date_from, date_to, "
            "bars, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "gbp-001",
                "Dukascopy",
                "GBPUSD_dukascopy",
                "GBPUSD",
                "GBPUSD",
                "M1",
                "3",
                "Dukascopy",
                "UTC",
                "Forex",
                "2024-01-01",
                "2024-01-10",
                1234,
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:00:00Z",
            ),
        )
        conn.execute(
            "INSERT INTO market_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "dukascopy",
                "m1",
                "gbpusd",
                "2024",
                "market/dukascopy/m1/gbpusd/2024.parquet",
                1,
                "dummyhash",
                5,
                1234,
                1000,
                2000,
                "[]",
                "cdn",
                "2024-01-01T00:00:00Z",
            ),
        )

    # Test 'clear' subcommand
    ret_clear = main(
        [
            "clear",
            "GBPUSD_dukascopy",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_clear == 0
    assert not fake_file.is_file()
    out = capsys.readouterr().out
    assert "history cleared (definition retained)" in out

    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT bars, date_from FROM datamgr_datasets WHERE symbol='GBPUSD_dukascopy'"
        ).fetchone()
        assert row == (0, "")

    # Test 'delete' subcommand
    ret_del = main(
        [
            "delete",
            "GBPUSD_dukascopy",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_del == 0
    out = capsys.readouterr().out
    assert "deleted and market files purged" in out

    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT count(*) FROM datamgr_datasets").fetchone()[0]
        assert count == 0

    # Delete again should fail
    assert (
        main(
            [
                "delete",
                "GBPUSD_dukascopy",
                "--db",
                str(db_path),
                "--data-dir",
                str(data_root),
            ]
        )
        == 1
    )


def test_download_subcommand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """'download' command executes pipeline, saves parquet, and updates records."""
    db_path = tmp_path / "database" / "haruquantai.db"
    data_root = tmp_path / "data"
    _setup_full_test_db(db_path)

    # Mock _fetch_day to return a small valid pyarrow Table
    dt = datetime(2024, 1, 8, 12, 0, tzinfo=UTC)
    mock_table = pa.Table.from_pydict(
        {
            "DateTime": [dt],
            "Open": [1.0850],
            "High": [1.0855],
            "Low": [1.0845],
            "Close": [1.0852],
            "Volume": [100.0],
        },
        schema=M1_SCHEMA,
    )

    mock_fetch = AsyncMock(return_value=mock_table)
    monkeypatch.setattr("scripts.data_manager_cli._fetch_day", mock_fetch)

    # Invalid date range exits 1
    ret_bad_date = main(
        [
            "download",
            "EURUSD_dukascopy",
            "EURUSD",
            "--start-date",
            "2024-01-10",
            "--end-date",
            "2024-01-05",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_bad_date == 1

    # Valid download
    ret = main(
        [
            "download",
            "EURUSD_dukascopy",
            "EURUSD",
            "--start-date",
            "2024-01-08",
            "--end-date",
            "2024-01-08",
            "--timeframe",
            "M1",
            "--sq-cdn-true",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "Download completed successfully!" in out
    assert "EURUSD_dukascopy" in out
    assert "Days Published:  1" in out

    # Verify parquet file was written
    expected_parquet = (
        data_root / "market" / "dukascopy" / "m1" / "eurusd" / "2024.parquet"
    )
    assert expected_parquet.is_file()

    # Verify database was updated
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT date_from, date_to, bars FROM datamgr_datasets WHERE symbol='EURUSD_dukascopy'"
        ).fetchone()
        assert row == ("2024-01-08", "2024-01-08", 1)

    # Verify operation log was created
    assert main(["--log", "--db", str(db_path)]) == 0
    out = capsys.readouterr().out
    assert "EURUSD_dukascopy" in out
    assert "download" in out


def test_dukascopy_source_parity_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test --source dukascopy flags for disclaimer, add-symbol, and import."""
    db_path = tmp_path / "haruquantai.db"
    data_root = tmp_path / "data"
    _setup_full_test_db(db_path)

    # 1. Test Disclaimer
    ret = main(["--source", "dukascopy", "--disclaimer"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "=== Dukascopy Bank SA Data Disclaimer ===" in out
    assert "=== StrategyQuant CDN Data Disclaimer ===" in out

    # 2. Test Add Symbol
    ret = main(
        [
            "--source",
            "dukascopy",
            "--add-symbol",
            "GBPUSD",
            "--data-type",
            "M1",
            "--broker-profile",
            "dukascopy",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "Added Dukascopy data symbol 'GBPUSD_dukascopy'" in out

    # Verify added in database
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT symbol, underlying, timeframe, broker FROM datamgr_datasets WHERE symbol='GBPUSD_dukascopy'"
        ).fetchone()
        assert row == ("GBPUSD_dukascopy", "GBPUSD", "M1", "3")

    # 3. Test Import with mock
    mock_bar = {
        "timestamp_utc": datetime(2024, 1, 8, 0, 0, tzinfo=UTC),
        "open": 1.2700,
        "high": 1.2710,
        "low": 1.2690,
        "close": 1.2705,
        "volume": 50,
    }
    mock_fetch = AsyncMock(return_value=[mock_bar])
    monkeypatch.setattr("scripts.data_manager_cli._fetch_day", mock_fetch)

    ret = main(
        [
            "--source",
            "dukascopy",
            "--import",
            "GBPUSD_dukascopy",
            "--start-date",
            "2024-01-08",
            "--end-date",
            "2024-01-08",
            "--redownload",
            "missing",
            "--fast-download",
            "sqx-cdn",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "Download completed successfully!" in out
    assert "GBPUSD_dukascopy" in out


def _seed_cli_test_data(db_path: Path, data_root: Path) -> None:
    """Helper to publish M1 data and register dataset for action CLI tests."""
    from app.persistence.market import MarketDataStore

    times = [datetime(2026, 3, 2, 10, i, 0, tzinfo=UTC) for i in range(10)]
    table = pa.Table.from_pylist(
        [
            {
                "DateTime": dt,
                "Open": 1.0850 + i * 0.0001,
                "High": 1.0860 + i * 0.0001,
                "Low": 1.0845 + i * 0.0001,
                "Close": 1.0855 + i * 0.0001,
                "Volume": 100 + i * 10,
            }
            for i, dt in enumerate(times)
        ],
        schema=M1_SCHEMA,
    )
    store = MarketDataStore(data_root, db_path)
    store.publish(
        source="dukascopy",
        kind="m1",
        symbol="eurusd",
        period="2026",
        table=table,
        coverage=(
            (int(times[0].timestamp() * 1000), int(times[-1].timestamp() * 1000)),
        ),
        provider_mode="test",
    )
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "INSERT OR REPLACE INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, "
            "broker, broker_name, timezone, category, date_from, date_to, "
            "bars, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "eur-001",
                "Dukascopy",
                "EURUSD_dukascopy",
                "EURUSD",
                "EURUSD",
                "M1",
                "3",
                "Dukascopy",
                "UTC",
                "Forex",
                "2026-03-02",
                "2026-03-02",
                10,
                "2026-03-02T00:00:00Z",
                "2026-03-02T00:00:00Z",
            ),
        )


def test_cli_actions_broker_and_export(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate broker data queries and MT4/MT5/CSV exports."""
    db_path = tmp_path / "database" / "haruquantai.db"
    data_root = tmp_path / "data"
    _setup_full_test_db(db_path)
    _seed_cli_test_data(db_path, data_root)

    # 1. broker-data
    ret_bdata = main(
        [
            "broker-data",
            "--query",
            "EUR",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_bdata == 0
    assert "EURUSD" in capsys.readouterr().out

    # 2. broker-data-update
    ret_bupdate = main(
        ["broker-data-update", "--db", str(db_path), "--data-dir", str(data_root)]
    )
    assert ret_bupdate == 0

    # 3. export-csv
    csv_file = tmp_path / "eurusd_m5.csv"
    ret_csv = main(
        [
            "export-csv",
            "EURUSD_dukascopy",
            "--timeframe",
            "M5",
            "--output-path",
            str(csv_file),
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_csv == 0
    assert csv_file.is_file()

    # 4. export-mt4
    mt4_dir = tmp_path / "mt4_out"
    ret_mt4 = main(
        [
            "export-mt4",
            "EURUSD_dukascopy",
            "--output-dir",
            str(mt4_dir),
            "--timeframe",
            "M1",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_mt4 == 0
    assert (mt4_dir / "EURUSD1.hst").is_file()

    # 5. export-mt5
    mt5_file = tmp_path / "eurusd_mt5.txt"
    ret_mt5 = main(
        [
            "export-mt5",
            "EURUSD_dukascopy",
            "--output-path",
            str(mt5_file),
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_mt5 == 0
    assert mt5_file.is_file()


def test_cli_actions_definitions_and_review(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate clone, backup/load definitions, review, and update actions."""
    db_path = tmp_path / "database" / "haruquantai.db"
    data_root = tmp_path / "data"
    _setup_full_test_db(db_path)
    _seed_cli_test_data(db_path, data_root)

    # 1. clone-to-timezone
    ret_clone = main(
        [
            "clone-to-timezone",
            "EURUSD_dukascopy",
            "--shift-hours",
            "2",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_clone == 0
    assert "Successfully cloned 1 dataset(s)" in capsys.readouterr().out

    # 2. save-definitions & load-definitions
    defs_file = tmp_path / "backup_defs.json"
    ret_save = main(
        [
            "save-definitions",
            "--file-path",
            str(defs_file),
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_save == 0
    assert defs_file.is_file()

    ret_load = main(
        [
            "load-definitions",
            str(defs_file),
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_load == 0
    assert "Restored" in capsys.readouterr().out

    # 3. review (data, chart, quality)
    ret_rev_data = main(
        [
            "review",
            "EURUSD_dukascopy",
            "--limit",
            "5",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_rev_data == 0

    ret_rev_qual = main(
        [
            "review",
            "EURUSD_dukascopy",
            "--quality",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_rev_qual == 0
    assert "Quality Score" in capsys.readouterr().out

    ret_rev_chart = main(
        [
            "review",
            "EURUSD_dukascopy",
            "--chart",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_rev_chart == 0
    assert "Retrieved" in capsys.readouterr().out

    # 4. update-all & update-selected
    ret_up_all = main(
        ["update-all", "--db", str(db_path), "--data-dir", str(data_root)]
    )
    assert ret_up_all == 0

    ret_up_sel = main(
        [
            "update-selected",
            "EURUSD_dukascopy",
            "--db",
            str(db_path),
            "--data-dir",
            str(data_root),
        ]
    )
    assert ret_up_sel == 0
