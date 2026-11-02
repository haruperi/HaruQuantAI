"""TEMA trend indicator strategy block.

Description:
    Calculates Triple Exponential Moving Average (TEMA) minimizing lag
    via triple smoothing.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend: Triple exponential moving average calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.tema import TEMA
    res = TEMA().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

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
from app.extend.calculators.average import tema_kernel

logger = get_logger(__name__)


class TEMA(BaseIndicator):
    """Triple Exponential Moving Average indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.tema",
        version="1.0.0",
        name="Triple Exponential Moving Average",
        description=(
            "Calculates triple smoothed exponential moving average "
            "reducing lag (3*EMA1 - 3*EMA2 + EMA3)"
        ),
        category="trend",
        tags=("trend", "moving_average", "tema"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(OutputPort("value", PortType.SERIES, "TEMA smoothed series"),),
        required_market_inputs=("close",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 200, "default": 14}
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
        """Return minimum history bars needed for the first valid TEMA calculation."""
        return 3 * self.period - 2

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute TEMA over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with 'value' series matching input bar length.
        """
        values = tema_kernel(bars.close, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated TEMA(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(values, name="TEMA")}


__all__ = ["TEMA"]
