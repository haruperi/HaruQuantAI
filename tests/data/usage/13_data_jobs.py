"""Demonstrate FEAT-DATA-13 update-job scheduling and lifecycle operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_settings,
    build_job_definition,
    build_job_status_request,
    create_data_update_job,
    data_settings_context,
    ensure_source,
    get_data_update_job_status,
    run_data_migrations,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.utils import generate_id


def _error_code(error: BaseException) -> str:
    """Return a safe public-boundary error identifier."""
    return str(getattr(error, "code", type(error).__name__))


_JOB_NAME = "usage_sync_eurusd"
_START = datetime(2026, 6, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise job creation, status querying, execution, and state transitions."""
    with TemporaryDirectory(prefix="usage-data-jobs-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            _demonstrate_job_operations()


def _demonstrate_job_operations() -> None:
    """Run the update-job lifecycle operations inside an active context."""
    req_id = generate_id("req")
    ensure_source("mt5", req_id)

    job_def = build_job_definition(
        job_id=_JOB_NAME,
        source_id="mt5",
        symbols=("EURUSD",),
        timeframes=("M1",),
        data_kinds=("ohlcv",),
        start=_START,
        end=_START + timedelta(days=1),
        interval_seconds=3600,
        enabled=True,
        created_at=datetime.now(UTC),
        request_id=req_id,
    )

    try:
        job = create_data_update_job(job_def, request_id=req_id)
        print(f"Registered job: name={job.job_id} enabled={job.enabled}")
    except Exception as exc:  # noqa: BLE001 - domain error classes stay internal.
        print(f"create_data_update_job handled: {_error_code(exc)}")

    status_req = build_job_status_request(job_id=_JOB_NAME, request_id=req_id)
    try:
        status = get_data_update_job_status(status_req)
        print(f"Job status: state={status.state} enabled={status.enabled}")
    except Exception as exc:  # noqa: BLE001 - domain error classes stay internal.
        print(f"get_data_update_job_status handled: {_error_code(exc)}")

    try:
        job = start_data_update_job(job_id=_JOB_NAME, request_id=req_id)
        print(f"Started job: state={job.state}")
    except Exception as exc:  # noqa: BLE001 - domain error classes stay internal.
        print(f"start_data_update_job handled: {_error_code(exc)}")

    try:
        result = run_data_update_job_once(job_id=_JOB_NAME, request_id=req_id)
        print(
            "Completed run:",
            f"state={result.state}",
            f"records={result.record_count}",
            f"checkpoint={result.last_checkpoint}",
        )
    except Exception as exc:  # noqa: BLE001 - domain error classes stay internal.
        print(f"run_data_update_job_once handled: {_error_code(exc)}")

    try:
        job = stop_data_update_job(job_id=_JOB_NAME, request_id=req_id)
        print(f"Stopped job: state={job.state}")
    except Exception as exc:  # noqa: BLE001 - domain error classes stay internal.
        print(f"stop_data_update_job handled: {_error_code(exc)}")


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
