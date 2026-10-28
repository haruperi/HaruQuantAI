"""Input/output protocols and series containers for strategy blocks."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np

from app.include.blocks.price import BarPrice
from app.include.contracts import DataframeSeries

IndicatorSeries = DataframeSeries
COMPUTED_PRICE_INPUTS = (
    ("close",),
    ("open",),
    ("high",),
    ("low",),
    ("high", "low"),
    ("high", "low", "close"),
    ("high", "low", "close"),
)
_MEDIAN_PRICE = 4
_TYPICAL_PRICE = 5


def computed_price(bars: BarData, selector: int) -> np.ndarray[Any, Any]:
    """Resolve the donor's seven price selectors without fabricating missing feeds."""
    if type(selector) is not int or selector not in range(len(COMPUTED_PRICE_INPUTS)):
        raise ValueError("Computed-from selector must be between 0 and 6")
    fields = COMPUTED_PRICE_INPUTS[selector]
    bars.require_inputs(fields)
    if len(fields) == 1:
        values = getattr(bars, fields[0])
    elif selector == _MEDIAN_PRICE:
        values = (bars.high + bars.low) / 2
    elif selector == _TYPICAL_PRICE:
        values = (bars.high + bars.low + bars.close) / 3
    else:
        values = (bars.high + bars.low + 2 * bars.close) / 4
    return np.asarray(values, dtype=np.float64)


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
    auxiliary: Mapping[str, np.ndarray[Any, Any]] = field(default_factory=dict)
    available_inputs: frozenset[str] | None = None

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
        auxiliary = {}
        for name, values in self.auxiliary.items():
            array = np.asarray(values, dtype=np.float64)
            if array.ndim != 1 or len(array) != len(self.prices):
                raise ValueError(f"Auxiliary input '{name}' must align with bars")
            view = array.view()
            view.flags.writeable = False
            auxiliary[name] = view
        object.__setattr__(self, "auxiliary", MappingProxyType(auxiliary))

    @classmethod
    def from_arrays(cls, **inputs: Any) -> BarData:
        """Build a context from explicitly supplied series; unused OHLCV slots are zero.

        Only supplied inputs are available to indicators. Missing required feeds
        are rejected, so a COT or order-flow feed cannot be fabricated from prices.
        """
        aliases = {"data": "close", "price": "close"}
        arrays = {
            aliases.get(name, name.removesuffix("_prices")): np.asarray(
                getattr(values, "values", values)
            )
            for name, values in inputs.items()
            if values is not None
        }
        count = len(next(iter(arrays.values()))) if arrays else 0
        for name, array in arrays.items():
            if array.ndim != 1 or len(array) != count:
                raise ValueError(
                    f"Input '{name}' must be a one-dimensional aligned series"
                )
        prices = BarPrice(
            **{
                name + "_data": arrays.get(name, np.zeros(count))
                for name in ("open", "high", "low", "close", "volume")
            }
        )
        return cls(
            prices=prices,
            timestamps=arrays.get("timestamps", np.array([], dtype=np.int64)),
            auxiliary={
                name: values
                for name, values in arrays.items()
                if name not in ("open", "high", "low", "close", "volume", "timestamps")
            },
            available_inputs=frozenset(arrays),
        )

    def require_inputs(self, names: tuple[str, ...]) -> None:
        """Reject unavailable market inputs before numerical evaluation."""
        available = (
            self.available_inputs
            if self.available_inputs is not None
            else frozenset(("open", "high", "low", "close", "volume"))
            | self.auxiliary.keys()
        )
        if len(self.timestamps):
            available = available | {"timestamps"}
        missing = set(names) - available
        if missing:
            raise ValueError(f"Missing indicator inputs: {', '.join(sorted(missing))}")

    def has_input(self, name: str) -> bool:
        """Distinguish absent optional feeds from explicitly supplied zero values."""
        if name == "timestamps":
            return bool(len(self.timestamps))
        if self.available_inputs is not None:
            return name in self.available_inputs
        return (
            name in ("open", "high", "low", "close", "volume") or name in self.auxiliary
        )

    def input(self, name: str, *, required: bool = True) -> np.ndarray[Any, Any] | None:
        """Resolve an auxiliary feed without substituting unrelated market data."""
        result = self.auxiliary.get(name)
        if result is None and required:
            raise ValueError(f"Missing indicator input: {name}")
        return result

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

    def open_series(self) -> IndicatorSeries:
        """Return open prices as IndicatorSeries."""
        return self.prices.open_series()

    def high_series(self) -> IndicatorSeries:
        """Return high prices as IndicatorSeries."""
        return self.prices.high_series()

    def low_series(self) -> IndicatorSeries:
        """Return low prices as IndicatorSeries."""
        return self.prices.low_series()

    def close_series(self) -> IndicatorSeries:
        """Return close prices as IndicatorSeries."""
        return self.prices.close_series()

    def volume_series(self) -> IndicatorSeries:
        """Return volume prices as IndicatorSeries."""
        return self.prices.volume_series()

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
    "COMPUTED_PRICE_INPUTS",
    "BarData",
    "IndicatorSeries",
    "computed_price",
    "resolve_shift_value",
    "round_value",
]
