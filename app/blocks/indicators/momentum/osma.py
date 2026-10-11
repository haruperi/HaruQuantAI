"""Moving Average of Oscillator (OSMA) indicator family implementation.

Description:
    Computes the Moving Average of Oscillator (OSMA / MACD Histogram), measuring
    the difference between the MACD oscillator (Fast EMA minus Slow EMA) and its
    signal line (Simple Moving Average of MACD), centered at 0.0.
    Value = (FastEMA - SlowEMA) - SMA(FastEMA - SlowEMA, SignalPeriod).
    Provides unified condition evaluation helpers for zero-line crossovers,
    momentum turns, and trend direction.

Purpose:
    FEAT-BLOCKS-INDICATOR-OSMA: OSMA indicator calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-OSMA-CALCULATE: Vectorized calculation of OSMA values.
      Associated: `OSMA.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-OSMA-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `OSMA.is_rising()`, `OSMA.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.osma import OSMA

    close = np.linspace(10.0, 30.0, 50)
    osma = OSMA.calculate(close, fast_ema=12, slow_ema=26, signal_period=9)
    val = osma.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.osma
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.trend.moving_average import MovingAverage
from app.host.logging import get_logger

logger = get_logger(__name__)


class OSMA(BaseIndicator):
    """Moving Average of Oscillator (OSMA) indicator family."""

    name: str = "OSMA"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        data: Sequence[float] | np.ndarray,
        fast_ema: int = 12,
        slow_ema: int = 26,
        signal_period: int = 9,
    ) -> IndicatorSeries:
        """Compute the OSMA series centered at 0.0.

        Args:
            data: Input price series (e.g. close).
            fast_ema: Lookback for fast EMA (default 12).
            slow_ema: Lookback for slow EMA (default 26).
            signal_period: Lookback for signal SMA (default 9).

        Returns:
            IndicatorSeries containing OSMA values.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if fast_ema <= 0:
            fast_ema = 12
        if slow_ema <= 0:
            slow_ema = 26
        if signal_period <= 0:
            signal_period = 9

        fast_arr = MovingAverage.ema(arr, fast_ema)
        slow_arr = MovingAverage.ema(arr, slow_ema)
        macd = fast_arr - slow_arr

        res = np.full(n, np.nan, dtype=np.float64)
        valid_indices = np.where(~np.isnan(macd))[0]
        if len(valid_indices) >= signal_period:
            first_idx = valid_indices[0]
            valid_macd = macd[first_idx:]
            sig_part = MovingAverage.sma(valid_macd, signal_period)
            res[first_idx:] = valid_macd - sig_part

        logger.info(
            "FR-BLOCKS-OSMA-CALCULATE: Computed OSMA(%d, %d, %d) for %d bars",
            fast_ema,
            slow_ema,
            signal_period,
            n,
        )
        return IndicatorSeries(res, name=f"OSMA({fast_ema},{slow_ema},{signal_period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMARising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMAFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMACrossZeroUp / crosses above level condition."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMACrossZeroDown / crosses below level condition."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_greater(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMAHigherZero / greater than level condition."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate OSMALowerZero / lower than level condition."""
        return series.is_lower(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate OSMA is higher than past value."""
        return series.is_higher(lookback, shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMAChangesUp turn condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate OSMAChangesDown turn condition."""
        return series.changes_down(shift)
