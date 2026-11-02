"""Moving Average Hamming window filter strategy block.

Description:
    Calculates a weighted moving average using coefficients derived from
    a Hamming window filter for minimal spectral side-lobe leakage.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-moving-average-hamming: Hamming window moving average.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.moving_average_hamming import (
        MovingAverageHamming,
    )
    res = MovingAverageHamming().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
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


class MovingAverageHamming(BaseIndicator):
    """Moving Average Hamming window filter block."""

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
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Hamming moving average values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        hma = hamming_kernel(close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated HammingMA(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(hma, name="HammingMA")}


__all__ = ["MovingAverageHamming", "hamming_kernel"]
