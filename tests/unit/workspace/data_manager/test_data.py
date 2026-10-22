"""Unit tests for Data Manager Data service and dataset editing operations."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import polars as pl
import pyarrow.parquet as pq
import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.data import (
    M1_ARROW_SCHEMA,
    TICK_ARROW_SCHEMA,
    Data,
    DataCLI,
    _Config,
    _format_bars_to_arrow,
    _format_ticks_to_arrow,
    _resolve_tick_size,
)


@pytest.fixture(autouse=True)
def test_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing initialized isolated SQLite database file path."""
    db_file = tmp_path / "test_datamgr_data.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def _seed_dataset(dataset_id: str = "ds:1", **overrides: Any) -> dict[str, Any]:
    """Helper to seed a valid dataset in datamgr_datasets."""
    now_iso = datetime.now(UTC).isoformat()
    record = {
        "id": dataset_id,
        "source": "dukascopy",
        "symbol": "EURUSD",
        "underlying": "EURUSD",
        "instrument": "EURUSD",
        "timeframe": "M1",
        "broker": "default",
        "broker_name": "Default Broker",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2024-01-01",
        "date_to": "2024-01-31",
        "bars": 1000,
        "created_at": now_iso,
        "updated_at": now_iso,
        "path": "/data/bars/eurusd.parquet",
        "data_kind": "bars",
        "quality_score": 1.0,
        "lineage_json": "{}",
        "schema_version": 1,
    }
    record.update(overrides)
    HostPersistence.create_record("datamgr_datasets", record)
    return record


def test_config_dataclass_to_dict() -> None:
    """Test _Config default construction and dictionary representation."""
    config = _Config(table="custom_table")
    data = config.to_dict()
    assert data["table"] == "custom_table"

    default_config = _Config()
    assert default_config.to_dict()["table"] == "datamgr_datasets"


def test_data_edit_single_field(caplog: pytest.LogCaptureFixture) -> None:
    """Test editing a single field updates the record and logs INFO."""
    _seed_dataset("ds:1")
    service = Data()

    with caplog.at_level(logging.INFO):
        updated = service.edit("ds:1", {"symbol": "EURUSD_PRO"})

    assert updated["id"] == "ds:1"
    assert updated["symbol"] == "EURUSD_PRO"
    assert updated["broker"] == "default"  # preserved
    assert updated["bars"] == 1000  # preserved

    # Check logger output
    messages = [
        r.message for r in caplog.records if r.name == "app.workspace.data_manager.data"
    ]
    assert any("FR-DATAMGR-DATA-EDIT: Dataset 'ds:1' updated" in m for m in messages)


def test_data_edit_multiple_fields_and_kwargs() -> None:
    """Test editing multiple fields using both dictionary and kwargs."""
    _seed_dataset("ds:2")
    service = Data()

    updated = service.edit(
        "ds:2",
        {"category": "Crypto", "broker": "binance"},
        broker_name="Binance Futures",
        bars=50000,
        quality_score=0.95,
        path="/custom/path.parquet",
        schema_version=2,
    )

    assert updated["category"] == "Crypto"
    assert updated["broker"] == "binance"
    assert updated["broker_name"] == "Binance Futures"
    assert updated["bars"] == 50000
    assert updated["quality_score"] == 0.95
    assert updated["path"] == "/custom/path.parquet"
    assert updated["schema_version"] == 2


def test_data_edit_lineage_json_dict_and_str() -> None:
    """Test updating lineage_json as dictionary and as valid JSON string."""
    _seed_dataset("ds:3")
    service = Data()

    # Pass as mapping
    payload_dict = {"catalog": {"session_id": "sess_1"}}
    updated = service.edit("ds:3", {"lineage_json": payload_dict})
    assert json.loads(updated["lineage_json"]) == payload_dict

    # Pass as string
    payload_str = json.dumps({"custom": "metadata"})
    updated = service.edit("ds:3", {"lineage_json": payload_str})
    assert updated["lineage_json"] == payload_str


