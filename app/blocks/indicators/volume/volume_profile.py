"""Volume Profile Indicator Block.

Description:
    Calculates Volume Profile price histograms over rolling windows or sessions,
    computing the Point of Control (POC), Value Area High (VAH), and Value Area
    Low (VAL) based on volume concentration. Provides condition evaluators for
    price relative to POC and Value Area containment.

Purpose:
    FEAT-BLOCKS-INDICATOR-VOLUMEPROFILE

Key Capabilities:
    - FR-BLOCKS-VOLUMEPROFILE-CALCULATE: Computes POC, VAH, and VAL from price/volume.
    - FR-BLOCKS-VOLUMEPROFILE-CONDITIONS: Evaluates POC position and Value Area
      containment.

Python API Usage:
    ```python
    from app.blocks.indicators.volume_profile import VolumeProfile

    # Calculate Volume Profile over a 50-bar rolling window with 50 rows
    profile = VolumeProfile.calculate(
        high,
        low,
        close,
        volume,
        period=50,
        profile_rows=50,
        value_area_pct=0.70,
    )
    poc = profile["poc"]
    vah = profile["vah"]
    val = profile["val"]

    # Condition checks
    inside_va = VolumeProfile.price_inside_va(close, vah, val, shift=0)
    above_poc = VolumeProfile.price_above_poc(close, poc, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

DEFAULT_PERIOD: int = 50
DEFAULT_PROFILE_ROWS: int = 50
DEFAULT_VALUE_AREA_PCT: float = 0.70


class VolumeProfile(BaseIndicator):
    """Volume Profile indicator extracting POC, VAH, and VAL levels."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        *,
        period: int = DEFAULT_PERIOD,
        profile_rows: int = DEFAULT_PROFILE_ROWS,
        value_area_pct: float = DEFAULT_VALUE_AREA_PCT,
    ) -> dict[str, IndicatorSeries]:
        """Calculate POC, VAH, and VAL over rolling lookback windows.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            volume: Trading volume series.
            period: Lookback window in bars (defaults to 50, min 2).
            profile_rows: Number of price bins (defaults to 50, min 5).
            value_area_pct: Proportion of total volume in Value Area (defaults to 0.70).

        Returns:
            Dictionary containing 'poc', 'vah', and 'val' IndicatorSeries.
        """
        h_arr = cls._to_numpy(high)
        l_arr = cls._to_numpy(low)
        c_arr = cls._to_numpy(close)
        v_arr = cls._to_numpy(volume)
        n = len(c_arr)

        poc_out = np.full(n, np.nan, dtype=np.float64)
        vah_out = np.full(n, np.nan, dtype=np.float64)
        val_out = np.full(n, np.nan, dtype=np.float64)

        if n < period:
            logger.info(
                "FR-BLOCKS-VOLUMEPROFILE-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return {
                "poc": IndicatorSeries(poc_out, name="POC"),
                "vah": IndicatorSeries(vah_out, name="VAH"),
                "val": IndicatorSeries(val_out, name="VAL"),
            }

        profile_rows = max(5, profile_rows)
        value_area_pct = min(0.99, max(0.10, value_area_pct))

        for i in range(period - 1, n):
            start = i - period + 1
            poc_val, vah_val, val_val = cls._compute_profile(
                h_slice=h_arr[start : i + 1],
                l_slice=l_arr[start : i + 1],
                v_slice=v_arr[start : i + 1],
                profile_rows=profile_rows,
                value_area_pct=value_area_pct,
            )
            poc_out[i] = poc_val
            vah_out[i] = vah_val
            val_out[i] = val_val

        logger.info(
            "FR-BLOCKS-VOLUMEPROFILE-CALCULATE: Computed VP(p=%d, rows=%d) for %d bars",
            period,
            profile_rows,
            n,
        )
        return {
            "poc": IndicatorSeries(poc_out, name="POC"),
            "vah": IndicatorSeries(vah_out, name="VAH"),
            "val": IndicatorSeries(val_out, name="VAL"),
        }

    @classmethod
    def _compute_profile(
        cls,
        *,
        h_slice: np.ndarray[Any, Any],
        l_slice: np.ndarray[Any, Any],
        v_slice: np.ndarray[Any, Any],
        profile_rows: int,
        value_area_pct: float,
    ) -> tuple[float, float, float]:
        """Compute POC, VAH, and VAL for a discrete price slice."""
        s_high = float(np.max(h_slice))
        s_low = float(np.min(l_slice))
        price_range = s_high - s_low

        if price_range <= 0.0:
            return s_high, s_high, s_low

        bin_size = price_range / profile_rows
        bins = np.zeros(profile_rows, dtype=np.float64)

        for h, lo, vol in zip(h_slice, l_slice, v_slice, strict=True):
            safe_vol = max(0.0, float(vol))
            bin_lo = int(
                np.clip(np.floor((lo - s_low) / bin_size), 0, profile_rows - 1)
            )
            bin_hi = int(np.clip(np.floor((h - s_low) / bin_size), 0, profile_rows - 1))
            count = bin_hi - bin_lo + 1
            vol_per_bin = safe_vol / count
            bins[bin_lo : bin_hi + 1] += vol_per_bin

        poc_idx = int(np.argmax(bins))
        poc = s_low + (poc_idx + 0.5) * bin_size

        vah, val = cls._expand_value_area(
            bins=bins,
            poc_idx=poc_idx,
            s_low=s_low,
            bin_size=bin_size,
            value_area_pct=value_area_pct,
            profile_rows=profile_rows,
        )
        return poc, vah, val

    @classmethod
    def _expand_value_area(
        cls,
        *,
        bins: np.ndarray[Any, Any],
        poc_idx: int,
        s_low: float,
        bin_size: float,
        value_area_pct: float,
        profile_rows: int,
    ) -> tuple[float, float]:
        """Expand outward from POC to identify Value Area High and Low boundaries."""
        total_volume = float(np.sum(bins))
        if total_volume <= 0.0:
            return s_low + (poc_idx + 1) * bin_size, s_low + poc_idx * bin_size

        target_vol = total_volume * value_area_pct
        current_vol = float(bins[poc_idx])
        lo_idx = poc_idx
        hi_idx = poc_idx

        while current_vol < target_vol and (lo_idx > 0 or hi_idx < profile_rows - 1):
            next_up = float(bins[hi_idx + 1]) if hi_idx < profile_rows - 1 else -1.0
            next_dn = float(bins[lo_idx - 1]) if lo_idx > 0 else -1.0

            if next_up >= next_dn:
                hi_idx += 1
                current_vol += next_up
            else:
                lo_idx -= 1
                current_vol += next_dn

        vah = s_low + (hi_idx + 1) * bin_size
        val = s_low + lo_idx * bin_size
        return vah, val

    @classmethod
    def price_above_poc(
        cls,
        close: IndicatorSeries,
        poc: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is above POC at specified shift."""
        return close.is_greater(poc, shift=shift)

    @classmethod
    def price_below_poc(
        cls,
        close: IndicatorSeries,
        poc: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is below POC at specified shift."""
        return close.is_lower(poc, shift=shift)

    @classmethod
    def price_inside_va(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is inside Value Area (val <= close <= vah)."""
        c = close.get(shift)
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return lower <= c <= upper

    @classmethod
    def price_outside_va(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is outside Value Area (close > vah or close < val)."""
        c = close.get(shift)
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return c > upper or c < lower

    @classmethod
    def poc_is_rising(cls, poc: IndicatorSeries, shift: int = 0) -> bool:
        """Check if POC is rising at shift compared to shift+1."""
        return poc.is_rising(shift=shift)

    @classmethod
    def poc_is_falling(cls, poc: IndicatorSeries, shift: int = 0) -> bool:
        """Check if POC is falling at shift compared to shift+1."""
        return poc.is_falling(shift=shift)

    @classmethod
    def is_narrow_value_area(
        cls,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """Check if Value Area width (vah - val) is strictly below a threshold."""
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(upper) or np.isnan(lower):
            return False
        return (upper - lower) < threshold

    @classmethod
    def is_wide_value_area(
        cls,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """Check if Value Area width (vah - val) is strictly above a threshold."""
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(upper) or np.isnan(lower):
            return False
        return (upper - lower) > threshold
