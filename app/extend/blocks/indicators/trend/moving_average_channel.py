"""Moving Average Channel strategy block.

Description:
    Calculates a price channel constructed from simple moving averages
    applied separately to high and low prices.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-moving-average-channel: MA Channel computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.moving_average_channel import (
        MovingAverageChannel,
    )
    res = MovingAverageChannel().calculate(bars)
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class MovingAverageChannel(BaseIndicator):
    """Moving Average Channel block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.moving_average_channel",
        version="1.0.0",
        name="Moving Average Channel",
        description="High and low price moving average channel",
        category="trend",
        tags=("trend", "channel", "ma", "moving_average"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, "High price series", required=True),
            InputPort("low", PortType.SERIES, "Low price series", required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Channel (High MA)"),
            OutputPort("lower", PortType.SERIES, "Lower Channel (Low MA)"),
        ),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Upper and Lower Moving Average Channel lines."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = np.asarray(bars.high, dtype=np.float64)
        low = np.asarray(bars.low, dtype=np.float64)
        upper = sma_kernel(high, self.period)
        lower = sma_kernel(low, self.period)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated MAChannel(p=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {
            "upper": IndicatorSeries(upper, name="MAChannel.Upper"),
            "lower": IndicatorSeries(lower, name="MAChannel.Lower"),
        }


__all__ = ["MovingAverageChannel"]
