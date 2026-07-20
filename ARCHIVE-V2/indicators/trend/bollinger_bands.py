"""Bollinger Bands Indicator."""

from typing import Any

import pandas as pd
from app.services.indicators.base import BaseIndicator


class BollingerBands(BaseIndicator):
    """Bollinger Bands

    Description:
    A volatility envelope consisting of a middle band (SMA) and two outer bands (standard deviations away).

    Sources:
    https://www.investopedia.com/terms/b/bollingerbands.asp

    Calculation:
    Middle Band = SMA(period)
    Upper Band = SMA(period) + (std_dev * Standard Deviation(period))
    Lower Band = SMA(period) - (std_dev * Standard Deviation(period))

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period for SMA and Standard Deviation. Default is 20.
    std_dev (float): Standard deviation multiplier. Default is 2.0.
    column (str): Column name to run calculation on. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new columns 'bb_middle_{period}', 'bb_upper_{period}_{std_dev}', and 'bb_lower_{period}_{std_dev}' added.
    """

    def calculate(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = "close",
        **kwargs: Any,
    ) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        middle = df[column].rolling(window=period).mean()
        std = df[column].rolling(window=period).std()

        bands_df = pd.DataFrame(index=df.index)
        bands_df[f"bb_middle_{period}"] = middle
        bands_df[f"bb_upper_{period}_{std_dev}"] = middle + (std_dev * std)
        bands_df[f"bb_lower_{period}_{std_dev}"] = middle - (std_dev * std)
        return bands_df
