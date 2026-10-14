"""Kaufman Efficiency Ratio (KER) indicator family implementation.

Description:
    Computes Perry Kaufman's Efficiency Ratio measuring the trend efficiency
    relative to market noise/volatility over a lookback period:
    Direction = |Close[t] - Close[t - Period]|
    Volatility = sum(|Close[k] - Close[k - 1]| for k in [t - Period + 1, t])
    KER = Direction / Volatility (bounded in [0.0, 1.0]).
    Provides condition helpers for efficiency threshold boundaries and slope.

Purpose:
    FEAT-SERVICES-INDICATOR-KER: Kaufman Efficiency Ratio trend efficiency calculation.

Key Capabilities:
    - FR-SERVICES-KER-CALCULATE: Vectorized calculation of KER values.
      Associated: `KaufmanEfficiencyRatio.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-KER-CONDITIONS: Level threshold and slope condition checks.
      Associated: `KaufmanEfficiencyRatio.is_above_level()`,
                  `KaufmanEfficiencyRatio.is_below_level()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.kaufman_efficiency_ratio import KaufmanEfficiencyRatio

    close = np.array([10.0, 10.5, 11.0, 11.2, 11.8, 12.5, 13.0])
    ker = KaufmanEfficiencyRatio.calculate(close, period=5)
    val = ker.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.kaufman_efficiency_ratio
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class KaufmanEfficiencyRatio(BaseIndicator):
    """Kaufman Efficiency Ratio indicator family."""

    name: str = "KaufmanEfficiencyRatio"
    category: str = "Trend"

    @classmethod
    @override
    def calculate(
        cls,
        close: Sequence[float] | np.ndarray,
        period: int = 10,
    ) -> IndicatorSeries:
        """Compute Kaufman Efficiency Ratio series.

        Args:
            close: Close prices array.
            period: Lookback window period (default 10).

        Returns:
            IndicatorSeries containing KER values in [0.0, 1.0].
        """
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-KER-CALCULATE: Invalid period %d, defaulting to 10",
                period,
            )
            period = 10

        res = np.zeros(n, dtype=np.float64)
        if n <= period:
            logger.info(
                "FR-SERVICES-KER-CALCULATE: Insufficient bars (%d <= %d), all 0.0",
                n,
                period,
            )
            return IndicatorSeries(res, name=f"KER({period})")

        diffs = np.abs(np.diff(c_arr))

        for t in range(period, n):
            change = abs(c_arr[t] - c_arr[t - period])
            vol_sum = float(np.sum(diffs[t - period : t]))
            if vol_sum > 0:
                res[t] = min(1.0, change / vol_sum)
            else:
                res[t] = 0.0

        logger.info(
            "FR-SERVICES-KER-CALCULATE: Computed KER(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"KER({period})")

    # Condition helpers
    @classmethod
    def is_above_level(
        cls, series: IndicatorSeries, level: float = 0.5, shift: int = 0
    ) -> bool:
        """Evaluate if KER at shift is above level threshold."""
        return series.is_greater(level, shift)

    @classmethod
    def is_below_level(
        cls, series: IndicatorSeries, level: float = 0.5, shift: int = 0
    ) -> bool:
        """Evaluate if KER at shift is below level threshold."""
        return series.is_lower(level, shift)

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if KER is rising."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if KER is falling."""
        return series.is_falling(shift)