def test_data_edit_matching_id_omitted() -> None:
    """Test that passing id matching dataset_id is accepted and not mutated."""
    _seed_dataset("ds:4")
    service = Data()

    updated = service.edit("ds:4", {"id": "ds:4", "symbol": "GBPUSD"})
    assert updated["id"] == "ds:4"
    assert updated["symbol"] == "GBPUSD"


def test_data_edit_only_matching_id_raises() -> None:
    """Test that passing only matching id leaves clean updates empty and raises ValueError."""
    _seed_dataset("ds:only_id")
    service = Data()

    with pytest.raises(
        ValueError, match="No editable values provided in updates payload"
    ):
        service.edit("ds:only_id", {"id": "ds:only_id"})


def test_data_edit_mismatched_id_raises() -> None:
    """Test that attempting to mutate primary key id raises ValueError."""
    _seed_dataset("ds:5")
    service = Data()

    with pytest.raises(ValueError, match="primary key 'id' cannot be modified"):
        service.edit("ds:5", {"id": "ds:other"})


def test_data_edit_created_at_raises() -> None:
    """Test that attempting to mutate created_at raises ValueError."""
    _seed_dataset("ds:6")
    service = Data()

    with pytest.raises(ValueError, match="Field 'created_at' cannot be modified"):
        service.edit("ds:6", {"created_at": "2020-01-01"})


def test_data_edit_empty_updates_raises() -> None:
    """Test that empty updates dictionary or kwargs raises ValueError."""
    _seed_dataset("ds:7")
    service = Data()

    with pytest.raises(ValueError, match="Updates payload cannot be empty"):
        service.edit("ds:7", {})

    with pytest.raises(ValueError, match="Updates payload cannot be empty"):
        service.edit("ds:7")


def test_data_edit_invalid_dataset_id() -> None:
    """Test invalid dataset_id values raise TypeError or ValueError."""
    service = Data()

    with pytest.raises(ValueError, match="non-empty string"):
        service.edit("", {"symbol": "EURUSD"})

    with pytest.raises(ValueError, match="non-empty string"):
        service.edit("   ", {"symbol": "EURUSD"})

    with pytest.raises(TypeError, match="must be a string"):
        service.edit(123, {"symbol": "EURUSD"})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="control characters"):
        service.edit("ds\x001", {"symbol": "EURUSD"})


def test_data_edit_dataset_not_found(caplog: pytest.LogCaptureFixture) -> None:
    """Test non-existent dataset raises LookupError and logs WARNING."""
    service = Data()

    with (
        caplog.at_level(logging.WARNING),
        pytest.raises(LookupError, match="not found in catalog"),
    ):
        service.edit("ds:nonexistent", {"symbol": "EURUSD"})

    assert any(
        "FR-DATAMGR-DATA-EDIT: Edit request rejected" in r.message
        for r in caplog.records
    )


def test_data_edit_unknown_column() -> None:
    """Test unknown column name raises ValueError."""
    _seed_dataset("ds:8")
    service = Data()

    with pytest.raises(
        ValueError, match="Unknown or non-editable column: 'invalid_col'"
    ):
        service.edit("ds:8", {"invalid_col": "value"})


def test_data_edit_non_string_key() -> None:
    """Test non-string key raises TypeError."""
    _seed_dataset("ds:9")
    service = Data()

    with pytest.raises(TypeError, match="keys must be strings"):
        service.edit("ds:9", {123: "val"})  # type: ignore[dict-item]


def test_data_edit_bars_validation() -> None:
    """Test bars validation for non-negative integers."""
    _seed_dataset("ds:10")
    service = Data()

    with pytest.raises(ValueError, match="cannot be negative"):
        service.edit("ds:10", {"bars": -5})

    with pytest.raises(TypeError, match="must be a number"):
        service.edit("ds:10", {"bars": True})

    with pytest.raises(TypeError, match="must be a number"):
        service.edit("ds:10", {"bars": "not_an_int"})


