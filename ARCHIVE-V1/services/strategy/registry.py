"""Strategy registry tools.

Purpose:
    Provide AI-callable registry lookups and registration helpers for strategy
    classes used by simulation and strategy workflows.

Exported AI Tools:
    - get_strategy_class: Resolve a strategy class by name.
    - list_strategy_names: List registered strategy names.
    - register_builtin_strategies: Load built-in strategy classes.
    - register_strategy: Register a strategy class.
    - registered_strategies: Return the current registry mapping.

Internal Helpers:
    - _normalize_name: Validates and normalizes registry names.
    - _ensure_builtin_strategies_registered: Loads built-ins once.
    - _builtin_strategy_classes: Imports built-in strategy classes lazily.

Classes:
    - StrategyRegistryError: Lookup error for registry failures.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.services.strategy.base import BaseStrategy
from app.services.utils.logger import logger

TOOL_NAME = "strategy_registry"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


class StrategyRegistryError(LookupError):
    """Raised when a strategy cannot be resolved from the registry."""


StrategyClass = type[BaseStrategy]

_STRATEGIES: dict[str, StrategyClass] = {}
_BUILTINS_REGISTERED = False


def register_strategy(name: str, strategy_cls: StrategyClass) -> None:
    """
    Register a strategy class by config-facing name.

    Use this tool when an agent needs to make a validated BaseStrategy subclass
    available to simulation or strategy workflows during the current process.

    Args:
        name (str): Non-empty registry name.
        strategy_cls (StrategyClass): BaseStrategy subclass to register.

    Returns:
        None: The public package export wraps this in a standard tool response.

    Raises:
        StrategyRegistryError: If the name is empty.
        TypeError: If strategy_cls is not a BaseStrategy subclass.
    """
    normalized = _normalize_name(name)
    if not isinstance(strategy_cls, type) or not issubclass(strategy_cls, BaseStrategy):
        logger.warning("strategy registration failed | name=%s", name)
        raise TypeError("strategy_cls must be a BaseStrategy subclass")
    _STRATEGIES[normalized] = strategy_cls
    logger.info(
        "strategy registered | name=%s | class=%s", normalized, strategy_cls.__name__
    )


def get_strategy_class(name: str) -> StrategyClass:
    """
    Resolve a strategy class by config-facing name.

    Use this tool when an agent or simulation config needs the concrete Python
    strategy class associated with a registered strategy name.

    Args:
        name (str): Non-empty registry name to resolve.

    Returns:
        StrategyClass: Matching BaseStrategy subclass.

    Raises:
        StrategyRegistryError: If the name is empty or no strategy is found.
    """
    normalized = _normalize_name(name)
    if normalized in _STRATEGIES:
        logger.info("strategy resolved | name=%s", normalized)
        return _STRATEGIES[normalized]
    _ensure_builtin_strategies_registered()
    try:
        logger.info(
            "strategy resolved after builtin registration | name=%s", normalized
        )
        return _STRATEGIES[normalized]
    except KeyError as exc:
        available = ", ".join(list_strategy_names())
        logger.warning("strategy resolution failed | name=%s", normalized)
        raise StrategyRegistryError(
            f"unknown strategy {normalized!r}; available strategies: {available}"
        ) from exc


def list_strategy_names() -> tuple[str, ...]:
    """
    Return registered strategy names in stable order.

    Use this tool when an agent needs to inspect which strategy classes can be
    referenced by simulation or strategy configuration.

    Returns:
        tuple[str, ...]: Sorted registered strategy names.
    """
    _ensure_builtin_strategies_registered()
    names = tuple(sorted(_STRATEGIES))
    logger.info("strategy names listed | count=%s", len(names))
    return names


def registered_strategies() -> dict[str, StrategyClass]:
    """
    Return a shallow copy of the strategy registry.

    Use this tool when an agent needs the current name-to-class mapping for
    diagnostics, validation, or workflow planning.

    Returns:
        dict[str, StrategyClass]: Copy of registered strategy classes by name.
    """
    _ensure_builtin_strategies_registered()
    registry = dict(_STRATEGIES)
    logger.info("strategy registry copied | count=%s", len(registry))
    return registry


def register_builtin_strategies() -> None:
    """
    Register built-in simulation strategies.

    Use this tool when an agent needs to ensure packaged baseline strategy
    classes are available in the registry before lookup or simulation.

    Returns:
        None: The public package export wraps this in a standard tool response.
    """
    for strategy_cls in _builtin_strategy_classes():
        register_strategy(strategy_cls.__name__, strategy_cls)
    logger.info("builtin strategies registered | count=%s", len(_STRATEGIES))


def _normalize_name(name: str) -> str:
    """Validate and normalize a strategy registry name."""
    normalized = str(name or "").strip()
    if not normalized:
        raise StrategyRegistryError("strategy name must be non-empty")
    return normalized


def _ensure_builtin_strategies_registered() -> None:
    """Register built-in strategies once per process."""
    global _BUILTINS_REGISTERED
    if _BUILTINS_REGISTERED:
        return
    register_builtin_strategies()
    _BUILTINS_REGISTERED = True


def _builtin_strategy_classes() -> Iterable[StrategyClass]:
    """Return lazily imported built-in strategy classes."""
    from data.strategies.baselines.close_breakout import CloseBreakoutStrategy
    from data.strategies.baselines.market_structure_hedge_grid import (
        MarketStructureHedgeGridStrategy,
    )
    from data.strategies.baselines.mtf_hedge_trail import StructureHedgeTrailStrategy
    from data.strategies.baselines.pyramiding import PyramidingStrategy
    from data.strategies.baselines.rsi_averaging_pyramid import (
        RsiAveragingPyramidStrategy,
    )
    from data.strategies.baselines.rsi_decomposing_reentry import (
        RsiDecomposingReentryStrategy,
    )
    from data.strategies.baselines.rsi_martingale import RsiMartingaleStrategy
    from data.strategies.baselines.trade_decomposition import TradeDecompositionStrategy
    from data.strategies.baselines.trend_following import TrendFollowingStrategy

    return (
        TrendFollowingStrategy,
        CloseBreakoutStrategy,
        RsiMartingaleStrategy,
        PyramidingStrategy,
        TradeDecompositionStrategy,
        RsiAveragingPyramidStrategy,
        StructureHedgeTrailStrategy,
        RsiDecomposingReentryStrategy,
        MarketStructureHedgeGridStrategy,
    )


__all__ = [
    "StrategyClass",
    "StrategyRegistryError",
    "get_strategy_class",
    "list_strategy_names",
    "register_builtin_strategies",
    "register_strategy",
    "registered_strategies",
]
