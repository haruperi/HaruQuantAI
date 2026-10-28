"""Moving Average Convergence Divergence (MACD) strategy indicator block."""

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
from app.include.numerical.macd import macd_kernel


class MACD(BaseIndicator):
    """Moving Average Convergence Divergence indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.macd",
        version="1.0.0",
        name="Moving Average Convergence Divergence",
        description=(
            "Calculates trend-following momentum indicator showing "
            "relationship between two exponential moving averages"
        ),
        category="momentum",
        tags=("momentum", "oscillator", "macd"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(
            OutputPort("main", PortType.SERIES, "MACD main line"),
            OutputPort("signal", PortType.SERIES, "MACD signal line"),
            OutputPort("histogram", PortType.SERIES, "MACD histogram"),
        ),
        required_market_inputs=("close",),
        is_generation_eligible=True,
        parameter_search_space={
            "fast": {"type": "int", "min": 2, "max": 100, "default": 12},
            "slow": {"type": "int", "min": 2, "max": 200, "default": 26},
            "smooth": {"type": "int", "min": 1, "max": 50, "default": 9},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    fast: int = Field(
        default=12,
        ge=1,
        title="Fast Period",
        description="Fast EMA smoothing period in bars",
    )
    slow: int = Field(
        default=26,
        ge=1,
        title="Slow Period",
        description="Slow EMA smoothing period in bars",
    )
    smooth: int = Field(
        default=9,
        ge=1,
        title="Signal Period",
        description="Signal line SMA smoothing period in bars",
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid MACD calculation."""
        return max(self.fast, self.slow) + self.smooth - 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute MACD over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'main', 'signal', and 'histogram' series.
        """
        lines = macd_kernel(bars.close, self.fast, self.slow, self.smooth)
        return {
            "main": IndicatorSeries(lines["main"], name="MACD.Main"),
            "signal": IndicatorSeries(lines["signal"], name="MACD.Signal"),
            "histogram": IndicatorSeries(lines["histogram"], name="MACD.Histogram"),
        }


__all__ = ["MACD"]
