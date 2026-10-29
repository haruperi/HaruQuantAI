"""ADX indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-ADX: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
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


class ADX(BaseIndicator):
    """ADX family consolidating Main ADX, +DI, -DI lines and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.adx",
        name="ADX",
        category="trend",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("main", PortType.SERIES),
            OutputPort("di_plus", PortType.SERIES),
            OutputPort("di_minus", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.volatility.atr",),
        required_history_lookback=28,
    )
    period: int = Field(default=14, ge=1)

    @classmethod
    def _compute_directional_moves(
        cls, high_arr: np.ndarray, low_arr: np.ndarray, n: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute raw positive and negative directional movement."""
        dm_plus = np.zeros(n, dtype=np.float64)
        dm_minus = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            up_move = high_arr[i] - high_arr[i - 1]
            down_move = low_arr[i - 1] - low_arr[i]
            if up_move > down_move and up_move > 0:
                dm_plus[i] = up_move
            if down_move > up_move and down_move > 0:
                dm_minus[i] = down_move
        return (dm_plus, dm_minus)

    @classmethod
    def _smooth_adx(cls, dx_arr: np.ndarray, period: int, n: int) -> np.ndarray:
        """Compute Wilder smoothed ADX line from raw DX values."""
        main_arr = np.full(n, np.nan, dtype=np.float64)
        valid_dx_idx = np.where(~np.isnan(dx_arr))[0]
        if len(valid_dx_idx) >= period:
            start = valid_dx_idx[0] + period - 1
            main_arr[start] = float(np.mean(dx_arr[valid_dx_idx[0] : start + 1]))
            for i in range(start + 1, n):
                main_arr[i] = (main_arr[i - 1] * (period - 1) + dx_arr[i]) / period
        return main_arr

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 2 * self.period

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
                "FR-SERVICES-ADX-CALCULATE: Invalid period %d, defaulting to 14", period
            )
            period = 14
        main_arr = np.full(n, np.nan, dtype=np.float64)
        di_plus_arr = np.full(n, np.nan, dtype=np.float64)
        di_minus_arr = np.full(n, np.nan, dtype=np.float64)
        if n <= period:
            return {
                "main": IndicatorSeries(main_arr, name="ADX.Main"),
                "di_plus": IndicatorSeries(di_plus_arr, name="ADX.DIPlus"),
                "di_minus": IndicatorSeries(di_minus_arr, name="ADX.DIMinus"),
            }
        tr = ATR.true_range(high_arr, low_arr, close_arr)
        dm_plus, dm_minus = self._compute_directional_moves(high_arr, low_arr, n)
        sum_tr = float(np.sum(tr[1 : period + 1]))
        sum_plus = float(np.sum(dm_plus[1 : period + 1]))
        sum_minus = float(np.sum(dm_minus[1 : period + 1]))
        dx_arr = np.full(n, np.nan, dtype=np.float64)
        for i in range(period, n):
            if i > period:
                sum_tr = sum_tr - sum_tr / period + tr[i]
                sum_plus = sum_plus - sum_plus / period + dm_plus[i]
                sum_minus = sum_minus - sum_minus / period + dm_minus[i]
            if sum_tr != 0.0:
                di_plus_arr[i] = sum_plus / sum_tr * 100.0
                di_minus_arr[i] = sum_minus / sum_tr * 100.0
                di_sum = di_plus_arr[i] + di_minus_arr[i]
                if di_sum != 0.0:
                    dx_arr[i] = abs(di_plus_arr[i] - di_minus_arr[i]) / di_sum * 100.0
        main_arr = self._smooth_adx(dx_arr, period, n)
        logger.info(
            "FR-SERVICES-ADX-CALCULATE: Computed ADX(%d) for %d bars", period, n
        )
        return {
            "main": IndicatorSeries(main_arr, name="ADX.Main"),
            "di_plus": IndicatorSeries(di_plus_arr, name="ADX.DIPlus"),
            "di_minus": IndicatorSeries(di_minus_arr, name="ADX.DIMinus"),
        }
