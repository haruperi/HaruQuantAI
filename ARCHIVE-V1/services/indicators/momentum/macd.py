"""Moving Average Convergence Divergence (MACD) Indicator."""

from typing import Any

import pandas as pd
from app.services.indicators.base import BaseIndicator


class MACD(BaseIndicator):
    """Moving Average Convergence Divergence (MACD)

    Description:
    A trend-following momentum indicator that shows the relationship between two moving averages of a security's price.

    Sources:
    https://www.investopedia.com/terms/m/macd.asp

    Calculation:
    MACD Line = 12-period EMA - 26-period EMA
    Signal Line = 9-period EMA of MACD Line
    MACD Histogram = MACD Line - Signal Line

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    fast_period (int): Fast EMA period. Default is 12.
    slow_period (int): Slow EMA period. Default is 26.
    signal_period (int): Signal line EMA period. Default is 9.
    column (str): Column name to run calculation on. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with 'macd_{fast}_{slow}', 'macd_signal_{fast}_{slow}_{signal}', and 'macd_hist_{fast}_{slow}_{signal}' columns added.
    """

    def calculate(
        self,
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close",
        **kwargs: Any,
    ) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if fast_period < 1 or slow_period < 1 or signal_period < 1:
            raise ValueError("All periods must be greater than or equal to 1.")

        result_df = df.copy()

        fast_ema = df[column].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df[column].ewm(span=slow_period, adjust=False).mean()

        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        macd_hist = macd_line - signal_line

        suffix = f"{fast_period}_{slow_period}"
        result_df[f"macd_{suffix}"] = macd_line
        result_df[f"macd_signal_{suffix}_{signal_period}"] = signal_line
        result_df[f"macd_hist_{suffix}_{signal_period}"] = macd_hist

        return result_df
