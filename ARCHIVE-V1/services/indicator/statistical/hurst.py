"""Hurst Exponent indicator.

Classes and functions:
    calculate_hurst: Function. Provides calculate_hurst behavior for indicator workflows.
    hurst: Function. Provides hurst behavior for indicator workflows.
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


def _calculate_hurst_impl(series: np.ndarray) -> float:
    """Calculate the Hurst exponent of a time series using Rescaled Range (R/S) method.

    Hurst Exponent (H) interprets the long-term memory of time series:
    - H < 0.5: Mean-reverting (anti-persistent)
    - H = 0.5: Random walk (Brownian motion)
    - H > 0.5: Trending (persistent)

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
    if len(series) < 50:
        return np.nan

    # We work on log returns to ensure stationarity of increments
    series = np.diff(np.log(series))
    N = len(series)

    lags = np.unique(np.floor(np.geomspace(10, N // 2, num=8)).astype(int))

    rescaled_ranges = []
    for lag in lags:
        # Rescaled range for this lag
        rs_list = []
        for i in range(0, N - lag + 1, lag):
            chunk = series[i : i + lag]
            if len(chunk) < lag:
                break

            # Mean centering
            mean_adj = chunk - np.mean(chunk)
            # Cumulative deviation
            cum_dev = np.cumsum(mean_adj)
            # Range
            r = np.max(cum_dev) - np.min(cum_dev)
            # Standard deviation
            s = np.std(chunk)
            if s > 1e-12:
                rs_list.append(r / s)

        if rs_list:
            rescaled_ranges.append(np.mean(rs_list))
        else:
            lags = lags[lags != lag]  # remove if no data

    if len(rescaled_ranges) < 2:
        return np.nan

    # Fit log(lags) vs log(rescaled_ranges)
    poly = np.polyfit(np.log(lags[: len(rescaled_ranges)]), np.log(rescaled_ranges), 1)
    return poly[0]


def _hurst_impl(
    data: pd.DataFrame,
    period: int = 100,
    price_col: str = "close",
) -> pd.DataFrame:
    """Compute the Rolling Hurst Exponent.

    The Hurst exponent provides a measure of the "memory" of a time series.
    Values near 0.5 indicate a random walk, while values moving towards 1.0
    indicate a trending series and values towards 0 indicate mean-reversion.

    Calculation steps:
        1. Extract the price series.
        2. Apply a rolling window of the specified period.
        3. For each window, calculate the R/S range and fit the Hurst exponent.

    Args:
        data: DataFrame containing the necessary market data.
        period: Window size for calculation (default: 100).
        price_col: Column to use for calculation (default: "close").

    Returns:
        DataFrame with the new Hurst column appended.
        Example column name: `hurst_{period}`

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
    require_positive_int(period, name="period")
    require_columns(data, (price_col,))

    logger.debug(
        f"Calculating Hurst Exponent with period={period} on column '{price_col}'"
    )

    # Rolling apply (this can be slow, but it's the standard way for custom rolling functions)
    def _rolling_hurst(x):
        return _calculate_hurst_impl(x.values)

    result = data.copy()
    col_name = f"hurst_{period}"
    result[col_name] = (
        data[price_col].rolling(window=period).apply(_rolling_hurst, raw=False)
    )

    logger.success(f"Hurst calculation complete: {col_name}")
    return result


def calculate_hurst(
    series: np.ndarray,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the calculate_hurst indicator. Use this tool to compute calculate_hurst values for market data.

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    return run_indicator_tool(
        "calculate_hurst",
        lambda: _calculate_hurst_impl(np.asarray(series, dtype=float)),
        request_id=request_id,
    )


def hurst(
    data: pd.DataFrame,
    period: int = 100,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate the hurst indicator. Use this tool to compute hurst values for market data.

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
        return _hurst_impl(frame, period=period, price_col=price_col)

    return run_indicator_tool("hurst", _operation, request_id=request_id)
