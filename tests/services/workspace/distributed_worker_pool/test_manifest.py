"""Unit tests for Distributed Worker Pool manifest."""

from app.contracts.workspace.capabilities import DISTRIBUTE_WORKERS_CAPABILITY
from app.services.workspace.distributed_worker_pool.manifest import SPEC


def test_manifest_specification_invariants() -> None:
    """Verify SPEC fields and capability declaration."""
    assert SPEC.feature_id == "FEAT-WS-DISTRIBUTE_WORKERS"
    assert SPEC.domain == "workspace"
    assert DISTRIBUTE_WORKERS_CAPABILITY in SPEC.provides
    assert len(SPEC.provides) == 1
    assert len(SPEC.requires) == 0
    assert len(SPEC.conflicts) == 0
    assert SPEC.state is None
