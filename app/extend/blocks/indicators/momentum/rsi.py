"""RSI momentum indicator strategy block.

Description:
    Calculates Relative Strength Index (RSI) momentum oscillator evaluating
    overbought and oversold conditions.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: RSI oscillator calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.rsi import RSI
    res = RSI().calculate(bars)
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
from app.extend.calculators.rsi import rsi_kernel

logger = get_logger(__name__)


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
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated RSI(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="RSI")}


__all__ = ["RSI"]
