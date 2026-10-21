"""SuperTrend indicator family implementation.

Description:
    Computes Olivier Seban's SuperTrend indicator, an ATR-based trend following
    stop and reverse indicator that plots upper/lower trailing stop levels
    depending on price relation to volatility bands:
    Median = (High + Low) / 2
    Upper Band = Median + Multiplier * ATR
    Lower Band = Median - Multiplier * ATR.
    Supports MetaTrader SMA ATR (Mode 1) and Wilder Smoothed ATR (Mode 2),
    providing condition helpers for trend detection and bar breakout levels.

Purpose:
    FEAT-SERVICES-INDICATOR-SUPERTREND: SuperTrend trailing stop and trend detection.

Key Capabilities:
    - FR-SERVICES-SUPERTREND-CALCULATE: Vectorized calculation of SuperTrend line.
      Associated: `SuperTrend.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-SUPERTREND-CONDITIONS: Trend state and bar close evaluation.
      Associated: `SuperTrend.is_uptrend()`, `SuperTrend.bar_closes_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.trend.supertrend import SuperTrend

    high = np.linspace(10.0, 20.0, 30)
    low = np.linspace(8.0, 18.0, 30)
    close = np.linspace(9.0, 19.0, 30)

    st = SuperTrend.calculate(high, low, close, mode=1, atr_period=14, atr_mult=3.0)
    val = st["main"].get(0)
    trend = st["trend"].get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.trend.supertrend
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    equals,
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.volatility.atr import ATR
from app.services.indicators.volatility.mt_atr import MTATR

logger = get_logger(__name__)


class SuperTrend(BaseIndicator):
    """SuperTrend indicator family."""

    name: str = "SuperTrend"
    category: str = "Trend"

    MODE_MT = 1
    MODE_TS = 2

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        mode: int = 1,
        atr_period: int = 24,
        atr_mult: float = 3.0,
    ) -> dict[str, IndicatorSeries]:
        """Compute SuperTrend line and trend signal series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            mode: 1 for MetaTrader SMA ATR, 2 for Wilder ATR (default 1).
            atr_period: ATR smoothing period (default 24).
            atr_mult: Multiplier for ATR bands (default 3.0).

        Returns:
            Dictionary with 'main', 'trend', 'upper', and 'lower' IndicatorSeries.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if n != len(high_arr) or n != len(low_arr):
            raise ValueError("High, low, and close arrays must have equal length.")

        if atr_period <= 0:
            logger.warning(
                "FR-SERVICES-SUPERTREND-CALCULATE: Invalid atr_period %d, default 24",
                atr_period,
            )
            atr_period = 24

        if mode == cls.MODE_MT:
            atr_series = MTATR.calculate(
                high_arr, low_arr, close_arr, period=atr_period
            )
        else:
            atr_series = ATR.calculate(high_arr, low_arr, close_arr, period=atr_period)

        atr_vals = atr_series.values
        st_arr = np.zeros(n, dtype=np.float64)
        trend_arr = np.zeros(n, dtype=np.float64)
        upper_arr = np.zeros(n, dtype=np.float64)
        lower_arr = np.zeros(n, dtype=np.float64)

        if n > 0:
            median0 = (high_arr[0] + low_arr[0]) / 2.0
            atr0 = atr_vals[0] if not np.isnan(atr_vals[0]) else 0.0
            upper_arr[0] = median0 + atr_mult * atr0
            lower_arr[0] = median0 - atr_mult * atr0
            st_arr[0] = lower_arr[0]
            trend_arr[0] = 1.0 if close_arr[0] >= st_arr[0] else -1.0

        for i in range(1, n):
            median = (high_arr[i] + low_arr[i]) / 2.0
            atr_v = atr_vals[i] if not np.isnan(atr_vals[i]) else 0.0

            d_upper = median + atr_mult * atr_v
            d_lower = median - atr_mult * atr_v
            upper_arr[i] = d_upper
            lower_arr[i] = d_lower

            prev_st = st_arr[i - 1]
            curr_c = close_arr[i]
            prev_c = close_arr[i - 1]

            if curr_c > prev_st and prev_c <= prev_st:
                st_arr[i] = d_lower
            elif curr_c < prev_st and prev_c >= prev_st:
                st_arr[i] = d_upper
            elif prev_st < d_lower:
                st_arr[i] = d_lower
            elif prev_st > d_upper:
                st_arr[i] = d_upper
            else:
                st_arr[i] = prev_st

            trend_arr[i] = 1.0 if curr_c >= st_arr[i] else -1.0

        logger.info(
            "FR-SERVICES-SUPERTREND-CALCULATE: ST(m=%d, p=%d, mult=%.2f) for %d bars",
            mode,
            atr_period,
            atr_mult,
            n,
        )
        param_label = f"{mode},{atr_period},{atr_mult}"
        return {
            "main": IndicatorSeries(st_arr, name=f"SuperTrend({param_label})"),
            "trend": IndicatorSeries(
                trend_arr, name=f"SuperTrend.Trend({param_label})"
            ),
            "upper": IndicatorSeries(
                upper_arr, name=f"SuperTrend.Upper({param_label})"
            ),
            "lower": IndicatorSeries(
                lower_arr, name=f"SuperTrend.Lower({param_label})"
            ),
        }

    # Condition helpers
    @classmethod
    def is_uptrend(cls, st_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if SuperTrend is in uptrend (rising line)."""
        res = is_rising(st_dict["main"], shift=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-SUPERTREND-CONDITIONS is_uptrend shift=%d res=%s",
            shift,
            res,
        )
        return res

    @classmethod
    def is_downtrend(cls, st_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if SuperTrend is in downtrend (falling line)."""
        res = is_falling(st_dict["main"], shift=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-SUPERTREND-CONDITIONS is_downtrend shift=%d res=%s",
            shift,
            res,
        )
        return res

    @classmethod
    def is_in_range(cls, st_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if SuperTrend is in range (flat line)."""
        res = equals(
            st_dict["main"],
            st_dict["main"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=5,
        )
        logger.debug(
            "FR-SERVICES-SUPERTREND-CONDITIONS is_in_range shift=%d res=%s",
            shift,
            res,
        )
        return res

    @classmethod
    def bar_closes_above(
        cls,
        close: IndicatorSeries | Sequence[float] | np.ndarray,
        st_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is above SuperTrend."""
        return is_greater(close, st_dict["main"], shift=shift)

    @classmethod
    def bar_closes_below(
        cls,
        close: IndicatorSeries | Sequence[float] | np.ndarray,
        st_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is below SuperTrend."""
        return is_lower(close, st_dict["main"], shift=shift)


Supertrend = SuperTrend
