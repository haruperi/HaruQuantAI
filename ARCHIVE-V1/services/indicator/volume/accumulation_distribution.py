"""Accumulation/Distribution indicator.

Classes and functions:
    accumulation_distribution: Function. Provides accumulation_distribution behavior for indicator workflows.
"""

from typing import Any

import pandas as pd

from app.services.indicator.standard import run_indicator_tool
from app.services.indicator.validation import require_columns, require_dataframe
from app.services.utils.logger import logger


def _accumulation_distribution_impl(data: pd.DataFrame) -> pd.DataFrame:
    """Compute the Accumulation/Distribution Line (ADL) volume flow indicator.

    ADL tracks whether volume is flowing into (accumulating) or out of
    (distributing) a symbol by weighting volume with the close's position within
    the high-low range of each bar. Positive multipliers signal buying pressure,
    negative multipliers signal selling pressure, and cumulative sums highlight
    confirmation or divergence versus price.

    Calculation steps:
        1. Calculate Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low).
        2. Calculate Money Flow Volume = Multiplier * Volume.
        3. Accumulate Money Flow Volume to get the ADL.

    Args:
        data: DataFrame containing OHLCV data with volume.

    Returns:
        DataFrame with added ``adl`` column.

    Raises:
        ValueError: If required columns are missing or lengths mismatch.

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
    require_dataframe(data)
    require_columns(data, ("high", "low", "close", "volume"))

    logger.debug("Calculating Accumulation/Distribution Line")
    price_range = (data["high"] - data["low"]).replace(0, pd.NA)
    money_flow_multiplier = (
        (data["close"] - data["low"]) - (data["high"] - data["close"])
    ) / price_range
    money_flow_multiplier = money_flow_multiplier.fillna(0)

    money_flow_volume = money_flow_multiplier * data["volume"]
    adl = money_flow_volume.cumsum().astype(float)

    result = data.copy()
    result["adl"] = adl

    logger.success("Accumulation/Distribution calculation complete: adl")
    return result


def accumulation_distribution(
    data: pd.DataFrame,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the accumulation_distribution indicator. Use this tool to compute accumulation_distribution values for market data.

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    from app.services.data.frames import _frame_from_records

    def _operation() -> pd.DataFrame:
        frame = (
            _frame_from_records(records=data)
            if isinstance(data, (list, dict))
            else data
        )
        return _accumulation_distribution_impl(frame)

    return run_indicator_tool(
        "accumulation_distribution",
        _operation,
        request_id=request_id,
    )
