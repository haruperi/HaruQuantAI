"""Rank Correlation Index (RCI) momentum strategy block.

Description:
    Calculates the Rank Correlation Index (RCI) measuring the Spearman rank
    correlation coefficient between price rank and temporal bar index.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-rank-correlation-index: Spearman rank correlation computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.rank_correlation_index import (
        RankCorrelationIndex,
    )
    res = RankCorrelationIndex().calculate(bars)
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

logger = get_logger(__name__)

_SCALE_100: float = 100.0


def _spearman_rank(window: np.ndarray) -> float:
    p = len(window)
    order = np.argsort(-window)
    price_ranks = np.empty(p, dtype=np.float64)
    price_ranks[order] = np.arange(1, p + 1)
    date_ranks = np.arange(p, 0, -1, dtype=np.float64)
    d = date_ranks - price_ranks
    d_sq_sum = np.sum(d**2)
    denom = p * (p**2 - 1)
    if denom == 0:
        return 0.0
    return float((1.0 - (6.0 * d_sq_sum) / denom) * _SCALE_100)


class RankCorrelationIndex(BaseIndicator):
    """Rank Correlation Index (RCI) block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.rank_correlation_index",
        version="1.0.0",
        name="Rank Correlation Index",
        description="Spearman rank correlation oscillator tracking trend purity",
        category="momentum",
        tags=("momentum", "oscillator", "rci", "spearman"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("close", PortType.SERIES, "Close price series", required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES, "Rank Correlation Index"),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 3, "max": 100, "default": 9},
        },
        is_causal=True,
        is_generation_eligible=True,
        is_deterministic=True,
        supports_incremental=False,
    )

    period: int = Field(default=9, ge=2)

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for valid calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Rank Correlation Index values."""
        bars.require_inputs(self.spec.required_market_inputs)
        close = np.asarray(bars.close, dtype=np.float64)
        n = len(close)
        rci = np.full(n, np.nan, dtype=np.float64)
        p = self.period
        if n >= p:
            for i in range(p - 1, n):
                rci[i] = _spearman_rank(close[i - p + 1 : i + 1])
        logger.debug(
            "FR-SERVICES-INDICATOR-MOMENTUM: Calculated RCI(period=%d) for %d bars",
            self.period,
            len(bars),
        )
        return {"value": IndicatorSeries(rci, name="RCI")}


__all__ = ["RankCorrelationIndex"]
