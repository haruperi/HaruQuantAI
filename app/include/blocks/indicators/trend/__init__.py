"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.trend.adx import ADX
    from app.include.blocks.indicators.trend.aroon import Aroon
    from app.include.blocks.indicators.trend.directional_index import DirectionalIndex
    from app.include.blocks.indicators.trend.donchian_channel import DonchianChannels
    from app.include.blocks.indicators.trend.ema import EMA
    from app.include.blocks.indicators.trend.gann_hi_lo import GannHiLo
    from app.include.blocks.indicators.trend.hull_moving_average import (
        HullMovingAverage,
    )
    from app.include.blocks.indicators.trend.ichimoku import Ichimoku
    from app.include.blocks.indicators.trend.kama import KAMA
    from app.include.blocks.indicators.trend.kaufman_efficiency_ratio import (
        KaufmanEfficiencyRatio,
    )
    from app.include.blocks.indicators.trend.lin_reg import LinReg
    from app.include.blocks.indicators.trend.lwma import LWMA
    from app.include.blocks.indicators.trend.parabolic_sar import ParabolicSAR
    from app.include.blocks.indicators.trend.sma import SMA
    from app.include.blocks.indicators.trend.smma import SMMA
    from app.include.blocks.indicators.trend.supertrend import SuperTrend
    from app.include.blocks.indicators.trend.tema import TEMA
    from app.include.blocks.indicators.trend.trend import Trend
    from app.include.blocks.indicators.trend.vortex import Vortex

_EXPORTS = {
    "ADX": "app.include.blocks.indicators.trend.adx",
    "Aroon": "app.include.blocks.indicators.trend.aroon",
    "DirectionalIndex": "app.include.blocks.indicators.trend.directional_index",
    "DonchianChannels": "app.include.blocks.indicators.trend.donchian_channel",
    "EMA": "app.include.blocks.indicators.trend.ema",
    "GannHiLo": "app.include.blocks.indicators.trend.gann_hi_lo",
    "HullMovingAverage": "app.include.blocks.indicators.trend.hull_moving_average",
    "Ichimoku": "app.include.blocks.indicators.trend.ichimoku",
    "KAMA": "app.include.blocks.indicators.trend.kama",
    ("KaufmanEfficiencyRatio"): (
        "app.include.blocks.indicators.trend.kaufman_efficiency_ratio"
    ),
    "LWMA": "app.include.blocks.indicators.trend.lwma",
    "LinReg": "app.include.blocks.indicators.trend.lin_reg",
    "ParabolicSAR": "app.include.blocks.indicators.trend.parabolic_sar",
    "SMA": "app.include.blocks.indicators.trend.sma",
    "SMMA": "app.include.blocks.indicators.trend.smma",
    "SuperTrend": "app.include.blocks.indicators.trend.supertrend",
    "TEMA": "app.include.blocks.indicators.trend.tema",
    "Trend": "app.include.blocks.indicators.trend.trend",
    "Vortex": "app.include.blocks.indicators.trend.vortex",
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
