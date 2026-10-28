"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.volume.aggressive_trade_imbalance import (
        AggressiveTradeImbalance,
    )
    from app.include.blocks.indicators.volume.anchored_vwap import AnchoredVWAP
    from app.include.blocks.indicators.volume.avg_volume import AvgVolume
    from app.include.blocks.indicators.volume.cmf import CMF
    from app.include.blocks.indicators.volume.cot import COT
    from app.include.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )
    from app.include.blocks.indicators.volume.mfi import MFI
    from app.include.blocks.indicators.volume.obv import OBV
    from app.include.blocks.indicators.volume.tpo_profile import TPOProfile
    from app.include.blocks.indicators.volume.volume_profile import VolumeProfile
    from app.include.blocks.indicators.volume.vwap import VWAP

_EXPORTS = {
    ("AggressiveTradeImbalance"): (
        "app.include.blocks.indicators.volume.aggressive_trade_imbalance"
    ),
    "AnchoredVWAP": "app.include.blocks.indicators.volume.anchored_vwap",
    "AvgVolume": "app.include.blocks.indicators.volume.avg_volume",
    "CMF": "app.include.blocks.indicators.volume.cmf",
    "COT": "app.include.blocks.indicators.volume.cot",
    ("CumulativeVolumeDelta"): (
        "app.include.blocks.indicators.volume.cumulative_volume_delta"
    ),
    "MFI": "app.include.blocks.indicators.volume.mfi",
    "OBV": "app.include.blocks.indicators.volume.obv",
    "TPOProfile": "app.include.blocks.indicators.volume.tpo_profile",
    "VWAP": "app.include.blocks.indicators.volume.vwap",
    "VolumeProfile": "app.include.blocks.indicators.volume.volume_profile",
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
