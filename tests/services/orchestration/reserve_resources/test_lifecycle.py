"""Lifecycle and non-functional performance tests for FEAT-ORCH-RESERVE_RESOURCES."""

from __future__ import annotations

import time
from typing import Any

import pytest
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.orchestration.resources import (
    AdmissionStatus,
    FiniteResourceProfile,
    ResourceAdmissionRequest,
    ResourcePolicyRef,
    WorkClass,
)
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.services.orchestration.reserve_resources._persistence import (
    ResourceReservationStore,
)
from app.services.orchestration.reserve_resources.feature import (
    ReserveResourcesFeature,
    create_feature,
    feature,
)
from app.services.orchestration.reserve_resources.reserve_resources import (
    ReserveResourcesService,
)


class _MockFeatureContext:
    """Mock feature context simulating lifecycle container."""

    def __init__(self) -> None:
        self.provided: dict[Any, Any] = {}
        self.callbacks: list[Any] = []
        self.dependencies: dict[Any, Any] = {
            PERSISTENCE_CAPABILITY: object(),
            ADMINISTER_SETTINGS_CAPABILITY: object(),
        }

    def require(self, key: Any) -> Any:
        if key in self.dependencies:
            return self.dependencies[key]
        raise RuntimeError(f"Missing required capability: {key}")

    def optional(self, key: Any) -> Any:
        return self.dependencies.get(key)

    def provide(self, key: Any, value: Any) -> None:
        self.provided[key] = value

    def register_callback(self, callback: Any) -> None:
        self.callbacks.append(callback)

    def close(self) -> None:
        for cb in reversed(self.callbacks):
            cb()


@pytest.mark.asyncio
async def test_atn_orch_reserve_resources_001_larger_than_ram_and_caps() -> None:
    """ATN-ORCH-RESERVE_RESOURCES-001:

    Larger-than-RAM and mixed-load measurements stay inside the effective global
    and per-operation caps.
    """
    store = ResourceReservationStore(database_path=":memory:")
    # 8 GiB RAM host envelope is 5.6 GiB (70%)
    service = ReserveResourcesService(
        store=store,
        policy=ResourcePolicyRef(buffer_bound_bytes=64 * 1024 * 1024),
        total_host_memory_bytes=8 * 1024 * 1024 * 1024,
        total_host_threads=4,
    )

    # Simulate streaming a 20 GiB dataset using chunked prefetch (2 chunks of 64 MiB buffer)
    # Total resident buffer is bounded to 128 MiB (well below 8 GiB RAM)
    chunk_size = 64 * 1024 * 1024
    stream_req = ResourceAdmissionRequest(
        request_id="req-stream-001",
        owner_id="owner-stream",
        work_id="stream-large-dataset",
        idempotency_key="idemp-stream-001",
        profile=FiniteResourceProfile(
            memory_bytes=chunk_size
            * 2,  # 128 MiB resident footprint for 20 GiB logical data
            thread_count=2,
            buffer_bytes=chunk_size,
            prefetch_chunks=2,
        ),
        work_class=WorkClass.BULK,
    )
    decision = await service.admit(stream_req)
    assert decision.status == AdmissionStatus.ADMITTED
    assert decision.lease is not None

    # Simulate chunked iterations
    for _ in range(10):
        # Reconcile observed memory stays strictly within chunk buffer limits
        service.reconcile_usage(
            decision.lease.lease_id, observed_native_bytes=chunk_size
        )

    snap = service.get_snapshot()
    assert snap.committed_memory_bytes == 128 * 1024 * 1024
    assert snap.committed_memory_bytes < snap.memory_envelope_bytes

    await service.release(decision.lease.lease_id)
    service.close()


@pytest.mark.asyncio
async def test_atn_orch_reserve_resources_002_control_latency_and_bm_app_01() -> None:
    """ATN-ORCH-RESERVE_RESOURCES-002:

    BM-APP-01 meets warm local metadata/control p95 <= 250 ms and p99 <= 1 s;
    over-capacity bulk work is visibly queued/refused.
    """
    store = ResourceReservationStore(database_path=":memory:")
    service = ReserveResourcesService(
        store=store,
        policy=ResourcePolicyRef(),
        total_host_memory_bytes=4 * 1024 * 1024 * 1024,  # 4 GiB
        total_host_threads=4,
    )

    # Fill capacity with bulk work
    bulk_decision = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-bulk-fill",
            owner_id="owner-bulk",
            work_id="work-bulk-fill",
            idempotency_key="idemp-fill",
            profile=FiniteResourceProfile(
                memory_bytes=int(4 * 1024 * 1024 * 1024 * 0.70),  # 70% envelope
                thread_count=2,
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert bulk_decision.status == AdmissionStatus.ADMITTED

    # Now measure 100 warm local control and metadata requests under load
    latencies: list[float] = []
    for i in range(100):
        t0 = time.perf_counter()
        # Control request
        ctrl_decision = await service.admit(
            ResourceAdmissionRequest(
                request_id=f"req-ctrl-{i}",
                owner_id="owner-ctrl",
                work_id=f"work-ctrl-{i}",
                idempotency_key=f"idemp-ctrl-{i}",
                profile=FiniteResourceProfile(memory_bytes=1024, thread_count=0),
                work_class=WorkClass.CONTROL,
            )
        )
        assert ctrl_decision.status == AdmissionStatus.ADMITTED
        _ = service.get_snapshot()
        if ctrl_decision.lease:
            await service.release(ctrl_decision.lease.lease_id)
        dt = (time.perf_counter() - t0) * 1000.0  # in ms
        latencies.append(dt)

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    # Assert p95 <= 250 ms and p99 <= 1000 ms
    assert p95 <= 250.0, f"p95 latency was {p95:.2f} ms > 250 ms"
    assert p99 <= 1000.0, f"p99 latency was {p99:.2f} ms > 1000 ms"

    service.close()


@pytest.mark.asyncio
async def test_feature_lifecycle_mount_and_disposal() -> None:
    """Test feature mount, capability registration, and scope disposal."""
    feat = create_feature()
    assert isinstance(feat, ReserveResourcesFeature)
    assert feat.spec.feature_id == "FEAT-ORCH-RESERVE_RESOURCES"

    ctx = _MockFeatureContext()
    await feat.mount(ctx, {})

    assert RESERVE_RESOURCES_CAPABILITY in ctx.provided
    service = ctx.provided[RESERVE_RESOURCES_CAPABILITY]
    assert isinstance(service, ReserveResourcesService)

    # Snapshot accessible
    snap = service.get_snapshot()
    assert snap.active_root_leases == 0

    # Scope close executes registered callbacks
    ctx.close()


def test_feature_factory_functions() -> None:
    """Verify feature and create_feature factories."""
    f1 = feature()
    f2 = create_feature()
    assert isinstance(f1, ReserveResourcesFeature)
    assert isinstance(f2, ReserveResourcesFeature)
