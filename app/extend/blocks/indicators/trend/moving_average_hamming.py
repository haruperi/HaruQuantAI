"""MovingAverageHamming indicator.

- Calculates a weighted moving average using coefficients derived from a Hamming
  window filter for minimal spectral side-lobe leakage.
"""

from __future__ import annotations

import math
from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)

_HAMMING_A0: float = 0.54
_HAMMING_A1: float = 0.46


class MovingAverageHamming(BaseIndicator):
    """Moving Average Hamming window filter block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.moving_average_hamming",
        version="1.0.0",
        name="Moving Average Hamming",
        description="Hamming window digital filter moving average",
        category="trend",
        tags=("trend", "ma", "hamming", "filter"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Hamming MA"),),
        required_market_inputs=("close",),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=20,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Hamming moving average values."""
        logger.debug(
            "FR-indicator-calculation: MovingAverageHamming requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        hma = hamming_kernel(close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated HammingMA(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(hma, name="HammingMA")}


# Private helpers: used only by this indicator.
def hamming_kernel(data: np.ndarray, period: int) -> np.ndarray:
    """Compute Hamming weighted moving average."""
    n = len(data)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n < period:
        return out
    if period == 1:
        return data.copy()
    weights = np.empty(period, dtype=np.float64)
    denom = float(period - 1)
    for i in range(period):
        weights[i] = _HAMMING_A0 - _HAMMING_A1 * math.cos(2.0 * math.pi * i / denom)
    w_sum = np.sum(weights)
    if w_sum > 0.0:
        weights /= w_sum
    for i in range(period - 1, n):
        out[i] = np.dot(data[i - period + 1 : i + 1], weights)
    return out


# Public exports.
__all__ = ["MovingAverageHamming"]
