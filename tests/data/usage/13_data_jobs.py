"""Demonstrate FEAT-DATA-13 update-job scheduling and lifecycle operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_job_definition,
    build_job_status_request,
    create_data_update_job,
    get_data_update_job_status,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.contracts.errors import DataError
from app.utils import generate_id

_JOB_NAME = "usage_sync_eurusd"
_START = datetime(2026, 6, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise job creation, status querying, execution, and state transitions."""
    req_id = generate_id("req")

    job_def = build_job_definition(
        job_id=_JOB_NAME,
        source_id="mt5",
        symbols=("EURUSD",),
        timeframes=("M1",),
        data_kinds=("bars",),
        start=_START,
        end=_START + timedelta(days=1),
        interval_seconds=3600,
        enabled=True,
        request_id=req_id,
    )

    try:
        job = create_data_update_job(job_def, request_id=req_id)
        print(f"Registered job: name={job.job_id} enabled={job.enabled}")
    except DataError as exc:
        print(f"create_data_update_job handled: {exc.code}")

    status_req = build_job_status_request(job_id=_JOB_NAME, request_id=req_id)
    try:
        status = get_data_update_job_status(status_req)
        print(f"Job status: state={status.state} enabled={status.enabled}")
    except DataError as exc:
        print(f"get_data_update_job_status handled: {exc.code}")

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


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_041() -> None:
    _header("fr_data_041")
    _demonstrate_once()


def fr_data_042() -> None:
    _header("fr_data_042")
    _demonstrate_once()


def fr_data_043() -> None:
    _header("fr_data_043")
    _demonstrate_once()


def fr_data_044() -> None:
    _header("fr_data_044")
    _demonstrate_once()


def fr_data_045() -> None:
    _header("fr_data_045")
    _demonstrate_once()


def fr_data_084() -> None:
    _header("fr_data_084")
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
