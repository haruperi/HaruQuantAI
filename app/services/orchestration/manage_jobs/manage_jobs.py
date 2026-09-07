"""Durable job lifecycle and non-blocking progress observation."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Coroutine
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

from app.contracts.orchestration.jobs import JobRecord, ProgressCallback, ProgressEvent

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
    def __call__(
        self, coroutine: Coroutine[Any, Any, None], *, name: str
    ) -> asyncio.Task[None]: ...


class ManageJobsService:
    """Own accepted jobs and isolate progress observers from state mutation."""

    def __init__(
        self,
        store: JobStore,
        callback_queue_capacity: int = 128,
        task_spawner: _TaskSpawner | None = None,
    ) -> None:
        """Initialize durable state and bounded callback delivery.

        Args:
            store: Feature-owned job persistence.
            callback_queue_capacity: Per-observer queue capacity.
            task_spawner: Lifecycle-aware task factory; defaults to asyncio for
                direct tests and the offline usage harness.
        """
        self._store = store
        self._callback_queue_capacity = callback_queue_capacity
        self._task_spawner = task_spawner or asyncio.create_task
        self._subscriptions: dict[str, _Subscription] = {}
        self._callback_failures = 0
        self._closed = False

    @property
    def callback_failures(self) -> int:
        """Return the bounded diagnostic count of observer failures."""
        return self._callback_failures

    async def submit(self, *, idempotency_key: str, job_id: str) -> JobRecord:
        """Persist or resolve one idempotent job.

        Returns:
            New or previously accepted job record.
        """
        self._ensure_open()
        return self._store.submit(job_id, idempotency_key)

    async def transition(
        self, job_id: str, *, expected_version: int, event: str
    ) -> JobRecord:
        """Apply one declared expected-version transition.

        Returns:
            Updated job record.

        Raises:
            ValueError: If the transition or expected version is invalid.
        """
        self._ensure_open()
        current = self._store.get(job_id)
        target = _TRANSITIONS.get((current.state, event))
        if target is None:
            raise ValueError("JOB_TRANSITION_INVALID")
        record, _sequence = self._store.update(
            job_id, expected_version=expected_version, state=target
        )
        return record

    async def report_progress(
        self,
        job_id: str,
        *,
        expected_version: int,
        progress: DecimalValue,
        message: str = "",
    ) -> ProgressEvent:
        """Persist monotonic progress and enqueue callbacks without waiting.

        Returns:
            Persisted progress event.

        Raises:
            ValueError: If progress regresses, exceeds its range, or conflicts.
        """
        self._ensure_open()
        current = self._store.get(job_id)
        requested = Decimal(progress)
        if requested < Decimal(current.progress) or not Decimal(
            0
        ) <= requested <= Decimal(1):
            raise ValueError("JOB_PROGRESS_INVALID")
        record, sequence = self._store.update(
            job_id,
            expected_version=expected_version,
            progress=str(progress),
            message=message,
        )
        update = ProgressEvent(
            job_id=job_id,
            sequence=sequence,
            progress=record.progress,
            message=message,
            occurred_at=record.updated_at,
        )
        for subscription in self._subscriptions.values():
            try:
                subscription.queue.put_nowait(update)
            except asyncio.QueueFull:
                self._callback_failures += 1
        return update

    async def subscribe(self, callback: ProgressCallback) -> str:
        """Register one isolated callback worker.

        Returns:
            Opaque subscription identity.
        """
        self._ensure_open()
        subscription_id = f"progress-{uuid.uuid4().hex}"
        callback_queue: asyncio.Queue[ProgressEvent | None] = asyncio.Queue(
            maxsize=self._callback_queue_capacity
        )

        async def consume() -> None:
            while (item := await callback_queue.get()) is not None:
                try:
                    await callback(item)
                except Exception:  # noqa: BLE001 - observers cannot break job state.
                    self._callback_failures += 1
                finally:
                    callback_queue.task_done()
            callback_queue.task_done()

        task = self._task_spawner(consume(), name=subscription_id)
        self._subscriptions[subscription_id] = _Subscription(callback_queue, task)
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove and drain one observer idempotently."""
        subscription = self._subscriptions.pop(subscription_id, None)
        if subscription is None:
            return
        await subscription.queue.put(None)
        await subscription.task

    async def close(self) -> None:
        """Stop observers and close persistence exactly once."""
        if self._closed:
            return
        self._closed = True
        for subscription_id in tuple(self._subscriptions):
            await self.unsubscribe(subscription_id)
        self._store.close()

    def _ensure_open(self) -> None:
        """Reject operations after lifecycle shutdown.

        Raises:
            RuntimeError: If this service has already been closed.
        """
        if self._closed:
            raise RuntimeError("manage-jobs service is closed")
