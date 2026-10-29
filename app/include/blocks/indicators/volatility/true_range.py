"""TrueRange indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-TRUERANGE: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import (
    is_lower,
)
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.indicators.volatility.atr import ATR
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


class TrueRange(BaseIndicator):
    """True Range indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.true_range",
        name="TrueRange",
        category="volatility",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={},
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.volatility.atr",),
        required_history_lookback=1,
    )

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        res = ATR.true_range(high_arr, low_arr, close_arr)
        logger.info(
            "FR-SERVICES-TRUERANGE-CALCULATE: Computed TrueRange for %d bars", n
        )
        return {"value": IndicatorSeries(res, name="TrueRange")}

    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        lookback: int = 1,
        shift: int = 0,
        level: float | None = None,
    ) -> bool:
        """Evaluate True Range is lower than past value (or level)."""
        if level is not None:
            return is_lower(series, level, shift=shift)
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)
