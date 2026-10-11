"""Bears Power (BEP) indicator family implementation.

Description:
    Computes Alexander Elder's Bear Power indicator from the Elder-Ray system,
    measuring the ability of sellers to drive prices below the consensus of value
    (Exponential Moving Average). Calculated as Low minus EMA of Close.
    Provides condition helpers for crossovers, trends, and turns.

Purpose:
    FEAT-BLOCKS-INDICATOR-BEARS: Bears Power indicator calculation and conditions.

Key Capabilities:
    - FR-BLOCKS-BEARS-CALCULATE: Vectorized calculation of Bears Power values.
      Associated: `BearsPower.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-BEARS-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `BearsPower.is_rising()`, `BearsPower.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.bears_power import BearsPower

    low = np.array([9.0, 9.5, 10.5, 11.5, 12.0])
    close = np.array([9.5, 10.5, 11.0, 12.5, 13.5])
    bp = BearsPower.calculate(low, close, period=14)
    val = bp.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.bears_power
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


class BearsPower(BaseIndicator):
    """Bears Power (Elder-Ray) indicator family."""

    name: str = "BearsPower"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Bears Power series.

        Args:
            low: Low prices array.
            close: Close (or computedFrom) prices array.
            period: Lookback period for EMA (default 14).

        Returns:
            IndicatorSeries containing Bears Power values.
        """
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(low_arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-BEARS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        ema = MovingAverage.ema(close_arr, period)
        res = low_arr - ema

        logger.info(
            "FR-BLOCKS-BEARS-CALCULATE: Computed BearsPower(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"BearsPower({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BEPCrossUp condition (crosses above level/zero)."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BEPCrossDown condition (crosses below level/zero)."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BEPHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BEPLower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPChangesUp turn condition."""
        return series.changes_up(shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPChangesDown turn condition."""
        return series.changes_down(shift)
