"""Shared validation for thin Optimization public operations."""

from __future__ import annotations

from collections.abc import Sequence

from app.services.optimization.evidence import OptimizationResult  # noqa: TC001
from app.services.optimization.validation import WalkForwardRequest  # noqa: TC001
from app.utils import logger


def validate_request_id(request_id: str | None) -> str | None:
    """Validate an optional trace identifier without inventing one.

    Args:
        request_id: Optional caller-owned request identity.

    Returns:
        Supplied non-blank identity or None.

    Raises:
        ValueError: If a supplied identifier is blank.
    """
    logger.debug("Validating optional Optimization public request ID")
    if request_id is not None and not request_id.strip():
        raise ValueError("request_id cannot be blank")
    return request_id


def validate_walk_forward_matrix(
    requests: Sequence[WalkForwardRequest], *, max_requests: int
) -> tuple[WalkForwardRequest, ...]:
    """Validate a non-empty bounded compatible WFA request matrix.

    Args:
        requests: Requested walk-forward configurations.
        max_requests: Explicit positive matrix cap.

    Returns:
        Immutable compatible requests.

    Raises:
        ValueError: If count, cap, or execution provenance differs.
    """
    logger.debug("Validating bounded Optimization walk-forward matrix")
    values = tuple(requests)
    if max_requests <= 0 or not values or len(values) > max_requests:
        raise ValueError("walk-forward matrix is empty or exceeds its cap")
    first = values[0].search.execution_context
    identity = (
        first.strategy_config_hash,
        first.data_hash,
        first.cost_model_hash,
        first.realism_hash,
        first.engine_version,
    )
    if any(
        (
            item.search.execution_context.strategy_config_hash,
            item.search.execution_context.data_hash,
            item.search.execution_context.cost_model_hash,
            item.search.execution_context.realism_hash,
            item.search.execution_context.engine_version,
        )
        != identity
        for item in values[1:]
    ):
        raise ValueError("walk-forward matrix provenance is incompatible")
    return values


def validate_compatible_results(
    results: Sequence[OptimizationResult],
) -> tuple[OptimizationResult, ...]:
    """Validate a non-empty compatible result sequence.

    Args:
        results: Optimization results to compare.

    Returns:
        Immutable compatible results.

    Raises:
        ValueError: If results are empty, duplicated, or schema-incompatible.
    """
    logger.debug("Validating compatible Optimization results")
    values = tuple(results)
    if not values:
        raise ValueError("result comparison cannot be empty")
    if len({item.search_id for item in values}) != len(values):
        raise ValueError("result comparison search IDs must be unique")
    if len({(item.contract_version, item.schema_id) for item in values}) != 1:
        raise ValueError("result comparison schemas are incompatible")
    return values


__all__ = [
    "validate_compatible_results",
    "validate_request_id",
    "validate_walk_forward_matrix",
]
