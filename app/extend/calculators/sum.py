"""Sliding sum streaming calculator.

Description:
    Provides incremental rolling sum calculation with O(1) sliding window
    updates and intra-bar update support matching StrategyQuant SumCalculator.
Purpose:
    FEAT-CALCULATORS: Stateful streaming window calculators and batch kernels.
Key Capabilities:
    - FR-CALC-SUM: O(1) rolling sum calculator with intra-bar update support.
Python API Usage:
    from app.extend.calculators.sum import SumCalculator
    calc = SumCalculator(period=14)
CLI Usage:
    uv run pytest tests/extend/calculators/test_calculators.py --no-cov
"""

from __future__ import annotations

import logging
from typing import override

from app.extend.calculators.base import AbstractCalculator

logger = logging.getLogger(__name__)


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
        logger.debug(
            "FR-CALC-SUM: bar=%d new_value=%f sum=%f",
            self.current_bar,
            new_value,
            self.current_value,
        )

    @override
    def get_value(self) -> float:
        """Return the current computed window sum."""
        return self.current_value


__all__ = ["SumCalculator"]
