"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.volatility.adr import AverageDailyRange
    from app.include.blocks.indicators.volatility.amihud import AmihudIlliquidity
    from app.include.blocks.indicators.volatility.atr import ATR
    from app.include.blocks.indicators.volatility.bar_range import BarRange
    from app.include.blocks.indicators.volatility.bollinger_bands import BollingerBands
    from app.include.blocks.indicators.volatility.garman_klass import (
        GarmanKlassVolatility,
    )
    from app.include.blocks.indicators.volatility.keltner_channel import KeltnerChannel
    from app.include.blocks.indicators.volatility.mt_atr import MTATR
    from app.include.blocks.indicators.volatility.mt_keltner_channel import (
        MTKeltnerChannel,
    )
    from app.include.blocks.indicators.volatility.parkinson import ParkinsonVolatility
    from app.include.blocks.indicators.volatility.rogers_satchell import (
        RogersSatchellVolatility,
    )
    from app.include.blocks.indicators.volatility.sr_percent_rank import SRPercentRank
    from app.include.blocks.indicators.volatility.std_dev import StdDev
    from app.include.blocks.indicators.volatility.true_range import TrueRange
    from app.include.blocks.indicators.volatility.ulcer_index import UlcerIndex

_EXPORTS = {
    "ATR": "app.include.blocks.indicators.volatility.atr",
    "AmihudIlliquidity": "app.include.blocks.indicators.volatility.amihud",
    "AverageDailyRange": "app.include.blocks.indicators.volatility.adr",
    "BarRange": "app.include.blocks.indicators.volatility.bar_range",
    "BollingerBands": "app.include.blocks.indicators.volatility.bollinger_bands",
    "GarmanKlassVolatility": "app.include.blocks.indicators.volatility.garman_klass",
    "KeltnerChannel": "app.include.blocks.indicators.volatility.keltner_channel",
    "MTATR": "app.include.blocks.indicators.volatility.mt_atr",
    "MTKeltnerChannel": "app.include.blocks.indicators.volatility.mt_keltner_channel",
    "ParkinsonVolatility": "app.include.blocks.indicators.volatility.parkinson",
    ("RogersSatchellVolatility"): (
        "app.include.blocks.indicators.volatility.rogers_satchell"
    ),
    "SRPercentRank": "app.include.blocks.indicators.volatility.sr_percent_rank",
    "StdDev": "app.include.blocks.indicators.volatility.std_dev",
    "TrueRange": "app.include.blocks.indicators.volatility.true_range",
    "UlcerIndex": "app.include.blocks.indicators.volatility.ulcer_index",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "ATR",
    "MTATR",
    "AmihudIlliquidity",
    "AverageDailyRange",
    "BarRange",
    "BollingerBands",
    "GarmanKlassVolatility",
    "KeltnerChannel",
    "MTKeltnerChannel",
    "ParkinsonVolatility",
    "RogersSatchellVolatility",
    "SRPercentRank",
    "StdDev",
    "TrueRange",
    "UlcerIndex",
]
