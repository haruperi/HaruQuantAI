"""Market catalog schema never mutates an existing unified database."""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from app.persistence.market import (
    BrokerSchemaUnavailableError,
    MarketDataStore,
    MarketSchemaUnavailableError,
    clear_datamgr_log,
    clear_market_symbol,
    create_isolated_schema,
    delete_market_symbol,
    log_datamgr_operation,
    migrate_market_schema,
    open_market_catalog,
    preseed_native_sqx_datasets,
    read_broker_profiles,
    read_datamgr_log,
)


def test_script_partition_preserves_values_and_revisions(tmp_path: Path) -> None:
    """Different bar granularities and fractional volumes survive custody unchanged."""
    import hashlib
    from datetime import UTC, datetime

    import pyarrow as pa  # type: ignore[import-untyped]

    database = tmp_path / "isolated.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    identity: dict[str, Any] = {
        "source": "Crypto",
        "symbol": "BTCUSDT",
        "underlying": "BTCUSDT",
        "instrument": "BTCUSDT",
        "timeframe": "H4",
        "timezone": "UTC",
        "broker": "-1",
        "options": {"exchange": "binance", "adjusted": False},
    }
    first = store.register_source("plugin.crypto", **identity)
    assert store.register_source("plugin.crypto", **identity) == first
    second = store.register_source("plugin.other", **identity)
    assert first != second
    with pytest.raises(ValueError, match="unavailable"):
        store.source_definition("plugin.other", first)
    table = pa.table(
        {
            "DateTime": pa.array(
                [datetime(2024, 1, 1, tzinfo=UTC)], type=pa.timestamp("ms", tz="UTC")
            ),
            "Open": [42000.123456789],
            "High": [43000.0],
            "Low": [41000.0],
            "Close": [42500.0],
            "Volume": [0.00000017],
        }
    )
    record = store.publish_source("plugin.crypto", first, "2024", table)
    assert store.read_source_partition(record).equals(table)
    path = tmp_path / record["relative_path"]
    old_bytes = path.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == record["sha256"]
    assert store.source_definition("plugin.crypto", first)["bars"] == 1
    assert (
        store.publish_source("plugin.crypto", first, "2024", table, expected_revision=1)
        == record
    )
    with pytest.raises(ValueError, match="changed"):
        store.publish_source("plugin.crypto", first, "2024", table)
    changed = table.set_column(5, "Volume", pa.array([0.125]))
    new = store.publish_source(
        "plugin.crypto", first, "2024", changed, expected_revision=1
    )
    assert new["revision"] == 2
    assert store.source_partitions(first) == (new,)
    assert path.read_bytes() == old_bytes
    assert store.read_source_partition(record).equals(table)
    assert store.source_definition("plugin.crypto", first)["bars"] == 1
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="digest mismatch"):
        store.read_source_partition(record)


def test_source_catalog_never_provisions_existing_database(tmp_path: Path) -> None:
    database = tmp_path / "existing.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")
    store = MarketDataStore(tmp_path, database)
    before = database.read_bytes()
    assert not store.source_available()
    assert database.read_bytes() == before
    with pytest.raises(MarketSchemaUnavailableError):
        store.register_source(
            "owner",
            source="Yahoo",
            symbol="AAPL",
            underlying="AAPL",
            instrument="AAPL",
            timeframe="D1",
            timezone="UTC",
            broker="-1",
            options={},
        )
    assert database.read_bytes() == before


def test_market_schema_is_explicit_and_rejects_existing_store(tmp_path: Path) -> None:
    """Provisioning a new test store is separate from live migration."""
    path = tmp_path / "database" / "haruquantai.db"
    with pytest.raises(MarketSchemaUnavailableError):
        open_market_catalog(path)
    create_isolated_schema(path)
    with closing(open_market_catalog(path)) as connection:
        assert (
            connection.execute("SELECT count(*) FROM market_files").fetchone()[0] == 0
        )
    with pytest.raises(FileExistsError):
        create_isolated_schema(path)


def test_read_only_broker_catalog_filters_eligible_rows(tmp_path: Path) -> None:
    """The profile list comes from SQLite, independent of market migration."""
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, "
            "postfix TEXT, server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.executemany(
            "INSERT INTO datamgr_broker VALUES (?,?,?,?,?,?)",
            [
                (3, "Dukascopy", "_dukascopy", "EETUS", 1, 1),
                (2, "RoboForex", "_robo", "EET", 1, 1),
                (4, "Disabled", "_hidden", "UTC", 0, 1),
                (5, "Stocks only", "_stock", "UTC", 1, 0),
            ],
        )
    assert read_broker_profiles(path) == (
        (2, "RoboForex", "_robo", "EET"),
        (3, "Dukascopy", "_dukascopy", "EETUS"),
    )
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT count(*) FROM datamgr_broker").fetchone() == (
            4,
        )


def test_missing_broker_table_fails_without_creation(tmp_path: Path) -> None:
    """An absent table cannot become a fabricated browser catalog."""
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)):
        pass
    with pytest.raises(BrokerSchemaUnavailableError):
        read_broker_profiles(path)
    with closing(sqlite3.connect(path)) as connection:
        names = connection.execute("SELECT name FROM sqlite_master").fetchall()
    assert names == []


