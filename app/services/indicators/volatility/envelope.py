"""Deterministic volatility operating-envelope evidence."""

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
def measure_volatility_envelope(
    *,
    current: float,
    historical: float,
    operating_ratio: float,
    extreme_ratio: float,
) -> Mapping[str, object]:
    """Compare current volatility with an explicit historical baseline.

    Args:
        current: Current non-negative volatility measurement.
        historical: Positive historical baseline.
        operating_ratio: Positive maximum normal operating ratio.
        extreme_ratio: Extreme ratio strictly above the operating ratio.

    Returns:
        Ratio, state, and extreme-event evidence.

    Raises:
        IndicatorError: If a numeric input or threshold is invalid.
    """
    logger.info("Measuring volatility envelope")
    values = (current, historical, operating_ratio, extreme_ratio)
    if any(not math.isfinite(value) for value in values):
        raise IndicatorError(
            IndicatorErrorCode.IND_UNSUPPORTED_DTYPE,
            "volatility-envelope inputs must be finite",
        )
    if current < 0.0 or historical <= 0.0 or not 0.0 < operating_ratio < extreme_ratio:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "volatility-envelope bounds are invalid",
        )
    ratio = current / historical
    state = "NORMAL" if ratio <= operating_ratio else "ELEVATED"
    if ratio >= extreme_ratio:
        state = "EXTREME"
    return {"ratio": ratio, "state": state, "extreme": state == "EXTREME"}


__all__ = ["measure_volatility_envelope"]
