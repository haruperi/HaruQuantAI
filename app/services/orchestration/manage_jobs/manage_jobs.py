"""Durable job lifecycle, attempts, controls, and bounded progress observation."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Coroutine
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from app.contracts.orchestration.jobs import (
    ControlIntent, DomainOutcome, EffectReconciliation, JobRecord, JobSemanticRecord,
    JobSubmission, ProgressCallback, ProgressEvent,
)

if TYPE_CHECKING:
    from app.contracts.common.models import DecimalValue
    from app.services.orchestration.manage_jobs._persistence import JobStore

_TRANSITIONS = {
    ("QUEUED", "START"): "RUNNING",
    ("RUNNING", "PAUSE"): "PAUSED",
    ("PAUSED", "RESUME"): "RUNNING",
    ("QUEUED", "CANCEL"): "CANCELLED",
    ("RUNNING", "CANCEL"): "CANCELLED",
    ("PAUSED", "CANCEL"): "CANCELLED",
    ("RUNNING", "COMPLETE"): "COMPLETED",
    ("RUNNING", "FAIL"): "FAILED",
}


@dataclass(slots=True)
class _Subscription:
    queue: asyncio.Queue[ProgressEvent | None]
    task: asyncio.Task[None]


class _TaskSpawner(Protocol):
    def __call__(self, coroutine: Coroutine[Any, Any, None], *, name: str) -> asyncio.Task[None]: ...


class ManageJobsService:
    """Own accepted logical jobs while isolating observers from durable state."""

    def __init__(self, store: JobStore, callback_queue_capacity: int = 128, task_spawner: _TaskSpawner | None = None) -> None:
        self._store = store
        self._callback_queue_capacity = callback_queue_capacity
        self._task_spawner = task_spawner or asyncio.create_task
        self._subscriptions: dict[str, _Subscription] = {}
        self._callback_failures = 0
        self._closed = False

    @property
    def callback_failures(self) -> int:
        return self._callback_failures

    async def submit(self, *, idempotency_key: str, job_id: str) -> JobRecord:
        self._ensure_open()
        return self._store.submit(job_id, idempotency_key)

    async def submit_job(self, submission: JobSubmission) -> JobSemanticRecord:
        self._ensure_open()
        return self._store.submit_job(submission)

    async def get_semantics(self, job_id: str) -> JobSemanticRecord:
        self._ensure_open()
        return self._store.get_semantics(job_id)

    async def request_control(self, job_id: str, *, expected_version: int, control: ControlIntent) -> JobSemanticRecord:
        self._ensure_open()
        job = self._store.get(job_id)
        if job.version != expected_version:
            raise ValueError("JOB_VERSION_CONFLICT")
        current = self._store.get_semantics(job_id)
        if control is ControlIntent.PAUSE and not current.supports_pause:
            raise ValueError("JOB_PAUSE_UNSUPPORTED")
        if control is ControlIntent.RESUME and job.state != "PAUSED":
            raise ValueError("JOB_RESUME_UNSUPPORTED")
        if control is ControlIntent.CANCEL and job.state in {"COMPLETED", "FAILED", "CANCELLED"}:
            raise ValueError("JOB_CONTROL_TERMINAL")
        return self._store.update_semantics(job_id, desired_control=control)

    async def acknowledge_control(self, job_id: str, *, control: ControlIntent) -> JobSemanticRecord:
        self._ensure_open()
        current = self._store.get_semantics(job_id)
        if current.desired_control is not control:
            raise ValueError("JOB_CONTROL_ACK_MISMATCH")
        return self._store.update_semantics(job_id, acknowledged_control=control)

    async def record_domain_outcome(self, job_id: str, outcome: DomainOutcome, *, waiting_for_human: bool = False) -> JobSemanticRecord:
        self._ensure_open()
        return self._store.update_semantics(job_id, domain_outcome=outcome, waiting_for_human=waiting_for_human)

    async def retry_terminal(self, job_id: str) -> JobSemanticRecord:
        self._ensure_open()
        return self._store.retry(job_id)

    async def reconcile_effect(self, reconciliation: EffectReconciliation) -> EffectReconciliation:
        self._ensure_open()
        return self._store.reconcile_effect(reconciliation)

    async def transition(self, job_id: str, *, expected_version: int, event: str) -> JobRecord:
        self._ensure_open()
        current = self._store.get(job_id)
        semantics = None
        try:
            semantics = self._store.get_semantics(job_id)
        except KeyError:
            pass
        if event == "PAUSE" and semantics is not None and not semantics.supports_pause:
            raise ValueError("JOB_PAUSE_UNSUPPORTED")
        target = _TRANSITIONS.get((current.state, event))
        if target is None:
            raise ValueError("JOB_TRANSITION_INVALID")
        record, _sequence = self._store.update(job_id, expected_version=expected_version, state=target)
        return record

    async def report_progress(self, job_id: str, *, expected_version: int, progress: DecimalValue, message: str = "") -> ProgressEvent:
        self._ensure_open()
        current = self._store.get(job_id)
        requested = Decimal(progress)
        if requested < Decimal(current.progress) or not Decimal(0) <= requested <= Decimal(1):
            raise ValueError("JOB_PROGRESS_INVALID")
        record, sequence = self._store.update(job_id, expected_version=expected_version, progress=str(progress), message=message)
        update = ProgressEvent(job_id=job_id, sequence=sequence, progress=record.progress, message=message, occurred_at=record.updated_at)
        for subscription in self._subscriptions.values():
            try:
                subscription.queue.put_nowait(update)
            except asyncio.QueueFull:
                self._callback_failures += 1
        return update

    async def subscribe(self, callback: ProgressCallback) -> str:
        self._ensure_open()
        subscription_id = f"progress-{uuid.uuid4().hex}"
        callback_queue: asyncio.Queue[ProgressEvent | None] = asyncio.Queue(maxsize=self._callback_queue_capacity)
        async def consume() -> None:
            while (item := await callback_queue.get()) is not None:
                try:
                    await callback(item)
                except Exception:
                    self._callback_failures += 1
                finally:
                    callback_queue.task_done()
            callback_queue.task_done()
        task = self._task_spawner(consume(), name=subscription_id)
        self._subscriptions[subscription_id] = _Subscription(callback_queue, task)
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        subscription = self._subscriptions.pop(subscription_id, None)
        if subscription is None:
            return
        await subscription.queue.put(None)
        await subscription.task

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for subscription_id in tuple(self._subscriptions):
            await self.unsubscribe(subscription_id)
        self._store.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("manage-jobs service is closed")
