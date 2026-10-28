"""Vortex indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-VORTEX: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.indicators.volatility.atr import ATR
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


MIN_BARS: int = 2


class Vortex(BaseIndicator):
    """Vortex indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.vortex",
        name="Vortex",
        category="trend",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("vi_plus", PortType.SERIES),
            OutputPort("vi_minus", PortType.SERIES),
            OutputPort("oscillator", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.volatility.atr",),
        required_history_lookback=15,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if n != len(high_arr) or n != len(low_arr):
            raise ValueError("High, low, and close arrays must have equal length.")
        if period <= 0:
            logger.warning(
                "FR-SERVICES-VORTEX-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        vi_plus = np.zeros(n, dtype=np.float64)
        vi_minus = np.zeros(n, dtype=np.float64)
        if n <= period or n < MIN_BARS:
            return {
                "vi_plus": IndicatorSeries(vi_plus, name=f"VI+({period})"),
                "vi_minus": IndicatorSeries(vi_minus, name=f"VI-({period})"),
                "oscillator": IndicatorSeries(
                    vi_plus - vi_minus, name=f"VortexOsc({period})"
                ),
            }
        tr = ATR.true_range(high_arr, low_arr, close_arr)
        vm_plus = np.zeros(n, dtype=np.float64)
        vm_minus = np.zeros(n, dtype=np.float64)
        vm_plus[1:] = np.abs(high_arr[1:] - low_arr[:-1])
        vm_minus[1:] = np.abs(low_arr[1:] - high_arr[:-1])
        for t in range(period, n):
            sum_tr = float(np.sum(tr[t - period + 1 : t + 1]))
            sum_vmp = float(np.sum(vm_plus[t - period + 1 : t + 1]))
            sum_vmm = float(np.sum(vm_minus[t - period + 1 : t + 1]))
            if sum_tr > 0:
                vi_plus[t] = sum_vmp / sum_tr
                vi_minus[t] = sum_vmm / sum_tr
            else:
                vi_plus[t] = 0.0
                vi_minus[t] = 0.0
        oscillator = vi_plus - vi_minus
        logger.info(
            "FR-SERVICES-VORTEX-CALCULATE: Computed Vortex(period=%d) for %d bars",
            period,
            n,
        )
        return {
            "vi_plus": IndicatorSeries(vi_plus, name=f"VI+({period})"),
            "vi_minus": IndicatorSeries(vi_minus, name=f"VI-({period})"),
            "oscillator": IndicatorSeries(oscillator, name=f"VortexOsc({period})"),
        }

    @classmethod
    def is_uptrend(cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if Vortex is in uptrend (VI+ > VI-)."""
        return is_greater(
            vx_dict["vi_plus"],
            vx_dict["vi_minus"],
            shift1=shift,
            shift2=shift,
            round_digits=8,
        )

    @classmethod
    def is_downtrend(cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if Vortex is in downtrend (VI+ < VI-)."""
        return is_lower(
            vx_dict["vi_plus"],
            vx_dict["vi_minus"],
            shift1=shift,
            shift2=shift,
            round_digits=8,
        )

    @classmethod
    def changes_trend_up(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ crosses above VI- (bullish reversal)."""
        return crosses_above(
            vx_dict["vi_plus"], vx_dict["vi_minus"], shift=shift, round_digits=8
        )

    @classmethod
    def changes_trend_down(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ crosses below VI- (bearish reversal)."""
        return crosses_below(
            vx_dict["vi_plus"], vx_dict["vi_minus"], shift=shift, round_digits=8
        )

    @classmethod
    def vi_plus_rising(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ is rising."""
        return is_rising(vx_dict["vi_plus"], shift=shift)

    @classmethod
    def vi_plus_falling(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ is falling."""
        return is_falling(vx_dict["vi_plus"], shift=shift)
