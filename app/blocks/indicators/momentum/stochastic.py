"""Stochastic Oscillator (STOCH) indicator family.

Description:
    Computes Stochastic Oscillator (%K, Slow %K, and Slow %D) according to
    StrategyQuant X specification. Consolidates calculations and all %K/%D line
    crossovers, overbought, and oversold conditions into a unified Python module.

Purpose:
    FEAT-BLOCKS-INDICATOR-STOCH: Stochastic momentum oscillator and conditions.

Key Capabilities:
    - FR-BLOCKS-STOCH-CALCULATE: Compute %K and %D series.
      Associated: `Stochastic.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-BLOCKS-STOCH-CONDITIONS: Evaluate %K/%D crossovers and overbought levels.
      Associated: `Stochastic.k_crosses_above_d()`,
      `Stochastic.k_crosses_below_d()`
      Logging: DEBUG on evaluation of Stochastic conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.stochastic import Stochastic

    high = np.array([12.0, 12.5, 12.8, 12.2, 13.0, 12.9, 13.2])
    low = np.array([11.2, 11.5, 12.0, 11.8, 12.1, 12.0, 12.5])
    close = np.array([11.8, 12.2, 12.1, 12.0, 12.8, 12.6, 13.0])

    stoch = Stochastic.calculate(high, low, close, k_period=5, d_period=3, slowing=3)
    k_val = stoch["k"].get(0)
    d_val = stoch["d"].get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py -k "test_stochastic" --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.trend.moving_average import MovingAverage
from app.host.logging import get_logger

logger = get_logger(__name__)


class Stochastic(BaseIndicator):
    """Stochastic Oscillator family consolidating %K, %D lines and conditions."""

    name = "(STOCH) Stochastic"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
        k_period: int = 14,
        *,
        d_period: int = 3,
        slowing: int = 3,
    ) -> dict[str, IndicatorSeries]:
        """Compute the Stochastic %K and %D series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            k_period: Lookback period for highest high/lowest low (default 14).
            d_period: %D smoothing period (default 3).
            slowing: %K slowing smoothing period (default 3).

        Returns:
            Dictionary with 'k' and 'd' series (0 to 100).
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if k_period <= 0:
            logger.warning(
                "FR-BLOCKS-STOCH-CALCULATE: Invalid k_period %d, defaulting to 14",
                k_period,
            )
            k_period = 14
        if d_period <= 0:
            d_period = 3
        if slowing <= 0:
            slowing = 3

        raw_k = np.full(n, np.nan, dtype=np.float64)
        for i in range(k_period - 1, n):
            h_win = high_arr[i - k_period + 1 : i + 1]
            l_win = low_arr[i - k_period + 1 : i + 1]
            hh = float(np.max(h_win))
            ll = float(np.min(l_win))
            diff = hh - ll
            if diff != 0.0:
                raw_k[i] = ((close_arr[i] - ll) / diff) * 100.0
            else:
                raw_k[i] = 50.0

        # Slow %K
        valid_k_idx = np.where(~np.isnan(raw_k))[0]
        slow_k = np.full(n, np.nan, dtype=np.float64)
        if len(valid_k_idx) >= slowing:
            first_idx = valid_k_idx[0]
            valid_slice = raw_k[first_idx:]
            slow_k[first_idx:] = MovingAverage.sma(valid_slice, slowing)

        # Slow %D
        valid_d_idx = np.where(~np.isnan(slow_k))[0]
        slow_d = np.full(n, np.nan, dtype=np.float64)
        if len(valid_d_idx) >= d_period:
            first_idx = valid_d_idx[0]
            valid_slice = slow_k[first_idx:]
            slow_d[first_idx:] = MovingAverage.sma(valid_slice, d_period)

        logger.info(
            "FR-BLOCKS-STOCH-CALCULATE: Computed Stoch(%d,%d,%d) for %d bars",
            k_period,
            d_period,
            slowing,
            n,
        )

        return {
            "k": IndicatorSeries(slow_k, name="Stoch.K"),
            "d": IndicatorSeries(slow_d, name="Stoch.D"),
        }

    # Unified condition helpers
    @classmethod
    def k_crosses_above_d(
        cls, stoch: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate %K crosses above %D."""
        return stoch["k"].crosses_above(stoch["d"], shift)

    @classmethod
    def k_crosses_below_d(
        cls, stoch: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate %K crosses below %D."""
        return stoch["k"].crosses_below(stoch["d"], shift)

    @classmethod
    def k_higher_d(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate %K is higher than %D."""
        return stoch["k"].is_greater(stoch["d"], shift)

    @classmethod
    def k_lower_d(cls, stoch: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate %K is lower than %D."""
        return stoch["k"].is_lower(stoch["d"], shift)
