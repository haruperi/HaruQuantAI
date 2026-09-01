"""Unit tests for DistributedWorkerPoolService and FR-WS Functional Requirements."""

from __future__ import annotations

import uuid

import pytest
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    ArtifactChunk,
    ArtifactManifest,
    DistributeWorkersRequest,
    DistributeWorkersSuccess,
    WorkerCapabilityDescriptor,
)
from app.services.workspace.distributed_worker_pool.distributed_worker_pool import (
    DistributedWorkerPoolService,
    fr_ws_register_worker_capabilities,
    fr_ws_schedule_data_locality,
    fr_ws_secure_remote_workers,
    fr_ws_verify_artifact_transfer,
)


def _make_descriptor(
    capabilities: tuple[str, ...] = ("workspace.distribute-workers@1",),
    build_hash: str = "a" * 64,
    artifact_locality: tuple[str, ...] = (),
    heartbeat_interval: int = 30,
) -> WorkerCapabilityDescriptor:
    return WorkerCapabilityDescriptor(
        capabilities=capabilities,
        build_hash=build_hash,
        os_family="LINUX",
        architecture="X86_64",
        cpu_cores=4,
        memory_mb=8192,
        artifact_locality=artifact_locality,
        heartbeat_interval_seconds=heartbeat_interval,
    )


@pytest.mark.asyncio
async def test_ws_register_worker_capabilities() -> None:
    """Verify FR-WS-REGISTER_WORKER_CAPABILITIES behavior and invariants."""
    service = DistributedWorkerPoolService()
    desc = _make_descriptor(heartbeat_interval=30)
    endpoint = "https://worker-1.local:9000"

    reg = await fr_ws_register_worker_capabilities(service, desc, endpoint)
    assert bool(reg.worker_id)
    assert reg.endpoint == endpoint
    assert not reg.trusted  # Registration alone confers no trust
    assert reg.registered_at == reg.last_heartbeat_at
    assert reg.heartbeat_expires_at > reg.last_heartbeat_at

    # Heartbeat renewal
    hb_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="HEARTBEAT",
        worker_id=reg.worker_id,
    )
    hb_res = await service.distribute_workers(hb_req)
    assert isinstance(hb_res, DistributeWorkersSuccess)
    assert hb_res.registration is not None
    assert hb_res.registration.worker_id == reg.worker_id

    # Unknown worker heartbeat fails
    bad_hb_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="HEARTBEAT",
        worker_id=str(uuid.uuid7()),
    )
    bad_hb_res = await service.distribute_workers(bad_hb_req)
    assert isinstance(bad_hb_res, WorkspaceFailure)
    assert bad_hb_res.code == "WORKER_UNKNOWN"


@pytest.mark.asyncio
async def test_ws_secure_remote_workers() -> None:
    """Verify FR-WS-SECURE_REMOTE_WORKERS authentication, leases, and fencing tokens."""
    service = DistributedWorkerPoolService()
    desc = _make_descriptor()
    reg = await fr_ws_register_worker_capabilities(
        service, desc, "https://worker-sec.local:9000"
    )
    job_id = str(uuid.uuid7())

    # Attempting to acquire lease before authentication fails (WORKER_UNTRUSTED)
    untrusted_lease_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="ACQUIRE_LEASE",
        worker_id=reg.worker_id,
        job_id=job_id,
        attempt_no=1,
    )
    untrusted_res = await service.distribute_workers(untrusted_lease_req)
    assert isinstance(untrusted_res, WorkspaceFailure)
    assert untrusted_res.code == "WORKER_UNTRUSTED"

    # Authenticate worker
    lease = await fr_ws_secure_remote_workers(service, reg.worker_id, job_id, 1)
    assert lease.worker_id == reg.worker_id
    assert lease.job_id == job_id
    assert lease.attempt_no == 1
    assert lease.fencing_token == 1
    assert lease.state == "ACTIVE"

    # Re-acquiring lease increments fencing token and supersedes prior lease
    lease2_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="ACQUIRE_LEASE",
        worker_id=reg.worker_id,
        job_id=job_id,
        attempt_no=1,
    )
    lease2_res = await service.distribute_workers(lease2_req)
    assert isinstance(lease2_res, DistributeWorkersSuccess)
    assert lease2_res.lease is not None
    assert lease2_res.lease.fencing_token == 2
    assert lease2_res.lease.state == "ACTIVE"

    # Releasing under old stale token fails with LEASE_TOKEN_STALE
    stale_release_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RELEASE_LEASE",
        worker_id=reg.worker_id,
        job_id=job_id,
        attempt_no=1,
        fencing_token=1,
    )
    stale_release_res = await service.distribute_workers(stale_release_req)
    assert isinstance(stale_release_res, WorkspaceFailure)
    assert stale_release_res.code == "LEASE_TOKEN_STALE"

    # Releasing under current active token succeeds
    valid_release_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RELEASE_LEASE",
        worker_id=reg.worker_id,
        job_id=job_id,
        attempt_no=1,
        fencing_token=2,
    )
    valid_release_res = await service.distribute_workers(valid_release_req)
    assert isinstance(valid_release_res, DistributeWorkersSuccess)
    assert valid_release_res.lease is not None
    assert valid_release_res.lease.state == "RELEASED"


