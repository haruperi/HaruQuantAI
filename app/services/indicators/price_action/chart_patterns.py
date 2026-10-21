"""Geometric Chart Pattern Recognition Indicator Block.

Description:
    Detects classical structural chart formations using rolling confirmed swing
    extrema and breakout/retest levels:
    - Double Top: Two confirmed swing peaks within tolerance (+1.0).
    - Double Bottom: Two confirmed swing troughs within tolerance (-1.0).
    - Breakout & Retest: Price closes beyond preceding consolidation extrema
      with low/high retesting broken boundary level (Bullish: +1.0, Bearish: -1.0).

Purpose:
    FEAT-SERVICES-INDICATOR-CHART-PATTERNS

Key Capabilities:
    - FR-SERVICES-CHART-PATTERNS-CALCULATE: Evaluates multi-structural chart
      pattern recognition over rolling price windows.
    - FR-SERVICES-CHART-PATTERNS-CONDITIONS: Evaluates pattern occurrence and
      polarity predicates.

Python API Usage:
    ```python
    from app.services.indicators.price_action.chart_patterns import ChartPatterns

    patterns = ChartPatterns.calculate(high, low, close, lookback=50)
    dtb = patterns["double_pattern"]
    breakout = patterns["breakout_retest"]

    # Condition checks
    is_dtop = ChartPatterns.is_double_top(dtb, shift=0)
    is_dbot = ChartPatterns.is_double_bottom(dtb, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import is_greater, is_lower
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_CHART_LOOKBACK: int = 10
DEFAULT_CHART_LOOKBACK: int = 50
DEFAULT_TOLERANCE_PCT: float = 0.03
PATTERN_THRESHOLD: float = 0.5
EPSILON: float = 1e-12


class ChartPatterns(BaseIndicator):
    """Multi-structural chart pattern recognizer."""

    @classmethod
    @override
    def calculate(
        cls,
        high: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        low: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        close: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        lookback: int = DEFAULT_CHART_LOOKBACK,
        tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling chart pattern recognition series.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            lookback: Rolling search window size for structural extrema.
            tolerance_pct: Extrema proximity tolerance percentage.

        Returns:
            Dictionary containing 'double_pattern' and 'breakout_retest'
            IndicatorSeries.
        """
        logger.info(
            "ChartPatterns.calculate called: lookback=%d, tol=%.2f",
            lookback,
            tolerance_pct,
        )
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)

        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        if lookback < MIN_CHART_LOOKBACK:
            raise ValueError(
                f"lookback must be >= {MIN_CHART_LOOKBACK}, got {lookback}"
            )
        if tolerance_pct <= 0.0 or tolerance_pct >= 1.0:
            raise ValueError(
                f"tolerance_pct must be between 0 and 1, got {tolerance_pct}"
            )

        double_pat, breakout_pat = cls._compute_chart_patterns(
            (h_arr, l_arr, c_arr), lookback, tolerance_pct
        )
        logger.info("ChartPatterns completed: bars=%d", n)
        return {
            "double_pattern": IndicatorSeries(
                double_pat, name=f"DoublePattern({lookback})"
            ),
            "breakout_retest": IndicatorSeries(
                breakout_pat, name=f"BreakoutRetest({lookback})"
            ),
        }

    @classmethod
    def _compute_chart_patterns(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
        lookback: int,
        tolerance_pct: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        double_pat = np.zeros(n, dtype=np.float64)
        breakout_pat = np.zeros(n, dtype=np.float64)

        for i in range(lookback, n):
            start = i - lookback
            w_h = h_arr[start : i + 1]
            w_l = l_arr[start : i + 1]

            w_max = float(np.max(w_h))
            w_min = float(np.min(w_l))
            rng = w_max - w_min
            tol = (tolerance_pct * rng) if rng > EPSILON else 0.01

            half = lookback // 2
            peak1 = float(np.max(w_h[:half]))
            peak2 = float(np.max(w_h[half:]))
            trough1 = float(np.min(w_l[:half]))
            trough2 = float(np.min(w_l[half:]))

            # Double top / bottom
            if abs(peak1 - peak2) <= tol and peak2 >= w_max - tol:
                double_pat[i] = -1.0
            elif abs(trough1 - trough2) <= tol and trough2 <= w_min + tol:
                double_pat[i] = 1.0

            # Breakout and retest
            prev_high_level = float(np.max(w_h[:-2]))
            prev_low_level = float(np.min(w_l[:-2]))

            curr_c = c_arr[i]
            curr_l = l_arr[i]
            curr_h = h_arr[i]

            if curr_c > prev_high_level and curr_l <= prev_high_level + tol:
                breakout_pat[i] = 1.0
            elif curr_c < prev_low_level and curr_h >= prev_low_level - tol:
                breakout_pat[i] = -1.0

        return double_pat, breakout_pat

    @classmethod
    def is_double_top(cls, double_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if double top pattern formed at shift."""
        logger.info("Evaluating ChartPatterns.is_double_top: shift=%d", shift)
        return is_lower(double_series, -PATTERN_THRESHOLD, shift1=shift, round_digits=8)

    @classmethod
    def is_double_bottom(cls, double_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if double bottom pattern formed at shift."""
        logger.info("Evaluating ChartPatterns.is_double_bottom: shift=%d", shift)
        return is_greater(
            double_series, PATTERN_THRESHOLD, shift1=shift, round_digits=8
        )

    @classmethod
    def is_bullish_breakout(
        cls, breakout_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bullish breakout and retest occurred at shift."""
        logger.info("Evaluating ChartPatterns.is_bullish_breakout: shift=%d", shift)
        return is_greater(
            breakout_series, PATTERN_THRESHOLD, shift1=shift, round_digits=8
        )

    @classmethod
    def is_bearish_breakout(
        cls, breakout_series: IndicatorSeries, shift: int = 0
    ) -> bool:
        """True if bearish breakdown and retest occurred at shift."""
        logger.info("Evaluating ChartPatterns.is_bearish_breakout: shift=%d", shift)
        return is_lower(
            breakout_series, -PATTERN_THRESHOLD, shift1=shift, round_digits=8
        )
