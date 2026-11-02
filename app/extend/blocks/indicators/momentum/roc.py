"""ROC momentum indicator strategy block.

Description:
    Calculates Rate of Change (ROC) percentage difference across lookback window.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Rate of change calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.roc import ROC
    res = ROC().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)


class ROC(BaseIndicator):
    """Rate of Change (ROC) indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.roc",
        name="ROC",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 20, "default": 5}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=6,
    )
    period: int = Field(default=5, ge=1)

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
                "FR-SERVICES-ROC-CALCULATE: Invalid period %d, defaulting to 5", period
            )
            period = 5
        res = np.zeros(n, dtype=np.float64)
        for i in range(period, n):
            past = arr[i - period]
            if past != 0.0 and (not np.isnan(past)):
                res[i] = (arr[i] - past) / past * 100.0
            else:
                res[i] = 0.0
        logger.info(
            "FR-SERVICES-ROC-CALCULATE: Computed ROC(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(res, name=f"ROC({period})")}
