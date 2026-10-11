"""Average True Range (ATR) indicator family.

Description:
    Computes Average True Range (ATR) volatility according to StrategyQuant X
    mathematical specification using Wilder's smoothing. Consolidates the ATR
    indicator calculation and all symmetrical condition blocks (ATRRising,
    ATRFalling, ATRCrossUp, ATRCrossDown, ATRHigher, ATRLower, ATRChangesUp,
    ATRChangesDown) into a unified Python module.

Purpose:
    FEAT-BLOCKS-INDICATOR-ATR: Average True Range volatility and conditions.

Key Capabilities:
    - FR-BLOCKS-ATR-CALCULATE: Compute True Range and smoothed ATR series.
      Associated: `ATR.calculate()`, `ATR.true_range()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-BLOCKS-ATR-CONDITIONS: Evaluate rising, falling, and level cross states.
      Associated: `ATR.is_rising()`, `ATR.crosses_above()`
      Logging: DEBUG on evaluation of ATR conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.atr import ATR

    high = np.array([10.5, 11.0, 11.2, 12.0, 11.8])
    low = np.array([9.8, 10.2, 10.5, 11.1, 10.9])
    close = np.array([10.1, 10.8, 11.0, 11.5, 11.2])

    atr_series = ATR.calculate(high, low, close, period=14)
    current_atr = atr_series.get(0)
    is_rising = ATR.is_rising(atr_series, shift=0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py -k "test_atr" --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)


class ATR(BaseIndicator):
    """Average True Range indicator family consolidating math and conditions."""

    name = "(ATR) Average True Range"
    category = "Indicators"

    @classmethod
    def true_range(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
    ) -> np.ndarray:
        """Calculate True Range array across all bars.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.

        Returns:
            1D float64 NumPy array of True Range values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)

        n = len(high_arr)
        if n == 0:
            return np.empty(0, dtype=np.float64)

        tr = np.empty(n, dtype=np.float64)
        tr[0] = high_arr[0] - low_arr[0]

        if n > 1:
            prev_c = close_arr[:-1]
            h_curr = high_arr[1:]
            l_curr = low_arr[1:]

            hl = h_curr - l_curr
            hc = np.abs(h_curr - prev_c)
            lc = np.abs(l_curr - prev_c)

            tr[1:] = np.maximum(hl, np.maximum(hc, lc))

        return tr

    @classmethod
    @override
    def calculate(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Average True Range (ATR) series using SQX Wilder smoothing.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Smoothing lookback period (default 14).

        Returns:
            IndicatorSeries containing the calculated ATR values.
        """
        if period <= 0:
            logger.warning(
                "FR-BLOCKS-ATR-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        tr = cls.true_range(high, low, close)
        n = len(tr)
        if n == 0:
            return IndicatorSeries(np.empty(0, dtype=np.float64), name="ATR")

        atr_vals = np.empty(n, dtype=np.float64)
        atr_vals[0] = tr[0]

        # SQX Wilder's smoothing algorithm
        for i in range(1, n):
            current_bar = i
            window = min(current_bar + 1, period)
            atr_vals[i] = ((window - 1) * atr_vals[i - 1] + tr[i]) / window

        logger.info(
            "FR-BLOCKS-ATR-CALCULATE: Computed ATR(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(atr_vals, name="ATR")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ATRRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ATRFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate ATRCrossUp condition."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate ATRCrossDown condition."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate ATRHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate ATRLower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ATRChangesUp condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ATRChangesDown condition."""
        return series.changes_down(shift)
