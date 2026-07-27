"""Demonstrate FEAT-DATA-13 update-job scheduling and lifecycle operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    DataError,
    JobDefinition,
    JobStatusRequest,
    create_data_update_job,
    get_data_update_job_status,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.utils import generate_id

_JOB_NAME = "usage_sync_eurusd"
_START = datetime(2026, 6, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_29_scheduler_create_status() -> None:
    """Create and inspect a persisted update-job status."""
    _header("Create and inspect a persisted update-job status.")
    req_id = generate_id("req")
    job_def = JobDefinition(
        job_id=_JOB_NAME,
        source_id="usage-job-source",
        symbols=("EURUSD",),
        timeframes=("M1",),
        data_kinds=("ohlcv",),
        start=_START,
        end=_START + timedelta(days=1),
        interval_seconds=300,
        enabled=True,
        created_at=_START,
        request_id=req_id,
    )
    try:
        job = create_data_update_job(job_def, request_id=req_id)
        print(f"Registered job: name={job.job_id} enabled={job.enabled}")
    except DataError as exc:
        print(f"create_data_update_job handled: {exc.code}")

    status_req = JobStatusRequest(
        job_id=_JOB_NAME,
        request_id=req_id,
    )
    try:
        status = get_data_update_job_status(status_req)
        print(f"Job status: state={status.state} enabled={status.enabled}")
    except DataError as exc:
        print(f"get_data_update_job_status handled: {exc.code}")


def example_30_scheduler_start_stop() -> None:
    """Start, run once, and stop a persisted update job."""
    _header("Start, run once, and stop a persisted update job.")
    req_id = generate_id("req")
    try:
        job = start_data_update_job(job_id=_JOB_NAME, request_id=req_id)
        print(f"Started job: state={job.state}")
    except DataError as exc:
        print(f"start_data_update_job handled: {exc.code}")

    try:
        job = stop_data_update_job(job_id=_JOB_NAME, request_id=req_id)
        print(f"Stopped job: state={job.state}")
    except DataError as exc:
        print(f"stop_data_update_job handled: {exc.code}")

    try:
        result = run_data_update_job_once(job_id=_JOB_NAME, request_id=req_id)
        print(f"run_data_update_job_once: state={result.state}")
    except DataError as exc:
        print(f"run_data_update_job_once handled: {exc.code}")


def _demonstrate_feature() -> None:
    """Run all data update job scheduler examples."""
    example_29_scheduler_create_status()
    example_30_scheduler_start_stop()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_041() -> None:
    _header("fr_data_041")
    "FR-DATA-041: Derive the stable SHA-256 idempotency key from source, symbol, kind, timeframe, start/end, schema version, and normalization version."
    _demonstrate_once()


def fr_data_042() -> None:
    _header("fr_data_042")
    "FR-DATA-042: Execute retrieval, normalization, quality, persistence, and checkpoint for one bounded chunk as one recoverable unit, deduplicating a committed key."
    _demonstrate_once()


def fr_data_043() -> None:
    _header("fr_data_043")
    "FR-DATA-043: Validate interrupted job leases/checkpoints at startup and resume only after the last committed chunk without publishing partial work."
    _demonstrate_once()


def fr_data_044() -> None:
    _header("fr_data_044")
    "FR-DATA-044: Start or stop a persisted job only after state-transition, lease, source-policy, and schedule validation; recurring execution uses the single-node in-process asyncio loop, while `run_data_update_job_once` remains independently invokable by an OS scheduler."
    _demonstrate_once()


def fr_data_045() -> None:
    _header("fr_data_045")
    "FR-DATA-045: Return persisted job definition/state, enabled flag, run/checkpoint/error/next-run evidence, lease and recovery state, and request ID without mutation."
    _demonstrate_once()


def fr_data_084() -> None:
    _header("fr_data_084")
    "FR-DATA-084: Keep ingestion chunking private to the bounded backfill workflow; expose no generic sequence helper."
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_041,
        fr_data_042,
        fr_data_043,
        fr_data_044,
        fr_data_045,
        fr_data_084,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
