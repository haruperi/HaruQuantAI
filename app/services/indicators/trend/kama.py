"""Kaufman's Adaptive Moving Average (KAMA) indicator family implementation.

Description:
    Computes Perry Kaufman's Adaptive Moving Average (KAMA) dynamically adjusting
    smoothing rate based on market efficiency and volatility:
    SC = (KER * (FastestSC - SlowestSC) + SlowestSC)^2
    KAMA[t] = KAMA[t-1] + SC * (Price[t] - KAMA[t-1]).
    Provides condition helpers for slope detection, price crosses, and dual-speed
    fast vs slow KAMA alignment.

Purpose:
    FEAT-SERVICES-INDICATOR-KAMA: Kaufman's Adaptive Moving Average calculation.

Key Capabilities:
    - FR-SERVICES-KAMA-CALCULATE: Vectorized adaptive smoothing calculation.
      Associated: `KAMA.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-KAMA-CONDITIONS: Slope, price cross, and dual-speed comparisons.
      Associated: `KAMA.is_rising()`, `KAMA.bar_closes_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.trend.kama import KAMA

    close = np.linspace(10.0, 30.0, 50)
    kama = KAMA.calculate(close, er_period=10, fast_period=2, slow_period=30)
    val = kama.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.trend.kama
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.trend.kaufman_efficiency_ratio import (
    KaufmanEfficiencyRatio,
)

logger = get_logger(__name__)


class KAMA(BaseIndicator):
    """Kaufman's Adaptive Moving Average indicator family."""

    name: str = "KAMA"
    category: str = "Trend"

    @classmethod
    @override
    def calculate(
        cls,
        close: Sequence[float] | np.ndarray,
        er_period: int = 10,
        fast_period: int = 2,
        slow_period: int = 30,
    ) -> IndicatorSeries:
        """Compute KAMA adaptive moving average series.

        Args:
            close: Close prices array.
            er_period: Efficiency ratio lookback period (default 10).
            fast_period: Fast EMA lookback period (default 2).
            slow_period: Slow EMA lookback period (default 30).

        Returns:
            IndicatorSeries containing KAMA values.
        """
        c_arr = np.asarray(close, dtype=np.float64)
        n = len(c_arr)

        if er_period <= 0:
            er_period = 10
        if fast_period <= 0:
            fast_period = 2
        if slow_period <= 0:
            slow_period = 30

        res = np.zeros(n, dtype=np.float64)
        max_p = max(fast_period, slow_period, er_period)

        if n == 0:
            return IndicatorSeries(
                res, name=f"KAMA({er_period},{fast_period},{slow_period})"
            )

        if n < max_p:
            res[:] = c_arr
            return IndicatorSeries(
                res, name=f"KAMA({er_period},{fast_period},{slow_period})"
            )

        er_series = KaufmanEfficiencyRatio.calculate(c_arr, period=er_period)
        er_vals = er_series.values

        fast_sc = 2.0 / (float(fast_period) + 1.0)
        slow_sc = 2.0 / (float(slow_period) + 1.0)
        smoothing_consts = np.square(er_vals * (fast_sc - slow_sc) + slow_sc)

        res[:max_p] = c_arr[:max_p]

        for t in range(max_p, n):
            sc = smoothing_consts[t]
            res[t] = res[t - 1] + sc * (c_arr[t] - res[t - 1])

        logger.info(
            "FR-SERVICES-KAMA-CALCULATE: Computed KAMA(%d,%d,%d) for %d bars",
            er_period,
            fast_period,
            slow_period,
            n,
        )
        return IndicatorSeries(
            res, name=f"KAMA({er_period},{fast_period},{slow_period})"
        )

    # Condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if KAMA is rising."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if KAMA is falling."""
        return is_falling(series, shift=shift)

    @classmethod
    def bar_closes_above(
        cls,
        close: IndicatorSeries | Sequence[float] | np.ndarray,
        kama_series: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is above KAMA."""
        return is_greater(close, kama_series, shift=shift)

    @classmethod
    def bar_closes_below(
        cls,
        close: IndicatorSeries | Sequence[float] | np.ndarray,
        kama_series: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is below KAMA."""
        return is_lower(close, kama_series, shift=shift)

    @classmethod
    def fast_above_slow(
        cls,
        fast_kama: IndicatorSeries,
        slow_kama: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Fast KAMA is above Slow KAMA."""
        return is_greater(fast_kama, slow_kama, shift=shift)

    @classmethod
    def fast_below_slow(
        cls,
        fast_kama: IndicatorSeries,
        slow_kama: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if Fast KAMA is below Slow KAMA."""
        return is_lower(fast_kama, slow_kama, shift=shift)
