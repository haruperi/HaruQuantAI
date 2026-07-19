"""Tests for atomic Optimization result persistence."""

# ruff: noqa: INP001

from app.services.optimization.evidence import build_optimization_evidence
from app.services.optimization.state import persist_optimization_result
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_state_contracts import MemoryOptimizationStore


def test_result_success_requires_atomic_receipt() -> None:
    """Durable success pairs canonical result and ranked evidence atomically."""
    result = build_optimization_evidence(evidence_request())
    store = MemoryOptimizationStore()
    receipt = persist_optimization_result(result, store)
    assert receipt.durable is True
    assert store.results[result.search_id] == result
