"""Correlation fallback policy and resolution services."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.risk.correlation.contracts import CorrelationFallbackContext
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models.contracts import CorrelationSnapshot
from app.utils.logger import logger


def should_fail_closed_for_missing_correlation(
    context: CorrelationFallbackContext, policy: object
) -> bool:
    """Determine whether missing correlation evidence must block/reject.

    Args:
        context: Context details for missing correlation.
        policy: Active risk policy profile settings.

    Returns:
        bool: True if execution must block.
    """
    logger.info("Evaluating fail-closed logic for missing correlation.")
    mode = context.mode.lower()
    is_live = mode in {
        "full_live",
        "micro_live",
        "live_readonly",
    } or getattr(policy, "allow_live_execution", False)

    # In live environments, reject/block if we lack enough samples for a matrix
    return bool(is_live and context.sample_count < context.minimum_samples)


def build_conservative_correlation_snapshot(
    symbols: Sequence[str], assumed_correlation: Decimal
) -> CorrelationSnapshot:
    """Build a deterministic conservative fallback correlation snapshot.

    Args:
        symbols: Collection of active symbols.
        assumed_correlation: Pairwise correlation assumed for non-diagonal entries.

    Returns:
        CorrelationSnapshot: Conservatively assumed snapshot.
    """
    logger.info("Building conservative fallback correlation snapshot.")
    matrix: dict[str, dict[str, Decimal]] = {}
    sorted_symbols = sorted(symbols)
    for s1 in sorted_symbols:
        matrix[s1] = {}
        for s2 in sorted_symbols:
            if s1 == s2:
                matrix[s1][s2] = Decimal("1.0")
            else:
                matrix[s1][s2] = Decimal(str(assumed_correlation))

    return CorrelationSnapshot(
        matrix=matrix,
        lookback=50,
        timeframe="M1",
        method="pearson",
        sample_count=0,
        fallback_status=True,
    )


def resolve_correlation_fallback(
    context: CorrelationFallbackContext, policy: object
) -> CorrelationSnapshot:
    """Resolve conservative fallback correlation snapshot.

    Args:
        context: Context details for fallback.
        policy: Active risk policy settings.

    Returns:
        CorrelationSnapshot: Resolved correlation snapshot.

    Raises:
        ValidationError: If fail-closed policy restricts fallbacks.
    """
    logger.info("Resolving correlation fallback snapshot.")
    if should_fail_closed_for_missing_correlation(context, policy):
        msg = (
            f"Fail-Closed: Insufficient aligned samples "
            f"({context.sample_count} < {context.minimum_samples}) "
            f"for correlation matrix calculation."
        )
        logger.error(msg)
        raise ValidationError(msg)

    # Determine default assumed correlation value
    assumed = Decimal("0.0")
    if (
        hasattr(policy, "assumed_correlation_fallback")
        and policy.assumed_correlation_fallback is not None
    ):
        assumed = Decimal(str(policy.assumed_correlation_fallback))
    elif getattr(policy, "allow_live_execution", False):
        assumed = Decimal("1.0")

    return build_conservative_correlation_snapshot(context.symbols, assumed)
