"""Focused public contract for durable shared job and attempt management."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.contracts.orchestration.models import JobRecord, ProgressEvent

if TYPE_CHECKING:
    from app.contracts.common.models import DecimalValue


class DomainOutcome(StrEnum):
    """Semantic outcome independent from infrastructure state."""

    UNKNOWN = "UNKNOWN"
    SUCCESS = "SUCCESS"
    REFUSED = "REFUSED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ControlIntent(StrEnum):
    """Desired job controls."""

    NONE = "NONE"
    CANCEL = "CANCEL"
    PAUSE = "PAUSE"
    RESUME = "RESUME"


@dataclass(frozen=True, slots=True)
class JobSubmission:
    """Immutable logical job acceptance request."""

    job_id: str
    idempotency_key: str
    request_fingerprint: str
    input_ref: str
    owner_operation: str
    parent_job_id: str | None = None
    root_job_id: str | None = None
    max_depth: int = 16
    supports_pause: bool = False


@dataclass(frozen=True, slots=True)
class JobAttempt:
    """One immutable execution attempt of a logical job."""

    attempt_id: str
    job_id: str
    attempt_no: int
    fence: int
    predecessor_attempt_id: str | None


@dataclass(frozen=True, slots=True)
class JobSemanticRecord:
    """Orthogonal semantic/control projection for one logical job."""

    job_id: str
    current_attempt: JobAttempt
    domain_outcome: DomainOutcome
    desired_control: ControlIntent
    acknowledged_control: ControlIntent
    waiting_for_human: bool
    enqueue_intent: bool
    request_fingerprint: str
    input_ref: str
    owner_operation: str
    parent_job_id: str | None
    root_job_id: str
    depth: int
    supports_pause: bool


@dataclass(frozen=True, slots=True)
class EffectReconciliation:
    """Original-idempotency-key receiver effect status."""

    idempotency_key: str
    status: str
    receipt_ref: str | None = None


@runtime_checkable
class ProgressCallback(Protocol):
    async def __call__(self, update: ProgressEvent) -> None:
        """Observe one progress event without owning job state."""
        ...


@runtime_checkable
class ManageJobsCapability(Protocol):
    """Capability for durable jobs, attempts, controls, and observations."""

    async def submit(self, *, idempotency_key: str, job_id: str) -> JobRecord:
        """Backward-compatible minimal submission."""
        ...

    async def submit_job(self, submission: JobSubmission) -> JobSemanticRecord:
        """Atomically persist immutable identity and enqueue intent."""
        ...

    async def get_semantics(self, job_id: str) -> JobSemanticRecord:
        """Return the current semantic/control projection."""
        ...

    async def request_control(
        self,
        job_id: str,
        *,
        expected_version: int,
        control: ControlIntent,
    ) -> JobSemanticRecord:
        """Persist desired control without fabricating acknowledgement."""
        ...

    async def acknowledge_control(
        self,
        job_id: str,
        *,
        control: ControlIntent,
    ) -> JobSemanticRecord:
        """Record owner/executor acknowledgement of a requested control."""
        ...

    async def record_domain_outcome(
        self,
        job_id: str,
        outcome: DomainOutcome,
        *,
        waiting_for_human: bool = False,
    ) -> JobSemanticRecord:
        """Record semantic outcome independently of worker status."""
        ...

    async def retry_terminal(self, job_id: str) -> JobSemanticRecord:
        """Create a linked new attempt instead of reopening a terminal attempt."""
        ...

    async def reconcile_effect(
        self,
        reconciliation: EffectReconciliation,
    ) -> EffectReconciliation:
        """Persist or resolve one receiver effect by original idempotency key."""
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


__all__ = (
    "ControlIntent",
    "DomainOutcome",
    "EffectReconciliation",
    "JobAttempt",
    "JobRecord",
    "JobSemanticRecord",
    "JobSubmission",
    "ManageJobsCapability",
    "ProgressCallback",
    "ProgressEvent",
)
