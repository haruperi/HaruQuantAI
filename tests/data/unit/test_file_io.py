"""Unit tests for datasets local persistence.

[CAP-DATA-026 Phase 2] Copy of the legacy storage test, re-pointed at the
new `persistence`/`audit` modules. The legacy copy still guards `storage/`
until Phase 11 deletes it. Behaviour assertions are unchanged.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import DataError, DataQualityReport
from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.contracts import (
    DatasetSaveRequest,
)
from app.services.data.persistence.dataset_writer import load_dataset, save_dataset

from tests.data.helpers_models import AVAILABLE, make_dataset


def _configure_datasets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Helper to configure datasets environment variables."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10")

    # Create approved roots folders
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


def test_save_and_load_csv_dataset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that we can save and load a dataset in CSV format."""
    _configure_datasets(monkeypatch, tmp_path)

    dataset = make_dataset()
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        overwrite=True,
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    manifest = save_dataset(save_req)
    assert manifest.format == "csv"
    assert manifest.row_count == 1
    assert manifest.content_hash != ""

    load_req = DatasetLoadRequest(
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    loaded = load_dataset(load_req)
    assert loaded.symbol == "ABC"
    assert loaded.record_count == 1
    assert len(loaded.records) == 1
    assert loaded.records[0].open == Decimal("10.0")


def test_save_and_load_parquet_dataset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that we can save and load a dataset in Parquet format."""
    _configure_datasets(monkeypatch, tmp_path)

    dataset = make_dataset()
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/test.parquet"),
        format="parquet",
        overwrite=True,
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    manifest = save_dataset(save_req)
    assert manifest.format == "parquet"

    load_req = DatasetLoadRequest(
        relative_path=Path("data/raw/test.parquet"),
        format="parquet",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    loaded = load_dataset(load_req)
    assert loaded.symbol == "ABC"
    assert loaded.records[0].close == Decimal("10.5")


def test_save_overwrite_prevention(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that save_dataset respects overwrite flag."""
    raw_dir = _configure_datasets(monkeypatch, tmp_path)

    # Create dummy file to trigger existing check
    target = raw_dir / "test.csv"
    target.touch()

    dataset = make_dataset()
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        overwrite=False,
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    with pytest.raises(DataError) as captured:
        save_dataset(save_req)
    assert captured.value.code == "DB_WRITE_FAILED"


def test_save_quality_failed_dataset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that dataset quality validation failures are rejected."""
    _configure_datasets(monkeypatch, tmp_path)

    from app.services.data.contracts import QualityIssue

    issue = QualityIssue(
        code="BAD_DATA",
        severity="error",
        message="Mock quality failure",
    )
    failed_quality = DataQualityReport(
        quality_status="failed",
        quality_score=Decimal("0.5"),
        issues=(issue,),
        warnings=(),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=AVAILABLE,
    )

    dataset = make_dataset().model_copy(update={"quality_report": failed_quality})
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        overwrite=True,
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    with pytest.raises(DataError) as captured:
        save_dataset(save_req)
    assert captured.value.code == "DATA_QUALITY_FAILED"


def test_save_and_load_unapproved_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that saving or loading outside approved roots raises PERMISSION_DENIED."""
    _configure_datasets(monkeypatch, tmp_path)

    # Make unapproved directory
    other_dir = tmp_path / "other"
    other_dir.mkdir(exist_ok=True)

    dataset = make_dataset()
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("other/test.csv"),
        format="csv",
        overwrite=True,
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    with pytest.raises(DataError) as captured:
        save_dataset(save_req)
    assert captured.value.code == "PERMISSION_DENIED"

    load_req = DatasetLoadRequest(
        relative_path=Path("other/test.csv"),
        format="csv",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    with pytest.raises(DataError) as captured:
        load_dataset(load_req)
    assert captured.value.code == "PERMISSION_DENIED"


def test_load_corrupted_hash(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify that dataset load fails if content hash does not match manifest."""
    raw_dir = _configure_datasets(monkeypatch, tmp_path)

    dataset = make_dataset()
    save_req = DatasetSaveRequest(
        dataset=dataset,
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        overwrite=True,
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )
    save_dataset(save_req)

    # Modify file contents to corrupt hash
    target = raw_dir / "test.csv"
    with target.open("a") as f:
        f.write("\ncorrupted,row\n")

    load_req = DatasetLoadRequest(
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    with pytest.raises(DataError) as captured:
        load_dataset(load_req)
    assert captured.value.code == "FILE_CORRUPTED"
