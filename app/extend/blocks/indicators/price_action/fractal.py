"""Fractal indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-FRACTAL: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
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
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_FRACTAL_BARS: int = 3


class Fractal(BaseIndicator):
    """Bill Williams Fractal indicator detecting local peak and trough formations."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.fractal",
        name="Fractal",
        category="price_action",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("up", PortType.SERIES),
            OutputPort("down", PortType.SERIES),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "fractal_bars": {"type": "int", "min": 3, "max": 20, "default": 5}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=5,
    )
    fractal_bars: int = Field(default=5, ge=MIN_FRACTAL_BARS)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject inconsistent settings before calculation."""
        if self.fractal_bars % 2 == 0:
            raise ValueError("fractal_bars must be odd")
        return self

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.fractal_bars < MIN_FRACTAL_BARS or self.fractal_bars % 2 == 0:
            raise ValueError(
                f"fractal_bars must be an odd integer >= 3, got {self.fractal_bars}"
            )
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.fractal_bars

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        fractal_bars = self.fractal_bars
        logger.info(
            "Fractal calculation initiated with fractal_bars=%d",
            fractal_bars,
            extra={"fractal_bars": fractal_bars},
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        if len(h_arr) == 0:
            raise ValueError("Input series cannot be empty")
        if len(h_arr) != len(l_arr):
            raise ValueError(
                f"High and low series length mismatch: {len(h_arr)} vs {len(l_arr)}"
            )
        n = len(h_arr)
        up_vals = np.zeros(n, dtype=np.float64)
        down_vals = np.zeros(n, dtype=np.float64)
        each_side = (fractal_bars - 1) // 2
        for i in range(fractal_bars - 1, n):
            up_p, down_p = self._check_fractal_at_bar(
                h_arr, l_arr, i, each_side, fractal_bars
            )
            up_vals[i] = up_p
            down_vals[i] = down_p
        logger.info(
            "Fractal calculation complete: bars=%d, fractal_bars=%d",
            n,
            fractal_bars,
            extra={"bars": n, "fractal_bars": fractal_bars},
        )
        return {
            "up": IndicatorSeries(up_vals, name=f"FractalUp({fractal_bars})"),
            "down": IndicatorSeries(down_vals, name=f"FractalDown({fractal_bars})"),
        }

    @staticmethod
    def _check_fractal_at_bar(
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        curr_i: int,
        each_side: int,
        fractal_bars: int,
    ) -> tuple[float, float]:
        """Check if middle bar in window forms an up or down fractal."""
        middle_idx = curr_i - each_side
        middle_high = h_arr[middle_idx]
        middle_low = l_arr[middle_idx]
        is_up = True
        is_down = True
        for offset in range(fractal_bars):
            check_idx = curr_i - offset
            if check_idx == middle_idx:
                continue
            if h_arr[check_idx] >= middle_high:
                is_up = False
            if l_arr[check_idx] <= middle_low:
                is_down = False
        up_val = middle_high if is_up else 0.0
        down_val = middle_low if is_down else 0.0
        return (up_val, down_val)

    @staticmethod
    def is_bullish_fractal(
        fractals: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if a bullish fractal formed at shift.

        Formula:
            fractals['down'][shift] > 0
        """
        logger.info(
            "Evaluating is_bullish_fractal at shift=%d", shift, extra={"shift": shift}
        )
        return is_greater(fractals["down"], 0.0, shift1=shift, round_digits=8)

    @staticmethod
    def is_bearish_fractal(
        fractals: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if a bearish fractal formed at shift.

        Formula:
            fractals['up'][shift] > 0
        """
        logger.info(
            "Evaluating is_bearish_fractal at shift=%d", shift, extra={"shift": shift}
        )
        return is_greater(fractals["up"], 0.0, shift1=shift, round_digits=8)
