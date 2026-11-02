"""SMA trend indicator strategy block.

Description:
    Calculates Simple Moving Average (SMA) unweighted rolling price mean.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend: Simple moving average computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.sma import SMA
    res = SMA().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

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


class SMA(BaseIndicator):
    """Simple Moving Average indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.sma",
        version="1.0.0",
        name="Simple Moving Average",
        description="Calculates arithmetic mean of prices over a sliding window",
        category="trend",
        tags=("trend", "moving_average", "sma"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "SMA smoothed series"),),
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
        """Return minimum history bars needed for the first valid SMA calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute SMA over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        values = sma_kernel(bars.close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated SMA(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="SMA")}


__all__ = ["SMA"]
