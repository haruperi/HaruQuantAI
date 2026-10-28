"""Population standard deviation streaming calculator.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-STDDEV: Rolling standard deviation with intra-bar update support.
"""

from __future__ import annotations

import math
from typing import override

from app.include.calculators.base import AbstractCalculator


class StdDevCalculator(AbstractCalculator):
    """Streaming rolling standard deviation (population formula) calculator."""

    def __init__(self, period: int) -> None:
        """Initialize the standard deviation calculator.

        Args:
            period: Window length in bars.
        """
        super().__init__(period)
        self.current_value: float = 0.0
        self.cur_temp_value: float = 0.0
        self.last_temp_value: float = 0.0

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Compute rolling population standard deviation."""
        if self.current_bar == 0:
            self.current_value = 0.0
            self.last_temp_value = new_value
            return

        if not is_same_bar and self.current_bar > 1:
            self.last_temp_value = self.cur_temp_value

        expired_val = self.old_buffer_value if self.current_bar >= self.period else 0.0
        self.cur_temp_value = new_value + self.last_temp_value - expired_val

        window_size = min(self.current_bar + 1, self.period)
        avg = self.cur_temp_value / window_size

        sum_squared_deviations = 0.0
        for bars_back in range(min(self.current_bar, self.period - 1), -1, -1):
            diff = self.buffer_get(bars_back) - avg
            sum_squared_deviations += diff * diff

        self.current_value = math.sqrt(sum_squared_deviations / window_size)

    @override
    def get_value(self) -> float:
        """Return the current computed standard deviation value."""
        return self.current_value
