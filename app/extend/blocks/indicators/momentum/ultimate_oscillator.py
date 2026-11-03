"""UltimateOscillator indicator.

- Calculates Larry Williams' Ultimate Oscillator combining buying pressure across
  three distinct timeframes (7, 14, 28) with weighted coefficients.
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

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_SCALE_100: float = 100.0
_MIN_BARS: int = 2


class UltimateOscillator(BaseIndicator):
    """Ultimate Oscillator (UO) block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.ultimate_oscillator",
        version="1.0.0",
        name="Ultimate Oscillator",
        description="Multi-timeframe buying pressure oscillator (Larry Williams)",
        category="momentum",
        tags=("momentum", "oscillator", "ultimate", "williams"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Ultimate Oscillator"),),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=29,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period1": {"type": "int", "min": 2, "max": 20, "default": 7},
            "period2": {"type": "int", "min": 5, "max": 40, "default": 14},
            "period3": {"type": "int", "min": 10, "max": 80, "default": 28},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period1: int = Field(
        default=7,
        ge=1,
        title="Period1",
        description="Number of bars in the first calculation window",
    )

    period2: int = Field(
        default=14,
        ge=1,
        title="Period2",
        description="Number of bars in the second calculation window",
    )

    period3: int = Field(
        default=28,
        ge=1,
        title="Period3",
        description="Number of bars in the third calculation window",
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
        return max(self.period1, self.period2, self.period3) + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Ultimate Oscillator values."""
        logger.debug(
            "FR-indicator-calculation: UltimateOscillator requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        uo = np.full(n, np.nan, dtype=np.float64)
        if n >= _MIN_BARS:
            prev_close = np.roll(close, 1)
            prev_close[0] = close[0]
            true_low = np.minimum(low, prev_close)
            true_high = np.maximum(high, prev_close)
            bp = close - true_low
            tr = true_high - true_low
            sum_bp1 = _rolling_sum(bp, self.period1)
            sum_tr1 = _rolling_sum(tr, self.period1)
            sum_bp2 = _rolling_sum(bp, self.period2)
            sum_tr2 = _rolling_sum(tr, self.period2)
            sum_bp3 = _rolling_sum(bp, self.period3)
            sum_tr3 = _rolling_sum(tr, self.period3)
            with np.errstate(divide="ignore", invalid="ignore"):
                avg1 = np.where(sum_tr1 > _EPSILON, sum_bp1 / sum_tr1, 0.0)
                avg2 = np.where(sum_tr2 > _EPSILON, sum_bp2 / sum_tr2, 0.0)
                avg3 = np.where(sum_tr3 > _EPSILON, sum_bp3 / sum_tr3, 0.0)
                val = _SCALE_100 * (4.0 * avg1 + 2.0 * avg2 + avg3) / 7.0
            max_p = max(self.period1, self.period2, self.period3)
            uo[max_p - 1 :] = val[max_p - 1 :]
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated UO for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(uo, name="UO")}


# Private helpers: used only by this indicator.
def _rolling_sum(x: np.ndarray, p: int) -> np.ndarray:
    n = len(x)
    res = np.full(n, np.nan, dtype=np.float64)
    if n >= p:
        cs = np.insert(np.cumsum(x), 0, 0.0)
        res[p - 1 :] = cs[p:] - cs[:-p]
    return res


# Public exports.
__all__ = ["UltimateOscillator"]
