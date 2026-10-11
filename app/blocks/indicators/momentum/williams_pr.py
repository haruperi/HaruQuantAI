"""Williams Percent Range (WILL%R) indicator family implementation.

Description:
    Computes Larry Williams' Percent Range (Williams %R) momentum oscillator,
    measuring overbought and oversold levels on a scale from -100.0 to 0.0.
    Value = -100.0 * (HighestHigh - Close) / (HighestHigh - LowestLow).
    Provides unified condition evaluation helpers for level crossovers,
    trend direction, and turning points.

Purpose:
    FEAT-BLOCKS-INDICATOR-WILLIAMS: Williams %R indicator calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-WILLIAMS-CALCULATE: Vectorized calculation of Williams %R values.
      Associated: `WilliamsPR.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-WILLIAMS-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `WilliamsPR.is_rising()`, `WilliamsPR.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.williams_pr import WilliamsPR

    high = np.array([12.0, 13.0, 14.0, 13.5, 15.0])
    low = np.array([10.0, 11.0, 12.0, 11.5, 13.0])
    close = np.array([11.5, 12.5, 13.5, 12.0, 14.5])
    wpr = WilliamsPR.calculate(high, low, close, period=14)
    val = wpr.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.williams_pr
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)


class WilliamsPR(BaseIndicator):
    """Williams Percent Range indicator family."""

    name: str = "WilliamsPR"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Williams %R series bounded within [-100.0, 0.0].

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Lookback period for highest/lowest search (default 14).

        Returns:
            IndicatorSeries containing Williams %R values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-WILLIAMS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        res = np.full(n, -50.0, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            h_win = high_arr[start : i + 1]
            l_win = low_arr[start : i + 1]
            hh = float(np.max(h_win))
            ll = float(np.min(l_win))
            diff = hh - ll
            if diff != 0.0:
                res[i] = -100.0 * (hh - close_arr[i]) / diff
            else:
                res[i] = -50.0

        logger.info(
            "FR-BLOCKS-WILLIAMS-CALCULATE: Computed WilliamsPR(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"WilliamsPR({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate WPRRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate WPRFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = -50.0, shift: int = 0
    ) -> bool:
        """Evaluate WPRCrossUp condition."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = -50.0, shift: int = 0
    ) -> bool:
        """Evaluate WPRCrossDown condition."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate WPRHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate WPRLower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate WPRChangesUp turn condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate WPRChangesDown turn condition."""
        return series.changes_down(shift)
