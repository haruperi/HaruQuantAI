"""Component tests for datasets local persistence.

[CAP-DATA-026 Phase 2] Copy of the legacy storage test, re-pointed at the
new `persistence`/`audit` modules. The legacy copy still guards `storage/`
until Phase 11 deletes it. Behaviour assertions are unchanged.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data import (
    build_data_error,
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    is_data_error,
)
from app.services.data.contracts import DataQualityReport
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.contracts import (
    DatasetSaveRequest,
)
from app.services.data.persistence.dataset_writer import load_dataset, save_dataset

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=1)
AVAILABLE = END + timedelta(seconds=1)


def make_bar():
    """Return one exact canonical OHLCV record."""
    return build_ohlcv_record(
        timestamp=START,
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=AVAILABLE,
    )


def make_quality(count=1):
    """Return passing bounded quality evidence."""
    return build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=AVAILABLE,
    )


def make_dataset():
    """Return one immutable provider-neutral market dataset."""
    bar = make_bar()
    return build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="ABC",
        timeframe="1m",
        records=(bar,),
        start=START,
        end=START,
        available_at=AVAILABLE,
        record_count=1,
        quality_report=make_quality(),
        source_metadata={"source": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="miss",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.persistence.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


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


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("C:/absolute.csv"),
        Path("../outside.csv"),
        Path("data/.hidden/file.csv"),
    ],
)
def test_dataset_load_request_rejects_unsafe_paths(relative_path: Path) -> None:
    """Local dataset reads reject absolute, traversal, and hidden paths."""
    data_error_type = type(build_data_error("INVALID_INPUT"))
    with pytest.raises(data_error_type, match="INVALID_INPUT") as captured:
        DatasetLoadRequest(
            relative_path=relative_path,
            format="csv",
            request_id=(
                "req-7f9b5e94ae934b46a594ec63344e837fc560223617ace5053e982a3c74471d47"  # pragma: allowlist secret
            ),
        )
    assert is_data_error(captured.value)


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

    manifest = _unwrap(save_dataset(save_req))
    assert manifest.format == "csv"
    assert manifest.row_count == 1
    assert manifest.content_hash != ""

    load_req = DatasetLoadRequest(
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    loaded = _unwrap(load_dataset(load_req))
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

    manifest = _unwrap(save_dataset(save_req))
    assert manifest.format == "parquet"

    load_req = DatasetLoadRequest(
        relative_path=Path("data/raw/test.parquet"),
        format="parquet",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    loaded = _unwrap(load_dataset(load_req))
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

    response = save_dataset(save_req)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "DB_WRITE_FAILED"


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
        quality_status="critical",
        quality_decision="rejected",
        quality_score=Decimal("50.00"),
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

    response = save_dataset(save_req)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "DATA_QUALITY_FAILED"


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

    save_response = save_dataset(save_req)
    assert save_response.status == "error"
    assert save_response.error is not None
    assert save_response.error.code == "PERMISSION_DENIED"

    load_req = DatasetLoadRequest(
        relative_path=Path("other/test.csv"),
        format="csv",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    load_response = load_dataset(load_req)
    assert load_response.status == "error"
    assert load_response.error is not None
    assert load_response.error.code == "PERMISSION_DENIED"


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
    _unwrap(save_dataset(save_req))

    # Modify file contents to corrupt hash
    target = raw_dir / "test.csv"
    with target.open("a") as f:
        f.write("\ncorrupted,row\n")

    load_req = DatasetLoadRequest(
        relative_path=Path("data/raw/test.csv"),
        format="csv",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )

    response = load_dataset(load_req)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "FILE_CORRUPTED"
