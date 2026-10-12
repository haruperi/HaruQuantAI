"""Candlestick Pattern Recognition Indicator Block.

Description:
    Implements pure causal, vectorized candlestick pattern detection across
    OHLC series incorporating both classic quantitative patterns and StrategyQuant X
    CandlePatterns building blocks:
    - Doji: Small real body relative to total range (<= 10%).
    - Engulfing: Real body completely covers previous bar's real body
      (Bullish: +1.0, Bearish: -1.0).
    - Pinbar / Hammer / Shooting Star: Long shadow at least twice the real
      body with small opposing wick (Bullish Hammer: +1.0, Bearish Shooting Star: -1.0).
    - Inside Bar: Range strictly contained within previous bar's range (+1.0).
    - Three-Bar Reversal: Confirmation of directional reversal over 3 bars
      (Bullish: +1.0, Bearish: -1.0).
    - Dark Cloud Cover (SQX): Bearish reversal where candle opens higher and
      penetrates deeply (>50%) into the preceding bullish candle (+1.0).
    - Piercing Line (SQX): Bullish reversal where candle opens lower and
      penetrates deeply (>50%) into the preceding bearish candle (+1.0).

Purpose:
    FEAT-SERVICES-INDICATOR-CANDLESTICK-PATTERNS

Key Capabilities:
    - FR-SERVICES-CANDLESTICK-PATTERNS-CALCULATE: Evaluates multi-pattern
      candlestick recognition across input OHLC arrays.
    - FR-SERVICES-CANDLESTICK-PATTERNS-CONDITIONS: Evaluates pattern presence
      and directional polarity predicates including SQX naming aliases.

Python API Usage:
    ```python
    from app.services.indicators.price_action.candlestick_patterns import (
        CandlestickPatterns,
    )

    patterns = CandlestickPatterns.calculate(open_p, high, low, close)
    doji = patterns["doji"]
    engulfing = patterns["engulfing"]
    dark_cloud = patterns["dark_cloud"]
    piercing = patterns["piercing_line"]

    # Condition checks
    is_doji = CandlestickPatterns.is_doji(doji, shift=0)
    is_dc = CandlestickPatterns.is_dark_cloud(dark_cloud, shift=0)
    is_pl = CandlestickPatterns.is_piercing_line(piercing, shift=0)
    is_ham = CandlestickPatterns.is_hammer(patterns["pinbar"], shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

DEFAULT_DOJI_RATIO: float = 0.10
DEFAULT_PINBAR_WICK_RATIO: float = 2.0
DEFAULT_OPPOSITE_WICK_RATIO: float = 0.20
DARK_CLOUD_PIERCING_RATIO: float = 0.50
PATTERN_THRESHOLD: float = 0.5
MIN_BARS_THREE_BAR: int = 2
EPSILON: float = 1e-12


class CandlestickPatterns(BaseIndicator):
    """Multi-pattern causal candlestick detector."""

    @classmethod
    @override
    def calculate(
        cls,
        open: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        high: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        low: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        close: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        doji_ratio: float = DEFAULT_DOJI_RATIO,
    ) -> dict[str, IndicatorSeries]:
        """Compute all candlestick pattern series.

        Args:
            open: Open price series.
            high: High price series.
            low: Low price series.
            close: Close price series.
            doji_ratio: Maximum body-to-range ratio for Doji qualification.

        Returns:
            Dictionary containing 'doji', 'engulfing', 'pinbar', 'inside_bar',
            'three_bar', 'dark_cloud', and 'piercing_line' IndicatorSeries.
        """
        logger.info(
            "CandlestickPatterns.calculate called: doji_ratio=%.2f",
            doji_ratio,
        )
        o_arr = cls.to_numpy(open)
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)

        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        if doji_ratio <= 0.0 or doji_ratio >= 1.0:
            raise ValueError(
                f"doji_ratio must be strictly between 0 and 1, got {doji_ratio}"
            )

        patterns = cls._compute_patterns((o_arr, h_arr, l_arr, c_arr), doji_ratio)
        logger.info("CandlestickPatterns completed: bars=%d", n)
        return {
            "doji": IndicatorSeries(patterns[0], name="Doji"),
            "engulfing": IndicatorSeries(patterns[1], name="Engulfing"),
            "pinbar": IndicatorSeries(patterns[2], name="Pinbar"),
            "inside_bar": IndicatorSeries(patterns[3], name="InsideBar"),
            "three_bar": IndicatorSeries(patterns[4], name="ThreeBarReversal"),
            "dark_cloud": IndicatorSeries(patterns[5], name="DarkCloud"),
            "piercing_line": IndicatorSeries(patterns[6], name="PiercingLine"),
        }

    @classmethod
    def _compute_patterns(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
        doji_ratio: float,
    ) -> tuple[
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
        np.ndarray[Any, Any],
    ]:
        o_arr, h_arr, l_arr, c_arr = prices
        doji, pinbar = cls._compute_single_bar(o_arr, h_arr, l_arr, c_arr, doji_ratio)
        engulfing, inside = cls._compute_two_bar_patterns(o_arr, h_arr, l_arr, c_arr)
        dark_cloud, piercing = cls._compute_piercing_and_dark_cloud(
            o_arr, h_arr, l_arr, c_arr
        )
        three_bar = cls._compute_three_bar(h_arr, l_arr, c_arr)
        return doji, engulfing, pinbar, inside, three_bar, dark_cloud, piercing

    @classmethod
    def _compute_single_bar(
        cls,
        o_arr: np.ndarray[Any, Any],
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        doji_ratio: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n = len(c_arr)
        doji = np.zeros(n, dtype=np.float64)
        pinbar = np.zeros(n, dtype=np.float64)

        for i in range(n):
            rng = h_arr[i] - l_arr[i]
            body = abs(c_arr[i] - o_arr[i])

            if rng > EPSILON and (body / rng) <= doji_ratio:
                doji[i] = 1.0

            upper_wick = h_arr[i] - max(o_arr[i], c_arr[i])
            lower_wick = min(o_arr[i], c_arr[i]) - l_arr[i]
            if rng > EPSILON:
                if (
                    lower_wick >= DEFAULT_PINBAR_WICK_RATIO * body
                    and upper_wick <= DEFAULT_OPPOSITE_WICK_RATIO * rng
                ):
                    pinbar[i] = 1.0
                elif (
                    upper_wick >= DEFAULT_PINBAR_WICK_RATIO * body
                    and lower_wick <= DEFAULT_OPPOSITE_WICK_RATIO * rng
                ):
                    pinbar[i] = -1.0

        return doji, pinbar

    @classmethod
    def _compute_two_bar_patterns(
        cls,
        o_arr: np.ndarray[Any, Any],
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n = len(c_arr)
        engulfing = np.zeros(n, dtype=np.float64)
        inside = np.zeros(n, dtype=np.float64)

        for i in range(1, n):
            p_o, p_c = o_arr[i - 1], c_arr[i - 1]
            p_h, p_l = h_arr[i - 1], l_arr[i - 1]

            if (
                c_arr[i] > o_arr[i]
                and p_c < p_o
                and o_arr[i] <= p_c
                and c_arr[i] >= p_o
            ):
                engulfing[i] = 1.0
            elif (
                c_arr[i] < o_arr[i]
                and p_c > p_o
                and o_arr[i] >= p_c
                and c_arr[i] <= p_o
            ):
                engulfing[i] = -1.0

            if h_arr[i] < p_h and l_arr[i] > p_l:
                inside[i] = 1.0

        return engulfing, inside

    @classmethod
    def _compute_piercing_and_dark_cloud(
        cls,
        o_arr: np.ndarray[Any, Any],
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n = len(c_arr)
        dark_cloud = np.zeros(n, dtype=np.float64)
        piercing_line = np.zeros(n, dtype=np.float64)

        for i in range(1, n):
            p_o, p_c = o_arr[i - 1], c_arr[i - 1]
            rng = h_arr[i] - l_arr[i]

            # Dark Cloud Cover (bearish reversal after bullish candle)
            if (
                p_c > p_o
                and c_arr[i] < o_arr[i]
                and c_arr[i] < (p_o + p_c) / 2.0
                and c_arr[i] > p_o
                and rng > EPSILON
                and ((o_arr[i] - c_arr[i]) / rng) > DARK_CLOUD_PIERCING_RATIO
            ):
                dark_cloud[i] = 1.0

            # Piercing Line (bullish reversal after bearish candle)
            if (
                p_c < p_o
                and c_arr[i] > o_arr[i]
                and c_arr[i] > (p_o + p_c) / 2.0
                and c_arr[i] < p_o
                and rng > EPSILON
                and ((c_arr[i] - o_arr[i]) / rng) > DARK_CLOUD_PIERCING_RATIO
            ):
                piercing_line[i] = 1.0

        return dark_cloud, piercing_line

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
            p_h, p_l = h_arr[i - 1], l_arr[i - 1]
            p2_h, p2_l = h_arr[i - 2], l_arr[i - 2]
            if p_l < p2_l and c_arr[i] > p_h:
                three_bar[i] = 1.0
            elif p_h > p2_h and c_arr[i] < p_l:
                three_bar[i] = -1.0

        return three_bar

    @classmethod
    def is_doji(cls, doji_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Doji."""
        logger.info("Evaluating CandlestickPatterns.is_doji: shift=%d", shift)
        val = doji_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD

    @classmethod
    def is_bullish_engulfing(
        cls, engulfing_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bar at shift is a Bullish Engulfing pattern."""
        logger.info(
            "Evaluating CandlestickPatterns.is_bullish_engulfing: shift=%d",
            shift,
        )
        val = engulfing_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD

    @classmethod
    def is_bearish_engulfing(
        cls, engulfing_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bar at shift is a Bearish Engulfing pattern."""
        logger.info(
            "Evaluating CandlestickPatterns.is_bearish_engulfing: shift=%d",
            shift,
        )
        val = engulfing_series.get(shift)
        return not np.isnan(val) and val < -PATTERN_THRESHOLD

    @classmethod
    def is_bullish_pinbar(cls, pinbar_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Bullish Pinbar / Hammer."""
        logger.info(
            "Evaluating CandlestickPatterns.is_bullish_pinbar: shift=%d",
            shift,
        )
        val = pinbar_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD

    @classmethod
    def is_hammer(cls, pinbar_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Hammer (SQX alias for Bullish Pinbar)."""
        logger.info("Evaluating CandlestickPatterns.is_hammer: shift=%d", shift)
        return cls.is_bullish_pinbar(pinbar_series, shift=shift)

    @classmethod
    def is_bearish_pinbar(cls, pinbar_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Bearish Pinbar / Shooting Star."""
        logger.info(
            "Evaluating CandlestickPatterns.is_bearish_pinbar: shift=%d",
            shift,
        )
        val = pinbar_series.get(shift)
        return not np.isnan(val) and val < -PATTERN_THRESHOLD

    @classmethod
    def is_shooting_star(cls, pinbar_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Shooting Star (SQX alias for Bearish Pinbar)."""
        logger.info("Evaluating CandlestickPatterns.is_shooting_star: shift=%d", shift)
        return cls.is_bearish_pinbar(pinbar_series, shift=shift)

    @classmethod
    def is_inside_bar(cls, inside_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is an Inside Bar."""
        logger.info("Evaluating CandlestickPatterns.is_inside_bar: shift=%d", shift)
        val = inside_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD

    @classmethod
    def is_bullish_three_bar(
        cls, three_bar_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bar at shift is a Bullish Three-Bar Reversal."""
        logger.info(
            "Evaluating CandlestickPatterns.is_bullish_three_bar: shift=%d",
            shift,
        )
        val = three_bar_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD

    @classmethod
    def is_bearish_three_bar(
        cls, three_bar_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bar at shift is a Bearish Three-Bar Reversal."""
        logger.info(
            "Evaluating CandlestickPatterns.is_bearish_three_bar: shift=%d",
            shift,
        )
        val = three_bar_series.get(shift)
        return not np.isnan(val) and val < -PATTERN_THRESHOLD

    @classmethod
    def is_dark_cloud(cls, dark_cloud_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Dark Cloud Cover pattern (SQX)."""
        logger.info("Evaluating CandlestickPatterns.is_dark_cloud: shift=%d", shift)
        val = dark_cloud_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD

    @classmethod
    def is_piercing_line(cls, piercing_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if bar at shift is a Piercing Line pattern (SQX)."""
        logger.info("Evaluating CandlestickPatterns.is_piercing_line: shift=%d", shift)
        val = piercing_series.get(shift)
        return not np.isnan(val) and val > PATTERN_THRESHOLD
