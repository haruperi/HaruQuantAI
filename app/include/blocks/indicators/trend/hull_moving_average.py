"""HullMovingAverage indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-HULLMOVINGAVERAGE: validated batch calculation.
"""

from __future__ import annotations

import math
from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    changes_down,
    changes_up,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.average import lwma_kernel

logger = get_logger(__name__)


class HullMovingAverage(BaseIndicator):
    """Hull Moving Average indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.hull_moving_average",
        name="HullMovingAverage",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=16,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + int(self.period**0.5) - 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = bars.close
        period = self.period
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)
        if period <= 1:
            logger.warning(
                "FR-SERVICES-HMA-CALCULATE: Invalid period %d, defaulting to 14", period
            )
            period = 14
        fast_period = max(1, math.floor(period / 2.0))
        sqrt_period = max(1, math.floor(math.sqrt(period)))
        fast_wma = lwma_kernel(c_arr, fast_period)
        slow_wma = lwma_kernel(c_arr, period)
        diff = 2.0 * fast_wma - slow_wma
        hma = lwma_kernel(diff, sqrt_period)
        logger.info(
            "FR-SERVICES-HMA-CALCULATE: Computed HMA(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(hma, name=f"HMA({period})")}

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA is rising."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA is falling."""
        return is_falling(series, shift=shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA turned upward."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA turned downward."""
        return changes_down(series, shift=shift)

    @classmethod
    def faster_above_slower(
        cls, faster_hma: IndicatorSeries, slower_hma: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate if Faster HMA is above Slower HMA."""
        return is_greater(faster_hma, slower_hma, shift=shift)

    @classmethod
    def faster_below_slower(
        cls, faster_hma: IndicatorSeries, slower_hma: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate if Faster HMA is below Slower HMA."""
        return is_lower(faster_hma, slower_hma, shift=shift)
