"""Vortex indicator.

- Calculates Vortex Indicator positive and negative trend line flows.
"""

from __future__ import annotations

from typing import ClassVar, override

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
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.volatility.atr import ATR

logger = get_logger(__name__)
MIN_BARS: int = 2


class Vortex(BaseIndicator):
    """Vortex indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.vortex",
        version="1.0.0",
        name="Vortex",
        description=(
            "Calculates Vortex Indicator positive and negative trend line flows."
        ),
        category="trend",
        tags=("trend", "vortex"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
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
            OutputPort("vi_plus", PortType.SERIES, description="Vi plus output series"),
            OutputPort(
                "vi_minus", PortType.SERIES, description="Vi minus output series"
            ),
            OutputPort(
                "oscillator", PortType.SERIES, description="Oscillator output series"
            ),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=15,
        dependencies=("indicator.volatility.atr",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=14,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
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
        return self.period + 1

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug("FR-indicator-calculation: Vortex requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
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


# Public exports.
__all__ = ["Vortex"]
