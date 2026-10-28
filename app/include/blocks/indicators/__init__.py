"""Indicator strategy blocks."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from app.include.blocks.indicators.base import BaseIndicator

if TYPE_CHECKING:
    from app.include.blocks.indicators.momentum.macd import MACD
    from app.include.blocks.indicators.momentum.rsi import RSI
    from app.include.blocks.indicators.trend.ema import EMA
    from app.include.blocks.indicators.trend.lwma import LWMA
    from app.include.blocks.indicators.trend.sma import SMA
    from app.include.blocks.indicators.trend.smma import SMMA
    from app.include.blocks.indicators.trend.tema import TEMA
    from app.include.blocks.indicators.volatility.bollinger_bands import BollingerBands

_EXPORTS: dict[str, tuple[str, str]] = {
    "SMA": ("app.include.blocks.indicators.trend.sma", "SMA"),
    "EMA": ("app.include.blocks.indicators.trend.ema", "EMA"),
    "SMMA": ("app.include.blocks.indicators.trend.smma", "SMMA"),
    "LWMA": ("app.include.blocks.indicators.trend.lwma", "LWMA"),
    "TEMA": ("app.include.blocks.indicators.trend.tema", "TEMA"),
    "RSI": ("app.include.blocks.indicators.momentum.rsi", "RSI"),
    "MACD": ("app.include.blocks.indicators.momentum.macd", "MACD"),
    "BollingerBands": (
        "app.include.blocks.indicators.volatility.bollinger_bands",
        "BollingerBands",
    ),
}


def __getattr__(name: str) -> Any:
    """Lazy-load canonical indicators so broken siblings do not poison the package."""
    if name in _EXPORTS:
        mod_name, attr_name = _EXPORTS[name]
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORTS.keys()))


__all__ = [
    "EMA",
    "LWMA",
    "MACD",
    "RSI",
    "SMA",
    "SMMA",
    "TEMA",
    "BaseIndicator",
    "BollingerBands",
]
