"""Relative Strength Index (RSI) indicator family.

Description:
    Computes Relative Strength Index (RSI) according to StrategyQuant X
    RSICalculator specification. Consolidates the RSI indicator calculation
    and all symmetrical condition blocks (RSIRising, RSIFalling, RSICrossUp,
    RSICrossDown, RSIHigher, RSILower, RSIChangesUp, RSIChangesDown) into a
    unified Python module.

Purpose:
    FEAT-SERVICES-INDICATOR-RSI: Relative Strength Index momentum and conditions.

Key Capabilities:
    - FR-SERVICES-RSI-CALCULATE: Compute momentum gains/losses and RSI series.
      Associated: `RSI.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-SERVICES-RSI-CONDITIONS: Evaluate overbought/oversold and trend crosses.
      Associated: `RSI.crosses_above()`, `RSI.is_rising()`
      Logging: DEBUG on evaluation of RSI conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.rsi import RSI

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.1, 11.8])
    rsi_series = RSI.calculate(close, period=14)
    current_rsi = rsi_series.get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py --no-cov
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


class RSI(BaseIndicator):
    """Relative Strength Index indicator family consolidating math and conditions."""

    name = "(RSI) Relative Strength Index"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        close: np.ndarray | Sequence[float],
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Relative Strength Index (RSI) series.

        Args:
            close: Close prices array.
            period: Smoothing lookback period (default 14).

        Returns:
            IndicatorSeries containing the calculated RSI values (0 to 100).
        """
        c = np.asarray(close, dtype=np.float64)
        n = len(c)
        if n == 0:
            return IndicatorSeries(np.empty(0, dtype=np.float64), name="RSI")

        if period <= 0:
            logger.warning(
                "FR-SERVICES-RSI-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        min_price_bars = 2
        rsi_vals = np.full(n, np.nan, dtype=np.float64)
        if n < min_price_bars:
            return IndicatorSeries(rsi_vals, name="RSI")

        deltas = np.diff(c)
        ups = np.maximum(deltas, 0.0)
        downs = np.maximum(-deltas, 0.0)

        if n <= period:
            return IndicatorSeries(rsi_vals, name="RSI")

        cur_avg_up = float(np.mean(ups[:period]))
        cur_avg_down = float(np.mean(downs[:period]))

        if cur_avg_down != 0.0:
            rsi_vals[period] = 100.0 - 100.0 / (1.0 + cur_avg_up / cur_avg_down)
        elif cur_avg_up != 0.0:
            rsi_vals[period] = 100.0
        else:
            rsi_vals[period] = 50.0

        for i in range(period + 1, n):
            up = ups[i - 1]
            down = downs[i - 1]

            cur_avg_up = (cur_avg_up * (period - 1) + up) / period
            cur_avg_down = (cur_avg_down * (period - 1) + down) / period

            if cur_avg_down != 0.0:
                rsi_vals[i] = 100.0 - 100.0 / (1.0 + cur_avg_up / cur_avg_down)
            elif cur_avg_up != 0.0:
                rsi_vals[i] = 100.0
            else:
                rsi_vals[i] = 50.0

        logger.info(
            "FR-SERVICES-RSI-CALCULATE: Computed RSI(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(rsi_vals, name="RSI")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate RSIRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate RSIFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate RSICrossUp condition."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate RSICrossDown condition."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate RSIHigher condition."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate RSILower condition."""
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)

    @classmethod
    def changes_up(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate RSIChangesUp condition."""
        return changes_up(series, shift=shift)

    @classmethod
    def changes_down(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate RSIChangesDown condition."""
        return changes_down(series, shift=shift)
