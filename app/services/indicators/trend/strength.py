"""Strategy-independent trend strength and direction measurement."""

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
def measure_trend_strength(
    *,
    adx_value: float,
    positive_directional: float,
    negative_directional: float,
    fast_average: float,
    slow_average: float,
    strength_threshold: float,
) -> Mapping[str, object]:
    """Measure direction and strength from supplied official outputs.

    Args:
        adx_value: Produced ADX value.
        positive_directional: Produced positive directional value.
        negative_directional: Produced negative directional value.
        fast_average: Produced higher-timeframe fast average.
        slow_average: Produced higher-timeframe slow average.
        strength_threshold: Explicit minimum ADX for a strong trend.

    Returns:
        Direction, strength state, and source measurements.

    Raises:
        IndicatorError: If any measurement or threshold is invalid.
    """
    logger.info("Measuring trend strength")
    values = (
        adx_value,
        positive_directional,
        negative_directional,
        fast_average,
        slow_average,
        strength_threshold,
    )
    if any(not math.isfinite(value) for value in values) or strength_threshold < 0.0:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "trend-strength inputs must be finite with a non-negative threshold",
        )
    direction = "FLAT"
    if fast_average > slow_average and positive_directional > negative_directional:
        direction = "UP"
    elif fast_average < slow_average and negative_directional > positive_directional:
        direction = "DOWN"
    strength = "STRONG" if adx_value >= strength_threshold else "WEAK"
    return {"direction": direction, "strength": strength, "adx": adx_value}


__all__ = ["measure_trend_strength"]
