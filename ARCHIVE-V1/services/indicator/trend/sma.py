"""Simple moving average indicator.

Classes and functions:
    sma: Function. Provides sma behavior for indicator workflows.
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


def _sma_impl(
    data: pd.DataFrame, window: int, price_col: str = "close"
) -> pd.DataFrame:
    """Compute the simple moving average (SMA) over a fixed window.

    SMA smooths price data by averaging the last ``window`` observations of
    ``price_col`` with equal weights. It is commonly used to filter noise,
    define trend direction, and generate cross-over signals when paired with
    other moving averages.

    Calculation steps:
        1. Apply rolling mean with the specified window.

    Args:
        data: DataFrame containing the necessary market data.
        window: Lookback window size for the average.
        price_col: Column name to use for calculations (default: "close").

    Returns:
        DataFrame with the new SMA column appended.
        Example column name: `sma_{window}`

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
    require_positive_int(window, name="window")
    require_columns(data, (price_col,))

    logger.debug(f"Calculating SMA with window={window} on column '{price_col}'")
    result = data.copy()

    col_name = f"sma_{window}"
    result[col_name] = (
        result[price_col].rolling(window=window, min_periods=window).mean()
    )

    logger.success(f"SMA calculation complete: {col_name}")
    return result


def sma(
    data: pd.DataFrame,
    window: int,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the sma indicator. Use this tool to compute sma values for market data.

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
        return _sma_impl(frame, window=window, price_col=price_col)

    return run_indicator_tool("sma", _operation, request_id=request_id)
