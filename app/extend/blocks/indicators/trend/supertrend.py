"""SuperTrend indicator.

- Calculates SuperTrend ATR-based trend direction and trailing support and
  resistance bands.
"""

from __future__ import annotations

from typing import ClassVar, Literal, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons import equals, is_falling, is_rising
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.volatility.atr import ATR
from app.extend.blocks.indicators.volatility.mt_atr import MTATR

logger = get_logger(__name__)


class SuperTrend(BaseIndicator):
    """SuperTrend indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.supertrend",
        version="1.0.0",
        name="SuperTrend",
        description=(
            "Calculates SuperTrend ATR-based trend direction and trailing "
            "support and resistance bands."
        ),
        category="trend",
        tags=("trend", "supertrend"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort("main", PortType.SERIES, description="Main output series"),
            OutputPort("trend", PortType.SERIES, description="Trend output series"),
            OutputPort("upper", PortType.SERIES, description="Upper output series"),
            OutputPort("lower", PortType.SERIES, description="Lower output series"),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=25,
        dependencies=("indicator.volatility.atr", "indicator.volatility.mt_atr"),
        is_generation_eligible=True,
        parameter_search_space={
            "mode": {"type": "int", "choices": [1, 2], "default": 1},
            "atr_period": {"type": "int", "min": 1, "max": 96, "default": 24},
            "atr_mult": {
                "type": "float",
                "min": 0.0,
                "max": 12.0,
                "default": 3.0,
                "min_exclusive": True,
            },
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    mode: Literal[1, 2] = Field(
        default=1, title="Mode", description="Mode used by the indicator calculation"
    )

    atr_period: int = Field(
        default=24,
        ge=1,
        title="Atr period",
        description="Number of bars in the atr window",
    )

    atr_mult: float = Field(
        default=3.0,
        gt=0.0,
        title="Atr mult",
        description="ATR multiplier used to place the trend bands",
    )

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.atr_period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: SuperTrend requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        mode = self.mode
        atr_period = self.atr_period
        atr_mult = self.atr_mult
        high_arr = bars.high
        low_arr = bars.low
        close_arr = bars.close
        n = len(close_arr)
        if n != len(high_arr) or n != len(low_arr):
            raise ValueError("High, low, and close arrays must have equal length.")
        if mode == 1:
            atr_series = MTATR(period=atr_period).calculate(bars)["value"]
        else:
            atr_series = ATR(period=atr_period).calculate(bars)["value"]
        atr_vals = atr_series.values
        st_arr = np.zeros(n, dtype=np.float64)
        trend_arr = np.zeros(n, dtype=np.float64)
        upper_arr = np.zeros(n, dtype=np.float64)
        lower_arr = np.zeros(n, dtype=np.float64)
        if n > 0:
            median0 = (high_arr[0] + low_arr[0]) / 2.0
            atr0 = atr_vals[0] if not np.isnan(atr_vals[0]) else 0.0
            upper_arr[0] = median0 + atr_mult * atr0
            lower_arr[0] = median0 - atr_mult * atr0
            st_arr[0] = lower_arr[0]
            trend_arr[0] = 1.0 if close_arr[0] >= st_arr[0] else -1.0
        for i in range(1, n):
            median = (high_arr[i] + low_arr[i]) / 2.0
            atr_v = atr_vals[i] if not np.isnan(atr_vals[i]) else 0.0
            d_upper = median + atr_mult * atr_v
            d_lower = median - atr_mult * atr_v
            upper_arr[i] = d_upper
            lower_arr[i] = d_lower
            prev_st = st_arr[i - 1]
            curr_c = close_arr[i]
            prev_c = close_arr[i - 1]
            if curr_c > prev_st and prev_c <= prev_st:
                st_arr[i] = d_lower
            elif curr_c < prev_st and prev_c >= prev_st:
                st_arr[i] = d_upper
            elif prev_st < d_lower:
                st_arr[i] = d_lower
            elif prev_st > d_upper:
                st_arr[i] = d_upper
            else:
                st_arr[i] = prev_st
            trend_arr[i] = 1.0 if curr_c >= st_arr[i] else -1.0
        logger.info(
            "FR-SERVICES-SUPERTREND-CALCULATE: ST(m=%d, p=%d, mult=%.2f) for %d bars",
            mode,
            atr_period,
            atr_mult,
            n,
        )
        param_label = f"{mode},{atr_period},{atr_mult}"
        return {
            "main": IndicatorSeries(st_arr, name=f"SuperTrend({param_label})"),
            "trend": IndicatorSeries(
                trend_arr, name=f"SuperTrend.Trend({param_label})"
            ),
            "upper": IndicatorSeries(
                upper_arr, name=f"SuperTrend.Upper({param_label})"
            ),
            "lower": IndicatorSeries(
                lower_arr, name=f"SuperTrend.Lower({param_label})"
            ),
        }

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def is_uptrend(cls, st_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if SuperTrend is in uptrend (rising line)."""
        res = is_rising(st_dict["main"], shift=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-SUPERTREND-CONDITIONS is_uptrend shift=%d res=%s", shift, res
        )
        return res

    @classmethod
    def is_downtrend(cls, st_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if SuperTrend is in downtrend (falling line)."""
        res = is_falling(st_dict["main"], shift=shift, round_digits=8)
        logger.debug(
            "FR-SERVICES-SUPERTREND-CONDITIONS is_downtrend shift=%d res=%s", shift, res
        )
        return res

    @classmethod
    def is_in_range(cls, st_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if SuperTrend is in range (flat line)."""
        res = equals(
            st_dict["main"],
            st_dict["main"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=5,
        )
        logger.debug(
            "FR-SERVICES-SUPERTREND-CONDITIONS is_in_range shift=%d res=%s", shift, res
        )
        return res


# Public exports.
__all__ = ["SuperTrend"]
