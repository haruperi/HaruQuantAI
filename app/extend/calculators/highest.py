"""Rolling and windowed highest value calculations.

Description:
    Provides incremental rolling highest value calculations, relative bar lag
    tracking, and time-window peak extraction conforming to StrategyQuant's
    HighestCalculator snippet.
Purpose:
    FEAT-CALCULATORS: Stateful streaming and batch window calculators.
Key Capabilities:
    - FR-CALC-HIGHEST: Rolling and windowed highest value calculations.
Python API Usage:
    from app.extend.calculators.highest import HighestCalculator, rolling_highest
    calc = HighestCalculator(period=14)
CLI Usage:
    uv run pytest tests/extend/calculators/test_calculators.py --no-cov
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import UTC, datetime
from typing import Any, override
from zoneinfo import ZoneInfo

import numpy as np

from app.extend.calculators.base import AbstractCalculator

logger = logging.getLogger(__name__)

_LAST_HHMM = 2359
_MINUTES_PER_HOUR = 60


def validate_hhmm(value: int) -> int:
    """Validate an actual clock time rather than accepting an invalid minute."""
    if not 0 <= value <= _LAST_HHMM or value % 100 >= _MINUTES_PER_HOUR:
        raise ValueError("Time must be a valid HHMM value")
    return value


def rolling_highest(values: np.ndarray[Any, Any], period: int) -> np.ndarray[Any, Any]:
    """Linear-time rolling maximum over available history, retaining oldest ties."""
    return rolling_extreme(values, period, highest=True)


def rolling_extreme(
    values: np.ndarray[Any, Any], period: int, *, highest: bool = True
) -> np.ndarray[Any, Any]:
    """Linear-time numeric extrema over available history, retaining oldest ties."""
    logger.debug(
        "FR-CALC-HIGHEST: rolling_extreme length=%d period=%d highest=%s",
        len(values),
        period,
        highest,
    )
    result = np.empty(len(values), dtype=np.float64)
    candidates: deque[int] = deque()
    for i, value in enumerate(values):
        while candidates and candidates[0] <= i - period:
            candidates.popleft()
        while candidates and (
            value > values[candidates[-1]]
            if highest
            else value < values[candidates[-1]]
        ):
            candidates.pop()
        candidates.append(i)
        result[i] = values[candidates[0]]
    return result


def time_window_highest(
    timestamps: np.ndarray[Any, Any],
    values: np.ndarray[Any, Any],
    *,
    time_from: int,
    time_to: int,
    timestamp_unit: str = "seconds",
    timezone: str = "UTC",
) -> np.ndarray[Any, Any]:
    """Replay donor completed-window highest extrema."""
    return time_window_extreme(
        timestamps,
        values,
        time_from=time_from,
        time_to=time_to,
        highest=True,
        timestamp_unit=timestamp_unit,
        timezone=timezone,
    )


def time_window_extreme(  # noqa: C901, PLR0912
    timestamps: np.ndarray[Any, Any],
    values: np.ndarray[Any, Any],
    *,
    time_from: int,
    time_to: int,
    highest: bool = True,
    timestamp_unit: str = "seconds",
    timezone: str = "UTC",
) -> np.ndarray[Any, Any]:
    """Replay donor completed-window extrema, including initial/sentinel behavior."""
    logger.debug(
        "FR-CALC-HIGHEST: time_window_extreme count=%d from=%d to=%d hi=%s",
        len(values),
        time_from,
        time_to,
        highest,
    )
    times = np.asarray(timestamps, dtype=np.int64)
    if len(times) != len(values):
        raise ValueError("Time-window extrema require aligned timestamps")
    if len(times) and (np.any(times <= 0) or np.any(np.diff(times) <= 0)):
        raise ValueError("Timestamps must be positive and strictly increasing")
    if not np.isfinite(values).all():
        raise ValueError("Extrema input must be finite")
    if timestamp_unit == "seconds":
        times = times * 1000
    zone = ZoneInfo(timezone)
    day_ms = 86_400_000
    from_offset = (time_from // 100 * 60 + time_from % 100) * 60_000
    to_offset = (time_to // 100 * 60 + time_to % 100) * 60_000
    sentinel = 0.0 if highest else np.finfo(np.float64).max
    current = last = last_usable = 0.0
    start = end = 0
    result = np.zeros(len(values))
    for i, timestamp in enumerate(times):
        now = int(timestamp)
        day = (
            datetime.fromtimestamp(now / 1000, UTC)
            .astimezone(zone)
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        day_start = int(day.timestamp() * 1000)
        if i == 0:
            start, end = day_start + from_offset, day_start + to_offset
            if end < start:
                end += day_ms
        if now >= end:
            start, end = day_start + from_offset, day_start + to_offset
            last, current = current, sentinel
            if end <= now:
                if time_to < time_from:
                    end += day_ms
                else:
                    start += day_ms
                    end += day_ms
            if start <= now:
                current = float(values[i])
        elif now >= start:
            current = (
                max(current, float(values[i]))
                if highest
                else min(current, float(values[i]))
            )
        else:
            current = sentinel
        usable = last > 0 if highest else last < sentinel
        if usable:
            last_usable = last
        result[i] = last if usable else last_usable
    return result


class HighestCalculator(AbstractCalculator):
    """Streaming rolling maximum value and bar lag tracker (HighestCalculator.java)."""

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

        logger.debug(
            "FR-CALC-HIGHEST: bar=%d new_value=%f highest=%f index=%d",
            self.current_bar,
            new_value,
            self.highest_value,
            self.highest_index,
        )

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


__all__ = [
    "HighestCalculator",
    "rolling_extreme",
    "rolling_highest",
    "time_window_extreme",
    "time_window_highest",
    "validate_hhmm",
]
