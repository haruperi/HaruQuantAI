"""Integration test for Optimization checkpoint and result persistence."""

# ruff: noqa: INP001

from app.services.optimization.evidence import build_optimization_evidence
from app.services.optimization.state import (
    load_search_checkpoint,
    persist_optimization_result,
    save_search_checkpoint,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_state_contracts import (
    MemoryOptimizationStore,
    checkpoint,
)


def test_state_workflow_confirms_checkpoint_and_result_durability() -> None:
    """One injected store confirms exact checkpoint and result identities."""
    store = MemoryOptimizationStore()
    value = checkpoint()
    save_search_checkpoint(value, store)
    recovered = load_search_checkpoint(
        search_id=value.search_id,
        reproducibility_hash=value.reproducibility_hash,
        store=store,
    )
    result = build_optimization_evidence(evidence_request())
    receipt = persist_optimization_result(result, store)
    assert recovered == value
    assert receipt.reproducibility_hash == result.reproducibility_hash
