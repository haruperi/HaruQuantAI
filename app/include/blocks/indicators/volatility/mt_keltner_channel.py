"""MTKeltnerChannel indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-MTKELTNERCHANNEL: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.average import sma_kernel

logger = get_logger(__name__)


class MTKeltnerChannel(BaseIndicator):
    """MetaTrader Keltner Channel indicator family (Close-based middle band)."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.mt_keltner_channel",
        name="MTKeltnerChannel",
        category="volatility",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES),
            OutputPort("middle", PortType.SERIES),
            OutputPort("lower", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20},
            "deviation": {
                "type": "float",
                "min": 0.0,
                "max": 6.0,
                "default": 1.5,
                "min_exclusive": True,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=20, ge=1)
    deviation: float = Field(default=1.5, gt=0.0)

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
        deviation = self.deviation
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-MTKELTNER-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20
        bar_range = high_arr - low_arr
        middle = sma_kernel(close_arr, period)
        offset = sma_kernel(bar_range, period) * deviation
        upper = middle + offset
        lower = middle - offset
        logger.info(
            "FR-SERVICES-MTKELTNER-CALCULATE: MTKC(p=%d, d=%.2f) computed for %d bars",
            period,
            deviation,
            n,
        )
        return {
            "upper": IndicatorSeries(upper, name="MTKC.Upper"),
            "middle": IndicatorSeries(middle, name="MTKC.Middle"),
            "lower": IndicatorSeries(lower, name="MTKC.Lower"),
        }
