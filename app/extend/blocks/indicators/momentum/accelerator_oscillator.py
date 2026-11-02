"""Accelerator Oscillator momentum indicator strategy block.

Description:
    Calculates Bill Williams Accelerator Oscillator (AC) as the difference
    between Awesome Oscillator and its 5-period simple moving average.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-accelerator-oscillator: Accelerator oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.accelerator_oscillator import (
        AcceleratorOscillator,
    )
    res = AcceleratorOscillator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


def _safe_sma(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = np.where(~np.isnan(x))[0]
    if len(valid) >= period:
        start = int(valid[0])
        out[start:] = sma_kernel(x[start:], period)
    return out


class AcceleratorOscillator(BaseIndicator):
    """Bill Williams Accelerator Oscillator (AC) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.accelerator_oscillator",
        version="1.0.0",
        name="Accelerator Oscillator",
        description="Measures acceleration or deceleration of driving force",
        category="momentum",
        tags=("momentum", "oscillator", "bill_williams", "accelerator"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Accelerator Oscillator"),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "fast_period": {"type": "int", "min": 2, "max": 20, "default": 5},
            "slow_period": {"type": "int", "min": 10, "max": 100, "default": 34},
            "smooth_period": {"type": "int", "min": 2, "max": 20, "default": 5},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    fast_period: int = Field(default=5, ge=1)
    slow_period: int = Field(default=34, ge=1)
    smooth_period: int = Field(default=5, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(self.fast_period, self.slow_period) + self.smooth_period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Accelerator Oscillator values over historical bars."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        median = (high + low) / 2.0
        fast_sma = sma_kernel(median, self.fast_period)
        slow_sma = sma_kernel(median, self.slow_period)
        ao = fast_sma - slow_sma
        ao_sma = _safe_sma(ao, self.smooth_period)
        ac = ao - ao_sma
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated AC(%d, %d, %d) for %d bars",
            self.fast_period,
            self.slow_period,
            self.smooth_period,
            len(bars),
        )
        return {"value": IndicatorSeries(ac, name="AC")}


__all__ = ["AcceleratorOscillator"]
