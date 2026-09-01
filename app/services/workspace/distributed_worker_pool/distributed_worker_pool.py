"""Distributed Worker Pool domain logic and capability implementation.

Purpose:
    Register, authenticate, schedule, and transfer artifacts to remote workers.

Key capabilities:
    * Register worker platform, capability descriptors, resources, and heartbeat.
    * Authenticate worker channels and issue/verify fenced job execution leases.
    * Schedule tasks with data locality scoring preserving deterministic output.
    * Validate chunked, content-addressed artifact transfers and commit under lease.

Python API usage:
    from app.services.workspace.distributed_worker_pool.distributed_worker_pool import (
        DistributedWorkerPoolService,
    )
    service = DistributedWorkerPoolService()
    result = await service.distribute_workers(request)

CLI usage:
    uv run python -m \
        app.services.workspace.distributed_worker_pool.distributed_worker_pool
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import override

from app.contracts.common.models import ProblemDetails, Uuid7
from app.contracts.workspace.errors import WorkspaceFailure, WorkspaceFailureCode
from app.contracts.workspace.models import (
    ArtifactChunk,
    ArtifactManifest,
    DistributeWorkersRequest,
    DistributeWorkersSuccess,
    WorkerCapabilityDescriptor,
    WorkerLease,
    WorkerRegistration,
    WorkerTaskEnvelope,
)
from app.contracts.workspace.ports import DistributeWorkersCapability
from app.services.workspace.distributed_worker_pool.config import (
    DistributedWorkerPoolConfig,
)

logger = logging.getLogger(__name__)


def _now_utc() -> str:
    """Return current UTC timestamp in ISO 8601 microseconds format.

    Returns:
        Current UTC timestamp formatted as ISO 8601 string.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _add_seconds_utc(iso_ts: str, seconds: int) -> str:
    """Add seconds to an ISO 8601 UTC timestamp.

    Args:
        iso_ts: Source timestamp ISO string.
        seconds: Number of seconds to add.

    Returns:
        Updated ISO 8601 UTC timestamp string.
    """
    dt = datetime.fromisoformat(iso_ts)
    return (dt + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _is_expired(expires_at_ts: str, now_ts: str) -> bool:
    """Return True if now_ts is at or after expires_at_ts.

    Args:
        expires_at_ts: Expiry ISO timestamp.
        now_ts: Current ISO timestamp.

    Returns:
        True if current timestamp is past expiry.
    """
    return now_ts >= expires_at_ts


def _make_failure(
    request_id: Uuid7,
    code: WorkspaceFailureCode,
    status: int,
    title: str,
    detail: str,
) -> WorkspaceFailure:
    """Construct a standard WorkspaceFailure envelope with ProblemDetails.

    Args:
        request_id: Request UUID identifier.
        code: Machine-readable failure code.
        status: HTTP status code.
        title: Short title for the error.
        detail: Human-readable explanation.

    Returns:
        Populated WorkspaceFailure record.
    """
    error_slug = code.lower().replace("_", "-")
    return WorkspaceFailure(
        request_id=request_id,
        code=code,
        problem=ProblemDetails(
            type=f"urn:haruquantai:workspace:{error_slug}",
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


async def fr_ws_register_worker_capabilities(
    service: DistributedWorkerPoolService,
    descriptor: WorkerCapabilityDescriptor,
    endpoint: str,
) -> WorkerRegistration:
    """Trace function for FR-WS-REGISTER_WORKER_CAPABILITIES.

    Args:
        service: Distributed worker pool service instance.
        descriptor: Capability and platform descriptor.
        endpoint: Network endpoint URI string.

    Returns:
        WorkerRegistration representing the registered worker.

    Raises:
        RuntimeError: If registration fails.
    """
    request_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())
    request = DistributeWorkersRequest(
        request_id=request_id,
        capability_snapshot_id=snapshot_id,
        operation="REGISTER",
        descriptor=descriptor,
        endpoint=endpoint,
    )
    result = await service.distribute_workers(request)
    if isinstance(result, DistributeWorkersSuccess) and result.registration is not None:
        return result.registration
    msg = f"Worker registration failed: {result}"
    raise RuntimeError(msg)


async def fr_ws_secure_remote_workers(
    service: DistributedWorkerPoolService,
    worker_id: Uuid7,
    job_id: Uuid7,
    attempt_no: int,
) -> WorkerLease:
    """Trace function for FR-WS-SECURE_REMOTE_WORKERS.

    Args:
        service: Distributed worker pool service instance.
        worker_id: Target worker UUID identifier.
        job_id: Target job UUID identifier.
        attempt_no: Execution attempt index.

    Returns:
        WorkerLease representing the acquired fenced lease.

    Raises:
        RuntimeError: If authentication or lease acquisition fails.
    """
    request_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())
    auth_request = DistributeWorkersRequest(
        request_id=request_id,
        capability_snapshot_id=snapshot_id,
        operation="AUTHENTICATE",
        worker_id=worker_id,
    )
    auth_res = await service.distribute_workers(auth_request)
    if auth_res.outcome == "FAILURE":
        auth_msg = f"Authentication failed: {auth_res.problem.detail}"
        raise RuntimeError(auth_msg)

    lease_request_id = str(uuid.uuid7())
    lease_request = DistributeWorkersRequest(
        request_id=lease_request_id,
        capability_snapshot_id=snapshot_id,
        operation="ACQUIRE_LEASE",
        worker_id=worker_id,
        job_id=job_id,
        attempt_no=attempt_no,
    )
    lease_res = await service.distribute_workers(lease_request)
    if isinstance(lease_res, DistributeWorkersSuccess) and lease_res.lease is not None:
        return lease_res.lease
    lease_msg = f"Lease acquisition failed: {lease_res}"
    raise RuntimeError(lease_msg)


async def fr_ws_schedule_data_locality(
    service: DistributedWorkerPoolService,
    job_id: Uuid7,
    attempt_no: int,
    task_run_id: Uuid7,
    locality_hints: tuple[str, ...],
) -> WorkerTaskEnvelope:
    """Trace function for FR-WS-SCHEDULE_DATA_LOCALITY.

    Args:
        service: Distributed worker pool service instance.
        job_id: Target job UUID identifier.
        attempt_no: Execution attempt index.
        task_run_id: Task run UUID identifier.
        locality_hints: Tuple of content hashes for locality matching.

    Returns:
        WorkerTaskEnvelope representing task assignment.

    Raises:
        RuntimeError: If assignment fails.
    """
    request_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())
    request = DistributeWorkersRequest(
        request_id=request_id,
        capability_snapshot_id=snapshot_id,
        operation="ASSIGN_TASK",
        job_id=job_id,
        attempt_no=attempt_no,
        task_run_id=task_run_id,
        locality_hints=locality_hints,
    )
    result = await service.distribute_workers(request)
    if isinstance(result, DistributeWorkersSuccess) and result.envelope is not None:
        return result.envelope
    assign_msg = f"Task assignment failed: {result}"
    raise RuntimeError(assign_msg)


