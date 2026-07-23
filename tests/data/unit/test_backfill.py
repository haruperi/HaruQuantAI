"""Behavioral coverage for recoverably atomic DATA backfill operations."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.services.data.contracts import DataError
from app.services.data.data_jobs import backfill, recovery
from app.services.data.data_jobs.contracts import (
    BackfillChunkRequest,
    BackfillChunkResult,
)
from app.utils import generate_id

from tests.data.helpers_models import make_dataset

_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _request(**updates: object) -> BackfillChunkRequest:
    """Return one bounded backfill chunk request."""
    values: dict[str, object] = {
        "job_id": "job-fixture",
        "source_id": "source-fixture",
        "symbol": "EURUSD",
        "data_kind": "ohlcv",
        "timeframe": "M1",
        "start": _NOW,
        "end": _NOW + timedelta(hours=1),
        "schema_version": "v1",
        "normalization_version": "v1",
        "max_records": 100,
        "request_id": generate_id("req"),
    }
    values.update(updates)
    return BackfillChunkRequest(**values)  # type: ignore[arg-type]


def _result(request: BackfillChunkRequest) -> BackfillChunkResult:
    """Return committed result evidence for a request."""
    return BackfillChunkResult(
        job_id=request.job_id,
        chunk_id="chunk-fixture",
        idempotency_key=backfill.derive_backfill_key(request),
        committed_start=request.start,
        committed_end=request.end,
        record_count=2,
        content_hash="hash-fixture",
        checkpoint="data/raw/backfill/checkpoint.parquet",
        committed=True,
        request_id=request.request_id,
    )


def test_key_limits_and_result_mapping() -> None:
    """Derive stable keys, enforce bounds, and reconstruct committed evidence."""
    request = _request()
    key = backfill.derive_backfill_key(request)
    assert key == backfill.derive_backfill_key(request)
    backfill._check_limits(request)
    with pytest.raises(DataError):
        backfill._check_limits(
            _request(max_records=backfill.BACKFILL_MAX_RECORDS_PER_CHUNK + 1)
        )
    with pytest.raises(DataError):
        backfill._check_limits(_request(end=_NOW + timedelta(days=2)))

    row = {
        "job_id": request.job_id,
        "chunk_id": "chunk-fixture",
        "idempotency_key": "key-fixture",
        "committed_start": request.start.isoformat(),
        "committed_end": request.end.isoformat(),
        "record_count": 2,
        "content_hash": "hash-fixture",
        "artifact_final": "checkpoint.parquet",
    }
    assert backfill._result_from_row(request, row).record_count == 2


def test_committed_lookup_and_lease_outcomes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return idempotent commits and distinguish lease contention from absence."""
    request = _request()
    result = _result(request)
    row = {
        "job_id": result.job_id,
        "chunk_id": result.chunk_id,
        "idempotency_key": result.idempotency_key,
        "committed_start": result.committed_start.isoformat(),
        "committed_end": result.committed_end.isoformat(),
        "record_count": result.record_count,
        "content_hash": result.content_hash,
        "artifact_final": result.checkpoint,
    }
    monkeypatch.setattr(
        backfill,
        "execute_transaction",
        lambda _transaction: SimpleNamespace(rows=(row,)),
    )
    assert backfill._committed_result(request, result.idempotency_key)

    monkeypatch.setattr(
        backfill,
        "execute_transaction",
        lambda _transaction: SimpleNamespace(rows=(), affected_rows=1),
    )
    backfill._acquire_lease(request, _NOW)

    responses = iter(
        (
            SimpleNamespace(rows=(), affected_rows=0),
            SimpleNamespace(rows=({"job_id": request.job_id},), affected_rows=0),
        )
    )
    monkeypatch.setattr(
        backfill,
        "execute_transaction",
        lambda _transaction: next(responses),
    )
    with pytest.raises(DataError) as exc_info:
        backfill._acquire_lease(request, _NOW)
    assert exc_info.value.code == "CONCURRENT_WRITE_LOCKED"


def test_fetch_and_configured_storage_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Map source kinds and require an explicit existing DATA storage root."""
    request = _request()
    dataset = make_dataset().model_copy(update={"request_id": request.request_id})
    monkeypatch.setattr(backfill, "fetch_market_dataset", lambda _request: dataset)
    assert backfill._fetch_backfill_data(request) is dataset

    persisted: list[object] = []
    monkeypatch.setattr(
        backfill,
        "execute_transaction",
        persisted.append,
    )

    def _fail(_request: object) -> object:
        raise DataError("SOURCE_UNAVAILABLE")

    monkeypatch.setattr(backfill, "fetch_market_dataset", _fail)
    with pytest.raises(DataError):
        backfill._fetch_backfill_data(request)
    assert persisted

    monkeypatch.setattr(
        backfill,
        "get_data_settings",
        lambda: SimpleNamespace(data_dir=tmp_path),
    )
    assert backfill._configured_data_dir(request.request_id) == tmp_path.resolve()
    missing = tmp_path / "missing"
    monkeypatch.setattr(
        backfill,
        "get_data_settings",
        lambda: SimpleNamespace(data_dir=missing),
    )
    with pytest.raises(DataError):
        backfill._configured_data_dir(request.request_id)


def test_publication_and_finalize_reject_incomplete_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Reject missing publication files and uncommitted checkpoint writes."""
    request = _request()
    monkeypatch.setattr(backfill, "_configured_data_dir", lambda _request_id: tmp_path)
    with pytest.raises(DataError) as exc_info:
        backfill._publish_artifact(
            request.request_id,
            "data/raw/pending.parquet",
            "data/raw/final.parquet",
            "hash-fixture",
        )
    assert exc_info.value.code == "CHECKPOINT_CORRUPTED"

    monkeypatch.setattr(
        backfill,
        "execute_transaction",
        lambda _transaction: SimpleNamespace(committed=False),
    )
    with pytest.raises(DataError):
        backfill._finalize_checkpoint(
            request.request_id,
            request.job_id,
            "key-fixture",
            "final.parquet",
        )


