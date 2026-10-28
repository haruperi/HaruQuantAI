"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.price_action.candlestick_patterns import (
        CandlestickPatterns,
    )
    from app.include.blocks.indicators.price_action.chart_patterns import ChartPatterns
    from app.include.blocks.indicators.price_action.fibo import Fibo
    from app.include.blocks.indicators.price_action.fractal import Fractal
    from app.include.blocks.indicators.price_action.heiken_ashi import HeikenAshi
    from app.include.blocks.indicators.price_action.highest_lowest import HighestLowest
    from app.include.blocks.indicators.price_action.level_clustering import (
        LevelClustering,
    )
    from app.include.blocks.indicators.price_action.pivots import Pivots
    from app.include.blocks.indicators.price_action.price_gap import PriceGap
    from app.include.blocks.indicators.price_action.zigzag import ZigZag

_EXPORTS = {
    ("CandlestickPatterns"): (
        "app.include.blocks.indicators.price_action.candlestick_patterns"
    ),
    "ChartPatterns": "app.include.blocks.indicators.price_action.chart_patterns",
    "Fibo": "app.include.blocks.indicators.price_action.fibo",
    "Fractal": "app.include.blocks.indicators.price_action.fractal",
    "HeikenAshi": "app.include.blocks.indicators.price_action.heiken_ashi",
    "HighestLowest": "app.include.blocks.indicators.price_action.highest_lowest",
    "LevelClustering": "app.include.blocks.indicators.price_action.level_clustering",
    "Pivots": "app.include.blocks.indicators.price_action.pivots",
    "PriceGap": "app.include.blocks.indicators.price_action.price_gap",
    "ZigZag": "app.include.blocks.indicators.price_action.zigzag",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "CandlestickPatterns",
    "ChartPatterns",
    "Fibo",
    "Fractal",
    "HeikenAshi",
    "HighestLowest",
    "LevelClustering",
    "Pivots",
    "PriceGap",
    "ZigZag",
]
