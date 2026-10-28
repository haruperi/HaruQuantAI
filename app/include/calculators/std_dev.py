"""Population standard deviation streaming calculator.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-STDDEV: Rolling standard deviation with intra-bar update support.
"""

from __future__ import annotations

import math
from typing import Any, override

import numpy as np

from app.include.calculators.base import AbstractCalculator

_MAX_WINDOW_ELEMENTS = 1_000_000


def centered_deviation(
    values: np.ndarray[Any, Any],
    centers: np.ndarray[Any, Any],
    period: int,
    *,
    fixed_divisor: bool = False,
) -> np.ndarray[Any, Any]:
    """Batch RMS deviation around supplied centers, with bounded temporary memory.

    BBWidthRatio divides even partial windows by the configured period. Standard
    population deviation divides partial windows by the available bar count.
    """
    result = np.zeros(len(values), dtype=np.float64)
    for i in range(min(period - 1, len(values))):
        difference = values[: i + 1] - centers[i]
        result[i] = np.sqrt(
            np.sum(difference * difference) / (period if fixed_divisor else i + 1)
        )
    if len(values) >= period:
        windows = np.lib.stride_tricks.sliding_window_view(values, period)
        chunk = max(1, _MAX_WINDOW_ELEMENTS // period)
        for start in range(0, len(windows), chunk):
            end = min(len(windows), start + chunk)
            difference = (
                windows[start:end]
                - centers[period - 1 + start : period - 1 + end, None]
            )
            result[period - 1 + start : period - 1 + end] = np.sqrt(
                np.sum(difference * difference, axis=1) / period
            )
    return result


def std_dev_kernel(values: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
    """Batch equivalent of the donor StdDevCalculator, including partial warmup."""
    centers = np.zeros(len(values))
    total = 0.0
    for i, value in enumerate(values.tolist()):
        total = value + total - (float(values[i - period]) if i >= period else 0.0)
        centers[i] = total / min(i + 1, period)
    return centered_deviation(values, centers, period)


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
