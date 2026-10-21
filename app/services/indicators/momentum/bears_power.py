"""Bears Power (BEP) indicator family implementation.

Description:
    Computes Alexander Elder's Bear Power indicator from the Elder-Ray system,
    measuring the ability of sellers to drive prices below the consensus of value
    (Exponential Moving Average). Calculated as Low minus EMA of Close.
    Provides condition helpers for crossovers, trends, and turns.

Purpose:
    FEAT-SERVICES-INDICATOR-BEARS: Bears Power calculation and conditions.

Key Capabilities:
    - FR-SERVICES-BEARS-CALCULATE: Vectorized calculation of Bears Power values.
      Associated: `BearsPower.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-BEARS-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `BearsPower.is_rising()`, `BearsPower.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.bears_power import BearsPower

    low = np.array([9.0, 9.5, 10.5, 11.5, 12.0])
    close = np.array([9.5, 10.5, 11.0, 12.5, 13.5])
    bp = BearsPower.calculate(low, close, period=14)
    val = bp.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.momentum.bears_power
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
                "FR-SERVICES-BEARS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        ema = MovingAverage.ema(close_arr, period)
        res = low_arr - ema

        logger.info(
            "FR-SERVICES-BEARS-CALCULATE: Computed BearsPower(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"BearsPower({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BEPCrossUp condition (crosses above level/zero)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate BEPCrossDown condition (crosses below level/zero)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BEPHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate BEPLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate BEPChangesDown turn condition."""
        return changes_down(series, shift=shift)
