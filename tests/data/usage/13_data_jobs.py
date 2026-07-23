"""Demonstrate FEAT-DATA-13 data update job definitions, scheduling, and lifecycle operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataError
from app.services.data.data_jobs.contracts import JobDefinition, JobStatusRequest
from app.services.data.data_jobs.job import (
    create_data_update_job,
    get_data_update_job_status,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.utils import generate_id

_JOB_NAME = "usage_sync_eurusd"
_START = datetime(2026, 6, 1, tzinfo=UTC)


def example_29_scheduler_create_status() -> None:
    """Create and inspect a scheduler job status via create_data_update_job and get_data_update_job_status."""
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
    """Start and stop a scheduler job via start_data_update_job, stop_data_update_job, run_data_update_job_once."""
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


def main() -> None:
    """Run all data update job scheduler examples."""
    example_29_scheduler_create_status()
    example_30_scheduler_start_stop()


if __name__ == "__main__":
    main()