def test_migrate_market_schema_creates_backup_and_tables(tmp_path: Path) -> None:
    """Authorized migration creates a recovery backup and provisions catalog tables."""
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE dummy (id INTEGER)")
    backup = migrate_market_schema(path)
    assert backup is not None
    assert backup.is_file()
    with closing(open_market_catalog(path)) as connection:
        names = {
            r[0]
            for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {
            "datamgr_datasets",
            "market_files",
            "market_ingestions",
            "dummy",
        }.issubset(names)
    # Subsequent migration on already provisioned DB returns None
    assert migrate_market_schema(path) is None


def test_explicit_source_migration_preserves_original_and_refuses_partial_schema(
    tmp_path: Path,
) -> None:
    from app.persistence.market import MarketDataStore, migrate_source_schema

    path = tmp_path / "catalog.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE existing_resource (value TEXT)")
        connection.execute("INSERT INTO existing_resource VALUES ('retained')")
    migrate_market_schema(path)
    backup = migrate_source_schema(path)
    assert backup is not None
    assert MarketDataStore(tmp_path, path).source_available()
    assert migrate_source_schema(path) is None
    with closing(sqlite3.connect(backup)) as connection:
        assert (
            connection.execute("SELECT value FROM existing_resource").fetchone()[0]
            == "retained"
        )
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='source_datasets'"
            ).fetchone()
            is None
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        assert (
            connection.execute("SELECT value FROM existing_resource").fetchone()[0]
            == "retained"
        )
        connection.execute("DROP TABLE source_partitions")
    with pytest.raises(ValueError, match="incompatible"):
        migrate_source_schema(path)


def test_preseed_native_sqx_datasets(tmp_path: Path) -> None:
    """Preseeding from donor CSV populates datamgr_datasets and is idempotent."""
    db_path = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(db_path)

    csv_path = tmp_path / "donor.csv"
    csv_path.write_text(
        "EURUSD;Euro / US Dollar;Forex;Major\n"
        "GBPUSD;British Pound / US Dollar;Forex;Major\n"
        "INVALID_ROW\n",
        encoding="latin-1",
    )

    inserted = preseed_native_sqx_datasets(db_path, csv_path)
    assert inserted == 2

    # Second call should insert 0 (idempotent)
    second_insert = preseed_native_sqx_datasets(db_path, csv_path)
    assert second_insert == 0

    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT symbol, underlying, category, timeframe FROM datamgr_datasets ORDER BY symbol"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0] == ("EURUSD_dukascopy", "EURUSD", "Forex", "M1")
        assert rows[1] == ("GBPUSD_dukascopy", "GBPUSD", "Forex", "M1")

    # Absent CSV returns 0 without error
    assert preseed_native_sqx_datasets(db_path, tmp_path / "nonexistent.csv") == 0


def test_delete_and_clear_market_symbol(tmp_path: Path) -> None:
    """Clear resets dates/bars and deletes parquet; delete purges definition entirely."""
    db_path = tmp_path / "database" / "haruquantai.db"
    data_root = tmp_path / "data"
    create_isolated_schema(db_path)

    fake_file = data_root / "market" / "dukascopy" / "m1" / "eurusd" / "2024.parquet"
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_text("dummy-parquet-content")

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "INSERT INTO datamgr_datasets ("
            "id, source, symbol, underlying, instrument, timeframe, "
            "broker, broker_name, timezone, category, date_from, date_to, "
            "bars, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "ds-001",
                "Dukascopy",
                "EURUSD_dukascopy",
                "EURUSD",
                "EURUSD",
                "M1",
                "3",
                "Dukascopy",
                "UTC",
                "Forex",
                "2024-01-01",
                "2024-01-10",
                5000,
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:00:00Z",
            ),
        )
        conn.execute(
            "INSERT INTO market_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "dukascopy",
                "m1",
                "eurusd",
                "2024",
                "market/dukascopy/m1/eurusd/2024.parquet",
                1,
                "abc",
                100,
                5000,
                1000,
                2000,
                "[]",
                "cdn",
                "2024-01-01T00:00:00Z",
            ),
        )

    assert fake_file.is_file()

    # Clear symbol
    assert clear_market_symbol(db_path, data_root, "EURUSD_dukascopy") is True
    assert not fake_file.is_file()

    with closing(sqlite3.connect(db_path)) as conn:
        ds = conn.execute(
            "SELECT date_from, date_to, bars FROM datamgr_datasets WHERE symbol='EURUSD_dukascopy'"
        ).fetchone()
        assert ds == ("", "", 0)
        file_count = conn.execute("SELECT count(*) FROM market_files").fetchone()[0]
        assert file_count == 0

    # Clear non-existent symbol returns False
    assert clear_market_symbol(db_path, data_root, "NONEXISTENT") is False

    # Delete symbol removes definition from datamgr_datasets
    assert delete_market_symbol(db_path, data_root, "EURUSD_dukascopy") is True
    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT count(*) FROM datamgr_datasets").fetchone()[0]
        assert count == 0

    # Delete non-existent symbol returns False
    assert delete_market_symbol(db_path, data_root, "EURUSD_dukascopy") is False


def test_datamgr_operation_log(tmp_path: Path) -> None:
    """Operational progress events are recorded, read in order, and cleared."""
    db_path = tmp_path / "database" / "haruquantai.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initial read with no table returns empty list
    assert read_datamgr_log(db_path) == []
    assert clear_datamgr_log(db_path) == 0

    log_datamgr_operation(
        db_path, "EURUSD_dukascopy", "download", "succeeded", "Downloaded 5 days"
    )
    log_datamgr_operation(
        db_path, "EURUSD_dukascopy", "clear", "succeeded", "Cleared history"
    )

    events = read_datamgr_log(db_path)
    assert len(events) == 2
    assert events[0]["symbol"] == "EURUSD_dukascopy"
    assert events[0]["operation"] == "download"
    assert events[0]["status"] == "succeeded"
    assert events[0]["message"] == "Downloaded 5 days"
    assert events[1]["operation"] == "clear"

    cleared = clear_datamgr_log(db_path)
    assert cleared == 2
    assert read_datamgr_log(db_path) == []
