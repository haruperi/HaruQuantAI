"""Momentum momentum indicator strategy block.

Description:
    Calculates standard price momentum measuring rate of price acceleration.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Price momentum calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.momentum import Momentum
    res = Momentum().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
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
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


class Momentum(BaseIndicator):
    """Momentum indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.momentum",
        name="Momentum",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=15,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        data = bars.close
        period = self.period
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-MOMENTUM-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        res = np.full(n, 100.0, dtype=np.float64)
        for i in range(1, n):
            past_idx = max(0, i - period)
            denom = arr[past_idx]
            if denom != 0.0 and (not np.isnan(denom)):
                res[i] = arr[i] * 100.0 / denom
            else:
                res[i] = 100.0
        logger.info(
            "FR-SERVICES-MOMENTUM-CALCULATE: Computed Momentum(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"Momentum({period})")}
