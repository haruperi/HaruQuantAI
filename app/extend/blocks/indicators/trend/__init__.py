"""__init__ trend indicator strategy block.

Description:
    Trend indicator package exports and lazy loading registry.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend: Trend indicator exports.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.__init__ import __init__
    res = __init__().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.trend.adx import ADX
    from app.extend.blocks.indicators.trend.aroon import Aroon
    from app.extend.blocks.indicators.trend.directional_index import DirectionalIndex
    from app.extend.blocks.indicators.trend.donchian_channel import DonchianChannels
    from app.extend.blocks.indicators.trend.ema import EMA
    from app.extend.blocks.indicators.trend.gann_hi_lo import GannHiLo
    from app.extend.blocks.indicators.trend.hull_moving_average import (
        HullMovingAverage,
    )
    from app.extend.blocks.indicators.trend.ichimoku import Ichimoku
    from app.extend.blocks.indicators.trend.kama import KAMA
    from app.extend.blocks.indicators.trend.kaufman_efficiency_ratio import (
        KaufmanEfficiencyRatio,
    )
    from app.extend.blocks.indicators.trend.lin_reg import LinReg
    from app.extend.blocks.indicators.trend.lwma import LWMA
    from app.extend.blocks.indicators.trend.parabolic_sar import ParabolicSAR
    from app.extend.blocks.indicators.trend.sma import SMA
    from app.extend.blocks.indicators.trend.smma import SMMA
    from app.extend.blocks.indicators.trend.supertrend import SuperTrend
    from app.extend.blocks.indicators.trend.tema import TEMA
    from app.extend.blocks.indicators.trend.trend import Trend
    from app.extend.blocks.indicators.trend.vortex import Vortex

_EXPORTS = {
    "ADX": "app.extend.blocks.indicators.trend.adx",
    "Aroon": "app.extend.blocks.indicators.trend.aroon",
    "DirectionalIndex": "app.extend.blocks.indicators.trend.directional_index",
    "DonchianChannels": "app.extend.blocks.indicators.trend.donchian_channel",
    "EMA": "app.extend.blocks.indicators.trend.ema",
    "GannHiLo": "app.extend.blocks.indicators.trend.gann_hi_lo",
    "HullMovingAverage": "app.extend.blocks.indicators.trend.hull_moving_average",
    "Ichimoku": "app.extend.blocks.indicators.trend.ichimoku",
    "KAMA": "app.extend.blocks.indicators.trend.kama",
    ("KaufmanEfficiencyRatio"): (
        "app.extend.blocks.indicators.trend.kaufman_efficiency_ratio"
    ),
    "LWMA": "app.extend.blocks.indicators.trend.lwma",
    "LinReg": "app.extend.blocks.indicators.trend.lin_reg",
    "ParabolicSAR": "app.extend.blocks.indicators.trend.parabolic_sar",
    "SMA": "app.extend.blocks.indicators.trend.sma",
    "SMMA": "app.extend.blocks.indicators.trend.smma",
    "SuperTrend": "app.extend.blocks.indicators.trend.supertrend",
    "TEMA": "app.extend.blocks.indicators.trend.tema",
    "Trend": "app.extend.blocks.indicators.trend.trend",
    "Vortex": "app.extend.blocks.indicators.trend.vortex",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "ADX",
    "EMA",
    "KAMA",
    "LWMA",
    "SMA",
    "SMMA",
    "TEMA",
    "Aroon",
    "DirectionalIndex",
    "DonchianChannels",
    "GannHiLo",
    "HullMovingAverage",
    "Ichimoku",
    "KaufmanEfficiencyRatio",
    "LinReg",
    "ParabolicSAR",
    "SuperTrend",
    "Trend",
    "Vortex",
]
