"""Trend indicator package exports and lazy loading registry."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.trend.accumulative_swing_index import (
        AccumulativeSwingIndex,
    )
    from app.extend.blocks.indicators.trend.adx import ADX
    from app.extend.blocks.indicators.trend.alma import ArnaudLegouxMovingAverage
    from app.extend.blocks.indicators.trend.aroon import Aroon
    from app.extend.blocks.indicators.trend.dema import DoubleEMA
    from app.extend.blocks.indicators.trend.directional_index import DirectionalIndex
    from app.extend.blocks.indicators.trend.donchian_channel import DonchianChannels
    from app.extend.blocks.indicators.trend.ema import EMA
    from app.extend.blocks.indicators.trend.envelopes import Envelopes
    from app.extend.blocks.indicators.trend.gann_hi_lo import GannHiLo
    from app.extend.blocks.indicators.trend.guppy_mma import GuppyMMA
    from app.extend.blocks.indicators.trend.hull_moving_average import HullMovingAverage
    from app.extend.blocks.indicators.trend.ichimoku import Ichimoku
    from app.extend.blocks.indicators.trend.kama import KAMA
    from app.extend.blocks.indicators.trend.kaufman_efficiency_ratio import (
        KaufmanEfficiencyRatio,
    )
    from app.extend.blocks.indicators.trend.lin_reg import LinReg
    from app.extend.blocks.indicators.trend.lwma import LWMA
    from app.extend.blocks.indicators.trend.mcginley_dynamic import McGinleyDynamic
    from app.extend.blocks.indicators.trend.moving_average_channel import (
        MovingAverageChannel,
    )
    from app.extend.blocks.indicators.trend.moving_average_hamming import (
        MovingAverageHamming,
    )
    from app.extend.blocks.indicators.trend.parabolic_sar import ParabolicSAR
    from app.extend.blocks.indicators.trend.sma import SMA
    from app.extend.blocks.indicators.trend.smma import SMMA
    from app.extend.blocks.indicators.trend.supertrend import SuperTrend
    from app.extend.blocks.indicators.trend.tema import TEMA
    from app.extend.blocks.indicators.trend.trend import Trend
    from app.extend.blocks.indicators.trend.trend_strength_index import (
        TrendStrengthIndex,
    )
    from app.extend.blocks.indicators.trend.vortex import Vortex
    from app.extend.blocks.indicators.trend.williams_alligator import WilliamsAlligator

_EXPORTS: dict[str, str] = {
    "ADX": "app.extend.blocks.indicators.trend.adx",
    ("AccumulativeSwingIndex"): (
        "app.extend.blocks.indicators.trend.accumulative_swing_index"
    ),
    "ArnaudLegouxMovingAverage": "app.extend.blocks.indicators.trend.alma",
    "Aroon": "app.extend.blocks.indicators.trend.aroon",
    "DirectionalIndex": "app.extend.blocks.indicators.trend.directional_index",
    "DonchianChannels": "app.extend.blocks.indicators.trend.donchian_channel",
    "DoubleEMA": "app.extend.blocks.indicators.trend.dema",
    "EMA": "app.extend.blocks.indicators.trend.ema",
    "Envelopes": "app.extend.blocks.indicators.trend.envelopes",
    "GannHiLo": "app.extend.blocks.indicators.trend.gann_hi_lo",
    "GuppyMMA": "app.extend.blocks.indicators.trend.guppy_mma",
    "HullMovingAverage": "app.extend.blocks.indicators.trend.hull_moving_average",
    "Ichimoku": "app.extend.blocks.indicators.trend.ichimoku",
    "KAMA": "app.extend.blocks.indicators.trend.kama",
    ("KaufmanEfficiencyRatio"): (
        "app.extend.blocks.indicators.trend.kaufman_efficiency_ratio"
    ),
    "LWMA": "app.extend.blocks.indicators.trend.lwma",
    "LinReg": "app.extend.blocks.indicators.trend.lin_reg",
    "McGinleyDynamic": "app.extend.blocks.indicators.trend.mcginley_dynamic",
    "MovingAverageChannel": "app.extend.blocks.indicators.trend.moving_average_channel",
    "MovingAverageHamming": "app.extend.blocks.indicators.trend.moving_average_hamming",
    "ParabolicSAR": "app.extend.blocks.indicators.trend.parabolic_sar",
    "SMA": "app.extend.blocks.indicators.trend.sma",
    "SMMA": "app.extend.blocks.indicators.trend.smma",
    "SuperTrend": "app.extend.blocks.indicators.trend.supertrend",
    "TEMA": "app.extend.blocks.indicators.trend.tema",
    "Trend": "app.extend.blocks.indicators.trend.trend",
    "TrendStrengthIndex": "app.extend.blocks.indicators.trend.trend_strength_index",
    "Vortex": "app.extend.blocks.indicators.trend.vortex",
    "WilliamsAlligator": "app.extend.blocks.indicators.trend.williams_alligator",
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
    "AccumulativeSwingIndex",
    "ArnaudLegouxMovingAverage",
    "Aroon",
    "DirectionalIndex",
    "DonchianChannels",
    "DoubleEMA",
    "Envelopes",
    "GannHiLo",
    "GuppyMMA",
    "HullMovingAverage",
    "Ichimoku",
    "KaufmanEfficiencyRatio",
    "LinReg",
    "McGinleyDynamic",
    "MovingAverageChannel",
    "MovingAverageHamming",
    "ParabolicSAR",
    "SuperTrend",
    "Trend",
    "TrendStrengthIndex",
    "Vortex",
    "WilliamsAlligator",
]
