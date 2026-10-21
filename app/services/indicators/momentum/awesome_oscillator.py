"""Awesome Oscillator (AWO) indicator family implementation.

Description:
    Computes the Awesome Oscillator (Bill Williams) measuring market momentum
    by subtracting a 34-period Simple Moving Average of median price from a
    5-period Simple Moving Average of median price. Provides unified condition
    evaluation methods for trend, zero-line crossovers, and momentum changes.

Purpose:
    FEAT-SERVICES-INDICATOR-AWO: Awesome Oscillator calculation and conditions.

Key Capabilities:
    - FR-SERVICES-AWO-CALCULATE: Vectorized calculation of AWO values.
      Associated: `AwesomeOscillator.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-AWO-CONDITIONS: Condition checks (rising, falling, crosses, turns).
      Associated: `AwesomeOscillator.is_rising()`, `AwesomeOscillator.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.awesome_oscillator import AwesomeOscillator

    high = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    low = np.array([9.0, 9.5, 10.5, 11.5, 12.0])
    awo = AwesomeOscillator.calculate(high, low, fast_period=5, slow_period=34)
    val = awo.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.momentum.awesome_oscillator
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


class AwesomeOscillator(BaseIndicator):
    """Awesome Oscillator indicator family."""

    name: str = "AwesomeOscillator"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        fast_period: int = 5,
        slow_period: int = 34,
    ) -> IndicatorSeries:
        """Compute the Awesome Oscillator series.

        Args:
            high: High prices array.
            low: Low prices array.
            fast_period: Lookback for fast SMA (default 5).
            slow_period: Lookback for slow SMA (default 34).

        Returns:
            IndicatorSeries containing the Awesome Oscillator values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)

        if fast_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid fast_period %d, defaulting to 5",
                fast_period,
            )
            fast_period = 5
        if slow_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid slow_period %d, defaulting to 34",
                slow_period,
            )
            slow_period = 34

        median = (high_arr + low_arr) / 2.0
        fast_sma = MovingAverage.sma(median, fast_period)
        slow_sma = MovingAverage.sma(median, slow_period)
        res = fast_sma - slow_sma

        logger.info(
            "FR-SERVICES-AWO-CALCULATE: Computed AWO(fast=%d, slow=%d) for %d bars",
            fast_period,
            slow_period,
            n,
        )
        return IndicatorSeries(res, name="AwesomeOscillator")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWORising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWOFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate AWOCrossUp condition (crosses above level/zero)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate AWOCrossDown condition (crosses below level/zero)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate AWOHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate AWOLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWOChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate AWOChangesDown turn condition."""
        return changes_down(series, shift=shift)
