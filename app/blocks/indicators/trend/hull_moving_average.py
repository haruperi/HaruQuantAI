"""Hull Moving Average (HMA) indicator family implementation.

Description:
    Computes Alan Hull's Hull Moving Average (HMA), an extremely responsive,
    low-lag moving average calculated using linear weighted moving averages:
    HMA = WMA(2 * WMA(Price, Period/2) - WMA(Price, Period), sqrt(Period)).
    Provides condition helpers for slope detection, turning points, and dual
    faster vs slower HMA crossovers.

Purpose:
    FEAT-BLOCKS-INDICATOR-HMA: Hull Moving Average low-lag trend filter.

Key Capabilities:
    - FR-BLOCKS-HMA-CALCULATE: Vectorized calculation of HMA series.
      Associated: `HullMovingAverage.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-HMA-CONDITIONS: Slope, turn, and relative speed conditions.
      Associated: `HullMovingAverage.is_rising()`, `HullMovingAverage.changes_up()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.hull_moving_average import HullMovingAverage

    close = np.linspace(10.0, 30.0, 40)
    hma = HullMovingAverage.calculate(close, period=16)
    val = hma.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.hull_moving_average
    ```
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.trend.moving_average import MovingAverage
from app.host.logging import get_logger

logger = get_logger(__name__)


class HullMovingAverage(BaseIndicator):
    """Hull Moving Average indicator family."""

    name: str = "HullMovingAverage"
    category: str = "Trend"

    @classmethod
    @override
    def calculate(
        cls,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute Hull Moving Average series.

        Args:
            close: Close prices array.
            period: Lookback period (default 14).

        Returns:
            IndicatorSeries containing HMA values.
        """
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)

        if period <= 1:
            logger.warning(
                "FR-BLOCKS-HMA-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        fast_period = max(1, math.floor(period / 2.0))
        sqrt_period = max(1, math.floor(math.sqrt(period)))

        fast_wma = MovingAverage.lwma(c_arr, fast_period)
        slow_wma = MovingAverage.lwma(c_arr, period)

        diff = 2.0 * fast_wma - slow_wma
        hma = MovingAverage.lwma(diff, sqrt_period)

        logger.info(
            "FR-BLOCKS-HMA-CALCULATE: Computed HMA(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(hma, name=f"HMA({period})")

    # Condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA is rising."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA is falling."""
        return series.is_falling(shift)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA turned upward."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if HMA turned downward."""
        return series.changes_down(shift)

    @classmethod
    def faster_above_slower(
        cls,
        faster_hma: IndicatorSeries,
        slower_hma: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Faster HMA is above Slower HMA."""
        return faster_hma.is_greater(slower_hma, shift)

    @classmethod
    def faster_below_slower(
        cls,
        faster_hma: IndicatorSeries,
        slower_hma: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Faster HMA is below Slower HMA."""
        return faster_hma.is_lower(slower_hma, shift)
