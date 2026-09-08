"""Core domain service for finite resource admission, hierarchy, and queues."""

from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, override

from app.composition.logging import get_logger
from app.contracts.orchestration.resources import (
    AdmissionStatus,
    FiniteResourceProfile,
    LeaseStatus,
    ResourceAdmissionDecision,
    ResourceAdmissionPort,
    ResourceAdmissionRequest,
    ResourceLease,
    ResourceLedgerSnapshot,
    ResourcePolicyRef,
    WorkClass,
)

if TYPE_CHECKING:
    from app.services.orchestration.reserve_resources._persistence import (
        ResourceReservationStore,
    )

_LOGGER = get_logger("orchestration.reserve_resources")


class ReserveResourcesService(ResourceAdmissionPort):
    """Authoritative ledger admitting finite work without double-allocation."""

    def __init__(
        self,
        store: ResourceReservationStore,
        policy: ResourcePolicyRef | None = None,
        *,
        total_host_memory_bytes: int | None = None,
        total_host_threads: int | None = None,
        total_disk_bytes: int | None = None,
        free_disk_bytes: int | None = None,
    ) -> None:
        """Initialize the resource reservation service.

        Args:
            store: Persistence store for durable lease records.
            policy: Effective resource policy and defaults.
            total_host_memory_bytes: Optional host memory override for testing.
            total_host_threads: Optional host thread count override for testing.
            total_disk_bytes: Optional total disk bytes override for testing.
            free_disk_bytes: Optional free disk bytes override for testing.
        """
        self._store = store
        self._policy = policy or ResourcePolicyRef()
        self._lock = asyncio.Lock()
        self._generation = 1

        # Host resource capacity detection or overrides
        self._total_host_memory_bytes = (
            total_host_memory_bytes
            if total_host_memory_bytes is not None
            else self._detect_host_memory()
        )
        self._total_host_threads = (
            total_host_threads
            if total_host_threads is not None
            else (os.cpu_count() or 4)
        )

        disk_total, disk_free = self._detect_disk_space()
        self._total_disk_bytes = (
            total_disk_bytes if total_disk_bytes is not None else disk_total
        )
        self._free_disk_bytes = (
            free_disk_bytes if free_disk_bytes is not None else disk_free
        )

        # Calculate initial temporary disk budget: min(16 GiB, 25% free at init)
        initial_allowance = int(
            self._free_disk_bytes * self._policy.initial_temp_disk_free_ratio
        )
        self._temp_disk_allowance = min(
            self._policy.max_initial_temp_disk_bytes,
            initial_allowance,
        )

        # Committed capacities (root-level global commitments)
        self._committed_memory_bytes = 0
        self._committed_threads = 0
        self._committed_temp_disk_bytes = 0
        self._committed_vram_bytes = 0
        self._committed_compile_slots = 0
        self._committed_ready_descriptors = 0

        # Active leases and hierarchy tracking
        self._active_leases: dict[str, ResourceLease] = {}
        # parent_lease_id -> list of child_lease_ids
        self._children_by_parent: dict[str, list[str]] = {}
        # parent_lease_id -> sum of delegated child profiles
        self._delegated_by_parent: dict[str, FiniteResourceProfile] = {}

        # Observed physical measurements for active leases
        self._observed_native_bytes: dict[str, int] = {}
        self._observed_vram_bytes: dict[str, int] = {}

        # Admission queues
        self._queue: list[ResourceAdmissionRequest] = []
        _LOGGER.info(
            "Initialized ReserveResourcesService "
            "(memory_env=%d, threads=%d, temp_disk_budget=%d)",
            int(self._total_host_memory_bytes * self._policy.memory_envelope_ratio),
            self._total_host_threads,
            self._temp_disk_allowance,
        )

    @staticmethod
    def _detect_host_memory() -> int:
        """Detect physical host memory in bytes.

        Returns:
            Physical host memory in bytes.
        """
        try:
            import psutil  # type: ignore[import-untyped,unused-ignore]

            return int(psutil.virtual_memory().total)
        except ImportError, OSError, AttributeError:
            # Fallback default: 8 GiB
            return 8 * 1024 * 1024 * 1024

    @staticmethod
    def _detect_disk_space() -> tuple[int, int]:
        """Detect total and free disk space in bytes.

        Returns:
            Tuple of total disk bytes and free disk bytes.
        """
        try:
            usage = shutil.disk_usage(".")
            return int(usage.total), int(usage.free)
        except OSError:
            # Fallback default: 100 GiB total, 40 GiB free
            return 100 * 1024 * 1024 * 1024, 40 * 1024 * 1024 * 1024

    def _check_idempotency(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision | None:
        """Check for active idempotent lease replay.

        Args:
            request: Incoming admission request.

        Returns:
            Decision if matching or conflicting lease exists, else None.
        """
        existing = self._store.get_lease_by_idempotency(request.idempotency_key)
        if existing is not None and existing.status == LeaseStatus.ACTIVE:
            if (
                existing.admitted_profile.memory_bytes == request.profile.memory_bytes
                and existing.admitted_profile.thread_count
                == request.profile.thread_count
            ):
                _LOGGER.info("Idempotent replay for lease %s", existing.lease_id)
                return ResourceAdmissionDecision(
                    status=AdmissionStatus.ADMITTED,
                    lease=existing,
                    effective_policy_version=self._policy.version,
                )
            return ResourceAdmissionDecision(
                status=AdmissionStatus.REFUSED,
                reason="Idempotency key reused with conflicting profile",
                effective_policy_version=self._policy.version,
            )
        return None

    def _check_descriptor_bounds(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision | None:
        """Check ready descriptor and control partition bounds.

        Args:
            request: Incoming admission request.

        Returns:
            Refusal decision if bounded descriptors are exceeded, else None.
        """
        total_descriptors = self._committed_ready_descriptors + len(self._queue)
        if total_descriptors >= self._policy.ready_descriptors_bound:
            _LOGGER.warning(
                "Refusing request %s: ready descriptors bound %d reached",
                request.request_id,
                self._policy.ready_descriptors_bound,
            )
            return ResourceAdmissionDecision(
                status=AdmissionStatus.REFUSED,
                constrained_dimension="ready_descriptors",
                reason=(
                    f"Exceeded descriptor bound of "
                    f"{self._policy.ready_descriptors_bound}"
                ),
                effective_policy_version=self._policy.version,
            )

        if request.work_class == WorkClass.BULK:
            max_bulk_descriptors = (
                self._policy.ready_descriptors_bound
                - self._policy.reserved_control_descriptors
            )
            if total_descriptors >= max_bulk_descriptors:
                _LOGGER.warning(
                    "Refusing bulk request %s: bulk descriptor bound %d reached",
                    request.request_id,
                    max_bulk_descriptors,
                )
                return ResourceAdmissionDecision(
                    status=AdmissionStatus.REFUSED,
                    constrained_dimension="ready_descriptors",
                    reason="Control descriptor partition reserved",
                    effective_policy_version=self._policy.version,
                )
        return None

    def _check_parent_headroom(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision | None:
        """Verify child request does not exceed parent lease headroom.

        Args:
            request: Incoming child admission request.

        Returns:
            Refusal decision if parent is missing or headroom exhausted, else None.
        """
        if request.parent_lease_id is None:
            return None

        parent = self._active_leases.get(request.parent_lease_id)
        if parent is None or parent.status != LeaseStatus.ACTIVE:
            return ResourceAdmissionDecision(
                status=AdmissionStatus.REFUSED,
                reason=f"Parent lease {request.parent_lease_id} is not active",
                effective_policy_version=self._policy.version,
            )

        delegated = self._delegated_by_parent.get(
            request.parent_lease_id, FiniteResourceProfile()
        )
        remaining_parent_mem = (
            parent.admitted_profile.memory_bytes - delegated.memory_bytes
        )
        remaining_parent_threads = (
            parent.admitted_profile.thread_count - delegated.thread_count
        )
        remaining_parent_disk = (
            parent.admitted_profile.temp_disk_bytes - delegated.temp_disk_bytes
        )

        if (
            request.profile.memory_bytes > remaining_parent_mem
            or request.profile.thread_count > remaining_parent_threads
            or request.profile.temp_disk_bytes > remaining_parent_disk
        ):
            _LOGGER.info(
                "Child request %s exceeds parent %s headroom",
                request.request_id,
                request.parent_lease_id,
            )
            return ResourceAdmissionDecision(
                status=AdmissionStatus.REFUSED,
                reason=(
                    f"Request exceeds parent lease {request.parent_lease_id} headroom"
                ),
                effective_policy_version=self._policy.version,
            )
        return None

    def _check_capacity(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision | None:
        """Check memory, threads, disk, and compile limits.

        Args:
            request: Incoming admission request.

        Returns:
            Queued or refused decision if capacity is constrained, else None.
        """
        # 1. Memory envelope and pressure check
        effective_mem_envelope = int(
            self._total_host_memory_bytes * self._policy.memory_envelope_ratio
        )
        projected_mem = self._committed_memory_bytes + (
            request.profile.memory_bytes if request.parent_lease_id is None else 0
        )
        pressure_ratio = projected_mem / max(1, self._total_host_memory_bytes)
        if (
            pressure_ratio >= self._policy.pressure_threshold_critical
            and request.work_class == WorkClass.BULK
        ):
            _LOGGER.warning(
                "Critical memory pressure (%.2f >= %.2f); refusing bulk request %s",
                pressure_ratio,
                self._policy.pressure_threshold_critical,
                request.request_id,
            )
            return ResourceAdmissionDecision(
                status=AdmissionStatus.REFUSED,
                constrained_dimension="memory_bytes",
                reason=f"Critical memory pressure: {pressure_ratio:.2%}",
                effective_policy_version=self._policy.version,
            )

        if (
            projected_mem > effective_mem_envelope
            and request.work_class == WorkClass.BULK
        ):
            _LOGGER.info(
                "Queueing request %s: projected memory %d exceeds envelope %d",
                request.request_id,
                projected_mem,
                effective_mem_envelope,
            )
            self._queue.append(request)
            return ResourceAdmissionDecision(
                status=AdmissionStatus.QUEUED,
                queue_position=len(self._queue),
                constrained_dimension="memory_bytes",
                reason="Memory envelope saturated",
                effective_policy_version=self._policy.version,
            )

        # 2. Thread limits
        usable_threads = max(
            1, self._total_host_threads - self._policy.reserved_control_cpus
        )
        projected_threads = self._committed_threads + (
            request.profile.thread_count if request.parent_lease_id is None else 0
        )
        if projected_threads > usable_threads and request.work_class == WorkClass.BULK:
            _LOGGER.info(
                "Queueing request %s: projected threads %d exceeds usable %d",
                request.request_id,
                projected_threads,
                usable_threads,
            )
            self._queue.append(request)
            return ResourceAdmissionDecision(
                status=AdmissionStatus.QUEUED,
                queue_position=len(self._queue),
                constrained_dimension="thread_count",
                reason="Thread capacity saturated",
                effective_policy_version=self._policy.version,
            )

        # 3. Disk headroom check (only for requests writing to temporary disk)
        if request.profile.temp_disk_bytes > 0:
            projected_disk = (
                self._committed_temp_disk_bytes + request.profile.temp_disk_bytes
            )
            min_headroom = int(
                self._total_disk_bytes * self._policy.disk_headroom_ratio
            )
            projected_free = self._free_disk_bytes - projected_disk
            if (
                projected_disk > self._temp_disk_allowance
                or projected_free < min_headroom
            ):
                _LOGGER.warning(
                    "Refusing request %s: temp disk or 10%% headroom violated",
                    request.request_id,
                )
                return ResourceAdmissionDecision(
                    status=AdmissionStatus.REFUSED,
                    constrained_dimension="temp_disk_bytes",
                    reason="Temporary disk headroom violation",
                    effective_policy_version=self._policy.version,
                )

        # 4. Compile slot check
        if (
            request.profile.compile_slots > 0
            and self._committed_compile_slots + request.profile.compile_slots
            > self._policy.max_concurrent_compilation
        ):
            _LOGGER.info("Queueing compile request %s", request.request_id)
            self._queue.append(request)
            return ResourceAdmissionDecision(
                status=AdmissionStatus.QUEUED,
                queue_position=len(self._queue),
                constrained_dimension="compile_slots",
                reason="Concurrent compilation slot saturated",
                effective_policy_version=self._policy.version,
            )

        return None

    def _issue_lease(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision:
        """Create and record an admitted resource lease.

        Args:
            request: Validated admission request.

        Returns:
            Decision with the newly created lease.
        """
        lease_id = f"lease-{uuid.uuid4().hex[:12]}"
        root_id = (
            self._active_leases[request.parent_lease_id].root_lease_id
            if request.parent_lease_id is not None
            else lease_id
        )

        lease = ResourceLease(
            lease_id=lease_id,
            request_id=request.request_id,
            owner_id=request.owner_id,
            work_id=request.work_id,
            parent_lease_id=request.parent_lease_id,
            root_lease_id=root_id,
            admitted_profile=request.profile,
            generation=self._generation,
            status=LeaseStatus.ACTIVE,
            created_at_utc=datetime.now(UTC),
        )

        if request.parent_lease_id is None:
            self._committed_memory_bytes += request.profile.memory_bytes
            self._committed_threads += request.profile.thread_count
            self._committed_temp_disk_bytes += request.profile.temp_disk_bytes
            self._committed_vram_bytes += request.profile.vram_bytes
            self._committed_compile_slots += request.profile.compile_slots
        else:
            parent_delegated = self._delegated_by_parent.get(
                request.parent_lease_id, FiniteResourceProfile()
            )
            self._delegated_by_parent[request.parent_lease_id] = FiniteResourceProfile(
                memory_bytes=(
                    parent_delegated.memory_bytes + request.profile.memory_bytes
                ),
                thread_count=(
                    parent_delegated.thread_count + request.profile.thread_count
                ),
                temp_disk_bytes=(
                    parent_delegated.temp_disk_bytes + request.profile.temp_disk_bytes
                ),
                vram_bytes=(parent_delegated.vram_bytes + request.profile.vram_bytes),
                compile_slots=(
                    parent_delegated.compile_slots + request.profile.compile_slots
                ),
                ready_descriptors=(
                    parent_delegated.ready_descriptors
                    + request.profile.ready_descriptors
                ),
            )
            self._children_by_parent.setdefault(request.parent_lease_id, []).append(
                lease_id
            )

        self._committed_ready_descriptors += 1
        self._active_leases[lease_id] = lease
        self._store.record_lease(request, lease)

        _LOGGER.info(
            "Admitted lease %s (root=%s, mem=%d, threads=%d)",
            lease_id,
            root_id,
            request.profile.memory_bytes,
            request.profile.thread_count,
        )
        return ResourceAdmissionDecision(
            status=AdmissionStatus.ADMITTED,
            lease=lease,
            effective_policy_version=self._policy.version,
        )

    @override
    async def admit(
        self, request: ResourceAdmissionRequest
    ) -> ResourceAdmissionDecision:
        """Admit or queue finite work under the resource ledger.

        Args:
            request: Validated admission request.

        Returns:
            ResourceAdmissionDecision with lease if admitted, or refusal reason.
        """
        async with self._lock:
            decision = self._check_idempotency(request)
            if decision is not None:
                return decision

            decision = self._check_descriptor_bounds(request)
            if decision is not None:
                return decision

            decision = self._check_parent_headroom(request)
            if decision is not None:
                return decision

            decision = self._check_capacity(request)
            if decision is not None:
                return decision

            return self._issue_lease(request)

    @override
    async def release(self, lease_id: str, generation: int | None = None) -> bool:
        """Release an admitted lease and reclaim capacity.

        Args:
            lease_id: Identifier of lease to release.
            generation: Optional generation fence to check.

        Returns:
            True if lease was released, False if not found or already released.
        """
        async with self._lock:
            lease = self._active_leases.get(lease_id)
            if lease is None:
                return False
            if generation is not None and lease.generation != generation:
                _LOGGER.warning(
                    "Stale generation %d for release of lease %s (current=%d)",
                    generation,
                    lease_id,
                    lease.generation,
                )
                return False

            # Release any active children recursively
            children = self._children_by_parent.pop(lease_id, [])
            for child_id in children:
                if child_id in self._active_leases:
                    self._active_leases.pop(child_id)
                    self._store.update_lease_status(child_id, LeaseStatus.RELEASED)
                    self._committed_ready_descriptors = max(
                        0, self._committed_ready_descriptors - 1
                    )
                    _LOGGER.info("Cascaded release of child lease %s", child_id)

            # Reclaim capacity
            if lease.parent_lease_id is None:
                # Root lease: restore global capacity
                self._committed_memory_bytes = max(
                    0,
                    self._committed_memory_bytes - lease.admitted_profile.memory_bytes,
                )
                self._committed_threads = max(
                    0, self._committed_threads - lease.admitted_profile.thread_count
                )
                self._committed_temp_disk_bytes = max(
                    0,
                    self._committed_temp_disk_bytes
                    - lease.admitted_profile.temp_disk_bytes,
                )
                self._committed_vram_bytes = max(
                    0, self._committed_vram_bytes - lease.admitted_profile.vram_bytes
                )
                self._committed_compile_slots = max(
                    0,
                    self._committed_compile_slots
                    - lease.admitted_profile.compile_slots,
                )
            else:
                # Child lease: restore parent delegation
                parent_delegated = self._delegated_by_parent.get(
                    lease.parent_lease_id, FiniteResourceProfile()
                )
                self._delegated_by_parent[lease.parent_lease_id] = (
                    FiniteResourceProfile(
                        memory_bytes=max(
                            0,
                            parent_delegated.memory_bytes
                            - lease.admitted_profile.memory_bytes,
                        ),
                        thread_count=max(
                            0,
                            parent_delegated.thread_count
                            - lease.admitted_profile.thread_count,
                        ),
                        temp_disk_bytes=max(
                            0,
                            parent_delegated.temp_disk_bytes
                            - lease.admitted_profile.temp_disk_bytes,
                        ),
                        vram_bytes=max(
                            0,
                            parent_delegated.vram_bytes
                            - lease.admitted_profile.vram_bytes,
                        ),
                        compile_slots=max(
                            0,
                            parent_delegated.compile_slots
                            - lease.admitted_profile.compile_slots,
                        ),
                    )
                )
                # Remove from parent children list
                if (
                    lease.parent_lease_id in self._children_by_parent
                    and lease_id in self._children_by_parent[lease.parent_lease_id]
                ):
                    self._children_by_parent[lease.parent_lease_id].remove(lease_id)

            self._committed_ready_descriptors = max(
                0, self._committed_ready_descriptors - 1
            )
            del self._active_leases[lease_id]
            self._delegated_by_parent.pop(lease_id, None)
            self._observed_native_bytes.pop(lease_id, None)
            self._observed_vram_bytes.pop(lease_id, None)

            self._store.update_lease_status(lease_id, LeaseStatus.RELEASED)
            _LOGGER.info("Released lease %s", lease_id)

            # Try to admit queued requests now that capacity is freed
            await self._drain_queue()
            return True

    @override
    async def cancel_queued(self, request_id: str) -> bool:
        """Cancel a queued request.

        Args:
            request_id: Request identifier.

        Returns:
            True if removed from queue, False otherwise.
        """
        async with self._lock:
            for i, req in enumerate(self._queue):
                if req.request_id == request_id:
                    self._queue.pop(i)
                    _LOGGER.info("Cancelled queued request %s", request_id)
                    return True
            return False

    async def _drain_queue(self) -> None:
        """Attempt to admit queued requests in priority and arrival order."""
        if not self._queue:
            return

        # Sort queue: SAFETY > CONTROL > BULK
        class_order = {WorkClass.SAFETY: 0, WorkClass.CONTROL: 1, WorkClass.BULK: 2}
        self._queue.sort(key=lambda r: class_order.get(r.work_class, 3))

        still_queued: list[ResourceAdmissionRequest] = []
        for req in self._queue:
            # Check if this queued request can now be admitted
            effective_mem_envelope = int(
                self._total_host_memory_bytes * self._policy.memory_envelope_ratio
            )
            if (
                self._committed_memory_bytes + req.profile.memory_bytes
                <= effective_mem_envelope
            ):
                # We can admit! Recursively call admit logic (without nested lock)
                lease_id = f"lease-{uuid.uuid4().hex[:12]}"
                lease = ResourceLease(
                    lease_id=lease_id,
                    request_id=req.request_id,
                    owner_id=req.owner_id,
                    work_id=req.work_id,
                    parent_lease_id=req.parent_lease_id,
                    root_lease_id=lease_id,
                    admitted_profile=req.profile,
                    generation=self._generation,
                    status=LeaseStatus.ACTIVE,
                    created_at_utc=datetime.now(UTC),
                )
                self._committed_memory_bytes += req.profile.memory_bytes
                self._committed_threads += req.profile.thread_count
                self._committed_temp_disk_bytes += req.profile.temp_disk_bytes
                self._committed_ready_descriptors += 1
                self._active_leases[lease_id] = lease
                self._store.record_lease(req, lease)
                _LOGGER.info(
                    "Dequeued and admitted lease %s for request %s",
                    lease_id,
                    req.request_id,
                )
            else:
                still_queued.append(req)

        self._queue = still_queued

    @override
    def get_snapshot(self) -> ResourceLedgerSnapshot:
        """Return a bounded snapshot of ledger state."""
        effective_mem_envelope = int(
            self._total_host_memory_bytes * self._policy.memory_envelope_ratio
        )
        pressure_ratio = self._committed_memory_bytes / max(
            1, self._total_host_memory_bytes
        )
        min_headroom = int(self._total_disk_bytes * self._policy.disk_headroom_ratio)

        active_roots = sum(
            1 for lease in self._active_leases.values() if lease.parent_lease_id is None
        )
        active_children = len(self._active_leases) - active_roots

        return ResourceLedgerSnapshot(
            total_memory_bytes=self._total_host_memory_bytes,
            memory_envelope_bytes=effective_mem_envelope,
            committed_memory_bytes=self._committed_memory_bytes,
            committed_threads=self._committed_threads,
            committed_temp_disk_bytes=self._committed_temp_disk_bytes,
            committed_vram_bytes=self._committed_vram_bytes,
            committed_compile_slots=self._committed_compile_slots,
            active_root_leases=active_roots,
            active_child_leases=active_children,
            queued_requests=len(self._queue),
            memory_pressure_ratio=round(pressure_ratio, 4),
            disk_free_bytes=self._free_disk_bytes,
            disk_headroom_bytes=min_headroom,
            effective_policy_version=self._policy.version,
        )

    @override
    def reconcile_usage(
        self,
        lease_id: str,
        observed_native_bytes: int,
        observed_vram_bytes: int = 0,
    ) -> None:
        """Reconcile observed physical usage against an active lease.

        Args:
            lease_id: Identifier of active lease.
            observed_native_bytes: Measured native memory bytes.
            observed_vram_bytes: Measured device VRAM bytes.
        """
        lease = self._active_leases.get(lease_id)
        if lease is None:
            _LOGGER.warning("Reconciliation on non-active lease %s", lease_id)
            return

        self._observed_native_bytes[lease_id] = observed_native_bytes
        self._observed_vram_bytes[lease_id] = observed_vram_bytes

        if observed_native_bytes > lease.admitted_profile.memory_bytes:
            _LOGGER.warning(
                "Lease %s exceeded memory cap: %d > %d",
                lease_id,
                observed_native_bytes,
                lease.admitted_profile.memory_bytes,
            )

    def close(self) -> None:
        """Quiesce and clean up the service."""
        _LOGGER.info("Closing ReserveResourcesService")
        self._store.close()
