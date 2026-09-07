"""Focused public contract for durable job and progress management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.contracts.orchestration.models import JobRecord, ProgressEvent

if TYPE_CHECKING:
    from app.contracts.common.models import DecimalValue


@runtime_checkable
class ProgressCallback(Protocol):
    """Asynchronous observer of accepted progress changes."""

    async def __call__(self, update: ProgressEvent) -> None:
        """Observe one progress event without owning job state."""
        ...


@runtime_checkable
class ManageJobsCapability(Protocol):
    """Capability for idempotent jobs, transitions, and progress observers."""

    async def submit(
        self,
        *,
        idempotency_key: str,
        job_id: str,
    ) -> JobRecord:
        """Persist or return one logical job."""
        ...

    async def transition(
        self,
        job_id: str,
        *,
        expected_version: int,
        event: str,
    ) -> JobRecord:
        """Apply one expected-version state transition."""
        ...

    async def report_progress(
        self,
        job_id: str,
        *,
        expected_version: int,
        progress: DecimalValue,
        message: str = "",
    ) -> ProgressEvent:
        """Persist and publish monotonic progress."""
        ...

    async def subscribe(self, callback: ProgressCallback) -> str:
        """Register a bounded asynchronous progress observer."""
        ...

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove and drain one observer."""
        ...


__all__ = ("JobRecord", "ManageJobsCapability", "ProgressCallback", "ProgressEvent")
