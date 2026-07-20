"""Weighted moving average indicator.

Classes and functions:
    wma: Function. Provides wma behavior for indicator workflows.
"""

from typing import Any

import numpy as np
import pandas as pd
from app.services.indicator.standard import run_indicator_tool
from app.services.indicator.validation import (
    require_columns,
    require_dataframe,
    require_positive_int,
)
from app.services.utils.logger import logger


def _wma_impl(
    data: pd.DataFrame, window: int, price_col: str = "close"
) -> pd.DataFrame:
    """Compute the weighted moving average (WMA) with linearly increasing weights.

    WMA assigns larger weights to more recent prices within the ``window`` while
    still considering all observations in the window. This creates a smoother yet
    responsive trend estimate that sits between SMA (slowest) and EMA (fastest).

    Calculation steps:
        1. Generate linearly increasing weights from 1 to window.
        2. Apply rolling weighted average using dot product.

    Args:
        data: DataFrame containing the necessary market data.
        window: Lookback window size for the average.
        price_col: Column name to use for calculations (default: "close").

    Returns:
        DataFrame with the new WMA column appended.
        Example column name: `wma_{window}`

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

    logger.debug(f"Calculating WMA with window={window} on column '{price_col}'")
    weights = np.arange(1, window + 1)
    weighted_sum = (
        data[price_col]
        .rolling(window=window, min_periods=window)
        .apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    )

    result = data.copy()
    col_name = f"wma_{window}"
    result[col_name] = weighted_sum

    logger.success(f"WMA calculation complete: {col_name}")
    return result


def wma(
    data: pd.DataFrame,
    window: int,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the wma indicator. Use this tool to compute wma values for market data.

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
        return _wma_impl(frame, window=window, price_col=price_col)

    return run_indicator_tool("wma", _operation, request_id=request_id)
