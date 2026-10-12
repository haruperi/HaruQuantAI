"""Time Price Opportunity (TPO) Profile Indicator Block.

Description:
    Computes Time Price Opportunity (TPO) market profiles over lookback windows
    or sessions. Tracks price distribution based on bracket time touches rather
    than trade volume, calculating TPO Point of Control (POC), Value Area High
    (VAH), Value Area Low (VAL), and Initial Balance (IB High / Low).

Purpose:
    FEAT-SERVICES-INDICATOR-TPOPROFILE

Key Capabilities:
    - FR-SERVICES-TPOPROFILE-CALCULATE: Computes TPO POC, VAH, VAL, and Initial Balance.
    - FR-SERVICES-TPOPROFILE-CONDITIONS: Evaluates IB breakout and VA containment.

Python API Usage:
    ```python
    from app.services.indicators.tpo_profile import TPOProfile

    profile = TPOProfile.calculate(
        high,
        low,
        close,
        period=48,
        profile_rows=40,
        ib_bars=2,
        value_area_pct=0.70,
    )
    poc = profile["poc"]
    ib_high = profile["ib_high"]
    ib_low = profile["ib_low"]

    # Condition checks
    breakout = TPOProfile.ib_breakout_up(close, ib_high, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

DEFAULT_PERIOD: int = 48
DEFAULT_PROFILE_ROWS: int = 40
DEFAULT_IB_BARS: int = 2
DEFAULT_VALUE_AREA_PCT: float = 0.70


class TPOProfile(BaseIndicator):
    """TPO Profile indicator with Initial Balance and Value Area boundaries."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        *,
        period: int = DEFAULT_PERIOD,
        profile_rows: int = DEFAULT_PROFILE_ROWS,
        ib_bars: int = DEFAULT_IB_BARS,
        value_area_pct: float = DEFAULT_VALUE_AREA_PCT,
    ) -> dict[str, IndicatorSeries]:
        """Calculate TPO POC, VAH, VAL, IB High, and IB Low series.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            period: Lookback window in bars (defaults to 48, min 2).
            profile_rows: Number of price bins (defaults to 40, min 5).
            ib_bars: Number of initial bars forming the Initial Balance (defaults to 2).
            value_area_pct: Value Area proportion (defaults to 0.70).

        Returns:
            Dictionary containing 'poc', 'vah', 'val', 'ib_high', and 'ib_low'.
        """
        h_arr = cls._to_numpy(high)
        l_arr = cls._to_numpy(low)
        c_arr = cls._to_numpy(close)
        n = len(c_arr)

        poc_out = np.full(n, np.nan, dtype=np.float64)
        vah_out = np.full(n, np.nan, dtype=np.float64)
        val_out = np.full(n, np.nan, dtype=np.float64)
        ibh_out = np.full(n, np.nan, dtype=np.float64)
        ibl_out = np.full(n, np.nan, dtype=np.float64)

        if n < period:
            logger.info(
                "FR-SERVICES-TPOPROFILE-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return {
                "poc": IndicatorSeries(poc_out, name="TPO_POC"),
                "vah": IndicatorSeries(vah_out, name="TPO_VAH"),
                "val": IndicatorSeries(val_out, name="TPO_VAL"),
                "ib_high": IndicatorSeries(ibh_out, name="TPO_IBH"),
                "ib_low": IndicatorSeries(ibl_out, name="TPO_IBL"),
            }

        profile_rows = max(5, profile_rows)
        ib_bars = max(1, min(ib_bars, period))

        for i in range(period - 1, n):
            start = i - period + 1
            h_slice = h_arr[start : i + 1]
            l_slice = l_arr[start : i + 1]

            # Initial balance from start of window
            ibh_out[i] = float(np.max(h_slice[:ib_bars]))
            ibl_out[i] = float(np.min(l_slice[:ib_bars]))

            poc_val, vah_val, val_val = cls._compute_tpo_slice(
                h_slice=h_slice,
                l_slice=l_slice,
                profile_rows=profile_rows,
                value_area_pct=value_area_pct,
            )
            poc_out[i] = poc_val
            vah_out[i] = vah_val
            val_out[i] = val_val

        logger.info(
            "FR-SERVICES-TPOPROFILE-CALCULATE: Computed TPO(p=%d, rows=%d) for %d bars",
            period,
            profile_rows,
            n,
        )
        return {
            "poc": IndicatorSeries(poc_out, name="TPO_POC"),
            "vah": IndicatorSeries(vah_out, name="TPO_VAH"),
            "val": IndicatorSeries(val_out, name="TPO_VAL"),
            "ib_high": IndicatorSeries(ibh_out, name="TPO_IBH"),
            "ib_low": IndicatorSeries(ibl_out, name="TPO_IBL"),
        }

    @classmethod
    def _compute_tpo_slice(
        cls,
        *,
        h_slice: np.ndarray[Any, Any],
        l_slice: np.ndarray[Any, Any],
        profile_rows: int,
        value_area_pct: float,
    ) -> tuple[float, float, float]:
        """Compute POC, VAH, and VAL for discrete TPO bracket touches."""
        s_high = float(np.max(h_slice))
        s_low = float(np.min(l_slice))
        price_range = s_high - s_low

        if price_range <= 0.0:
            return s_high, s_high, s_low

        bin_size = price_range / profile_rows
        tpo_counts = np.zeros(profile_rows, dtype=np.float64)

        for h, lo in zip(h_slice, l_slice, strict=True):
            bin_lo = int(
                np.clip(np.floor((lo - s_low) / bin_size), 0, profile_rows - 1)
            )
            bin_hi = int(np.clip(np.floor((h - s_low) / bin_size), 0, profile_rows - 1))
            tpo_counts[bin_lo : bin_hi + 1] += 1.0

        poc_idx = int(np.argmax(tpo_counts))
        poc = s_low + (poc_idx + 0.5) * bin_size

        total_tpo = float(np.sum(tpo_counts))
        if total_tpo <= 0.0:
            return poc, s_high, s_low

        target_tpo = total_tpo * value_area_pct
        current_tpo = float(tpo_counts[poc_idx])
        lo_idx = poc_idx
        hi_idx = poc_idx

        while current_tpo < target_tpo and (lo_idx > 0 or hi_idx < profile_rows - 1):
            next_up = (
                float(tpo_counts[hi_idx + 1]) if hi_idx < profile_rows - 1 else -1.0
            )
            next_dn = float(tpo_counts[lo_idx - 1]) if lo_idx > 0 else -1.0

            if next_up >= next_dn:
                hi_idx += 1
                current_tpo += next_up
            else:
                lo_idx -= 1
                current_tpo += next_dn

        vah = s_low + (hi_idx + 1) * bin_size
        val = s_low + lo_idx * bin_size
        return poc, vah, val

    @classmethod
    def ib_breakout_up(
        cls,
        close: IndicatorSeries,
        ib_high: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close has broken above Initial Balance High."""
        return close.is_greater(ib_high, shift=shift)

    @classmethod
    def ib_breakout_down(
        cls,
        close: IndicatorSeries,
        ib_low: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close has broken below Initial Balance Low."""
        return close.is_lower(ib_low, shift=shift)

    @classmethod
    def price_above_poc(
        cls,
        close: IndicatorSeries,
        poc: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is above TPO POC at specified shift."""
        return close.is_greater(poc, shift=shift)

    @classmethod
    def price_below_poc(
        cls,
        close: IndicatorSeries,
        poc: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is below TPO POC at specified shift."""
        return close.is_lower(poc, shift=shift)

    @classmethod
    def price_inside_va(
        cls,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if price close is within TPO Value Area."""
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
        """Check if price close is outside TPO Value Area."""
        c = close.get(shift)
        upper = vah.get(shift)
        lower = val.get(shift)
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return c > upper or c < lower
