"""Input/output protocols and series containers for strategy blocks."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.include.contracts import DataframeSeries
from app.include.price import BarPrice

IndicatorSeries = DataframeSeries


@dataclass(frozen=True)
class BarData:
    """Lightweight shared calculation context wrapping BarPrice and metadata.

    Ensures zero-copy, read-only array views and strict alignment.

    Attributes:
        prices: Canonical BarPrice container holding OHLCV arrays.
        timestamps: Chronological epoch timestamps (must match price length).
        symbol: Instrument symbol (e.g. 'EURUSD').
        timeframe: Bar timeframe identifier (e.g. 'H1').
        dataset_revision: Identifier or hash of the underlying dataset version.
    """

    prices: BarPrice
    timestamps: np.ndarray[Any, np.dtype[np.int64]] = field(
        default_factory=lambda: np.array([], dtype=np.int64)
    )
    symbol: str = "DEFAULT"
    timeframe: str = "H1"
    dataset_revision: str = "latest"

    def __post_init__(self) -> None:
        """Validate array alignment and enforce immutability on timestamps."""
        ts_arr = np.asarray(self.timestamps, dtype=np.int64)
        if len(ts_arr) > 0 and len(ts_arr) != len(self.prices):
            msg = (
                f"Timestamps length ({len(ts_arr)}) "
                f"does not match bar count ({len(self.prices)})"
            )
            raise ValueError(msg)
        ts_view = ts_arr.view()
        ts_view.flags.writeable = False
        object.__setattr__(self, "timestamps", ts_view)

    @property
    def open(self) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Return 1D read-only view of open prices without copying."""
        return self.prices.open_values

    @property
    def high(self) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Return 1D read-only view of high prices without copying."""
        return self.prices.high_values

    @property
    def low(self) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Return 1D read-only view of low prices without copying."""
        return self.prices.low_values

    @property
    def close(self) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Return 1D read-only view of close prices without copying."""
        return self.prices.close_values

    @property
    def volume(self) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Return 1D read-only view of volume prices without copying."""
        return self.prices.volume_values

    def __len__(self) -> int:
        """Return number of bars in context."""
        return len(self.prices)


def resolve_shift_value(target: Any, shift: int = 0) -> float:
    """Resolve numerical value from scalar, array, series, or callable at shift.

    Shift convention: shift=0 is current/newest bar; shift=k is k bars in past.
    """
    if target is None:
        return float("nan")

    val = target() if callable(target) else target

    if isinstance(val, (int, float, np.integer, np.floating)):
        return float(val) if shift == 0 else float("nan")

    if isinstance(val, DataframeSeries):
        return val.get(shift)

    arr = np.asarray(val, dtype=np.float64)
    n = len(arr)
    if n == 0 or shift < 0 or shift >= n:
        return float("nan")
    return float(arr[n - 1 - shift])


def round_value(val: float, precision: int = 6) -> float:
    """Round a floating-point value to a specified decimal precision."""
    return float("nan") if math.isnan(val) else round(float(val), precision)


__all__ = [
    "BarData",
    "IndicatorSeries",
    "resolve_shift_value",
    "round_value",
]
