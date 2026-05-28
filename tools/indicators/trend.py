"""Trend indicator implementations and official AI Tools for HaruQuant.

This file contains deterministic, vectorized moving-average indicators. Public
functions return the HaruQuant standard AI Tool response schema and are intended
to be exported from ``tools.indicators.__init__``.

Classes:
    None.

Functions:
    calculate_sma_frame: Internal SMA implementation.
    calculate_ema_frame: Internal EMA implementation.
    calculate_wma_frame: Internal WMA implementation.
    sma: Official AI Tool for simple moving average.
    ema: Official AI Tool for exponential moving average.
    wma: Official AI Tool for weighted moving average.

Exported AI Tools:
    sma, ema, wma.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from tools.utils.standard import ToolSpec, run_indicator_tool
from tools.utils.validators import (
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


def _spec(tool_name: str) -> ToolSpec:
    return ToolSpec(tool_name=tool_name)


def calculate_sma_frame(
    data: Any,
    *,
    period: int = 20,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate a simple moving average and return a new DataFrame.

    Args:
        data: DataFrame or records containing a price column.
        period: Rolling lookback period.
        price_col: Input price column.
        output_col: Optional output column name.
        warmup_policy: ``nan``, ``fill``, or ``drop``.
        fill_value: Fill value when ``warmup_policy='fill'``.

    Returns:
        DataFrame with the SMA column appended.
    """
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    col = output_col or f"sma_{period}"
    frame[col] = frame[price_col].rolling(window=period, min_periods=period).mean()
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def calculate_ema_frame(
    data: Any,
    *,
    period: int = 20,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate an exponential moving average and return a new DataFrame."""
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    col = output_col or f"ema_{period}"
    frame[col] = (
        frame[price_col].ewm(span=period, adjust=False, min_periods=period).mean()
    )
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def calculate_wma_frame(
    data: Any,
    *,
    period: int = 20,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate a weighted moving average and return a new DataFrame."""
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    col = output_col or f"wma_{period}"
    weights = np.arange(1, period + 1, dtype=float)
    frame[col] = (
        frame[price_col]
        .rolling(window=period, min_periods=period)
        .apply(lambda values: float(np.dot(values, weights) / weights.sum()), raw=True)
    )
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def sma(
    data: Any,
    period: int = 20,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate Simple Moving Average as an agent-callable indicator tool.

    Use this tool when an agent needs a deterministic SMA feature for trend
    analysis, signal preparation, or backtesting input generation.

    Args:
        data: Market data as DataFrame or records.
        period: Rolling lookback period.
        price_col: Source price column.
        output_col: Optional output column name.
        warmup_policy: ``nan`` by default; optionally ``fill`` or ``drop``.
        fill_value: Fill value when using ``warmup_policy='fill'``.
        request_id: Optional trace identifier.

    Returns:
        Standard HaruQuant tool response with serialized DataFrame records.
    """
    return run_indicator_tool(
        _spec("sma"),
        lambda: calculate_sma_frame(
            data,
            period=period,
            price_col=price_col,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )


def ema(
    data: Any,
    period: int = 20,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate Exponential Moving Average as an agent-callable tool."""
    return run_indicator_tool(
        _spec("ema"),
        lambda: calculate_ema_frame(
            data,
            period=period,
            price_col=price_col,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )


def wma(
    data: Any,
    period: int = 20,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate Weighted Moving Average as an agent-callable tool."""
    return run_indicator_tool(
        _spec("wma"),
        lambda: calculate_wma_frame(
            data,
            period=period,
            price_col=price_col,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )
