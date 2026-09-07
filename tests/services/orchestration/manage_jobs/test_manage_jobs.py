"""Focused acceptance tests for jobs and progress callbacks."""

import asyncio
from pathlib import Path

import pytest
from app.contracts.orchestration.jobs import ProgressEvent
from app.services.orchestration.manage_jobs._persistence import JobStore
from app.services.orchestration.manage_jobs.manage_jobs import ManageJobsService


@pytest.mark.asyncio
async def test_idempotency_transitions_and_monotonic_progress() -> None:
    service = ManageJobsService(JobStore(":memory:"))
    first = await service.submit(idempotency_key="same", job_id="job-1")
    replay = await service.submit(idempotency_key="same", job_id="job-2")
    assert replay.job_id == first.job_id
    running = await service.transition("job-1", expected_version=1, event="START")
    update = await service.report_progress(
        "job-1", expected_version=running.version, progress="0.5"
    )
    assert update.progress == "0.5"
    with pytest.raises(ValueError, match="JOB_PROGRESS_INVALID"):
        await service.report_progress("job-1", expected_version=3, progress="0.4")
    await service.close()


@pytest.mark.asyncio
async def test_slow_and_failing_callbacks_do_not_block_state() -> None:
    service = ManageJobsService(JobStore(":memory:"), callback_queue_capacity=2)
    release = asyncio.Event()

    async def slow_callback(update: ProgressEvent) -> None:
        del update
        await release.wait()

    async def failing_callback(update: ProgressEvent) -> None:
        del update
        raise RuntimeError("observer failed")

    slow_id = await service.subscribe(slow_callback)
    await service.subscribe(failing_callback)
    job = await service.submit(idempotency_key="progress", job_id="job-progress")
    running = await service.transition(job.job_id, expected_version=1, event="START")
    await asyncio.wait_for(
        service.report_progress(
            job.job_id, expected_version=running.version, progress="0.25"
        ),
        timeout=0.05,
    )
    release.set()
    await service.unsubscribe(slow_id)
    await service.close()
    assert service.callback_failures == 1


@pytest.mark.asyncio
async def test_job_identity_and_state_survive_restart(tmp_path: Path) -> None:
    database_path = str(tmp_path / "jobs.sqlite3")
    first_service = ManageJobsService(JobStore(database_path))
    job = await first_service.submit(idempotency_key="durable", job_id="job-durable")
    running = await first_service.transition(
        job.job_id, expected_version=job.version, event="START"
    )
    await first_service.close()

    restarted = ManageJobsService(JobStore(database_path))
    replay = await restarted.submit(idempotency_key="durable", job_id="different-id")
    assert replay.job_id == job.job_id
    assert replay.state == "RUNNING"
    assert replay.version == running.version
    await restarted.close()
