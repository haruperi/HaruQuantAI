"""Relative Strength Index (RSI) streaming calculator.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-RSI: Wilder's RSI with SMA warmup and intra-bar update support.
"""

from __future__ import annotations

from typing import override

from app.include.calculators.average import AverageCalculator, AverageType
from app.include.calculators.base import AbstractCalculator


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

    @override
    def get_value(self) -> float:
        """Return the current computed RSI value."""
        return self.current_value
