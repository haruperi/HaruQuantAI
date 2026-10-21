"""Momentum (MO) indicator family implementation.

Description:
    Computes price momentum as the ratio of current price to historical price
    over a lookback period, centered at 100.0.
    Value = Price[t] * 100.0 / Price[t - Period].
    Provides unified condition evaluation helpers for level crossovers,
    trend direction, and turning points.

Purpose:
    FEAT-SERVICES-INDICATOR-MOMENTUM: Momentum calculation and conditions.

Key Capabilities:
    - FR-SERVICES-MOMENTUM-CALCULATE: Vectorized calculation of Momentum values.
      Associated: `Momentum.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-MOMENTUM-CONDITIONS: Condition checks (rising, falling, crosses).
      Associated: `Momentum.is_rising()`, `Momentum.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.momentum import Momentum

    close = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    mom = Momentum.calculate(close, period=3)
    val = mom.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.momentum.momentum
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


class Momentum(BaseIndicator):
    """Momentum indicator family."""

    name: str = "Momentum"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        data: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Momentum series centered at 100.0.

        Args:
            data: Price series array (e.g. close).
            period: Lookback period (default 14).

        Returns:
            IndicatorSeries containing Momentum values.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-MOMENTUM-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        res = np.full(n, 100.0, dtype=np.float64)
        for i in range(1, n):
            past_idx = max(0, i - period)
            denom = arr[past_idx]
            if denom != 0.0 and not np.isnan(denom):
                res[i] = (arr[i] * 100.0) / denom
            else:
                res[i] = 100.0

        logger.info(
            "FR-SERVICES-MOMENTUM-CALCULATE: Computed Momentum(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"Momentum({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 100.0, shift: int = 0
    ) -> bool:
        """Evaluate MomCrossUp condition (crosses above level/100)."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 100.0, shift: int = 0
    ) -> bool:
        """Evaluate MomCrossDown condition (crosses below level/100)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate MomHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate MomLower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomChangesUp turn condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate MomChangesDown turn condition."""
        return changes_down(series, shift=shift)
