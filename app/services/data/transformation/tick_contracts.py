"""Tick-derivation closed-set contract vocabulary."""

from typing import Literal

type TickDerivationModel = Literal["real", "trading_bar", "ohlc_m1", "generated"]
type SpreadModel = Literal["native_spread", "fixed_spread", "variable_spread"]

__all__ = ["SpreadModel", "TickDerivationModel"]
