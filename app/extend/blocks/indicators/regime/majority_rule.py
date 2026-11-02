"""Majority Rule consensus voting indicator strategy block.

Description:
    Aggregates multi-indicator trend consensus by calculating the majority
    vote among short, medium, and long moving average alignments.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative market regime indicator library.
Key Capabilities:
    - FR-indicator-majority-rule: Consensus voting regime computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.regime.majority_rule import MajorityRule
    res = MajorityRule().calculate(bars)
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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class MajorityRule(BaseIndicator):
    """Majority Rule multi-period voting consensus block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.regime.majority_rule",
        version="1.0.0",
        name="Majority Rule",
        description="Multi-timeframe moving average voting consensus indicator",
        category="regime",
        tags=("regime", "voting", "majority_rule", "consensus"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Majority Vote (-1, 0, +1)"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period1": {"type": "int", "min": 2, "max": 50, "default": 10},
            "period2": {"type": "int", "min": 5, "max": 100, "default": 20},
            "period3": {"type": "int", "min": 10, "max": 200, "default": 50},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period1: int = Field(default=10, ge=1)
    period2: int = Field(default=20, ge=1)
    period3: int = Field(default=50, ge=1)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return max(self.period1, self.period2, self.period3)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Majority Rule consensus direction."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        sma1 = sma_kernel(close, self.period1)
        sma2 = sma_kernel(close, self.period2)
        sma3 = sma_kernel(close, self.period3)
        v1 = np.where(close > sma1, 1.0, np.where(close < sma1, -1.0, 0.0))
        v2 = np.where(close > sma2, 1.0, np.where(close < sma2, -1.0, 0.0))
        v3 = np.where(close > sma3, 1.0, np.where(close < sma3, -1.0, 0.0))
        total = v1 + v2 + v3
        vote = np.where(total > 0.0, 1.0, np.where(total < 0.0, -1.0, 0.0))
        max_p = max(self.period1, self.period2, self.period3)
        vote[: max_p - 1] = np.nan
        logger.debug(
            "FR-SERVICES-INDICATOR-REGIME: Calculated MajorityRule for %d bars",
            len(bars),
        )
        return {"value": IndicatorSeries(vote, name="MajorityRule")}


__all__ = ["MajorityRule"]
