"""Floor Trader Pivot Points Indicator Block.

Description:
    Computes classic Floor Trader Pivot Points including the primary Pivot Point
    (PP) and three tiers of Support (S1, S2, S3) and Resistance (R1, R2, R3)
    levels derived from previous period or prior session high, low, and close.

Purpose:
    FEAT-SERVICES-INDICATOR-PIVOTS

Key Capabilities:
    - FR-SERVICES-PIVOTS-CALCULATE: Computes PP, R1-R3, S1-S3 price levels.
    - FR-SERVICES-PIVOTS-CONDITIONS: Evaluates relationship and crossovers of pivots.

Python API Usage:
    ```python
    from app.services.indicators.price_action.pivots import Pivots

    pivots = Pivots.calculate(high, low, close, period=1)
    pp = pivots["pp"]
    r1 = pivots["r1"]
    s1 = pivots["s1"]

    # Condition checks
    is_above = Pivots.is_above_pp(close, pp, shift=0)
    cross_r1 = Pivots.crosses_above(close, r1, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    crosses_above,
    crosses_below,
    is_greater,
    is_lower,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class Pivots(BaseIndicator):
    """Floor Trader Pivot Points indicator calculating multi-tier levels."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        period: int = 1,
        timestamps: np.ndarray[Any, Any] | None = None,
    ) -> dict[str, IndicatorSeries]:
        """Compute Floor Trader Pivot Points and 3 support/resistance tiers.

        Formulas:
            PP = (PrevHigh + PrevLow + PrevClose) / 3
            R1 = (2 * PP) - PrevLow
            S1 = (2 * PP) - PrevHigh
            R2 = PP + (PrevHigh - PrevLow)
            S2 = PP - (PrevHigh - PrevLow)
            R3 = PP + 2 * (PrevHigh - PrevLow)
            S3 = PP - 2 * (PrevHigh - PrevLow)

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            period: Lookback window length in bars (default 1 bar ago).
            timestamps: Optional session timestamps for session-aware pivots.

        Returns:
            Dictionary containing 'pp', 'r1', 'r2', 'r3', 's1', 's2', 's3' series.

        Raises:
            ValueError: If period < 1 or array lengths mismatch.
        """
        logger.info(
            "Pivots calculation initiated with period=%d",
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
            raise ValueError("High, low, and close series must have identical lengths")

        if timestamps is not None and len(timestamps) == n:
            return cls._calculate_session_pivots(h_arr, l_arr, c_arr, timestamps)

        return cls._calculate_rolling_pivots(h_arr, l_arr, c_arr, period)

    @classmethod
    def _calculate_rolling_pivots(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        period: int,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling period-based pivots."""
        n = len(c_arr)
        arrays = {
            k: np.full(n, np.nan, dtype=np.float64)
            for k in ("pp", "r1", "r2", "r3", "s1", "s2", "s3")
        }

        for i in range(period, n):
            start_idx = i - period
            prev_high = np.max(h_arr[start_idx:i])
            prev_low = np.min(l_arr[start_idx:i])
            prev_close = c_arr[i - 1]

            p_val = (prev_high + prev_low + prev_close) / 3.0
            range_val = prev_high - prev_low

            arrays["pp"][i] = p_val
            arrays["r1"][i] = (2.0 * p_val) - prev_low
            arrays["s1"][i] = (2.0 * p_val) - prev_high
            arrays["r2"][i] = p_val + range_val
            arrays["s2"][i] = p_val - range_val
            arrays["r3"][i] = p_val + (2.0 * range_val)
            arrays["s3"][i] = p_val - (2.0 * range_val)

        logger.info(
            "Rolling Pivots complete: bars=%d, period=%d",
            n,
            period,
            extra={"bars": n, "period": period},
        )
        return cls._package_outputs(arrays)

    @classmethod
    def _calculate_session_pivots(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        timestamps: np.ndarray[Any, Any],
    ) -> dict[str, IndicatorSeries]:
        """Compute session-aware daily pivots."""
        n = len(c_arr)
        arrays = {
            k: np.full(n, np.nan, dtype=np.float64)
            for k in ("pp", "r1", "r2", "r3", "s1", "s2", "s3")
        }

        prev_day = None
        curr_session_high = -np.inf
        curr_session_low = np.inf
        curr_session_close = 0.0

        last_p = np.nan
        last_r1 = np.nan
        last_r2 = np.nan
        last_r3 = np.nan
        last_s1 = np.nan
        last_s2 = np.nan
        last_s3 = np.nan

        for i in range(n):
            day_str = str(timestamps[i])[:10]
            if prev_day is not None and day_str != prev_day:
                session_sum = curr_session_high + curr_session_low + curr_session_close
                p_val = session_sum / 3.0
                rng = curr_session_high - curr_session_low
                last_p = p_val
                last_r1 = (2.0 * p_val) - curr_session_low
                last_s1 = (2.0 * p_val) - curr_session_high
                last_r2 = p_val + rng
                last_s2 = p_val - rng
                last_r3 = p_val + (2.0 * rng)
                last_s3 = p_val - (2.0 * rng)

                curr_session_high = h_arr[i]
                curr_session_low = l_arr[i]
            else:
                curr_session_high = max(curr_session_high, h_arr[i])
                curr_session_low = min(curr_session_low, l_arr[i])

            curr_session_close = c_arr[i]
            prev_day = day_str

            arrays["pp"][i] = last_p
            arrays["r1"][i] = last_r1
            arrays["r2"][i] = last_r2
            arrays["r3"][i] = last_r3
            arrays["s1"][i] = last_s1
            arrays["s2"][i] = last_s2
            arrays["s3"][i] = last_s3

        logger.info(
            "Session Pivots complete: bars=%d",
            n,
            extra={"bars": n},
        )
        return cls._package_outputs(arrays)

    @staticmethod
    def _package_outputs(
        arrays: dict[str, np.ndarray[Any, Any]],
    ) -> dict[str, IndicatorSeries]:
        return {
            "pp": IndicatorSeries(arrays["pp"], name="PP"),
            "r1": IndicatorSeries(arrays["r1"], name="R1"),
            "r2": IndicatorSeries(arrays["r2"], name="R2"),
            "r3": IndicatorSeries(arrays["r3"], name="R3"),
            "s1": IndicatorSeries(arrays["s1"], name="S1"),
            "s2": IndicatorSeries(arrays["s2"], name="S2"),
            "s3": IndicatorSeries(arrays["s3"], name="S3"),
        }

    @staticmethod
    def is_above_pp(
        price: IndicatorSeries | np.ndarray[Any, Any],
        pp: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly above the central Pivot Point (PP)."""
        logger.info("Evaluating is_above_pp at shift=%d", shift, extra={"shift": shift})
        if len(price) - 1 - shift >= len(pp):
            return False
        return is_greater(price, pp, shift=shift)

    @staticmethod
    def is_below_pp(
        price: IndicatorSeries | np.ndarray[Any, Any],
        pp: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price is strictly below the central Pivot Point (PP)."""
        logger.info("Evaluating is_below_pp at shift=%d", shift, extra={"shift": shift})
        if len(price) - 1 - shift >= len(pp):
            return False
        return is_lower(price, pp, shift=shift)

    @staticmethod
    def crosses_above(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed above a pivot level."""
        logger.info(
            "Evaluating Pivots crosses_above at shift=%d",
            shift,
            extra={"shift": shift},
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return crosses_above(price, level, shift=shift)

    @staticmethod
    def crosses_below(
        price: IndicatorSeries | np.ndarray[Any, Any],
        level: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if price crossed below a pivot level."""
        logger.info(
            "Evaluating Pivots crosses_below at shift=%d",
            shift,
            extra={"shift": shift},
        )
        if len(price) - 1 - shift >= len(level):
            return False
        return crosses_below(price, level, shift=shift)
