"""Volume indicator package exports and lazy loading registry."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.volume.accumulation_distribution import (
        AccumulationDistribution,
    )
    from app.extend.blocks.indicators.volume.advance_decline import AdvanceDecline
    from app.extend.blocks.indicators.volume.aggressive_trade_imbalance import (
        AggressiveTradeImbalance,
    )
    from app.extend.blocks.indicators.volume.anchored_vwap import AnchoredVWAP
    from app.extend.blocks.indicators.volume.avg_volume import AvgVolume
    from app.extend.blocks.indicators.volume.chaikin_oscillator import ChaikinOscillator
    from app.extend.blocks.indicators.volume.cmf import CMF
    from app.extend.blocks.indicators.volume.cot import COT
    from app.extend.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )
    from app.extend.blocks.indicators.volume.ease_of_movement import EaseOfMovement
    from app.extend.blocks.indicators.volume.force_index import ForceIndex
    from app.extend.blocks.indicators.volume.klinger_oscillator import KlingerOscillator
    from app.extend.blocks.indicators.volume.mfi import MFI
    from app.extend.blocks.indicators.volume.net_volume import NetVolume
    from app.extend.blocks.indicators.volume.obv import OBV
    from app.extend.blocks.indicators.volume.price_volume_trend import PriceVolumeTrend
    from app.extend.blocks.indicators.volume.tpo_profile import TPOProfile
    from app.extend.blocks.indicators.volume.volume_oscillator import VolumeOscillator
    from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
    from app.extend.blocks.indicators.volume.vwap import VWAP
    from app.extend.blocks.indicators.volume.vwma import VWMA

_EXPORTS: dict[str, str] = {
    ("AccumulationDistribution"): (
        "app.extend.blocks.indicators.volume.accumulation_distribution"
    ),
    "AdvanceDecline": "app.extend.blocks.indicators.volume.advance_decline",
    ("AggressiveTradeImbalance"): (
        "app.extend.blocks.indicators.volume.aggressive_trade_imbalance"
    ),
    "AnchoredVWAP": "app.extend.blocks.indicators.volume.anchored_vwap",
    "AvgVolume": "app.extend.blocks.indicators.volume.avg_volume",
    "CMF": "app.extend.blocks.indicators.volume.cmf",
    "COT": "app.extend.blocks.indicators.volume.cot",
    "ChaikinOscillator": "app.extend.blocks.indicators.volume.chaikin_oscillator",
    ("CumulativeVolumeDelta"): (
        "app.extend.blocks.indicators.volume.cumulative_volume_delta"
    ),
    "EaseOfMovement": "app.extend.blocks.indicators.volume.ease_of_movement",
    "ForceIndex": "app.extend.blocks.indicators.volume.force_index",
    "KlingerOscillator": "app.extend.blocks.indicators.volume.klinger_oscillator",
    "MFI": "app.extend.blocks.indicators.volume.mfi",
    "NetVolume": "app.extend.blocks.indicators.volume.net_volume",
    "OBV": "app.extend.blocks.indicators.volume.obv",
    "PriceVolumeTrend": "app.extend.blocks.indicators.volume.price_volume_trend",
    "TPOProfile": "app.extend.blocks.indicators.volume.tpo_profile",
    "VWAP": "app.extend.blocks.indicators.volume.vwap",
    "VWMA": "app.extend.blocks.indicators.volume.vwma",
    "VolumeOscillator": "app.extend.blocks.indicators.volume.volume_oscillator",
    "VolumeProfile": "app.extend.blocks.indicators.volume.volume_profile",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "CMF",
    "COT",
    "MFI",
    "OBV",
    "VWAP",
    "VWMA",
    "AccumulationDistribution",
    "AdvanceDecline",
    "AggressiveTradeImbalance",
    "AnchoredVWAP",
    "AvgVolume",
    "ChaikinOscillator",
    "CumulativeVolumeDelta",
    "EaseOfMovement",
    "ForceIndex",
    "KlingerOscillator",
    "NetVolume",
    "PriceVolumeTrend",
    "TPOProfile",
    "VolumeOscillator",
    "VolumeProfile",
]
