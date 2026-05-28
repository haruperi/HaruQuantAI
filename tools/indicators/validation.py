"""Validation helpers for deterministic indicator calculations.

This file contains internal helpers used by official AI Tools in the indicators
domain. Helpers raise explicit exceptions; public tools convert those exceptions
into the HaruQuant standard tool response schema.

Classes:
    None.

Functions:
    ensure_dataframe: Normalize DataFrame or record input.
    require_columns: Validate required columns.
    require_positive_int: Validate positive integer periods/lookbacks.
    require_positive_float: Validate positive float values.
    maybe_fill_warmup: Apply optional warmup filling.

Exported AI Tools:
    None.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import pandas as pd


def ensure_dataframe(data: Any) -> pd.DataFrame:
    """Normalize supported market-data input into a copied DataFrame.

    Args:
        data: DataFrame, list of row dictionaries, dictionary of columns, or an
            object with a ``df`` DataFrame attribute.

    Returns:
        Copied DataFrame safe for indicator mutation.

    Raises:
        TypeError: If input cannot be converted to a DataFrame.
        ValueError: If the resulting DataFrame is empty.
    """
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        frame = pd.DataFrame(data)
    elif isinstance(data, Mapping):
        frame = pd.DataFrame(data)
    elif isinstance(getattr(data, "df", None), pd.DataFrame):
        frame = data.df.copy()
    else:
        raise TypeError("data must be a pandas DataFrame or DataFrame-like records")

    if frame.empty:
        raise ValueError("data must not be empty")
    return frame


def require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Require all columns to exist in a DataFrame.

    Args:
        frame: DataFrame to inspect.
        columns: Required column names.

    Raises:
        ValueError: If any required column is missing.
    """
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def require_positive_int(value: int, *, name: str) -> None:
    """Require a value to be a positive integer.

    Raises:
        TypeError: If value is not an int.
        ValueError: If value is less than or equal to zero.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def require_positive_float(value: float, *, name: str) -> None:
    """Require a value to be a positive int/float.

    Raises:
        TypeError: If value is not numeric.
        ValueError: If value is less than or equal to zero.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    if float(value) <= 0:
        raise ValueError(f"{name} must be greater than zero")


def require_known_warmup_policy(policy: str) -> None:
    """Validate the warmup policy used by an indicator.

    Supported policies:
        ``nan``: keep warmup as NaN.
        ``fill``: fill warmup with ``fill_value``.
        ``drop``: remove rows with NaN in the output column(s).
    """
    if policy not in {"nan", "fill", "drop"}:
        raise ValueError("warmup_policy must be one of: nan, fill, drop")


def apply_warmup_policy(
    frame: pd.DataFrame,
    columns: str | Iterable[str],
    *,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Apply a deterministic warmup policy to indicator output columns.

    Args:
        frame: DataFrame containing indicator output columns.
        columns: One or more output columns.
        warmup_policy: ``nan``, ``fill``, or ``drop``.
        fill_value: Value used when ``warmup_policy='fill'``.

    Returns:
        DataFrame after applying the requested policy.
    """
    require_known_warmup_policy(warmup_policy)
    column_list = [columns] if isinstance(columns, str) else list(columns)

    if warmup_policy == "nan":
        return frame
    if warmup_policy == "fill":
        if fill_value is None:
            raise ValueError("fill_value is required when warmup_policy='fill'")
        frame[column_list] = frame[column_list].fillna(fill_value)
        return frame
    return frame.dropna(subset=column_list)
