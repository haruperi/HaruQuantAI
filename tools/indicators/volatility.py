"""Volatility indicator implementations and official AI Tools for HaruQuant.

Classes:
    None.

Functions:
    calculate_atr_frame: Internal ATR implementation.
    calculate_adr_frame: Internal ADR implementation.
    calculate_bbands_frame: Internal Bollinger Bands implementation.
    atr: Official AI Tool for Average True Range.
    adr: Official AI Tool for Average Daily Range / average range.
    bbands: Official AI Tool for Bollinger Bands.

Exported AI Tools:
    atr, adr, bbands.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.indicators.standard import ToolSpec, run_indicator_tool
from tools.indicators.validation import (
    apply_warmup_policy,
    ensure_dataframe,
    require_columns,
    require_positive_float,
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


def _true_range(frame: pd.DataFrame) -> pd.Series:
    previous_close = frame["close"].shift(1)
    return pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def calculate_atr_frame(
    data: Any,
    *,
    period: int = 14,
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate Average True Range and return a new DataFrame."""
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, ("high", "low", "close"))
    col = output_col or f"atr_{period}"
    frame[col] = _true_range(frame).rolling(window=period, min_periods=period).mean()
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def calculate_adr_frame(
    data: Any,
    *,
    period: int = 10,
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate Average Daily Range / average high-low range.

    The function is timeframe-agnostic and computes a rolling average of
    ``high - low``. Use daily bars for true ADR.
    """
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, ("high", "low"))
    col = output_col or f"adr_{period}"
    frame[col] = (
        (frame["high"] - frame["low"]).rolling(window=period, min_periods=period).mean()
    )
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def calculate_bbands_frame(
    data: Any,
    *,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = "close",
    middle_col: str | None = None,
    upper_col: str | None = None,
    lower_col: str | None = None,
    width_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate Bollinger Bands and return a new DataFrame."""
    require_positive_int(period, name="period")
    require_positive_float(std_dev, name="std_dev")
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))

    mid = middle_col or f"bbands_middle_{period}"
    upper = upper_col or f"bbands_upper_{period}_{std_dev:g}"
    lower = lower_col or f"bbands_lower_{period}_{std_dev:g}"
    width = width_col or f"bbands_width_{period}_{std_dev:g}"

    rolling = frame[price_col].rolling(window=period, min_periods=period)
    frame[mid] = rolling.mean()
    std = rolling.std(ddof=0)
    frame[upper] = frame[mid] + (std_dev * std)
    frame[lower] = frame[mid] - (std_dev * std)
    frame[width] = frame[upper] - frame[lower]
    return apply_warmup_policy(
        frame,
        (mid, upper, lower, width),
        warmup_policy=warmup_policy,
        fill_value=fill_value,
    )


def atr(
    data: Any,
    period: int = 14,
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate ATR as an official agent-callable indicator tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="atr"),
        lambda: calculate_atr_frame(
            data,
            period=period,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )


def adr(
    data: Any,
    period: int = 10,
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate ADR/average range as an official agent-callable tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="adr"),
        lambda: calculate_adr_frame(
            data,
            period=period,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )


def bbands(
    data: Any,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = "close",
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate Bollinger Bands as an official agent-callable tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="bbands"),
        lambda: calculate_bbands_frame(
            data,
            period=period,
            std_dev=std_dev,
            price_col=price_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )
