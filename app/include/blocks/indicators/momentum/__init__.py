"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.momentum.awesome_oscillator import (
        AwesomeOscillator,
    )
    from app.include.blocks.indicators.momentum.bears_power import BearsPower
    from app.include.blocks.indicators.momentum.bulls_power import BullsPower
    from app.include.blocks.indicators.momentum.cci import CCI
    from app.include.blocks.indicators.momentum.demarker import DeMarker
    from app.include.blocks.indicators.momentum.laguerre_rsi import LaguerreRSI
    from app.include.blocks.indicators.momentum.macd import MACD
    from app.include.blocks.indicators.momentum.momentum import Momentum
    from app.include.blocks.indicators.momentum.osma import OSMA
    from app.include.blocks.indicators.momentum.price_velocity import PriceVelocity
    from app.include.blocks.indicators.momentum.qqe import QQE
    from app.include.blocks.indicators.momentum.reflex import Reflex
    from app.include.blocks.indicators.momentum.roc import ROC
    from app.include.blocks.indicators.momentum.rsi import RSI
    from app.include.blocks.indicators.momentum.schaff_trend_cycle import (
        SchaffTrendCycle,
    )
    from app.include.blocks.indicators.momentum.stochastic import Stochastic
    from app.include.blocks.indicators.momentum.wave_trend import WaveTrend
    from app.include.blocks.indicators.momentum.williams_pr import WilliamsPR

_EXPORTS = {
    "AwesomeOscillator": "app.include.blocks.indicators.momentum.awesome_oscillator",
    "BearsPower": "app.include.blocks.indicators.momentum.bears_power",
    "BullsPower": "app.include.blocks.indicators.momentum.bulls_power",
    "CCI": "app.include.blocks.indicators.momentum.cci",
    "DeMarker": "app.include.blocks.indicators.momentum.demarker",
    "LaguerreRSI": "app.include.blocks.indicators.momentum.laguerre_rsi",
    "MACD": "app.include.blocks.indicators.momentum.macd",
    "Momentum": "app.include.blocks.indicators.momentum.momentum",
    "OSMA": "app.include.blocks.indicators.momentum.osma",
    "PriceVelocity": "app.include.blocks.indicators.momentum.price_velocity",
    "QQE": "app.include.blocks.indicators.momentum.qqe",
    "ROC": "app.include.blocks.indicators.momentum.roc",
    "RSI": "app.include.blocks.indicators.momentum.rsi",
    "Reflex": "app.include.blocks.indicators.momentum.reflex",
    "SchaffTrendCycle": "app.include.blocks.indicators.momentum.schaff_trend_cycle",
    "Stochastic": "app.include.blocks.indicators.momentum.stochastic",
    "WaveTrend": "app.include.blocks.indicators.momentum.wave_trend",
    "WilliamsPR": "app.include.blocks.indicators.momentum.williams_pr",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "CCI",
    "MACD",
    "OSMA",
    "QQE",
    "ROC",
    "RSI",
    "AwesomeOscillator",
    "BearsPower",
    "BullsPower",
    "DeMarker",
    "LaguerreRSI",
    "Momentum",
    "PriceVelocity",
    "Reflex",
    "SchaffTrendCycle",
    "Stochastic",
    "WaveTrend",
    "WilliamsPR",
]
