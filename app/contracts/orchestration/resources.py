"""Focused public contract for resource admission and ledger management."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable


class WorkClass(StrEnum):
    """Workload priority class for resource admission."""

    SAFETY = "safety"
    CONTROL = "control"
    BULK = "bulk"


class AdmissionStatus(StrEnum):
    """Status outcomes for resource admission decisions."""

    ADMITTED = "admitted"
    QUEUED = "queued"
    REFUSED = "refused"


class LeaseStatus(StrEnum):
    """Status lifecycle of an admitted resource lease."""

    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True)
class FiniteResourceProfile:
    """Immutable requested resources and hard caps in explicit integer units."""

    memory_bytes: int = 0
    thread_count: int = 0
    temp_disk_bytes: int = 0
    vram_bytes: int = 0
    compile_slots: int = 0
    ready_descriptors: int = 0
    prefetch_chunks: int = 0
    buffer_bytes: int = 0
    cache_bytes: int = 0

    def __post_init__(self) -> None:
        """Validate that all fields are finite, non-negative integers.

        Raises:
            TypeError: If any field is not an integer or is a boolean.
            ValueError: If any field is negative or non-finite.
        """
        for field_name in (
            "memory_bytes",
            "thread_count",
            "temp_disk_bytes",
            "vram_bytes",
            "compile_slots",
            "ready_descriptors",
            "prefetch_chunks",
            "buffer_bytes",
            "cache_bytes",
        ):
            val = getattr(self, field_name)
            # Boolean is a subclass of int in Python, reject bool explicitly
            if isinstance(val, bool) or not isinstance(val, int):
                msg = f"{field_name} must be an integer, got {type(val).__name__}"
                raise TypeError(msg)
            if val < 0:
                msg = f"{field_name} cannot be negative: {val}"
                raise ValueError(msg)
            if not math.isfinite(val):
                msg = f"{field_name} must be finite: {val}"
                raise ValueError(msg)


@dataclass(frozen=True)
class ResourcePolicyRef:
    """Immutable reference to the effective resource policy and workstation defaults."""

    policy_id: str = "default-workstation"
    version: int = 1
    memory_envelope_ratio: float = 0.70
    pressure_threshold_elevated: float = 0.85
    pressure_threshold_critical: float = 0.95
    reserved_control_cpus: int = 2
    ready_descriptors_bound: int = 256
    reserved_control_descriptors: int = 32
    prefetch_chunks_default: int = 2
    buffer_bound_bytes: int = 64 * 1024 * 1024  # 64 MiB
    cache_ceiling_ratio: float = 0.20
    max_concurrent_compilation: int = 1
    disk_headroom_ratio: float = 0.10
    max_initial_temp_disk_bytes: int = 16 * 1024 * 1024 * 1024  # 16 GiB
    initial_temp_disk_free_ratio: float = 0.25

    def __post_init__(self) -> None:
        """Validate numeric limits and ratios.

        Raises:
            ValueError: If numeric ratios or descriptor bounds are invalid.
        """
        if not (0.0 < self.memory_envelope_ratio <= 1.0):
            msg = (
                f"memory_envelope_ratio must be in (0, 1]: {self.memory_envelope_ratio}"
            )
            raise ValueError(msg)
        if not (
            0.0
            < self.pressure_threshold_elevated
            < self.pressure_threshold_critical
            <= 1.0
        ):
            msg = "Invalid pressure thresholds"
            raise ValueError(msg)
        if self.ready_descriptors_bound <= self.reserved_control_descriptors:
            msg = "ready_descriptors_bound must exceed reserved control descriptors"
            raise ValueError(msg)


@dataclass(frozen=True)
class ResourceAdmissionRequest:
    """Request to admit finite work under the resource ledger."""

    request_id: str
    owner_id: str
    work_id: str
    idempotency_key: str
    profile: FiniteResourceProfile
    work_class: WorkClass = WorkClass.BULK
    parent_lease_id: str | None = None
    deadline_utc: datetime | None = None

    def __post_init__(self) -> None:
        """Validate required identifiers.

        Raises:
            ValueError: If required string identifier is blank.
        """
        if not self.request_id.strip():
            msg = "request_id cannot be blank"
            raise ValueError(msg)
        if not self.owner_id.strip():
            msg = "owner_id cannot be blank"
            raise ValueError(msg)
        if not self.work_id.strip():
            msg = "work_id cannot be blank"
            raise ValueError(msg)
        if not self.idempotency_key.strip():
            msg = "idempotency_key cannot be blank"
            raise ValueError(msg)


@dataclass(frozen=True)
class ResourceLease:
    """Reservation lease representing admitted capacity."""

    lease_id: str
    request_id: str
    owner_id: str
    work_id: str
    parent_lease_id: str | None
    root_lease_id: str
    admitted_profile: FiniteResourceProfile
    generation: int
    status: LeaseStatus
    created_at_utc: datetime


@dataclass(frozen=True)
class ResourceAdmissionDecision:
    """Outcome of an admission decision."""

    status: AdmissionStatus
    lease: ResourceLease | None = None
    queue_position: int | None = None
    constrained_dimension: str | None = None
    reason: str | None = None
    effective_policy_version: int = 1


@dataclass(frozen=True)
class ResourceLedgerSnapshot:
    """Bounded snapshot of ledger capacities, commitments, and queues."""

    total_memory_bytes: int
    memory_envelope_bytes: int
    committed_memory_bytes: int
    committed_threads: int
    committed_temp_disk_bytes: int
    committed_vram_bytes: int
    committed_compile_slots: int
    active_root_leases: int
    active_child_leases: int
    queued_requests: int
    memory_pressure_ratio: float
    disk_free_bytes: int
    disk_headroom_bytes: int
    effective_policy_version: int


@runtime_checkable
class ResourceAdmissionPort(Protocol):
    """Public port for resource admission, queueing, and ledger control."""

    async def admit(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision:
        """Admit or queue finite work under the resource ledger.

        Args:
            request: The validated admission request.

        Returns:
            ResourceAdmissionDecision with ADMITTED, QUEUED, or REFUSED status.
        """
        ...

    async def release(self, lease_id: str, generation: int | None = None) -> bool:
        """Release an admitted lease and return capacity to parent/global ledger.

        Args:
            lease_id: Identifier of the lease to release.
            generation: Optional fence generation to verify.

        Returns:
            True if released, False if not found or already released.
        """
        ...

    async def cancel_queued(self, request_id: str) -> bool:
        """Cancel a queued admission request before execution.

        Args:
            request_id: Identifier of the queued request.

        Returns:
            True if request was removed from queue, False if not found.
        """
        ...

    def get_snapshot(self) -> ResourceLedgerSnapshot:
        """Return a bounded snapshot of ledger state."""
        ...

    def reconcile_usage(
        self,
        lease_id: str,
        observed_native_bytes: int,
        observed_vram_bytes: int = 0,
    ) -> None:
        """Reconcile observed physical usage against an active lease.

        Args:
            lease_id: Identifier of the active lease.
            observed_native_bytes: Measured native memory bytes.
            observed_vram_bytes: Measured device VRAM bytes.
        """
        ...
