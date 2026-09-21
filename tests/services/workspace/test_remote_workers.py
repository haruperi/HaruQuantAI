"""Unit tests for the remote worker grid and leasing feature (FR-WORKSPACE-COOPERATIVE_CONTROL)."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.contracts.workspace import (
    WORKSPACE_WORKERS,
    GridNodeInfo,
    GridNodeState,
    JobDefinition,
    JobState,
    LeaseState,
    WorkerLeaseError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.workspace import (
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
    WorkspacePersistenceService,
)
from app.services.workspace.jobs import (
    JobConfig,
    JobService,
)
from app.services.workspace.jobs import (
    feature as jobs_feature,
)
from app.services.workspace.remote_workers import (
    SPEC,
    RemoteWorkerConfig,
    RemoteWorkerService,
)
from app.services.workspace.remote_workers import (
    feature as workers_feature,
)


@pytest.fixture
def persistence_service(
    tmp_path: pytest.TempPathFactory,
) -> Iterator[WorkspacePersistenceService]:
    """Create isolated SQLite persistence service for test duration."""
    db_file = str(tmp_path) + "/workspace_workers_test.db"
    config = WorkspacePersistenceConfig(db_path=db_file, wal_mode=True)
    svc = WorkspacePersistenceService(config)
    yield svc
    svc.close()


def _make_node(node_id: str, host: str = "127.0.0.1", port: int = 9000) -> GridNodeInfo:
    return GridNodeInfo(
        node_id=node_id,
        host=host,
        port=port,
        cores=8,
        memory_mb=16384,
        state=GridNodeState.ONLINE,
        last_heartbeat_utc=datetime.now(UTC),
    )


def _make_job(job_id: str) -> JobDefinition:
    return JobDefinition(
        job_id=job_id,
        group_id="grp",
        operation="run",
        priority=1,
        resource_class="cpu",
        config_hash="h",
        payload={},
        created_at_utc=datetime.now(UTC),
    )


def test_node_registration_and_heartbeat(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify node registration and liveness heartbeat updates."""
    job_service = JobService(JobConfig(), persistence_service)
    worker_svc = RemoteWorkerService(
        RemoteWorkerConfig(), job_service, persistence_service
    )

    node = _make_node("node-1")
    worker_svc.register_node(node)

    nodes = worker_svc.list_nodes()
    assert len(nodes) == 1
    assert nodes[0].node_id == "node-1"
    assert nodes[0].state == GridNodeState.ONLINE

    # Heartbeat
    assert worker_svc.heartbeat_node("node-1") is True
    assert worker_svc.heartbeat_node("node-unknown") is False


def test_job_lease_lifecycle(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify lease acquisition, busy state transition, and normal release."""
    job_service = JobService(JobConfig(), persistence_service)
    worker_svc = RemoteWorkerService(
        RemoteWorkerConfig(), job_service, persistence_service
    )

    node = _make_node("node-2")
    worker_svc.register_node(node)

    job = _make_job("job-lease-1")
    job_service.create_job(job)
    job_service.transition_state("job-lease-1", JobState.QUEUED, JobState.RUNNING)

    # Acquire lease for 100 seconds
    lease = worker_svc.acquire_lease("node-2", "job-lease-1", duration_seconds=100.0)
    assert lease.node_id == "node-2"
    assert lease.job_id == "job-lease-1"
    assert lease.expires_at_utc > lease.leased_at_utc

    # Node is now BUSY
    nodes = worker_svc.list_nodes()
    assert nodes[0].state == GridNodeState.BUSY

    # Duplicate lease on same job raises error
    with pytest.raises(WorkerLeaseError, match="already actively leased"):
        worker_svc.acquire_lease("node-2", "job-lease-1", duration_seconds=100.0)

    # Release lease
    worker_svc.release_lease(lease.lease_id, completed=True)

    # Node reverts to ONLINE
    nodes = worker_svc.list_nodes()
    assert nodes[0].state == GridNodeState.ONLINE


def test_lease_reconciliation_on_timeout(
    persistence_service: WorkspacePersistenceService,
) -> None:
    """Verify expired worker leases are revoked and jobs marked INTERRUPTED."""
    job_service = JobService(JobConfig(), persistence_service)
    worker_svc = RemoteWorkerService(
        RemoteWorkerConfig(), job_service, persistence_service
    )

    node = _make_node("node-3")
    worker_svc.register_node(node)

    job = _make_job("job-timeout-1")
    job_service.create_job(job)
    job_service.transition_state("job-timeout-1", JobState.QUEUED, JobState.RUNNING)

    # Acquire micro-lease (0.01s)
    lease = worker_svc.acquire_lease("node-3", "job-timeout-1", duration_seconds=0.01)
    assert lease.state == LeaseState.ACTIVE
    time.sleep(0.05)

    # Reconcile expired leases
    reclaimed = worker_svc.reconcile_expired_leases()
    assert reclaimed == 1

    # Associated job is now interrupted
    receipt = job_service.get_receipt("job-timeout-1")
    assert receipt is not None
    assert receipt.state == JobState.INTERRUPTED

    # Node reverts to ONLINE
    nodes = worker_svc.list_nodes()
    assert nodes[0].state == GridNodeState.ONLINE


def test_remote_workers_lifecycle_within_runtime(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """Verify feature boots inside Runtime and provides WORKSPACE_WORKERS."""
    db_file = str(tmp_path) + "/workers_rt.db"

    def _persistence_factory() -> WorkspacePersistenceFeature:
        return WorkspacePersistenceFeature(WorkspacePersistenceConfig(db_path=db_file))

    feat = workers_feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime(
            (_persistence_factory, jobs_feature, workers_feature)
        ) as runtime:
            rws = runtime.require(WORKSPACE_WORKERS)
            assert len(rws.list_nodes()) == 0

    asyncio.run(_test())


def test_remote_workers_config_validation() -> None:
    """Verify bounds enforcement on RemoteWorkerConfig."""
    with pytest.raises(ValueError, match="node_heartbeat_timeout_s"):
        RemoteWorkerConfig(node_heartbeat_timeout_s=0.0)

    with pytest.raises(ValueError, match="default_lease_duration_s"):
        RemoteWorkerConfig(default_lease_duration_s=-1.0)

    valid = RemoteWorkerConfig(
        node_heartbeat_timeout_s=30.0, default_lease_duration_s=120.0
    )
    assert valid.node_heartbeat_timeout_s == 30.0
    assert valid.default_lease_duration_s == 120.0
