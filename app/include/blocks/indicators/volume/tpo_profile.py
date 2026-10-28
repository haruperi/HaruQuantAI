"""TPOProfile indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-TPOPROFILE: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_PERIOD: int = 48
DEFAULT_PROFILE_ROWS: int = 40
DEFAULT_IB_BARS: int = 2
DEFAULT_VALUE_AREA_PCT: float = 0.7


class TPOProfile(BaseIndicator):
    """TPO Profile indicator with Initial Balance and Value Area boundaries."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.tpo_profile",
        name="TPOProfile",
        category="volume",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("poc", PortType.SERIES),
            OutputPort("vah", PortType.SERIES),
            OutputPort("val", PortType.SERIES),
            OutputPort("ib_high", PortType.SERIES),
            OutputPort("ib_low", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 192, "default": 48},
            "profile_rows": {"type": "int", "min": 5, "max": 160, "default": 40},
            "ib_bars": {"type": "int", "min": 1, "max": 8, "default": 2},
            "value_area_pct": {
                "type": "float",
                "min": 0.1,
                "max": 0.99,
                "default": 0.7,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=48,
    )
    period: int = Field(default=DEFAULT_PERIOD, ge=1)
    profile_rows: int = Field(default=DEFAULT_PROFILE_ROWS, ge=5)
    ib_bars: int = Field(default=DEFAULT_IB_BARS, ge=1)
    value_area_pct: float = Field(default=DEFAULT_VALUE_AREA_PCT, ge=0.1, le=0.99)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        profile_rows = self.profile_rows
        ib_bars = self.ib_bars
        value_area_pct = self.value_area_pct
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
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
            ibh_out[i] = float(np.max(h_slice[:ib_bars]))
            ibl_out[i] = float(np.min(l_slice[:ib_bars]))
            poc_val, vah_val, val_val = self._compute_tpo_slice(
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
            return (s_high, s_high, s_low)
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
            return (poc, s_high, s_low)
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
        return (poc, vah, val)

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
