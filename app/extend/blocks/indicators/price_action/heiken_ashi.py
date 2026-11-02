"""HeikenAshi price_action indicator strategy block.

Description:
    Calculates Heiken Ashi modified smoothed price candlesticks.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative indicator library.
Key Capabilities:
    - FR-indicator-price-action: Heiken Ashi price candlestick calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.price_action.heiken_ashi import (
        HeikenAshi,
    )
    res = HeikenAshi().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons import is_lower
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)


class HeikenAshi(BaseIndicator):
    """Heiken Ashi smoothed candlestick generator with trend condition helpers."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.heiken_ashi",
        name="HeikenAshi",
        category="price_action",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("open", PortType.SERIES, required=True),
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("open", PortType.SERIES),
            OutputPort("high", PortType.SERIES),
            OutputPort("low", PortType.SERIES),
            OutputPort("close", PortType.SERIES),
        ),
        required_market_inputs=("open", "high", "low", "close"),
        parameter_search_space={},
        is_causal=True,
        is_generation_eligible=True,
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
        open_prices = bars.open
        high = bars.high
        low = bars.low
        close = bars.close
        o_arr = to_numpy(open_prices)
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0:
            logger.info("FR-SERVICES-HEIKENASHI-CALCULATE: Empty series supplied")
            raise ValueError("Input series cannot be empty")
        if not len(o_arr) == len(h_arr) == len(l_arr) == n:
            raise ValueError("OHLC series lengths must match")
        ha_open = np.full(n, np.nan, dtype=np.float64)
        ha_high = np.full(n, np.nan, dtype=np.float64)
        ha_low = np.full(n, np.nan, dtype=np.float64)
        ha_close = np.full(n, np.nan, dtype=np.float64)
        ha_close[0] = (o_arr[0] + h_arr[0] + l_arr[0] + c_arr[0]) / 4.0
        ha_open[0] = (o_arr[0] + c_arr[0]) / 2.0
        ha_high[0] = max(h_arr[0], ha_open[0], ha_close[0])
        ha_low[0] = min(l_arr[0], ha_open[0], ha_close[0])
        for i in range(1, n):
            c_val = (o_arr[i] + h_arr[i] + l_arr[i] + c_arr[i]) / 4.0
            o_val = (ha_open[i - 1] + ha_close[i - 1]) / 2.0
            h_val = max(h_arr[i], o_val, c_val)
            l_val = min(l_arr[i], o_val, c_val)
            ha_close[i] = c_val
            ha_open[i] = o_val
            ha_high[i] = h_val
            ha_low[i] = l_val
        logger.info(
            "FR-SERVICES-HEIKENASHI-CALCULATE: Computed HeikenAshi for %d bars", n
        )
        return {
            "open": IndicatorSeries(ha_open, name="HAOpen"),
            "high": IndicatorSeries(ha_high, name="HAHigh"),
            "low": IndicatorSeries(ha_low, name="HALow"),
            "close": IndicatorSeries(ha_close, name="HAClose"),
        }

    @classmethod
    def turns_bullish(cls, ha: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Check if candle turned bullish on current bar from bearish on prior bar."""
        curr_bull = is_greater(
            ha["close"], ha["open"], shift1=shift, shift2=shift, round_digits=8
        )
        prev_bear = is_lower(
            ha["close"], ha["open"], shift1=shift + 1, shift2=shift + 1, round_digits=8
        )
        return curr_bull and prev_bear

    @classmethod
    def turns_bearish(cls, ha: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Check if candle turned bearish on current bar from bullish on prior bar."""
        curr_bear = is_lower(
            ha["close"], ha["open"], shift1=shift, shift2=shift, round_digits=8
        )
        prev_bull = is_greater(
            ha["close"], ha["open"], shift1=shift + 1, shift2=shift + 1, round_digits=8
        )
        return curr_bear and prev_bull
