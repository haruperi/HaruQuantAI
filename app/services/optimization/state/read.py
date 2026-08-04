"""Read-side invocation of injected Optimization-owned state operations."""

from __future__ import annotations

from app.services.optimization.errors import OptimizationError
from app.services.optimization.evidence import OptimizationResult  # noqa: TC001
from app.services.optimization.state.contracts import (
    OptimizationStateStore,  # noqa: TC001
)
from app.utils import get_logger

logger = get_logger(__name__)


def load_optimization_result(
    *,
    search_id: str,
    reproducibility_hash: str,
    store: OptimizationStateStore,
) -> OptimizationResult | None:
    """Recover only an exact compatible persisted Optimization result.

    Args:
        search_id: Expected canonical search identity.
        reproducibility_hash: Expected canonical evidence identity.
        store: Injected Optimization state port.

    Returns:
        Exact canonical result, or ``None`` when no result is persisted.

    Raises:
        OptimizationError: If loaded state is stale, conflicting, or
            unavailable.
    """
    logger.info("Loading exact Optimization result")
    try:
        result = store.load_result(search_id)
    except Exception as exc:
        raise OptimizationError("OPT_PERSISTENCE_FAILED", "RESULT_READ_FAILED") from exc
    if result is None:
        return None
    if result.search_id != search_id or (
        reproducibility_hash and result.reproducibility_hash != reproducibility_hash
    ):
        raise OptimizationError("OPT_STATE_CONFLICT", "RESULT_IDENTITY_MISMATCH")
    return result


__all__ = ["load_optimization_result"]
