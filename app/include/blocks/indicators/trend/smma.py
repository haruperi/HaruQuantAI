"""Smoothed Moving Average (SMMA / Wilder's MA) strategy indicator block."""

from __future__ import annotations

from typing import ClassVar, override

from pydantic import Field

from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.average import smma_kernel


class SMMA(BaseIndicator):
    """Smoothed Moving Average (Wilder's MA) indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.smma",
        version="1.0.0",
        name="Smoothed Moving Average",
        description=(
            "Calculates smoothed moving average using Wilder's smoothing algorithm"
        ),
        category="trend",
        tags=("trend", "moving_average", "smma", "wilder"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "SMMA smoothed series"),),
        required_market_inputs=("close",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 200, "default": 20}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    period: int = Field(
        default=20,
        ge=1,
        title="Period",
        description="Smoothing lookback period in bars",
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid SMMA calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute SMMA over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        values = smma_kernel(bars.close, self.period)
        return {"value": IndicatorSeries(values, name="SMMA")}


__all__ = ["SMMA"]
