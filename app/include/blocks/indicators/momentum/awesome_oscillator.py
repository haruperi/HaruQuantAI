"""AwesomeOscillator indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-AWESOMEOSCILLATOR: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    changes_down,
    changes_up,
    crosses_above,
    crosses_below,
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
from app.include.calculators.average import sma_kernel

logger = get_logger(__name__)


class AwesomeOscillator(BaseIndicator):
    """Awesome Oscillator indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.awesome_oscillator",
        name="AwesomeOscillator",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "fast_period": {"type": "int", "min": 1, "max": 20, "default": 5},
            "slow_period": {"type": "int", "min": 1, "max": 136, "default": 34},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=34,
    )
    fast_period: int = Field(default=5, ge=1)
    slow_period: int = Field(default=34, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.fast_period, self.slow_period)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        fast_period = self.fast_period
        slow_period = self.slow_period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        if fast_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid fast_period %d, defaulting to 5",
                fast_period,
            )
            fast_period = 5
        if slow_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid slow_period %d, defaulting to 34",
                slow_period,
            )
            slow_period = 34
        median = (high_arr + low_arr) / 2.0
        fast_sma = sma_kernel(median, fast_period)
        slow_sma = sma_kernel(median, slow_period)
        res = fast_sma - slow_sma
        logger.info(
            "FR-SERVICES-AWO-CALCULATE: Computed AWO(fast=%d, slow=%d) for %d bars",
            fast_period,
            slow_period,
            n,
        )
        return {"value": IndicatorSeries(res, name="AwesomeOscillator")}

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWORising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWOFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate AWOCrossUp condition (crosses above level/zero)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate AWOCrossDown condition (crosses below level/zero)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate AWOHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate AWOLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWOChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWOChangesDown turn condition."""
        return changes_down(series, shift=shift)
