"""No scaling position sizing method snippet.

Description:
    Implements pass-through scaling method conforming to StrategyQuant
    SQ.Trading.Scaling.NoScaling. Returns requested position volume unchanged.

Purpose:
    FEAT-TRADING-SCALING: Port NoScaling method from StrategyQuant.

Key Capabilities:
    - FR-SCALING-NO-SCALING: Return requested size directly without modifications.

Python API Usage:
    from app.extend.trading.scaling.no_scaling import NoScaling
    scaling = NoScaling()
    size = scaling.scale_size(2.5)

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py -k test_no_scaling
"""

from __future__ import annotations

import logging
from typing import override

from app.extend.trading.scaling.base import (
    ScalingMethod,
    ScalingMethodsList,
)

logger = logging.getLogger(__name__)


class NoScaling(ScalingMethod):
    """Pass-through scaling method matching SQ Scaling/NoScaling.java."""

    name: str = "No scaling"
    display: str = "No scaling"

    def __init__(self) -> None:
        super().__init__()
        logger.debug("FR-SCALING-NO-SCALING: initialized NoScaling method")

    @override
    def scale_size(self, requested_size: float) -> float:
        """Return requested position size without adjustment."""
        result = max(requested_size, 0.0)
        logger.debug("FR-SCALING-NO-SCALING: scale_size=%f", result)
        return result


ScalingMethodsList.register("NoScaling", NoScaling)
ScalingMethodsList.register("No scaling", NoScaling)

__all__ = [
    "NoScaling",
]
