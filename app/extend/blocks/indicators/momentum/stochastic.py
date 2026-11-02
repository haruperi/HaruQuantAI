"""Stochastic momentum indicator strategy block.

Description:
    Calculates Stochastic Oscillator %K and %D lines relative to high/low range.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Stochastic oscillator calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.stochastic import Stochastic
    res = Stochastic().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.average import (
    ema_kernel,
    lwma_kernel,
    sma_kernel,
    smma_kernel,
)

logger = get_logger(__name__)

MA_SMA: int = 0
MA_EMA: int = 1
MA_SMMA: int = 2
MA_LWMA: int = 3

PRICE_LOW_HIGH: int = 0
PRICE_CLOSE_CLOSE: int = 1


def _apply_ma_kernel(
    values: np.ndarray[Any, Any], period: int, ma_method: int
) -> np.ndarray[Any, Any]:
    """Apply selected moving average kernel to valid numerical slice."""
    if ma_method == MA_SMA:
        return sma_kernel(values, period)
    if ma_method == MA_EMA:
        return ema_kernel(values, period)
    if ma_method == MA_SMMA:
        return smma_kernel(values, period)
    if ma_method == MA_LWMA:
        return lwma_kernel(values, period)
    raise ValueError(f"Unsupported ma_method: {ma_method}")


class Stochastic(BaseIndicator):
    """Stochastic Oscillator family consolidating %K, %D lines and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.stochastic",
        name="Stochastic",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=False),
            InputPort("low", PortType.SERIES, required=False),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("k", PortType.SERIES), OutputPort("d", PortType.SERIES)),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "k_period": {"type": "int", "min": 1, "max": 56, "default": 14},
            "d_period": {"type": "int", "min": 1, "max": 12, "default": 3},
            "slowing": {"type": "int", "min": 1, "max": 12, "default": 3},
            "ma_method": {"type": "int", "min": 0, "max": 3, "default": 0},
            "price_field": {"type": "int", "min": 0, "max": 1, "default": 0},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=18,
    )
    k_period: int = Field(default=14, ge=1)
    d_period: int = Field(default=3, ge=1)
    slowing: int = Field(default=3, ge=1)
    ma_method: int = Field(default=0, ge=0, le=3)
    price_field: int = Field(default=0, ge=0, le=1)

    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Resolve market dependencies conditioned on price_field."""
        if self.price_field == PRICE_CLOSE_CLOSE:
            return ("close",)
        return ("high", "low", "close")

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.k_period + self.slowing + self.d_period - 2

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.required_inputs())
        close = bars.close
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if self.price_field == PRICE_LOW_HIGH:
            high_arr = np.asarray(bars.high, dtype=np.float64)
            low_arr = np.asarray(bars.low, dtype=np.float64)
        else:
            high_arr = close_arr
            low_arr = close_arr

        k_period = self.k_period
        d_period = self.d_period
        slowing = self.slowing
        ma_method = self.ma_method

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
            slow_k[first_idx:] = _apply_ma_kernel(valid_slice, slowing, ma_method)

        valid_d_idx = np.where(~np.isnan(slow_k))[0]
        slow_d = np.full(n, np.nan, dtype=np.float64)
        if len(valid_d_idx) >= d_period:
            first_idx = valid_d_idx[0]
            valid_slice = slow_k[first_idx:]
            slow_d[first_idx:] = _apply_ma_kernel(valid_slice, d_period, ma_method)

        logger.info(
            "FR-SERVICES-STOCH-CALCULATE: Stoch(%d,%d,%d,ma=%d,pf=%d) for %d bars",
            k_period,
            d_period,
            slowing,
            ma_method,
            self.price_field,
            n,
        )
        return {
            "k": IndicatorSeries(slow_k, name="Stoch.K"),
            "d": IndicatorSeries(slow_d, name="Stoch.D"),
        }
