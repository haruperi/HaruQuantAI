"""MTATR indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-MTATR: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import (
    is_lower,
)
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.volatility.atr import ATR
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class MTATR(BaseIndicator):
    """MetaTrader Average True Range indicator family (SMA-smoothed True Range)."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.mt_atr",
        name="MTATR",
        category="volatility",
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
        dependencies=("indicator.volatility.atr",),
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
                "FR-SERVICES-MTATR-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14
        tr = ATR.true_range(high_arr, low_arr, close_arr)
        res = sma_kernel(tr, period)
        for i in range(min(period - 1, n)):
            res[i] = float(np.mean(tr[: i + 1]))
        logger.info(
            "FR-SERVICES-MTATR-CALCULATE: Computed MTATR(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(res, name=f"MTATR({period})")}

    @classmethod
    def is_lower(
        cls,
        series: IndicatorSeries,
        lookback: int = 1,
        shift: int = 0,
        level: float | None = None,
    ) -> bool:
        """Evaluate MTATR is lower than past value (or level)."""
        if level is not None:
            return is_lower(series, level, shift=shift)
        return is_lower(series, series, shift1=shift, shift2=shift + lookback)
