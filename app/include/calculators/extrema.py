"""Rolling extrema streaming calculators (Highest, Lowest).

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-EXTREMA: Fast incremental peak/trough and bar-lag tracking over rolling window.
"""

from __future__ import annotations

from typing import override

from app.include.calculators.base import AbstractCalculator


class HighestCalculator(AbstractCalculator):
    """Streaming rolling maximum value and bar lag tracker."""

    def __init__(self, period: int) -> None:
        """Initialize the rolling highest calculator.

        Args:
            period: Window length in bars.
        """
        super().__init__(period)
        self.highest_index: int = 0
        self.highest_value: float = -float("inf")

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Update highest value and its bar lag index."""
        start_index = (
            self.current_bar if self.current_bar < self.period else (self.period - 1)
        )

        if new_value > self.highest_value:
            self.highest_index = 0
            self.highest_value = new_value
        elif self.highest_index < start_index:
            if not is_same_bar:
                self.highest_index += 1
            elif self.highest_index == 0:
                # Latest value was replaced on the same bar by a lower one
                self._find_highest_in_buffer(start_index)
        else:
            # Trailing extremum expired from the sliding window
            self._find_highest_in_buffer(start_index)

    def _find_highest_in_buffer(self, start_index: int) -> None:
        """Scan buffered values to locate maximum and its relative lag."""
        self.highest_index = 0
        self.highest_value = -float("inf")

        for a in range(start_index, -1, -1):
            val = self.buffer_get(a)
            if val > self.highest_value:
                self.highest_value = val
                self.highest_index = a

    def get_highest_value(self) -> float:
        """Return the highest observed value across the active window."""
        return self.highest_value

    def get_highest_index(self) -> int:
        """Return the bar lag index of the highest value (0 = current bar)."""
        return self.highest_index

    @override
    def get_value(self) -> float:
        """Return the highest observed value across the active window."""
        return self.highest_value


class LowestCalculator(AbstractCalculator):
    """Streaming rolling minimum value and bar lag tracker."""

    def __init__(self, period: int) -> None:
        """Initialize the rolling lowest calculator.

        Args:
            period: Window length in bars.
        """
        super().__init__(period)
        self.lowest_index: int = 0
        self.lowest_value: float = float("inf")

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Update lowest value and its bar lag index."""
        start_index = (
            self.current_bar if self.current_bar < self.period else (self.period - 1)
        )

        if new_value < self.lowest_value:
            self.lowest_index = 0
            self.lowest_value = new_value
        elif self.lowest_index < start_index:
            if not is_same_bar:
                self.lowest_index += 1
            elif self.lowest_index == 0:
                # Latest value was replaced on the same bar by a higher one
                self._find_lowest_in_buffer(start_index)
        else:
            # Trailing extremum expired from the sliding window
            self._find_lowest_in_buffer(start_index)

    def _find_lowest_in_buffer(self, start_index: int) -> None:
        """Scan buffered values to locate minimum and its relative lag."""
        self.lowest_index = 0
        self.lowest_value = float("inf")

        for a in range(start_index, -1, -1):
            val = self.buffer_get(a)
            if val < self.lowest_value:
                self.lowest_value = val
                self.lowest_index = a

    def get_lowest_value(self) -> float:
        """Return the lowest observed value across the active window."""
        return self.lowest_value

    def get_lowest_index(self) -> int:
        """Return the bar lag index of the lowest value (0 = current bar)."""
        return self.lowest_index

    @override
    def get_value(self) -> float:
        """Return the lowest observed value across the active window."""
        return self.lowest_value
