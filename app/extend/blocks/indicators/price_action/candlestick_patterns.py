"""CandlestickPatterns indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-CANDLESTICKPATTERNS: validated batch calculation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import is_lower
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
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
DOJI_TICK_FACTOR: float = 0.6
WICK_BODY_PERCENT: float = 0.9
HAMMER_MIN_TICKS: float = 12.0
PIERCING_MIN_TICKS: float = 10.0
DARK_CLOUD_PIERCING_RATIO: float = 0.5
DEFAULT_PINBAR_WICK_RATIO: float = 2.0
DEFAULT_OPPOSITE_WICK_RATIO: float = 0.2
PATTERN_THRESHOLD: float = 0.5
MIN_BARS_THREE_BAR: int = 2
MIN_BARS_HAMMER: int = 3
RATIO_DECIMALS: int = 6
EPSILON: float = 1e-12


def _eval_wick_tiers(dom_wick: float, opp_wick: float, digits: int) -> bool:
    """Evaluate 1/2, 1/3, and 1/4 dominant-to-opposing wick tiers."""
    d2 = round(dom_wick / 2.0, digits)
    d3 = round(dom_wick / 3.0, digits)
    d4 = round(dom_wick / 4.0, digits)
    return (
        (d2 > opp_wick and d3 <= opp_wick and (d4 <= opp_wick))
        or (d3 > opp_wick and d4 <= opp_wick)
        or d4 > opp_wick
    )


def _check_cond(
    source: IndicatorSeries | Mapping[str, IndicatorSeries],
    key: str,
    shift: int,
    *,
    negative: bool = False,
) -> bool:
    """Evaluate pattern threshold on an IndicatorSeries or pattern mapping."""
    logger.info("Evaluating CandlestickPatterns.%s: shift=%d", key, shift)
    series = source[key] if isinstance(source, Mapping) else source
    if negative:
        return is_lower(series, -PATTERN_THRESHOLD, shift1=shift, round_digits=8)
    return is_greater(series, PATTERN_THRESHOLD, shift1=shift, round_digits=8)


class CandlestickPatterns(BaseIndicator):
    """Multi-pattern causal candlestick detector."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.candlestick_patterns",
        name="CandlestickPatterns",
        category="price_action",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, required=True),
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("doji", PortType.SERIES),
            OutputPort("bullish_engulfing", PortType.SERIES),
            OutputPort("bearish_engulfing", PortType.SERIES),
            OutputPort("engulfing", PortType.SERIES),
            OutputPort("hammer", PortType.SERIES),
            OutputPort("shooting_star", PortType.SERIES),
            OutputPort("pinbar", PortType.SERIES),
            OutputPort("inside_bar", PortType.SERIES),
            OutputPort("three_bar", PortType.SERIES),
            OutputPort("dark_cloud", PortType.SERIES),
            OutputPort("piercing_line", PortType.SERIES),
        ),
        required_market_inputs=("open", "high", "low", "close"),
        parameter_search_space={
            "tick_size": {
                "type": "float",
                "min": 0.0,
                "max": 4,
                "default": 0.0001,
                "min_exclusive": True,
            },
            "digits": {"type": "int", "min": 0, "max": 20, "default": 5},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=3,
    )
    doji_ratio: float | None = Field(default=None, lt=1.0, gt=0.0)
    tick_size: float = Field(default=0.0001, gt=0.0)
    digits: int = Field(default=5, ge=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.doji_ratio is not None and (
            self.doji_ratio <= 0.0 or self.doji_ratio >= 1.0
        ):
            raise ValueError(
                f"doji_ratio must be strictly in (0, 1), got {self.doji_ratio}"
            )
        if self.tick_size <= 0.0 or self.digits < 0:
            raise ValueError("tick_size must be positive and digits non-negative")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 3

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        open_prices = bars.open
        high = bars.high
        low = bars.low
        close = bars.close
        doji_ratio = self.doji_ratio
        tick_size = self.tick_size
        digits = self.digits
        logger.info(
            "CandlestickPatterns.calculate: tick_size=%g, digits=%d", tick_size, digits
        )
        o_arr, h_arr = (to_numpy(open_prices), to_numpy(high))
        l_arr, c_arr = (to_numpy(low), to_numpy(close))
        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(h_arr) != n or (len(l_arr) != n):
            raise ValueError("Arrays cannot be empty and lengths must match")
        prices = (o_arr, h_arr, l_arr, c_arr)
        doji, pinbar = self._compute_single_bar(prices, doji_ratio, tick_size, digits)
        bull_eng, bear_eng, eng, inside = self._compute_two_bar_patterns(prices)
        dark_cloud, piercing = self._compute_piercing_dark_cloud(
            prices, tick_size, digits
        )
        hammer, shooting_star = self._compute_hammer_shooting_star(
            prices, tick_size, digits
        )
        three_bar = self._compute_three_bar(h_arr, l_arr, c_arr)
        logger.info("CandlestickPatterns completed: bars=%d", n)
        return {
            "doji": IndicatorSeries(doji, name="Doji"),
            "bullish_engulfing": IndicatorSeries(bull_eng, name="BullishEngulfing"),
            "bearish_engulfing": IndicatorSeries(bear_eng, name="BearishEngulfing"),
            "engulfing": IndicatorSeries(eng, name="Engulfing"),
            "hammer": IndicatorSeries(hammer, name="Hammer"),
            "shooting_star": IndicatorSeries(shooting_star, name="ShootingStar"),
            "pinbar": IndicatorSeries(pinbar, name="Pinbar"),
            "inside_bar": IndicatorSeries(inside, name="InsideBar"),
            "three_bar": IndicatorSeries(three_bar, name="ThreeBarReversal"),
            "dark_cloud": IndicatorSeries(dark_cloud, name="DarkCloud"),
            "piercing_line": IndicatorSeries(piercing, name="PiercingLine"),
        }

    @classmethod
    def _compute_single_bar(
        cls,
        prices: tuple[np.ndarray[Any, Any], ...],
        doji_ratio: float | None,
        tick_size: float,
        digits: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        doji = np.zeros(n, dtype=np.float64)
        pinbar = np.zeros(n, dtype=np.float64)
        max_doji_diff = round(DOJI_TICK_FACTOR * tick_size, digits)
        for i in range(n):
            rng = float(h_arr[i] - l_arr[i])
            body = float(abs(c_arr[i] - o_arr[i]))
            if doji_ratio is None:
                if round(body, digits) < max_doji_diff:
                    doji[i] = 1.0
            elif rng > EPSILON and body / rng <= doji_ratio:
                doji[i] = 1.0
            if rng > EPSILON:
                uw = float(h_arr[i] - max(o_arr[i], c_arr[i]))
                lw = float(min(o_arr[i], c_arr[i]) - l_arr[i])
                if (
                    lw >= DEFAULT_PINBAR_WICK_RATIO * body
                    and uw <= DEFAULT_OPPOSITE_WICK_RATIO * rng
                ):
                    pinbar[i] = 1.0
                elif (
                    uw >= DEFAULT_PINBAR_WICK_RATIO * body
                    and lw <= DEFAULT_OPPOSITE_WICK_RATIO * rng
                ):
                    pinbar[i] = -1.0
        return (doji, pinbar)

    @classmethod
    def _compute_two_bar_patterns(
        cls, prices: tuple[np.ndarray[Any, Any], ...]
    ) -> tuple[np.ndarray[Any, Any], ...]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        bull_eng = np.zeros(n, dtype=np.float64)
        bear_eng = np.zeros(n, dtype=np.float64)
        engulfing = np.zeros(n, dtype=np.float64)
        inside = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            o, c, o1, c1 = (o_arr[i], c_arr[i], o_arr[i - 1], c_arr[i - 1])
            if o1 > c1 and c > o and (c >= o1) and (c1 >= o) and (c - o > o1 - c1):
                bull_eng[i] = 1.0
                engulfing[i] = 1.0
            elif c1 > o1 and o > c and (o >= c1) and (o1 >= c) and (o - c > c1 - o1):
                bear_eng[i] = 1.0
                engulfing[i] = -1.0
            if h_arr[i] < h_arr[i - 1] and l_arr[i] > l_arr[i - 1]:
                inside[i] = 1.0
        return (bull_eng, bear_eng, engulfing, inside)

    @classmethod
    def _compute_piercing_dark_cloud(
        cls, prices: tuple[np.ndarray[Any, Any], ...], tick_size: float, digits: int
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        dark_cloud = np.zeros(n, dtype=np.float64)
        piercing = np.zeros(n, dtype=np.float64)
        min_len = round(PIERCING_MIN_TICKS * tick_size, digits)
        for i in range(1, n):
            o, c = (float(o_arr[i]), float(c_arr[i]))
            o1, c1 = (float(o_arr[i - 1]), float(c_arr[i - 1]))
            hl = round(float(h_arr[i] - l_arr[i]), digits)
            if hl < min_len or hl == 0.0:
                continue
            mid = round((o1 + c1) / 2.0, digits)
            oc_hl = round(round(o - c, digits) / hl, RATIO_DECIMALS)
            co_hl = round(round(c - o, digits) / hl, RATIO_DECIMALS)
            if (
                c1 > o1
                and mid > c
                and (o > c > o1)
                and (oc_hl > DARK_CLOUD_PIERCING_RATIO)
            ):
                dark_cloud[i] = 1.0
            if (
                c1 < o1
                and mid < c
                and (o < c < o1)
                and (co_hl > DARK_CLOUD_PIERCING_RATIO)
            ):
                piercing[i] = 1.0
        return (dark_cloud, piercing)

    @classmethod
    def _compute_hammer_shooting_star(
        cls, prices: tuple[np.ndarray[Any, Any], ...], tick_size: float, digits: int
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        hammer = np.zeros(n, dtype=np.float64)
        shooting = np.zeros(n, dtype=np.float64)
        min_len = round(HAMMER_MIN_TICKS * tick_size, digits)
        for i in range(MIN_BARS_HAMMER, n):
            o, c = (float(o_arr[i]), float(c_arr[i]))
            h, l_val = (float(h_arr[i]), float(l_arr[i]))
            cl = round(h - l_val, digits)
            if o == c or cl < min_len:
                continue
            lw = round(min(o, c) - l_val, digits)
            uw = round(h - max(o, c), digits)
            bl90_m2 = round(
                2.0 * round(round(abs(o - c), digits) * WICK_BODY_PERCENT, digits),
                digits,
            )
            if (
                l_val <= l_arr[i - 1]
                and l_val < l_arr[i - 2]
                and (l_val < l_arr[i - 3])
                and (lw > bl90_m2)
                and _eval_wick_tiers(lw, uw, digits)
            ):
                hammer[i] = 1.0
            if (
                h >= h_arr[i - 1]
                and h > h_arr[i - 2]
                and (h > h_arr[i - 3])
                and (uw > bl90_m2)
                and _eval_wick_tiers(uw, lw, digits)
            ):
                shooting[i] = 1.0
        return (hammer, shooting)

    @classmethod
    def _compute_three_bar(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        three_bar = np.zeros(n, dtype=np.float64)
        for i in range(MIN_BARS_THREE_BAR, n):
            if l_arr[i - 1] < l_arr[i - 2] and c_arr[i] > h_arr[i - 1]:
                three_bar[i] = 1.0
            elif h_arr[i - 1] > h_arr[i - 2] and c_arr[i] < l_arr[i - 1]:
                three_bar[i] = -1.0
        return three_bar

    @classmethod
    def is_doji(
        cls,
        doji_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Doji pattern."""
        return _check_cond(doji_series, "doji", shift)

    @classmethod
    def is_bullish_engulfing(
        cls,
        engulfing_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Bullish Engulfing pattern."""
        return _check_cond(engulfing_series, "bullish_engulfing", shift)

    @classmethod
    def is_bearish_engulfing(
        cls,
        engulfing_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Bearish Engulfing pattern."""
        if isinstance(engulfing_series, Mapping):
            return _check_cond(engulfing_series, "bearish_engulfing", shift)
        neg = engulfing_series.name != "BearishEngulfing"
        return _check_cond(engulfing_series, "bearish_engulfing", shift, negative=neg)

    @classmethod
    def is_bullish_pinbar(
        cls,
        pinbar_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Bullish Pinbar."""
        return _check_cond(pinbar_series, "pinbar", shift)

    @classmethod
    def is_hammer(
        cls,
        hammer_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Hammer pattern."""
        return _check_cond(hammer_series, "hammer", shift)

    @classmethod
    def is_bearish_pinbar(
        cls,
        pinbar_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Bearish Pinbar."""
        return _check_cond(pinbar_series, "pinbar", shift, negative=True)

    @classmethod
    def is_shooting_star(
        cls,
        shooting_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Shooting Star pattern."""
        if isinstance(shooting_series, Mapping):
            return _check_cond(shooting_series, "shooting_star", shift)
        neg = shooting_series.name == "Pinbar"
        return _check_cond(shooting_series, "shooting_star", shift, negative=neg)

    @classmethod
    def is_inside_bar(
        cls,
        inside_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is an Inside Bar."""
        return _check_cond(inside_series, "inside_bar", shift)

    @classmethod
    def is_bullish_three_bar(
        cls,
        three_bar_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Bullish Three-Bar Reversal."""
        return _check_cond(three_bar_series, "three_bar", shift)

    @classmethod
    def is_bearish_three_bar(
        cls,
        three_bar_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Bearish Three-Bar Reversal."""
        return _check_cond(three_bar_series, "three_bar", shift, negative=True)

    @classmethod
    def is_dark_cloud(
        cls,
        dark_cloud_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Dark Cloud Cover pattern."""
        return _check_cond(dark_cloud_series, "dark_cloud", shift)

    @classmethod
    def is_piercing_line(
        cls,
        piercing_series: IndicatorSeries | Mapping[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Return True if bar at shift is a Piercing Line pattern."""
        return _check_cond(piercing_series, "piercing_line", shift)
