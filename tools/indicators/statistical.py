"""Statistical indicator implementations and official AI Tools for HaruQuant.

Classes:
    None.

Functions:
    calculate_hurst_value: Internal Hurst exponent value calculation.
    calculate_hurst_frame: Internal rolling Hurst implementation.
    calculate_hurst: Official AI Tool for scalar Hurst calculation.
    hurst: Official AI Tool for rolling Hurst feature creation.

Exported AI Tools:
    calculate_hurst, hurst.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from tools.indicators.standard import ToolSpec, run_indicator_tool
from tools.indicators.validation import (
    apply_warmup_policy,
    ensure_dataframe,
    require_columns,
    require_positive_int,
)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "indicators"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def calculate_hurst_value(series: Any, *, min_length: int = 50) -> float:
    """Calculate a Hurst exponent value using a rescaled range approach.

    Args:
        series: One-dimensional price-like series.
        min_length: Minimum observations required.

    Returns:
        Hurst exponent, or NaN if there is insufficient valid data.
    """
    require_positive_int(min_length, name="min_length")
    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < min_length:
        return float("nan")
    if np.any(values <= 0):
        values = values - np.nanmin(values) + 1e-9

    returns = np.diff(np.log(values))
    n = len(returns)
    if n < 20:
        return float("nan")

    max_lag = max(10, n // 2)
    lags = np.unique(np.floor(np.geomspace(10, max_lag, num=8)).astype(int))
    rs_values: list[float] = []
    valid_lags: list[int] = []

    for lag in lags:
        if lag < 2 or lag > n:
            continue
        chunks = [returns[i : i + lag] for i in range(0, n - lag + 1, lag)]
        chunk_rs: list[float] = []
        for chunk in chunks:
            if len(chunk) < lag:
                continue
            centered = chunk - np.mean(chunk)
            cumulative = np.cumsum(centered)
            r_value = np.max(cumulative) - np.min(cumulative)
            s_value = np.std(chunk)
            if s_value > 1e-12:
                chunk_rs.append(float(r_value / s_value))
        if chunk_rs:
            valid_lags.append(int(lag))
            rs_values.append(float(np.mean(chunk_rs)))

    if len(rs_values) < 2:
        return float("nan")
    slope, _ = np.polyfit(np.log(valid_lags), np.log(rs_values), 1)
    return float(slope)


def calculate_hurst_frame(
    data: Any,
    *,
    period: int = 100,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate rolling Hurst exponent and return a new DataFrame."""
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    col = output_col or f"hurst_{period}"
    frame[col] = (
        frame[price_col]
        .rolling(window=period, min_periods=period)
        .apply(
            lambda values: calculate_hurst_value(
                values, min_length=max(20, period // 2)
            ),
            raw=True,
        )
    )
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def calculate_hurst(
    series: Any,
    min_length: int = 50,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate a single Hurst exponent value as an AI Tool.

    Use this read-only tool when an agent needs to classify a series as more
    mean-reverting, random-walk-like, or trending.
    """
    return run_indicator_tool(
        ToolSpec(tool_name="calculate_hurst"),
        lambda: {"hurst": calculate_hurst_value(series, min_length=min_length)},
        request_id=request_id,
    )


def hurst(
    data: Any,
    period: int = 100,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate rolling Hurst exponent as an official AI Tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="hurst"),
        lambda: calculate_hurst_frame(
            data,
            period=period,
            price_col=price_col,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )
