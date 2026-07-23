"""Behavioral coverage for persisted DATA scheduler lifecycle operations."""

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.services.data.contracts import DataError
from app.services.data.data_jobs import job
from app.services.data.data_jobs.contracts import (
    BackfillChunkRequest,
    BackfillChunkResult,
    JobDefinition,
    JobRunResult,
    JobStatus,
    JobStatusRequest,
    ScheduleJobRequest,
)
from app.utils import generate_id

_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


class _SequenceClock:
    """Return deterministic increasing UTC instants."""

    def __init__(self) -> None:
        """Initialize the bounded call counter."""
        self._calls = 0

    def now(self) -> datetime:
        """Return the next deterministic instant."""
        self._calls += 1
        return _NOW + timedelta(seconds=self._calls)


def _definition(**updates: object) -> JobDefinition:
    """Return one bounded disabled job definition."""
    values: dict[str, object] = {
        "job_id": "job-fixture",
        "source_id": "source-fixture",
        "symbols": ("EURUSD",),
        "timeframes": ("M1",),
        "data_kinds": ("ohlcv",),
        "start": _NOW,
        "end": _NOW + timedelta(hours=1),
        "interval_seconds": 60,
        "enabled": False,
        "created_at": _NOW,
        "request_id": generate_id("req"),
    }
    values.update(updates)
    return JobDefinition(**values)  # type: ignore[arg-type]


def _request(
    action: str,
    definition: JobDefinition | None = None,
) -> ScheduleJobRequest:
    """Return one scheduler action request."""
    return ScheduleJobRequest(
        action=action,  # type: ignore[arg-type]
        job_id=definition.job_id if definition else "job-fixture",
        definition=definition,
        request_id=generate_id("req"),
    )


def _row(**updates: object) -> dict[str, object]:
    """Return one persisted scheduler row."""
    values: dict[str, object] = {
        "job_id": "job-fixture",
        "source_id": "source-fixture",
        "symbols_json": json.dumps(["EURUSD"]),
        "timeframes_json": json.dumps(["M1"]),
        "data_kinds_json": json.dumps(["ohlcv"]),
        "start": _NOW.isoformat(),
        "end": (_NOW + timedelta(hours=1)).isoformat(),
        "interval_seconds": 60,
        "enabled": 1,
        "state": "created",
        "lease_owner": None,
        "lease_expires_at": None,
    }
    values.update(updates)
    return values


def test_lease_state_and_job_contract_invariants() -> None:
    """Classify leases and reject contradictory scheduler contracts."""
    assert job._get_active_lease_state(None, _NOW) == "none"
    held = (_NOW + timedelta(seconds=1)).isoformat()
    expired = (_NOW - timedelta(seconds=1)).isoformat()
    assert job._get_active_lease_state(held, _NOW) == "held"
    assert job._get_active_lease_state(expired, _NOW) == "expired"

    with pytest.raises(DataError):
        _definition(end=_NOW)
    with pytest.raises(DataError):
        _definition(interval_seconds=0)
    with pytest.raises(DataError):
        _definition(end=None, interval_seconds=None)
    with pytest.raises(DataError):
        ScheduleJobRequest(
            action="create",
            job_id="job-fixture",
            request_id=generate_id("req"),
        )


def test_create_start_stop_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Persist valid lifecycle changes and invoke bounded loop controls."""
    results = iter(
        (
            SimpleNamespace(rows=()),
            SimpleNamespace(rows=()),
            SimpleNamespace(rows=(_row(),)),
            SimpleNamespace(rows=()),
            SimpleNamespace(rows=({"job_id": "job-fixture"},)),
            SimpleNamespace(rows=()),
        )
    )
    monkeypatch.setattr(job, "execute_transaction", lambda _request: next(results))
    monkeypatch.setattr(job, "evaluate_source_policy", lambda _request: None)
    started: list[tuple[str, int]] = []
    stopped: list[str] = []
    monkeypatch.setattr(
        job,
        "_start_background_loop",
        lambda job_id, interval: started.append((job_id, interval)),
    )
    monkeypatch.setattr(job, "_stop_background_loop", stopped.append)

    definition = _definition()
    job._handle_create(_request("create", definition))
    job._handle_start(_request("start"), _SequenceClock())
    job._handle_stop(_request("stop"))

    assert started == [("job-fixture", 60)]
    assert stopped == ["job-fixture"]


def test_handlers_reject_missing_duplicate_and_held_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail closed for absent, duplicate, and concurrently leased jobs."""
    definition = _definition()
    monkeypatch.setattr(job, "evaluate_source_policy", lambda _request: None)
    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(rows=({"job_id": definition.job_id},)),
    )
    with pytest.raises(DataError):
        job._handle_create(_request("create", definition))

    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(rows=()),
    )
    with pytest.raises(DataError):
        job._handle_start(_request("start"), _SequenceClock())
    with pytest.raises(DataError):
        job._handle_stop(_request("stop"))

    held = _row(
        state="running",
        lease_expires_at=(_NOW + timedelta(hours=1)).isoformat(),
    )
    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(rows=(held,)),
    )
    with pytest.raises(DataError):
        job._handle_start(_request("start"), _SequenceClock())


