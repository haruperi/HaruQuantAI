"""Unit tests for Data Manager Actions service, transforms, and exports."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import polars as pl
import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.action import Actions, ActionsCLI
from app.workspace.data_manager.data import Data


@pytest.fixture(autouse=True)
def test_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing initialized isolated SQLite database file path."""
    db_file = tmp_path / "test_datamgr_actions.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def _create_sample_parquet(parquet_path: Path, rows: list[dict[str, Any]]) -> None:
    """Helper to write sample rows to parquet file."""
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows)
    df.write_parquet(parquet_path, compression="zstd", compression_level=6)


def _seed_action_dataset(
    tmp_path: Path,
    dataset_id: str = "ds:dukascopy:EURUSD:M1",
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    **overrides: Any,
) -> tuple[dict[str, Any], Path]:
    """Helper to seed a valid dataset and corresponding Parquet file."""
    parquet_file = (
        tmp_path / "market" / "dukascopy" / timeframe / symbol / "data.parquet"
    )
    now_iso = datetime.now(UTC).isoformat()
    rows = [
        {
            "timestamp": "2024-01-08T10:00:00Z",  # Monday
            "open": 1.0850,
            "high": 1.0860,
            "low": 1.0845,
            "close": 1.0855,
            "volume": 120,
            "spread": 2,
        },
        {
            "timestamp": "2024-01-08T10:01:00Z",
            "open": 1.0855,
            "high": 1.0870,
            "low": 1.0850,
            "close": 1.0865,
            "volume": 150,
            "spread": 2,
        },
        {
            "timestamp": "2024-01-08T10:02:00Z",
            "open": 1.0865,
            "high": 1.0880,
            "low": 1.0860,
            "close": 1.0875,
            "volume": 200,
            "spread": 3,
        },
        {
            "timestamp": "2024-01-08T10:03:00Z",
            "open": 1.0875,
            "high": 1.0890,
            "low": 1.0870,
            "close": 1.0885,
            "volume": 180,
            "spread": 2,
        },
        {
            "timestamp": "2024-01-08T10:04:00Z",
            "open": 1.0885,
            "high": 1.0895,
            "low": 1.0880,
            "close": 1.0890,
            "volume": 160,
            "spread": 2,
        },
    ]
    _create_sample_parquet(parquet_file, rows)

    record = {
        "id": dataset_id,
        "source": "dukascopy",
        "symbol": symbol,
        "underlying": symbol,
        "instrument": symbol,
        "timeframe": timeframe,
        "broker": "default",
        "broker_name": "Default Broker",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2024-01-08",
        "date_to": "2024-01-08",
        "bars": len(rows),
        "created_at": now_iso,
        "updated_at": now_iso,
        "path": str(parquet_file),
        "data_kind": "bars",
        "quality_score": 100.0,
        "lineage_json": "{}",
        "schema_version": 1,
    }
    record.update(overrides)
    HostPersistence.create_record("datamgr_datasets", record)
    return record, parquet_file


def test_clone_to_timezone_success(tmp_path: Path) -> None:
    """Test cloning price data to a shifted timezone."""
    _seed_action_dataset(tmp_path, "ds:dukascopy:EURUSD:M1")
    service = Actions()

    result = service.clone_to_timezone(
        "ds:dukascopy:EURUSD:M1", "EET", shift_hours=2, new_symbol="EURUSD_EET"
    )

    assert result["symbol"] == "EURUSD_EET"
    assert result["shift_hours"] == 2
    assert result["bars"] == 5
    assert Path(result["path"]).exists()

    # Verify cloned dataset was persisted
    cloned_rec = HostPersistence.read_records(
        "datamgr_datasets", {"id": result["dataset_id"]}
    )
    assert len(cloned_rec) == 1
    assert cloned_rec[0]["source"] == "cloned"
    assert cloned_rec[0]["timezone"] == "EET"

    # Verify timestamps shifted by +2 hours
    cloned_df = pl.read_parquet(result["path"])
    first_ts = cloned_df["timestamp"][0]
    assert first_ts == "2024-01-08T12:00:00Z"


