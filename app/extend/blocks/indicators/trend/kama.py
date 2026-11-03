"""KAMA indicator.

- Calculates Kaufman Adaptive Moving Average (KAMA) adjusting smoothing to market
  noise.
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
from app.extend.blocks.indicators.trend.kaufman_efficiency_ratio import (
    KaufmanEfficiencyRatio,
)

logger = get_logger(__name__)


class KAMA(BaseIndicator):
    """Kaufman's Adaptive Moving Average indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.kama",
        version="1.0.0",
        name="KAMA",
        description=(
            "Calculates Kaufman Adaptive Moving Average (KAMA) adjusting "
            "smoothing to market noise."
        ),
        category="trend",
        tags=("trend", "kama"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("close",),
        required_history_lookback=11,
        dependencies=("indicator.trend.kaufman_efficiency_ratio",),
        is_generation_eligible=True,
        parameter_search_space={
            "er_period": {"type": "int", "min": 1, "max": 40, "default": 10},
            "fast_period": {"type": "int", "min": 1, "max": 8, "default": 2},
            "slow_period": {"type": "int", "min": 1, "max": 120, "default": 30},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    er_period: int = Field(
        default=10,
        ge=1,
        title="Er period",
        description="Number of bars in the er window",
    )

    fast_period: int = Field(
        default=2,
        ge=1,
        title="Fast period",
        description="Number of bars in the fast window",
    )

    slow_period: int = Field(
        default=30,
        ge=1,
        title="Slow period",
        description="Number of bars in the slow window",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.er_period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: KAMA requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        close = bars.close
        er_period = self.er_period
        fast_period = self.fast_period
        slow_period = self.slow_period
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)
        if er_period <= 0:
            er_period = 10
        if fast_period <= 0:
            fast_period = 2
        if slow_period <= 0:
            slow_period = 30
        res = np.zeros(n, dtype=np.float64)
        max_p = max(fast_period, slow_period, er_period)
        if n == 0:
            return {
                "value": IndicatorSeries(
                    res, name=f"KAMA({er_period},{fast_period},{slow_period})"
                )
            }
        if n < max_p:
            res[:] = c_arr
            return {
                "value": IndicatorSeries(
                    res, name=f"KAMA({er_period},{fast_period},{slow_period})"
                )
            }
        er_series = KaufmanEfficiencyRatio(period=er_period).calculate(bars)["value"]
        er_vals = er_series.values
        fast_sc = 2.0 / (float(fast_period) + 1.0)
        slow_sc = 2.0 / (float(slow_period) + 1.0)
        smoothing_consts = np.square(er_vals * (fast_sc - slow_sc) + slow_sc)
        res[:max_p] = c_arr[:max_p]
        for t in range(max_p, n):
            sc = smoothing_consts[t]
            res[t] = res[t - 1] + sc * (c_arr[t] - res[t - 1])
        logger.info(
            "FR-SERVICES-KAMA-CALCULATE: Computed KAMA(%d,%d,%d) for %d bars",
            er_period,
            fast_period,
            slow_period,
            n,
        )
        return {
            "value": IndicatorSeries(
                res, name=f"KAMA({er_period},{fast_period},{slow_period})"
            )
        }


# Public exports.
__all__ = ["KAMA"]
