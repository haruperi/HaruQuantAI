"""Tests for Dukascopy market data ingestion, partitioning, and catalog service."""

import pandas as pd  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.dukascopy import (
    M1_SCHEMA,
    TICK_SCHEMA,
    Dukascopy,
)


@pytest.fixture
def temp_env(tmp_path):
    """Fixture providing isolated database, storage root, and test catalog."""
    import sqlite3

    db_file = tmp_path / "test.db"
    sqlite3.connect(db_file).close()
    gateway = HostPersistence(db_file)
    gateway.ensure_datasets_schema()

    storage_root = tmp_path / "market" / "dukascopy"
    catalog_path = storage_root / "dukascopy.csv"
    storage_root.mkdir(parents=True, exist_ok=True)

    # Minimal catalog for testing
    csv_content = (
        "EURUSD;Euro / US Dollar;Forex;Majors;05.05.2003;05.05.2003;5;100000;3;0.0001;0.00001;3\n"
        "GBPUSD;British Pound / US Dollar;Forex;Majors;05.05.2003;05.05.2003;5;100000;3;0.0001;0.00001;3\n"
        "USDJPY;US Dollar / Yen;Forex;Majors;05.05.2003;05.05.2003;3;1000;3;0.01;0.001;3\n"
    )
    catalog_path.write_text(csv_content, encoding="latin1")

    service = Dukascopy(
        gateway=gateway,
        storage_root=storage_root,
        catalog_path=catalog_path,
    )
    return service, gateway, storage_root


def test_disclaimer(temp_env):
    service, _, _ = temp_env
    res = service.disclaimer()
    assert res["success"] is True
    assert res["data"]["title"] == "Dukascopy data disclaimer"
    assert len(res["data"]["paragraphs"]) == 4
    assert res["data"]["requires_confirmation"] is True
    assert "StrategyQuant CDN" in res["data"]["cdn_disclaimer"]


def test_catalog_query(temp_env):
    service, _, _ = temp_env
    res = service.get_catalog()
    assert res["success"] is True
    assert res["data"]["count"] == 3

    search_res = service.get_catalog(search="yen")
    assert search_res["success"] is True
    assert search_res["data"]["count"] == 1
    assert search_res["data"]["symbols"][0]["symbol"] == "USDJPY"


def test_add_success(temp_env):
    service, gateway, _ = temp_env
    res = service.add(
        symbols=["EURUSD", "GBPUSD"],
        data_type="M1",
        broker="default",
        postfix="_DEMO",
    )
    assert res["success"] is True
    assert res["data"]["count"] == 2
    records = res["data"]["records"]
    assert records[0]["id"] == "dukascopy:EURUSD_DEMO:M1"
    assert records[1]["id"] == "dukascopy:GBPUSD_DEMO:M1"

    # Verify persisted in database
    db_recs = gateway.read_records("datamgr_datasets")["data"]["records"]
    assert len(db_recs) == 2


def test_add_disclaimer_rejected(temp_env):
    service, _, _ = temp_env
    res = service.add(
        symbols=["EURUSD"],
        disclaimer_confirmed=False,
    )
    assert res["success"] is False
    assert res["error"]["code"] == "validation"


def test_add_duplicate_conflict(temp_env):
    service, _, _ = temp_env
    assert service.add(symbols=["EURUSD"], postfix="")["success"] is True
    res2 = service.add(symbols=["EURUSD"], postfix="")
    assert res2["success"] is False
    assert res2["error"]["code"] == "conflict"


def test_add_unknown_symbol(temp_env):
    service, _, _ = temp_env
    res = service.add(symbols=["NONEXISTENT"])
    assert res["success"] is False
    assert res["error"]["code"] == "not_found"


