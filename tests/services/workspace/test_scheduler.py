"""Unit tests for the bounded scheduler feature (FR-WORKSPACE-COOPERATIVE_CONTROL)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.contracts.workspace import (
    WORKSPACE_SCHEDULER,
    JobDefinition,
    JobState,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.workspace import (
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
    WorkspacePersistenceService,
)
from app.services.workspace.jobs import (
    JobConfig,
    JobService,
)
from app.services.workspace.jobs import (
    feature as jobs_feature,
)
from app.services.workspace.scheduler import (
    SPEC,
    SchedulerConfig,
    SchedulerService,
)
from app.services.workspace.scheduler import (
    feature as scheduler_feature,
)


@pytest.fixture
def persistence_service(
    tmp_path: pytest.TempPathFactory,
) -> Iterator[WorkspacePersistenceService]:
    """Create isolated SQLite persistence service for test duration."""
    db_file = str(tmp_path) + "/workspace_scheduler_test.db"
    config = WorkspacePersistenceConfig(db_path=db_file, wal_mode=True)
    svc = WorkspacePersistenceService(config)
    yield svc
    svc.close()


def _make_job(job_id: str, priority: int) -> JobDefinition:
    return JobDefinition(
        job_id=job_id,
        group_id="grp",
        operation="run",
        priority=priority,
        resource_class="cpu",
        config_hash="h",
        payload={},
        created_at_utc=datetime.now(UTC),
    )


def test_priority_queue_dispatch_and_concurrency(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify jobs are dispatched in order of highest priority up to max concurrency."""
    job_service = JobService(JobConfig(), persistence_service)
    scheduler = SchedulerService(SchedulerConfig(max_concurrency=2), job_service)

    scheduler.submit_job(_make_job("job-low", priority=1))
    scheduler.submit_job(_make_job("job-high", priority=100))
    scheduler.submit_job(_make_job("job-mid", priority=50))

    stats = scheduler.get_queue_stats()
    assert stats.queued_count == 3
    assert stats.running_count == 0

    # Dispatch up to max concurrency (2)
    dispatched = scheduler.poll_and_dispatch()
    assert dispatched == ["job-high", "job-mid"]

    stats_after = scheduler.get_queue_stats()
    assert stats_after.running_count == 2
    assert stats_after.queued_count == 1

    # Further dispatch yields nothing while at max concurrency
    assert scheduler.poll_and_dispatch() == []

    # Finish high priority job
    scheduler.mark_completed("job-high")
    job_service.transition_state("job-high", JobState.RUNNING, JobState.SUCCEEDED)

    # Now low priority job can be dispatched
    dispatched_next = scheduler.poll_and_dispatch()
    assert dispatched_next == ["job-low"]


def test_cooperative_pause_resume_cancel(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify cooperative pause, resume, and cancellation through scheduler."""
    job_service = JobService(JobConfig(), persistence_service)
    scheduler = SchedulerService(SchedulerConfig(max_concurrency=1), job_service)

    scheduler.submit_job(_make_job("job-1", priority=10))
    scheduler.submit_job(_make_job("job-2", priority=5))

    # Dispatch job-1
    scheduler.poll_and_dispatch()
    assert job_service.get_receipt("job-1").state == JobState.RUNNING  # type: ignore[union-attr]

    # Pause running job-1
    assert scheduler.pause_job("job-1") is True
    assert job_service.get_receipt("job-1").state == JobState.PAUSING  # type: ignore[union-attr]
    job_service.transition_state("job-1", JobState.PAUSING, JobState.PAUSED)

    # Resume job-1
    assert scheduler.resume_job("job-1") is True
    assert job_service.get_receipt("job-1").state == JobState.QUEUED  # type: ignore[union-attr]

    # Cancel queued job-2
    assert scheduler.cancel_job("job-2") is True
    assert job_service.get_receipt("job-2").state == JobState.CANCELLED  # type: ignore[union-attr]


def test_scheduler_lifecycle_within_runtime(tmp_path: pytest.TempPathFactory) -> None:
    """Verify feature boots inside Runtime with dependencies and publishes capability."""
    db_file = str(tmp_path) + "/scheduler_rt.db"

    def _persistence_factory() -> WorkspacePersistenceFeature:
        return WorkspacePersistenceFeature(WorkspacePersistenceConfig(db_path=db_file))

    feat = scheduler_feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime(
            (_persistence_factory, jobs_feature, scheduler_feature)
        ) as runtime:
            sched = runtime.require(WORKSPACE_SCHEDULER)
            stats = sched.get_queue_stats()
            assert stats.running_count == 0

    asyncio.run(_test())


def test_scheduler_config_validation() -> None:
    """Verify bounds enforcement on SchedulerConfig."""
    with pytest.raises(ValueError, match="max_concurrency"):
        SchedulerConfig(max_concurrency=0)

    with pytest.raises(ValueError, match="poll_interval_s"):
        SchedulerConfig(poll_interval_s=0.0)

    valid = SchedulerConfig(max_concurrency=8, poll_interval_s=1.0)
    assert valid.max_concurrency == 8
    assert valid.poll_interval_s == 1.0
