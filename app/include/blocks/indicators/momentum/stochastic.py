"""Stochastic indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-STOCHASTIC: validated batch calculation.
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


class Stochastic(BaseIndicator):
    """Stochastic Oscillator family consolidating %K, %D lines and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.stochastic",
        name="Stochastic",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("k", PortType.SERIES), OutputPort("d", PortType.SERIES)),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "k_period": {"type": "int", "min": 1, "max": 56, "default": 14},
            "d_period": {"type": "int", "min": 1, "max": 12, "default": 3},
            "slowing": {"type": "int", "min": 1, "max": 12, "default": 3},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=18,
    )
    k_period: int = Field(default=14, ge=1)
    d_period: int = Field(default=3, ge=1)
    slowing: int = Field(default=3, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.k_period + self.slowing + self.d_period - 2

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        k_period = self.k_period
        d_period = self.d_period
        slowing = self.slowing
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if k_period <= 0:
            logger.warning(
                "FR-SERVICES-STOCH-CALCULATE: Invalid k_period %d, defaulting to 14",
                k_period,
            )
            k_period = 14
        if d_period <= 0:
            d_period = 3
        if slowing <= 0:
            slowing = 3
        raw_k = np.full(n, np.nan, dtype=np.float64)
        for i in range(k_period - 1, n):
            h_win = high_arr[i - k_period + 1 : i + 1]
            l_win = low_arr[i - k_period + 1 : i + 1]
            hh = float(np.max(h_win))
            ll = float(np.min(l_win))
            diff = hh - ll
            if diff != 0.0:
                raw_k[i] = (close_arr[i] - ll) / diff * 100.0
            else:
                raw_k[i] = 50.0
        valid_k_idx = np.where(~np.isnan(raw_k))[0]
        slow_k = np.full(n, np.nan, dtype=np.float64)
        if len(valid_k_idx) >= slowing:
            first_idx = valid_k_idx[0]
            valid_slice = raw_k[first_idx:]
            slow_k[first_idx:] = sma_kernel(valid_slice, slowing)
        valid_d_idx = np.where(~np.isnan(slow_k))[0]
        slow_d = np.full(n, np.nan, dtype=np.float64)
        if len(valid_d_idx) >= d_period:
            first_idx = valid_d_idx[0]
            valid_slice = slow_k[first_idx:]
            slow_d[first_idx:] = sma_kernel(valid_slice, d_period)
        logger.info(
            "FR-SERVICES-STOCH-CALCULATE: Computed Stoch(%d,%d,%d) for %d bars",
            k_period,
            d_period,
            slowing,
            n,
        )
        return {
            "k": IndicatorSeries(slow_k, name="Stoch.K"),
            "d": IndicatorSeries(slow_d, name="Stoch.D"),
        }
