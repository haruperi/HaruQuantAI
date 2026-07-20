"""Strategy tools exposed to HaruQuant agents.

Purpose:
    Route approved strategy-domain AI tools from their implementation modules.

AI Tools exported through __all__:
    - registry.py: get_strategy_class, list_strategy_names,
      register_builtin_strategies, register_strategy, registered_strategies
    - stateful_common.py: basket_pnl, current_mid_price,
      ensure_no_signal_columns, ensure_signal_columns, historical_mid_prices,
      is_bar_close, oldest_position, positions_for_side, rolling_rsi,
      rolling_sma, weighted_average_price

Compatibility exports not listed in __all__:
    - base.py: BaseStrategy, SignalDict, SignalIntent, StrategyEvent
    - registry.py: StrategyClass, StrategyRegistryError
    - storage.py: StrategyStorage, storage
    - template_strategy.py: TemplateStrategy
"""

from __future__ import annotations

from app.services.utils.logger import logger
from app.services.utils.standard import (
    standardize_domain_exports,
    standardize_tool_callable,
)

# base.py compatibility exports
from .base import BaseStrategy, SignalDict, SignalIntent, StrategyEvent

# registry.py tools
from .registry import (
    StrategyClass,
    StrategyRegistryError,
    get_strategy_class,
    list_strategy_names,
    register_builtin_strategies,
    register_strategy,
    registered_strategies,
)

# template_strategy.py compatibility exports
from .template_strategy import TemplateStrategy

_LAZY_EXPORTS = {
    "ACTIVATOR_COLUMN_DEFAULTS": "stateful_common",
    "SIGNAL_COLUMN_DEFAULTS": "stateful_common",
    "StrategyStorage": "storage",
    "basket_pnl": "stateful_common",
    "current_mid_price": "stateful_common",
    "ensure_no_signal_columns": "stateful_common",
    "ensure_signal_columns": "stateful_common",
    "historical_mid_prices": "stateful_common",
    "is_bar_close": "stateful_common",
    "oldest_position": "stateful_common",
    "positions_for_side": "stateful_common",
    "rolling_rsi": "stateful_common",
    "rolling_sma": "stateful_common",
    "storage": "storage",
    "weighted_average_price": "stateful_common",
}


def __getattr__(name: str):
    """
    Lazily route strategy compatibility exports and tools.

    Args:
        name (str): Attribute requested from the strategy package.

    Returns:
        Any: Requested object. Callable AI tools are wrapped in the HaruQuant
        standard response envelope before being exposed.

    Raises:
        AttributeError: If the requested name is not a strategy package export.
    """
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    logger.info("strategy lazy export requested | name=%s", name)
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    if callable(value) and not isinstance(value, type):
        value = standardize_tool_callable(
            value,
            tool_name=name,
            tool_category="strategy",
        )
    globals()[name] = value
    return value


__all__ = [
    # stateful_common.py tools
    "basket_pnl",
    "current_mid_price",
    "ensure_no_signal_columns",
    "ensure_signal_columns",
    "historical_mid_prices",
    "is_bar_close",
    "oldest_position",
    "positions_for_side",
    "rolling_rsi",
    "rolling_sma",
    "weighted_average_price",
    # registry.py tools
    "get_strategy_class",
    "list_strategy_names",
    "register_builtin_strategies",
    "register_strategy",
    "registered_strategies",
]


standardize_domain_exports(globals(), __all__, tool_category="strategy")
