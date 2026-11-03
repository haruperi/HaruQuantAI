"""ArnaudLegouxMovingAverage indicator.

- Calculates Arnaud Legoux Moving Average (ALMA) using Gaussian weights to provide
  responsiveness and noise reduction with minimal phase lag.
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


class ArnaudLegouxMovingAverage(BaseIndicator):
    """Arnaud Legoux Moving Average (ALMA) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.alma",
        version="1.0.0",
        name="Arnaud Legoux Moving Average",
        description="Gaussian filter moving average with low lag and smoothness",
        category="trend",
        tags=("trend", "ma", "alma", "gaussian"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "ALMA"),),
        required_market_inputs=("close",),
        required_history_lookback=9,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 9},
            "offset": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.85},
            "sigma": {"type": "float", "min": 1.0, "max": 20.0, "default": 6.0},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=9,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    offset: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        title="Offset",
        description="Offset applied by the indicator calculation",
    )

    sigma: float = Field(
        default=6.0,
        gt=0.0,
        title="Sigma",
        description="Sigma used by the indicator calculation",
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
        """Compute ALMA values over closing prices."""
        logger.debug(
            "FR-indicator-calculation: ArnaudLegouxMovingAverage requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        alma = alma_kernel(close, self.period, self.offset, self.sigma)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated ALMA(p=%d, off=%.2f, sig=%.1f) "
            "for %d bars",
            self.period,
            self.offset,
            self.sigma,
            len(bars),
        )
        return {"value": IndicatorSeries(alma, name="ALMA")}


# Private helpers: used only by this indicator.
def alma_kernel(
    data: np.ndarray,
    period: int,
    offset: float,
    sigma: float,
) -> np.ndarray:
    """Compute ALMA filter over 1D series."""
    n = len(data)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n < period or sigma <= 0.0:
        return out
    m = math.floor(offset * (period - 1))
    s = period / sigma
    weights = np.empty(period, dtype=np.float64)
    for i in range(period):
        weights[i] = math.exp(-((i - m) ** 2) / (2.0 * s * s))
    w_sum = np.sum(weights)
    if w_sum > 0.0:
        weights /= w_sum
    for i in range(period - 1, n):
        out[i] = np.dot(data[i - period + 1 : i + 1], weights)
    return out


# Public exports.
__all__ = ["ArnaudLegouxMovingAverage"]
