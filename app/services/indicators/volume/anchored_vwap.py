"""Anchored Volume Weighted Average Price (AnchoredVWAP) Indicator Block.

Description:
    Computes session-anchored Volume Weighted Average Price with volume-weighted
    standard deviation bands. Supports Daily (1), Weekly (2), and Monthly (3)
    calendar session resets, bar-interval resets, or explicit anchor indices.
    Provides condition helpers for band touches, crossovers, and trend slopes.

Purpose:
    FEAT-SERVICES-INDICATOR-AVWAP

Key Capabilities:
    - FR-SERVICES-AVWAP-CALCULATE: Calculates anchored VWAP with upper and lower bands.
    - FR-SERVICES-AVWAP-CONDITIONS: Evaluates close crosses, band boundaries, and slope.

Python API Usage:
    ```python
    from app.services.indicators.volume.anchored_vwap import AnchoredVWAP

    # Calculate Daily anchored VWAP with 1.5 standard deviation bands
    bands = AnchoredVWAP.calculate(
        high,
        low,
        close,
        volume,
        session_type=1,
        std_dev_mult=1.5,
    )
    vwap = bands["vwap"]
    upper = bands["upper"]
    lower = bands["lower"]

    # Condition checks
    above_upper = AnchoredVWAP.bar_closes_above_upper(close, upper, shift=0)
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
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

SESSION_DAILY: int = 1
SESSION_WEEKLY: int = 2
SESSION_MONTHLY: int = 3
DEFAULT_STD_DEV_MULT: float = 1.0
MS_TIMESTAMP_THRESHOLD: float = 1e11


class AnchoredVWAP(BaseIndicator):
    """Anchored VWAP indicator with volume-weighted standard deviation bands."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        *,
        timestamps: np.ndarray[Any, Any] | list[Any] | None = None,
        session_type: int = SESSION_DAILY,
        std_dev_mult: float = DEFAULT_STD_DEV_MULT,
        anchor_period: int = 0,
        anchor_indices: list[int] | set[int] | None = None,
    ) -> dict[str, IndicatorSeries]:
        """Compute session-anchored VWAP, Upper band, and Lower band series.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            volume: Trading volume series.
            timestamps: Optional timestamp array (seconds, milliseconds, or datetime).
            session_type: 1 = Daily, 2 = Weekly, 3 = Monthly.
            std_dev_mult: Standard deviation band multiplier (defaults to 1.0).
            anchor_period: Optional periodic anchor bar interval if timestamps omitted.
            anchor_indices: Optional explicit bar indices where anchor resets.

        Returns:
            Dictionary containing 'vwap', 'upper', and 'lower' IndicatorSeries.
        """
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)

        vwap_out = np.full(n, np.nan, dtype=np.float64)
        upper_out = np.full(n, np.nan, dtype=np.float64)
        lower_out = np.full(n, np.nan, dtype=np.float64)

        if n == 0:
            logger.info("FR-SERVICES-AVWAP-CALCULATE: Empty series supplied")
            return {
                "vwap": IndicatorSeries(vwap_out, name="AVWAP"),
                "upper": IndicatorSeries(upper_out, name="AVWAP_Upper"),
                "lower": IndicatorSeries(lower_out, name="AVWAP_Lower"),
            }

        typical_price = (h_arr + l_arr + c_arr) / 3.0
        # Replace zero or negative volumes with 1.0 as done in SQX donor
        safe_volume = np.where(v_arr <= 0.0, 1.0, v_arr)

        # Detect session reset boundaries
        is_reset = cls._detect_resets(
            n=n,
            timestamps=timestamps,
            session_type=session_type,
            anchor_period=anchor_period,
            anchor_indices=anchor_indices,
        )

        cum_pv = 0.0
        cum_vol = 0.0
        cum_pv2 = 0.0

        for i in range(n):
            p = typical_price[i]
            v = safe_volume[i]

            if is_reset[i] or i == 0:
                cum_pv = p * v
                cum_vol = v
                cum_pv2 = (p * p) * v
            else:
                cum_pv += p * v
                cum_vol += v
                cum_pv2 += (p * p) * v

            vwap_val = cum_pv / cum_vol if cum_vol > 0.0 else p
            variance = (
                (cum_pv2 / cum_vol) - (vwap_val * vwap_val) if cum_vol > 0.0 else 0.0
            )
            variance = max(0.0, variance)
            std_dev = np.sqrt(variance)

            vwap_out[i] = vwap_val
            upper_out[i] = vwap_val + std_dev_mult * std_dev
            lower_out[i] = vwap_val - std_dev_mult * std_dev

        logger.info(
            "FR-SERVICES-AVWAP-CALCULATE: Computed AVWAP(session=%d, mult=%.2f) "
            "for %d bars",
            session_type,
            std_dev_mult,
            n,
        )
        return {
            "vwap": IndicatorSeries(vwap_out, name="AVWAP"),
            "upper": IndicatorSeries(upper_out, name="AVWAP_Upper"),
            "lower": IndicatorSeries(lower_out, name="AVWAP_Lower"),
        }

    @classmethod
    def _detect_timestamp_resets(
        cls,
        *,
        ts_arr: np.ndarray[Any, Any],
        session_type: int,
        n: int,
    ) -> np.ndarray[Any, np.dtype[np.bool_]]:
        """Detect session boundary resets from timestamp array."""
        is_reset = np.zeros(n, dtype=bool)
        try:
            if np.issubdtype(ts_arr.dtype, np.number):
                scale = 1000 if ts_arr[0] > MS_TIMESTAMP_THRESHOLD else 1
                dt_series = (ts_arr / scale).astype("datetime64[s]")
            else:
                dt_series = ts_arr.astype("datetime64[s]")

            if session_type == SESSION_DAILY:
                days = dt_series.astype("datetime64[D]")
                is_reset[1:] = days[1:] != days[:-1]
            elif session_type == SESSION_WEEKLY:
                weeks = dt_series.astype("datetime64[W]")
                is_reset[1:] = weeks[1:] != weeks[:-1]
            elif session_type == SESSION_MONTHLY:
                months = dt_series.astype("datetime64[M]")
                is_reset[1:] = months[1:] != months[:-1]
        except (ValueError, TypeError, KeyError) as err:
            logger.warning(
                "FR-SERVICES-AVWAP-CALCULATE: Timestamp parsing failed (%s)",
                err,
            )
        return is_reset

    @classmethod
    def _detect_resets(
        cls,
        *,
        n: int,
        timestamps: np.ndarray[Any, Any] | list[Any] | None,
        session_type: int,
        anchor_period: int,
        anchor_indices: list[int] | set[int] | None,
    ) -> np.ndarray[Any, np.dtype[np.bool_]]:
        """Determine boolean array indicating bar indices where session resets."""
        is_reset = np.zeros(n, dtype=bool)
        is_reset[0] = True

        if anchor_indices is not None:
            for idx in anchor_indices:
                if 0 <= idx < n:
                    is_reset[idx] = True
            return is_reset

        if timestamps is not None and len(timestamps) == n:
            ts_res = cls._detect_timestamp_resets(
                ts_arr=np.asarray(timestamps),
                session_type=session_type,
                n=n,
            )
            is_reset[1:] = ts_res[1:]
            return is_reset

        if anchor_period > 0:
            for i in range(anchor_period, n, anchor_period):
                is_reset[i] = True

        return is_reset

    @classmethod
    def is_rising(cls, vwap: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VWAP is rising at shift compared to shift+1."""
        return is_rising(vwap, shift=shift)

    @classmethod
    def is_falling(cls, vwap: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VWAP is falling at shift compared to shift+1."""
        return is_falling(vwap, shift=shift)

    @classmethod
    def bar_closes_above_vwap(
        cls,
        close: IndicatorSeries,
        vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close is above VWAP at specified shift."""
        return is_greater(close, vwap, shift=shift)

    @classmethod
    def bar_closes_below_vwap(
        cls,
        close: IndicatorSeries,
        vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close is below VWAP at specified shift."""
        return is_lower(close, vwap, shift=shift)

    @classmethod
    def bar_closes_above_upper(
        cls,
        close: IndicatorSeries,
        upper: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close is above upper band at specified shift."""
        return is_greater(close, upper, shift=shift)

    @classmethod
    def bar_closes_below_lower(
        cls,
        close: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close is below lower band at specified shift."""
        return is_lower(close, lower, shift=shift)

    @classmethod
    def bar_crosses_above_lower(
        cls,
        close: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close crosses above lower band."""
        return crosses_above(close, lower, shift=shift)

    @classmethod
    def bar_crosses_above_upper(
        cls,
        close: IndicatorSeries,
        upper: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close crosses above upper band."""
        return crosses_above(close, upper, shift=shift)

    @classmethod
    def bar_crosses_below_lower(
        cls,
        close: IndicatorSeries,
        lower: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close crosses below lower band."""
        return crosses_below(close, lower, shift=shift)

    @classmethod
    def bar_crosses_below_upper(
        cls,
        close: IndicatorSeries,
        upper: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close crosses below upper band."""
        return crosses_below(close, upper, shift=shift)

    @classmethod
    def fast_above_slow(
        cls,
        fast_vwap: IndicatorSeries,
        slow_vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if fast Anchored VWAP is above slow Anchored VWAP."""
        return is_greater(fast_vwap, slow_vwap, shift=shift)

    @classmethod
    def fast_below_slow(
        cls,
        fast_vwap: IndicatorSeries,
        slow_vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if fast Anchored VWAP is below slow Anchored VWAP."""
        return is_lower(fast_vwap, slow_vwap, shift=shift)
