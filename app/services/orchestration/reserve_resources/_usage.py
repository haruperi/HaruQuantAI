"""Offline usage demonstration for finite resource admission."""

from __future__ import annotations

import asyncio
import json

from app.composition.logging import get_logger
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

logger = get_logger("orchestration.reserve_resources._usage")


async def _demo_hierarchical_leases(
    service: ReserveResourcesService, results: dict[str, object]
) -> tuple[str, str]:
    """Demonstrate admitting a parent lease and a child lease.

    Args:
        service: Active resource reservation service.
        results: Dictionary collecting demonstration outputs.

    Returns:
        Tuple of (root_lease_id, child_a_lease_id).

    Raises:
        RuntimeError: If admission does not succeed as expected.
    """
    root_req = ResourceAdmissionRequest(
        request_id="req-root-001",
        owner_id="owner-demo",
        work_id="job-parent",
        idempotency_key="idemp-root-001",
        profile=FiniteResourceProfile(
            memory_bytes=4 * 1024 * 1024 * 1024,
            thread_count=4,
            temp_disk_bytes=2 * 1024 * 1024 * 1024,
        ),
        work_class=WorkClass.BULK,
    )
    root_decision = await service.admit(root_req)
    if root_decision.status != AdmissionStatus.ADMITTED or root_decision.lease is None:
        msg = "Root admission failed unexpectedly"
        raise RuntimeError(msg)
    root_lease_id = root_decision.lease.lease_id
    results["root_admission"] = {
        "status": root_decision.status.value,
        "lease_id": root_lease_id,
        "committed_memory_bytes": service.get_snapshot().committed_memory_bytes,
    }

    child_a_req = ResourceAdmissionRequest(
        request_id="req-child-001",
        owner_id="owner-demo",
        work_id="job-child-a",
        idempotency_key="idemp-child-001",
        parent_lease_id=root_lease_id,
        profile=FiniteResourceProfile(
            memory_bytes=2 * 1024 * 1024 * 1024,
            thread_count=2,
            temp_disk_bytes=1 * 1024 * 1024 * 1024,
        ),
        work_class=WorkClass.BULK,
    )
    child_a_decision = await service.admit(child_a_req)
    if (
        child_a_decision.status != AdmissionStatus.ADMITTED
        or child_a_decision.lease is None
    ):
        msg = "Child admission failed unexpectedly"
        raise RuntimeError(msg)
    snap = service.get_snapshot()
    if snap.committed_memory_bytes != 4 * 1024 * 1024 * 1024:
        msg = "Global commitment should not double-spend child allocation"
        raise RuntimeError(msg)
    child_a_lease_id = child_a_decision.lease.lease_id
    results["child_a_admission"] = {
        "status": child_a_decision.status.value,
        "lease_id": child_a_lease_id,
        "global_committed_memory_bytes": snap.committed_memory_bytes,
    }
    return root_lease_id, child_a_lease_id


async def _demo_rejections(
    service: ReserveResourcesService,
    root_lease_id: str,
    results: dict[str, object],
) -> None:
    """Demonstrate refusals for parent headroom, negative values, and disk limits.

    Args:
        service: Active resource reservation service.
        root_lease_id: Admitted root lease ID.
        results: Dictionary collecting demonstration outputs.

    Raises:
        RuntimeError: If rejection behavior fails to trigger as expected.
    """
    child_b_req = ResourceAdmissionRequest(
        request_id="req-child-002",
        owner_id="owner-demo",
        work_id="job-child-b",
        idempotency_key="idemp-child-002",
        parent_lease_id=root_lease_id,
        profile=FiniteResourceProfile(
            memory_bytes=3 * 1024 * 1024 * 1024,
            thread_count=2,
        ),
        work_class=WorkClass.BULK,
    )
    child_b_decision = await service.admit(child_b_req)
    if child_b_decision.status != AdmissionStatus.REFUSED:
        msg = "Child B should be refused due to parent envelope exhaustion"
        raise RuntimeError(msg)
    results["child_b_headroom_refusal"] = {
        "status": child_b_decision.status.value,
        "reason": child_b_decision.reason,
    }

    try:
        FiniteResourceProfile(memory_bytes=-1024)
        negative_rejected = False
    except ValueError:
        negative_rejected = True
    if not negative_rejected:
        msg = "Negative profile did not raise ValueError"
        raise RuntimeError(msg)
    results["negative_cap_rejected"] = True

    large_disk_req = ResourceAdmissionRequest(
        request_id="req-disk-001",
        owner_id="owner-demo",
        work_id="job-disk-overflow",
        idempotency_key="idemp-disk-001",
        profile=FiniteResourceProfile(
            temp_disk_bytes=12 * 1024 * 1024 * 1024,
        ),
        work_class=WorkClass.BULK,
    )
    disk_decision = await service.admit(large_disk_req)
    if disk_decision.status != AdmissionStatus.REFUSED:
        msg = "Disk request exceeding headroom should be refused"
        raise RuntimeError(msg)
    results["disk_headroom_refusal"] = {
        "status": disk_decision.status.value,
        "reason": disk_decision.reason,
    }


async def _demo_cleanup(
    service: ReserveResourcesService,
    child_lease_id: str,
    root_lease_id: str,
    results: dict[str, object],
) -> None:
    """Demonstrate releasing child and parent leases.

    Args:
        service: Active resource reservation service.
        child_lease_id: Child lease ID to release.
        root_lease_id: Root lease ID to release.
        results: Dictionary collecting demonstration outputs.

    Raises:
        RuntimeError: If lease release fails.
    """
    released_child = await service.release(child_lease_id)
    released_root = await service.release(root_lease_id)
    if not (released_child and released_root):
        msg = "Failed to release active leases"
        raise RuntimeError(msg)
    final_snap = service.get_snapshot()
    if final_snap.committed_memory_bytes != 0:
        msg = "Committed memory should be 0 after releases"
        raise RuntimeError(msg)
    results["cleanup"] = {
        "final_committed_memory_bytes": final_snap.committed_memory_bytes,
        "active_root_leases": final_snap.active_root_leases,
    }


async def run_usage() -> dict[str, object]:
    """Execute the bounded offline resource admission demonstration.

    Returns:
        Dictionary of demonstrated outcomes and assertions.

    Raises:
        RuntimeError: If unexpected admission behavior occurs.
    """
    logger.info("Starting resource admission usage demonstration")
    store = ResourceReservationStore(database_path=":memory:")
    total_mem = 16 * 1024 * 1024 * 1024
    service = ReserveResourcesService(
        store=store,
        policy=ResourcePolicyRef(),
        total_host_memory_bytes=total_mem,
        total_host_threads=8,
        total_disk_bytes=100 * 1024 * 1024 * 1024,
        free_disk_bytes=40 * 1024 * 1024 * 1024,
    )

    results: dict[str, object] = {}
    root_id, child_id = await _demo_hierarchical_leases(service, results)
    await _demo_rejections(service, root_id, results)
    await _demo_cleanup(service, child_id, root_id, results)

    service.close()
    logger.info("Completed resource admission usage demonstration successfully")
    return results


def main() -> None:
    """Run the usage demonstration as a script."""
    results = asyncio.run(run_usage())
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
