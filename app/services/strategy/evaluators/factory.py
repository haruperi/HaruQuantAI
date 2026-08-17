"""Function-only construction of the registered Strategy evaluator library."""

from collections.abc import Callable, Mapping

from app.services.strategy.evaluators.decomposing_trade import DecomposingTradeEvaluator
from app.services.strategy.evaluators.harriet_hedging import HarrietHedgingEvaluator
from app.services.strategy.evaluators.market_structure import MarketStructureEvaluator
from app.services.strategy.evaluators.naive_ma_trend import NaiveMATrendEvaluator
from app.services.strategy.evaluators.naive_ma_trend_incremental import (
    NaiveMATrendIncrementalEvaluator,
)
from app.services.strategy.evaluators.random_walk import RandomWalkEvaluator
from app.services.strategy.evaluators.sqx_breakout_atr_trailing import (
    SQXBreakoutAtrTrailingEvaluator,
)
from app.services.strategy.evaluators.white_fairy import WhiteFairyEvaluator

_EVALUATORS: Mapping[str, Callable[..., object]] = {
    "decomposing_trade": DecomposingTradeEvaluator,
    "harriet_hedging": HarrietHedgingEvaluator,
    "market_structure": MarketStructureEvaluator,
    "naive_ma_trend": NaiveMATrendEvaluator,
    "naive_ma_trend_incremental": NaiveMATrendIncrementalEvaluator,
    "random_walk": RandomWalkEvaluator,
    "sqx_breakout_atr_trailing": SQXBreakoutAtrTrailingEvaluator,
    "white_fairy": WhiteFairyEvaluator,
}


def create_strategy_evaluator(name: str, **kwargs: object) -> object:
    """Create one approved concrete evaluator by its registered name.

    Args:
        name: Stable registered evaluator name.
        **kwargs: Evaluator-specific construction values.

    Returns:
        Approved internal concrete evaluator.

    Raises:
        ValueError: If ``name`` is not registered.
    """
    normalized_name = name.replace("-", "_")
    try:
        evaluator_type = _EVALUATORS[normalized_name]
    except KeyError as exc:
        message = f"Unknown Strategy evaluator: {name}"
        raise ValueError(message) from exc
    return evaluator_type(**kwargs)


__all__ = ["create_strategy_evaluator"]
