"""Public Strategy signal-library exports.

Each name below is one strategy in the library — catalogue content, not a
Strategy feature. The execution mechanism lives in
``app.services.strategy.signals``.
"""

from app.services.strategy.evaluators.decomposing_trade import (
    DecomposingTradeEvaluator,
)
from app.services.strategy.evaluators.harriet_hedging import HarrietHedgingEvaluator
from app.services.strategy.evaluators.market_structure import MarketStructureEvaluator
from app.services.strategy.evaluators.naive_ma_trend import NaiveMATrendEvaluator
from app.services.strategy.evaluators.random_walk import RandomWalkEvaluator
from app.services.strategy.evaluators.sqx_breakout_atr_trailing import (
    SQXBreakoutAtrTrailingEvaluator,
)
from app.services.strategy.evaluators.white_fairy import WhiteFairyEvaluator

__all__ = [
    "DecomposingTradeEvaluator",
    "HarrietHedgingEvaluator",
    "MarketStructureEvaluator",
    "NaiveMATrendEvaluator",
    "RandomWalkEvaluator",
    "SQXBreakoutAtrTrailingEvaluator",
    "WhiteFairyEvaluator",
]
