"""Heiken Ashi Indicator Block.

Description:
    Computes smoothed Heiken Ashi candlesticks (Open, High, Low, Close) to
    filter market noise and highlight visual trend persistence. Provides
    condition evaluators for bullish/bearish candle color and color turns.

Purpose:
    FEAT-SERVICES-INDICATOR-HEIKENASHI

Key Capabilities:
    - FR-SERVICES-HEIKENASHI-CALCULATE: Computes HA Open, High, Low, and Close.
    - FR-SERVICES-HEIKENASHI-CONDITIONS: Evaluates candle color and trend direction.

Python API Usage:
    ```python
    from app.services.indicators.heiken_ashi import HeikenAshi

    ha = HeikenAshi.calculate(open_p, high, low, close)
    ha_open = ha["open"]
    ha_close = ha["close"]

    # Condition checks
    is_bull = HeikenAshi.is_bullish(ha, shift=0)
    turns_bull = HeikenAshi.turns_bullish(ha, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class HeikenAshi(BaseIndicator):
    """Heiken Ashi smoothed candlestick generator with trend condition helpers."""

    @classmethod
    @override
    def calculate(
        cls,
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
    ) -> dict[str, IndicatorSeries]:
        """Compute Heiken Ashi Open, High, Low, and Close price series.

        Formula:
            ha_close[i] = (Open[i] + High[i] + Low[i] + Close[i]) / 4.0
            ha_open[i]  = (ha_open[i-1] + ha_close[i-1]) / 2.0 (ha_open[0] = Open[0])
            ha_high[i]  = max(High[i], ha_open[i], ha_close[i])
            ha_low[i]   = min(Low[i], ha_open[i], ha_close[i])

        Args:
            open_prices: Open price series.
            high: High price series.
            low: Low price series.
            close: Close price series.

        Returns:
            Dictionary containing 'open', 'high', 'low', and 'close' IndicatorSeries.
        """
        o_arr = cls._to_numpy(open_prices)
        h_arr = cls._to_numpy(high)
        l_arr = cls._to_numpy(low)
        c_arr = cls._to_numpy(close)

        n = len(c_arr)
        if n == 0:
            logger.info("FR-SERVICES-HEIKENASHI-CALCULATE: Empty series supplied")
            raise ValueError("Input series cannot be empty")
        if not (len(o_arr) == len(h_arr) == len(l_arr) == n):
            raise ValueError(
                f"Series length mismatch: open({len(o_arr)}), high({len(h_arr)}), "
                f"low({len(l_arr)}), close({n})"
            )

        ha_open = np.full(n, np.nan, dtype=np.float64)
        ha_high = np.full(n, np.nan, dtype=np.float64)
        ha_low = np.full(n, np.nan, dtype=np.float64)
        ha_close = np.full(n, np.nan, dtype=np.float64)

        # Bar 0 seed
        ha_close[0] = (o_arr[0] + h_arr[0] + l_arr[0] + c_arr[0]) / 4.0
        ha_open[0] = (o_arr[0] + c_arr[0]) / 2.0
        ha_high[0] = max(h_arr[0], ha_open[0], ha_close[0])
        ha_low[0] = min(l_arr[0], ha_open[0], ha_close[0])

        for i in range(1, n):
            c_val = (o_arr[i] + h_arr[i] + l_arr[i] + c_arr[i]) / 4.0
            o_val = (ha_open[i - 1] + ha_close[i - 1]) / 2.0
            h_val = max(h_arr[i], o_val, c_val)
            l_val = min(l_arr[i], o_val, c_val)

            ha_close[i] = c_val
            ha_open[i] = o_val
            ha_high[i] = h_val
            ha_low[i] = l_val

        logger.info(
            "FR-SERVICES-HEIKENASHI-CALCULATE: Computed HeikenAshi for %d bars",
            n,
        )
        return {
            "open": IndicatorSeries(ha_open, name="HAOpen"),
            "high": IndicatorSeries(ha_high, name="HAHigh"),
            "low": IndicatorSeries(ha_low, name="HALow"),
            "close": IndicatorSeries(ha_close, name="HAClose"),
        }

    @classmethod
    def is_bullish(
        cls,
        ha: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Check if Heiken Ashi candle is bullish (Close > Open)."""
        return ha["close"].is_greater(ha["open"], shift=shift)

    @classmethod
    def is_bearish(
        cls,
        ha: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Check if Heiken Ashi candle is bearish (Close < Open)."""
        return ha["close"].is_lower(ha["open"], shift=shift)

    @classmethod
    def turns_bullish(
        cls,
        ha: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Check if candle turned bullish on current bar from bearish on prior bar."""
        curr_bull = ha["close"].is_greater(ha["open"], shift=shift)
        prev_bear = ha["close"].is_lower(ha["open"], shift=shift + 1)
        return curr_bull and prev_bear

    @classmethod
    def turns_bearish(
        cls,
        ha: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Check if candle turned bearish on current bar from bullish on prior bar."""
        curr_bear = ha["close"].is_lower(ha["open"], shift=shift)
        prev_bull = ha["close"].is_greater(ha["open"], shift=shift + 1)
        return curr_bear and prev_bull
