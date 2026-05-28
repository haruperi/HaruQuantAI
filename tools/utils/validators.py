"""Data validation helpers for HaruQuantAI tools."""

from __future__ import annotations

import pandas as pd

REQUIRED_OHLC_COLUMNS = frozenset({"open", "high", "low", "close"})


def prepare_ohlcv_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize and validate OHLCV-style data.

    Args:
        frame: Input DataFrame containing OHLCV market data.

    Returns:
        pd.DataFrame: Copy with lowercase column names and numeric OHLCV fields.

    Raises:
        TypeError: If frame is not a DataFrame.
        ValueError: If frame is empty or missing OHLC columns.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame.")
    if frame.empty:
        raise ValueError("frame must not be empty.")

    result = frame.copy()
    result.columns = [str(column).strip().lower() for column in result.columns]
    missing = REQUIRED_OHLC_COLUMNS.difference(result.columns)
    if missing:
        raise ValueError(f"frame is missing required OHLC columns: {sorted(missing)}")

    for column in sorted(REQUIRED_OHLC_COLUMNS | {"volume", "spread"}):
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")

    return result


__all__ = [
    "REQUIRED_OHLC_COLUMNS",
    "prepare_ohlcv_data",
]
