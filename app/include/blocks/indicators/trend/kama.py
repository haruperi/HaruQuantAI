"""KAMA indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-KAMA: validated batch calculation.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import is_falling, is_lower, is_rising
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.indicators.trend.kaufman_efficiency_ratio import (
    KaufmanEfficiencyRatio,
)
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


class KAMA(BaseIndicator):
    """Kaufman's Adaptive Moving Average indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.kama",
        name="KAMA",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "er_period": {"type": "int", "min": 1, "max": 40, "default": 10},
            "fast_period": {"type": "int", "min": 1, "max": 8, "default": 2},
            "slow_period": {"type": "int", "min": 1, "max": 120, "default": 30},
        },
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.trend.kaufman_efficiency_ratio",),
        required_history_lookback=11,
    )
    er_period: int = Field(default=10, ge=1)
    fast_period: int = Field(default=2, ge=1)
    slow_period: int = Field(default=30, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.er_period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
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

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if KAMA is rising."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if KAMA is falling."""
        return is_falling(series, shift=shift)

    @classmethod
    def bar_closes_above(
        cls,
        close: IndicatorSeries | Sequence[float] | np.ndarray,
        kama_series: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is above KAMA."""
        return is_greater(close, kama_series, shift=shift)

    @classmethod
    def bar_closes_below(
        cls,
        close: IndicatorSeries | Sequence[float] | np.ndarray,
        kama_series: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is below KAMA."""
        return is_lower(close, kama_series, shift=shift)

    @classmethod
    def fast_above_slow(
        cls, fast_kama: IndicatorSeries, slow_kama: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate if Fast KAMA is above Slow KAMA."""
        return is_greater(fast_kama, slow_kama, shift=shift)

    @classmethod
    def fast_below_slow(
        cls, fast_kama: IndicatorSeries, slow_kama: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate if Fast KAMA is below Slow KAMA."""
        return is_lower(fast_kama, slow_kama, shift=shift)
