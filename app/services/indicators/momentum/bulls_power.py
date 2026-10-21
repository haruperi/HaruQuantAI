"""Bulls Power (BUP) indicator family implementation.

Description:
    Computes Alexander Elder's Bull Power indicator from the Elder-Ray system,
    measuring the ability of buyers to drive prices above the consensus of value
    (Exponential Moving Average). Calculated as High minus EMA of Close.
    Provides condition helpers for crossovers, trends, and turns.

Purpose:
    FEAT-SERVICES-INDICATOR-BULLS: Bulls Power calculation and conditions.

Key Capabilities:
    - FR-SERVICES-BULLS-CALCULATE: Vectorized calculation of Bulls Power values.
      Associated: `BullsPower.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-BULLS-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `BullsPower.is_rising()`, `BullsPower.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.bulls_power import BullsPower

    high = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    close = np.array([9.5, 10.5, 11.0, 12.5, 13.5])
    bp = BullsPower.calculate(high, close, period=14)
    val = bp.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.momentum.bulls_power
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
from app.services.indicators.trend.moving_average import MovingAverage

logger = get_logger(__name__)


class BullsPower(BaseIndicator):
    """Bulls Power (Elder-Ray) indicator family."""

    name: str = "BullsPower"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Bulls Power series.

        Args:
            high: High prices array.
            close: Close (or computedFrom) prices array.
            period: Lookback period for EMA (default 14).

        Returns:
            IndicatorSeries containing Bulls Power values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(high_arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-BULLS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        ema = MovingAverage.ema(close_arr, period)
        res = high_arr - ema

        logger.info(
            "FR-SERVICES-BULLS-CALCULATE: Computed BullsPower(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"BullsPower({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BUPCrossUp condition (crosses above level/zero)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BUPCrossDown condition (crosses below level/zero)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BUPHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BUPLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPChangesDown turn condition."""
        return changes_down(series, shift=shift)
