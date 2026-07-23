"""Bounded update jobs, resumable backfills, and explicit crash recovery.

Split in ``CAP-DATA-026`` Phase 8: lifecycle in ``job.py``, chunk execution in
``backfill.py``, and recovery in ``recovery.py``. The public surface is unchanged.

Recovery is deliberately absent from any import-time path. It runs when a caller asks
and not before.
"""

from app.services.data.data_jobs.backfill import (
    derive_backfill_key,
    execute_backfill_chunk,
)
from app.services.data.data_jobs.job import (
    read_update_job_status,
    run_data_update_job_once,
    schedule_update_job,
)
from app.services.data.data_jobs.recovery import recover_update_jobs

__all__ = [
    "derive_backfill_key",
    "execute_backfill_chunk",
    "read_update_job_status",
    "recover_update_jobs",
    "run_data_update_job_once",
    "schedule_update_job",
]
