"""VWAP volume indicator strategy block.

Description:
    Calculates intraday Volume Weighted Average Price (VWAP) benchmark.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-volume: Volume weighted average price calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.vwap import VWAP
    res = VWAP().calculate(bars)
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
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_PERIOD: int = 10


class VWAP(BaseIndicator):
    """Rolling Volume Weighted Average Price indicator with condition helpers."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.vwap",
        name="VWAP",
        category="volume",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
            InputPort("volume", PortType.SERIES, required=True),
            InputPort("open", PortType.SERIES, required=False),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low", "close", "volume"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 40, "default": 10}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=10,
    )
    period: int = Field(default=DEFAULT_PERIOD, ge=1)

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
        volume = bars.volume
        open_prices = bars.open if bars.has_input("open") else None
        period = self.period
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if period < 1:
            logger.warning(
                "FR-SERVICES-VWAP-CALCULATE: Invalid period %d, defaulting to %d",
                period,
                DEFAULT_PERIOD,
            )
            period = DEFAULT_PERIOD
        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            logger.info(
                "FR-SERVICES-VWAP-CALCULATE: Insufficient bars (%d < %d)", n, period
            )
            return {"value": IndicatorSeries(out, name=f"VWAP({period})")}
        if open_prices is not None:
            o_arr = to_numpy(open_prices)
            price_arr = (o_arr + h_arr + l_arr + c_arr) / 4.0
        else:
            price_arr = (h_arr + l_arr + c_arr) / 3.0
        pv_arr = price_arr * v_arr
        cum_pv = np.cumsum(np.nan_to_num(pv_arr, nan=0.0))
        cum_vol = np.cumsum(np.nan_to_num(v_arr, nan=0.0))
        sum_pv_init = cum_pv[period - 1]
        sum_vol_init = cum_vol[period - 1]
        out[period - 1] = (
            sum_pv_init / sum_vol_init if sum_vol_init > 0 else price_arr[period - 1]
        )
        window_pv = cum_pv[period:] - cum_pv[:-period]
        window_vol = cum_vol[period:] - cum_vol[:-period]
        valid_vol = window_vol > 0
        window_vwap = np.where(
            valid_vol,
            window_pv / np.where(valid_vol, window_vol, 1.0),
            price_arr[period:],
        )
        out[period:] = window_vwap
        logger.info(
            "FR-SERVICES-VWAP-CALCULATE: Computed VWAP(period=%d) for %d bars",
            period,
            n,
        )
        return {"value": IndicatorSeries(out, name=f"VWAP({period})")}
