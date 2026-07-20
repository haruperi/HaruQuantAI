"""Average True Range (ATR) indicator.

Classes and functions:
    atr: Function. Provides atr behavior for indicator workflows.
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


def _atr_impl(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate the Average True Range (ATR) volatility measure.

    ATR captures the average range of price movement, accounting for gaps,
    by taking the greatest of:
        - current high minus current low
        - absolute high minus previous close
        - absolute low minus previous close
    Those true range values are then exponentially smoothed over ``period``
    bars. Higher ATR indicates higher volatility.

    Calculation steps:
        1. Calculate True Range (TR) as max(high-low, |high-prev_close|, |low-prev_close|).
        2. Smooth TR using EWMA with alpha=1/period.

    Args:
        data: DataFrame containing OHLCV data.
        period: Lookback period (default: 14).

    Returns:
        DataFrame with added ATR column named ``atr_{period}``.

    Raises:
        ValueError: If period is not positive or required columns are missing.

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
    require_positive_int(period, name="period")
    require_columns(data, ("high", "low", "close"))

    logger.debug(f"Calculating ATR with period={period}")
    prev_close = data["close"].shift(1)
    high_low = data["high"] - data["low"]
    high_close = (data["high"] - prev_close).abs()
    low_close = (data["low"] - prev_close).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_values = true_range.ewm(
        alpha=1 / period, adjust=False, min_periods=period
    ).mean()

    result = data.copy()
    col_name = f"atr_{period}"
    result[col_name] = atr_values.astype(float)

    logger.success(f"ATR calculation complete: {col_name}")
    return result


def atr(
    data: pd.DataFrame,
    period: int = 14,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the atr indicator. Use this tool to compute atr values for market data.

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
        return _atr_impl(frame, period=period)

    return run_indicator_tool("atr", _operation, request_id=request_id)
