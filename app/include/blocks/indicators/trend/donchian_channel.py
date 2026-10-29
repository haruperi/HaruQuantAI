"""DonchianChannels indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-DONCHIANCHANNELS: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_lower,
    is_lower_or_equal,
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
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_DONCHIAN_PERIOD: int = 2
DEFAULT_DONCHIAN_PERIOD: int = 20
EPSILON: float = 1e-12


class DonchianChannels(BaseIndicator):
    """Donchian Channels breakout envelope and volatility width block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.donchian_channel",
        name="DonchianChannels",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES),
            OutputPort("lower", PortType.SERIES),
            OutputPort("middle", PortType.SERIES),
            OutputPort("width", PortType.SERIES),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 80, "default": 20},
            "offset": {"type": "int", "min": 0, "max": 4, "default": 0},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=DEFAULT_DONCHIAN_PERIOD, ge=MIN_DONCHIAN_PERIOD)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_DONCHIAN_PERIOD:
            raise ValueError(
                f"period must be >= {MIN_DONCHIAN_PERIOD}, got {self.period}"
            )
        if self.offset < 0:
            raise ValueError(f"offset must be >= 0, got {self.offset}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + self.offset

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        period = self.period
        offset = self.offset
        logger.info(
            "DonchianChannels calculation initiated: period=%d, offset=%d",
            period,
            offset,
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        upper, lower, middle, width = self._compute_channels(
            h_arr, l_arr, period, offset, n=n
        )
        logger.info("DonchianChannels calculation completed: bars=%d", n)
        return {
            "upper": IndicatorSeries(upper, name=f"DonchianUpper({period})"),
            "lower": IndicatorSeries(lower, name=f"DonchianLower({period})"),
            "middle": IndicatorSeries(middle, name=f"DonchianMiddle({period})"),
            "width": IndicatorSeries(width, name=f"DonchianWidth({period})"),
        }

    @classmethod
    def _compute_channels(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        period: int,
        offset: int,
        *,
        n: int,
    ) -> tuple[
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
    ]:
        raw_upper = np.zeros(n, dtype=np.float64)
        raw_lower = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            raw_upper[i] = float(np.max(h_arr[start : i + 1]))
            raw_lower[i] = float(np.min(l_arr[start : i + 1]))
        if offset > 0:
            upper = np.full(n, np.nan, dtype=np.float64)
            lower = np.full(n, np.nan, dtype=np.float64)
            if offset < n:
                upper[offset:] = raw_upper[: n - offset]
                lower[offset:] = raw_lower[: n - offset]
        else:
            upper = raw_upper
            lower = raw_lower
        middle = (upper + lower) / 2.0
        width = upper - lower
        return (upper, lower, middle, width)

    @classmethod
    def is_above_upper(
        cls, price: IndicatorSeries, upper: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if price is greater than upper channel band."""
        logger.info("Evaluating Donchian is_above_upper at shift=%d", shift)
        return is_greater(price, upper, shift=shift)

    @classmethod
    def is_below_lower(
        cls, price: IndicatorSeries, lower: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if price is less than lower channel band."""
        logger.info("Evaluating Donchian is_below_lower at shift=%d", shift)
        return is_lower(price, lower, shift=shift)

    @classmethod
    def crosses_above_upper(
        cls, price: IndicatorSeries, upper: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if price crosses above upper band."""
        logger.info("Evaluating Donchian crosses_above_upper at shift=%d", shift)
        return crosses_above(price, upper, shift=shift)

    @classmethod
    def crosses_below_lower(
        cls, price: IndicatorSeries, lower: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if price crosses below lower band."""
        logger.info("Evaluating Donchian crosses_below_lower at shift=%d", shift)
        return crosses_below(price, lower, shift=shift)

    @classmethod
    def crosses_above_middle(
        cls, price: IndicatorSeries, middle: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if price crosses above middle band."""
        logger.info("Evaluating Donchian crosses_above_middle at shift=%d", shift)
        return crosses_above(price, middle, shift=shift)

    @classmethod
    def crosses_below_middle(
        cls, price: IndicatorSeries, middle: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if price crosses below middle band."""
        logger.info("Evaluating Donchian crosses_below_middle at shift=%d", shift)
        return crosses_below(price, middle, shift=shift)

    @classmethod
    def is_squeezed(
        cls, width: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if channel width is less than or equal to specified threshold."""
        logger.info("Evaluating Donchian is_squeezed at shift=%d", shift)
        return is_lower_or_equal(width, threshold, shift1=shift, round_digits=8)
