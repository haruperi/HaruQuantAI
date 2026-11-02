"""Relative Strength Index batch kernel and streaming calculator.

Description:
    Provides streaming RSI calculations with Wilder's smoothing and initial
    SMA warmup matching StrategyQuant RSICalculator donor behavior, alongside
    vectorized NumPy batch kernels.
Purpose:
    FEAT-CALCULATORS: Stateful streaming window calculators and batch kernels.
Key Capabilities:
    - FR-CALC-RSI: Wilder's RSI with SMA warmup and intra-bar update support.
Python API Usage:
    from app.extend.calculators.rsi import RSICalculator, rsi_kernel
    calc = RSICalculator(period=14)
CLI Usage:
    uv run pytest tests/extend/calculators/test_calculators.py --no-cov
"""

from __future__ import annotations

import logging
from typing import Any, override

import numpy as np

from app.extend.calculators.average import AverageCalculator, AverageType
from app.extend.calculators.base import AbstractCalculator

logger = logging.getLogger(__name__)


class RSICalculator(AbstractCalculator):
    """Streaming Relative Strength Index calculator with Wilder's smoothing."""

    def __init__(self, period: int) -> None:
        """Initialize the RSI calculator.

        Args:
            period: Smoothing period for RSI calculations.
        """
        super().__init__(period)

        self.down_average_calculator = AverageCalculator(AverageType.SMA, self.period)
        self.up_average_calculator = AverageCalculator(AverageType.SMA, self.period)

        self.cur_avg_up: float = 0.0
        self.last_avg_up: float = 0.0
        self.cur_avg_down: float = 0.0
        self.last_avg_down: float = 0.0
        self.current_value: float = 0.0

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Update RSI state with incoming price value."""
        if self.current_bar == 0:
            self.down_average_calculator.on_bar_update(0.0, self.current_bar)
            self.up_average_calculator.on_bar_update(0.0, self.current_bar)
            return

        buffer1 = self.buffer_get(1)
        down = max(buffer1 - new_value, 0.0)
        up = max(new_value - buffer1, 0.0)

        if not is_same_bar:
            self.last_avg_down = self.cur_avg_down
            self.last_avg_up = self.cur_avg_up

        if self.current_bar < self.period:
            self.down_average_calculator.on_bar_update(down, self.current_bar)
            self.up_average_calculator.on_bar_update(up, self.current_bar)
            return

        if self.current_bar == self.period:
            self.down_average_calculator.on_bar_update(down, self.current_bar)
            self.up_average_calculator.on_bar_update(up, self.current_bar)

            # Seed first averages from warm-up SMA
            self.cur_avg_down = self.down_average_calculator.get_value()
            self.cur_avg_up = self.up_average_calculator.get_value()
        else:
            # Subsequent updates use Wilder's modified moving average smoothing
            self.cur_avg_down = (
                self.last_avg_down * (self.period - 1) + down
            ) / self.period
            self.cur_avg_up = (self.last_avg_up * (self.period - 1) + up) / self.period

        if self.cur_avg_down != 0.0:
            self.current_value = 100.0 - 100.0 / (
                1.0 + (self.cur_avg_up / self.cur_avg_down)
            )
        elif self.cur_avg_up != 0.0:
            self.current_value = 100.0
        else:
            self.current_value = 50.0

        logger.debug(
            "FR-CALC-RSI: bar=%d new_value=%f rsi=%f",
            self.current_bar,
            new_value,
            self.current_value,
        )

    @override
    def get_value(self) -> float:
        """Return the current computed RSI value."""
        return self.current_value


def rsi_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Relative Strength Index (RSI) using Wilder smoothing.

    Args:
        data: 1D numerical array of price values (e.g. Close).
        period: Smoothing lookback period (>= 1).

    Returns:
        1D float64 array with calculated RSI values in [0, 100], NaN for warmup.
    """
    c = np.asarray(data, dtype=np.float64)
    n = len(c)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n <= period:
        return out

    deltas = np.diff(c)
    ups = np.maximum(deltas, 0.0)
    downs = np.maximum(-deltas, 0.0)

    ups_l = ups.tolist()
    downs_l = downs.tolist()

    cur_avg_up = float(np.mean(ups[:period]))
    cur_avg_down = float(np.mean(downs[:period]))

    if cur_avg_down != 0.0:
        out[period] = 100.0 - 100.0 / (1.0 + cur_avg_up / cur_avg_down)
    elif cur_avg_up != 0.0:
        out[period] = 100.0
    else:
        out[period] = 50.0

    p_minus_1 = float(period - 1)
    f_p = float(period)
    for i in range(period + 1, n):
        up = ups_l[i - 1]
        down = downs_l[i - 1]
        cur_avg_up = (cur_avg_up * p_minus_1 + up) / f_p
        cur_avg_down = (cur_avg_down * p_minus_1 + down) / f_p

        if cur_avg_down != 0.0:
            out[i] = 100.0 - 100.0 / (1.0 + cur_avg_up / cur_avg_down)
        elif cur_avg_up != 0.0:
            out[i] = 100.0
        else:
            out[i] = 50.0

    logger.debug("FR-CALC-RSI: computed rsi_kernel length=%d period=%d", n, period)
    return out


__all__ = ["RSICalculator", "rsi_kernel"]
