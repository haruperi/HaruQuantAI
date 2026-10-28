"""Momentum indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-MOMENTUM: validated batch calculation.
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


class Momentum(BaseIndicator):
    """Momentum indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.momentum",
        name="Momentum",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=15,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

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
                "FR-SERVICES-MOMENTUM-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        res = np.full(n, 100.0, dtype=np.float64)
        for i in range(1, n):
            past_idx = max(0, i - period)
            denom = arr[past_idx]
            if denom != 0.0 and (not np.isnan(denom)):
                res[i] = arr[i] * 100.0 / denom
            else:
                res[i] = 100.0
        logger.info(
            "FR-SERVICES-MOMENTUM-CALCULATE: Computed Momentum(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"Momentum({period})")}

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 100.0, shift: int = 0
    ) -> bool:
        """Evaluate MomCrossUp condition (crosses above level/100)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 100.0, shift: int = 0
    ) -> bool:
        """Evaluate MomCrossDown condition (crosses below level/100)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate MomHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate MomLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomChangesDown turn condition."""
        return changes_down(series, shift=shift)