@pytest.mark.asyncio
async def test_ws_schedule_data_locality() -> None:
    """Verify FR-WS-SCHEDULE_DATA_LOCALITY priority ordering and task semantics."""
    service = DistributedWorkerPoolService()
    hash_1 = "1" * 64
    hash_2 = "2" * 64

    # Worker A has locality for both hash_1 and hash_2
    desc_a = _make_descriptor(artifact_locality=(hash_1, hash_2))
    reg_a = await fr_ws_register_worker_capabilities(
        service, desc_a, "https://worker-a:9000"
    )
    await fr_ws_secure_remote_workers(service, reg_a.worker_id, str(uuid.uuid7()), 1)

    # Worker B has locality for hash_1 only
    desc_b = _make_descriptor(artifact_locality=(hash_1,))
    reg_b = await fr_ws_register_worker_capabilities(
        service, desc_b, "https://worker-b:9000"
    )
    await fr_ws_secure_remote_workers(service, reg_b.worker_id, str(uuid.uuid7()), 1)

    # Schedule task with locality hints (hash_1, hash_2) -> Worker A must be selected
    job_id = str(uuid.uuid7())
    task_run_id = str(uuid.uuid7())
    envelope = await fr_ws_schedule_data_locality(
        service,
        job_id=job_id,
        attempt_no=1,
        task_run_id=task_run_id,
        locality_hints=(hash_1, hash_2),
    )
    assert envelope.assigned_worker_id == reg_a.worker_id
    assert envelope.input_hashes == (hash_1, hash_2)

    # Reassignment to another compatible worker preserves invariant input hashes
    envelope2 = await fr_ws_schedule_data_locality(
        service,
        job_id=job_id,
        attempt_no=2,
        task_run_id=task_run_id,
        locality_hints=(hash_1, hash_2),
    )
    assert envelope2.input_hashes == envelope.input_hashes
    assert envelope2.job_id == envelope.job_id
    assert envelope2.task_run_id == envelope.task_run_id

    # If required capability is missing, scheduling fails with CAPABILITY_UNAVAILABLE
    missing_cap_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="ASSIGN_TASK",
        job_id=job_id,
        attempt_no=3,
        task_run_id=str(uuid.uuid7()),
        required_capabilities=("workspace.custom-engine@99",),
    )
    missing_cap_res = await service.distribute_workers(missing_cap_req)
    assert isinstance(missing_cap_res, WorkspaceFailure)
    assert missing_cap_res.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_ws_verify_artifact_transfer() -> None:
    """Verify FR-WS-VERIFY_ARTIFACT_TRANSFER chunk plans, validation, and commit states."""
    service = DistributedWorkerPoolService()
    desc = _make_descriptor()
    reg = await fr_ws_register_worker_capabilities(
        service, desc, "https://worker-art:9000"
    )
    job_id = str(uuid.uuid7())
    lease = await fr_ws_secure_remote_workers(service, reg.worker_id, job_id, 1)

    content_hash = "c" * 64
    chunk0 = ArtifactChunk(index=0, offset_bytes=0, size_bytes=512, chunk_hash="0" * 64)
    chunk1 = ArtifactChunk(
        index=1, offset_bytes=512, size_bytes=512, chunk_hash="1" * 64
    )

    staged = ArtifactManifest(
        artifact_id=str(uuid.uuid7()),
        kind="DATASET",
        content_hash=content_hash,
        size_bytes=1024,
        media_type="application/parquet",
        artifact_schema_version=1,
        state="STAGED",
        chunks=(chunk0, chunk1),
        created_at=reg.registered_at,
    )

    committed = await fr_ws_verify_artifact_transfer(
        service,
        artifact=staged,
        job_id=job_id,
        attempt_no=1,
        fencing_token=lease.fencing_token,
    )
    assert committed.state == "COMMITTED"
    assert committed.committed_at is not None
    assert committed.size_bytes == 1024

    # Commit with stale fencing token fails with LEASE_TOKEN_STALE
    stale_commit_req = DistributeWorkersRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="COMMIT_TRANSFER",
        artifact_id=staged.artifact_id,
        job_id=job_id,
        attempt_no=1,
        fencing_token=999,
    )
    stale_commit_res = await service.distribute_workers(stale_commit_req)
    assert isinstance(stale_commit_res, WorkspaceFailure)
    assert stale_commit_res.code == "LEASE_TOKEN_STALE"
