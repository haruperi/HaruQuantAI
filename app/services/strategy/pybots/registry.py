"""Explicit catalog of bundled strategies for agent/tool discovery."""

from __future__ import annotations

from pathlib import Path

from app.services.strategy.base import BaseStrategy
from app.services.strategy.config import StrategyConfig, load_strategy_config
from app.services.strategy.pybots.decomposing_trade_ea.strategy import (
    DecomposingTradeStrategy,
)
from app.services.strategy.pybots.harriet_hedging_ea.strategy import (
    HarrietHedgingStrategy,
)
from app.services.strategy.pybots.market_structure_ea.strategy import (
    MarketStructureStrategy,
)
from app.services.strategy.pybots.naive_ma_trend.strategy import NaiveMATrendStrategy
from app.services.strategy.pybots.random_walk_ea.strategy import RandomWalkStrategy
from app.services.strategy.pybots.sqx_breakout_atr_trailing.strategy import (
    SQXBreakoutAtrTrailingStrategy,
)
from app.services.strategy.pybots.white_fairy_ea.strategy import WhiteFairyStrategy
from app.services.strategy.state import StrategyState

STRATEGY_TYPES: dict[str, type[BaseStrategy]] = {
    "sqx_breakout_atr_trailing": SQXBreakoutAtrTrailingStrategy,
    "naive_ma_trend": NaiveMATrendStrategy,
    "decomposing_trade_ea": DecomposingTradeStrategy,
    "harriet_hedging_ea": HarrietHedgingStrategy,
    "market_structure_ea": MarketStructureStrategy,
    "random_walk_ea": RandomWalkStrategy,
    "white_fairy_ea": WhiteFairyStrategy,
}


def bundled_strategy_ids() -> tuple[str, ...]:
    """Return stable strategy IDs that agents are allowed to instantiate."""
    return tuple(sorted(STRATEGY_TYPES))


def load_bundled_strategy(
    strategy_id: str, state: StrategyState | None = None
) -> BaseStrategy:
    """Load a bundled config and construct its matching implementation class."""
    try:
        strategy_type = STRATEGY_TYPES[strategy_id]
    except KeyError as error:
        raise KeyError(f"Unknown bundled strategy {strategy_id!r}.") from error
    config = load_strategy_config(Path(__file__).parent / strategy_id / "strategy.json")
    return strategy_type(config, state)


def strategy_from_config(
    config: StrategyConfig, state: StrategyState | None = None
) -> BaseStrategy:
    """Construct a bundled implementation from an already validated config."""
    try:
        return STRATEGY_TYPES[config.strategy_id](config, state)
    except KeyError as error:
        raise KeyError(
            f"No bundled implementation for {config.strategy_id!r}."
        ) from error
