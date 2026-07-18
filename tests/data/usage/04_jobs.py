"""Executable jobs examples for update and backfill scheduling."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    create_data_update_job,
    get_data_update_job_status,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.contracts import (
    DataError,
    JobDefinition,
    JobStatusRequest,
)
from app.utils import generate_id

_SOURCE_ID = "usage-job-source"
_JOB_ID = "usage-aapl-m1-update"
_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(minutes=1)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Create a persistent update/backfill job.")
definition = JobDefinition(
    job_id=_JOB_ID,
    source_id=_SOURCE_ID,
    symbols=("AAPL",),
    timeframes=("M1",),
    data_kinds=("ohlcv",),
    start=_START,
    end=_END,
    interval_seconds=300,
    enabled=False,
    created_at=_START,
    request_id=generate_id("req"),
)
try:
    status = create_data_update_job(definition, generate_id("req"))
    print("Created Job ID:", status.job_id)
except DataError as err:
    print("Expected job creation error:", err.code)

_header("Example 2: Query status of a persistent job.")
try:
    status_query = get_data_update_job_status(
        JobStatusRequest(job_id=_JOB_ID, request_id=generate_id("req"))
    )
    print("Polled Job Enabled Status:", status_query.enabled)
except DataError as err:
    print("Expected job status query error:", err.code)

_header("Example 3: Start a configured persistent job.")
try:
    status_started = start_data_update_job(_JOB_ID, generate_id("req"))
    print("Started Job Enabled Status:", status_started.enabled)
except DataError as err:
    print("Expected job start error:", err.code)

_header("Example 4: Stop a configured persistent job.")
try:
    status_stopped = stop_data_update_job(_JOB_ID, generate_id("req"))
    print("Stopped Job Enabled Status:", status_stopped.enabled)
except DataError as err:
    print("Expected job stop error:", err.code)

_header("Example 5: Trigger a single immediate backfill run for the job.")
try:
    run_res = run_data_update_job_once(_JOB_ID, generate_id("req"))
    print("Job Run State:", run_res.state)
except DataError as err:
    print("Expected job run once error:", err.code)
