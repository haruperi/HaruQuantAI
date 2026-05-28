"""Volume indicator implementations and official AI Tools for HaruQuant.

Classes:
    None.

Functions:
    calculate_accumulation_distribution_frame: Internal ADL implementation.
    accumulation_distribution: Official AI Tool for ADL.

Exported AI Tools:
    accumulation_distribution.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.indicators.standard import ToolSpec, run_indicator_tool
from tools.indicators.validation import ensure_dataframe, require_columns

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "indicators"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def calculate_accumulation_distribution_frame(
    data: Any,
    *,
    output_col: str = "adl",
) -> pd.DataFrame:
    """Calculate Accumulation/Distribution Line and return a new DataFrame."""
    frame = ensure_dataframe(data)
    require_columns(frame, ("high", "low", "close", "volume"))
    price_range = (frame["high"] - frame["low"]).replace(0, pd.NA)
    money_flow_multiplier = (
        ((frame["close"] - frame["low"]) - (frame["high"] - frame["close"]))
        / price_range
    ).fillna(0.0)
    frame[output_col] = (money_flow_multiplier * frame["volume"]).cumsum().astype(float)
    return frame


def accumulation_distribution(
    data: Any,
    output_col: str = "adl",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate Accumulation/Distribution Line as an AI Tool.

    Use this read-only tool when an agent needs a deterministic volume-flow
    feature for confirmation, divergence checks, or signal preparation.
    """
    return run_indicator_tool(
        ToolSpec(tool_name="accumulation_distribution"),
        lambda: calculate_accumulation_distribution_frame(data, output_col=output_col),
        request_id=request_id,
    )
