"""Detrended Price Oscillator strategy block.

Description:
    Calculates Detrended Price Oscillator (DPO) removing trend to highlight
    short-term price cycles by comparing price to a shifted moving average.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-detrended-price-oscillator: DPO cycle computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.detrended_price_oscillator import (
        DetrendedPriceOscillator,
    )
    res = DetrendedPriceOscillator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class DetrendedPriceOscillator(BaseIndicator):
    """Detrended Price Oscillator (DPO) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.detrended_price_oscillator",
        version="1.0.0",
        name="Detrended Price Oscillator",
        description="Isolates short-term cycles by eliminating longer-term trend",
        category="momentum",
        tags=("momentum", "oscillator", "dpo", "cycles"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Detrended Price Oscillator"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 21},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=21, ge=2)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period + (self.period // 2 + 1)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Detrended Price Oscillator values over historical bars."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        shift = self.period // 2 + 1
        sma = sma_kernel(close, self.period)
        dpo = np.full(n, np.nan, dtype=np.float64)
        if n >= self.period + shift:
            for i in range(self.period - 1 + shift, n):
                if not np.isnan(sma[i]):
                    dpo[i] = close[i - shift] - sma[i]
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated DPO(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(dpo, name="DPO")}


__all__ = ["DetrendedPriceOscillator"]
