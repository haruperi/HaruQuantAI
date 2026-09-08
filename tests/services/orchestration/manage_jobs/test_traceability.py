from pathlib import Path

import pytest

from app.contracts.orchestration.jobs import ControlIntent, DomainOutcome, EffectReconciliation, JobSubmission
from app.services.orchestration.manage_jobs._persistence import JobStore
from app.services.orchestration.manage_jobs.manage_jobs import ManageJobsService


@pytest.mark.asyncio
async def test_atomic_identity_control_outcome_and_effect(tmp_path: Path) -> None:
    service = ManageJobsService(JobStore(str(tmp_path / "jobs.db")))
    submission = JobSubmission("j1", "k1", "fp1", "artifact:a", "demo", supports_pause=False)
    first = await service.submit_job(submission)
    second = await service.submit_job(submission)
    assert first == second
    job = service._store.get("j1")
    with pytest.raises(ValueError, match="PAUSE"):
        await service.request_control("j1", expected_version=job.version, control=ControlIntent.PAUSE)
    semantic = await service.record_domain_outcome("j1", DomainOutcome.REFUSED, waiting_for_human=True)
    assert semantic.domain_outcome is DomainOutcome.REFUSED
    assert semantic.waiting_for_human is True
    effect = EffectReconciliation("effect-1", "COMMITTED", "receipt-1")
    assert await service.reconcile_effect(effect) == effect
    assert await service.reconcile_effect(effect) == effect
    await service.close()


@pytest.mark.asyncio
async def test_idempotency_and_ancestry_fail_closed(tmp_path: Path) -> None:
    service = ManageJobsService(JobStore(str(tmp_path / "jobs.db")))
    await service.submit_job(JobSubmission("root", "k-root", "fp-root", "a", "demo"))
    with pytest.raises(ValueError, match="IDEMPOTENCY"):
        await service.submit_job(JobSubmission("other", "k-root", "different", "a", "demo"))
    with pytest.raises(ValueError, match="ANCESTRY"):
        await service.submit_job(JobSubmission("root", "k-child", "fp", "a", "demo", parent_job_id="root"))
    await service.close()
