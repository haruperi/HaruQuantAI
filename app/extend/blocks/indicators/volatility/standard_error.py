"""StandardError indicator.

- Calculates the Standard Error of a linear regression estimate measuring the
  dispersion of prices around the linear regression trend line.
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

_MIN_PERIOD: int = 3


class StandardError(BaseIndicator):
    """Standard Error of linear regression estimate block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.standard_error",
        version="1.0.0",
        name="Standard Error",
        description="Standard error of linear regression estimate around the trendline",
        category="volatility",
        tags=("volatility", "statistics", "standard_error", "linreg"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Standard Error"),),
        required_market_inputs=("close",),
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 3, "max": 100, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
        ge=3,
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
        """Compute Standard Error values."""
        logger.debug(
            "FR-indicator-calculation: StandardError requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        se = standard_error_kernel(close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLATILITY: Calculated StdErr(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(se, name="StdErr")}


# Private helpers: used only by this indicator.
def standard_error_kernel(data: np.ndarray, period: int) -> np.ndarray:
    """Compute rolling Standard Error of linear regression estimate."""
    n = len(data)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < _MIN_PERIOD or n < period:
        return out
    x = np.arange(period, dtype=np.float64)
    x_mean = float(np.mean(x))
    x_var = float(np.sum((x - x_mean) ** 2))
    denom = float(period - 2)
    for i in range(period - 1, n):
        y = data[i - period + 1 : i + 1]
        y_mean = float(np.mean(y))
        slope = float(np.sum((x - x_mean) * (y - y_mean)) / x_var)
        intercept = y_mean - slope * x_mean
        residuals = y - (slope * x + intercept)
        rss = float(np.sum(residuals**2))
        out[i] = math.sqrt(rss / denom)
    return out


# Public exports.
__all__ = ["StandardError"]
