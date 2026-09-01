# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-13 update-job scheduling and lifecycle operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
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

_JOB_NAME = "usage_sync_eurusd"
_CALENDAR_JOB_NAME = "usage_sync_economic_calendar"
_START = datetime(2026, 6, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_data_041() -> None:
    """FR-DATA-041: Stage 1 — Register job definition with source, symbol, timeframe, interval, and enabled status."""
    _header("Stage 1: Job Registration & Definition - Job Definition (FR-DATA-041)")
    req_id = generate_id("req")
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
    print(_format_result(job_def))
    try:
        job = create_data_update_job(job_def, request_id=req_id)
        print(_format_result(job))
        print(f"Data -> JobStatus(job_id={job.job_id}, state={job.state})")
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        print(f"Data -> DataError({code})")


def fr_data_042_043() -> None:
    """FR-DATA-042, FR-DATA-043: Stage 2 — Start and stop data update jobs deterministically."""
    _header(
        "Stage 2: Job Lifecycle Control - Start & Stop Job (FR-DATA-042, FR-DATA-043)"
    )
    req_id = generate_id("req")
    try:
        job_st = start_data_update_job(job_id=_JOB_NAME, request_id=req_id)
        print(_format_result(job_st))
        print(f"Data -> JobStatus(job_id={job_st.job_id}, state={job_st.state})")
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        print(f"Data -> DataError({code})")

    try:
        job_sp = stop_data_update_job(job_id=_JOB_NAME, request_id=req_id)
        print(_format_result(job_sp))
        print(f"Data -> JobStatus(job_id={job_sp.job_id}, state={job_sp.state})")
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        print(f"Data -> DataError({code})")


def fr_data_044_084() -> None:
    """FR-DATA-044, FR-DATA-084: Stage 3 — Run update job once and advance checkpoint deterministically."""
    _header(
        "Stage 3: Single-Run Execution & Checkpointing - Run Job Once (FR-DATA-044, FR-DATA-084)"
    )
    req_id = generate_id("req")
    try:
        res = run_data_update_job_once(job_id=_JOB_NAME, request_id=req_id)
        print(_format_result(res))
        print(f"Data -> JobRunResult(job_id={res.job_id}, state={res.state})")
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        print(f"Data -> DataError({code})")


def fr_data_045() -> None:
    """FR-DATA-045: Stage 4 — Query data update job status and recovery state."""
    _header("Stage 4: Job Status & Recovery - Job Status Query (FR-DATA-045)")
    req_id = generate_id("req")
    status_req = build_job_status_request(job_id=_JOB_NAME, request_id=req_id)
    try:
        st = get_data_update_job_status(status_req)
        print(_format_result(st))
        print(f"Data -> JobStatus(job_id={st.job_id}, state={st.state})")
    except Exception as exc:
        code = getattr(exc, "code", type(exc).__name__)
        print(f"Data -> DataError({code})")


def fr_data_174() -> None:
    """FR-DATA-174: Schedule and dispatch the safe weekly calendar refresh."""
    _header("Stage 5: Weekly Economic Calendar Dispatch (FR-DATA-174)")
    req_id = generate_id("req")
    definition = build_job_definition(
        job_id=_CALENDAR_JOB_NAME,
        source_id="forexfactory",
        symbols=(),
        timeframes=(),
        data_kinds=("economic_calendar",),
        start=datetime(2026, 8, 2, tzinfo=UTC),
        end=None,
        interval_seconds=604800,
        enabled=True,
        environment="dev",
        created_at=datetime.now(UTC),
        request_id=req_id,
    )
    created = create_data_update_job(definition, request_id=req_id)
    result = run_data_update_job_once(
        _CALENDAR_JOB_NAME,
        req_id,
        calendar_rows=(
            {
                "title": "Final Manufacturing PMI",
                "country": "JPY",
                "date": "2026-08-02T20:30:00-04:00",
                "impact": "Low",
                "forecast": "54.7",
                "previous": "54.7",
            },
        ),
    )
    print(_format_result(result))
    print(
        "Data -> "
        f"JobStatus(job_id={created.job_id}); "
        f"JobRunResult(state={result.state}, records={result.record_count})"
    )


def main() -> None:
    """Execute every functional-requirement demonstration."""
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
            ensure_source("mt5", generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-13 - Data Jobs and Orchestration")
            print(
                "PURPOSE: Register, schedule, execute, checkpoint, and monitor automated data update jobs"
            )
            print(
                "MODULE FLOW: Stage 1 (Registration & Definition) -> Stage 2 (Lifecycle Control) -> Stage 3 (Single-Run & Checkpoint) -> Stage 4 (Status & Recovery)"
            )
            print("=" * 80)

            fr_data_041()
            fr_data_042_043()
            fr_data_044_084()
            fr_data_045()
            fr_data_174()
            print("SUCCESS: FEAT-DATA-13 completed")


if __name__ == "__main__":
    main()