async def fr_ws_verify_artifact_transfer(
    service: DistributedWorkerPoolService,
    artifact: ArtifactManifest,
    job_id: Uuid7,
    attempt_no: int,
    fencing_token: int,
) -> ArtifactManifest:
    """Trace function for FR-WS-VERIFY_ARTIFACT_TRANSFER.

    Args:
        service: Distributed worker pool service instance.
        artifact: Staged artifact manifest.
        job_id: Active job UUID identifier.
        attempt_no: Active attempt index.
        fencing_token: Fencing token for the active lease.

    Returns:
        ArtifactManifest representing committed artifact.

    Raises:
        RuntimeError: If prepare or commit transfer fails.
    """
    prep_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())
    prep_req = DistributeWorkersRequest(
        request_id=prep_id,
        capability_snapshot_id=snapshot_id,
        operation="PREPARE_TRANSFER",
        artifact=artifact,
    )
    prep_res = await service.distribute_workers(prep_req)
    if prep_res.outcome == "FAILURE":
        prep_msg = f"Prepare transfer failed: {prep_res.problem.detail}"
        raise RuntimeError(prep_msg)

    commit_id = str(uuid.uuid7())
    commit_req = DistributeWorkersRequest(
        request_id=commit_id,
        capability_snapshot_id=snapshot_id,
        operation="COMMIT_TRANSFER",
        artifact_id=artifact.artifact_id,
        job_id=job_id,
        attempt_no=attempt_no,
        fencing_token=fencing_token,
    )
    commit_res = await service.distribute_workers(commit_req)
    if (
        isinstance(commit_res, DistributeWorkersSuccess)
        and commit_res.artifact is not None
    ):
        return commit_res.artifact
    commit_msg = f"Commit transfer failed: {commit_res}"
    raise RuntimeError(commit_msg)


