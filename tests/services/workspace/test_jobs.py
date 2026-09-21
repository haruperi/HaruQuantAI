"""Unit tests for the durable job and attempt lifecycle management feature.

Fulfills requirements:
    * FR-WORKSPACE-COOPERATIVE_CONTROL: Durable job lifecycle, attempts, and checkpoints.
    * ATW-WORKSPACE-JOB-001: Job state machine transition invariants and CAS integrity.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.contracts.workspace import (
    WORKSPACE_JOBS,
    InvalidJobTransitionError,
    JobDefinition,
    JobNotFoundError,
    JobProgress,
    JobState,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.workspace import (
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
    WorkspacePersistenceService,
)
from app.services.workspace.jobs import (
    SPEC,
    JobConfig,
    JobService,
)
from app.services.workspace.jobs import (
    feature as jobs_feature,
)


@pytest.fixture
def persistence_service(
    tmp_path: pytest.TempPathFactory,
) -> Iterator[WorkspacePersistenceService]:
    """Create isolated SQLite persistence service for test duration."""
    db_file = str(tmp_path) + "/workspace_jobs_test.db"
    config = WorkspacePersistenceConfig(db_path=db_file, wal_mode=True)
    svc = WorkspacePersistenceService(config)
    yield svc
    svc.close()


def test_job_crud_and_receipt(persistence_service: WorkspacePersistenceService) -> None:
    """Verify creating, querying, and receipts of durable jobs."""
    service = JobService(JobConfig(), persistence_service)

    job_def = JobDefinition(
        job_id="job-001",
        group_id="group-alpha",
        operation="backtest.run",
        priority=10,
        resource_class="cpu.standard",
        config_hash="sha256:abc",
        payload={"symbol": "EURUSD", "timeframe": "M1"},
        created_at_utc=datetime.now(UTC),
    )

    receipt = service.create_job(job_def)
    assert receipt.job_id == "job-001"
    assert receipt.state == JobState.QUEUED
    assert receipt.progress_percent == 0.0

    retrieved = service.get_job("job-001")
    assert retrieved is not None
    assert retrieved.job_id == "job-001"
    assert retrieved.payload == {"symbol": "EURUSD", "timeframe": "M1"}

    assert service.get_job("unknown") is None
    assert service.get_receipt("unknown") is None


def test_state_machine_cas_and_invalid_transitions(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify CAS transitions and rejection of invalid state jumps."""
    service = JobService(JobConfig(), persistence_service)

    job_def = JobDefinition(
        job_id="job-sm-01",
        group_id="grp",
        operation="optimize",
        priority=1,
        resource_class="cpu",
        config_hash="h1",
        payload={},
        created_at_utc=datetime.now(UTC),
    )
    service.create_job(job_def)

    # Invalid jump: queued -> succeeded directly is forbidden
    with pytest.raises(InvalidJobTransitionError):
        service.transition_state("job-sm-01", JobState.QUEUED, JobState.SUCCEEDED)

    # CAS mismatch: expected running, but actually queued
    assert not service.transition_state("job-sm-01", JobState.RUNNING, JobState.PAUSING)

    # Valid step: queued -> running
    assert service.transition_state("job-sm-01", JobState.QUEUED, JobState.RUNNING)
    assert service.get_receipt("job-sm-01").state == JobState.RUNNING  # type: ignore[union-attr]

    # Valid step: running -> pausing -> paused -> running -> succeeded
    assert service.transition_state("job-sm-01", JobState.RUNNING, JobState.PAUSING)
    assert service.transition_state("job-sm-01", JobState.PAUSING, JobState.PAUSED)
    assert service.transition_state("job-sm-01", JobState.PAUSED, JobState.RUNNING)
    assert service.transition_state("job-sm-01", JobState.RUNNING, JobState.SUCCEEDED)

    receipt = service.get_receipt("job-sm-01")
    assert receipt is not None
    assert receipt.state == JobState.SUCCEEDED