def test_download_m1_parquet(temp_env):
    service, gateway, storage_root = temp_env
    # Add definition first
    service.add(symbols=["EURUSD"], data_type="M1")

    # Synthetic M1 bars across 2 years
    dts_2024 = pd.date_range("2024-12-31 23:58:00", periods=2, freq="1min", tz="UTC")
    dts_2025 = pd.date_range("2025-01-01 00:00:00", periods=3, freq="1min", tz="UTC")
    all_dts = dts_2024.append(dts_2025)

    df = pd.DataFrame(
        {
            "Open": [1.0850, 1.0851, 1.0852, 1.0853, 1.0854],
            "High": [1.0855, 1.0856, 1.0857, 1.0858, 1.0859],
            "Low": [1.0845, 1.0846, 1.0847, 1.0848, 1.0849],
            "Close": [1.0852, 1.0853, 1.0854, 1.0855, 1.0856],
            "Volume": [100, 200, 300, 400, 500],
        },
        index=all_dts,
    )

    res = service.download("EURUSD", timeframe="M1", data_frame=df)
    assert res["success"] is True
    assert res["data"]["downloaded_bars"] == 5
    assert res["data"]["total_bars"] == 5

    # Check partitioned files on disk
    p2024 = storage_root / "m1" / "eurusd" / "2024.parquet"
    p2025 = storage_root / "m1" / "eurusd" / "2025.parquet"
    assert p2024.exists()
    assert p2025.exists()

    # Verify PyArrow schema & integer tick unit encoding
    tbl_2024 = pq.read_table(p2024)
    assert tbl_2024.schema.equals(M1_SCHEMA)
    # Check int64 prices (1.0850 / 0.00001 = 108500)
    assert tbl_2024.column("Open")[0].as_py() == 108500
    assert tbl_2024.column("Close")[0].as_py() == 108520
    assert tbl_2024.column("Volume")[0].as_py() == 100

    # Verify database was updated
    ds_row = gateway.read_records(
        "datamgr_datasets", filters={"id": "dukascopy:EURUSD:M1"}
    )["data"]["records"][0]
    assert ds_row["bars"] == 5
    assert ds_row["date_from"] == "2024-12-31"
    assert ds_row["date_to"] == "2025-01-01"


def test_download_ticks_parquet(temp_env):
    service, gateway, storage_root = temp_env
    service.add(symbols=["EURUSD"], data_type="TICK")

    dts = pd.date_range("2025-04-10 10:00:00", periods=4, freq="1s", tz="UTC")
    df = pd.DataFrame(
        {
            "Bid": [1.08501, 1.08502, 1.08503, 1.08504],
            "Ask": [1.08504, 1.08505, 1.08506, 1.08507],
            "Flags": [1, 2, 4, 8],
        },
        index=dts,
    )

    res = service.download("EURUSD", timeframe="TICK", data_frame=df)
    assert res["success"] is True
    assert res["data"]["downloaded_bars"] == 4

    # Check path format: source/ticks/symbol/year/month
    tick_file = storage_root / "ticks" / "eurusd" / "2025" / "04-apr.parquet"
    assert tick_file.exists()

    tbl = pq.read_table(tick_file)
    assert tbl.schema.equals(TICK_SCHEMA)
    assert tbl.column("Bid")[0].as_py() == 108501
    assert tbl.column("Ask")[0].as_py() == 108504
    assert tbl.column("Flags")[0].as_py() == 1


def test_polars_and_duckdb_readers(temp_env):
    service, _, _ = temp_env
    service.add(symbols=["EURUSD"], data_type="M1")
    dts = pd.date_range("2025-01-01", periods=10, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {
            "Open": [1.085] * 10,
            "High": [1.086] * 10,
            "Low": [1.084] * 10,
            "Close": [1.0855] * 10,
            "Volume": [50] * 10,
        },
        index=dts,
    )
    service.download("EURUSD", timeframe="M1", data_frame=df)

    # Polars scan
    lazy_df = service.scan_polars("EURUSD", "M1")
    collected = lazy_df.collect()
    assert collected.shape == (10, 6)
    assert "DateTime" in collected.columns
    assert "Close" in collected.columns

    # DuckDB query
    duck_res = service.query_duckdb(
        "SELECT count(*) AS total, max(Close) AS max_c FROM $PARQUET",
        symbol="EURUSD",
        timeframe="M1",
    ).fetchall()
    assert duck_res[0][0] == 10
    assert duck_res[0][1] == 108550  # int64 tick unit
