"""StdDev indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-STDDEV: validated batch calculation.
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

logger = get_logger(__name__)


class StdDev(BaseIndicator):
    """Standard Deviation indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.std_dev",
        name="StdDev",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=20, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        data = bars.close
        period = self.period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-STDDEV-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20
        res = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]
            if len(win) > 0:
                res[i] = float(np.std(win, ddof=0))
        logger.info(
            "FR-SERVICES-STDDEV-CALCULATE: Computed StdDev(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"StdDev({period})")}

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate StdDevCrossUp condition."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate StdDevCrossDown condition."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate StdDevHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate StdDevLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevChangesDown turn condition."""
        return changes_down(series, shift=shift)
