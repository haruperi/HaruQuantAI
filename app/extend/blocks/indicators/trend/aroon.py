"""Aroon indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-AROON: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_lower,
)
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)
BOTTOM_LEVEL: float = 8.0
TOP_LEVEL: float = 99.9
MID_LOW_LEVEL: float = 30.0
MID_HIGH_LEVEL: float = 70.0


class Aroon(BaseIndicator):
    """Aroon indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.aroon",
        name="Aroon",
        category="trend",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("up", PortType.SERIES),
            OutputPort("down", PortType.SERIES),
            OutputPort("oscillator", PortType.SERIES),
        ),
        required_market_inputs=("high", "low"),
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
        low = bars.low
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        if n != len(low_arr):
            raise ValueError("High and Low arrays must have equal length.")
        if period <= 0:
            logger.warning(
                "FR-SERVICES-AROON-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        up = np.zeros(n, dtype=np.float64)
        down = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start_idx = max(0, i - period)
            window_h = high_arr[start_idx : i + 1]
            window_l = low_arr[start_idx : i + 1]
            hh_idx = len(window_h) - 1 - int(np.argmax(window_h))
            ll_idx = len(window_l) - 1 - int(np.argmin(window_l))
            up[i] = 100.0 - 100.0 / float(period) * float(hh_idx)
            down[i] = 100.0 - 100.0 / float(period) * float(ll_idx)
        oscillator = up - down
        logger.info(
            "FR-SERVICES-AROON-CALCULATE: Computed Aroon(period=%d) for %d bars",
            period,
            n,
        )
        return {
            "up": IndicatorSeries(up, name=f"Aroon.Up({period})"),
            "down": IndicatorSeries(down, name=f"Aroon.Down({period})"),
            "oscillator": IndicatorSeries(
                oscillator, name=f"Aroon.Oscillator({period})"
            ),
        }

    @classmethod
    def up_rises_from_bottom(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Up rises from bottom condition."""
        res = crosses_above(
            aroon_dict["up"], BOTTOM_LEVEL, shift=shift, round_digits=8
        ) and is_greater(
            aroon_dict["down"], MID_LOW_LEVEL, shift1=shift, round_digits=8
        )
        logger.debug(
            "FR-SERVICES-AROON-CONDITIONS up_rises_from_bottom shift=%d res=%s",
            shift,
            res,
        )
        return res

    @classmethod
    def down_falls_from_top(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Down falls from top condition."""
        res = crosses_below(
            aroon_dict["down"], TOP_LEVEL, shift=shift, round_digits=8
        ) and is_lower(aroon_dict["up"], MID_HIGH_LEVEL, shift1=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-AROON-CONDITIONS down_falls_from_top shift=%d res=%s",
            shift,
            res,
        )
        return res

    @classmethod
    def down_rises_from_bottom(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Down rises from bottom condition."""
        res = crosses_above(
            aroon_dict["down"], BOTTOM_LEVEL, shift=shift, round_digits=8
        ) and is_greater(aroon_dict["up"], MID_LOW_LEVEL, shift1=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-AROON-CONDITIONS down_rises_from_bottom shift=%d res=%s",
            shift,
            res,
        )
        return res

    @classmethod
    def up_falls_from_top(
        cls, aroon_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate Aroon Up falls from top condition."""
        res = crosses_below(
            aroon_dict["up"], TOP_LEVEL, shift=shift, round_digits=8
        ) and is_lower(aroon_dict["down"], MID_HIGH_LEVEL, shift1=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-AROON-CONDITIONS up_falls_from_top shift=%d res=%s", shift, res
        )
        return res
