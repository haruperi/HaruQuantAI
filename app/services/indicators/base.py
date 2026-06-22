"""Base Indicator Class.

All indicators must inherit from this class and implement the calculate method.
"""

from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

class BaseIndicator(ABC):
    """Base class for all technical indicators."""

    @abstractmethod
    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Calculate the indicator and return the DataFrame with the new columns added.

        Args:
            df: Input DataFrame containing financial data (e.g. open, high, low, close, volume).
            **kwargs: Configuration parameters for the calculation.

        Returns:
            pd.DataFrame: The input DataFrame with the computed indicator columns added.
        """
        pass
