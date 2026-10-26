"""Tests for Dukascopy market data ingestion, partitioning, and catalog service."""

import sqlite3

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
    assert records[0]["broker"] == "SQ default"
    assert "instrument" not in records[0]
    assert "broker_name" not in records[0]

    # Verify persisted in database
    db_recs = gateway.read_records("datamgr_datasets")["data"]["records"]
    assert len(db_recs) == 2
    assert "instrument" not in db_recs[0]
    assert "broker_name" not in db_recs[0]
    assert db_recs[0]["underlying"] == "EURUSD"
    assert db_recs[0]["broker"] == "SQ default"


def test_add_with_numeric_broker_id(temp_env):
    service, gateway, _ = temp_env
    conn = sqlite3.connect(gateway.database_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS datamgr_broker (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, is_system INTEGER DEFAULT 0
            );
        """)
        conn.execute(
            "INSERT INTO datamgr_broker (id, name, is_system) VALUES (3, '[[Dukascopy]]', 1);"
        )
        conn.commit()
    finally:
        conn.close()

    res = service.add(
        symbols=["USDJPY"],
        data_type="M1",
        broker="3",
        postfix="_DUKAS",
    )
    assert res["success"] is True
    rec = res["data"]["records"][0]
    assert rec["broker"] == "Dukascopy"
    assert "instrument" not in rec
    assert "broker_name" not in rec

    db_rec = gateway.read_records(
        "datamgr_datasets", filters={"id": "dukascopy:USDJPY_DUKAS:M1"}
    )["data"]["records"][0]
    assert db_rec["broker"] == "Dukascopy"
    assert "instrument" not in db_rec
    assert "broker_name" not in db_rec


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
    assert ds_row["date_from"].startswith("2024-12-31")
    assert ds_row["date_to"].startswith("2025-01-01")


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


def _bars(dates, prices=None, volume=1):
    prices = prices or [1.1] * len(dates)
    return pd.DataFrame(
        {
            **dict.fromkeys(("Open", "High", "Low", "Close"), prices),
            "Volume": [volume] * len(dates),
        },
        index=pd.to_datetime(dates, utc=True),
    )


def test_canonical_reader_decodes_exactly_once(temp_env):
    from app.workspace.brokers.dukascopy import DukascopyClient
    from app.workspace.brokers.files import read_parquet_bars

    service, gateway, root = temp_env
    result = service.download("EURUSD", data_frame=_bars(["2025-01-01"]))
    assert result["success"], result
    path = result["data"]["partitions_written"][0]
    assert read_parquet_bars(path)[0]["open"] == pytest.approx(1.1)
    client = DukascopyClient(
        data_dir=root, catalog_path=service.catalog_path, gateway=gateway
    )
    try:
        assert client.get_bars("EURUSD", count=1)["Open"].iloc[0] == pytest.approx(1.1)
    finally:
        client.disconnect()


def test_postfix_and_tick_paths_are_dataset_owned(temp_env):
    from pathlib import Path

    service, gateway, _ = temp_env
    ticks = pd.DataFrame(
        {"Bid": [1.1], "Ask": [1.10001]}, index=pd.to_datetime(["2025-04-01"], utc=True)
    )
    result = service.download(
        "EURUSD_X", underlying="EURUSD", timeframe="TICK", data_frame=ticks
    )
    assert result["success"], result
    row = gateway.read_records(
        "datamgr_datasets", filters={"id": result["data"]["dataset_id"]}
    )["data"]["records"][0]
    assert Path(row["path"]).exists()
    assert Path(row["path"]).parts[-2:] == ("ticks", "eurusd_x")
    assert Path(result["data"]["partitions_written"][0]).is_relative_to(row["path"])


def test_distinct_same_timestamp_ticks_survive_repeated_import(temp_env):
    service, _, _ = temp_env
    frame = pd.DataFrame(
        {"Bid": [1.1, 1.10001], "Ask": [1.10002, 1.10003], "Flags": [1, 2]},
        index=pd.to_datetime(["2025-04-01", "2025-04-01"], utc=True),
    )
    for _ in range(2):
        result = service.download("EURUSD", timeframe="TICK", data_frame=frame)
        assert result["success"], result
        assert result["data"]["total_bars"] == 2


def test_overwrite_preserves_history_outside_requested_interval(temp_env):
    service, _, _ = temp_env
    assert service.download("EURUSD", data_frame=_bars(["2025-01-01", "2025-02-01"]))[
        "success"
    ]
    result = service.download(
        "EURUSD",
        data_frame=_bars(["2025-02-01"], [1.2]),
        date_from="2025-02-01",
        date_to="2025-02-01",
        overwrite=True,
    )
    assert result["success"], result
    assert result["data"]["total_bars"] == 2
    assert service.scan_polars("EURUSD").collect()["Open"].to_list() == [110000, 120000]


@pytest.mark.parametrize("volume", [-1, 1.5, 2**64, float("nan")])
def test_invalid_unsigned_values_never_publish(temp_env, volume):
    service, _, root = temp_env
    result = service.download("EURUSD", data_frame=_bars(["2025-01-01"], volume=volume))
    assert not result["success"]
    assert list(root.rglob("*.parquet")) == []


def test_failed_catalog_commit_keeps_old_snapshot_and_cleans_new_parts(
    temp_env, monkeypatch
):
    from pathlib import Path

    service, gateway, root = temp_env
    first = service.download("EURUSD", data_frame=_bars(["2025-01-01"]))
    old = Path(first["data"]["partitions_written"][0])
    original = old.read_bytes()
    monkeypatch.setattr(
        HostPersistence,
        "update_record",
        lambda *args, **kwargs: {"success": False, "error": {"message": "Rejected"}},
    )
    result = service.download("EURUSD", data_frame=_bars(["2025-01-02"]))
    assert not result["success"]
    assert old.read_bytes() == original
    assert list(root.rglob("*.parquet")) == [old]
    assert gateway.read_records("datamgr_datasets")["data"]["records"][0]["bars"] == 1


def test_publication_replaces_one_canonical_file_and_reader_sees_latest(temp_env):
    from pathlib import Path

    service, _, _ = temp_env
    first = service.download("EURUSD", data_frame=_bars(["2025-01-01"]))
    path = Path(first["data"]["partitions_written"][0])
    original = path.read_bytes()
    second = service.download("EURUSD", data_frame=_bars(["2025-01-02"]))
    assert second["success"], second
    assert path.read_bytes() != original
    assert path.name == "2025.parquet"
    assert second["data"]["partitions"] == [str(path)]
    assert list(path.parent.glob("*.parquet")) == [path]
    assert service.scan_polars("EURUSD").collect().height == 2
    assert (
        pq.read_metadata(second["data"]["partitions_written"][0])
        .row_group(0)
        .column(1)
        .compression
        == "ZSTD"
    )


def test_concurrent_writers_preserve_both_committed_ranges(temp_env):
    from concurrent.futures import ThreadPoolExecutor

    service, _, _ = temp_env
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda date: service.download("EURUSD", data_frame=_bars([date])),
                ["2025-01-01", "2025-01-02"],
            )
        )
    assert all(result["success"] for result in results), results
    assert service.scan_polars("EURUSD").collect().height == 2


def test_large_partition_is_one_file_with_batched_row_groups(temp_env):
    service, _, root = temp_env
    dates = pd.date_range("2026-01-01", periods=70_000, freq="min", tz="UTC")
    result = service.download("EURUSD", data_frame=_bars(dates))
    assert result["success"], result
    target = root / "m1" / "eurusd" / "2026.parquet"
    assert result["data"]["partitions"] == [str(target)]
    metadata = pq.read_metadata(target)
    assert metadata.num_rows == 70_000
    assert metadata.num_row_groups == 2
    assert metadata.row_group(0).num_rows == 65_536
    assert metadata.schema.to_arrow_schema().remove_metadata().equals(M1_SCHEMA)
    assert metadata.row_group(0).column(1).compression == "ZSTD"
    assert list(target.parent.glob("*.parquet")) == [target]


@pytest.mark.parametrize("committed", [False, True])
def test_interrupted_canonical_replacement_recovers_from_journal(temp_env, committed):
    from app.workspace.data_manager.partition_files import (
        FilePublication,
        dataset_lock,
        recover_publications,
    )

    service, gateway, root = temp_env
    result = service.download("EURUSD", data_frame=_bars(["2025-01-01"]))
    target = root / "m1" / "eurusd" / "2025.parquet"
    before = target.read_bytes()
    stage = target.with_name(".2025.test.pending.parquet")
    stage.write_bytes(before)
    # Different valid bytes let the test distinguish undo from committed cleanup.
    table = pq.ParquetFile(target).read()
    pq.write_table(table, stage, compression="zstd", compression_level=6)
    after = stage.read_bytes()
    publication = FilePublication(
        target.parent, [stage], result["data"]["dataset_id"], "commit-token"
    )
    publication.install()
    if committed:
        assert gateway.update_record(
            "datamgr_datasets",
            {"updated_at": "commit-token"},
            filters={"id": result["data"]["dataset_id"]},
        )["success"]
    with dataset_lock(target.parent):
        recover_publications(target.parent, gateway)
    assert target.read_bytes() == (after if committed else before)
    assert not publication.journal.exists()
    assert not list(target.parent.glob("*.backup"))


def test_old_part_manifest_is_consolidated_without_rescaling(temp_env):
    import json

    service, gateway, root = temp_env
    first = service.download("EURUSD", data_frame=_bars(["2025-01-01"]))
    target = root / "m1" / "eurusd" / "2025.parquet"
    old = target.parent / "2025" / "part-old.parquet"
    old.parent.mkdir()
    target.replace(old)
    row = gateway.read_records("datamgr_datasets")["data"]["records"][0]
    lineage = json.loads(row["lineage_json"])
    lineage["partitions"] = [str(old)]
    assert gateway.update_record(
        "datamgr_datasets",
        {"lineage_json": json.dumps(lineage)},
        filters={"id": first["data"]["dataset_id"]},
    )["success"]
    result = service.download("EURUSD", data_frame=_bars(["2025-01-02"]))
    assert result["success"], result
    assert result["data"]["partitions"] == [str(target)]
    assert service.scan_polars("EURUSD").collect()["Open"].to_list() == [110000, 110000]


def test_parquet_preparation_does_not_hold_sqlite_write_lock(temp_env, monkeypatch):
    from app.workspace.data_manager import storage

    service, gateway, _ = temp_env
    assert service.download("EURUSD", data_frame=_bars(["2025-01-01"]))["success"]
    probe = HostPersistence(gateway.database_path, timeout=0.05)
    original = storage._merge_partition
    checked = []

    def merge(*args, **kwargs):
        # Authentication/status requests must be able to write while Parquet
        # merge/compression is in progress, even with a short SQLite timeout.
        with probe.transaction() as tx:
            result = tx.update_record(
                "datamgr_datasets",
                {"quality_score": 1.0},
                filters={"id": "dukascopy:EURUSD:M1"},
            )
            assert result["success"]
        checked.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(storage, "_merge_partition", merge)
    result = service.download("EURUSD", data_frame=_bars(["2025-01-02"]))
    assert result["success"], result
    assert checked
    assert result["data"]["total_bars"] == 2


def test_legacy_integer_partition_migrates_without_rescaling(temp_env):
    import json
    from pathlib import Path

    service, gateway, root = temp_env
    first = service.download("EURUSD", data_frame=_bars(["2025-01-01"]))
    legacy = root / "m1" / "eurusd" / "2025.parquet"
    pq.write_table(
        pq.read_table(first["data"]["partitions_written"][0]).replace_schema_metadata(
            None
        ),
        legacy,
    )
    row = gateway.read_records("datamgr_datasets")["data"]["records"][0]
    lineage = json.loads(row["lineage_json"])
    lineage["partitions"] = [str(legacy)]
    gateway.update_record(
        "datamgr_datasets",
        {"lineage_json": json.dumps(lineage)},
        filters={"id": row["id"]},
    )
    before = Path(legacy).read_bytes()
    result = service.download("EURUSD", data_frame=_bars(["2025-01-02"]))
    assert result["success"], result
    assert legacy.read_bytes() != before
    assert result["data"]["partitions"] == [str(legacy)]
    assert service.scan_polars("EURUSD").collect()["Open"].to_list() == [110000, 110000]


def test_broker_tick_range_visits_every_hour_without_default_limit(
    temp_env, monkeypatch
):
    from datetime import UTC, datetime

    from app.workspace.brokers.dukascopy import DukascopyClient

    service, gateway, root = temp_env
    client = DukascopyClient(
        data_dir=root,
        catalog_path=service.catalog_path,
        gateway=gateway,
        use_cache=False,
    )
    calls = []

    def fetch(**kwargs):
        calls.append(kwargs)
        base = int(kwargs["dt"].timestamp() * 1000)
        return [{"time_msc": base + i, "bid": 1.1, "ask": 1.10001} for i in range(1200)]

    monkeypatch.setattr(client, "_fetch_datafeed_ticks", fetch)
    try:
        result = client.get_ticks(
            "EURUSD",
            date_from=datetime(2025, 1, 1, tzinfo=UTC),
            date_to=datetime(2025, 1, 1, 1, 59, tzinfo=UTC),
        )
        assert len(result) == 2400
        assert len(calls) == 2 and all(call["count"] is None for call in calls)
    finally:
        client.disconnect()
