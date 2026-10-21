"""Moving Average (MA) indicator family.

Description:
    Computes Moving Averages across standard methods (Simple, Exponential,
    Smoothed/Wilder, Linear Weighted, and Triple Exponential). Consolidates
    calculations and all trend, crossover, and bar open/close vs. MA conditions
    into a unified Python module.

Purpose:
    FEAT-SERVICES-INDICATOR-MA: Moving average trend smoothing and conditions.

Key Capabilities:
    - FR-SERVICES-MA-CALCULATE: Compute SMA, EMA, SMMA, LWMA, and TEMA series.
      Associated: `MovingAverage.calculate()`, `MovingAverage.sma()`,
      `MovingAverage.ema()`, `MovingAverage.tema()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-SERVICES-MA-CONDITIONS: Evaluate trend directions, crossovers, and bar
      opens/closes.
      Associated: `MovingAverage.crosses_above()`, `MovingAverage.is_rising()`,
      `MovingAverage.bar_closes_above()`, `MovingAverage.bar_opens_above()`
      Logging: DEBUG on evaluation of MA conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.trend.moving_average import MovingAverage

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0])
    sma20 = MovingAverage.calculate(close, period=5, method=MovingAverage.SMA)
    ema20 = MovingAverage.calculate(close, period=5, method=MovingAverage.EMA)
    is_bullish = MovingAverage.is_greater(ema20, sma20)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "ma"
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class MovingAverage(BaseIndicator):
    """Moving Average family supporting SMA, EMA, SMMA, LWMA, and TEMA methods."""

    name = "(MA) Moving Average"
    category = "Indicators"

    SMA = 0
    EMA = 1
    SMMA = 2
    LWMA = 3
    TEMA = 4

    @classmethod
    def sma(cls, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        n = len(data)
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            return out

        cumsum = np.cumsum(np.insert(data, 0, 0.0))
        out[period - 1 :] = (cumsum[period:] - cumsum[:-period]) / period
        return out

    @classmethod
    def ema(cls, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        n = len(data)
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            return out

        alpha = 2.0 / (period + 1.0)
        out[period - 1] = float(np.mean(data[:period]))
        for i in range(period, n):
            out[i] = alpha * data[i] + (1.0 - alpha) * out[i - 1]
        return out

    @classmethod
    def smma(cls, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Smoothed Moving Average (Wilder's MA)."""
        n = len(data)
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            return out

        out[period - 1] = float(np.mean(data[:period]))
        for i in range(period, n):
            out[i] = (out[i - 1] * (period - 1) + data[i]) / period
        return out

    @classmethod
    def lwma(cls, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Linear Weighted Moving Average."""
        n = len(data)
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            return out

        weights = np.arange(1, period + 1, dtype=np.float64)
        denom = weights.sum()

        for i in range(period - 1, n):
            window = data[i - period + 1 : i + 1]
            out[i] = np.dot(window, weights) / denom
        return out

    @classmethod
    def tema(cls, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Triple Exponential Moving Average (`3*EMA1 - 3*EMA2 + EMA3`)."""
        n = len(data)
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            return out

        ema1 = cls.ema(data, period)
        valid1 = np.where(~np.isnan(ema1))[0]
        if len(valid1) < period:
            return out
        ema2 = np.full(n, np.nan, dtype=np.float64)
        ema2[valid1[0] :] = cls.ema(ema1[valid1[0] :], period)

        valid2 = np.where(~np.isnan(ema2))[0]
        if len(valid2) < period:
            return out
        ema3 = np.full(n, np.nan, dtype=np.float64)
        ema3[valid2[0] :] = cls.ema(ema2[valid2[0] :], period)

        valid3 = ~np.isnan(ema3)
        out[valid3] = 3.0 * ema1[valid3] - 3.0 * ema2[valid3] + ema3[valid3]
        return out

    @classmethod
    @override
    def calculate(
        cls,
        data: np.ndarray | Sequence[float],
        period: int = 14,
        method: int = 0,
    ) -> IndicatorSeries:
        """Compute the Moving Average series."""
        arr = np.asarray(data, dtype=np.float64)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-MA-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        method_names = {0: "SMA", 1: "EMA", 2: "SMMA", 3: "LWMA", 4: "TEMA"}
        m_name = method_names.get(method, "SMA")

        if method == cls.EMA:
            res = cls.ema(arr, period)
        elif method == cls.SMMA:
            res = cls.smma(arr, period)
        elif method == cls.LWMA:
            res = cls.lwma(arr, period)
        elif method == cls.TEMA:
            res = cls.tema(arr, period)
        else:
            res = cls.sma(arr, period)

        logger.info(
            "FR-SERVICES-MA-CALCULATE: Computed %s(period=%d) for %d bars",
            m_name,
            period,
            len(arr),
        )
        return IndicatorSeries(res, name=f"MA({m_name},{period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MARising condition (`MA[shift] > MA[shift + 1]`)."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MAFalling condition (`MA[shift] < MA[shift + 1]`)."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA crosses above another MA or level."""
        return crosses_above(series, other, shift=shift)

    @classmethod
    def crosses_below(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA crosses below another MA or level."""
        return crosses_below(series, other, shift=shift)

    @classmethod
    def is_greater(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA is greater than another MA or level."""
        return is_greater(series, other, shift=shift)

    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA is lower than another MA or level."""
        return is_lower(series, other, shift=shift)

    @classmethod
    def bar_closes_above(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        ma_series: IndicatorSeries | Sequence[float] | np.ndarray,
        shift: int = 0,
    ) -> bool:
        """Evaluate MABarClosesAbove (`Close[shift] > MA[shift]`)."""
        return is_greater(close_series, ma_series, shift=shift)

    @classmethod
    def bar_closes_below(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        ma_series: IndicatorSeries | Sequence[float] | np.ndarray,
        shift: int = 0,
    ) -> bool:
        """Evaluate MABarClosesBelow (`Close[shift] < MA[shift]`)."""
        return is_lower(close_series, ma_series, shift=shift)

    @classmethod
    def bar_opens_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        ma_series: IndicatorSeries | Sequence[float] | np.ndarray,
        shift: int = 0,
    ) -> bool:
        """Evaluate MABarOpensAbove (`Open[shift] > MA[shift + 1]`)."""
        return is_greater(
            open_series,
            ma_series,
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        ma_series: IndicatorSeries | Sequence[float] | np.ndarray,
        shift: int = 0,
    ) -> bool:
        """Evaluate MABarOpensBelow (`Open[shift] < MA[shift + 1]`)."""
        return is_lower(
            open_series,
            ma_series,
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_above_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        ma_series: IndicatorSeries | Sequence[float] | np.ndarray,
        shift: int = 0,
    ) -> bool:
        """Evaluate MABarOpensAboveAfterOpenBelow (`Open[s+1] < MA[s+1] < Open[s]`)."""
        return is_lower(
            open_series,
            ma_series,
            shift1=shift + 1,
            shift2=shift + 1,
            round_digits=8,
        ) and is_greater(
            open_series,
            ma_series,
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_below_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        ma_series: IndicatorSeries | Sequence[float] | np.ndarray,
        shift: int = 0,
    ) -> bool:
        """Evaluate MABarOpensBelowAfterOpenAbove (`Open[s+1] > MA[s+1] > Open[s]`)."""
        return is_greater(
            open_series,
            ma_series,
            shift1=shift + 1,
            shift2=shift + 1,
            round_digits=8,
        ) and is_lower(
            open_series,
            ma_series,
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )
