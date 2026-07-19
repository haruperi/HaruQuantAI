"""Atomic persistence coordination for complete Optimization results."""

from __future__ import annotations

from app.services.optimization.errors import OptimizationError
from app.services.optimization.evidence import OptimizationResult  # noqa: TC001
from app.services.optimization.state.contracts import (
    OptimizationPersistenceReceipt,  # noqa: TC001
    OptimizationStateStore,  # noqa: TC001
)
from app.services.optimization.state.stores import _validate_receipt
from app.utils import logger


def persist_optimization_result(
    result: OptimizationResult,
    store: OptimizationStateStore,
) -> OptimizationPersistenceReceipt:
    """Atomically persist a result with its ranked-candidate evidence.

    Args:
        result: Canonical Optimization result version one.
        store: Injected Optimization state port.

    Returns:
        Exact durable persistence receipt.

    Raises:
        OptimizationError: If the write fails or confirmation conflicts.
    """
    logger.info("Persisting canonical Optimization result atomically")
    try:
        receipt = store.save_result(result, result.ranked_candidates)
    except Exception as exc:
        raise OptimizationError(
            "OPT_PERSISTENCE_FAILED", "RESULT_WRITE_FAILED"
        ) from exc
    return _validate_receipt(
        receipt,
        search_id=result.search_id,
        reproducibility_hash=result.reproducibility_hash,
    )


__all__ = ["persist_optimization_result"]
