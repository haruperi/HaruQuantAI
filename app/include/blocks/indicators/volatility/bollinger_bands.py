"""Bollinger Bands (BB) strategy indicator block."""

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
from app.include.numerical.bollinger_bands import bollinger_bands_kernel


class BollingerBands(BaseIndicator):
    """Bollinger Bands volatility indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.bollinger_bands",
        version="1.0.0",
        name="Bollinger Bands",
        description=(
            "Calculates volatility envelopes around a moving average "
            "using standard deviation"
        ),
        category="volatility",
        tags=("volatility", "bands", "bollinger"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Bollinger Band"),
            OutputPort("middle", PortType.SERIES, "Middle Bollinger Band (SMA)"),
            OutputPort("lower", PortType.SERIES, "Lower Bollinger Band"),
            OutputPort("bandwidth", PortType.SERIES, "Normalized Bollinger BandWidth"),
            OutputPort("range", PortType.SERIES, "Bollinger Band Range"),
        ),
        required_market_inputs=("close",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
            "deviation": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0},
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
    deviation: float = Field(
        default=2.0,
        gt=0.0,
        title="Deviation",
        description="Standard deviation multiplier for bands",
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid BB calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Bollinger Bands over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with upper, middle, lower, bandwidth, and range series.
        """
        bands = bollinger_bands_kernel(bars.close, self.period, self.deviation)
        return {
            "upper": IndicatorSeries(bands["upper"], name="BB.Upper"),
            "middle": IndicatorSeries(bands["middle"], name="BB.Middle"),
            "lower": IndicatorSeries(bands["lower"], name="BB.Lower"),
            "bandwidth": IndicatorSeries(bands["bandwidth"], name="BB.BandWidth"),
            "range": IndicatorSeries(bands["range"], name="BB.Range"),
        }


__all__ = ["BollingerBands"]
