"""Integration tests for Distributed Worker Pool lifecycle and scheduling."""

from __future__ import annotations

import uuid

import pytest
from app.contracts.workspace.models import (
    ArtifactChunk,
    ArtifactManifest,
    WorkerCapabilityDescriptor,
)
from app.services.workspace.distributed_worker_pool.distributed_worker_pool import (
    DistributedWorkerPoolService,
    fr_ws_register_worker_capabilities,
    fr_ws_schedule_data_locality,
    fr_ws_secure_remote_workers,
    fr_ws_verify_artifact_transfer,
)


@pytest.mark.asyncio
async def test_distributed_worker_pool_end_to_end_lifecycle() -> None:
    """Verify multi-worker registration, lease fencing, locality scheduling, and artifact transfer."""
    service = DistributedWorkerPoolService()

    hash_a = "a" * 64
    hash_b = "b" * 64

    # 1. Register 2 workers
    desc1 = WorkerCapabilityDescriptor(
        capabilities=("workspace.distribute-workers@1",),
        build_hash="1" * 64,
        os_family="LINUX",
        architecture="X86_64",
        cpu_cores=8,
        memory_mb=16384,
        artifact_locality=(hash_a, hash_b),
        heartbeat_interval_seconds=60,
    )
    reg1 = await fr_ws_register_worker_capabilities(
        service, desc1, "https://node-1.cluster:8000"
    )

    desc2 = WorkerCapabilityDescriptor(
        capabilities=("workspace.distribute-workers@1",),
        build_hash="2" * 64,
        os_family="LINUX",
        architecture="X86_64",
        cpu_cores=4,
        memory_mb=8192,
        artifact_locality=(hash_a,),
        heartbeat_interval_seconds=60,
    )
    _ = await fr_ws_register_worker_capabilities(
        service, desc2, "https://node-2.cluster:8000"
    )

    job_id = str(uuid.uuid7())

    # 2. Authenticate and acquire lease on Worker 1
    lease1 = await fr_ws_secure_remote_workers(service, reg1.worker_id, job_id, 1)
    assert lease1.fencing_token == 1

    # 3. Schedule task with locality hints
    task_run_id = str(uuid.uuid7())
    envelope = await fr_ws_schedule_data_locality(
        service,
        job_id=job_id,
        attempt_no=1,
        task_run_id=task_run_id,
        locality_hints=(hash_a, hash_b),
    )
    assert envelope.assigned_worker_id == reg1.worker_id

    # 4. Prepare and commit artifact transfer
    chunk = ArtifactChunk(index=0, offset_bytes=0, size_bytes=2048, chunk_hash="f" * 64)
    staged = ArtifactManifest(
        artifact_id=str(uuid.uuid7()),
        kind="CHECKPOINT",
        content_hash="9" * 64,
        size_bytes=2048,
        media_type="application/octet-stream",
        artifact_schema_version=1,
        state="STAGED",
        chunks=(chunk,),
        created_at=reg1.registered_at,
    )
    committed = await fr_ws_verify_artifact_transfer(
        service,
        artifact=staged,
        job_id=job_id,
        attempt_no=1,
        fencing_token=lease1.fencing_token,
    )
    assert committed.state == "COMMITTED"
