"""Bulls Power (BUP) indicator family implementation.

Description:
    Computes Alexander Elder's Bull Power indicator from the Elder-Ray system,
    measuring the ability of buyers to drive prices above the consensus of value
    (Exponential Moving Average). Calculated as High minus EMA of Close.
    Provides condition helpers for crossovers, trends, and turns.

Purpose:
    FEAT-BLOCKS-INDICATOR-BULLS: Bulls Power indicator calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-BULLS-CALCULATE: Vectorized calculation of Bulls Power values.
      Associated: `BullsPower.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-BULLS-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `BullsPower.is_rising()`, `BullsPower.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.bulls_power import BullsPower

    high = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    close = np.array([9.5, 10.5, 11.0, 12.5, 13.5])
    bp = BullsPower.calculate(high, close, period=14)
    val = bp.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.bulls_power
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
                "FR-BLOCKS-BULLS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        ema = MovingAverage.ema(close_arr, period)
        res = high_arr - ema

        logger.info(
            "FR-BLOCKS-BULLS-CALCULATE: Computed BullsPower(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"BullsPower({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BUPCrossUp condition (crosses above level/zero)."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BUPCrossDown condition (crosses below level/zero)."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BUPHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BUPLower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPChangesUp turn condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BUPChangesDown turn condition."""
        return series.changes_down(shift)
