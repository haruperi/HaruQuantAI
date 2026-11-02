"""Chaikin Oscillator volume strategy block.

Description:
    Calculates the Chaikin Oscillator as the difference between 3-day and
    10-day exponential moving averages of the Accumulation/Distribution Line.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-chaikin-oscillator: Chaikin oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.chaikin_oscillator import (
        ChaikinOscillator,
    )
    res = ChaikinOscillator().calculate(bars)
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
from app.extend.blocks.indicators.volume.accumulation_distribution import (
    adl_kernel,
)
from app.extend.calculators.average import ema_kernel

logger = get_logger(__name__)


class ChaikinOscillator(BaseIndicator):
    """Chaikin Oscillator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.chaikin_oscillator",
        version="1.0.0",
        name="Chaikin Oscillator",
        description="MACD applied to Accumulation/Distribution Line (3-EMA - 10-EMA)",
        category="volume",
        tags=("volume", "oscillator", "chaikin", "adl"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
            InputPort("close", PortType.SERIES, "Close price series", required=True),
            InputPort("volume", PortType.SERIES, "Volume series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Chaikin Oscillator"),),
        required_market_inputs=("high", "low", "close", "volume"),
        parameter_search_space={
            "fast_period": {"type": "int", "min": 2, "max": 20, "default": 3},
            "slow_period": {"type": "int", "min": 5, "max": 50, "default": 10},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    fast_period: int = Field(default=3, ge=1)
    slow_period: int = Field(default=10, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(self.fast_period, self.slow_period)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Chaikin Oscillator values."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        close = np.asarray(bars.close, dtype=np.float64)
        volume = np.asarray(bars.volume, dtype=np.float64)
        adl = adl_kernel(high, low, close, volume)
        fast_ema = ema_kernel(adl, self.fast_period)
        slow_ema = ema_kernel(adl, self.slow_period)
        co = fast_ema - slow_ema
        logger.debug(
            "FR-SERVICES-INDICATOR-VOLUME: Calculated ChaikinOsc(%d, %d) for %d bars",
            self.fast_period,
            self.slow_period,
            len(bars),
        )
        return {"value": IndicatorSeries(co, name="ChaikinOsc")}


__all__ = ["ChaikinOscillator"]
