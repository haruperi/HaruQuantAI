"""Deterministic composite market-speed measurement."""

from __future__ import annotations

import math
from collections.abc import Mapping

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import get_logger

logger = get_logger(__name__)


@guard_public_boundary
def measure_market_speed(
    components: Mapping[str, float], *, thresholds: tuple[float, float, float]
) -> Mapping[str, object]:
    """Measure composite market speed from normalized causal components.

    Args:
        components: Exact momentum, realized-volatility, range-expansion,
            volume-acceleration, and order-flow-velocity values normalized to a
            common non-negative scale.
        thresholds: Strictly increasing slow, fast, and extreme boundaries.

    Returns:
        Composite score, state, and ordered component evidence.

    Raises:
        IndicatorError: If evidence or thresholds are incomplete or invalid.
    """
    logger.info("Measuring deterministic market speed")
    required = {
        "momentum",
        "realized_volatility",
        "range_expansion",
        "volume_acceleration",
        "order_flow_velocity",
    }
    if set(components) != required:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA,
            "market-speed components are incomplete",
        )
    values = tuple(float(components[name]) for name in sorted(required))
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise IndicatorError(
            IndicatorErrorCode.IND_UNSUPPORTED_DTYPE,
            "market-speed components must be finite and non-negative",
        )
    slow, fast, extreme = thresholds
    if not 0.0 <= slow < fast < extreme or any(
        not math.isfinite(value) for value in thresholds
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "market-speed thresholds must be finite and strictly increasing",
        )
    score = sum(values) / len(values)
    state = (
        "SLOW"
        if score < slow
        else "NORMAL"
        if score < fast
        else "FAST"
        if score < extreme
        else "EXTREME"
    )
    return {
        "score": score,
        "state": state,
        "components": dict(sorted(components.items())),
    }


__all__ = ["measure_market_speed"]
