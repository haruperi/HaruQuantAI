"""Aroon indicator.

- Calculates Aroon Up, Aroon Down, and Aroon Oscillator trend indicators.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_lower,
)
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)
BOTTOM_LEVEL: float = 8.0
TOP_LEVEL: float = 99.9
MID_LOW_LEVEL: float = 30.0
MID_HIGH_LEVEL: float = 70.0


class Aroon(BaseIndicator):
    """Aroon indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.aroon",
        version="1.0.0",
        name="Aroon",
        description=(
            "Calculates Aroon Up, Aroon Down, and Aroon Oscillator trend indicators."
        ),
        category="trend",
        tags=("trend", "aroon"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
        ),
        outputs=(
            OutputPort("up", PortType.SERIES, description="Up output series"),
            OutputPort("down", PortType.SERIES, description="Down output series"),
            OutputPort(
                "oscillator", PortType.SERIES, description="Oscillator output series"
            ),
        ),
        required_market_inputs=("high", "low"),
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: Aroon requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
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

    # Specialized methods: indicator-specific behavior only.
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


# Public exports.
__all__ = ["Aroon"]
