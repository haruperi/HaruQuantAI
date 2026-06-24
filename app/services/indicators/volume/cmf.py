"""Chaikin Money Flow (CMF) Indicator."""

from typing import Any

import pandas as pd

from app.services.indicators.base import BaseIndicator


class CMF(BaseIndicator):
    """Chaikin Money Flow (CMF)

    Description:
    Measures the amount of Money Flow Volume over a specific period.

    Sources:
    https://www.investopedia.com/terms/c/chaikinmoneyflow.asp

    Calculation:
    Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
    Money Flow Volume = Money Flow Multiplier * Volume
    CMF = Sum(Money Flow Volume, period) / Sum(Volume, period)

    Args:
    df (pd.DataFrame): DataFrame containing 'high', 'low', 'close', and 'volume' columns.
    period (int): Lookback period for CMF. Default is 20.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'cmf_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 20, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        result_df = df.copy()

        high_low_range = df["high"] - df["low"]
        mf_multiplier = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / high_low_range.replace(0, 1e-10)

        mf_multiplier = mf_multiplier.fillna(0)

        mf_volume = mf_multiplier * df["volume"]

        sum_mf_volume = mf_volume.rolling(window=period).sum()
        sum_volume = df["volume"].rolling(window=period).sum()

        cmf = sum_mf_volume / sum_volume.replace(0, 1e-10)

        result_df[f"cmf_{period}"] = cmf
        return result_df
