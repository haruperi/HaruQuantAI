"""Price formula evaluation for order entry levels and protective boundaries.

Translates high-level trading formula offsets (pips, ATR multiples, percentages,
and points) into normalized absolute order prices aligned with instrument tick steps.
"""

from __future__ import annotations

import math
from typing import Literal

from app.include.blocks.order.types import normalize_price
from app.include.contracts import SymbolInfo


def price_offset_pips(
    base_price: float,
    direction: int,
    pips: float,
    pip_size: float,
    *,
    is_protective: bool = False,
) -> float:
    """Calculate price offset by an exact pip distance.

    For entry orders (is_protective=False):
        Long (1) adds pips; Short (-1) subtracts pips.
    For protective stop-loss orders (is_protective=True):
        Long (1) stop is below entry (-); Short (-1) stop is above entry (+).
    """
    if not math.isfinite(base_price) or base_price <= 0:
        raise ValueError("base_price must be finite and positive")
    if direction not in (1, -1):
        raise ValueError("direction must be 1 (Long) or -1 (Short)")
    if not math.isfinite(pips) or pips < 0:
        raise ValueError("pips must be finite and nonnegative")
    if not math.isfinite(pip_size) or pip_size <= 0:
        raise ValueError("pip_size must be finite and positive")

    distance = pips * pip_size
    sign = -direction if is_protective else direction
    return base_price + sign * distance


def price_offset_atr(
    base_price: float,
    direction: int,
    atr_value: float,
    multiplier: float = 1.0,
    *,
    is_protective: bool = False,
) -> float:
    """Calculate price offset by an ATR volatility multiple."""
    if not math.isfinite(base_price) or base_price <= 0:
        raise ValueError("base_price must be finite and positive")
    if direction not in (1, -1):
        raise ValueError("direction must be 1 (Long) or -1 (Short)")
    if not math.isfinite(atr_value) or atr_value < 0:
        raise ValueError("atr_value must be finite and nonnegative")
    if not math.isfinite(multiplier) or multiplier < 0:
        raise ValueError("multiplier must be finite and nonnegative")

    distance = atr_value * multiplier
    sign = -direction if is_protective else direction
    return base_price + sign * distance


def price_offset_percent(
    base_price: float,
    direction: int,
    percent: float,
    *,
    is_protective: bool = False,
) -> float:
    """Calculate price offset by a percentage of base price."""
    if not math.isfinite(base_price) or base_price <= 0:
        raise ValueError("base_price must be finite and positive")
    if direction not in (1, -1):
        raise ValueError("direction must be 1 (Long) or -1 (Short)")
    if not math.isfinite(percent) or percent < 0:
        raise ValueError("percent must be finite and nonnegative")

    distance = base_price * (percent / 100.0)
    sign = -direction if is_protective else direction
    return base_price + sign * distance


PriceFormulaMode = Literal["pips", "atr", "percent", "absolute"]


def evaluate_price_level(
    mode: PriceFormulaMode,
    base_price: float,
    direction: int,
    *,
    pips: float = 0.0,
    pip_size: float = 0.0001,
    atr_value: float = 0.0,
    multiplier: float = 1.0,
    percent: float = 0.0,
    absolute_price: float = 0.0,
    is_protective: bool = False,
    spec: SymbolInfo | None = None,
) -> float:
    """Evaluate order level and optionally normalize to symbol tick grid."""
    if mode == "absolute":
        raw = absolute_price
    elif mode == "pips":
        raw = price_offset_pips(
            base_price, direction, pips, pip_size, is_protective=is_protective
        )
    elif mode == "atr":
        raw = price_offset_atr(
            base_price,
            direction,
            atr_value,
            multiplier=multiplier,
            is_protective=is_protective,
        )
    elif mode == "percent":
        raw = price_offset_percent(
            base_price, direction, percent, is_protective=is_protective
        )
    else:
        raise ValueError(f"Unknown price formula mode: {mode}")

    if spec is not None:
        return normalize_price(raw, spec)
    return raw
