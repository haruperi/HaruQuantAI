"""Input validation helpers for deterministic indicator tools.

Classes and functions:
    require_dataframe: Function. Provides require_dataframe behavior for indicator workflows.
    require_columns: Function. Provides require_columns behavior for indicator workflows.
    require_positive_int: Function. Provides require_positive_int behavior for indicator workflows.
    require_positive_float: Function. Provides require_positive_float behavior for indicator workflows.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def require_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Require a non-empty pandas DataFrame for indicator computation.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Indicator input must be a pandas DataFrame")
    if data.empty:
        raise ValueError("Indicator input must not be empty")
    return data


def require_columns(data: pd.DataFrame, columns: Iterable[str]) -> None:
    """Require columns to be present before computing an indicator.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    required = set(columns)
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def require_positive_int(value: int, *, name: str) -> None:
    """Require positive integer periods/windows for lookback-based indicators.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def require_positive_float(value: float, *, name: str) -> None:
    """Require positive floating parameters such as Bollinger standard deviations.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    if float(value) <= 0:
        raise ValueError(f"{name} must be positive")


__all__ = [
    "require_columns",
    "require_dataframe",
    "require_positive_float",
    "require_positive_int",
]
