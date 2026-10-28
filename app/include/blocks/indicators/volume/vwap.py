"""VWAP indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-VWAP: validated batch calculation.
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
from app.include.calculators.base import to_numpy

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

    @classmethod
    def bar_closes_above(
        cls, close: IndicatorSeries, vwap: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Check if bar close is above VWAP at specified shift."""
        return is_greater(close, vwap, shift=shift)

    @classmethod
    def bar_closes_below(
        cls, close: IndicatorSeries, vwap: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Check if bar close is below VWAP at specified shift."""
        return is_lower(close, vwap, shift=shift)

    @classmethod
    def is_rising(cls, vwap: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VWAP is rising at shift compared to shift+1."""
        return is_rising(vwap, shift=shift)

    @classmethod
    def is_falling(cls, vwap: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VWAP is falling at shift compared to shift+1."""
        return is_falling(vwap, shift=shift)

    @classmethod
    def fast_above_slow(
        cls, fast_vwap: IndicatorSeries, slow_vwap: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Check if fast VWAP is above slow VWAP at shift."""
        return is_greater(fast_vwap, slow_vwap, shift=shift)

    @classmethod
    def fast_below_slow(
        cls, fast_vwap: IndicatorSeries, slow_vwap: IndicatorSeries, shift: int = 0
    ) -> bool:
        """Check if fast VWAP is below slow VWAP at shift."""
        return is_lower(fast_vwap, slow_vwap, shift=shift)

    @classmethod
    def crosses_above(
        cls, series1: IndicatorSeries, series2: IndicatorSeries | float, shift: int = 0
    ) -> bool:
        """Check if series1 crosses above series2."""
        return crosses_above(series1, series2, shift=shift)

    @classmethod
    def crosses_below(
        cls, series1: IndicatorSeries, series2: IndicatorSeries | float, shift: int = 0
    ) -> bool:
        """Check if series1 crosses below series2."""
        return crosses_below(series1, series2, shift=shift)