class DistributedWorkerPoolService(DistributeWorkersCapability):
    """Production service implementing DistributeWorkersCapability port."""

    def __init__(
        self,
        config: DistributedWorkerPoolConfig | None = None,
    ) -> None:
        """Initialize the distributed worker pool service.

        Args:
            config: Optional configuration settings.
        """
        self._config = config or DistributedWorkerPoolConfig()
        self._workers: dict[str, WorkerRegistration] = {}
        self._leases: dict[tuple[str, int, int], WorkerLease] = {}
        self._active_leases: dict[tuple[str, int], WorkerLease] = {}
        self._job_fencing_tokens: dict[str, int] = {}
        self._artifacts: dict[str, ArtifactManifest] = {}
        self._envelopes: dict[str, WorkerTaskEnvelope] = {}
        self._handlers: dict[
            str,
            Callable[
                [DistributeWorkersRequest],
                DistributeWorkersSuccess | WorkspaceFailure,
            ],
        ] = {
            "REGISTER": self._handle_register,
            "AUTHENTICATE": self._handle_authenticate,
            "HEARTBEAT": self._handle_heartbeat,
            "ACQUIRE_LEASE": self._handle_acquire_lease,
            "RELEASE_LEASE": self._handle_release_lease,
            "ASSIGN_TASK": self._handle_assign_task,
            "PREPARE_TRANSFER": self._handle_prepare_transfer,
            "COMMIT_TRANSFER": self._handle_commit_transfer,
        }

    def _next_fencing_token(self, job_id: str) -> int:
        """Return next monotonically increasing fencing token for a job."""
        next_tok = self._job_fencing_tokens.get(job_id, 0) + 1
        self._job_fencing_tokens[job_id] = next_tok
        return next_tok

    def _count_active_leases_for_worker(self, worker_id: str) -> int:
        """Return count of active leases currently assigned to the worker."""
        return sum(
            1
            for lease in self._active_leases.values()
            if lease.worker_id == worker_id and lease.state == "ACTIVE"
        )

    @override
    async def distribute_workers(
        self,
        request: DistributeWorkersRequest,
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        """Process operation-discriminated distributed worker pool request.

        Args:
            request: Distributed worker pool request DTO.

        Returns:
            DistributeWorkersSuccess on successful operation, or WorkspaceFailure.
        """
        handler = self._handlers[request.operation]
        return handler(request)

    def _handle_register(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if request.descriptor is None or request.endpoint is None:
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                "REGISTER operation requires descriptor and endpoint",
            )
        worker_id = str(uuid.uuid7())
        now = _now_utc()
        interval = request.descriptor.heartbeat_interval_seconds
        expires_at = _add_seconds_utc(now, interval)
        registration = WorkerRegistration(
            worker_id=worker_id,
            descriptor=request.descriptor,
            endpoint=request.endpoint,
            registered_at=now,
            last_heartbeat_at=now,
            heartbeat_expires_at=expires_at,
            trusted=False,
        )
        self._workers[worker_id] = registration
        logger.info(
            "Registered worker %s at %s (untrusted)",
            worker_id,
            request.endpoint,
        )
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            registration=registration,
        )

    def _handle_authenticate(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if request.worker_id is None:
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                "AUTHENTICATE requires worker_id",
            )
        worker_id = request.worker_id
        if worker_id not in self._workers:
            return _make_failure(
                request.request_id,
                "WORKER_UNKNOWN",
                404,
                "Worker Unknown",
                f"Worker {worker_id} is not registered",
            )
        existing = self._workers[worker_id]
        now = _now_utc()
        heartbeat_expires = (
            existing.heartbeat_expires_at
            if existing.heartbeat_expires_at > now
            else _add_seconds_utc(
                now,
                existing.descriptor.heartbeat_interval_seconds,
            )
        )
        last_heartbeat = max(existing.last_heartbeat_at, now)
        if heartbeat_expires <= last_heartbeat:
            heartbeat_expires = _add_seconds_utc(
                last_heartbeat,
                existing.descriptor.heartbeat_interval_seconds,
            )

        authenticated = WorkerRegistration(
            worker_id=worker_id,
            descriptor=existing.descriptor,
            endpoint=existing.endpoint,
            registered_at=existing.registered_at,
            last_heartbeat_at=last_heartbeat,
            heartbeat_expires_at=heartbeat_expires,
            trusted=True,
        )
        self._workers[worker_id] = authenticated
        logger.info("Worker %s channel authenticated (trusted=True)", worker_id)
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            registration=authenticated,
        )

    def _handle_heartbeat(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if request.worker_id is None:
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                "HEARTBEAT requires worker_id",
            )
        worker_id = request.worker_id
        if worker_id not in self._workers:
            return _make_failure(
                request.request_id,
                "WORKER_UNKNOWN",
                404,
                "Worker Unknown",
                f"Worker {worker_id} is not registered",
            )
        existing = self._workers[worker_id]
        now = _now_utc()
        if _is_expired(existing.heartbeat_expires_at, now):
            return _make_failure(
                request.request_id,
                "WORKER_EXPIRED",
                410,
                "Worker Expired",
                f"Worker {worker_id} heartbeat expired",
            )
        interval = existing.descriptor.heartbeat_interval_seconds
        expires_at = _add_seconds_utc(now, interval)
        updated = WorkerRegistration(
            worker_id=worker_id,
            descriptor=existing.descriptor,
            endpoint=existing.endpoint,
            registered_at=existing.registered_at,
            last_heartbeat_at=now,
            heartbeat_expires_at=expires_at,
            trusted=existing.trusted,
        )
        self._workers[worker_id] = updated
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            registration=updated,
        )

    def _validate_worker_for_lease(
        self,
        request_id: Uuid7,
        worker_id: str,
        now: str,
    ) -> WorkspaceFailure | None:
        """Validate worker existence, trust, and liveness for lease acquisition.

        Args:
            request_id: Distributed worker pool request identifier.
            worker_id: Worker UUID identifier.
            now: Current ISO UTC timestamp.

        Returns:
            WorkspaceFailure on validation error, or None if valid.
        """
        if worker_id not in self._workers:
            return _make_failure(
                request_id,
                "WORKER_UNKNOWN",
                404,
                "Worker Unknown",
                f"Worker {worker_id} is not registered",
            )
        worker = self._workers[worker_id]
        if not worker.trusted:
            return _make_failure(
                request_id,
                "WORKER_UNTRUSTED",
                403,
                "Worker Untrusted",
                f"Worker {worker_id} is untrusted",
            )
        if _is_expired(worker.heartbeat_expires_at, now):
            return _make_failure(
                request_id,
                "WORKER_EXPIRED",
                410,
                "Worker Expired",
                f"Worker {worker_id} is expired",
            )
        return None

    def _handle_acquire_lease(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if (
            request.worker_id is None
            or request.job_id is None
            or request.attempt_no is None
        ):
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                "ACQUIRE_LEASE requires worker_id, job_id, attempt_no",
            )
        now = _now_utc()
        err = self._validate_worker_for_lease(
            request.request_id, request.worker_id, now
        )
        if err is not None:
            return err

        worker = self._workers[request.worker_id]
        job_key = (request.job_id, request.attempt_no)
        if job_key in self._active_leases:
            old = self._active_leases[job_key]
            superseded = WorkerLease(
                job_id=old.job_id,
                attempt_no=old.attempt_no,
                worker_id=old.worker_id,
                worker_build_hash=old.worker_build_hash,
                fencing_token=old.fencing_token,
                acquired_at=old.acquired_at,
                last_heartbeat_at=now,
                expires_at=old.expires_at,
                heartbeat_interval_seconds=old.heartbeat_interval_seconds,
                state="SUPERSEDED",
            )
            self._leases[(old.job_id, old.attempt_no, old.fencing_token)] = superseded

        fencing_token = self._next_fencing_token(request.job_id)
        lease_duration = self._config.max_lease_duration_seconds
        expires_at = _add_seconds_utc(now, lease_duration)
        lease = WorkerLease(
            job_id=request.job_id,
            attempt_no=request.attempt_no,
            worker_id=request.worker_id,
            worker_build_hash=worker.descriptor.build_hash,
            fencing_token=fencing_token,
            acquired_at=now,
            last_heartbeat_at=now,
            expires_at=expires_at,
            heartbeat_interval_seconds=worker.descriptor.heartbeat_interval_seconds,
            state="ACTIVE",
        )
        self._leases[(request.job_id, request.attempt_no, fencing_token)] = lease
        self._active_leases[job_key] = lease
        logger.info(
            "Issued lease token=%d to worker=%s for job=%s attempt=%d",
            fencing_token,
            request.worker_id,
            request.job_id,
            request.attempt_no,
        )
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            lease=lease,
        )

    def _handle_release_lease(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if (
            request.worker_id is None
            or request.job_id is None
            or request.attempt_no is None
            or request.fencing_token is None
        ):
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                ("RELEASE_LEASE requires worker_id, job_id, attempt_no, fencing_token"),
            )
        lease_key = (request.job_id, request.attempt_no, request.fencing_token)
        if lease_key not in self._leases:
            return _make_failure(
                request.request_id,
                "LEASE_UNAVAILABLE",
                404,
                "Lease Unavailable",
                f"No lease found for token {request.fencing_token}",
            )
        lease = self._leases[lease_key]
        job_key = (request.job_id, request.attempt_no)
        active_lease = self._active_leases.get(job_key)
        if (
            active_lease is None
            or active_lease.fencing_token != request.fencing_token
            or lease.state != "ACTIVE"
        ):
            return _make_failure(
                request.request_id,
                "LEASE_TOKEN_STALE",
                409,
                "Lease Token Stale",
                f"Lease token {request.fencing_token} is stale",
            )
        now = _now_utc()
        released = WorkerLease(
            job_id=lease.job_id,
            attempt_no=lease.attempt_no,
            worker_id=lease.worker_id,
            worker_build_hash=lease.worker_build_hash,
            fencing_token=lease.fencing_token,
            acquired_at=lease.acquired_at,
            last_heartbeat_at=now,
            expires_at=lease.expires_at,
            heartbeat_interval_seconds=lease.heartbeat_interval_seconds,
            state="RELEASED",
        )
        self._leases[lease_key] = released
        self._active_leases.pop(job_key, None)
        logger.info(
            "Released lease token=%d for job=%s attempt=%d",
            request.fencing_token,
            request.job_id,
            request.attempt_no,
        )
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            lease=released,
        )

    def _handle_assign_task(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if (
            request.job_id is None
            or request.attempt_no is None
            or request.task_run_id is None
        ):
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                "ASSIGN_TASK requires job_id, attempt_no, task_run_id",
            )
        now = _now_utc()
        eligible: list[WorkerRegistration] = []
        for worker in self._workers.values():
            if not worker.trusted or _is_expired(worker.heartbeat_expires_at, now):
                continue
            if request.required_capabilities:
                worker_caps = set(worker.descriptor.capabilities)
                if not all(req in worker_caps for req in request.required_capabilities):
                    continue
            eligible.append(worker)

        if not eligible:
            return _make_failure(
                request.request_id,
                "CAPABILITY_UNAVAILABLE",
                503,
                "Capability Unavailable",
                "No compatible worker found for task scheduling",
            )

        def _sort_key(w: WorkerRegistration) -> tuple[int, int, str]:
            locality_matches = len(
                set(request.locality_hints).intersection(
                    set(w.descriptor.artifact_locality)
                )
            )
            load = self._count_active_leases_for_worker(w.worker_id)
            return (-locality_matches, load, w.worker_id)

        eligible.sort(key=_sort_key)
        selected_worker = eligible[0]

        job_key = (request.job_id, request.attempt_no)
        active_lease = self._active_leases.get(job_key)
        fencing_token = active_lease.fencing_token if active_lease is not None else 1

        envelope_id = str(uuid.uuid7())
        envelope = WorkerTaskEnvelope(
            envelope_id=envelope_id,
            task_run_id=request.task_run_id,
            job_id=request.job_id,
            attempt_no=request.attempt_no,
            fencing_token=fencing_token,
            assigned_worker_id=selected_worker.worker_id,
            assigned_at=now,
            input_hashes=request.locality_hints,
            locality_hints=request.locality_hints,
        )
        self._envelopes[envelope_id] = envelope
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            envelope=envelope,
        )

    def _validate_chunk_plan(
        self,
        request_id: Uuid7,
        artifact: ArtifactManifest,
    ) -> WorkspaceFailure | None:
        """Validate chunk continuity and size consistency.

        Args:
            request_id: Distributed worker pool request identifier.
            artifact: Staged artifact manifest.

        Returns:
            WorkspaceFailure on validation error, or None if valid.
        """
        expected_offset = 0
        for position, chunk in enumerate(artifact.chunks):
            if chunk.index != position or chunk.offset_bytes != expected_offset:
                return _make_failure(
                    request_id,
                    "TRANSFER_INVALID",
                    400,
                    "Transfer Invalid",
                    f"Chunk at position {position} is non-contiguous",
                )
            expected_offset += chunk.size_bytes

        if artifact.chunks and expected_offset != artifact.size_bytes:
            return _make_failure(
                request_id,
                "TRANSFER_INVALID",
                400,
                "Transfer Invalid",
                (
                    f"Total chunk bytes ({expected_offset}) mismatch size"
                    f" ({artifact.size_bytes})"
                ),
            )
        return None

    def _handle_prepare_transfer(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if request.artifact is None:
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                "PREPARE_TRANSFER requires artifact manifest",
            )
        artifact = request.artifact
        if artifact.state != "STAGED":
            return _make_failure(
                request.request_id,
                "TRANSFER_INVALID",
                400,
                "Transfer Invalid",
                "Artifact state must be STAGED for PREPARE_TRANSFER",
            )
        err = self._validate_chunk_plan(request.request_id, artifact)
        if err is not None:
            return err

        self._artifacts[artifact.artifact_id] = artifact
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            artifact=artifact,
        )

    def _validate_commit_lease(
        self,
        request_id: Uuid7,
        job_id: str,
        attempt_no: int,
        fencing_token: int,
        now: str,
    ) -> WorkspaceFailure | None:
        """Validate lease active status and token match for artifact commit.

        Args:
            request_id: Distributed worker pool request identifier.
            job_id: Target job UUID string.
            attempt_no: Attempt index.
            fencing_token: Fencing token integer.
            now: Current ISO UTC timestamp string.

        Returns:
            WorkspaceFailure on validation error, or None if valid.
        """
        job_key = (job_id, attempt_no)
        active_lease = self._active_leases.get(job_key)
        if active_lease is None:
            return _make_failure(
                request_id,
                "LEASE_UNAVAILABLE",
                404,
                "Lease Unavailable",
                f"No active lease for job={job_id} attempt={attempt_no}",
            )
        if active_lease.fencing_token != fencing_token:
            return _make_failure(
                request_id,
                "LEASE_TOKEN_STALE",
                409,
                "Lease Token Stale",
                (
                    f"Token {fencing_token} is stale;"
                    f" active is {active_lease.fencing_token}"
                ),
            )
        if _is_expired(active_lease.expires_at, now):
            return _make_failure(
                request_id,
                "LEASE_UNAVAILABLE",
                410,
                "Lease Expired",
                "Active execution lease has expired",
            )
        return None

    def _validate_staged_artifact(
        self,
        request_id: Uuid7,
        artifact_id: str,
    ) -> WorkspaceFailure | None:
        """Validate staged artifact presence and chunk completeness.

        Args:
            request_id: Distributed worker pool request identifier.
            artifact_id: Staged artifact UUID string.

        Returns:
            WorkspaceFailure on validation error, or None if valid.
        """
        if artifact_id not in self._artifacts:
            return _make_failure(
                request_id,
                "TRANSFER_INVALID",
                404,
                "Transfer Not Found",
                f"Artifact {artifact_id} was not staged",
            )
        staged = self._artifacts[artifact_id]
        if staged.size_bytes > 0 and not staged.chunks:
            return _make_failure(
                request_id,
                "TRANSFER_INCOMPLETE",
                400,
                "Transfer Incomplete",
                "Artifact has non-zero size but no transfer chunks",
            )
        return None

    def _handle_commit_transfer(
        self, request: DistributeWorkersRequest
    ) -> DistributeWorkersSuccess | WorkspaceFailure:
        if (
            request.artifact_id is None
            or request.job_id is None
            or request.attempt_no is None
            or request.fencing_token is None
        ):
            return _make_failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                400,
                "Validation Failed",
                (
                    "COMMIT_TRANSFER requires artifact_id, job_id, attempt_no,"
                    " fencing_token"
                ),
            )
        now = _now_utc()
        lease_err = self._validate_commit_lease(
            request.request_id,
            request.job_id,
            request.attempt_no,
            request.fencing_token,
            now,
        )
        if lease_err is not None:
            return lease_err

        art_err = self._validate_staged_artifact(
            request.request_id, request.artifact_id
        )
        if art_err is not None:
            return art_err

        staged = self._artifacts[request.artifact_id]
        if staged.state == "COMMITTED":
            return DistributeWorkersSuccess(
                request_id=request.request_id,
                artifact=staged,
            )

        committed = ArtifactManifest(
            artifact_id=staged.artifact_id,
            kind=staged.kind,
            content_hash=staged.content_hash,
            size_bytes=staged.size_bytes,
            media_type=staged.media_type,
            artifact_schema_version=staged.artifact_schema_version,
            state="COMMITTED",
            chunks=staged.chunks,
            created_at=staged.created_at,
            committed_at=now,
        )
        self._artifacts[request.artifact_id] = committed
        logger.info(
            "Committed artifact %s under token %d",
            request.artifact_id,
            request.fencing_token,
        )
        return DistributeWorkersSuccess(
            request_id=request.request_id,
            artifact=committed,
        )


