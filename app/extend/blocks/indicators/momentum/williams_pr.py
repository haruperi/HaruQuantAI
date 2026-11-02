"""WilliamsPR momentum indicator strategy block.

Description:
    Calculates Williams %R dynamic overbought/oversold momentum indicator.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Williams %R calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.williams_pr import WilliamsPR
    res = WilliamsPR().calculate(bars)
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


class WilliamsPR(BaseIndicator):
    """Williams Percent Range indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.williams_pr",
        name="WilliamsPR",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-WILLIAMS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        res = np.full(n, -50.0, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            h_win = high_arr[start : i + 1]
            l_win = low_arr[start : i + 1]
            hh = float(np.max(h_win))
            ll = float(np.min(l_win))
            diff = hh - ll
            if diff != 0.0:
                res[i] = -100.0 * (hh - close_arr[i]) / diff
            else:
                res[i] = -50.0
        logger.info(
            "FR-SERVICES-WILLIAMS-CALCULATE: WPR(period=%d) computed for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"WilliamsPR({period})")}
