"""Mutable donor numeric and integer time series.

Description:
    Implements SQX reversed historical indexing, reserve bars, append and
    listener semantics through a shared typed buffer. Avoids offheap Java state.
Purpose:
    FEAT-DATA-SERIES: Recovered DataSeriesBase mutable storage behavior.
Key Capabilities:
    - FR-DATA-SERIES-history: Shift-indexed reads, writes and reserve operations.
    - FR-DATA-SERIES-events: Bar/tick change listener notifications.
Python API Usage:
    DataSeries().add(1.0)
CLI Usage:
    uv run pytest tests/core/data/test_series.py --no-cov
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

_Value = TypeVar("_Value", float, int)
ChangeListener = Callable[[int, int], None]


class SeriesBuffer(Generic[_Value]):
    """Shared primitive for donor double and long series without float casting."""

    def __init__(self, zero: _Value, name: str = "") -> None:
        self._zero = zero
        self._values: list[_Value] = []
        self.name = name
        self.shift = 0
        self.computed_until = -1
        self._bar_listeners: list[ChangeListener] = []
        self._tick_listeners: list[ChangeListener] = []

    def size(self) -> int:
        """Return visible size after reserved shift bars."""
        return len(self._values) - self.shift

    def special_size(self) -> int:
        """Return underlying allocation size including shift bars."""
        return len(self._values)

    def set_shift(self, shift: int) -> None:
        """Reserve an existing prefix, rejecting impossible negative sizes."""
        if shift < 0 or shift > len(self._values):
            raise ValueError("Invalid series shift")
        self.shift = shift

    def get(self, index: int) -> _Value:
        """Read newest-first; donor returns zero when index exceeds size."""
        if index < 0:
            raise ValueError("Index cannot be smaller than zero!")
        if index >= self.size():
            return self._zero
        return self._values[self.size() - index - 1]

    def set(self, index: int, value: _Value, *, notify_bar: bool = True) -> None:
        """Set an existing bar; donor ignores writes beyond visible history."""
        if index < 0:
            raise ValueError("Index cannot be smaller than zero!")
        if index >= self.size():
            return
        self._values[self.size() - index - 1] = self._normalize(value)
        if notify_bar:
            for fn in self._bar_listeners:
                fn(index + self.shift, self.special_size())
        for fn in self._tick_listeners:
            fn(index + self.shift, self.special_size())

    def _normalize(self, value: _Value) -> _Value:
        return value

    def add(self, value: _Value) -> None:
        """Append the newest observation only when shift is zero."""
        if self.shift:
            raise ValueError("Shift must be 0 when calling addValues() !")
        self._values.append(self._normalize(value))
        for fn in self._bar_listeners:
            fn(1, self.size())
        for fn in self._tick_listeners:
            fn(1, self.size())

    def add_values(self, count: int, fill: _Value | None = None) -> None:
        """Append reserved observations, including when a shift exists."""
        if count < 0:
            raise ValueError("Count cannot be negative")
        if count == 0:
            return
        self._values.extend([self._zero if fill is None else fill] * count)
        if self.computed_until > -1:
            self.computed_until += count
        for fn in self._bar_listeners:
            fn(count - 1, self.size())
        for fn in self._tick_listeners:
            fn(count - 1, self.size())

    def on_bar_change(self, callback: ChangeListener) -> None:
        """Register a donor-style bar change callback."""
        self._bar_listeners.append(callback)

    def on_tick_change(self, callback: ChangeListener) -> None:
        """Register a donor-style tick change callback."""
        self._tick_listeners.append(callback)


class DataSeries(SeriesBuffer[float]):
    """Donor floating-point series with near-zero write normalization."""

    def __init__(self, name: str = "") -> None:
        super().__init__(0.0, name)

    def _normalize(self, value: float) -> float:
        value = float(value)
        return 0.0 if -1e-17 < value < 1e-17 else value


class TimeDataSeries(SeriesBuffer[int]):
    """Long timestamp series; retain full 64-bit integer precision."""

    def __init__(self, name: str = "") -> None:
        super().__init__(0, name)

    def _normalize(self, value: int) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("Time series values must be integer timestamps")
        return value
