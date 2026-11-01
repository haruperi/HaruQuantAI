"""Linear Weighted Moving Average (LWMA) strategy indicator block."""

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
from app.include.calculators.average import lwma_kernel


class LWMA(BaseIndicator):
    """Linear Weighted Moving Average indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.lwma",
        version="1.0.0",
        name="Linear Weighted Moving Average",
        description=(
            "Calculates linearly weighted moving average with weight "
            "proportionally increasing towards recent prices"
        ),
        category="trend",
        tags=("trend", "moving_average", "lwma", "wma"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "LWMA smoothed series"),),
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
        description="Rolling window lookback period in bars",
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid LWMA calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute LWMA over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        values = lwma_kernel(bars.close, self.period)
        return {"value": IndicatorSeries(values, name="LWMA")}


__all__ = ["LWMA"]
