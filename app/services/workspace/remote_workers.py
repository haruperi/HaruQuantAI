"""Distributed remote worker grid and job leasing feature module.

Purpose:
    Manages compute node registration, health heartbeats, time-bounded job
    leases, and automatic expired lease reclamation across local and remote
    worker nodes.

Key capabilities:
    * Compute grid node registration and capacity advertisement.
    * Time-bounded worker lease issuance with heartbeat renewal.
    * Graceful worker deregistration and offline state detection.
    * Automatic reconciliation and reclamation of expired leases.

Python API usage:
    workers = ctx.require(WORKSPACE_WORKERS)
    workers.register_node(GridNodeInfo(node_id="worker-1", core_count=8))
    lease = workers.acquire_lease("worker-1", job_id="job-100", ttl_seconds=60)
    workers.release_lease(lease.lease_id)

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, override

from app.contracts.workspace import (
    WORKSPACE_JOBS,
    WORKSPACE_PERSISTENCE,
    WORKSPACE_WORKERS,
    GridNodeInfo,
    GridNodeState,
    JobService,
    JobState,
    LeaseState,
    WorkerLease,
    WorkerLeaseError,
    WorkspacePersistenceService,
)
from app.contracts.workspace import (
    RemoteWorkerService as IRemoteWorkerService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RemoteWorkerConfig:
    """Configuration for remote worker heartbeat intervals and lease timeouts."""

    node_heartbeat_timeout_s: float = 60.0
    default_lease_duration_s: float = 300.0

    def __post_init__(self) -> None:
        """Validate configuration bounds."""
        if self.node_heartbeat_timeout_s <= 0:
            raise ValueError("node_heartbeat_timeout_s must be greater than 0")
        if self.default_lease_duration_s <= 0:
            raise ValueError("default_lease_duration_s must be greater than 0")


class RemoteWorkerService(IRemoteWorkerService):
    """Production implementation of remote worker grid and leasing."""

    def __init__(
        self,
        config: RemoteWorkerConfig,
        job_service: JobService,
        persistence: WorkspacePersistenceService,
    ) -> None:
        """Initialize remote worker service.

        Args:
            config: Worker configuration options.
            job_service: Durable job service boundary.
            persistence: Workspace SQLite persistence boundary.
        """
        self._config = config
        self._job_service = job_service
        self._persistence = persistence

    @override
    def register_node(self, node_info: GridNodeInfo) -> None:
        """Register or update a compute node in the grid ledger.

        Args:
            node_info: Remote worker node details.
        """
        self._persistence.upsert_grid_node(
            node_id=node_info.node_id,
            host=node_info.host,
            port=node_info.port,
            cores=node_info.cores,
            memory_mb=node_info.memory_mb,
            state=node_info.state.value,
            last_heartbeat_utc=node_info.last_heartbeat_utc.isoformat(),
        )
        logger.info("remote_node_registered")

    @override
    def heartbeat_node(self, node_id: str) -> bool:
        """Record a heartbeat signal from a worker node.

        Args:
            node_id: Reporting node ID.

        Returns:
            True if recognized; False if node is unknown.
        """
        now = datetime.now(UTC).isoformat()
        return self._persistence.update_node_heartbeat(node_id, now)

    @override
    def acquire_lease(
        self, node_id: str, job_id: str, duration_seconds: float
    ) -> WorkerLease:
        """Lease a job to an online worker node for a fixed duration.

        Args:
            node_id: Target node.
            job_id: Target job.
            duration_seconds: Lease validity period.

        Returns:
            WorkerLease instance.

        Raises:
            WorkerLeaseError: If node is unavailable, job missing, or lease active.
        """
        node_row = self._persistence.get_grid_node(node_id)
        if not node_row:
            raise WorkerLeaseError(f"Node '{node_id}' is not registered")

        node_state = str(node_row[5])
        last_hb = datetime.fromisoformat(str(node_row[6]))
        if (
            datetime.now(UTC) - last_hb
        ).total_seconds() > self._config.node_heartbeat_timeout_s:
            raise WorkerLeaseError(f"Node '{node_id}' heartbeat has timed out")

        if node_state == GridNodeState.OFFLINE.value:
            raise WorkerLeaseError(f"Node '{node_id}' is offline")

        # Verify job
        job = self._job_service.get_job(job_id)
        if not job:
            raise WorkerLeaseError(f"Job '{job_id}' does not exist")

        now = datetime.now(UTC)
        expires = now + timedelta(seconds=duration_seconds)
        lease_id = f"lease-{uuid.uuid4()}"

        acquired = self._persistence.acquire_grid_lease(
            lease_id=lease_id,
            node_id=node_id,
            job_id=job_id,
            acquired_at_utc=now.isoformat(),
            expires_at_utc=expires.isoformat(),
            state=LeaseState.ACTIVE.value,
            now_utc=now.isoformat(),
        )
        if not acquired:
            raise WorkerLeaseError(f"Job '{job_id}' is already actively leased")

        logger.info("worker_lease_acquired")
        return WorkerLease(
            lease_id=lease_id,
            node_id=node_id,
            job_id=job_id,
            leased_at_utc=now,
            expires_at_utc=expires,
            state=LeaseState.ACTIVE,
        )

    @override
    def release_lease(self, lease_id: str, completed: bool) -> None:
        """Release or settle an active job lease.

        Args:
            lease_id: Lease identifier.
            completed: Whether the leased job completed successfully.
        """
        now = datetime.now(UTC).isoformat()
        completed_state = (
            LeaseState.COMPLETED.value if completed else LeaseState.REVOKED.value
        )
        self._persistence.release_grid_lease(lease_id, completed_state, now)
        logger.info("worker_lease_released")

    @override
    def list_nodes(self) -> tuple[GridNodeInfo, ...]:
        """List all known worker nodes and their status.

        Returns:
            Tuple of registered nodes.
        """
        rows = self._persistence.get_grid_nodes()
        now = datetime.now(UTC)
        nodes: list[GridNodeInfo] = []

        for r in rows:
            hb = datetime.fromisoformat(str(r[6]))
            is_timed_out = (
                now - hb
            ).total_seconds() > self._config.node_heartbeat_timeout_s
            state = GridNodeState.OFFLINE if is_timed_out else GridNodeState(str(r[5]))
            nodes.append(
                GridNodeInfo(
                    node_id=str(r[0]),
                    host=str(r[1]),
                    port=int(r[2]),
                    cores=int(r[3]),
                    memory_mb=int(r[4]),
                    state=state,
                    last_heartbeat_utc=hb,
                )
            )

        return tuple(nodes)

    @override
    def reconcile_expired_leases(self) -> int:
        """Revoke all expired leases and reset associated jobs.

        Returns:
            Count of reclaimed leases.
        """
        now = datetime.now(UTC).isoformat()
        expired = self._persistence.reconcile_expired_leases(now)
        for _lease_id, job_id in expired:
            rcpt = self._job_service.get_receipt(job_id)
            if rcpt and rcpt.state == JobState.RUNNING:
                self._job_service.transition_state(
                    job_id,
                    JobState.RUNNING,
                    JobState.INTERRUPTED,
                    {"reason": "Worker lease expired"},
                )

        logger.info("reconciled_expired_leases")
        return len(expired)


SPEC = FeatureSpec(
    name="workspace.workers",
    provides=frozenset({WORKSPACE_WORKERS}),
    requires=frozenset({WORKSPACE_JOBS, WORKSPACE_PERSISTENCE}),
    optional=frozenset(),
    description="Distributed remote worker grid and leasing reconciliation.",
)


class RemoteWorkerFeature:
    """Lifecycle-managed runtime feature providing remote worker grid and leasing.

    Mounts RemoteWorkerService, connects to WORKSPACE_JOBS and WORKSPACE_PERSISTENCE,
    reconciles node leases, and publishes WORKSPACE_WORKERS into runtime composition.
    """

    def __init__(self, config: RemoteWorkerConfig | None = None) -> None:
        """Initialize remote worker grid feature with lease and heartbeat configuration.

        Args:
            config: Remote worker configuration specifying heartbeat intervals and lease
                durations. If None, default RemoteWorkerConfig is used.
        """
        self._config = config or RemoteWorkerConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable specification declaring capabilities and dependencies."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start worker grid service and publish WORKSPACE_WORKERS capability.

        Args:
            context: Runtime feature context used for dependency resolution and
                capability provision.
        """
        job_service = context.require(WORKSPACE_JOBS)
        persistence = context.require(WORKSPACE_PERSISTENCE)
        service = RemoteWorkerService(self._config, job_service, persistence)
        context.provide(WORKSPACE_WORKERS, service)
        logger.info("workspace_remote_workers_started")


def feature() -> RemoteWorkerFeature:
    """Construct an unmounted RemoteWorkerFeature instance for bootstrapping.

    Returns:
        Configured RemoteWorkerFeature instance ready for registration.
    """
    return RemoteWorkerFeature()


__all__ = [
    "SPEC",
    "RemoteWorkerConfig",
    "RemoteWorkerFeature",
    "RemoteWorkerService",
    "feature",
]
