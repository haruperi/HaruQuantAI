"""MetaTrader Average True Range (MTATR) indicator family implementation.

Description:
    Computes the MetaTrader variation of Average True Range (iATR), which uses
    a Simple Moving Average (SMA) of True Range rather than J. Welles Wilder's
    exponential smoothing.
    Value = SMA(TrueRange, Period).
    Provides unified condition evaluation helpers for volatility expansion and trend.

Purpose:
    FEAT-BLOCKS-INDICATOR-MTATR: MetaTrader ATR calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-MTATR-CALCULATE: Vectorized calculation of MTATR values.
      Associated: `MTATR.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-MTATR-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `MTATR.is_rising()`, `MTATR.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.mt_atr import MTATR

    high = np.array([10.0, 11.0, 12.0, 11.5, 12.5])
    low = np.array([9.0, 9.5, 10.5, 10.0, 11.0])
    close = np.array([9.5, 10.5, 11.0, 11.2, 12.0])
    atr = MTATR.calculate(high, low, close, period=14)
    val = atr.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.mt_atr
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.trend.moving_average import MovingAverage
from app.blocks.indicators.volatility.atr import ATR
from app.host.logging import get_logger

logger = get_logger(__name__)


class MTATR(BaseIndicator):
    """MetaTrader Average True Range indicator family (SMA-smoothed True Range)."""

    name: str = "MTATR"
    category: str = "Volatility"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the MetaTrader ATR series using SMA smoothing of True Range.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Lookback period for SMA (default 14).

        Returns:
            IndicatorSeries containing MTATR values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-MTATR-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        tr = ATR.true_range(high_arr, low_arr, close_arr)
        res = MovingAverage.sma(tr, period)

        # For warmup bars (< period), compute cumulative mean matching SQX
        for i in range(min(period - 1, n)):
            res[i] = float(np.mean(tr[: i + 1]))

        logger.info(
            "FR-BLOCKS-MTATR-CALCULATE: Computed MTATR(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"MTATR({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MTATR is rising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MTATR is falling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate MTATR crosses above level."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate MTATR crosses below level."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate MTATR is greater than level."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        lookback: int = 1,
        shift: int = 0,
        level: float | None = None,
    ) -> bool:
        """Evaluate MTATR is lower than past value (or level)."""
        if level is not None:
            return series.is_lower(level, shift)
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate MTATR is higher than past value."""
        return series.is_higher(lookback, shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MTATR turn upwards condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MTATR turn downwards condition."""
        return series.changes_down(shift)
