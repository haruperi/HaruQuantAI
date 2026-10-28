"""ROC indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-ROC: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

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

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ROCRising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ROCFalling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCCrossesAboveLevel condition."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCCrossesBelowLevel condition."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_greater(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCAboveLevel condition."""
        return is_greater(series, level, shift=shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCBelowLevel condition."""
        return is_lower(series, level, shift=shift)