def test_attempts_heartbeat_and_progress(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify attempt sequence, heartbeats, and checkpoint progression."""
    service = JobService(JobConfig(), persistence_service)

    job_def = JobDefinition(
        job_id="job-att-01",
        group_id="grp",
        operation="run",
        priority=5,
        resource_class="cpu",
        config_hash="h",
        payload={},
        created_at_utc=datetime.now(UTC),
    )
    service.create_job(job_def)
    service.transition_state("job-att-01", JobState.QUEUED, JobState.RUNNING)

    attempt1 = service.create_attempt("job-att-01", "worker-node-1")
    assert attempt1.sequence == 1
    assert attempt1.attempt_id == "job-att-01-att-1"
    assert attempt1.state == JobState.RUNNING

    # Heartbeat
    service.update_heartbeat(attempt1.attempt_id)

    # Record progress with checkpoint
    progress = JobProgress(
        job_id="job-att-01",
        attempt_id=attempt1.attempt_id,
        progress_percent=55.5,
        message="Halfway completed",
        checkpoint={"last_index": 500},
    )
    service.record_progress(progress)

    receipt = service.get_receipt("job-att-01")
    assert receipt is not None
    assert receipt.progress_percent == 55.5
    assert receipt.message == "Halfway completed"

    attempts = service.list_attempts("job-att-01")
    assert len(attempts) == 1
    assert attempts[0].checkpoint == {"last_index": 500}

    # Events audit trail recorded
    events = service.list_events("job-att-01")
    assert len(events) >= 3


def test_orphan_recovery_on_coordinator_restart(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify running jobs are truthfully marked INTERRUPTED on coordinator restart."""
    service = JobService(JobConfig(), persistence_service)

    job_def = JobDefinition(
        job_id="job-orphan-01",
        group_id="grp",
        operation="run",
        priority=5,
        resource_class="cpu",
        config_hash="h",
        payload={},
        created_at_utc=datetime.now(UTC),
    )
    service.create_job(job_def)
    service.transition_state("job-orphan-01", JobState.QUEUED, JobState.RUNNING)
    service.create_attempt("job-orphan-01", "worker-died")

    # Simulate sudden coordinator restart
    recovered_count = service.recover_orphans(interrupted_reason="Sudden crash")
    assert recovered_count == 1

    # Job is now interrupted
    receipt = service.get_receipt("job-orphan-01")
    assert receipt is not None
    assert receipt.state == JobState.INTERRUPTED

    # Attempt is also marked interrupted
    attempts = service.list_attempts("job-orphan-01")
    assert attempts[0].state == JobState.INTERRUPTED


def test_job_not_found_raises(persistence_service: WorkspacePersistenceService) -> None:
    """Verify JobNotFoundError when operating on missing IDs."""
    service = JobService(JobConfig(), persistence_service)
    with pytest.raises(JobNotFoundError):
        service.transition_state("missing", None, JobState.RUNNING)

    with pytest.raises(JobNotFoundError):
        service.create_attempt("missing", "worker-1")


def test_jobs_lifecycle_within_runtime(tmp_path: pytest.TempPathFactory) -> None:
    """Verify feature boots inside Runtime and provides WORKSPACE_JOBS."""
    db_file = str(tmp_path) + "/jobs_rt.db"

    def _persistence_factory() -> WorkspacePersistenceFeature:
        return WorkspacePersistenceFeature(WorkspacePersistenceConfig(db_path=db_file))

    feat = jobs_feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime((_persistence_factory, jobs_feature)) as runtime:
            js = runtime.require(WORKSPACE_JOBS)
            assert js.get_job("missing") is None

    asyncio.run(_test())


def test_job_config_validation() -> None:
    """Verify bounds enforcement on JobConfig."""
    with pytest.raises(ValueError, match="heartbeat_timeout_s"):
        JobConfig(heartbeat_timeout_s=0.0)

    with pytest.raises(ValueError, match="max_attempts_per_job"):
        JobConfig(max_attempts_per_job=0)

    valid = JobConfig(heartbeat_timeout_s=15.0, max_attempts_per_job=5)
    assert valid.heartbeat_timeout_s == 15.0
    assert valid.max_attempts_per_job == 5