def test_read_status_maps_persisted_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Map one durable scheduler row into immutable status evidence."""
    row = {
        "job_id": "job-fixture",
        "state": "stopped",
        "enabled": 0,
        "last_run_status": "succeeded",
        "last_checkpoint": "checkpoint.parquet",
        "last_error": None,
        "next_run_at": (_NOW + timedelta(hours=1)).isoformat(),
        "lease_owner": None,
        "lease_expires_at": None,
        "recovery_state": "clean",
    }
    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(rows=(row,)),
    )
    result = job.read_update_job_status(
        JobStatusRequest(job_id="job-fixture", request_id=generate_id("req")),
        clock=_SequenceClock(),
    )
    assert result.last_checkpoint == "checkpoint.parquet"

    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(rows=()),
    )
    with pytest.raises(DataError):
        job.read_update_job_status(
            JobStatusRequest(job_id="missing", request_id=generate_id("req"))
        )


def test_run_range_and_chunk_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resume after committed evidence and execute the Cartesian chunk plan."""
    checkpoint_end = _NOW + timedelta(minutes=10)
    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(
            rows=({"max_end": checkpoint_end.isoformat()},)
        ),
    )
    start, end = job._determine_run_range(
        _row(),
        "job-fixture",
        generate_id("req"),
        _NOW + timedelta(hours=2),
    )
    assert start == checkpoint_end
    assert end == _NOW + timedelta(hours=1)

    def _execute(
        request: BackfillChunkRequest,
        *,
        clock: object = None,
    ) -> BackfillChunkResult:
        chunk = request
        return BackfillChunkResult(
            job_id=chunk.job_id,
            chunk_id="chunk-1",
            idempotency_key="key-1",
            committed_start=chunk.start,
            committed_end=chunk.end,
            record_count=2,
            content_hash="hash",
            checkpoint="checkpoint.parquet",
            committed=True,
            request_id=chunk.request_id,
        )

    monkeypatch.setattr(job, "execute_backfill_chunk", _execute)
    chunks, records, checkpoint = job._execute_run_chunks(
        _row(),
        _NOW,
        _NOW + timedelta(hours=1),
        generate_id("req"),
        None,
    )
    assert chunks == 1
    assert records == 2
    assert checkpoint == "checkpoint.parquet"


def test_run_once_success_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Report success only for committed work and normalize safe failures."""
    row = _row()
    monkeypatch.setattr(job, "_acquire_job_run_lease", lambda *_args: row)
    monkeypatch.setattr(
        job,
        "_determine_run_range",
        lambda *_args: (_NOW, _NOW + timedelta(minutes=1)),
    )
    monkeypatch.setattr(
        job,
        "_execute_run_chunks",
        lambda *_args: (1, 2, "checkpoint.parquet"),
    )
    monkeypatch.setattr(
        job,
        "execute_transaction",
        lambda _request: SimpleNamespace(rows=()),
    )
    success = job.run_data_update_job_once(
        "job-fixture",
        generate_id("req"),
        clock=_SequenceClock(),
    )
    assert success.state == "succeeded"

    def _fail(*args: object) -> dict[str, object]:
        raise DataError("JOB_NOT_FOUND")

    monkeypatch.setattr(job, "_acquire_job_run_lease", _fail)
    failure = job.run_data_update_job_once(
        "job-fixture",
        generate_id("req"),
        clock=_SequenceClock(),
    )
    assert failure.state == "failed"
    assert failure.error_code == "JOB_NOT_FOUND"


def test_job_result_and_status_validation() -> None:
    """Reject status claims that lack their required durable evidence."""
    request_id = generate_id("req")
    with pytest.raises(DataError):
        JobRunResult(
            job_id="job-fixture",
            run_id="run-fixture",
            state="succeeded",
            started_at=_NOW,
            finished_at=_NOW + timedelta(seconds=1),
            committed_chunks=0,
            record_count=0,
            request_id=request_id,
        )
    with pytest.raises(DataError):
        JobStatus(
            job_id="job-fixture",
            state="running",
            enabled=True,
            lease_state="none",
            recovery_state="clean",
            request_id=request_id,
        )
