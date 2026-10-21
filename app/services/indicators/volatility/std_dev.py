"""Standard Deviation (StdDev) indicator family implementation.

Description:
    Computes rolling population standard deviation measuring market volatility
    and price dispersion over a specified lookback period:
    StdDev = sqrt( sum((Price[t-k] - Mean)^2) / Period ).
    Provides unified condition evaluation helpers for volatility expansion,
    trend direction, and turning points.

Purpose:
    FEAT-SERVICES-INDICATOR-STDDEV: Standard Deviation volatility calculation.

Key Capabilities:
    - FR-SERVICES-STDDEV-CALCULATE: Vectorized calculation of StdDev values.
      Associated: `StdDev.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-STDDEV-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `StdDev.is_rising()`, `StdDev.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.volatility.std_dev import StdDev

    close = np.array([10.0, 11.0, 12.0, 11.5, 12.5, 13.0, 14.0])
    sd = StdDev.calculate(close, period=5)
    val = sd.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.volatility.std_dev
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

logger = get_logger(__name__)


class StdDev(BaseIndicator):
    """Standard Deviation indicator family."""

    name: str = "StdDev"
    category: str = "Volatility"

    @classmethod
    @override
    def calculate(
        cls,
        data: Sequence[float] | np.ndarray,
        period: int = 20,
    ) -> IndicatorSeries:
        """Compute rolling population standard deviation (ddof=0).

        Args:
            data: Input price series.
            period: Lookback period (default 20).

        Returns:
            IndicatorSeries containing StdDev values.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-STDDEV-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20

        res = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]
            if len(win) > 0:
                res[i] = float(np.std(win, ddof=0))

        logger.info(
            "FR-SERVICES-STDDEV-CALCULATE: Computed StdDev(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"StdDev({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate StdDevCrossUp condition."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate StdDevCrossDown condition."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate StdDevHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate StdDevLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate StdDevChangesDown turn condition."""
        return changes_down(series, shift=shift)
