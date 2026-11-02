"""BearsPower momentum indicator strategy block.

Description:
    Calculates Bears Power measuring sellers' capability to push price
    below EMA smoothing baseline.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Bears power calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.bears_power import BearsPower
    res = BearsPower().calculate(bars)
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
from app.extend.calculators.average import ema_kernel

logger = get_logger(__name__)


class BearsPower(BaseIndicator):
    """Bears Power (Elder-Ray) indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.bears_power",
        name="BearsPower",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("low", "close"),
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
        low = bars.low
        close = bars.close
        period = self.period
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(low_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-BEARS-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        ema = ema_kernel(close_arr, period)
        res = low_arr - ema
        logger.info(
            "FR-SERVICES-BEARS-CALCULATE: Computed BearsPower(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"BearsPower({period})")}
