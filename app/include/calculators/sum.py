"""Sliding sum streaming calculator.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-SUM: O(1) rolling sum calculator with intra-bar update support.
"""

from __future__ import annotations

from typing import override

from app.include.calculators.base import AbstractCalculator


class SumCalculator(AbstractCalculator):
    """Streaming rolling sum calculator with O(1) window updates."""

    def __init__(self, period: int) -> None:
        """Initialize the rolling sum calculator.

        Args:
            period: Window length in bars.
        """
        super().__init__(period)
        self.last_value: float = 0.0
        self.current_value: float = 0.0

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Update rolling sum by adding incoming value and subtracting expelled."""
        if not is_same_bar:
            self.last_value = self.current_value

        self.current_value = self.last_value - self.old_buffer_value + new_value

    @override
    def get_value(self) -> float:
        """Return the current computed window sum."""
        return self.current_value
