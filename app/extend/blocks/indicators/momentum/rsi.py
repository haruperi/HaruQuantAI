"""Relative Strength Index (RSI) strategy indicator block."""

from __future__ import annotations

from typing import ClassVar, override

from pydantic import Field

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
from app.extend.calculators.rsi import rsi_kernel


class RSI(BaseIndicator):
    """Relative Strength Index indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.rsi",
        version="1.0.0",
        name="Relative Strength Index",
        description=(
            "Calculates oscillator measuring speed and change of price movements"
        ),
        category="momentum",
        tags=("momentum", "oscillator", "rsi"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "RSI momentum series"),),
        required_market_inputs=("close",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    period: int = Field(
        default=14,
        ge=1,
        title="Period",
        description="Smoothing lookback period in bars",
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid RSI calculation."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute RSI over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        values = rsi_kernel(bars.close, self.period)
        return {"value": IndicatorSeries(values, name="RSI")}


__all__ = ["RSI"]