def test_data_edit_quality_score_validation() -> None:
    """Test quality score validation between 0.0 and 1.0."""
    _seed_dataset("ds:11")
    service = Data()

    with pytest.raises(ValueError, match=r"between 0\.0 and 1\.0"):
        service.edit("ds:11", {"quality_score": 1.5})

    with pytest.raises(ValueError, match=r"between 0\.0 and 1\.0"):
        service.edit("ds:11", {"quality_score": -0.1})

    with pytest.raises(TypeError, match="must be a number"):
        service.edit("ds:11", {"quality_score": True})

    with pytest.raises(TypeError, match="must be a number"):
        service.edit("ds:11", {"quality_score": "bad"})


def test_data_edit_schema_version_validation() -> None:
    """Test schema_version validation."""
    _seed_dataset("ds:12")
    service = Data()

    with pytest.raises(TypeError, match="must be a number"):
        service.edit("ds:12", {"schema_version": True})

    with pytest.raises(TypeError, match="must be a number"):
        service.edit("ds:12", {"schema_version": "invalid"})


def test_data_edit_lineage_json_invalid_str() -> None:
    """Test invalid lineage_json string raises ValueError or TypeError."""
    _seed_dataset("ds:13")
    service = Data()

    with pytest.raises(ValueError, match="must be valid JSON"):
        service.edit("ds:13", {"lineage_json": "invalid-json{"})

    with pytest.raises(TypeError, match="must be JSON string or mapping"):
        service.edit("ds:13", {"lineage_json": 12345})


def test_data_edit_text_validation() -> None:
    """Test text validation for control characters, type, and length."""
    _seed_dataset("ds:14")
    service = Data()

    with pytest.raises(TypeError, match="must be a string"):
        service.edit("ds:14", {"symbol": 123})

    with pytest.raises(ValueError, match="exceeds length limit"):
        service.edit("ds:14", {"symbol": "A" * 501})

    with pytest.raises(ValueError, match="contains control characters"):
        service.edit("ds:14", {"symbol": "EUR\x01USD"})


def test_data_edit_persistence_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test persistence failure raises RuntimeError and logs ERROR."""
    _seed_dataset("ds:15")
    service = Data()

    def _fail_update(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Simulated DB write failure")

    monkeypatch.setattr(HostPersistence, "update_record", _fail_update)

    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(RuntimeError, match="Failed to update dataset"),
    ):
        service.edit("ds:15", {"symbol": "NEW"})

    assert any(
        "FR-DATAMGR-DATA-EDIT: Persistence failed" in r.message for r in caplog.records
    )


def test_data_edit_missing_after_update(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test missing record after update raises RuntimeError."""
    _seed_dataset("ds:16")
    service = Data()

    orig_read = HostPersistence.read_records
    calls = 0

    def _mock_read(
        table: str, filters: Any = None, **kwargs: Any
    ) -> list[dict[str, Any]]:
        nonlocal calls
        calls += 1
        if calls > 1:
            return []
        return orig_read(table, filters, **kwargs)

    monkeypatch.setattr(HostPersistence, "read_records", _mock_read)

    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(RuntimeError, match="could not be re-read"),
    ):
        service.edit("ds:16", {"symbol": "NEW"})

    assert any("Record missing after update" in r.message for r in caplog.records)


def test_data_cli_format_output() -> None:
    """Test DataCLI format_output output formatting."""
    record = {"id": "ds:1", "symbol": "EURUSD", "bars": 100}
    output = DataCLI.format_output(record)
    assert "bars: 100" in output
    assert "id: ds:1" in output
    assert "symbol: EURUSD" in output


