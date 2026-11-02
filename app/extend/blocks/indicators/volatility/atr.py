"""ATR volatility indicator strategy block.

Description:
    Calculates Average True Range (ATR) measuring market volatility.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-volatility: Average true range calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.atr import ATR
    res = ATR().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence
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


class ATR(BaseIndicator):
    """Average True Range indicator family consolidating math and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.atr",
        name="ATR",
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
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=1)

    @classmethod
    def true_range(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
    ) -> np.ndarray:
        """Calculate True Range array across all bars.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.

        Returns:
            1D float64 NumPy array of True Range values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(high_arr)
        if n == 0:
            return np.empty(0, dtype=np.float64)
        tr = np.empty(n, dtype=np.float64)
        tr[0] = high_arr[0] - low_arr[0]
        if n > 1:
            prev_c = close_arr[:-1]
            h_curr = high_arr[1:]
            l_curr = low_arr[1:]
            hl = h_curr - l_curr
            hc = np.abs(h_curr - prev_c)
            lc = np.abs(l_curr - prev_c)
            tr[1:] = np.maximum(hl, np.maximum(hc, lc))
        return tr

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
        if period <= 0:
            logger.warning(
                "FR-SERVICES-ATR-CALCULATE: Invalid period %d, defaulting to 14", period
            )
            period = 14
        tr = self.true_range(high, low, close)
        n = len(tr)
        if n == 0:
            return {"value": IndicatorSeries(np.empty(0, dtype=np.float64), name="ATR")}
        atr_vals = np.empty(n, dtype=np.float64)
        atr_vals[0] = tr[0]
        for i in range(1, n):
            current_bar = i
            window = min(current_bar + 1, period)
            atr_vals[i] = ((window - 1) * atr_vals[i - 1] + tr[i]) / window
        logger.info(
            "FR-SERVICES-ATR-CALCULATE: Computed ATR(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(atr_vals, name="ATR")}
