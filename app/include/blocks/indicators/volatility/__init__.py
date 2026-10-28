"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.volatility.adr import AverageDailyRange
    from app.include.blocks.indicators.volatility.amihud import AmihudIlliquidity
    from app.include.blocks.indicators.volatility.atr import ATR
    from app.include.blocks.indicators.volatility.bar_range import BarRange
    from app.include.blocks.indicators.volatility.bb_range import BBRange
    from app.include.blocks.indicators.volatility.bb_width_ratio import BBWidthRatio
    from app.include.blocks.indicators.volatility.biggest_range import BiggestRange
    from app.include.blocks.indicators.volatility.bollinger_bands import BollingerBands
    from app.include.blocks.indicators.volatility.garman_klass import (
        GarmanKlassVolatility,
    )
    from app.include.blocks.indicators.volatility.highest_in_range import HighestInRange
    from app.include.blocks.indicators.volatility.keltner_channel import KeltnerChannel
    from app.include.blocks.indicators.volatility.lowest_in_range import LowestInRange
    from app.include.blocks.indicators.volatility.mt_atr import MTATR
    from app.include.blocks.indicators.volatility.mt_keltner_channel import (
        MTKeltnerChannel,
    )
    from app.include.blocks.indicators.volatility.parkinson import ParkinsonVolatility
    from app.include.blocks.indicators.volatility.rogers_satchell import (
        RogersSatchellVolatility,
    )
    from app.include.blocks.indicators.volatility.smallest_range import SmallestRange
    from app.include.blocks.indicators.volatility.sr_percent_rank import SRPercentRank
    from app.include.blocks.indicators.volatility.std_dev import StdDev
    from app.include.blocks.indicators.volatility.true_range import TrueRange
    from app.include.blocks.indicators.volatility.ulcer_index import UlcerIndex

_EXPORTS = {
    "BiggestRange": "app.include.blocks.indicators.volatility.biggest_range",
    "SmallestRange": "app.include.blocks.indicators.volatility.smallest_range",
    "HighestInRange": "app.include.blocks.indicators.volatility.highest_in_range",
    "LowestInRange": "app.include.blocks.indicators.volatility.lowest_in_range",
    "BBRange": "app.include.blocks.indicators.volatility.bb_range",
    "BBWidthRatio": "app.include.blocks.indicators.volatility.bb_width_ratio",
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
    "BBRange",
    "BBWidthRatio",
    "BarRange",
    "BiggestRange",
    "BollingerBands",
    "GarmanKlassVolatility",
    "HighestInRange",
    "KeltnerChannel",
    "LowestInRange",
    "MTKeltnerChannel",
    "ParkinsonVolatility",
    "RogersSatchellVolatility",
    "SRPercentRank",
    "SmallestRange",
    "StdDev",
    "TrueRange",
    "UlcerIndex",
]
