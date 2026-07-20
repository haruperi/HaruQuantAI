"""Exponential moving average indicator.

Classes and functions:
    ema: Function. Provides ema behavior for indicator workflows.
"""

from typing import Any

import pandas as pd
from app.services.indicator.standard import run_indicator_tool
from app.services.indicator.validation import (
    require_columns,
    require_dataframe,
    require_positive_int,
)
from app.services.utils.logger import logger


def _ema_impl(
    data: pd.DataFrame, span: int, price_col: str = "close", adjust: bool = False
) -> pd.DataFrame:
    """Compute the exponential moving average (EMA) with exponential weighting.

    EMA smooths price data using exponentially decaying weights so recent values
    influence the average more than older ones. Compared to SMA, EMA reacts
    faster to price changes, making it popular for crossover systems and dynamic
    support/resistance references.

    Calculation steps:
        1. Apply EWM mean with the specified span.
        2. Adjust for bias if requested.

    Args:
        data: DataFrame containing the necessary market data.
        span: Lookback span for the exponential weighting (alpha = 2 / (span + 1)).
        price_col: Column name to use for calculations (default: "close").
        adjust: Whether to divide by decaying adjustment factor in beginning periods.

    Returns:
        DataFrame with the new EMA column appended.
        Example column name: `ema_{span}`

    Raises:
        ValueError: If parameters are invalid or required columns are missing.
        TypeError: If input types are incorrect.

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
    require_positive_int(span, name="span")
    require_columns(data, (price_col,))

    logger.debug(f"Calculating EMA with span={span} on column '{price_col}'")
    result = data.copy()

    col_name = f"ema_{span}"
    result[col_name] = (
        result[price_col].ewm(span=span, adjust=adjust, min_periods=span).mean()
    )

    logger.success(f"EMA calculation complete: {col_name}")
    return result


def ema(
    data: pd.DataFrame,
    span: int,
    price_col: str = "close",
    adjust: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the ema indicator. Use this tool to compute ema values for market data.

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
        return _ema_impl(frame, span=span, price_col=price_col, adjust=adjust)

    return run_indicator_tool("ema", _operation, request_id=request_id)
