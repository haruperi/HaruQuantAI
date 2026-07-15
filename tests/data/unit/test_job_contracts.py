"""Unit tests for backfill and job lifecycle contracts."""

import pytest
from app.services.data.contracts import JobRunResult, JobStatus
from app.services.data.contracts.errors import DataError

from tests.data.helpers import END, START


def test_job_contracts_require_work_and_checkpoint_evidence() -> None:
    """Elapsed time alone can never represent successful job work."""
    with pytest.raises(DataError):
        JobRunResult(
            job_id="job-1",
            run_id="run-1",
            state="succeeded",
            started_at=START,
            finished_at=END,
            committed_chunks=0,
            record_count=0,
            request_id="req-72ce963e0c5f7c540ff7d0ed2fc7739dc72e59fa5d58fcaa880d430989932a21",
        )
    with pytest.raises(DataError):
        JobStatus(
            job_id="job-1",
            state="running",
            enabled=True,
            lease_state="none",
            recovery_state="clean",
            request_id="req-19008909f52936622bcbb72143057f7a79cafe14ce1a6e1ba01773238698abf5",
        )
