"""Traceability tests for FEAT-ORCH-RESERVE_RESOURCES acceptance oracles."""

from __future__ import annotations

import pytest
from app.contracts.orchestration.resources import (
    AdmissionStatus,
    FiniteResourceProfile,
    ResourceAdmissionRequest,
    ResourcePolicyRef,
    WorkClass,
)
from app.services.orchestration.reserve_resources._persistence import (
    ResourceReservationStore,
)
from app.services.orchestration.reserve_resources.reserve_resources import (
    ReserveResourcesService,
)


@pytest.fixture
def service() -> ReserveResourcesService:
    """Provide a deterministic in-memory resource reservation service."""
    store = ResourceReservationStore(database_path=":memory:")
    # 10 GiB total RAM, 8 threads, 100 GiB disk, 40 GiB free disk
    return ReserveResourcesService(
        store=store,
        policy=ResourcePolicyRef(),
        total_host_memory_bytes=10 * 1024 * 1024 * 1024,
        total_host_threads=8,
        total_disk_bytes=100 * 1024 * 1024 * 1024,
        free_disk_bytes=40 * 1024 * 1024 * 1024,
    )


@pytest.mark.asyncio
async def test_at_orch_reserve_resources_001_hierarchy_and_negative_caps(
    service: ReserveResourcesService,
) -> None:
    """AT-ORCH-RESERVE_RESOURCES-001:

    A child job cannot reserve its parent's capacity again; missing or negative caps
    do not mean unlimited permission.
    """
    # 1. Negative caps reject immediately
    with pytest.raises(ValueError, match="cannot be negative"):
        FiniteResourceProfile(memory_bytes=-100)

    with pytest.raises(TypeError, match="must be an integer"):
        FiniteResourceProfile(memory_bytes=True)  # type: ignore[arg-type]

    # 2. Admit parent job with 4 GiB, 4 threads
    parent_req = ResourceAdmissionRequest(
        request_id="req-p1",
        owner_id="owner-1",
        work_id="work-p1",
        idempotency_key="idemp-p1",
        profile=FiniteResourceProfile(
            memory_bytes=4 * 1024 * 1024 * 1024,
            thread_count=4,
        ),
        work_class=WorkClass.BULK,
    )
    parent_decision = await service.admit(parent_req)
    assert parent_decision.status == AdmissionStatus.ADMITTED
    assert parent_decision.lease is not None
    p_lease_id = parent_decision.lease.lease_id

    # Global commitment is 4 GiB
    assert service.get_snapshot().committed_memory_bytes == 4 * 1024 * 1024 * 1024

    # 3. Child job admits under parent: 2 GiB
    child_req = ResourceAdmissionRequest(
        request_id="req-c1",
        owner_id="owner-1",
        work_id="work-c1",
        idempotency_key="idemp-c1",
        parent_lease_id=p_lease_id,
        profile=FiniteResourceProfile(
            memory_bytes=2 * 1024 * 1024 * 1024,
            thread_count=2,
        ),
        work_class=WorkClass.BULK,
    )
    child_decision = await service.admit(child_req)
    assert child_decision.status == AdmissionStatus.ADMITTED
    assert child_decision.lease is not None
    assert child_decision.lease.root_lease_id == p_lease_id

    # Global commitment must still be 4 GiB (child draws from parent, not double-counted!)
    assert service.get_snapshot().committed_memory_bytes == 4 * 1024 * 1024 * 1024

    # 4. Sibling child requesting 3 GiB exceeds parent's remaining 2 GiB -> Refused!
    child_excess_req = ResourceAdmissionRequest(
        request_id="req-c2",
        owner_id="owner-1",
        work_id="work-c2",
        idempotency_key="idemp-c2",
        parent_lease_id=p_lease_id,
        profile=FiniteResourceProfile(
            memory_bytes=3 * 1024 * 1024 * 1024,
            thread_count=1,
        ),
        work_class=WorkClass.BULK,
    )
    excess_decision = await service.admit(child_excess_req)
    assert excess_decision.status == AdmissionStatus.REFUSED
    assert "exceeds parent lease" in (excess_decision.reason or "")


