"""Bounded offline usage for durable jobs and progress callbacks."""

import asyncio
from typing import TYPE_CHECKING

from app.services.orchestration.manage_jobs._persistence import JobStore
from app.services.orchestration.manage_jobs.manage_jobs import ManageJobsService

if TYPE_CHECKING:
    from app.contracts.orchestration.jobs import ProgressEvent


async def _run_usage_example() -> None:
    service = ManageJobsService(JobStore(":memory:"))
    observed: list[str] = []

    async def observe(update: ProgressEvent) -> None:
        observed.append(str(update))

    await service.subscribe(observe)
    job = await service.submit(idempotency_key="demo", job_id="job-demo")
    job = await service.transition(
        job.job_id, expected_version=job.version, event="START"
    )
    await service.report_progress(
        job.job_id, expected_version=job.version, progress="0.5", message="halfway"
    )
    await service.close()
    print(f"observed_progress={len(observed)}")


if __name__ == "__main__":
    asyncio.run(_run_usage_example())
