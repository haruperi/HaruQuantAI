"""OSMA indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-OSMA: validated batch calculation.
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
from app.include.calculators.average import ema_kernel, sma_kernel

logger = get_logger(__name__)


class OSMA(BaseIndicator):
    """Moving Average of Oscillator (OSMA) indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.osma",
        name="OSMA",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "fast_ema": {"type": "int", "min": 1, "max": 48, "default": 12},
            "slow_ema": {"type": "int", "min": 1, "max": 104, "default": 26},
            "signal_period": {"type": "int", "min": 1, "max": 36, "default": 9},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=34,
    )
    fast_ema: int = Field(default=12, ge=1)
    slow_ema: int = Field(default=26, ge=1)
    signal_period: int = Field(default=9, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.fast_ema, self.slow_ema) + self.signal_period - 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        data = bars.close
        fast_ema = self.fast_ema
        slow_ema = self.slow_ema
        signal_period = self.signal_period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if fast_ema <= 0:
            fast_ema = 12
        if slow_ema <= 0:
            slow_ema = 26
        if signal_period <= 0:
            signal_period = 9
        fast_arr = ema_kernel(arr, fast_ema)
        slow_arr = ema_kernel(arr, slow_ema)
        macd = fast_arr - slow_arr
        res = np.full(n, np.nan, dtype=np.float64)
        valid_indices = np.where(~np.isnan(macd))[0]
        if len(valid_indices) >= signal_period:
            first_idx = valid_indices[0]
            valid_macd = macd[first_idx:]
            sig_part = sma_kernel(valid_macd, signal_period)
            res[first_idx:] = valid_macd - sig_part
        logger.info(
            "FR-SERVICES-OSMA-CALCULATE: Computed OSMA(%d, %d, %d) for %d bars",
            fast_ema,
            slow_ema,
            signal_period,
            n,
        )
        return {
            "value": IndicatorSeries(
                res, name=f"OSMA({fast_ema},{slow_ema},{signal_period})"
            )
        }

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMARising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMAFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMACrossZeroUp / crosses above level condition."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMACrossZeroDown / crosses below level condition."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_greater(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMAHigherZero / greater than level condition."""
        return is_greater(series, level, shift=shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMALowerZero / lower than level condition."""
        return is_lower(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate OSMA is higher than past value."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMAChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMAChangesDown turn condition."""
        return changes_down(series, shift=shift)
