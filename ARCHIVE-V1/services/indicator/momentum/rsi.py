"""Relative Strength Index (RSI) indicator.

Classes and functions:
    rsi: Function. Provides rsi behavior for indicator workflows.
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


def _rsi_impl(
    data: pd.DataFrame, period: int = 14, price_col: str = "close"
) -> pd.DataFrame:
    """Compute the Relative Strength Index (RSI) momentum oscillator.

    RSI compares the magnitude of recent gains to recent losses over a fixed lookback
    to gauge the speed and change of price movements. Values oscillate between 0 and
    100, where readings above 70 often signal overbought conditions and readings
    below 30 often signal oversold conditions. This implementation uses an
    exponentially smoothed average of gains and losses over ``period`` bars.

    Calculation steps:
        1. Compute price changes of ``price_col``.
        2. Separate positive (gains) and negative (losses) moves.
        3. Smooth gains and losses with an EWMA using alpha=1/period.
        4. Compute RS = avg_gain / avg_loss and convert to RSI = 100 - 100/(1 + RS).
        5. Fill initial values with a neutral 50 and guard divide-by-zero cases.

    Args:
        data: DataFrame containing OHLCV data.
        period: Lookback period for smoothing (default: 14).
        price_col: Column name for prices to compute RSI on (default: "close").

    Returns:
        DataFrame with added RSI column named ``rsi_{period}``.

    Raises:
        ValueError: If period is not positive or price column missing.

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
    require_columns(data, (price_col,))

    logger.debug(f"Calculating RSI with period={period} on column '{price_col}'")
    close = data[price_col]
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain.divide(avg_loss.replace(0, pd.NA))
    rsi_values = 100 - (100 / (1 + rs))

    rsi_values = rsi_values.fillna(50.0)
    rsi_values = rsi_values.mask(avg_loss == 0, 100.0)
    rsi_values = rsi_values.mask(avg_gain == 0, 0.0)

    result = data.copy()
    col_name = f"rsi_{period}"
    result[col_name] = rsi_values.astype(float)

    logger.success(f"RSI calculation complete: {col_name}")
    return result


def rsi(
    data: pd.DataFrame,
    period: int = 14,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the rsi indicator. Use this tool to compute rsi values for market data.

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
        return _rsi_impl(frame, period=period, price_col=price_col)

    return run_indicator_tool("rsi", _operation, request_id=request_id)
