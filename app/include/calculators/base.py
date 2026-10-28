"""Base ring buffer and execution lifecycle for streaming rolling calculators.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-BUFFER: Circular buffer with intra-bar overwrite and bar advance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.host.logging import get_logger

logger = get_logger(__name__)


class CalculatorError(ValueError):
    """Raised when an invalid calculator configuration or input parameter is used."""


class AbstractCalculator(ABC):
    """Abstract base class for streaming rolling-window calculation kernels.

    Maintains a fixed-size circular ring buffer indexed by relative bar lag
    (0 = newest/current bar) and coordinates intra-bar overwrites versus
    bar-advance state transitions.
    """

    DEFAULT_FALLBACK_PERIOD: ClassVar[int] = 2

    def __init__(self, period: int) -> None:
        """Initialize the calculator with a positive rolling period.

        Args:
            period: Window length in bars. If <= 0, defaults to 2 with a log notice.
        """
        if period <= 0:
            logger.debug(
                "Calculator period <= 0 (%d); falling back to default period %d",
                period,
                self.DEFAULT_FALLBACK_PERIOD,
            )
            period = self.DEFAULT_FALLBACK_PERIOD

        self.period: int = period
        self.buffer: list[float] = [0.0] * self.period
        self.buffer_index_offset: int = 0
        self.old_buffer_value: float = 0.0
        self.current_bar: int = 0
        self.buffer_last_bar: int | None = None
        self._initialized: bool = False

    def on_bar_update(self, new_value: float, current_bar: int) -> None:
        """Process an incoming price update for the specified bar index.

        Supports tick-level intra-bar recalculations (when current_bar equals the
        last seen bar index) by rewriting slot 0, and bar-advance transitions
        (when current_bar advances) by pushing trailing values out of the window.

        Args:
            new_value: Floating-point price or series value.
            current_bar: Zero-based bar index.
        """
        if not self._initialized:
            self.buffer = [0.0] * self.period
            self.buffer_index_offset = 0
            self.buffer_last_bar = current_bar
            self._initialized = True

        self.current_bar = current_bar
        is_same_bar = self.buffer_last_bar == current_bar

        if is_same_bar:
            self._buffer_set(0, float(new_value))
        else:
            self.old_buffer_value = self.buffer_get(self.period - 1)
            self._increase_buffer_index_offset()
            self._buffer_set(0, float(new_value))
            self.buffer_last_bar = current_bar

        self._calculate(float(new_value), is_same_bar)

    @abstractmethod
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        """Execute the concrete rolling algorithm calculation step.

        Args:
            new_value: Value submitted for the current bar update.
            is_same_bar: True if evaluating multiple ticks within the same bar.
        """

    @abstractmethod
    def get_value(self) -> float:
        """Return the current computed output value."""

    def buffer_get(self, index: int) -> float:
        """Retrieve a buffered value by relative bar lag.

        Args:
            index: Lag relative to the current bar (0 = current bar, 1 = 1 bar ago).

        Returns:
            The buffered floating-point value at the specified lag.
        """
        real_index = self._compute_real_index(index)
        return self.buffer[real_index]

    def _buffer_set(self, index: int, value: float) -> None:
        """Store a value into the circular buffer at the specified relative lag."""
        real_index = self._compute_real_index(index)
        self.buffer[real_index] = value

    def _compute_real_index(self, index: int) -> int:
        """Map relative lag index to absolute physical buffer index."""
        real_index = self.buffer_index_offset - index
        if real_index < 0:
            real_index += self.period
        return real_index % self.period

    def _increase_buffer_index_offset(self) -> None:
        """Advance the ring buffer head pointer."""
        self.buffer_index_offset += 1
        if self.buffer_index_offset >= self.period:
            self.buffer_index_offset = 0

    def average_buffer_get(self) -> float:
        """Calculate the arithmetic mean of populated values in the buffer."""
        count = min(self.current_bar + 1, self.period)
        if count <= 0:
            return 0.0
        total = sum(self.buffer_get(idx) for idx in range(count))
        return total / count

    def buffer_length(self) -> int:
        """Return the physical length of the circular buffer."""
        return self.period