def test_clone_to_timezone_remove_weekends(tmp_path: Path) -> None:
    """Test timezone cloning filters weekend bars when requested."""
    rows = [
        {
            "timestamp": "2024-01-05T23:00:00Z",  # Friday 23:00 UTC -> Saturday 02:00 EET
            "open": 1.08,
            "high": 1.09,
            "low": 1.07,
            "close": 1.08,
            "volume": 10,
            "spread": 1,
        },
        {
            "timestamp": "2024-01-08T08:00:00Z",  # Monday 08:00 UTC -> Monday 11:00 EET
            "open": 1.08,
            "high": 1.09,
            "low": 1.07,
            "close": 1.08,
            "volume": 10,
            "spread": 1,
        },
    ]
    record, _ = _seed_action_dataset(tmp_path, "ds:test:weekend", symbol="TEST")
    _create_sample_parquet(Path(record["path"]), rows)

    service = Actions()
    res = service.clone_to_timezone(
        "ds:test:weekend", "EET", shift_hours=3, remove_weekends=True
    )
    assert res["bars"] == 1  # Weekend bar was filtered out


def test_clone_to_timezone_guards(tmp_path: Path) -> None:
    """Test cloning guards against cloning cloned data and invalid IDs."""
    service = Actions()
    with pytest.raises(ValueError, match="not found"):
        service.clone_to_timezone("ds:nonexistent", "EET")

    _seed_action_dataset(
        tmp_path,
        "ds:cloned:EURUSD:M1",
        source="cloned",
        data_kind="cloned",
    )
    with pytest.raises(ValueError, match="cannot clone it again"):
        service.clone_to_timezone("ds:cloned:EURUSD:M1", "CET")


def test_delete_multiple_datasets(tmp_path: Path) -> None:
    """Test deleting multiple datasets removes records and files."""
    _seed_action_dataset(tmp_path, "ds:del:1", symbol="SYM1")
    _seed_action_dataset(tmp_path, "ds:del:2", symbol="SYM2")

    service = Actions()
    res = service.delete(["ds:del:1", "ds:del:2"])
    assert res["deleted_count"] == 2
    assert "ds:del:1" in res["deleted_ids"]
    assert "ds:del:2" in res["deleted_ids"]

    # Verify both deleted from DB
    remaining = HostPersistence.read_records("datamgr_datasets")
    assert not any(r["id"] in ("ds:del:1", "ds:del:2") for r in remaining)


def test_export_to_csv_default(tmp_path: Path) -> None:
    """Test exporting price data to default CSV format."""
    _seed_action_dataset(tmp_path, "ds:csv:test")
    service = Actions()
    out_csv = tmp_path / "exports" / "test.csv"

    res = service.export_to_csv("ds:csv:test", out_csv)
    assert res["rows_exported"] == 5
    assert out_csv.exists()

    with out_csv.open("r", encoding="utf-8") as fp:
        reader = list(csv.reader(fp))
        assert reader[0] == ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]
        assert len(reader) == 6  # header + 5 rows
        assert reader[1][0] == "2024.01.08"
        assert reader[1][1] == "10:00:00"


def test_export_to_csv_custom_format_and_date_range(tmp_path: Path) -> None:
    """Test CSV export with custom delimiter, custom columns, and date filter."""
    _seed_action_dataset(tmp_path, "ds:csv:custom")
    service = Actions()
    out_csv = tmp_path / "exports" / "custom.csv"

    custom = {
        "delimiter": ";",
        "include_header": False,
        "columns": ["DateTime", "Close", "Volume"],
    }
    res = service.export_to_csv(
        "ds:csv:custom",
        out_csv,
        custom_format=custom,
        date_from="2024-01-08T10:02:00Z",
    )
    assert res["rows_exported"] == 3

    with out_csv.open("r", encoding="utf-8") as fp:
        lines = [line.strip() for line in fp if line.strip()]
        assert len(lines) == 3
        assert ";" in lines[0]


