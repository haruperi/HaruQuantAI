"""Base Indicator Class.

All indicators must inherit from this class and implement the calculate method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from math import floor
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from app.services.contracts.strategies import AccountSnapshot


class BaseIndicator(ABC):
    """Base class for all technical indicators."""

    @abstractmethod
    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.Series | pd.DataFrame:  # noqa: ANN401
        """Calculate the indicator and return the DataFrame with the new columns added.

        Args:
            df: Input DataFrame containing financial data
                (e.g., open, high, low, close, volume).
            **kwargs: Configuration parameters for the calculation.

        Returns:
            pd.DataFrame: The input DataFrame with the computed indicator columns added.
        """


def crossed_above(
    previous_left: float,
    previous_right: float,
    current_left: float,
    current_right: float,
) -> bool:
    """Return a strict upward crossover using two fully completed observations."""
    return previous_left <= previous_right and current_left > current_right


def crossed_below(
    previous_left: float,
    previous_right: float,
    current_left: float,
    current_right: float,
) -> bool:
    """Return a strict downward crossover using two fully completed observations."""
    return previous_left >= previous_right and current_left < current_right


def pips_to_price(
    pips: float, point_size: float, pip_multiplier: float = 10.0
) -> float:
    """Convert MQL-style pips using an explicit point-to-pip multiplier."""
    return pips * point_size * pip_multiplier


def balance_scaled_volume(
    balance: float,
    balance_increase: float,
    volume_increase: float,
    account: AccountSnapshot | None,
) -> float:
    """Translate common MQL balance-scaled lot formulas and clamp to broker bounds."""
    if balance_increase <= 0 or volume_increase <= 0:
        raise ValueError("Balance and volume scaling inputs must be positive.")
    volume = volume_increase * balance / balance_increase
    if account is None:
        return volume
    bounded = min(max(volume, account.volume_min), account.volume_max)
    steps = floor((bounded - account.volume_min) / account.volume_step + 1e-9)
    return round(account.volume_min + steps * account.volume_step, 10)


def arithmetic_average(values: Sequence[float]) -> float:
    """Calculate the arithmetic average of a sequence of values.

    Args:
        values: The sequence of float values.

    Returns:
        float: The arithmetic average.

    Raises:
        ValueError: If the sequence is empty.
    """
    if not values:
        msg = "Cannot average an empty sequence."
        raise ValueError(msg)
    return sum(values) / len(values)


def weighted_average(prices: Sequence[float], quantities: Sequence[float]) -> float:
    """Calculate the weighted average of prices and quantities.

    Args:
        prices: The prices sequence.
        quantities: The aligned quantities sequence.

    Returns:
        float: The weighted average.

    Raises:
        ValueError: If sequences are not aligned, are empty, or quantities
            sum to zero or less.
    """
    if len(prices) != len(quantities) or not prices:
        msg = "Weighted average requires non-empty aligned sequences."
        raise ValueError(msg)
    denominator = sum(quantities)
    if denominator <= 0:
        msg = "Weighted average quantities must sum to a positive value."
        raise ValueError(msg)
    return (
        sum(
            price * quantity for price, quantity in zip(prices, quantities, strict=True)
        )
        / denominator
    )
