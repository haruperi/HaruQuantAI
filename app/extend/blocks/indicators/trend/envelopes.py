"""Moving Average Envelopes strategy block.

Description:
    Calculates Moving Average Envelopes defining upper and lower percentage
    bands around a central moving average.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-envelopes: Envelopes band computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.envelopes import Envelopes
    res = Envelopes().calculate(bars)
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
from app.extend.calculators.average import ema_kernel, sma_kernel

logger = get_logger(__name__)

_SCALE_100: float = 100.0


class Envelopes(BaseIndicator):
    """Moving Average Envelopes block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.envelopes",
        version="1.0.0",
        name="Envelopes",
        description="Moving average percentage envelope bands",
        category="trend",
        tags=("trend", "envelopes", "bands", "channel"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Envelope"),
            OutputPort("middle", PortType.SERIES, "Middle MA"),
            OutputPort("lower", PortType.SERIES, "Lower Envelope"),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
            "percent": {"type": "float", "min": 0.1, "max": 20.0, "default": 5.0},
            "exponential": {"type": "bool", "default": False},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=20, ge=1)
    percent: float = Field(default=5.0, gt=0.0)
    exponential: bool = Field(default=False)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Upper, Middle, and Lower Envelopes."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        if self.exponential:
            mid = ema_kernel(close, self.period)
        else:
            mid = sma_kernel(close, self.period)
        factor = self.percent / _SCALE_100
        upper = mid * (1.0 + factor)
        lower = mid * (1.0 - factor)
        logger.debug(
            "FR-SERVICES-INDICATOR-TREND: Calculated Envelopes(p=%d, pct=%.1f) "
            "for %d bars",
            self.period,
            self.percent,
            len(bars),
        )
        return {
            "upper": IndicatorSeries(upper, name="Env.Upper"),
            "middle": IndicatorSeries(mid, name="Env.Middle"),
            "lower": IndicatorSeries(lower, name="Env.Lower"),
        }


__all__ = ["Envelopes"]
