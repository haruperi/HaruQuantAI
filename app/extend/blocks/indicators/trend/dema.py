"""DoubleEMA indicator.

- Calculates Patrick Mulloy's Double Exponential Moving Average (DEMA) reducing lag
  by calculating 2*EMA - EMA(EMA).
"""

from __future__ import annotations

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
from app.extend.calculators.average import ema_kernel

logger = get_logger(__name__)


class DoubleEMA(BaseIndicator):
    """Double Exponential Moving Average (DEMA) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.dema",
        version="1.0.0",
        name="Double EMA",
        description="Double exponential moving average (2*EMA - EMA(EMA))",
        category="trend",
        tags=("trend", "ma", "dema", "moving_average"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "DEMA"),),
        required_market_inputs=("close",),
        required_history_lookback=40,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 200, "default": 20}
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
        return self.period * 2

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute DEMA values over closing prices."""
        logger.debug("FR-indicator-calculation: DoubleEMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        close = np.asarray(bars.close, dtype=np.float64)
        dema = dema_kernel(close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated DEMA(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(dema, name="DEMA")}


# Private helpers: used only by this indicator.
def _safe_ema(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = ema_kernel(x[start:], period)
    return out


def dema_kernel(data: np.ndarray, period: int) -> np.ndarray:
    """Compute Double Exponential Moving Average (2*EMA1 - EMA2)."""
    ema1 = ema_kernel(data, period)
    ema2 = _safe_ema(ema1, period)
    dema = np.full_like(data, np.nan, dtype=np.float64)
    valid = ~np.isnan(ema1) & ~np.isnan(ema2)
    dema[valid] = 2.0 * ema1[valid] - ema2[valid]
    return dema


# Public exports.
__all__ = ["DoubleEMA"]
