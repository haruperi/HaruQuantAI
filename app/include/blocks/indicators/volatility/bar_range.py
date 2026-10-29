"""BarRange indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-BARRANGE: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import is_lower
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

logger = get_logger(__name__)


class BarRange(BaseIndicator):
    """Bar Range indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.bar_range",
        name="BarRange",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        parameter_search_space={},
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=1,
    )

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        res = high_arr - low_arr
        logger.info("FR-SERVICES-BARRANGE-CALCULATE: Computed BarRange for %d bars", n)
        return {"value": IndicatorSeries(res, name="BarRange")}

    @classmethod
    def fixed_pips(cls, value: float, pip_size: float = 0.0001) -> float:
        """Convert a fixed pips value into a price range (`Value * pip_size`)."""
        return float(value * pip_size)

    @classmethod
    def is_biggest_range(
        cls,
        series: IndicatorSeries,
        period: int = 5,
        shift: int = 0,
        lookback: int | None = None,
    ) -> bool:
        """Evaluate if range at shift is the highest among past period bars."""
        if lookback is not None:
            period = lookback
        if period <= 1:
            return False
        return all(
            is_greater(series, series, shift1=shift, shift2=s, round_digits=8)
            for s in range(shift + 1, shift + period)
        )

    @classmethod
    def is_smallest_range(
        cls,
        series: IndicatorSeries,
        period: int = 5,
        shift: int = 0,
        lookback: int | None = None,
    ) -> bool:
        """Evaluate if range at shift is the lowest among past period bars."""
        if lookback is not None:
            period = lookback
        if period <= 1:
            return False
        return all(
            is_lower(series, series, shift1=shift, shift2=s, round_digits=8)
            for s in range(shift + 1, shift + period)
        )

    @classmethod
    def in_range_pips(
        cls,
        series: IndicatorSeries,
        min_pips: float,
        max_pips: float,
        pip_size: float = 0.0001,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate if bar range in pips is between min_pips and max_pips."""
        val = series.get(shift)
        if np.isnan(val) or pip_size <= 0:
            return False
        pips = val / pip_size
        return min_pips <= pips <= max_pips
