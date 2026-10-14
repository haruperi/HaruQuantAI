"""Bar Range (BarRange) indicator family implementation.

Description:
    Computes the price range of each bar calculated as High minus Low.
    Provides condition helpers for range expansion/contraction analysis,
    including biggest range in period, smallest range in period, and relative
    range comparisons.

Purpose:
    FEAT-SERVICES-INDICATOR-BARRANGE: Bar range calculation and range conditions.

Key Capabilities:
    - FR-SERVICES-BARRANGE-CALCULATE: Vectorized calculation of bar ranges.
      Associated: `BarRange.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-BARRANGE-CONDITIONS: Condition checks (biggest, smallest, higher).
      Associated: `BarRange.is_biggest_range()`, `BarRange.is_smallest_range()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.bar_range import BarRange

    high = np.array([10.0, 11.5, 12.0, 13.0, 14.0])
    low = np.array([9.0, 10.0, 10.5, 11.0, 12.5])
    rng = BarRange.calculate(high, low)
    val = rng.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.bar_range
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class BarRange(BaseIndicator):
    """Bar Range indicator family."""

    name: str = "BarRange"
    category: str = "Ranges"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
    ) -> IndicatorSeries:
        """Compute the bar range series (High - Low).

        Args:
            high: High prices array.
            low: Low prices array.

        Returns:
            IndicatorSeries containing bar range values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)

        res = high_arr - low_arr

        logger.info(
            "FR-SERVICES-BARRANGE-CALCULATE: Computed BarRange for %d bars",
            n,
        )
        return IndicatorSeries(res, name="BarRange")

    # Unified condition helpers
    @classmethod
    def is_biggest_range(
        cls,
        series: IndicatorSeries,
        period: int = 5,
        shift: int = 0,
        lookback: int | None = None,
    ) -> bool:
        """Evaluate if range at shift is the highest among past period bars."""
        if lookback is not None:
            period = lookback
        val = series.get(shift)
        if np.isnan(val) or period <= 1:
            return False
        for s in range(shift + 1, shift + period):
            other = series.get(s)
            if np.isnan(other) or val <= other:
                return False
        return True

    @classmethod
    def is_smallest_range(
        cls,
        series: IndicatorSeries,
        period: int = 5,
        shift: int = 0,
        lookback: int | None = None,
    ) -> bool:
        """Evaluate if range at shift is the lowest among past period bars."""
        if lookback is not None:
            period = lookback
        val = series.get(shift)
        if np.isnan(val) or period <= 1:
            return False
        for s in range(shift + 1, shift + period):
            other = series.get(s)
            if np.isnan(other) or val >= other:
                return False
        return True

    @classmethod
    def is_highest_in_range(
        cls,
        series: IndicatorSeries | Sequence[float] | np.ndarray,
        lookback: int = 1,
        shift: int = 0,
    ) -> bool:
        """Evaluate if range at shift is higher than range lookback bars ago."""
        if not isinstance(series, IndicatorSeries):
            series = IndicatorSeries(series, name="Series")
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lowest_in_range(
        cls,
        series: IndicatorSeries | Sequence[float] | np.ndarray,
        lookback: int = 1,
        shift: int = 0,
    ) -> bool:
        """Evaluate if range at shift is lower than range lookback bars ago."""
        if not isinstance(series, IndicatorSeries):
            series = IndicatorSeries(series, name="Series")
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def in_range_pips(
        cls,
        series: IndicatorSeries,
        min_pips: float,
        max_pips: float,
        pip_size: float = 0.0001,
        shift: int = 0,
    ) -> bool:
        """Evaluate if bar range in pips is between min_pips and max_pips."""
        val = series.get(shift)
        if np.isnan(val) or pip_size <= 0:
            return False
        pips = val / pip_size
        return min_pips <= pips <= max_pips

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate range is rising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate range is falling condition."""
        return series.is_falling(shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate range is greater than level condition."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate range is lower than level condition."""
        return series.is_lower(level, shift)
