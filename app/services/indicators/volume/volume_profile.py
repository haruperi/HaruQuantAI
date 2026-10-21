"""Volume Profile Indicator Block.

Description:
    Calculates Volume Profile price histograms over rolling windows, custom
    hours, or multi-session boundaries, computing the Point of Control (POC),
    Value Area High (VAH), Value Area Low (VAL), Bull/Bear POC, Volume Delta,
    POC relative position percentages, and Initial Balance (IBH/IBL). Provides
    condition evaluators for all 36 Volume Profile signal blocks.

Purpose:
    FEAT-SERVICES-INDICATOR-VOLUMEPROFILE: Volume Profile calculation and conditions.

Key Capabilities:
    - FR-SERVICES-VOLUMEPROFILE-CALCULATE: Computes POC, VAH, VAL, BullPOC, BearPOC,
      Delta, POCPctUp, POCPctDown, IBH, and IBL over rolling or custom-hour sessions.
    - FR-SERVICES-VOLUMEPROFILE-CONDITIONS: Evaluates all POC, Value Area, Initial
      Balance, Delta, Excess Reversal, and Value Shift conditions.

Python API Usage:
    ```python
    from app.services.indicators.volume.volume_profile import VolumeProfile

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

    inside_va = VolumeProfile.price_inside_va(close, vah, val, shift=0)
    above_poc = VolumeProfile.price_above_poc(close, poc, shift=0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "vp"
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

DEFAULT_PERIOD: int = 50
DEFAULT_PROFILE_ROWS: int = 50
DEFAULT_VALUE_AREA_PCT: float = 0.70
_SEC_TO_MS_CUTOFF: float = 1e11


class VolumeProfile(BaseIndicator):
    """Volume Profile indicator extracting POC, VAH, VAL, Delta, IB, and conditions."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        low: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        close: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        volume: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        *,
        open_prices: IndicatorSeries
        | Sequence[float]
        | np.ndarray[Any, Any]
        | None = None,
        period: int = DEFAULT_PERIOD,
        profile_rows: int = DEFAULT_PROFILE_ROWS,
        value_area_pct: float = DEFAULT_VALUE_AREA_PCT,
        ib_bars: int = 4,
    ) -> dict[str, IndicatorSeries]:
        """Calculate POC, VAH, VAL, Bull/Bear POC, Delta, POC%, and IBH/IBL."""
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)

        if open_prices is not None:
            o_arr = cls.to_numpy(open_prices)
        else:
            o_arr = np.empty(n, dtype=np.float64)
            if n > 0:
                o_arr[0] = c_arr[0]
                if n > 1:
                    o_arr[1:] = c_arr[:-1]

        keys = (
            "poc",
            "vah",
            "val",
            "bull_poc",
            "bear_poc",
            "delta",
            "poc_pct_up",
            "poc_pct_down",
            "ibh",
            "ibl",
        )
        arrays = {k: np.full(n, np.nan, dtype=np.float64) for k in keys}

        if n < period:
            logger.info(
                "FR-SERVICES-VOLUMEPROFILE-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return {k: IndicatorSeries(arrays[k], name=k.upper()) for k in keys}

        profile_rows = max(5, profile_rows)
        value_area_pct = min(0.99, max(0.10, value_area_pct))
        ib_len = max(1, min(ib_bars, period))

        for i in range(period - 1, n):
            start = i - period + 1
            h_sl = h_arr[start : i + 1]
            l_sl = l_arr[start : i + 1]
            o_sl = o_arr[start : i + 1]
            c_sl = c_arr[start : i + 1]
            v_sl = v_arr[start : i + 1]

            poc_val, vah_val, val_val, bull_poc, bear_poc, delta_val = (
                cls._compute_profile_extended(
                    h_slice=h_sl,
                    l_slice=l_sl,
                    o_slice=o_sl,
                    c_slice=c_sl,
                    v_slice=v_sl,
                    profile_rows=profile_rows,
                    value_area_pct=value_area_pct,
                )
            )
            s_high = float(np.max(h_sl))
            s_low = float(np.min(l_sl))
            rng = s_high - s_low
            pct_down = ((poc_val - s_low) / rng * 100.0) if rng > 0.0 else 50.0
            pct_up = ((s_high - poc_val) / rng * 100.0) if rng > 0.0 else 50.0

            arrays["poc"][i] = poc_val
            arrays["vah"][i] = vah_val
            arrays["val"][i] = val_val
            arrays["bull_poc"][i] = bull_poc
            arrays["bear_poc"][i] = bear_poc
            arrays["delta"][i] = delta_val
            arrays["poc_pct_up"][i] = pct_up
            arrays["poc_pct_down"][i] = pct_down
            arrays["ibh"][i] = float(np.max(h_sl[:ib_len]))
            arrays["ibl"][i] = float(np.min(l_sl[:ib_len]))

        logger.info(
            "FR-SERVICES-VOLUMEPROFILE-CALCULATE: VP(p=%d, rows=%d) for %d bars",
            period,
            profile_rows,
            n,
        )
        return {k: IndicatorSeries(arrays[k], name=k.upper()) for k in keys}

    @classmethod
    def calculate_custom_hours(
        cls,
        timestamps: Sequence[int | float] | np.ndarray[Any, Any],
        high: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        low: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        close: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        volume: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        *,
        start_hhmm: int = 800,
        end_hhmm: int = 1700,
        period: int = DEFAULT_PERIOD,
        profile_rows: int = DEFAULT_PROFILE_ROWS,
        value_area_pct: float = DEFAULT_VALUE_AREA_PCT,
    ) -> dict[str, IndicatorSeries]:
        """Compute VolumeProfileCustomHours within `start_hhmm`..`end_hhmm`."""
        ts = np.asarray(timestamps, dtype=np.float64)
        if len(ts) > 0 and float(np.max(np.abs(ts))) < _SEC_TO_MS_CUTOFF:
            ts = ts * 1000.0
        v_arr = cls.to_numpy(volume).copy()
        day_ms = 24 * 60 * 60 * 1000
        start_ms = (start_hhmm // 100) * 3600000 + (start_hhmm % 100) * 60000
        end_ms = (end_hhmm // 100) * 3600000 + (end_hhmm % 100) * 60000

        for i in range(min(len(ts), len(v_arr))):
            tod = int(ts[i]) % day_ms
            in_win = (
                (start_ms <= tod <= end_ms)
                if start_ms <= end_ms
                else (tod >= start_ms or tod <= end_ms)
            )
            if not in_win:
                v_arr[i] = 0.0

        return cls.calculate(
            high,
            low,
            close,
            v_arr,
            period=period,
            profile_rows=profile_rows,
            value_area_pct=value_area_pct,
        )

    @classmethod
    def calculate_custom_hours_multi_session(
        cls,
        timestamps: Sequence[int | float] | np.ndarray[Any, Any],
        high: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        low: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        close: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        volume: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
        *,
        sessions: Sequence[tuple[int, int]] = ((800, 1200), (1300, 1700)),
        period: int = DEFAULT_PERIOD,
        profile_rows: int = DEFAULT_PROFILE_ROWS,
        value_area_pct: float = DEFAULT_VALUE_AREA_PCT,
    ) -> dict[str, IndicatorSeries]:
        """Compute VolumeProfileCustomHoursMultiSession across session windows."""
        ts = np.asarray(timestamps, dtype=np.float64)
        if len(ts) > 0 and float(np.max(np.abs(ts))) < _SEC_TO_MS_CUTOFF:
            ts = ts * 1000.0
        v_arr = cls.to_numpy(volume).copy()
        day_ms = 24 * 60 * 60 * 1000
        win_bounds = [
            (
                (s // 100) * 3600000 + (s % 100) * 60000,
                (e // 100) * 3600000 + (e % 100) * 60000,
            )
            for s, e in sessions
        ]

        for i in range(min(len(ts), len(v_arr))):
            tod = int(ts[i]) % day_ms
            matched = any(
                (sm <= tod <= em) if sm <= em else (tod >= sm or tod <= em)
                for sm, em in win_bounds
            )
            if not matched:
                v_arr[i] = 0.0

        return cls.calculate(
            high,
            low,
            close,
            v_arr,
            period=period,
            profile_rows=profile_rows,
            value_area_pct=value_area_pct,
        )

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
        zeros = np.zeros_like(h_slice)
        poc, vah, val, _, _, _ = cls._compute_profile_extended(
            h_slice=h_slice,
            l_slice=l_slice,
            o_slice=zeros,
            c_slice=zeros,
            v_slice=v_slice,
            profile_rows=profile_rows,
            value_area_pct=value_area_pct,
        )
        return poc, vah, val

    @classmethod
    def _compute_profile_extended(
        cls,
        *,
        h_slice: np.ndarray[Any, Any],
        l_slice: np.ndarray[Any, Any],
        o_slice: np.ndarray[Any, Any],
        c_slice: np.ndarray[Any, Any],
        v_slice: np.ndarray[Any, Any],
        profile_rows: int,
        value_area_pct: float,
    ) -> tuple[float, float, float, float, float, float]:
        """Compute POC, VAH, VAL, BullPOC, BearPOC, and Delta."""
        s_high = float(np.max(h_slice))
        s_low = float(np.min(l_slice))
        price_range = s_high - s_low

        if price_range <= 0.0:
            return s_high, s_high, s_low, s_high, s_low, 0.0

        bin_size = price_range / profile_rows
        bins = np.zeros(profile_rows, dtype=np.float64)
        bull_bins = np.zeros(profile_rows, dtype=np.float64)
        bear_bins = np.zeros(profile_rows, dtype=np.float64)
        delta_sum = 0.0

        for h, lo, op, cl, vol in zip(
            h_slice, l_slice, o_slice, c_slice, v_slice, strict=True
        ):
            safe_vol = max(0.0, float(vol))
            bin_lo = int(
                np.clip(np.floor((lo - s_low) / bin_size), 0, profile_rows - 1)
            )
            bin_hi = int(np.clip(np.floor((h - s_low) / bin_size), 0, profile_rows - 1))
            count = bin_hi - bin_lo + 1
            vol_per_bin = safe_vol / count
            bins[bin_lo : bin_hi + 1] += vol_per_bin
            if cl >= op:
                bull_bins[bin_lo : bin_hi + 1] += vol_per_bin
                delta_sum += safe_vol
            else:
                bear_bins[bin_lo : bin_hi + 1] += vol_per_bin
                delta_sum -= safe_vol

        poc_idx = int(np.argmax(bins))
        poc = s_low + (poc_idx + 0.5) * bin_size
        bull_idx = int(np.argmax(bull_bins)) if np.max(bull_bins) > 0.0 else poc_idx
        bear_idx = int(np.argmax(bear_bins)) if np.max(bear_bins) > 0.0 else poc_idx
        bull_poc = s_low + (bull_idx + 0.5) * bin_size
        bear_poc = s_low + (bear_idx + 0.5) * bin_size

        vah, val = cls._expand_value_area(
            bins=bins,
            poc_idx=poc_idx,
            s_low=s_low,
            bin_size=bin_size,
            value_area_pct=value_area_pct,
            profile_rows=profile_rows,
        )
        return poc, vah, val, bull_poc, bear_poc, delta_sum

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

    @staticmethod
    def _as_series(
        s: IndicatorSeries | Sequence[float] | np.ndarray[Any, Any],
    ) -> IndicatorSeries:
        return s if isinstance(s, IndicatorSeries) else IndicatorSeries(s)

    # Core & Extended VolumeProfile condition evaluators (all 36 VP* blocks)
    @classmethod
    def price_above_poc(
        cls, close: IndicatorSeries, poc: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPPriceAbovePOC (`close[shift] > poc[shift]`)."""
        return close.is_greater(poc, shift=shift)

    @classmethod
    def price_below_poc(
        cls, close: IndicatorSeries, poc: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPPriceBelowPOC (`close[shift] < poc[shift]`)."""
        return close.is_lower(poc, shift=shift)

    @classmethod
    def price_inside_va(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPriceInsideVA (`val[shift] <= close[shift] <= vah[shift]`)."""
        c, upper, lower = close.get(shift), vah.get(shift), val.get(shift)
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
        """Evaluate VPPriceOutsideVA (`close[s] > vah[s] or close[s] < val[s]`)."""
        c, upper, lower = close.get(shift), vah.get(shift), val.get(shift)
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
    def vah_is_rising(cls, vah: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VAH is rising at shift compared to shift+1."""
        return vah.is_rising(shift=shift)

    @classmethod
    def vah_is_falling(cls, vah: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VAH is falling at shift compared to shift+1."""
        return vah.is_falling(shift=shift)

    @classmethod
    def val_is_rising(cls, val: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VAL is rising at shift compared to shift+1."""
        return val.is_rising(shift=shift)

    @classmethod
    def val_is_falling(cls, val: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VAL is falling at shift compared to shift+1."""
        return val.is_falling(shift=shift)

    @classmethod
    def is_narrow_value_area(
        cls,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPNarrowValueArea (`0 < (vah - val) < threshold`)."""
        upper, lower = vah.get(shift), val.get(shift)
        if np.isnan(upper) or np.isnan(lower):
            return False
        width = upper - lower
        return 0.0 < width < threshold

    @classmethod
    def is_wide_value_area(
        cls,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPWideValueArea (`(vah - val) > threshold`)."""
        upper, lower = vah.get(shift), val.get(shift)
        if np.isnan(upper) or np.isnan(lower):
            return False
        return (upper - lower) > threshold

    @classmethod
    def bull_above_bear(
        cls, bull_poc: IndicatorSeries, bear_poc: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPBullAboveBear (`bull_poc[shift] > bear_poc[shift]`)."""
        return bull_poc.is_greater(bear_poc, shift=shift)

    @classmethod
    def bear_above_bull(
        cls, bull_poc: IndicatorSeries, bear_poc: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPBearAboveBull (`bear_poc[shift] > bull_poc[shift]`)."""
        return bear_poc.is_greater(bull_poc, shift=shift)

    @classmethod
    def bottom_heavy_poc(
        cls,
        poc_pct_down: IndicatorSeries,
        threshold_pct: float = 35.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPBottomHeavyPOC (`0 < poc_pct_down[shift] < threshold_pct`)."""
        v = poc_pct_down.get(shift)
        return not np.isnan(v) and 0.0 < v < threshold_pct

    @classmethod
    def top_heavy_poc(
        cls,
        poc_pct_up: IndicatorSeries,
        threshold_pct: float = 35.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPTopHeavyPOC (`0 < poc_pct_up[shift] < threshold_pct`)."""
        v = poc_pct_up.get(shift)
        return not np.isnan(v) and 0.0 < v < threshold_pct

    @classmethod
    def high_delta(
        cls, delta: IndicatorSeries, min_delta: float = 100.0, shift: int = 0
    ) -> bool:
        """Evaluate VPHighDelta (`delta[shift] > min_delta`)."""
        return delta.is_greater(min_delta, shift=shift)

    @classmethod
    def high_neg_delta(
        cls, delta: IndicatorSeries, min_delta: float = 100.0, shift: int = 0
    ) -> bool:
        """Evaluate VPHighNegDelta (`delta[shift] < -min_delta`)."""
        return delta.is_lower(-min_delta, shift=shift)

    @classmethod
    def ib_breakout_up(
        cls, close: IndicatorSeries, ibh: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPIBBreakoutUp (`ibh[shift] > 0 and close[shift] > ibh[shift]`)."""
        c, h = close.get(shift), ibh.get(shift)
        return not (np.isnan(c) or np.isnan(h)) and (h > 0.0 and c > h)

    @classmethod
    def ib_breakout_down(
        cls, close: IndicatorSeries, ibl: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPIBBreakoutDown (`ibl[s] > 0 and close[s] < ibl[s]`)."""
        c, lo = close.get(shift), ibl.get(shift)
        return not (np.isnan(c) or np.isnan(lo)) and (lo > 0.0 and c < lo)

    @classmethod
    def ib_rejection_long(  # noqa: PLR0917
        cls,
        low: IndicatorSeries,
        close: IndicatorSeries,
        ibl: IndicatorSeries,
        tolerance: float = 0.0,
        min_rejection: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPIBRejectionLong (`low < ibl - tol and close > ibl + rej`)."""
        lo, c, b = low.get(shift), close.get(shift), ibl.get(shift)
        if any(np.isnan(x) for x in (lo, c, b)):
            return False
        return b > 0.0 and lo < (b - tolerance) and c > (b + min_rejection)

    @classmethod
    def ib_rejection_short(  # noqa: PLR0917
        cls,
        high: IndicatorSeries,
        close: IndicatorSeries,
        ibh: IndicatorSeries,
        tolerance: float = 0.0,
        min_rejection: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPIBRejectionShort (`high > ibh + tol and close < ibh - rej`)."""
        hi, c, b = high.get(shift), close.get(shift), ibh.get(shift)
        if any(np.isnan(x) for x in (hi, c, b)):
            return False
        return b > 0.0 and hi > (b + tolerance) and c < (b - min_rejection)

    @classmethod
    def excess_reversal_long(  # noqa: PLR0917
        cls,
        open_prices: IndicatorSeries,
        high: IndicatorSeries,
        low: IndicatorSeries,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_wick: float = 0.0,
        wick_ratio: float = 1.5,
        tick_size: float = 0.0001,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPExcessReversalLong."""
        o, hi, lo, c = (
            open_prices.get(shift),
            high.get(shift),
            low.get(shift),
            close.get(shift),
        )
        u, d = vah.get(shift), val.get(shift)
        if any(np.isnan(x) for x in (o, hi, lo, c, u, d)):
            return False
        if lo >= (d - min_wick) or c < d or c > u:
            return False
        body = abs(c - o)
        lower_wick = min(o, c) - lo
        return lower_wick > wick_ratio * max(body, tick_size)

    @classmethod
    def excess_reversal_short(  # noqa: PLR0917
        cls,
        open_prices: IndicatorSeries,
        high: IndicatorSeries,
        low: IndicatorSeries,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_wick: float = 0.0,
        wick_ratio: float = 1.5,
        tick_size: float = 0.0001,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPExcessReversalShort."""
        o, hi, lo, c = (
            open_prices.get(shift),
            high.get(shift),
            low.get(shift),
            close.get(shift),
        )
        u, d = vah.get(shift), val.get(shift)
        if any(np.isnan(x) for x in (o, hi, lo, c, u, d)):
            return False
        if hi <= (u + min_wick) or c > u or c < d:
            return False
        body = abs(c - o)
        upper_wick = hi - max(o, c)
        return upper_wick > wick_ratio * max(body, tick_size)

    @classmethod
    def rising_poc(
        cls,
        poc: IndicatorSeries,
        lookback_bars: int = 1,
        min_shift: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPRisingPOC (`poc[s] > average_offset`)."""
        lb = max(1, lookback_bars)
        p0, pp = poc.get(shift), poc.get(shift + lb)
        return not (np.isnan(p0) or np.isnan(pp)) and (p0 > (pp + min_shift))

    @classmethod
    def falling_poc(
        cls,
        poc: IndicatorSeries,
        lookback_bars: int = 1,
        min_shift: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPFallingPOC (`poc[s] < average_offset`)."""
        lb = max(1, lookback_bars)
        p0, pp = poc.get(shift), poc.get(shift + lb)
        return not (np.isnan(p0) or np.isnan(pp)) and (p0 < (pp - min_shift))

    @classmethod
    def late_acceptance_failure_long(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPLateAcceptanceFailureLong (3 bars below VAL then inside VA)."""
        if not cls.price_inside_va(close, vah, val, shift=shift):
            return False
        for k in (1, 2, 3):
            ck, vk = close.get(shift + k), val.get(shift + k)
            if np.isnan(ck) or np.isnan(vk) or ck >= (vk - min_deviation):
                return False
        return True

    @classmethod
    def late_acceptance_failure_short(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPLateAcceptanceFailureShort (3 bars above VAH then inside VA)."""
        if not cls.price_inside_va(close, vah, val, shift=shift):
            return False
        for k in (1, 2, 3):
            ck, vk = close.get(shift + k), vah.get(shift + k)
            if np.isnan(ck) or np.isnan(vk) or ck <= (vk + min_deviation):
                return False
        return True

    @classmethod
    def open_drive_long(
        cls,
        open_prices: IndicatorSeries,
        close: IndicatorSeries,
        min_move: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPOpenDriveLong (3 bullish bars with net move >= `min_move`)."""
        for k in (0, 1, 2):
            ok, ck = open_prices.get(shift + k), close.get(shift + k)
            if np.isnan(ok) or np.isnan(ck) or ck <= ok:
                return False
        return (close.get(shift) - open_prices.get(shift + 2)) >= min_move

    @classmethod
    def open_drive_short(
        cls,
        open_prices: IndicatorSeries,
        close: IndicatorSeries,
        min_move: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPOpenDriveShort (3 bearish bars with net move >= `min_move`)."""
        for k in (0, 1, 2):
            ok, ck = open_prices.get(shift + k), close.get(shift + k)
            if np.isnan(ok) or np.isnan(ck) or ck >= ok:
                return False
        return (open_prices.get(shift + 2) - close.get(shift)) >= min_move

    @classmethod
    def poc_at_edge_long(
        cls,
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        edge_pct: float = 20.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCAtEdgeLong (`poc >= vah - (vah - val) * edge_pct / 100`)."""
        p, u, d = poc.get(shift), vah.get(shift), val.get(shift)
        if any(np.isnan(x) for x in (p, u, d)) or (u - d) <= 0.0:
            return False
        return p >= u - (u - d) * (edge_pct / 100.0)

    @classmethod
    def poc_at_edge_short(
        cls,
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        edge_pct: float = 20.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCAtEdgeShort (`poc <= val + (vah - val) * edge_pct / 100`)."""
        p, u, d = poc.get(shift), vah.get(shift), val.get(shift)
        if any(np.isnan(x) for x in (p, u, d)) or (u - d) <= 0.0:
            return False
        return p <= d + (u - d) * (edge_pct / 100.0)

    @classmethod
    def poc_magnet_long(  # noqa: PLR0917
        cls,
        close: IndicatorSeries,
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCMagnetLong (`inside_va and close < poc - min_deviation`)."""
        if not cls.price_inside_va(close, vah, val, shift=shift):
            return False
        c, p = close.get(shift), poc.get(shift)
        return not (np.isnan(c) or np.isnan(p)) and (c < (p - min_deviation))

    @classmethod
    def poc_magnet_short(  # noqa: PLR0917
        cls,
        close: IndicatorSeries,
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCMagnetShort (`inside_va and close > poc + min_deviation`)."""
        if not cls.price_inside_va(close, vah, val, shift=shift):
            return False
        c, p = close.get(shift), poc.get(shift)
        return not (np.isnan(c) or np.isnan(p)) and (c > (p + min_deviation))

    @classmethod
    def vah_test_rejection(  # noqa: PLR0917
        cls,
        high: IndicatorSeries,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        min_wick: float = 0.0,
        min_rejection: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPVAHTestRejection (`high > vah + wick and close < vah - rej`)."""
        hi, c, u = high.get(shift), close.get(shift), vah.get(shift)
        if any(np.isnan(x) for x in (hi, c, u)):
            return False
        return hi > (u + min_wick) and c < (u - min_rejection)

    @classmethod
    def val_test_rejection(  # noqa: PLR0917
        cls,
        low: IndicatorSeries,
        close: IndicatorSeries,
        val: IndicatorSeries,
        min_wick: float = 0.0,
        min_rejection: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPVALTestRejection (`low < val - wick and close > val + rej`)."""
        lo, c, d = low.get(shift), close.get(shift), val.get(shift)
        if any(np.isnan(x) for x in (lo, c, d)):
            return False
        return lo < (d - min_wick) and c > (d + min_rejection)

    @classmethod
    def value_return_long(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueReturnLong (close inside VA after prior below VAL - dev)."""
        if not cls.price_inside_va(close, vah, val, shift=shift):
            return False
        c1, d1 = close.get(shift + 1), val.get(shift + 1)
        return not (np.isnan(c1) or np.isnan(d1)) and (c1 < (d1 - min_deviation))

    @classmethod
    def value_return_short(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueReturnShort (close inside VA after prior above VAH + dev)."""
        if not cls.price_inside_va(close, vah, val, shift=shift):
            return False
        c1, u1 = close.get(shift + 1), vah.get(shift + 1)
        return not (np.isnan(c1) or np.isnan(u1)) and (c1 > (u1 + min_deviation))

    @classmethod
    def value_shift_up(
        cls,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        lookback_bars: int = 1,
        min_gap: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueShiftUp (`val[s] > vah[s + lookback_bars] + min_gap`)."""
        lb = max(1, lookback_bars)
        cur_val, prior_vah = val.get(shift), vah.get(shift + lb)
        return not (np.isnan(cur_val) or np.isnan(prior_vah)) and (
            cur_val > (prior_vah + min_gap)
        )

    @classmethod
    def value_shift_down(
        cls,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        lookback_bars: int = 1,
        min_gap: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueShiftDown (`vah[s] < val[s + lookback_bars] - min_gap`)."""
        lb = max(1, lookback_bars)
        cur_vah, prior_val = vah.get(shift), val.get(shift + lb)
        return not (np.isnan(cur_vah) or np.isnan(prior_val)) and (
            cur_vah < (prior_val - min_gap)
        )

    @classmethod
    def vwap_cross_up(
        cls, close: IndicatorSeries, vwap: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPVWAPCrossUp (`close` crosses above `vwap`)."""
        return close.crosses_above(vwap, shift=shift)

    @classmethod
    def vwap_cross_down(
        cls, close: IndicatorSeries, vwap: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPVWAPCrossDown (`close` crosses below `vwap`)."""
        return close.crosses_below(vwap, shift=shift)