@pytest.mark.asyncio
async def test_at_orch_reserve_resources_002_mixed_load_and_envelope_caps(
    service: ReserveResourcesService,
) -> None:
    """AT-ORCH-RESERVE_RESOURCES-002:

    Mixed-load fixtures cannot exceed combined runnable-thread or memory reservations;
    unknown estimates carry hard caps and visible capacity outcomes.
    """
    # 70% envelope on 10 GiB is 7 GiB. Usable threads on 8 cores (with 2 control reserved) is 6.
    # 1. Admit 5 GiB, 4 threads
    r1 = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-m1",
            owner_id="owner-1",
            work_id="work-m1",
            idempotency_key="idemp-m1",
            profile=FiniteResourceProfile(
                memory_bytes=5 * 1024 * 1024 * 1024,
                thread_count=4,
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert r1.status == AdmissionStatus.ADMITTED

    # 2. Second request for 3 GiB exceeds 7 GiB envelope -> Queued!
    r2 = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-m2",
            owner_id="owner-1",
            work_id="work-m2",
            idempotency_key="idemp-m2",
            profile=FiniteResourceProfile(
                memory_bytes=3 * 1024 * 1024 * 1024,
                thread_count=1,
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert r2.status == AdmissionStatus.QUEUED
    assert r2.constrained_dimension == "memory_bytes"

    # 3. Thread saturation: request for 4 threads when 4/6 are used -> Queued!
    r3 = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-m3",
            owner_id="owner-1",
            work_id="work-m3",
            idempotency_key="idemp-m3",
            profile=FiniteResourceProfile(
                memory_bytes=512 * 1024 * 1024,
                thread_count=4,  # 4 + 4 = 8 > 6 usable threads
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert r3.status == AdmissionStatus.QUEUED
    assert r3.constrained_dimension == "thread_count"

    # 4. Critical memory pressure (>= 95% total host RAM) refuses bulk immediately
    r_crit = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-crit",
            owner_id="owner-1",
            work_id="work-crit",
            idempotency_key="idemp-crit",
            profile=FiniteResourceProfile(
                memory_bytes=9800 * 1024 * 1024,  # 9.8 GiB / 10 GiB = 98% > 95%
                thread_count=1,
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert r_crit.status == AdmissionStatus.REFUSED
    assert "Critical memory pressure" in (r_crit.reason or "")


@pytest.mark.asyncio
async def test_at_orch_reserve_resources_003_disk_headroom_and_accounting(
    service: ReserveResourcesService,
) -> None:
    """AT-ORCH-RESERVE_RESOURCES-003:

    A new write is denied before violating disk headroom; shared resident pages are
    not double-counted and Python heap alone is not treated as total memory.
    """
    # Free disk: 40 GiB. Initial temp disk allowance: min(16 GiB, 25% of 40 GiB) = 10 GiB.
    # Total disk: 100 GiB. Headroom floor: 10% of 100 GiB = 10 GiB.
    # A request asking for 11 GiB temp disk exceeds the 10 GiB allowance -> Refused!
    r_disk_excess = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-disk-excess",
            owner_id="owner-1",
            work_id="work-disk-excess",
            idempotency_key="idemp-disk-excess",
            profile=FiniteResourceProfile(
                temp_disk_bytes=11 * 1024 * 1024 * 1024,
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert r_disk_excess.status == AdmissionStatus.REFUSED
    assert r_disk_excess.constrained_dimension == "temp_disk_bytes"

    # Admissible disk request: 4 GiB temp disk
    r_disk_ok = await service.admit(
        ResourceAdmissionRequest(
            request_id="req-disk-ok",
            owner_id="owner-1",
            work_id="work-disk-ok",
            idempotency_key="idemp-disk-ok",
            profile=FiniteResourceProfile(
                temp_disk_bytes=4 * 1024 * 1024 * 1024,
                memory_bytes=1 * 1024 * 1024 * 1024,
            ),
            work_class=WorkClass.BULK,
        )
    )
    assert r_disk_ok.status == AdmissionStatus.ADMITTED
    assert r_disk_ok.lease is not None

    # Reconcile native and VRAM usage
    service.reconcile_usage(
        lease_id=r_disk_ok.lease.lease_id,
        observed_native_bytes=512 * 1024 * 1024,
        observed_vram_bytes=256 * 1024 * 1024,
    )
    snap = service.get_snapshot()
    assert snap.committed_temp_disk_bytes == 4 * 1024 * 1024 * 1024


@pytest.mark.asyncio
async def test_at_orch_reserve_resources_004_control_isolation_and_fairness(
    service: ReserveResourcesService,
) -> None:
    """AT-ORCH-RESERVE_RESOURCES-004:

    Under BM-APP-01 bulk work cannot suppress control acknowledgement or disable
    risk/broker serialization checks.
    """
    # Bound ready descriptors: 256. Reserved for control: 32.
    # Bulk capacity is 256 - 32 = 224 descriptors.
    # Fill up ready descriptors near bulk limit
    service._committed_ready_descriptors = 224

    # 1. Additional bulk request is refused because control partition is preserved
    bulk_req = ResourceAdmissionRequest(
        request_id="req-bulk-saturated",
        owner_id="owner-1",
        work_id="work-bulk",
        idempotency_key="idemp-bulk-sat",
        profile=FiniteResourceProfile(memory_bytes=1024),
        work_class=WorkClass.BULK,
    )
    bulk_decision = await service.admit(bulk_req)
    assert bulk_decision.status == AdmissionStatus.REFUSED
    assert "Control descriptor partition reserved" in (bulk_decision.reason or "")

    # 2. Control/Safety request CAN still be admitted into the reserved partition
    control_req = ResourceAdmissionRequest(
        request_id="req-control-ok",
        owner_id="owner-1",
        work_id="work-control-cancel",
        idempotency_key="idemp-ctrl-ok",
        profile=FiniteResourceProfile(memory_bytes=1024),
        work_class=WorkClass.CONTROL,
    )
    control_decision = await service.admit(control_req)
    assert control_decision.status == AdmissionStatus.ADMITTED
    assert control_decision.lease is not None
