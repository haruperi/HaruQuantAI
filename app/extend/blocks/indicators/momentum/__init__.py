"""__init__ momentum indicator strategy block.

Description:
    Momentum indicator package exports and lazy loading registry.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Momentum indicator exports.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.__init__ import __init__
    res = __init__().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.momentum.awesome_oscillator import (
        AwesomeOscillator,
    )
    from app.extend.blocks.indicators.momentum.bears_power import BearsPower
    from app.extend.blocks.indicators.momentum.bulls_power import BullsPower
    from app.extend.blocks.indicators.momentum.cci import CCI
    from app.extend.blocks.indicators.momentum.demarker import DeMarker
    from app.extend.blocks.indicators.momentum.laguerre_rsi import LaguerreRSI
    from app.extend.blocks.indicators.momentum.macd import MACD
    from app.extend.blocks.indicators.momentum.momentum import Momentum
    from app.extend.blocks.indicators.momentum.osma import OSMA
    from app.extend.blocks.indicators.momentum.price_velocity import PriceVelocity
    from app.extend.blocks.indicators.momentum.qqe import QQE
    from app.extend.blocks.indicators.momentum.reflex import Reflex
    from app.extend.blocks.indicators.momentum.roc import ROC
    from app.extend.blocks.indicators.momentum.rsi import RSI
    from app.extend.blocks.indicators.momentum.schaff_trend_cycle import (
        SchaffTrendCycle,
    )
    from app.extend.blocks.indicators.momentum.stochastic import Stochastic
    from app.extend.blocks.indicators.momentum.wave_trend import WaveTrend
    from app.extend.blocks.indicators.momentum.williams_pr import WilliamsPR

_EXPORTS = {
    "AwesomeOscillator": "app.extend.blocks.indicators.momentum.awesome_oscillator",
    "BearsPower": "app.extend.blocks.indicators.momentum.bears_power",
    "BullsPower": "app.extend.blocks.indicators.momentum.bulls_power",
    "CCI": "app.extend.blocks.indicators.momentum.cci",
    "DeMarker": "app.extend.blocks.indicators.momentum.demarker",
    "LaguerreRSI": "app.extend.blocks.indicators.momentum.laguerre_rsi",
    "MACD": "app.extend.blocks.indicators.momentum.macd",
    "Momentum": "app.extend.blocks.indicators.momentum.momentum",
    "OSMA": "app.extend.blocks.indicators.momentum.osma",
    "PriceVelocity": "app.extend.blocks.indicators.momentum.price_velocity",
    "QQE": "app.extend.blocks.indicators.momentum.qqe",
    "ROC": "app.extend.blocks.indicators.momentum.roc",
    "RSI": "app.extend.blocks.indicators.momentum.rsi",
    "Reflex": "app.extend.blocks.indicators.momentum.reflex",
    "SchaffTrendCycle": "app.extend.blocks.indicators.momentum.schaff_trend_cycle",
    "Stochastic": "app.extend.blocks.indicators.momentum.stochastic",
    "WaveTrend": "app.extend.blocks.indicators.momentum.wave_trend",
    "WilliamsPR": "app.extend.blocks.indicators.momentum.williams_pr",
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
