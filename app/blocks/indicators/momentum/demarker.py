"""DeMarker (DEM) indicator family implementation.

Description:
    Computes Tom DeMarker's oscillator (DeM), comparing recent price extremes
    to previous period prices to identify exhaustion and market turning points.
    Calculates SMA of DeMax over the sum of SMA(DeMax) and SMA(DeMin), bounded
    within [0, 1]. Provides unified condition evaluation helpers for overbought/
    oversold crossovers and trend changes.

Purpose:
    FEAT-BLOCKS-INDICATOR-DEMARKER: DeMarker oscillator calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-DEMARKER-CALCULATE: Vectorized calculation of DeMarker values.
      Associated: `DeMarker.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-DEMARKER-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `DeMarker.is_rising()`, `DeMarker.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.demarker import DeMarker

    high = np.array([10.0, 11.0, 12.0, 12.5, 13.0])
    low = np.array([9.0, 9.5, 10.5, 11.0, 11.5])
    dem = DeMarker.calculate(high, low, period=14)
    val = dem.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.demarker
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


class DeMarker(BaseIndicator):
    """DeMarker oscillator indicator family."""

    name: str = "DeMarker"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the DeMarker oscillator series.

        Args:
            high: High prices array.
            low: Low prices array.
            period: Lookback smoothing period (default 14).

        Returns:
            IndicatorSeries containing DeMarker values in range [0, 1].
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-DEMARKER-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        de_max = np.zeros(n, dtype=np.float64)
        de_min = np.zeros(n, dtype=np.float64)

        if n > 1:
            diff_h = high_arr[1:] - high_arr[:-1]
            diff_l = low_arr[:-1] - low_arr[1:]
            de_max[1:] = np.maximum(diff_h, 0.0)
            de_min[1:] = np.maximum(diff_l, 0.0)

        avg_de_max = MovingAverage.sma(de_max, period)
        avg_de_min = MovingAverage.sma(de_min, period)

        denom = avg_de_max + avg_de_min
        res = np.zeros(n, dtype=np.float64)
        valid = (denom != 0.0) & (~np.isnan(denom))
        res[valid] = avg_de_max[valid] / denom[valid]

        logger.info(
            "FR-BLOCKS-DEMARKER-CALCULATE: Computed DeMarker(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"DeMarker({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate DEMRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate DEMFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.5, shift: int = 0
    ) -> bool:
        """Evaluate DEMCrossUp condition (crosses above level)."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.5, shift: int = 0
    ) -> bool:
        """Evaluate DEMCrossDown condition (crosses below level)."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate DEMHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate DEMLower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate DEMChangesUp turn condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate DEMChangesDown turn condition."""
        return series.changes_down(shift)
