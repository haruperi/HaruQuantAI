"""__init__ volatility indicator strategy block.

Description:
    Volatility indicator package exports and lazy loading registry.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volatility indicator library.
Key Capabilities:
    - FR-indicator-volatility: Volatility indicator exports.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volatility.__init__ import __init__
    res = __init__().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.volatility.adr import AverageDailyRange
    from app.extend.blocks.indicators.volatility.amihud import AmihudIlliquidity
    from app.extend.blocks.indicators.volatility.atr import ATR
    from app.extend.blocks.indicators.volatility.bar_range import BarRange
    from app.extend.blocks.indicators.volatility.bb_range import BBRange
    from app.extend.blocks.indicators.volatility.bb_width_ratio import BBWidthRatio
    from app.extend.blocks.indicators.volatility.biggest_range import BiggestRange
    from app.extend.blocks.indicators.volatility.bollinger_bands import BollingerBands
    from app.extend.blocks.indicators.volatility.garman_klass import (
        GarmanKlassVolatility,
    )
    from app.extend.blocks.indicators.volatility.highest_in_range import HighestInRange
    from app.extend.blocks.indicators.volatility.keltner_channel import KeltnerChannel
    from app.extend.blocks.indicators.volatility.lowest_in_range import LowestInRange
    from app.extend.blocks.indicators.volatility.mt_atr import MTATR
    from app.extend.blocks.indicators.volatility.mt_keltner_channel import (
        MTKeltnerChannel,
    )
    from app.extend.blocks.indicators.volatility.parkinson import ParkinsonVolatility
    from app.extend.blocks.indicators.volatility.rogers_satchell import (
        RogersSatchellVolatility,
    )
    from app.extend.blocks.indicators.volatility.smallest_range import SmallestRange
    from app.extend.blocks.indicators.volatility.sr_percent_rank import SRPercentRank
    from app.extend.blocks.indicators.volatility.std_dev import StdDev
    from app.extend.blocks.indicators.volatility.true_range import TrueRange
    from app.extend.blocks.indicators.volatility.ulcer_index import UlcerIndex

_EXPORTS = {
    "BiggestRange": "app.extend.blocks.indicators.volatility.biggest_range",
    "SmallestRange": "app.extend.blocks.indicators.volatility.smallest_range",
    "HighestInRange": "app.extend.blocks.indicators.volatility.highest_in_range",
    "LowestInRange": "app.extend.blocks.indicators.volatility.lowest_in_range",
    "BBRange": "app.extend.blocks.indicators.volatility.bb_range",
    "BBWidthRatio": "app.extend.blocks.indicators.volatility.bb_width_ratio",
    "ATR": "app.extend.blocks.indicators.volatility.atr",
    "AmihudIlliquidity": "app.extend.blocks.indicators.volatility.amihud",
    "AverageDailyRange": "app.extend.blocks.indicators.volatility.adr",
    "BarRange": "app.extend.blocks.indicators.volatility.bar_range",
    "BollingerBands": "app.extend.blocks.indicators.volatility.bollinger_bands",
    "GarmanKlassVolatility": "app.extend.blocks.indicators.volatility.garman_klass",
    "KeltnerChannel": "app.extend.blocks.indicators.volatility.keltner_channel",
    "MTATR": "app.extend.blocks.indicators.volatility.mt_atr",
    "MTKeltnerChannel": "app.extend.blocks.indicators.volatility.mt_keltner_channel",
    "ParkinsonVolatility": "app.extend.blocks.indicators.volatility.parkinson",
    ("RogersSatchellVolatility"): (
        "app.extend.blocks.indicators.volatility.rogers_satchell"
    ),
    "SRPercentRank": "app.extend.blocks.indicators.volatility.sr_percent_rank",
    "StdDev": "app.extend.blocks.indicators.volatility.std_dev",
    "TrueRange": "app.extend.blocks.indicators.volatility.true_range",
    "UlcerIndex": "app.extend.blocks.indicators.volatility.ulcer_index",
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
