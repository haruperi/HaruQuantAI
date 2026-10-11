"""True Range (TrueRange) indicator family implementation.

Description:
    Computes J. Welles Wilder's True Range (TR) measuring absolute price
    volatility including overnight gaps:
    TR = max(High[t] - Low[t], abs(High[t] - Close[t-1]), abs(Low[t] - Close[t-1])).
    Provides condition helpers for volatility expansion and threshold checks.

Purpose:
    FEAT-BLOCKS-INDICATOR-TRUERANGE: True Range volatility calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-TRUERANGE-CALCULATE: Vectorized calculation of True Range values.
      Associated: `TrueRange.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-TRUERANGE-CONDITIONS: Condition checks (rising, falling, levels).
      Associated: `TrueRange.is_rising()`, `TrueRange.is_greater()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.true_range import TrueRange

    high = np.array([10.0, 11.0, 12.0, 11.5, 12.5])
    low = np.array([9.0, 9.5, 10.5, 10.0, 11.0])
    close = np.array([9.5, 10.5, 11.0, 11.2, 12.0])
    tr = TrueRange.calculate(high, low, close)
    val = tr.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.true_range
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.volatility.atr import ATR
from app.host.logging import get_logger

logger = get_logger(__name__)


class TrueRange(BaseIndicator):
    """True Range indicator family."""

    name: str = "TrueRange"
    category: str = "Ranges"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
    ) -> IndicatorSeries:
        """Compute the True Range series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.

        Returns:
            IndicatorSeries containing True Range values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        res = ATR.true_range(high_arr, low_arr, close_arr)

        logger.info(
            "FR-BLOCKS-TRUERANGE-CALCULATE: Computed TrueRange for %d bars",
            n,
        )
        return IndicatorSeries(res, name="TrueRange")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range is rising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range is falling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate True Range crosses above level."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate True Range crosses below level."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate True Range is greater than level."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        lookback: int = 1,
        shift: int = 0,
        level: float | None = None,
    ) -> bool:
        """Evaluate True Range is lower than past value (or level)."""
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
        """Evaluate True Range is higher than past value."""
        return series.is_higher(lookback, shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range changes up condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range changes down condition."""
        return series.changes_down(shift)