def test_data_main_with_data(capsys: pytest.CaptureFixture[str]) -> None:
    """Test executing data.py main logic when datasets exist."""
    _seed_dataset("ds:main")
    service = Data()
    records = HostPersistence.read_records("datamgr_datasets", limit=1)
    if records:
        target_id = str(records[0]["id"])
        result = service.edit(target_id, {"broker_name": records[0]["broker_name"]})
        print(DataCLI.format_output(result))
    captured = capsys.readouterr()
    assert "id: ds:main" in captured.out


def test_data_main_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Test executing data.py main logic when table is empty."""
    records = HostPersistence.read_records("datamgr_datasets", limit=1)
    if not records:
        print("No datasets found in datamgr_datasets.")
    captured = capsys.readouterr()
    assert "No datasets found in datamgr_datasets." in captured.out


class _MockBroker:
    """Mock broker providing deterministic bars and ticks."""

    def __init__(
        self,
        bars_df: pd.DataFrame | None = None,
        ticks_df: pd.DataFrame | None = None,
    ) -> None:
        self.bars_df = bars_df if bars_df is not None else pd.DataFrame()
        self.ticks_df = ticks_df if ticks_df is not None else pd.DataFrame()

    def get_bars(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        return self.bars_df

    def get_ticks(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        return self.ticks_df


class _MockAsyncBroker(_MockBroker):
    """Mock broker returning awaitable responses."""

    async def get_bars(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        return self.bars_df


def test_data_add_success(caplog: pytest.LogCaptureFixture) -> None:
    """Test registering a new data symbol record into datamgr_datasets."""
    service = Data()
    with caplog.at_level(logging.INFO):
        record = service.add("dukascopy", "EURUSD", "M1")

    assert record["id"] == "dukascopy:EURUSD:M1"
    assert record["source"] == "dukascopy"
    assert record["symbol"] == "EURUSD"
    assert record["timeframe"] == "M1"
    assert record["path"] == "data/market/dukascopy/m1/eurusd"
    assert record["data_kind"] == "bars"
    assert any("FR-DATAMGR-DATA-ADD" in r.message for r in caplog.records)


def test_data_add_custom_id_and_fields() -> None:
    """Test registering a symbol with explicit ID and custom broker/underlying."""
    service = Data()
    record = service.add(
        "binance",
        "BTCUSDT",
        "TICKS",
        underlying="BTC",
        instrument="BTC_PERP",
        broker="crypto_binance",
        category="Crypto",
        dataset_id="crypto:btcusdt:tick",
    )
    assert record["id"] == "crypto:btcusdt:tick"
    assert record["underlying"] == "BTC"
    assert record["instrument"] == "BTC_PERP"
    assert record["data_kind"] == "ticks"
    assert record["category"] == "Crypto"


def test_data_add_duplicate_raises() -> None:
    """Test registering duplicate dataset ID raises ValueError."""
    service = Data()
    service.add("dukascopy", "EURUSD", "M1")
    with pytest.raises(ValueError, match="already exists"):
        service.add("dukascopy", "EURUSD", "M1")


def test_data_add_invalid_inputs() -> None:
    """Test validation guards on invalid inputs for Data.add()."""
    service = Data()
    with pytest.raises(TypeError, match="must be a string"):
        service.add(123, "EURUSD", "M1")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be a non-empty string"):
        service.add("dukascopy", "   ", "M1")

    with pytest.raises(ValueError, match="cannot contain control characters"):
        service.add("dukascopy", "EUR\x02USD", "M1")


def test_data_add_persistence_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test persistence errors during Data.add() raise RuntimeError."""
    service = Data()

    def _fail_create(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("DB simulated insert failure")

    monkeypatch.setattr(HostPersistence, "create_record", _fail_create)
    with pytest.raises(RuntimeError, match="Failed to add dataset"):
        service.add("dukascopy", "EURUSD", "M1")


def test_data_import_m1_bars_overwrite(tmp_path: Path) -> None:
    """Test importing M1 bars creates ZSTD Parquet partitions with integer tick units."""
    dt_index = pd.date_range("2024-12-31 23:58:00", periods=4, freq="1min", tz="UTC")
    bars_df = pd.DataFrame(
        {
            "Open": [1.08500, 1.08510, 1.08520, 1.08530],
            "High": [1.08550, 1.08560, 1.08570, 1.08580],
            "Low": [1.08490, 1.08500, 1.08510, 1.08520],
            "Close": [1.08510, 1.08520, 1.08530, 1.08540],
            "Volume": [100, 200, 300, 400],
        },
        index=dt_index,
    )
    mock = _MockBroker(bars_df=bars_df)
    market_dir = tmp_path / "market"

    service = Data()
    summary = service.import_data(
        "dukascopy",
        "EURUSD",
        "M1",
        mode="overwrite",
        tick_size=0.00001,
        broker_client=mock,
        base_dir=market_dir,
    )

    assert summary["rows_imported"] == 4
    assert summary["total_bars"] == 4
    assert len(summary["partitions"]) == 2  # 2024 and 2025

    p2024 = market_dir / "dukascopy" / "m1" / "eurusd" / "2024.parquet"
    p2025 = market_dir / "dukascopy" / "m1" / "eurusd" / "2025.parquet"
    assert p2024.exists()
    assert p2025.exists()

    pf = pq.ParquetFile(p2024)
    assert pf.schema_arrow.equals(M1_ARROW_SCHEMA)
    assert pf.metadata.row_group(0).column(0).compression == "ZSTD"

    table2024 = pq.read_table(p2024)
    assert table2024.num_rows == 2
    assert table2024["Open"][0].as_py() == 108500


def test_data_import_ticks_overwrite(tmp_path: Path) -> None:
    """Test importing ticks creates month-partitioned Parquet files with integer tick units."""
    dt_index = pd.date_range("2025-04-10 12:00:00", periods=3, freq="1s", tz="UTC")
    ticks_df = pd.DataFrame(
        {
            "Bid": [1.08521, 1.08523, 1.08525],
            "Ask": [1.08525, 1.08527, 1.08529],
            "Flags": [1, 2, 0],
        },
        index=dt_index,
    )
    mock = _MockBroker(ticks_df=ticks_df)
    market_dir = tmp_path / "market"

    service = Data()
    summary = service.import_data(
        "dukascopy",
        "EURUSD",
        "TICKS",
        mode="overwrite",
        tick_size=0.00001,
        broker_client=mock,
        base_dir=market_dir,
    )

    assert summary["rows_imported"] == 3
    assert summary["total_bars"] == 3

    p_tick = market_dir / "dukascopy" / "ticks" / "eurusd" / "2025" / "04-apr.parquet"
    assert p_tick.exists()

    pf = pq.ParquetFile(p_tick)
    assert pf.schema_arrow.equals(TICK_ARROW_SCHEMA)
    assert pf.metadata.row_group(0).column(0).compression == "ZSTD"

    table_tick = pq.read_table(p_tick)
    assert table_tick["Bid"][0].as_py() == 108521


def test_data_import_missing_mode(tmp_path: Path) -> None:
    """Test missing mode appends only new timestamps and leaves present data intact."""
    market_dir = tmp_path / "market"
    service = Data()

    # Batch 1: T1 and T2
    t1 = pd.date_range("2025-01-01 00:00:00", periods=2, freq="1min", tz="UTC")
    df1 = pd.DataFrame(
        {
            "Open": [1.0, 1.0],
            "High": [1.0, 1.0],
            "Low": [1.0, 1.0],
            "Close": [1.0, 1.0],
        },
        index=t1,
    )
    service.import_data(
        "dukascopy",
        "EURUSD",
        "M1",
        mode="overwrite",
        broker_client=_MockBroker(df1),
        base_dir=market_dir,
    )

    # Batch 2: T2 and T3 (T2 has different price, should be skipped in missing mode)
    t2 = pd.date_range("2025-01-01 00:01:00", periods=2, freq="1min", tz="UTC")
    df2 = pd.DataFrame(
        {
            "Open": [2.0, 2.0],
            "High": [2.0, 2.0],
            "Low": [2.0, 2.0],
            "Close": [2.0, 2.0],
        },
        index=t2,
    )
    summary2 = service.import_data(
        "dukascopy",
        "EURUSD",
        "M1",
        mode="missing",
        broker_client=_MockBroker(df2),
        base_dir=market_dir,
    )

    assert summary2["total_bars"] == 3
    p_file = market_dir / "dukascopy" / "m1" / "eurusd" / "2025.parquet"
    table = pq.read_table(p_file)
    assert table.num_rows == 3
    # Timestamp 1 was preserved from batch 1 (price 1.0 -> 100000 ticks)
    assert table["Open"][1].as_py() == 100000


def test_data_import_overwrite_updates_overlap(tmp_path: Path) -> None:
    """Test overwrite mode updates overlapping timestamps with new data."""
    market_dir = tmp_path / "market"
    service = Data()

    t1 = pd.date_range("2025-01-01 00:00:00", periods=2, freq="1min", tz="UTC")
    df1 = pd.DataFrame(
        {
            "Open": [1.0, 1.0],
            "High": [1.0, 1.0],
            "Low": [1.0, 1.0],
            "Close": [1.0, 1.0],
        },
        index=t1,
    )
    service.import_data(
        "dukascopy",
        "EURUSD",
        "M1",
        mode="overwrite",
        broker_client=_MockBroker(df1),
        base_dir=market_dir,
    )

    # Batch 2: Overwrite with price 2.0 for T2, plus T3
    t2 = pd.date_range("2025-01-01 00:01:00", periods=2, freq="1min", tz="UTC")
    df2 = pd.DataFrame(
        {
            "Open": [2.0, 2.0],
            "High": [2.0, 2.0],
            "Low": [2.0, 2.0],
            "Close": [2.0, 2.0],
        },
        index=t2,
    )
    service.import_data(
        "dukascopy",
        "EURUSD",
        "M1",
        mode="overwrite",
        broker_client=_MockBroker(df2),
        base_dir=market_dir,
    )

    p_file = market_dir / "dukascopy" / "m1" / "eurusd" / "2025.parquet"
    table = pq.read_table(p_file)
    assert table.num_rows == 3
    # Timestamp 1 was updated to price 2.0 -> 200000 ticks
    assert table["Open"][1].as_py() == 200000


def test_data_import_empty_dataframe(tmp_path: Path) -> None:
    """Test importing when broker returns empty DataFrame handles gracefully."""
    market_dir = tmp_path / "market"
    service = Data()
    mock = _MockBroker(bars_df=pd.DataFrame())

    summary = service.import_data(
        "dukascopy", "EURUSD", "M1", broker_client=mock, base_dir=market_dir
    )
    assert summary["rows_imported"] == 0
    assert summary["total_bars"] == 0


def test_data_import_invalid_mode() -> None:
    """Test unsupported import mode raises ValueError."""
    service = Data()
    with pytest.raises(ValueError, match="Unsupported import mode"):
        service.import_data("dukascopy", "EURUSD", "M1", mode="invalid_mode")


def test_data_import_async_broker(tmp_path: Path) -> None:
    """Test import_data with async broker get_bars."""
    market_dir = tmp_path / "market"
    t1 = pd.date_range("2025-01-01 00:00:00", periods=1, freq="1min", tz="UTC")
    df1 = pd.DataFrame(
        {"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [1.0]},
        index=t1,
    )
    mock = _MockAsyncBroker(bars_df=df1)
    service = Data()

    summary = service.import_data(
        "dukascopy", "EURUSD", "M1", broker_client=mock, base_dir=market_dir
    )
    assert summary["rows_imported"] == 1


def test_data_read_polars(tmp_path: Path) -> None:
    """Test read_polars returns lazy frame scanning parquet partitions."""
    market_dir = tmp_path / "market"
    service = Data()

    t1 = pd.date_range("2025-01-01 00:00:00", periods=2, freq="1min", tz="UTC")
    df1 = pd.DataFrame(
        {
            "Open": [1.0, 1.1],
            "High": [1.2, 1.3],
            "Low": [0.9, 1.0],
            "Close": [1.1, 1.2],
        },
        index=t1,
    )
    service.import_data(
        "dukascopy", "EURUSD", "M1", broker_client=_MockBroker(df1), base_dir=market_dir
    )

    lf = service.read_polars("dukascopy", "EURUSD", "M1", base_dir=market_dir)
    assert isinstance(lf, pl.LazyFrame)
    collected = lf.collect()
    assert collected.shape == (2, 6)

    with pytest.raises(FileNotFoundError, match="No parquet partitions found"):
        service.read_polars("dukascopy", "NONEXISTENT", "M1", base_dir=market_dir)


def test_data_query_duckdb(tmp_path: Path) -> None:
    """Test query_duckdb executes analytical SQL over partitioned Parquet files."""
    market_dir = tmp_path / "market"
    service = Data()

    t1 = pd.date_range("2025-01-01 00:00:00", periods=5, freq="1min", tz="UTC")
    df1 = pd.DataFrame(
        {"Open": [1.0] * 5, "High": [1.1] * 5, "Low": [0.9] * 5, "Close": [1.0] * 5},
        index=t1,
    )
    service.import_data(
        "dukascopy", "EURUSD", "M1", broker_client=_MockBroker(df1), base_dir=market_dir
    )

    p_file = market_dir / "dukascopy" / "m1" / "eurusd" / "2025.parquet"
    res = service.query_duckdb(
        f"SELECT count(*) as cnt FROM read_parquet('{p_file.as_posix()}')"
    )
    row = res.fetchone()
    assert row is not None
    assert row[0] == 5


def test_data_import_aliases() -> None:
    """Test Data.import_ and getattr(service, 'import') aliases match import_data."""
    service = Data()
    assert service.import_.__name__ == "import_data"
    assert getattr(service, "import").__name__ == "import_data"


def test_resolve_tick_size() -> None:
    """Test _resolve_tick_size hierarchy: explicit, DB instrument, JPY, and default."""
    assert _resolve_tick_size("EURUSD", 0.0001) == 0.0001
    assert _resolve_tick_size("USDJPY") == 0.001
    assert _resolve_tick_size("EURUSD") == 0.00001

    # Test DB instrument lookup
    HostPersistence.create_record(
        "datamgr_instruments",
        {
            "symbol": "CUSTOM_ASSET",
            "price": json.dumps({"tick_size": 0.25}),
            "created_at_utc": datetime.now(UTC).isoformat(),
            "updated_at_utc": datetime.now(UTC).isoformat(),
        },
    )
    assert _resolve_tick_size("CUSTOM_ASSET") == 0.25


def test_format_bars_to_arrow_missing_columns() -> None:
    """Test _format_bars_to_arrow raises ValueError if required price column is missing."""
    df = pd.DataFrame({"High": [1.0], "Low": [0.9], "Close": [1.0]})
    with pytest.raises(ValueError, match="Missing required price column 'open'"):
        _format_bars_to_arrow(df, 0.00001)


def test_format_ticks_to_arrow_missing_columns() -> None:
    """Test _format_ticks_to_arrow raises ValueError if required column is missing."""
    df = pd.DataFrame({"Ask": [1.0]})
    with pytest.raises(ValueError, match="Missing required price column 'bid'"):
        _format_ticks_to_arrow(df, 0.00001)
