"""Momentum indicator implementations and official AI Tools for HaruQuant.

Classes:
    None.

Functions:
    calculate_rsi_frame: Internal RSI implementation.
    rsi: Official AI Tool for Relative Strength Index.

Exported AI Tools:
    rsi.
"""

from __future__ import annotations

from typing import Any

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


def calculate_rsi_frame(
    data: Any,
    *,
    period: int = 14,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate Relative Strength Index using Wilder-style smoothing.

    Args:
        data: DataFrame or records containing a price column.
        period: RSI lookback period.
        price_col: Source price column.
        output_col: Optional output column.
        warmup_policy: ``nan``, ``fill``, or ``drop``.
        fill_value: Fill value when ``warmup_policy='fill'``.

    Returns:
        DataFrame with an RSI column appended.
    """
    require_positive_int(period, name="period")
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    col = output_col or f"rsi_{period}"

    delta = frame[price_col].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    average_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = average_gain / average_loss.replace(0, pd.NA)
    frame[col] = 100 - (100 / (1 + rs))
    frame.loc[(average_loss == 0) & average_gain.notna(), col] = 100.0
    frame.loc[(average_gain == 0) & average_loss.notna(), col] = 0.0
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def rsi(
    data: Any,
    period: int = 14,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate RSI as an official agent-callable indicator tool.

    Use this tool when an agent needs a deterministic momentum feature for
    overbought/oversold analysis, signal engineering, or research.
    """
    return run_indicator_tool(
        ToolSpec(tool_name="rsi"),
        lambda: calculate_rsi_frame(
            data,
            period=period,
            price_col=price_col,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )
