"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.volume.aggressive_trade_imbalance import (
        AggressiveTradeImbalance,
    )
    from app.extend.blocks.indicators.volume.anchored_vwap import AnchoredVWAP
    from app.extend.blocks.indicators.volume.avg_volume import AvgVolume
    from app.extend.blocks.indicators.volume.cmf import CMF
    from app.extend.blocks.indicators.volume.cot import COT
    from app.extend.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )
    from app.extend.blocks.indicators.volume.mfi import MFI
    from app.extend.blocks.indicators.volume.obv import OBV
    from app.extend.blocks.indicators.volume.tpo_profile import TPOProfile
    from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
    from app.extend.blocks.indicators.volume.vwap import VWAP

_EXPORTS = {
    ("AggressiveTradeImbalance"): (
        "app.extend.blocks.indicators.volume.aggressive_trade_imbalance"
    ),
    "AnchoredVWAP": "app.extend.blocks.indicators.volume.anchored_vwap",
    "AvgVolume": "app.extend.blocks.indicators.volume.avg_volume",
    "CMF": "app.extend.blocks.indicators.volume.cmf",
    "COT": "app.extend.blocks.indicators.volume.cot",
    ("CumulativeVolumeDelta"): (
        "app.extend.blocks.indicators.volume.cumulative_volume_delta"
    ),
    "MFI": "app.extend.blocks.indicators.volume.mfi",
    "OBV": "app.extend.blocks.indicators.volume.obv",
    "TPOProfile": "app.extend.blocks.indicators.volume.tpo_profile",
    "VWAP": "app.extend.blocks.indicators.volume.vwap",
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
    "AggressiveTradeImbalance",
    "AnchoredVWAP",
    "AvgVolume",
    "CumulativeVolumeDelta",
    "TPOProfile",
    "VolumeProfile",
]
