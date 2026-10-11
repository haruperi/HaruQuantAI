"""Moving Average (MA) indicator family.

Description:
    Computes Moving Averages across standard methods (Simple, Exponential,
    Smoothed/Wilder, and Linear Weighted) according to StrategyQuant X
    MovingAverage specification. Consolidates calculations and all trend/cross
    conditions into a unified Python module.

Purpose:
    FEAT-BLOCKS-INDICATOR-MA: Moving average trend smoothing and conditions.

Key Capabilities:
    - FR-BLOCKS-MA-CALCULATE: Compute SMA, EMA, SMMA, and LWMA series.
      Associated: `MovingAverage.calculate()`, `MovingAverage.sma()`,
      `MovingAverage.ema()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-BLOCKS-MA-CONDITIONS: Evaluate moving average trend directions and crossovers.
      Associated: `MovingAverage.crosses_above()`, `MovingAverage.is_rising()`
      Logging: DEBUG on evaluation of MA conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.moving_average import MovingAverage

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0])
    sma20 = MovingAverage.calculate(close, period=5, method=MovingAverage.SMA)
    ema20 = MovingAverage.calculate(close, period=5, method=MovingAverage.EMA)
    is_bullish = ema20.is_greater(sma20)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py -k "test_moving_average" --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)


class MovingAverage(BaseIndicator):
    """Moving Average family supporting SMA, EMA, SMMA, and LWMA methods."""

    name = "(MA) Moving Average"
    category = "Indicators"

    SMA = 0
    EMA = 1
    SMMA = 2
    LWMA = 3

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
    @override
    def calculate(
        cls,
        data: np.ndarray | Sequence[float],
        period: int = 14,
        method: int = 0,
    ) -> IndicatorSeries:
        """Compute the Moving Average series.

        Args:
            data: Input price series.
            period: Smoothing period (default 14).
            method: 0=SMA, 1=EMA, 2=SMMA, 3=LWMA.

        Returns:
            IndicatorSeries containing the smoothed moving average.
        """
        arr = np.asarray(data, dtype=np.float64)
        if period <= 0:
            logger.warning(
                "FR-BLOCKS-MA-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        method_names = {0: "SMA", 1: "EMA", 2: "SMMA", 3: "LWMA"}
        m_name = method_names.get(method, "SMA")

        if method == cls.EMA:
            res = cls.ema(arr, period)
        elif method == cls.SMMA:
            res = cls.smma(arr, period)
        elif method == cls.LWMA:
            res = cls.lwma(arr, period)
        else:
            res = cls.sma(arr, period)

        logger.info(
            "FR-BLOCKS-MA-CALCULATE: Computed %s(period=%d) for %d bars",
            m_name,
            period,
            len(arr),
        )
        return IndicatorSeries(res, name=f"MA({m_name},{period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MA is rising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MA is falling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA crosses above another MA or level."""
        return series.crosses_above(other, shift)

    @classmethod
    def crosses_below(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA crosses below another MA or level."""
        return series.crosses_below(other, shift)

    @classmethod
    def is_greater(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA is greater than another MA or level."""
        return series.is_greater(other, shift)

    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        other: float | IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate MA is lower than another MA or level."""
        return series.is_lower(other, shift)
