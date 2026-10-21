"""True Range (TrueRange) indicator family implementation.

Description:
    Computes J. Welles Wilder's True Range (TR) measuring absolute price
    volatility including overnight gaps:
    TR = max(High[t] - Low[t], abs(High[t] - Close[t-1]), abs(Low[t] - Close[t-1])).
    Provides condition helpers for volatility expansion and threshold checks.

Purpose:
    FEAT-SERVICES-INDICATOR-TRUERANGE: True Range volatility calculation and conditions.

Key Capabilities:
    - FR-SERVICES-TRUERANGE-CALCULATE: Vectorized calculation of True Range values.
      Associated: `TrueRange.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-TRUERANGE-CONDITIONS: Condition checks (rising, falling, levels).
      Associated: `TrueRange.is_rising()`, `TrueRange.is_greater()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.volatility.true_range import TrueRange

    high = np.array([10.0, 11.0, 12.0, 11.5, 12.5])
    low = np.array([9.0, 9.5, 10.5, 10.0, 11.0])
    close = np.array([9.5, 10.5, 11.0, 11.2, 12.0])
    tr = TrueRange.calculate(high, low, close)
    val = tr.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.volatility.true_range
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    changes_down,
    changes_up,
    crosses_above,
    crosses_below,
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.volatility.atr import ATR

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
            "FR-SERVICES-TRUERANGE-CALCULATE: Computed TrueRange for %d bars",
            n,
        )
        return IndicatorSeries(res, name="TrueRange")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range is rising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range is falling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate True Range crosses above level."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate True Range crosses below level."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate True Range is greater than level."""
        return is_greater(series, level, shift=shift)

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
            return is_lower(series, level, shift=shift)
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate True Range is higher than past value."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range changes up condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate True Range changes down condition."""
        return changes_down(series, shift=shift)
