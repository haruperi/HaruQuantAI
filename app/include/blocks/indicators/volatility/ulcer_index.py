"""UlcerIndex indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-ULCERINDEX: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, Literal, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
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

DOWN_MODE = 2

logger = get_logger(__name__)


class UlcerIndex(BaseIndicator):
    """Ulcer Index indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.ulcer_index",
        name="UlcerIndex",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "mode": {"type": "int", "choices": [1, 2], "default": 1},
            "period": {"type": "int", "min": 1, "max": 96, "default": 24},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=24,
    )
    mode: Literal[1, 2] = Field(default=1)
    period: int = Field(default=24, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        data = bars.close
        mode = self.mode
        period = self.period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-ULCER-CALCULATE: Invalid period %d, defaulting to 24",
                period,
            )
            period = 24
        dd_buffer = np.zeros(n, dtype=np.float64)
        res = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]
            if mode == DOWN_MODE:
                lc = float(np.min(win))
                if lc != 0.0 and (not np.isnan(lc)):
                    dd_buffer[i] = 100.0 * (arr[i] - lc) / lc
            else:
                hc = float(np.max(win))
                if hc != 0.0 and (not np.isnan(hc)):
                    dd_buffer[i] = 100.0 * (arr[i] - hc) / hc
            if i >= period:
                dd_win = dd_buffer[i - period + 1 : i + 1]
                sum_sq = float(np.sum(np.square(dd_win)))
                res[i] = float(np.sqrt(sum_sq / period))
        logger.info(
            "FR-SERVICES-ULCER-CALCULATE: UI(mode=%d, period=%d) computed for %d bars",
            mode,
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"UlcerIndex(mode={mode},{period})")}

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is rising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is falling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate Ulcer Index crosses above level."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate Ulcer Index crosses below level (below safe level)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_lower(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is below safe level threshold."""
        return is_lower(series, level, shift=shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is above safe level threshold."""
        return is_greater(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate Ulcer Index is higher than past value."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)
