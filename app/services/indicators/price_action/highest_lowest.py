"""Highest and Lowest Price Extrema Indicator Block.

Description:
    Computes rolling highest high and lowest low price bounds and their
    relative bar offset indices across a configurable lookback window.
    Provides condition evaluators for breakout opens, bar penetration,
    and COT emergency exit logic.

Purpose:
    FEAT-SERVICES-INDICATOR-HIGHESTLOWEST

Key Capabilities:
    - FR-SERVICES-HIGHESTLOWEST-CALCULATE: Computes highest, lowest, and peak indices.
    - FR-SERVICES-HIGHESTLOWEST-CONDITIONS: Evaluates open breakouts and COT exits.

Python API Usage:
    ```python
    from app.services.indicators.highest_lowest import HighestLowest

    hl = HighestLowest.calculate(high, low, period=14)
    highest = hl["highest"]
    lowest = hl["lowest"]
    highest_idx = hl["highest_index"]
    lowest_idx = hl["lowest_index"]

    # Condition checks
    opens_above = HighestLowest.bar_opens_above_highest(open_p, highest, shift=0)
    opens_below = HighestLowest.bar_opens_below_lowest(open_p, lowest, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class HighestLowest(BaseIndicator):
    """Highest and Lowest price extrema indicator with breakout condition evaluators."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        period: int = 14,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling highest high, lowest low, and relative peak/trough indices.

        Args:
            high: High prices or input value series.
            low: Optional low prices series. If None, high series is used for both.
            period: Lookback window length in bars (must be >= 1).

        Returns:
            Dictionary containing:
                - 'highest': Rolling maximum over lookback window.
                - 'lowest': Rolling minimum over lookback window.
                - 'highest_index': Shift offset (bars ago) of highest bar.
                - 'lowest_index': Shift offset (bars ago) of lowest bar.

        Raises:
            ValueError: If period < 1 or input arrays have mismatched or zero lengths.
        """
        logger.info(
            "HighestLowest calculation initiated with period=%d",
            period,
            extra={"period": period},
        )
        if period < 1:
            raise ValueError(f"Period must be >= 1, got {period}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low) if low is not None else h_arr

        if len(h_arr) == 0:
            raise ValueError("Input series cannot be empty")
        if len(h_arr) != len(l_arr):
            raise ValueError(
                f"High and low series length mismatch: {len(h_arr)} vs {len(l_arr)}"
            )

        n = len(h_arr)
        highest_vals = np.full(n, np.nan, dtype=np.float64)
        lowest_vals = np.full(n, np.nan, dtype=np.float64)
        highest_idx = np.full(n, np.nan, dtype=np.float64)
        lowest_idx = np.full(n, np.nan, dtype=np.float64)

        for i in range(n):
            start_idx = max(0, i - period + 1)
            h_win = h_arr[start_idx : i + 1]
            l_win = l_arr[start_idx : i + 1]

            max_val = np.max(h_win)
            min_val = np.min(l_win)

            highest_vals[i] = max_val
            lowest_vals[i] = min_val

            # Index is bars ago from current bar (0 = current bar, 1 = 1 bar ago)
            rel_max_idx = np.argmax(h_win)
            rel_min_idx = np.argmin(l_win)

            highest_idx[i] = float(len(h_win) - 1 - rel_max_idx)
            lowest_idx[i] = float(len(l_win) - 1 - rel_min_idx)

        logger.info(
            "HighestLowest calculation complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )

        return {
            "highest": IndicatorSeries(highest_vals, name=f"Highest({period})"),
            "lowest": IndicatorSeries(lowest_vals, name=f"Lowest({period})"),
            "highest_index": IndicatorSeries(
                highest_idx, name=f"HighestIndex({period})"
            ),
            "lowest_index": IndicatorSeries(lowest_idx, name=f"LowestIndex({period})"),
        }

    @staticmethod
    def bar_opens_above_highest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        highest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened above previous highest level after opening below.

        Formula:
            open[shift + 1] < highest[shift + 1] and open[shift] > highest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_above_highest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        o = BaseIndicator.to_numpy(open_prices)
        h = BaseIndicator.to_numpy(highest)

        curr_bar = len(o) - 1 - shift
        prev_bar = curr_bar - 1

        if prev_bar < 0 or curr_bar >= len(o) or prev_bar >= len(h):
            return False

        return bool(o[prev_bar] < h[prev_bar] and o[curr_bar] > h[prev_bar])

    @staticmethod
    def bar_opens_below_lowest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lowest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened below previous lowest level after opening above.

        Formula:
            open[shift + 1] > lowest[shift + 1] and open[shift] < lowest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_below_lowest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        o = BaseIndicator.to_numpy(open_prices)
        low_arr = BaseIndicator.to_numpy(lowest)

        curr_bar = len(o) - 1 - shift
        prev_bar = curr_bar - 1

        if prev_bar < 0 or curr_bar >= len(o) or prev_bar >= len(low_arr):
            return False

        return bool(o[prev_bar] > low_arr[prev_bar] and o[curr_bar] < low_arr[prev_bar])

    @staticmethod
    def bar_opens_below_highest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        highest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened below previous highest level after opening above.

        Formula:
            open[shift + 1] > highest[shift + 1] and open[shift] < highest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_below_highest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        o = BaseIndicator.to_numpy(open_prices)
        h = BaseIndicator.to_numpy(highest)

        curr_bar = len(o) - 1 - shift
        prev_bar = curr_bar - 1

        if prev_bar < 0 or curr_bar >= len(o) or prev_bar >= len(h):
            return False

        return bool(o[prev_bar] > h[prev_bar] and o[curr_bar] < h[prev_bar])

    @staticmethod
    def bar_opens_above_lowest(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        lowest: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if bar opened above previous lowest level after opening below.

        Formula:
            open[shift + 1] < lowest[shift + 1] and open[shift] > lowest[shift + 1]
        """
        logger.info(
            "Evaluating bar_opens_above_lowest at shift=%d",
            shift,
            extra={"shift": shift},
        )
        o = BaseIndicator.to_numpy(open_prices)
        low_arr = BaseIndicator.to_numpy(lowest)

        curr_bar = len(o) - 1 - shift
        prev_bar = curr_bar - 1

        if prev_bar < 0 or curr_bar >= len(o) or prev_bar >= len(low_arr):
            return False

        return bool(o[prev_bar] < low_arr[prev_bar] and o[curr_bar] > low_arr[prev_bar])

    @staticmethod
    def cot_emergency_exit_long(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        low_prices: IndicatorSeries | np.ndarray[Any, Any],
        lookback: int = 20,
        shift: int = 0,
    ) -> bool:
        """Check if current close dropped below lowest low of lookback window.

        Formula:
            close[shift] < min(low[shift+1 : shift+1+lookback])
        """
        logger.info(
            "Evaluating cot_emergency_exit_long at shift=%d, lookback=%d",
            shift,
            lookback,
            extra={"shift": shift, "lookback": lookback},
        )
        c = BaseIndicator.to_numpy(close_prices)
        l_arr = BaseIndicator.to_numpy(low_prices)

        curr_bar = len(c) - 1 - shift
        if curr_bar < 0 or curr_bar >= len(c):
            return False

        start_bar = max(0, curr_bar - lookback)
        end_bar = curr_bar
        if start_bar >= end_bar:
            return False

        month_low = np.min(l_arr[start_bar:end_bar])
        return bool(c[curr_bar] < month_low)

    @staticmethod
    def cot_emergency_exit_short(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        high_prices: IndicatorSeries | np.ndarray[Any, Any],
        lookback: int = 20,
        shift: int = 0,
    ) -> bool:
        """Check if current close exceeded highest high of lookback window.

        Formula:
            close[shift] > max(high[shift+1 : shift+1+lookback])
        """
        logger.info(
            "Evaluating cot_emergency_exit_short at shift=%d, lookback=%d",
            shift,
            lookback,
            extra={"shift": shift, "lookback": lookback},
        )
        c = BaseIndicator.to_numpy(close_prices)
        h_arr = BaseIndicator.to_numpy(high_prices)

        curr_bar = len(c) - 1 - shift
        if curr_bar < 0 or curr_bar >= len(c):
            return False

        start_bar = max(0, curr_bar - lookback)
        end_bar = curr_bar
        if start_bar >= end_bar:
            return False

        month_high = np.max(h_arr[start_bar:end_bar])
        return bool(c[curr_bar] > month_high)
