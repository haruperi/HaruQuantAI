"""Canonical Parquet and independent reader tests on an isolated store."""

from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import MarketAccess
from app.persistence.market import (
    TICK_SCHEMA,
    MarketDataStore,
    create_isolated_schema,
)


def test_tick_month_publish_scan_and_query(tmp_path: Path) -> None:
    """One period uses the requested schema, compression and file path."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    start = datetime(2020, 4, 1, tzinfo=UTC)
    table = pa.Table.from_arrays(
        [
            pa.array([start], type=TICK_SCHEMA.field("DateTime").type),
            pa.array([1500000], type=pa.int64()),
            pa.array([1499990], type=pa.int64()),
            pa.array([20000], type=pa.uint64()),
        ],
        schema=TICK_SCHEMA,
    )
    first_ms = int(start.timestamp() * 1000)
    record = store.publish(
        source="dukascopy",
        kind="ticks",
        symbol="chfjpy",
        period="2020-04",
        table=table,
        coverage=((first_ms, first_ms),),
        provider_mode="standard",
    )
    assert record.relative_path == "market/dukascopy/ticks/chfjpy/2020/04-apr.parquet"
    assert record.row_count == 1
    try:
        import duckdb  # noqa: F401 -- native module can be blocked by host policy.
    except ImportError:
        pass
    else:
        assert store.query(record, "SELECT count(*) FROM market_data") == [(1,)]
    assert store.list_files("dukascopy", "ticks", "chfjpy") == (record,)
    with pytest.raises(ValueError):
        store.path("dukascopy", "ticks", "../evil", "2020-04")


def test_broker_catalog_is_owner_scoped(tmp_path: Path) -> None:
    """Other plugins cannot read Data Manager broker profiles."""
    market = MarketAccess(
        "plugin.some_other_owner",
        MarketDataStore(tmp_path, tmp_path / "database" / "haruquantai.db"),
    )
    with pytest.raises(PermissionError, match="ownership denied"):
        market.list_brokers()


def test_interval_rewrite_keeps_other_days_and_one_current_file(tmp_path: Path) -> None:
    """A month rewrite retains prior days and publishes one ZSTD file."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    def table(day: int, volume: int) -> pa.Table:
        instant = datetime(2020, 4, day, tzinfo=UTC)
        return pa.Table.from_arrays(
            [
                pa.array([instant], type=TICK_SCHEMA.field("DateTime").type),
                pa.array([1500000], type=pa.int64()),
                pa.array([1499990], type=pa.int64()),
                pa.array([volume], type=pa.uint64()),
            ],
            schema=TICK_SCHEMA,
        )

    def replace(day: int, volume: int) -> None:
        start = int(datetime(2020, 4, day, tzinfo=UTC).timestamp() * 1000)
        store.replace_interval(
            source="dukascopy",
            kind="ticks",
            symbol="chfjpy",
            period="2020-04",
            incoming=table(day, volume),
            start_ms=start,
            end_ms=start + 86400000 - 1,
            provider_mode="standard",
        )

    replace(1, 10000)
    replace(2, 20000)
    replace(1, 30000)
    record = store.list_files("dukascopy", "ticks", "chfjpy")[0]
    assert record.revision == 3
    path = tmp_path / record.relative_path
    parquet = pq.ParquetFile(path)
    assert parquet.metadata.row_group(0).column(0).compression == "ZSTD"
    assert parquet.read().column("Volume").to_pylist() == [30000, 20000]
    assert len(list(path.parent.glob("*.parquet"))) == 1


def test_dataset_registration_is_separate_from_coverage(tmp_path: Path) -> None:
    """An added definition has no fabricated dates, bars, or market file."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    dataset = store.register_dataset(
        source="dukascopy", symbol="eurusd", kind="m1", instrument="EURUSD"
    )
    assert store.get_dataset(dataset.id) == dataset
    assert store.list_files("dukascopy", "m1", "eurusd") == ()
    with pytest.raises(ValueError, match="already exists"):
        store.register_dataset(
            source="dukascopy", symbol="eurusd", kind="m1", instrument="EURUSD"
        )


def test_tick_rows_with_same_millisecond_are_preserved(tmp_path: Path) -> None:
    """The canonical Tick schema has no sequence key, so equal times stay distinct."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    instant = datetime(2020, 4, 1, tzinfo=UTC)
    table = pa.Table.from_arrays(
        [
            pa.array([instant, instant], type=TICK_SCHEMA.field("DateTime").type),
            pa.array([1500000, 1500001], type=pa.int64()),
            pa.array([1499990, 1499991], type=pa.int64()),
            pa.array([10000, 20000], type=pa.uint64()),
        ],
        schema=TICK_SCHEMA,
    )
    start = int(instant.timestamp() * 1000)
    record = store.replace_interval(
        source="dukascopy",
        kind="ticks",
        symbol="chfjpy",
        period="2020-04",
        incoming=table,
        start_ms=start,
        end_ms=start + 86400000 - 1,
        provider_mode="standard",
    )
    values = pq.read_table(tmp_path / record.relative_path).column("Ask").to_pylist()
    assert values == [1500000, 1500001]


def test_definition_batch_without_price_catalog(tmp_path):
    """A save is durable, atomic and independent of price storage migrations."""
    import sqlite3
    from contextlib import closing

    from app.persistence.market import SCHEMA, DefinitionRequest

    database = tmp_path / "definitions.db"
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executescript(SCHEMA.split("CREATE TABLE market_files")[0])
        connection.execute(
            "ALTER TABLE datamgr_datasets ADD COLUMN path TEXT DEFAULT ''"
        )
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER, name TEXT, postfix TEXT, "
            "server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (3,'Dukascopy','_dukascopy','EET',1,1)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (4,'Disabled','','UTC',0,1)"
        )
    store = MarketDataStore(tmp_path, database)
    assert store.definitions_available() and not store.available()
    rows = store.register_definitions(
        (
            DefinitionRequest("USDJPY", "m1", "3", "_dukascopy"),
            DefinitionRequest("EURUSD", "ticks"),
        )
    )
    reopened = MarketDataStore(tmp_path, database)
    listed = reopened.list_datasets("dukascopy")
    assert len(listed) == 2
    saved = next(row for row in listed if row["broker"] == "3")
    assert saved["symbol"] == "USDJPY_dukascopy"
    assert saved["underlying"] == "USDJPY"
    assert saved["brokerName"] == "Dukascopy"
    assert saved["bars"] == 0 and saved["timezone"] == "UTC"
    assert reopened.get_dataset(rows[0].id).symbol == "usdjpy"
    for invalid in (
        DefinitionRequest("GBPUSD", "m1", "4"),
        DefinitionRequest("GBPUSD", "m1", postfix="../escape"),
        DefinitionRequest("GBPUSD", "m1", instrument="fabricated"),
        DefinitionRequest("USDJPY", "m1", "3", "_dukascopy"),
    ):
        with pytest.raises(ValueError):
            store.register_definitions((DefinitionRequest("AUDUSD", "m1"), invalid))
        assert len(store.list_datasets("dukascopy")) == 2
    with pytest.raises(ValueError):
        store.register_definitions((DefinitionRequest("NZDUSD", "m1"),) * 2)
    with pytest.raises(ValueError):
        store.register_definitions(())
    assert len(store.list_datasets("dukascopy")) == 2
    assert not MarketDataStore(tmp_path, tmp_path / "absent.db").definitions_available()
