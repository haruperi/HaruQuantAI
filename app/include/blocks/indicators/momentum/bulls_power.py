"""BullsPower indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-BULLSPOWER: validated batch calculation.
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
from app.include.calculators.average import ema_kernel

logger = get_logger(__name__)


class BullsPower(BaseIndicator):
    """Bulls Power (Elder-Ray) indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.bulls_power",
        name="BullsPower",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        close = bars.close
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(high_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-BULLS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        ema = ema_kernel(close_arr, period)
        res = high_arr - ema
        logger.info(
            "FR-SERVICES-BULLS-CALCULATE: Computed BullsPower(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"BullsPower({period})")}

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BUPCrossUp condition (crosses above level/zero)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BUPCrossDown condition (crosses below level/zero)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BUPHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BUPLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPChangesDown turn condition."""
        return changes_down(series, shift=shift)
