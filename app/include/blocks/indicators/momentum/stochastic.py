"""Stochastic indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-STOCHASTIC: validated batch calculation.
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


class Stochastic(BaseIndicator):
    """Stochastic Oscillator family consolidating %K, %D lines and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.stochastic",
        name="Stochastic",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("k", PortType.SERIES), OutputPort("d", PortType.SERIES)),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "k_period": {"type": "int", "min": 1, "max": 56, "default": 14},
            "d_period": {"type": "int", "min": 1, "max": 12, "default": 3},
            "slowing": {"type": "int", "min": 1, "max": 12, "default": 3},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=18,
    )
    k_period: int = Field(default=14, ge=1)
    d_period: int = Field(default=3, ge=1)
    slowing: int = Field(default=3, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.k_period + self.slowing + self.d_period - 2

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        k_period = self.k_period
        d_period = self.d_period
        slowing = self.slowing
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if k_period <= 0:
            logger.warning(
                "FR-SERVICES-STOCH-CALCULATE: Invalid k_period %d, defaulting to 14",
                k_period,
            )
            k_period = 14
        if d_period <= 0:
            d_period = 3
        if slowing <= 0:
            slowing = 3
        raw_k = np.full(n, np.nan, dtype=np.float64)
        for i in range(k_period - 1, n):
            h_win = high_arr[i - k_period + 1 : i + 1]
            l_win = low_arr[i - k_period + 1 : i + 1]
            hh = float(np.max(h_win))
            ll = float(np.min(l_win))
            diff = hh - ll
            if diff != 0.0:
                raw_k[i] = (close_arr[i] - ll) / diff * 100.0
            else:
                raw_k[i] = 50.0
        valid_k_idx = np.where(~np.isnan(raw_k))[0]
        slow_k = np.full(n, np.nan, dtype=np.float64)
        if len(valid_k_idx) >= slowing:
            first_idx = valid_k_idx[0]
            valid_slice = raw_k[first_idx:]
            slow_k[first_idx:] = sma_kernel(valid_slice, slowing)
        valid_d_idx = np.where(~np.isnan(slow_k))[0]
        slow_d = np.full(n, np.nan, dtype=np.float64)
        if len(valid_d_idx) >= d_period:
            first_idx = valid_d_idx[0]
            valid_slice = slow_k[first_idx:]
            slow_d[first_idx:] = sma_kernel(valid_slice, d_period)
        logger.info(
            "FR-SERVICES-STOCH-CALCULATE: Computed Stoch(%d,%d,%d) for %d bars",
            k_period,
            d_period,
            slowing,
            n,
        )
        return {
            "k": IndicatorSeries(slow_k, name="Stoch.K"),
            "d": IndicatorSeries(slow_d, name="Stoch.D"),
        }

    @classmethod
    def k_crosses_above_d(
        cls, stoch: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate %K crosses above %D."""
        return crosses_above(stoch["k"], stoch["d"], shift=shift)

    @classmethod
    def k_crosses_below_d(
        cls, stoch: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate %K crosses below %D."""
        return crosses_below(stoch["k"], stoch["d"], shift=shift)

    @classmethod
    def k_higher_d(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate StochFastKUp (`%K[shift] > %D[shift]`)."""
        return is_greater(stoch["k"], stoch["d"], shift=shift)

    @classmethod
    def k_lower_d(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate StochFastKDown (`%K[shift] < %D[shift]`)."""
        return is_lower(stoch["k"], stoch["d"], shift=shift)

    @classmethod
    def k_crosses_above(
        cls, stoch: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate StochFastKCrossUp (`%K` crosses above `level`)."""
        return crosses_above(stoch["k"], level, shift=shift)

    @classmethod
    def k_crosses_below(
        cls, stoch: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate StochFastKCrossDown (`%K` crosses below `level`)."""
        return crosses_below(stoch["k"], level, shift=shift)

    @classmethod
    def d_changes_up(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate StochSlowDChangesUp (`%D[s+2] > %D[s+1] < %D[s]`)."""
        return changes_up(stoch["d"], shift=shift)

    @classmethod
    def d_changes_down(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate StochSlowDChangesDown (`%D[s+2] < %D[s+1] > %D[s]`)."""
        return changes_down(stoch["d"], shift=shift)

    @classmethod
    def d_crosses_above(
        cls, stoch: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate StochSlowDCrossUp (`%D` crosses above `level`)."""
        return crosses_above(stoch["d"], level, shift=shift)

    @classmethod
    def d_crosses_below(
        cls, stoch: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate StochSlowDCrossDown (`%D` crosses below `level`)."""
        return crosses_below(stoch["d"], level, shift=shift)

    @classmethod
    def d_is_rising(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate StochSlowDRising (`%D[shift+1] < %D[shift]`)."""
        return is_rising(stoch["d"], shift=shift)

    @classmethod
    def d_is_falling(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate StochSlowDFalling (`%D[shift+1] > %D[shift]`)."""
        return is_falling(stoch["d"], shift=shift)

    @classmethod
    def d_is_higher(
        cls, stoch: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate StochSlowDHigher (`%D[shift] > level`)."""
        return is_greater(stoch["d"], level, shift=shift)

    @classmethod
    def d_is_lower(
        cls, stoch: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate StochSlowDLower (`%D[shift] < level`)."""
        return is_lower(stoch["d"], level, shift=shift)
