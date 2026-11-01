"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.price_action.candlestick_patterns import (
        CandlestickPatterns,
    )
    from app.extend.blocks.indicators.price_action.chart_patterns import ChartPatterns
    from app.extend.blocks.indicators.price_action.fibo import Fibo
    from app.extend.blocks.indicators.price_action.fractal import Fractal
    from app.extend.blocks.indicators.price_action.heiken_ashi import HeikenAshi
    from app.extend.blocks.indicators.price_action.highest_lowest import HighestLowest
    from app.extend.blocks.indicators.price_action.level_clustering import (
        LevelClustering,
    )
    from app.extend.blocks.indicators.price_action.pivots import Pivots
    from app.extend.blocks.indicators.price_action.price_gap import PriceGap
    from app.extend.blocks.indicators.price_action.zigzag import ZigZag

_EXPORTS = {
    ("CandlestickPatterns"): (
        "app.extend.blocks.indicators.price_action.candlestick_patterns"
    ),
    "ChartPatterns": "app.extend.blocks.indicators.price_action.chart_patterns",
    "Fibo": "app.extend.blocks.indicators.price_action.fibo",
    "Fractal": "app.extend.blocks.indicators.price_action.fractal",
    "HeikenAshi": "app.extend.blocks.indicators.price_action.heiken_ashi",
    "HighestLowest": "app.extend.blocks.indicators.price_action.highest_lowest",
    "LevelClustering": "app.extend.blocks.indicators.price_action.level_clustering",
    "Pivots": "app.extend.blocks.indicators.price_action.pivots",
    "PriceGap": "app.extend.blocks.indicators.price_action.price_gap",
    "ZigZag": "app.extend.blocks.indicators.price_action.zigzag",
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
