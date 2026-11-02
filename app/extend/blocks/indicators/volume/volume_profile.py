"""VolumeProfile volume indicator strategy block.

Description:
    Calculates session Volume Profile (POC, VAH, VAL) across trading hours.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-volume: Volume profile price distribution calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
    res = VolumeProfile().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, Literal, override
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np
from pydantic import Field, field_validator

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.profile import VOLUME_OUTPUTS
from app.extend.calculators.profile_sessions import calculate_sessions

logger = get_logger(__name__)


class VolumeProfile(BaseIndicator):
    """Donor session profiles with validated in-class configuration."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.volume_profile",
        version="2.0.0",
        name="VolumeProfile",
        category="volume",
        chart_pane=ChartPane.MAIN,
        inputs=tuple(
            InputPort(name, PortType.SERIES, required=True)
            for name in ("open", "high", "low", "close", "volume", "timestamps")
        ),
        outputs=tuple(
            OutputPort(name, PortType.SERIES)
            for name in VOLUME_OUTPUTS
            + tuple(
                f"{session}_{key}"
                for session in ("london", "new_york", "sydney", "tokyo")
                for key in ("poc", "vah", "val")
            )
        ),
        required_market_inputs=("open", "high", "low", "close", "volume", "timestamps"),
        is_causal=True,
        is_generation_eligible=False,
        required_history_lookback=1,
    )
    timestamp_unit: Literal["seconds", "milliseconds"] = "seconds"
    timezone: str = "UTC"
    bin_size_mode: Literal[1, 2] = 2
    tick_size: float | None = Field(default=None, gt=0)
    ticks_per_bin: int = Field(default=3, ge=1, le=1000)
    value_area_pct: float = Field(default=70.0, ge=65, le=75)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        """Require a real chart timezone rather than guessing broker local time."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown chart timezone") from exc
        return value

    session_type: int = Field(default=2, ge=1, le=10)
    profile_mode: Literal["calendar", "custom", "multi"] = "calendar"
    profile_rows: int = Field(default=50, ge=10, le=100)
    session_start: int = Field(default=480, ge=0, le=1439)
    session_end: int = Field(default=960, ge=0, le=1439)
    session_mode: Literal[1, 2] = 1
    ib_minutes: int = Field(default=0, ge=0, le=14400)
    hvn_count: int = Field(default=5, ge=1, le=10)
    hvn_threshold_pct: int = Field(default=20, ge=10, le=90)
    lvn_threshold_pct: int = Field(default=40, ge=10, le=90)
    enable_lvn: bool = False
    enable_vcp: bool = False
    cluster_spread: float = Field(default=6.0, ge=0.5, le=20)
    max_cluster_centers: int = Field(default=2, ge=1, le=10)
    pivot_method: Literal[1, 2, 3] = 1
    pivot_pct: float = Field(default=2.0, ge=0.01, le=10)
    pivot_ticks: int = Field(default=50, ge=1, le=10000)
    pivot_atr_multiple: float = Field(default=1.5, ge=0.1, le=10)
    pivot_atr_period: int = Field(default=14, ge=2, le=200)
    enable_london: bool = True
    london_start: int = Field(default=420, ge=0, le=1439)
    london_end: int = Field(default=960, ge=0, le=1439)
    enable_new_york: bool = True
    new_york_start: int = Field(default=780, ge=0, le=1439)
    new_york_end: int = Field(default=1320, ge=0, le=1439)
    enable_sydney: bool = False
    sydney_start: int = Field(default=1260, ge=0, le=1439)
    sydney_end: int = Field(default=360, ge=0, le=1439)
    enable_tokyo: bool = True
    tokyo_start: int = Field(default=0, ge=0, le=1439)
    tokyo_end: int = Field(default=540, ge=0, le=1439)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Calculate calendar, custom-hour or independent named session profiles."""
        config = self.model_dump()
        if self.profile_mode == "calendar":
            result = calculate_sessions(bars, config)
        else:
            config["session_type"] = 1 if self.session_mode == 1 else 5
            if self.profile_mode == "custom":
                result = calculate_sessions(
                    bars, config, custom=(self.session_start, self.session_end)
                )
            else:
                result = {}
                for name in ("london", "new_york", "sydney", "tokyo"):
                    if getattr(self, "enable_" + name):
                        session = calculate_sessions(
                            bars,
                            config,
                            custom=(
                                getattr(self, name + "_start"),
                                getattr(self, name + "_end"),
                            ),
                            multi=True,
                        )
                        if not result:
                            result.update(session)
                        for key in ("poc", "vah", "val"):
                            result[name + "_" + key] = session[key]
        for port in self.spec.outputs:
            if port.name not in result:
                result[port.name] = IndicatorSeries(
                    np.zeros(len(bars.close)), name=port.name.upper()
                )
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated VolumeProfile for %d bars",
            len(bars),
        )
        return result

    @staticmethod
    def price_inside_va(
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPriceInsideVA (`val[shift] <= close[shift] <= vah[shift]`)."""
        c, upper, lower = (close.get(shift), vah.get(shift), val.get(shift))
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return lower <= c <= upper

    @staticmethod
    def price_outside_va(
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPriceOutsideVA (`close[s] > vah[s] or close[s] < val[s]`)."""
        c, upper, lower = (close.get(shift), vah.get(shift), val.get(shift))
        if np.isnan(c) or np.isnan(upper) or np.isnan(lower):
            return False
        return c > upper or c < lower

    @staticmethod
    def is_narrow_value_area(
        vah: IndicatorSeries, val: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """Evaluate VPNarrowValueArea (`0 < (vah - val) < threshold`)."""
        upper, lower = (vah.get(shift), val.get(shift))
        if np.isnan(upper) or np.isnan(lower):
            return False
        width = upper - lower
        return 0.0 < width < threshold

    @staticmethod
    def is_wide_value_area(
        vah: IndicatorSeries, val: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """Evaluate VPWideValueArea (`(vah - val) > threshold`)."""
        upper, lower = (vah.get(shift), val.get(shift))
        if np.isnan(upper) or np.isnan(lower):
            return False
        return upper - lower > threshold

    @staticmethod
    def bottom_heavy_poc(
        poc_pct_down: IndicatorSeries, threshold_pct: float = 35.0, shift: int = 0
    ) -> bool:
        """Evaluate VPBottomHeavyPOC (`0 < poc_pct_down[shift] < threshold_pct`)."""
        v = poc_pct_down.get(shift)
        return not np.isnan(v) and 0.0 < v < threshold_pct

    @staticmethod
    def top_heavy_poc(
        poc_pct_up: IndicatorSeries, threshold_pct: float = 35.0, shift: int = 0
    ) -> bool:
        """Evaluate VPTopHeavyPOC (`0 < poc_pct_up[shift] < threshold_pct`)."""
        v = poc_pct_up.get(shift)
        return not np.isnan(v) and 0.0 < v < threshold_pct

    @staticmethod
    def ib_breakout_up(
        close: IndicatorSeries, ibh: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPIBBreakoutUp (`ibh[shift] > 0 and close[shift] > ibh[shift]`)."""
        c, h = (close.get(shift), ibh.get(shift))
        return not (np.isnan(c) or np.isnan(h)) and (h > 0.0 and c > h)

    @staticmethod
    def ib_breakout_down(
        close: IndicatorSeries, ibl: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Evaluate VPIBBreakoutDown (`ibl[s] > 0 and close[s] < ibl[s]`)."""
        c, lo = (close.get(shift), ibl.get(shift))
        return not (np.isnan(c) or np.isnan(lo)) and (lo > 0.0 and c < lo)

    @staticmethod
    def ib_rejection_long(
        low: IndicatorSeries,
        close: IndicatorSeries,
        ibl: IndicatorSeries,
        tolerance: float = 0.0,
        min_rejection: float = 0.0,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPIBRejectionLong (`low < ibl - tol and close > ibl + rej`)."""
        lo, c, b = (low.get(shift), close.get(shift), ibl.get(shift))
        if any(np.isnan(x) for x in (lo, c, b)):
            return False
        return b > 0.0 and lo < b - tolerance and (c > b + min_rejection)

    @staticmethod
    def ib_rejection_short(
        high: IndicatorSeries,
        close: IndicatorSeries,
        ibh: IndicatorSeries,
        tolerance: float = 0.0,
        min_rejection: float = 0.0,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPIBRejectionShort (`high > ibh + tol and close < ibh - rej`)."""
        hi, c, b = (high.get(shift), close.get(shift), ibh.get(shift))
        if any(np.isnan(x) for x in (hi, c, b)):
            return False
        return b > 0.0 and hi > b + tolerance and (c < b - min_rejection)

    @staticmethod
    def excess_reversal_long(
        open_prices: IndicatorSeries,
        high: IndicatorSeries,
        low: IndicatorSeries,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        *,
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
        u, d = (vah.get(shift), val.get(shift))
        if any(np.isnan(x) for x in (o, hi, lo, c, u, d)):
            return False
        if lo >= d - min_wick or c < d or c > u:
            return False
        body = abs(c - o)
        lower_wick = min(o, c) - lo
        return lower_wick > wick_ratio * max(body, tick_size)

    @staticmethod
    def excess_reversal_short(
        open_prices: IndicatorSeries,
        high: IndicatorSeries,
        low: IndicatorSeries,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        *,
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
        u, d = (vah.get(shift), val.get(shift))
        if any(np.isnan(x) for x in (o, hi, lo, c, u, d)):
            return False
        if hi <= u + min_wick or c > u or c < d:
            return False
        body = abs(c - o)
        upper_wick = hi - max(o, c)
        return upper_wick > wick_ratio * max(body, tick_size)

    @staticmethod
    def rising_poc(
        poc: IndicatorSeries,
        lookback_bars: int = 1,
        min_shift: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPRisingPOC (`poc[s] > average_offset`)."""
        lb = max(1, lookback_bars)
        p0, pp = (poc.get(shift), poc.get(shift + lb))
        return not (np.isnan(p0) or np.isnan(pp)) and p0 > pp + min_shift

    @staticmethod
    def falling_poc(
        poc: IndicatorSeries,
        lookback_bars: int = 1,
        min_shift: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPFallingPOC (`poc[s] < average_offset`)."""
        lb = max(1, lookback_bars)
        p0, pp = (poc.get(shift), poc.get(shift + lb))
        return not (np.isnan(p0) or np.isnan(pp)) and p0 < pp - min_shift

    @staticmethod
    def late_acceptance_failure_long(
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPLateAcceptanceFailureLong (3 bars below VAL then inside VA)."""
        if not VolumeProfile.price_inside_va(close, vah, val, shift=shift):
            return False
        for k in (1, 2, 3):
            ck, vk = (close.get(shift + k), val.get(shift + k))
            if np.isnan(ck) or np.isnan(vk) or ck >= vk - min_deviation:
                return False
        return True

    @staticmethod
    def late_acceptance_failure_short(
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPLateAcceptanceFailureShort (3 bars above VAH then inside VA)."""
        if not VolumeProfile.price_inside_va(close, vah, val, shift=shift):
            return False
        for k in (1, 2, 3):
            ck, vk = (close.get(shift + k), vah.get(shift + k))
            if np.isnan(ck) or np.isnan(vk) or ck <= vk + min_deviation:
                return False
        return True

    @staticmethod
    def open_drive_long(
        open_prices: IndicatorSeries,
        close: IndicatorSeries,
        min_move: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPOpenDriveLong (3 bullish bars with net move >= `min_move`)."""
        for k in (0, 1, 2):
            ok, ck = (open_prices.get(shift + k), close.get(shift + k))
            if np.isnan(ok) or np.isnan(ck) or ck <= ok:
                return False
        return close.get(shift) - open_prices.get(shift + 2) >= min_move

    @staticmethod
    def open_drive_short(
        open_prices: IndicatorSeries,
        close: IndicatorSeries,
        min_move: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPOpenDriveShort (3 bearish bars with net move >= `min_move`)."""
        for k in (0, 1, 2):
            ok, ck = (open_prices.get(shift + k), close.get(shift + k))
            if np.isnan(ok) or np.isnan(ck) or ck >= ok:
                return False
        return open_prices.get(shift + 2) - close.get(shift) >= min_move

    @staticmethod
    def poc_at_edge_long(
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        edge_pct: float = 20.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCAtEdgeLong (`poc >= vah - (vah - val) * edge_pct / 100`)."""
        p, u, d = (poc.get(shift), vah.get(shift), val.get(shift))
        if any(np.isnan(x) for x in (p, u, d)) or u - d <= 0.0:
            return False
        return p >= u - (u - d) * (edge_pct / 100.0)

    @staticmethod
    def poc_at_edge_short(
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        edge_pct: float = 20.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCAtEdgeShort (`poc <= val + (vah - val) * edge_pct / 100`)."""
        p, u, d = (poc.get(shift), vah.get(shift), val.get(shift))
        if any(np.isnan(x) for x in (p, u, d)) or u - d <= 0.0:
            return False
        return p <= d + (u - d) * (edge_pct / 100.0)

    @staticmethod
    def poc_magnet_long(
        close: IndicatorSeries,
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCMagnetLong (`inside_va and close < poc - min_deviation`)."""
        if not VolumeProfile.price_inside_va(close, vah, val, shift=shift):
            return False
        c, p = (close.get(shift), poc.get(shift))
        return not (np.isnan(c) or np.isnan(p)) and c < p - min_deviation

    @staticmethod
    def poc_magnet_short(
        close: IndicatorSeries,
        poc: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPPOCMagnetShort (`inside_va and close > poc + min_deviation`)."""
        if not VolumeProfile.price_inside_va(close, vah, val, shift=shift):
            return False
        c, p = (close.get(shift), poc.get(shift))
        return not (np.isnan(c) or np.isnan(p)) and c > p + min_deviation

    @staticmethod
    def vah_test_rejection(
        high: IndicatorSeries,
        close: IndicatorSeries,
        vah: IndicatorSeries,
        min_wick: float = 0.0,
        min_rejection: float = 0.0,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPVAHTestRejection (`high > vah + wick and close < vah - rej`)."""
        hi, c, u = (high.get(shift), close.get(shift), vah.get(shift))
        if any(np.isnan(x) for x in (hi, c, u)):
            return False
        return hi > u + min_wick and c < u - min_rejection

    @staticmethod
    def val_test_rejection(
        low: IndicatorSeries,
        close: IndicatorSeries,
        val: IndicatorSeries,
        min_wick: float = 0.0,
        min_rejection: float = 0.0,
        *,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPVALTestRejection (`low < val - wick and close > val + rej`)."""
        lo, c, d = (low.get(shift), close.get(shift), val.get(shift))
        if any(np.isnan(x) for x in (lo, c, d)):
            return False
        return lo < d - min_wick and c > d + min_rejection

    @staticmethod
    def value_return_long(
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueReturnLong (close inside VA after prior below VAL - dev)."""
        if not VolumeProfile.price_inside_va(close, vah, val, shift=shift):
            return False
        c1, d1 = (close.get(shift + 1), val.get(shift + 1))
        return not (np.isnan(c1) or np.isnan(d1)) and c1 < d1 - min_deviation

    @staticmethod
    def value_return_short(
        close: IndicatorSeries,
        vah: IndicatorSeries,
        val: IndicatorSeries,
        min_deviation: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueReturnShort (close inside VA after prior above VAH + dev)."""
        if not VolumeProfile.price_inside_va(close, vah, val, shift=shift):
            return False
        c1, u1 = (close.get(shift + 1), vah.get(shift + 1))
        return not (np.isnan(c1) or np.isnan(u1)) and c1 > u1 + min_deviation

    @staticmethod
    def value_shift_up(
        vah: IndicatorSeries,
        val: IndicatorSeries,
        lookback_bars: int = 1,
        min_gap: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueShiftUp (`val[s] > vah[s + lookback_bars] + min_gap`)."""
        lb = max(1, lookback_bars)
        cur_val, prior_vah = (val.get(shift), vah.get(shift + lb))
        return (
            not (np.isnan(cur_val) or np.isnan(prior_vah))
            and cur_val > prior_vah + min_gap
        )

    @staticmethod
    def value_shift_down(
        vah: IndicatorSeries,
        val: IndicatorSeries,
        lookback_bars: int = 1,
        min_gap: float = 0.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate VPValueShiftDown (`vah[s] < val[s + lookback_bars] - min_gap`)."""
        lb = max(1, lookback_bars)
        cur_vah, prior_val = (vah.get(shift), val.get(shift + lb))
        return (
            not (np.isnan(cur_vah) or np.isnan(prior_val))
            and cur_vah < prior_val - min_gap
        )