def test_new_format_persistence(tmp_path: Path) -> None:
    """Test registering and reusing a new CSV export format."""
    service = Actions()
    spec = {
        "name": "MyCustomFormat",
        "delimiter": "\t",
        "include_header": True,
        "columns": ["Date", "Time", "Close"],
    }
    created = service.new_format(spec)
    assert created["name"] == "MyCustomFormat"
    assert created["delimiter"] == "\t"

    _seed_action_dataset(tmp_path, "ds:format:test")
    out_file = tmp_path / "exports" / "format_test.tsv"
    res = service.export_to_csv(
        "ds:format:test", out_file, format_name="MyCustomFormat"
    )
    assert res["rows_exported"] == 5
    assert res["format"] == "MyCustomFormat"

    with out_file.open("r", encoding="utf-8") as fp:
        first_line = fp.readline().strip()
        assert first_line == "Date\tTime\tClose"


def test_export_to_mt4(tmp_path: Path) -> None:
    """Test exporting price data to MetaTrader 4 FXT and HST files."""
    _seed_action_dataset(tmp_path, "ds:mt4:test", symbol="EURUSD")
    service = Actions()
    out_dir = tmp_path / "mt4_out"

    res = service.export_to_mt4("ds:mt4:test", out_dir, period=1)
    assert res["symbol"] == "EURUSD"
    assert res["record_count"] == 5
    assert len(res["files"]) == 2

    hst_path = out_dir / "EURUSD1.hst"
    fxt_path = out_dir / "EURUSD1_0.fxt"
    assert hst_path.exists()
    assert fxt_path.exists()
    assert hst_path.stat().st_size > 0
    assert fxt_path.stat().st_size > 0


def test_export_to_mt5(tmp_path: Path) -> None:
    """Test exporting price data to MetaTrader 5 format."""
    _seed_action_dataset(tmp_path, "ds:mt5:test", symbol="GBPUSD", timeframe="M1")
    service = Actions()
    out_dir = tmp_path / "mt5_out"

    res = service.export_to_mt5("ds:mt5:test", out_dir)
    assert res["symbol"] == "GBPUSD"
    assert res["rows_exported"] == 5
    out_path = Path(res["output_path"])
    assert out_path.exists()

    with out_path.open("r", encoding="utf-8") as fp:
        lines = [line.strip() for line in fp if line.strip()]
        assert (
            lines[0]
            == "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"
        )
        assert len(lines) == 6


def test_review_statistics(tmp_path: Path) -> None:
    """Test data review summary statistics computation."""
    _seed_action_dataset(tmp_path, "ds:review:test")
    service = Actions()

    rev = service.review("ds:review:test")
    assert rev["dataset"]["id"] == "ds:review:test"
    stats = rev["statistics"]
    assert stats["total_records"] == 5
    assert stats["min_price"] == 1.0845
    assert stats["max_price"] == 1.0895
    assert stats["avg_volume"] > 0


def test_review_data_pagination(tmp_path: Path) -> None:
    """Test paginated raw bar inspection."""
    _seed_action_dataset(tmp_path, "ds:revdata:test")
    service = Actions()

    # Request slice with limit=2, offset=1
    page1 = service.review_data("ds:revdata:test", offset=1, limit=2)
    assert page1["total_records"] == 5
    assert page1["offset"] == 1
    assert page1["limit"] == 2
    assert len(page1["rows"]) == 2
    assert "timestamp" in page1["columns"]
    assert "close" in page1["columns"]


def test_quality_clean_data(tmp_path: Path) -> None:
    """Test quality audit on clean dataset yields 100% score and 0 errors."""
    _seed_action_dataset(tmp_path, "ds:qual:clean")
    service = Actions()

    q = service.quality("ds:qual:clean", max_gap_minutes=60)
    assert q["quality_score"] == 100.0
    assert q["total_errors"] == 0
    assert q["problems"]["total_errors"] == 0


