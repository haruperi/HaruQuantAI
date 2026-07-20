"""Bollinger Bands indicator.

Classes and functions:
    bbands: Function. Provides bbands behavior for indicator workflows.
"""

from typing import Any

import pandas as pd

from app.services.indicator.standard import run_indicator_tool
from app.services.indicator.validation import (
    require_columns,
    require_dataframe,
    require_positive_float,
    require_positive_int,
)
from app.services.utils.logger import logger


def _bbands_impl(
    data: pd.DataFrame, period: int = 20, std_dev: float = 2.0, price_col: str = "close"
) -> pd.DataFrame:
    """Compute Bollinger Bands volatility indicator.

    Bollinger Bands consist of a moving average (middle band) and two bands
    positioned at a specified number of standard deviations above and below it.
    They help identify periods of high or low volatility and potential
    overbought/oversold conditions.

    The indicator produces three bands:
        - Upper band = SMA(period) + (std_dev * standard deviation)
        - Middle band = SMA(period)
        - Lower band = SMA(period) - (std_dev * standard deviation)

    Calculation steps:
        1. Calculate SMA of price_col.
        2. Calculate rolling standard deviation.
        3. Derive upper and lower bands using std_dev multiplier.

    Args:
        data: DataFrame containing OHLCV data.
        period: Lookback period for moving average (default: 20).
        std_dev: Number of standard deviations for bands (default: 2.0).
        price_col: Column name for prices (default: "close").

    Returns:
        DataFrame with three added columns:
            - ``bb_upper_{period}_{std_dev}``
            - ``bb_middle_{period}_{std_dev}``
            - ``bb_lower_{period}_{std_dev}``

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
    require_positive_float(std_dev, name="std_dev")
    require_columns(data, (price_col,))

    logger.debug(
        f"Calculating Bollinger Bands with period={period}, std_dev={std_dev} on column '{price_col}'"
    )

    result = data.copy()
    prices = result[price_col]

    # Calculate middle band (SMA)
    middle = prices.rolling(window=period, min_periods=period).mean()

    # Calculate standard deviation
    rolling_std = prices.rolling(window=period, min_periods=period).std()

    # Calculate upper and lower bands
    upper = middle + (std_dev * rolling_std)
    lower = middle - (std_dev * rolling_std)

    # Add columns to result
    suffix = f"{period}_{int(std_dev) if std_dev == int(std_dev) else std_dev}"
    result[f"bb_upper_{suffix}"] = upper.astype(float)
    result[f"bb_middle_{suffix}"] = middle.astype(float)
    result[f"bb_lower_{suffix}"] = lower.astype(float)

    logger.success(f"Bollinger Bands calculation complete: bb_{suffix}")
    return result


def bbands(
    data: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the bbands indicator. Use this tool to compute bbands values for market data.

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
        return _bbands_impl(frame, period=period, std_dev=std_dev, price_col=price_col)

    return run_indicator_tool("bbands", _operation, request_id=request_id)