def test_execute_returns_existing_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return durable idempotency evidence without repeating side effects."""
    request = _request()
    existing = _result(request)
    monkeypatch.setattr(backfill, "_committed_result", lambda *_args: existing)
    assert backfill.execute_backfill_chunk(request) is existing


def test_artifact_paths_hash_and_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Resolve approved paths, hash payloads, and publish data/manifest atomically."""
    request = _request()
    monkeypatch.setattr(backfill, "_configured_data_dir", lambda _request_id: tmp_path)
    pending_relative, final_relative, pending, final = backfill._artifact_paths(
        request,
        "key-fixture",
    )
    pending.write_bytes(b"payload")
    pending_manifest = pending.with_suffix(pending.suffix + ".manifest.json")
    pending_manifest.write_text("{}", encoding="utf-8")
    content_hash = backfill._file_hash(pending)
    backfill._publish_artifact(
        request.request_id,
        str(pending_relative),
        str(final_relative),
        content_hash,
    )
    assert final.read_bytes() == b"payload"
    assert final.with_suffix(final.suffix + ".manifest.json").is_file()

    backfill._publish_artifact(
        request.request_id,
        str(pending_relative),
        str(final_relative),
        content_hash,
    )
    final.write_bytes(b"corrupt")
    with pytest.raises(DataError):
        backfill._publish_artifact(
            request.request_id,
            str(pending_relative),
            str(final_relative),
            content_hash,
        )


def test_prepare_finalize_and_execute_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare, finalize, and compose one complete backfill protocol."""
    request = _request()
    dataset = make_dataset().model_copy(update={"request_id": request.request_id})
    monkeypatch.setattr(
        backfill,
        "_artifact_paths",
        lambda _request, _key: (
            Path("pending.parquet"),
            Path("final.parquet"),
            Path("pending.parquet"),
            Path("final.parquet"),
        ),
    )
    monkeypatch.setattr(
        backfill,
        "save_dataset",
        lambda _request: SimpleNamespace(content_hash="hash-fixture"),
    )
    monkeypatch.setattr(
        backfill,
        "execute_transaction",
        lambda _transaction: SimpleNamespace(committed=True),
    )
    prepared = backfill._prepare_artifact(
        request,
        dataset,
        "key-fixture",
        _NOW,
    )
    assert prepared[0] == "chunk-key-fixture"
    backfill._finalize_checkpoint(
        request.request_id,
        request.job_id,
        "key-fixture",
        "final.parquet",
    )

    monkeypatch.setattr(backfill, "_committed_result", lambda *_args: None)
    monkeypatch.setattr(backfill, "_acquire_lease", lambda *_args: None)
    monkeypatch.setattr(backfill, "_fetch_backfill_data", lambda _request: dataset)
    monkeypatch.setattr(
        backfill,
        "_prepare_artifact",
        lambda *_args: (
            "chunk-key-fixture",
            "hash-fixture",
            "pending.parquet",
            "final.parquet",
        ),
    )
    monkeypatch.setattr(backfill, "_publish_artifact", lambda *_args: None)
    monkeypatch.setattr(backfill, "_finalize_checkpoint", lambda *_args: None)
    result = backfill.execute_backfill_chunk(request)
    assert result.committed


def test_recovery_classifies_recovered_and_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Classify each prepared publication from explicit recovery evidence."""
    rows = (
        {
            "idempotency_key": "good",
            "job_id": "job-good",
            "content_hash": "hash",
            "artifact_temp": "pending-good",
            "artifact_final": "final-good",
        },
        {
            "idempotency_key": "bad",
            "job_id": "job-bad",
            "content_hash": "hash",
            "artifact_temp": "pending-bad",
            "artifact_final": "final-bad",
        },
    )
    monkeypatch.setattr(
        recovery,
        "execute_transaction",
        lambda _transaction: SimpleNamespace(rows=rows),
    )

    def _publish(
        request_id: str,
        pending: str,
        final: str,
        content_hash: str,
    ) -> None:
        del request_id, final, content_hash
        if pending == "pending-bad":
            raise DataError("CHECKPOINT_CORRUPTED")

    monkeypatch.setattr(recovery, "_publish_artifact", _publish)
    monkeypatch.setattr(recovery, "_finalize_checkpoint", lambda *_args: None)
    report = recovery.recover_update_jobs(
        request_id=generate_id("req"),
        clock=SimpleNamespace(now=lambda: _NOW),
    )
    assert report.recovered_job_ids == ("job-good",)
    assert report.blocked_job_ids == ("job-bad",)
