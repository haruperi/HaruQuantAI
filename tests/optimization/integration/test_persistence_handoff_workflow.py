"""WF-OPT-006 evidence and persistence handoff integration."""

# ruff: noqa: INP001
from app.services.optimization import (
    build_optimization_handoff,
    persist_optimization_result,
)
from app.utils import get_logger
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_state_contracts import MemoryOptimizationStore

logger = get_logger(__name__)


def test_evidence_handoff_is_durable_only_after_receipt() -> None:
    """Canonical handoff and ranked evidence receive atomic confirmation."""
    logger.debug("Testing WF-OPT-006 evidence persistence handoff")
    response = build_optimization_handoff(evidence_request())
    assert response.data is not None
    result = response.data
    receipt = persist_optimization_result(result, MemoryOptimizationStore())
    assert receipt.durable is True
    assert receipt.reproducibility_hash == result.reproducibility_hash