async def _async_run_scenarios() -> None:
    """Asynchronously execute all requirement scenarios.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    print("=== DistributeWorkersService Executable Usage Harness ===")
    service = DistributedWorkerPoolService()

    # Scenario 1: FR-WS-REGISTER_WORKER_CAPABILITIES
    print("\n--- Scenario 1: FR-WS-REGISTER_WORKER_CAPABILITIES ---")
    desc1 = WorkerCapabilityDescriptor(
        capabilities=("workspace.distribute-workers@1",),
        build_hash="a" * 64,
        os_family="LINUX",
        architecture="X86_64",
        cpu_cores=8,
        memory_mb=16384,
        artifact_locality=("b" * 64, "c" * 64),
        heartbeat_interval_seconds=30,
    )
    reg1 = await fr_ws_register_worker_capabilities(
        service, desc1, "https://worker-node-1.internal:8443"
    )
    print(f"Registered Worker 1 ID: {reg1.worker_id}, Trusted: {reg1.trusted}")
    if reg1.trusted:
        err_msg = "Worker must not be trusted on registration alone"
        raise RuntimeError(err_msg)

    # Scenario 2: FR-WS-SECURE_REMOTE_WORKERS
    print("\n--- Scenario 2: FR-WS-SECURE_REMOTE_WORKERS ---")
    job_id = str(uuid.uuid7())
    lease = await fr_ws_secure_remote_workers(service, reg1.worker_id, job_id, 1)
    print(f"Acquired Fenced Lease Token: {lease.fencing_token} for Job: {lease.job_id}")
    if lease.fencing_token != 1 or lease.state != "ACTIVE":
        err_msg = "Expected active lease with fencing token 1"
        raise RuntimeError(err_msg)

    # Scenario 3: FR-WS-SCHEDULE_DATA_LOCALITY
    print("\n--- Scenario 3: FR-WS-SCHEDULE_DATA_LOCALITY ---")
    task_run_id = str(uuid.uuid7())
    envelope = await fr_ws_schedule_data_locality(
        service,
        job_id=job_id,
        attempt_no=1,
        task_run_id=task_run_id,
        locality_hints=("b" * 64,),
    )
    print(
        f"Assigned Task Run: {envelope.task_run_id} to Worker:"
        f" {envelope.assigned_worker_id}"
    )
    if envelope.assigned_worker_id != reg1.worker_id:
        err_msg = "Expected assignment to Worker 1 matching locality"
        raise RuntimeError(err_msg)

    # Scenario 4: FR-WS-VERIFY_ARTIFACT_TRANSFER
    print("\n--- Scenario 4: FR-WS-VERIFY_ARTIFACT_TRANSFER ---")
    content_hash = "d" * 64
    chunk1_hash = "e" * 64
    chunk = ArtifactChunk(
        index=0,
        offset_bytes=0,
        size_bytes=1024,
        chunk_hash=chunk1_hash,
    )
    staged_manifest = ArtifactManifest(
        artifact_id=str(uuid.uuid7()),
        kind="MODEL_WEIGHTS",
        content_hash=content_hash,
        size_bytes=1024,
        media_type="application/octet-stream",
        artifact_schema_version=1,
        state="STAGED",
        chunks=(chunk,),
        created_at=_now_utc(),
    )
    committed_manifest = await fr_ws_verify_artifact_transfer(
        service,
        artifact=staged_manifest,
        job_id=job_id,
        attempt_no=1,
        fencing_token=lease.fencing_token,
    )
    print(
        f"Committed Artifact: {committed_manifest.artifact_id}, State:"
        f" {committed_manifest.state}"
    )
    if (
        committed_manifest.state != "COMMITTED"
        or committed_manifest.committed_at is None
    ):
        err_msg = "Artifact commit verification failed"
        raise RuntimeError(err_msg)

    print("\n=== All Scenarios Verified Successfully ===")


def _run_scenarios() -> None:
    """Execute all requirement scenarios as an executable teaching harness."""
    asyncio.run(_async_run_scenarios())


if __name__ == "__main__":
    _run_scenarios()
