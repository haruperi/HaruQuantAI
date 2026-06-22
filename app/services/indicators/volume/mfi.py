"""Money Flow Index (MFI) Indicator."""

from typing import Any
import pandas as pd
import numpy as np
from app.services.indicators.base import BaseIndicator

class MFI(BaseIndicator):
    """Money Flow Index (MFI)

    Description:
    An oscillator that uses both price and volume to measure buying and selling pressure.

    Sources:
    https://www.investopedia.com/terms/m/mfi.asp

    Calculation:
    Typical Price = (High + Low + Close) / 3
    Raw Money Flow = Typical Price * Volume
    Money Flow Ratio = (14-period Positive Money Flow) / (14-period Negative Money Flow)
    MFI = 100 - (100 / (1 + Money Flow Ratio))

    Args:
    df (pd.DataFrame): DataFrame containing 'high', 'low', 'close', and 'volume' columns.
    period (int): Lookback period for MFI. Default is 14.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'mfi_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 14, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")
        
        result_df = df.copy()
        
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        raw_money_flow = typical_price * df["volume"]
        
        price_diff = typical_price.diff()
        
        pos_flow = np.where(price_diff > 0, raw_money_flow, 0)
        neg_flow = np.where(price_diff < 0, raw_money_flow, 0)
        
        pos_mf = pd.Series(pos_flow).rolling(window=period).sum()
        neg_mf = pd.Series(neg_flow).rolling(window=period).sum()
        
        mfr = pos_mf / neg_mf.replace(0, 1e-10)
        mfi = 100 - (100 / (1 + mfr))
        
        result_df[f"mfi_{period}"] = mfi
        return result_df
