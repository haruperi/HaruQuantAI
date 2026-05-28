"""
Strategy tools exposed to HaruQuant agents.

This package exposes approved AI-callable strategy tools and compatibility
classes for strategy implementations.

Official AI Tools:
    - register_builtin_strategy_tools
    - list_strategy_names
    - get_strategy_metadata
    - validate_strategy_dataframe
    - normalize_signal_columns
    - validate_trade_actions
    - run_vectorized_strategy
    - extract_strategy_signals
    - validate_strategy_actions
    - save_strategy_source_file

Compatibility Classes and Contracts:
    - BaseStrategy
    - VectorizedSignalStrategy
    - StatefulEventStrategy
    - SignalDict
    - SignalIntent
    - StrategyEvent
    - StrategyContext
    - PositionSnapshot
    - TradeAction

Notes:
    Storage tools are medium-risk because they write local files. This package
    does not expose dynamic imports, destructive deletes, or broker actions.
"""

# base.py compatibility exports
from tools.strategy.base import (
    BaseStrategy,
    StatefulEventStrategy,
    VectorizedSignalStrategy,
)

# contracts.py compatibility exports
from tools.strategy.contracts import (
    OrderType,
    PositionSnapshot,
    SignalDict,
    SignalIntent,
    SignalSide,
    StatefulStrategyMixin,
    StrategyContext,
    StrategyEvent,
    TradeAction,
    TradeActionType,
)

# registry.py tools
from tools.strategy.registry import (
    get_strategy_metadata,
    list_strategy_names,
    register_builtin_strategy_tools,
)

# signal_tools.py tools
from tools.strategy.signal_tools import (
    extract_strategy_signals,
    run_vectorized_strategy,
)

# storage.py tools
from tools.strategy.storage import save_strategy_source_file

# validation.py tools and compatibility helpers
from tools.utils.validators import (
    normalize_signal_columns,
    validate_strategy_actions,
    validate_strategy_dataframe,
    validate_trade_actions,
)

__all__ = [
    # registry.py tools
    "register_builtin_strategy_tools",
    "list_strategy_names",
    "get_strategy_metadata",
    # signal_tools.py tools
    "run_vectorized_strategy",
    "extract_strategy_signals",
    # storage.py tools
    "save_strategy_source_file",
    # validation.py tools
    "validate_strategy_dataframe",
    "normalize_signal_columns",
    "validate_trade_actions",
    "validate_strategy_actions",
    # compatibility classes/contracts
    "BaseStrategy",
    "VectorizedSignalStrategy",
    "StatefulEventStrategy",
    "SignalDict",
    "SignalIntent",
    "SignalSide",
    "StrategyEvent",
    "StrategyContext",
    "StatefulStrategyMixin",
    "PositionSnapshot",
    "TradeAction",
    "TradeActionType",
    "OrderType",
]
