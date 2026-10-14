"""Gann Hi-Lo Activator Indicator Block.

Description:
    Implements the Gann High-Low Activator (GHA) trailing stop line using
    simple moving averages of High and Low prices. When price breaks above
    the SMA of Highs, the trend switches to bullish with the trailing stop
    following the SMA of Lows. When price drops below the SMA of Lows, the
    trend switches to bearish with the trailing stop tracking the SMA of Highs.

Purpose:
    FEAT-SERVICES-INDICATOR-GANNHILO

Key Capabilities:
    - FR-SERVICES-GANNHILO-CALCULATE: Computes GHA stop line and trend regime.
    - FR-SERVICES-GANNHILO-CONDITIONS: Evaluates uptrend/downtrend states.

Python API Usage:
    ```python
    from app.services.indicators.gann_hi_lo import GannHiLo

    gh = GannHiLo.calculate(high, low, close, period=10)
    gha = gh["gha"]
    trend = gh["trend"]

    # Condition checks
    is_up = GannHiLo.is_uptrend(close, gha, shift=0)
    is_down = GannHiLo.is_downtrend(close, gha, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class GannHiLo(BaseIndicator):
    """Gann High-Low Activator indicator with trend regime tracking."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        period: int = 10,
    ) -> dict[str, IndicatorSeries]:
        """Compute Gann Hi-Lo Activator, band lines, and trend state.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            period: Smoothing period for High and Low SMAs (default 10).

        Returns:
            Dictionary containing:
                - 'gha': Gann High-Low Activator trailing line.
                - 'gh_high': Simple moving average of Highs.
                - 'gh_low': Simple moving average of Lows.
                - 'trend': Trend regime series (1.0 for Uptrend, -1.0 for Downtrend).

        Raises:
            ValueError: If period < 1 or input array lengths mismatch.
        """
        logger.info(
            "GannHiLo calculation initiated with period=%d",
            period,
            extra={"period": period},
        )
        if period < 1:
            raise ValueError(f"Period must be >= 1, got {period}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)

        n = len(c_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if not (len(h_arr) == len(l_arr) == n):
            raise ValueError(
                f"Array mismatch: high({len(h_arr)}), low({len(l_arr)}), close({n})"
            )

        gha_vals = np.full(n, np.nan, dtype=np.float64)
        gh_high_vals = np.full(n, np.nan, dtype=np.float64)
        gh_low_vals = np.full(n, np.nan, dtype=np.float64)
        trend_vals = np.zeros(n, dtype=np.float64)

        if n < period:
            return {
                "gha": IndicatorSeries(gha_vals, name=f"GHA({period})"),
                "gh_high": IndicatorSeries(gh_high_vals, name=f"GHHigh({period})"),
                "gh_low": IndicatorSeries(gh_low_vals, name=f"GHLow({period})"),
                "trend": IndicatorSeries(trend_vals, name=f"GHTrend({period})"),
            }

        # Calculate SMA of High and Low
        for i in range(period - 1, n):
            gh_high_vals[i] = np.mean(h_arr[i - period + 1 : i + 1])
            gh_low_vals[i] = np.mean(l_arr[i - period + 1 : i + 1])

        hlv = 1.0  # Default initial trend state
        for i in range(period, n):
            prev_high_sma = gh_high_vals[i - 1]
            prev_low_sma = gh_low_vals[i - 1]
            curr_close = c_arr[i]

            if curr_close > prev_high_sma:
                hlv = 1.0
            elif curr_close < prev_low_sma:
                hlv = -1.0

            trend_vals[i] = hlv
            gha_vals[i] = gh_high_vals[i] if hlv == -1.0 else gh_low_vals[i]

        logger.info(
            "GannHiLo calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )

        return {
            "gha": IndicatorSeries(gha_vals, name=f"GHA({period})"),
            "gh_high": IndicatorSeries(gh_high_vals, name=f"GHHigh({period})"),
            "gh_low": IndicatorSeries(gh_low_vals, name=f"GHLow({period})"),
            "trend": IndicatorSeries(trend_vals, name=f"GHTrend({period})"),
        }

    @staticmethod
    def is_uptrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close is above the Gann Hi-Lo Activator line (Uptrend).

        Formula:
            close[shift] > gha[shift]
        """
        logger.info(
            "Evaluating GannHiLo is_uptrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        c = BaseIndicator.to_numpy(close_prices)
        g = BaseIndicator.to_numpy(gha)

        idx = len(c) - 1 - shift
        if idx < 0 or idx >= len(c) or idx >= len(g) or np.isnan(g[idx]):
            return False

        return bool(c[idx] > g[idx])

    @staticmethod
    def is_downtrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close is below the Gann Hi-Lo Activator line (Downtrend).

        Formula:
            close[shift] < gha[shift]
        """
        logger.info(
            "Evaluating GannHiLo is_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        c = BaseIndicator.to_numpy(close_prices)
        g = BaseIndicator.to_numpy(gha)

        idx = len(c) - 1 - shift
        if idx < 0 or idx >= len(c) or idx >= len(g) or np.isnan(g[idx]):
            return False

        return bool(c[idx] < g[idx])

    @staticmethod
    def turns_uptrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close turned from below or equal to GHA into above GHA."""
        logger.info(
            "Evaluating GannHiLo turns_uptrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        c = BaseIndicator.to_numpy(close_prices)
        g = BaseIndicator.to_numpy(gha)

        curr_idx = len(c) - 1 - shift
        prev_idx = curr_idx - 1

        if prev_idx < 0 or curr_idx >= len(c) or curr_idx >= len(g):
            return False
        if np.isnan(g[curr_idx]) or np.isnan(g[prev_idx]):
            return False

        return bool(c[prev_idx] <= g[prev_idx] and c[curr_idx] > g[curr_idx])

    @staticmethod
    def turns_downtrend(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        gha: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close turned from above or equal to GHA into below GHA."""
        logger.info(
            "Evaluating GannHiLo turns_downtrend at shift=%d",
            shift,
            extra={"shift": shift},
        )
        c = BaseIndicator.to_numpy(close_prices)
        g = BaseIndicator.to_numpy(gha)

        curr_idx = len(c) - 1 - shift
        prev_idx = curr_idx - 1

        if prev_idx < 0 or curr_idx >= len(c) or curr_idx >= len(g):
            return False
        if np.isnan(g[curr_idx]) or np.isnan(g[prev_idx]):
            return False

        return bool(c[prev_idx] >= g[prev_idx] and c[curr_idx] < g[curr_idx])
