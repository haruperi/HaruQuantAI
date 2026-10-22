"""Unit tests for Data Manager Data service and dataset editing operations."""

from __future__ import annotations

import json
import logging
import runpy
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.data import (
    Data,
    DataCLI,
    _Config,
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
    """Test executing data.py as main module when datasets exist."""
    _seed_dataset("ds:main")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("app.workspace.data_manager.data", run_name="__main__")
    captured = capsys.readouterr()
    assert "id: ds:main" in captured.out


def test_data_main_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Test executing data.py as main module when table is empty."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("app.workspace.data_manager.data", run_name="__main__")
    captured = capsys.readouterr()
    assert "No datasets found in datamgr_datasets." in captured.out
