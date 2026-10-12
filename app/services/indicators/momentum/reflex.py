"""John Ehlers' Reflex Indicator Block.

Description:
    Computes John Ehlers' Reflex indicator, a low-lag, cycle-tuned filter that
    detects cyclical turning points and market rhythms before traditional moving
    averages. Provides dual fast/slow cycle tracking and condition evaluators.

Purpose:
    FEAT-SERVICES-INDICATOR-REFLEX

Key Capabilities:
    - FR-SERVICES-REFLEX-CALCULATE: Computes low-lag Reflex cycle series.
    - FR-SERVICES-REFLEX-CONDITIONS: Evaluates cycle crossovers and turning points.

Python API Usage:
    ```python
    from app.services.indicators.reflex import Reflex

    reflex_res = Reflex.calculate(close, period=20, slow_period=40)
    fast = reflex_res["fast"]
    slow = reflex_res["slow"]

    # Condition checks
    cross_up = Reflex.fast_crosses_above_slow(fast, slow, shift=0)
    is_up = Reflex.changes_direction_up(fast, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

import math
from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_REFLEX_PERIOD: int = 2
DEFAULT_FAST_PERIOD: int = 20
DEFAULT_SLOW_PERIOD: int = 40
EPSILON: float = 1e-12
FALLBACK_DENOM: float = 1e-6


class Reflex(BaseIndicator):
    """John Ehlers' Reflex cycle indicator block."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_FAST_PERIOD,
        slow_period: int | None = None,
    ) -> dict[str, IndicatorSeries]:
        """Compute Reflex indicator line(s).

        Args:
            price: Input price series (typically Close).
            period: Primary (or fast) cycle period (must be >= 2).
            slow_period: Optional secondary (slow) cycle period.

        Returns:
            Dictionary containing 'reflex' (or 'fast') and optionally 'slow'.

        Raises:
            ValueError: If period < 2, slow_period < 2, or series is empty.
        """
        logger.info(
            "Reflex calculation initiated: period=%d, slow_period=%s",
            period,
            str(slow_period),
            extra={"period": period, "slow_period": slow_period},
        )
        if period < MIN_REFLEX_PERIOD:
            raise ValueError(f"period must be >= 2, got {period}")
        if slow_period is not None and slow_period < MIN_REFLEX_PERIOD:
            raise ValueError(f"slow_period must be >= 2, got {slow_period}")

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")

        fast_vals = cls._compute_single_reflex(p_arr, period)
        res = {
            "reflex": IndicatorSeries(fast_vals, name=f"Reflex({period})"),
            "fast": IndicatorSeries(fast_vals, name=f"FastReflex({period})"),
        }

        if slow_period is not None:
            slow_vals = cls._compute_single_reflex(p_arr, slow_period)
            res["slow"] = IndicatorSeries(slow_vals, name=f"SlowReflex({slow_period})")

        logger.info(
            "Reflex calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return res

    @staticmethod
    def _compute_single_reflex(
        p_arr: np.ndarray[Any, Any],
        period: int,
    ) -> np.ndarray[Any, Any]:
        """Compute single-line Reflex series according to Ehlers' formula."""
        n = len(p_arr)
        reflex = np.zeros(n, dtype=np.float64)
        if n < period:
            return reflex

        filt = np.zeros(n, dtype=np.float64)
        ms = np.zeros(n, dtype=np.float64)

        # 2-pole SuperSmoother filter constants
        arg = (1.414 * math.pi) / (0.5 * period)
        a1 = math.exp(-arg)
        b1 = 2.0 * a1 * math.cos(arg)
        c2 = b1
        c3 = -a1 * a1
        c1 = 1.0 - c2 - c3

        filt[0] = p_arr[0]
        if n > 1:
            filt[1] = p_arr[1]

        for i in range(2, n):
            c_term = c1 * (p_arr[i] + p_arr[i - 1]) * 0.5
            filt[i] = c_term + (c2 * filt[i - 1]) + (c3 * filt[i - 2])

        for i in range(period, n):
            f_curr = filt[i]
            slope = (filt[i - period] - f_curr) / period

            sum_diff = 0.0
            for k in range(1, period + 1):
                sum_diff += (f_curr + (k * slope)) - filt[i - k]
            sum_diff /= period

            ms[i] = (0.04 * sum_diff * sum_diff) + (0.96 * ms[i - 1])
            denom = math.sqrt(ms[i]) if ms[i] > EPSILON else FALLBACK_DENOM
            reflex[i] = sum_diff / denom

        return reflex

    @staticmethod
    def fast_crosses_above_slow(
        fast: IndicatorSeries | np.ndarray[Any, Any],
        slow: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Fast Reflex crossed above Slow Reflex."""
        logger.info("Evaluating Reflex fast_crosses_above_slow at shift=%d", shift)
        f = BaseIndicator.to_numpy(fast)
        s = BaseIndicator.to_numpy(slow)
        curr = len(f) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(f) or curr >= len(s):
            return False
        if np.isnan(f[curr]) or np.isnan(s[curr]) or np.isnan(f[prev]):
            return False
        return bool(f[prev] <= s[prev] and f[curr] > s[curr])

    @staticmethod
    def fast_crosses_below_slow(
        fast: IndicatorSeries | np.ndarray[Any, Any],
        slow: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Fast Reflex crossed below Slow Reflex."""
        logger.info("Evaluating Reflex fast_crosses_below_slow at shift=%d", shift)
        f = BaseIndicator.to_numpy(fast)
        s = BaseIndicator.to_numpy(slow)
        curr = len(f) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(f) or curr >= len(s):
            return False
        if np.isnan(f[curr]) or np.isnan(s[curr]) or np.isnan(f[prev]):
            return False
        return bool(f[prev] >= s[prev] and f[curr] < s[curr])

    @staticmethod
    def is_rising(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Reflex is rising."""
        logger.info("Evaluating Reflex is_rising at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[curr] > s[prev])

    @staticmethod
    def is_falling(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Reflex is falling."""
        logger.info("Evaluating Reflex is_falling at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[curr] < s[prev])

    @staticmethod
    def changes_direction_up(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Reflex turned upward (v0 > v1 and v1 <= v2)."""
        logger.info("Evaluating Reflex changes_direction_up at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        i0 = len(s) - 1 - shift
        i1 = i0 - 1
        i2 = i0 - 2
        if i2 < 0 or i0 >= len(s):
            return False
        if np.isnan(s[i0]) or np.isnan(s[i1]) or np.isnan(s[i2]):
            return False
        return bool(s[i0] > s[i1] and s[i1] <= s[i2])

    @staticmethod
    def changes_direction_down(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Reflex turned downward (v0 < v1 and v1 >= v2)."""
        logger.info("Evaluating Reflex changes_direction_down at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        i0 = len(s) - 1 - shift
        i1 = i0 - 1
        i2 = i0 - 2
        if i2 < 0 or i0 >= len(s):
            return False
        if np.isnan(s[i0]) or np.isnan(s[i1]) or np.isnan(s[i2]):
            return False
        return bool(s[i0] < s[i1] and s[i1] >= s[i2])
