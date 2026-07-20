"""Shared helpers for simulation backends."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

_PHASE_BITS: dict[str, int] = {
    "open": 1,
    "high": 2,
    "low": 4,
    "close": 8,
}


def signal_to_float_array(data, col_name_map: dict[str, object], names: Iterable[str]):
    """Return the first named signal column as a float array."""
    for name in names:
        col = col_name_map.get(name)
        if col is not None:
            return data[col].fillna(0.0).to_numpy(dtype="float64", copy=False)
    return None


def signal_to_object_array(data, col_name_map: dict[str, object], names: Iterable[str]):
    """Return the first named signal column as an object array."""
    for name in names:
        col = col_name_map.get(name)
        if col is not None:
            return data[col].to_numpy(copy=False)
    return None


def phase_matches(value, phases: Iterable[str]) -> bool:
    """Return whether a phase value contains any requested phase.

    Phase values may be old pipe-delimited strings or numeric bitmasks where
    open=1, high=2, low=4, and close=8.
    """
    target = {str(phase).strip().lower() for phase in phases}
    target_mask = sum(_PHASE_BITS.get(phase, 0) for phase in target)
    if value is None:
        return False
    if isinstance(value, (bool, np.bool_)):
        return bool(value) if "close" in target else False
    if isinstance(value, (int, np.integer)):
        return bool(int(value) & target_mask)
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return False
        return bool(int(value) & target_mask)
    text = str(value).strip()
    if text.isdigit():
        return bool(int(text) & target_mask)
    parts = {
        part.strip().lower()
        for part in text.split("|")
        if part is not None and str(part).strip()
    }
    return bool(parts & target)


def phase_mask(values, phases: Iterable[str]) -> np.ndarray:
    """Return a boolean mask for values matching any target phase."""
    target = {str(phase).strip().lower() for phase in phases}
    target_mask = sum(_PHASE_BITS.get(phase, 0) for phase in target)
    values_array = np.asarray(values)
    if np.issubdtype(values_array.dtype, np.bool_):
        if "close" in target:
            return values_array.astype(bool, copy=False)
        return np.zeros(len(values_array), dtype=bool)
    if np.issubdtype(values_array.dtype, np.integer):
        return (values_array.astype(np.int64, copy=False) & target_mask) != 0
    if np.issubdtype(values_array.dtype, np.floating):
        numeric = np.nan_to_num(values_array, nan=0.0).astype(np.int64, copy=False)
        return (numeric & target_mask) != 0

    mask = np.zeros(len(values), dtype=bool)
    for idx, value in enumerate(values):
        mask[idx] = phase_matches(value, phases)
    return mask