def test_quality_anomalies_detected(tmp_path: Path) -> None:
    """Test quality audit flags gaps, weekend bars, envelope errors, and spikes."""
    rows = [
        {
            "timestamp": "2024-01-08T10:00:00Z",  # Clean base bar
            "open": 1.0800,
            "high": 1.0850,
            "low": 1.0750,
            "close": 1.0820,
            "volume": 100,
            "spread": 1,
        },
        {
            "timestamp": "2024-01-08T10:01:00Z",  # Envelope error: high < low
            "open": 1.0800,
            "high": 1.0700,
            "low": 1.0900,
            "close": 1.0800,
            "volume": 100,
            "spread": 1,
        },
        {
            "timestamp": "2024-01-08T12:00:00Z",  # Time gap: > 60 mins
            "open": 1.0820,
            "high": 1.0850,
            "low": 1.0800,
            "close": 1.0830,
            "volume": 100,
            "spread": 1,
        },
        {
            "timestamp": "2024-01-08T12:01:00Z",  # Price spike > 10%
            "open": 1.3000,
            "high": 1.3100,
            "low": 1.2900,
            "close": 1.3050,
            "volume": 100,
            "spread": 1,
        },
        {
            "timestamp": "2024-01-13T10:00:00Z",  # Weekend bar (Saturday)
            "open": 1.3050,
            "high": 1.3100,
            "low": 1.3000,
            "close": 1.3050,
            "volume": 50,
            "spread": 2,
        },
    ]
    record, _ = _seed_action_dataset(
        tmp_path, "ds:qual:anomalies", symbol="ANOM", bars=len(rows)
    )
    _create_sample_parquet(Path(record["path"]), rows)

    service = Actions()
    q = service.quality("ds:qual:anomalies", max_gap_minutes=60)
    assert q["quality_score"] < 100.0
    assert q["problems"]["envelope_errors"] >= 1
    assert q["problems"]["gaps"] >= 1
    assert q["problems"]["price_spikes"] >= 1
    assert q["problems"]["weekend_bars"] >= 1
    assert len(q["anomalies"]) >= 4


def test_update_and_update_all(tmp_path: Path) -> None:
    """Test selective and catalog-wide data update triggers."""
    _seed_action_dataset(tmp_path, "ds:up:1", symbol="SYM1")
    _seed_action_dataset(tmp_path, "ds:up:2", symbol="SYM2")

    mock_data = MagicMock(spec=Data)
    mock_data.import_data.return_value = {"status": "ok", "imported": 50}
    mock_data.list_datasets.return_value = [
        {"id": "ds:up:1", "source": "dukascopy"},
        {"id": "ds:up:2", "source": "dukascopy"},
    ]

    service = Actions(data_service=mock_data)
    up_res = service.update(["ds:up:1"])
    assert up_res["updated_count"] == 1
    assert mock_data.import_data.called

    all_res = service.update_all()
    assert all_res["total_datasets"] == 2
    assert all_res["updated_count"] == 2


def test_actions_cli_dispatch(tmp_path: Path) -> None:
    """Test ActionsCLI command line dispatcher."""
    _seed_action_dataset(tmp_path, "ds:cli:test")
    service = Actions()

    # Review dispatch
    rev = ActionsCLI.dispatch_action(["action=review", "symbol=ds:cli:test"], service)
    assert rev["dataset"]["id"] == "ds:cli:test"

    # Quality dispatch
    qual = ActionsCLI.dispatch_action(["action=quality", "symbol=ds:cli:test"], service)
    assert qual["quality_score"] == 100.0

    # Delete dispatch
    del_res = ActionsCLI.dispatch_action(
        ["action=delete", "symbol=ds:cli:test"], service
    )
    assert del_res["deleted_count"] == 1

    # Invalid action dispatch
    with pytest.raises(ValueError, match="Unsupported action command"):
        ActionsCLI.dispatch_action(["action=unknown"], service)
