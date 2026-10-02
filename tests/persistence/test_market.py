"""Market catalog schema never mutates an existing unified database."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import MarketAccess
from app.host.contracts import (
    BrokerTimeProvenance,
    ClockPolicy,
    ClockProvenance,
    OperationRejectedError,
)
from app.persistence import market as market_module
from app.persistence.market import (
    M1_SCHEMA,
    TICK_SCHEMA,
    BrokerSchemaUnavailableError,
    DefinitionRequest,
    MarketDataStore,
    MarketSchemaUnavailableError,
    clear_datamgr_log,
    clear_market_symbol,
    create_isolated_schema,
    delete_market_symbol,
    log_datamgr_operation,
    migrate_broker_clock_schema,
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


def clock_test_store(tmp_path: Path) -> tuple[MarketDataStore, ClockPolicy]:
    database = tmp_path / "clock.db"
    create_isolated_schema(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, postfix TEXT, server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (2,'Test broker','','UTC+2',1,1)"
        )
    backup = migrate_broker_clock_schema(database)
    assert backup is not None and backup.is_file()
    assert migrate_broker_clock_schema(database) is None
    policy = ClockPolicy.model_validate(
        {
            "revision": 1,
            "effective_from_utc": "2024-01-01T00:00:00Z",
            "effective_to_utc": "2025-01-01T00:00:00Z",
            "standard_offset_minutes": 120,
            "initial_offset_minutes": 120,
            "tick_time_basis": "server_wall_clock",
            "bar_time_basis": "server_wall_clock",
            "request_time_basis": "utc",
            "verified": True,
            "evidence_references": ["synthetic-test"],
            "assessed_at": "2026-10-02T00:00:00Z",
            "limitations": "Synthetic fixture; no live broker inference",
        }
    )
    return MarketDataStore(tmp_path, database), policy


def test_missing_clock_schema_rejects_without_changing_store(tmp_path: Path) -> None:
    database = tmp_path / "missing-clock.db"
    create_isolated_schema(database)
    before = database.read_bytes()
    store = MarketDataStore(tmp_path, database)
    with pytest.raises(OperationRejectedError) as rejected:
        store.broker_clock_policy("6")
    assert rejected.value.code == "CLOCK_SCHEMA_REQUIRED"
    assert rejected.value.status == 409
    assert database.read_bytes() == before


def test_clock_policy_migration_history_cas_and_backup(tmp_path: Path) -> None:
    store, policy = clock_test_store(tmp_path)
    assert store.broker_clock_policy("2")["revision"] == 0
    store.replace_broker_clock_policy("2", 0, policy)
    with pytest.raises(ValueError, match="changed"):
        store.replace_broker_clock_policy("2", 0, policy)
    overlap = policy.model_copy(update={"revision": 2})
    with pytest.raises(ValueError, match="overlap"):
        store.replace_broker_clock_policy("2", 1, overlap)
    second = ClockPolicy.model_validate(
        {
            **policy.model_dump(mode="json"),
            "revision": 2,
            "effective_from_utc": "2025-01-01T00:00:00Z",
            "effective_to_utc": "2026-01-01T00:00:00Z",
        }
    )
    store.replace_broker_clock_policy("2", 1, second)
    assert len(store.broker_clock_policy("2")["revisions"]) == 2
    backup = next(tmp_path.glob("*.backup"))
    with closing(sqlite3.connect(backup)) as connection:
        assert (
            connection.execute("SELECT name FROM datamgr_broker WHERE id=2").fetchone()[
                0
            ]
            == "Test broker"
        )
        assert "clock_policy_json" not in {
            row[1] for row in connection.execute("PRAGMA table_info(datamgr_broker)")
        }


def test_clock_provenance_integrity_replay_and_owner_boundaries(tmp_path: Path) -> None:
    store, policy = clock_test_store(tmp_path)
    owner = "plugin.data_manager.meta_trader"
    source = MarketAccess(owner, store)
    workspace = MarketAccess("workspace.data_manager", store)
    dataset_id = source.register_source(
        source="MT5",
        symbol="TEST",
        underlying="TEST",
        instrument="TEST",
        timeframe="M1",
        broker="2",
    )
    workspace.replace_broker_clock_policy("2", 0, policy)
    assert source.broker_clock_policy("2", dataset_id=dataset_id)["revision"] == 1
    with pytest.raises(PermissionError):
        source.replace_broker_clock_policy("2", 1, policy)
    with pytest.raises(PermissionError):
        source.broker_clock_policy("2")
    table = pa.Table.from_pandas(
        pd.DataFrame(
            {
                "DateTime": [pd.Timestamp("2024-01-01T10:00:00Z")],
                "Open": [1.0],
                "High": [1.0],
                "Low": [1.0],
                "Close": [1.0],
                "Volume": [1],
            }
        ),
        preserve_index=False,
    )
    raw = int(pd.Timestamp("2024-01-01T12:00:00Z").timestamp() * 1000)
    provenance = ClockProvenance(
        policy=policy, input_basis="server_wall_clock", raw_timestamps_ms=(raw,)
    )
    part = source.publish_source(dataset_id, "2024", table, clock_provenance=provenance)
    assert workspace.source_clock_provenance(dataset_id, "2024") == provenance
    assert workspace.inventory()[0]["clockNormalization"] == "normalized"
    assert (
        source.publish_source(
            dataset_id, "2024", table, expected_revision=1, clock_provenance=provenance
        )["revision"]
        == 1
    )
    with pytest.raises(ValueError, match="correspond"):
        source.publish_source(
            dataset_id,
            "2024",
            table,
            expected_revision=1,
            clock_provenance=provenance.model_copy(
                update={"raw_timestamps_ms": (raw + 1,)}
            ),
        )
    record = json.loads(part["clock_provenance_json"])
    (tmp_path / record["raw_resource"]["relative_path"]).write_text("[]")
    with pytest.raises(ValueError, match="integrity"):
        workspace.source_clock_provenance(dataset_id, "2024")


def legacy_clock_database(tmp_path: Path) -> Path:
    """Represent a populated deployed store without any clock columns."""
    database = tmp_path / "legacy.db"
    create_isolated_schema(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "ALTER TABLE source_partitions DROP COLUMN clock_provenance_json"
        )
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, "
            "enabled INTEGER, mt_use INTEGER, server_timezone TEXT)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (6,'Test broker',1,1,'UTC')"
        )
        connection.execute('CREATE TABLE "quoted""table" (value BLOB, note TEXT)')
        connection.execute(
            'INSERT INTO "quoted""table" VALUES (?, ?)', (b"\x00\xff", "retained")
        )
    return database


def test_clock_migration_preserves_wal_rows_and_verified_backup(tmp_path: Path) -> None:
    database = legacy_clock_database(tmp_path)
    with closing(sqlite3.connect(database)) as writer, writer:
        writer.execute('INSERT INTO "quoted""table" VALUES (?, ?)', (b"wal", "new"))
        writer.commit()
        columns = market_module._clock_original_columns(writer)
        before = market_module._clock_contents(writer, columns)
        backup = migrate_broker_clock_schema(database)
        assert backup is not None
        with closing(sqlite3.connect(backup)) as copied:
            assert copied.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert market_module._clock_contents(copied, columns) == before
            assert market_module._clock_original_columns(copied) == columns
        assert market_module._clock_contents(writer, columns) == before
        assert writer.execute(
            "SELECT clock_policy_json,clock_policy_revision FROM datamgr_broker "
            "WHERE id=6"
        ).fetchone() == ("{}", 0)
    assert migrate_broker_clock_schema(database) is None


@pytest.mark.parametrize("defect", ["type", "partial", "conflict"])
def test_clock_migration_refuses_incompatible_schema(
    tmp_path: Path, defect: str
) -> None:
    database = legacy_clock_database(tmp_path)
    with closing(sqlite3.connect(database)) as connection, connection:
        if defect == "type":
            connection.execute("ALTER TABLE datamgr_broker RENAME TO old_broker")
            connection.execute(
                "CREATE TABLE datamgr_broker (id TEXT PRIMARY KEY, name TEXT, "
                "enabled INTEGER, mt_use INTEGER, server_timezone TEXT)"
            )
        elif defect == "partial":
            connection.execute(
                "ALTER TABLE datamgr_broker ADD COLUMN clock_policy_json TEXT "
                "NOT NULL DEFAULT '{}'"
            )
        else:
            connection.execute(
                "ALTER TABLE source_partitions ADD COLUMN clock_provenance_json "
                "INTEGER NOT NULL DEFAULT 0"
            )
    with pytest.raises(BrokerSchemaUnavailableError):
        migrate_broker_clock_schema(database)
    assert list(tmp_path.glob("*.backup")) == []


def test_clock_migration_rolls_back_failed_postcondition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = legacy_clock_database(tmp_path)
    validate = market_module._clock_validate_schema
    calls = 0

    def fail_after_alter(schema: dict[str, dict[str, tuple[Any, ...]]]) -> None:
        nonlocal calls
        calls += 1
        validate(schema)
        if calls == 2:
            raise ValueError("Injected verification failure")

    monkeypatch.setattr(market_module, "_clock_validate_schema", fail_after_alter)
    with pytest.raises(ValueError, match="Injected"):
        migrate_broker_clock_schema(database)
    with closing(sqlite3.connect(database)) as connection:
        assert (
            "clock_policy_json"
            not in market_module._clock_schema(connection)["datamgr_broker"]
        )
        assert connection.execute("SELECT id FROM datamgr_broker").fetchall() == [(6,)]
    assert len(list(tmp_path.glob("*.backup"))) == 1


def test_clock_migration_lock_wait_is_bounded(tmp_path: Path) -> None:
    database = legacy_clock_database(tmp_path)
    with closing(sqlite3.connect(database)) as writer:
        writer.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            migrate_broker_clock_schema(database, lock_timeout_seconds=0.05)
        writer.rollback()
    assert list(tmp_path.glob("*.backup")) == []
    with pytest.raises(ValueError, match="timeout"):
        migrate_broker_clock_schema(database, lock_timeout_seconds=0)


def test_broker_time_publication_is_explicit_and_independently_readable(
    tmp_path: Path,
) -> None:
    database = tmp_path / "raw.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    source = MarketAccess("plugin.data_manager.meta_trader", store)
    dataset_id = source.register_source(
        source="MT5",
        symbol="RAW",
        underlying="RAW",
        instrument="RAW",
        timeframe="M1",
        timezone="Exchange/Broker",
        options={"timestamp_basis": "broker_reported"},
    )
    table = pa.Table.from_pandas(
        pd.DataFrame(
            {
                "DateTime": pd.to_datetime(["2024-10-27 03:00", "2024-10-27 03:00"]),
                "Open": [1.0, 2.0],
                "High": [2.0, 3.0],
                "Low": [1.0, 2.0],
                "Close": [1.5, 2.5],
                "Volume": [1, 2],
                "SourceRecord": ["first", "second"],
            }
        ),
        preserve_index=False,
    )
    stamps = tuple(
        table.column("DateTime").cast(pa.timestamp("ms")).cast(pa.int64()).to_pylist()
    )
    provenance = BrokerTimeProvenance(dataset_id=dataset_id, raw_timestamps_ms=stamps)
    with pytest.raises(ValueError, match="explicit raw"):
        source.publish_source(dataset_id, "2024", table)
    with pytest.raises(ValueError, match="correspond"):
        source.publish_broker_time_source(
            dataset_id,
            "2024",
            table,
            provenance=provenance.model_copy(update={"raw_timestamps_ms": (1, 2)}),
        )
    utc_table = table.set_column(
        0, "DateTime", table.column("DateTime").cast(pa.timestamp("ms", tz="UTC"))
    )
    with pytest.raises(ValueError, match="declared time basis"):
        source.publish_broker_time_source(
            dataset_id, "2024", utc_table, provenance=provenance
        )
    with pytest.raises(ValueError, match="identity mismatch"):
        source.publish_broker_time_source(
            dataset_id,
            "2024",
            table,
            provenance=provenance.model_copy(update={"dataset_id": "f" * 32}),
        )
    source.publish_broker_time_source(dataset_id, "2024", table, provenance=provenance)
    workspace = MarketAccess("workspace.data_manager", store)
    assert workspace.read_source(dataset_id).equals(table)
    assert workspace.source_clock_provenance(dataset_id, "2024") == provenance
    assert store.inventory()[0]["clockNormalization"] == "broker_time"
    with pytest.raises(ValueError):
        MarketAccess("plugin.other", store).publish_broker_time_source(
            dataset_id, "2024", table, provenance=provenance
        )


def test_mt5_canonical_persistence_paths_and_lifecycle(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    ds_m1 = store.register_dataset(
        source="mt5", symbol="eurusd", kind="m1", instrument="EURUSD"
    )
    assert ds_m1.source == "mt5"
    assert ds_m1.symbol == "eurusd"
    assert ds_m1.kind == "m1"

    defs = (DefinitionRequest("GBPUSD", "ticks", "-1", "", "GBPUSD"),)
    created = store.register_definitions(defs, source="mt5")
    assert len(created) == 1
    ds_ticks = created[0]
    assert ds_ticks.source == "mt5"
    assert ds_ticks.symbol == "gbpusd"
    assert ds_ticks.kind == "ticks"

    reused = store.register_definitions(defs, source="mt5", idempotent=True)
    assert len(reused) == 1
    assert reused[0].id == ds_ticks.id

    with pytest.raises(ValueError, match="MT5 dataset definition already exists"):
        store.register_definitions(defs, source="mt5", idempotent=False)

    m1_table = pa.Table.from_pandas(
        pd.DataFrame(
            {
                "DateTime": pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
                "Open": [1.1000],
                "High": [1.1010],
                "Low": [1.0990],
                "Close": [1.1005],
                "Volume": [100],
            }
        ),
        schema=M1_SCHEMA,
    )
    stamps_m1 = m1_table.column("DateTime").cast(pa.int64()).to_pylist()
    f_m1 = store.replace_interval(
        source="mt5",
        kind="m1",
        symbol="eurusd",
        period="2024",
        incoming=m1_table,
        start_ms=stamps_m1[0],
        end_ms=stamps_m1[-1],
        provider_mode="standard",
    )
    assert f_m1.relative_path == "market/mt5/m1/eurusd/2024.parquet"
    assert (tmp_path / f_m1.relative_path).exists()

    ticks_table = pa.Table.from_pandas(
        pd.DataFrame(
            {
                "DateTime": pd.to_datetime(["2024-05-15 12:00:00+00:00"]),
                "Bid": [125000],
                "Ask": [125020],
                "Volume": [50],
            }
        ),
        schema=TICK_SCHEMA,
    )
    stamps_ticks = ticks_table.column("DateTime").cast(pa.int64()).to_pylist()
    f_ticks = store.replace_interval(
        source="mt5",
        kind="ticks",
        symbol="gbpusd",
        period="2024-05",
        incoming=ticks_table,
        start_ms=stamps_ticks[0],
        end_ms=stamps_ticks[-1],
        provider_mode="standard",
    )
    assert f_ticks.relative_path == "market/mt5/ticks/gbpusd/2024/05-may.parquet"
    assert (tmp_path / f_ticks.relative_path).exists()

    files = store.list_files("mt5", "m1", "eurusd")
    assert len(files) == 1
    assert files[0].relative_path == f_m1.relative_path

    rows_tbl = store.read_market_rows(ds_m1.id, start_ms=0, end_ms=2000000000000)
    assert rows_tbl.num_rows == 1

    with closing(open_market_catalog(database)) as connection:
        connection.execute(
            "UPDATE datamgr_datasets SET timezone = 'EST' WHERE id = ?",
            (ds_m1.id,),
        )
        connection.commit()

    with pytest.raises(
        ValueError, match="non-UTC dataset is not a canonical market dataset"
    ):
        store.get_dataset(ds_m1.id)

    with closing(open_market_catalog(database)) as connection:
        connection.execute(
            "UPDATE datamgr_datasets SET timezone = 'UTC' WHERE id = ?",
            (ds_m1.id,),
        )
        connection.commit()

    cleared = store.clear_dataset("eurusd")
    assert cleared is True
    assert not (tmp_path / f_m1.relative_path).exists()

    deleted = store.delete_dataset("eurusd")
    assert deleted is True
    with pytest.raises(ValueError, match="Market dataset unavailable"):
        store.get_dataset(ds_m1.id)
