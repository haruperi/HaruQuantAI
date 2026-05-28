"""Strategy registry helpers and official registry AI tools.

This module stores BaseStrategy subclasses by name and exposes safe registry
query tools for HaruQuant agents.

Exported AI Tools:
    - register_builtin_strategy_tools
    - list_strategy_names
    - get_strategy_metadata

Internal Helpers:
    - normalize_name
    - register_strategy_class
    - get_strategy_class
    - list_registered_strategy_names
    - registered_strategy_metadata
    - register_builtin_strategies

Classes:
    - StrategyRegistryError
"""

from __future__ import annotations

from typing import Any, Type

from tools.strategy.base import BaseStrategy
from tools.utils import logger
from tools.utils.standard import execute_tool_boundary

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

StrategyClass = Type[BaseStrategy]
_STRATEGIES: dict[str, StrategyClass] = {}
_BUILTINS_REGISTERED = False


class StrategyRegistryError(LookupError):
    """Raised when strategy registry operations fail."""


def normalize_name(name: str) -> str:
    """Normalize and validate a strategy registry name."""
    normalized = str(name or "").strip()
    if not normalized:
        raise StrategyRegistryError("strategy name is required.")
    return normalized


def register_strategy_class(name: str, strategy_cls: StrategyClass) -> None:
    """Register a BaseStrategy subclass by name."""
    normalized = normalize_name(name)
    if not isinstance(strategy_cls, type) or not issubclass(strategy_cls, BaseStrategy):
        raise TypeError("strategy_cls must be a BaseStrategy subclass.")
    _STRATEGIES[normalized] = strategy_cls
    logger.info(
        "strategy class registered | name=%s | class=%s",
        normalized,
        strategy_cls.__name__,
    )


def get_strategy_class(name: str) -> StrategyClass:
    """Return a registered strategy class by name."""
    register_builtin_strategies()
    normalized = normalize_name(name)
    if normalized not in _STRATEGIES:
        raise StrategyRegistryError(f"Unknown strategy: {normalized}.")
    return _STRATEGIES[normalized]


def list_registered_strategy_names() -> list[str]:
    """Return sorted registered strategy names."""
    register_builtin_strategies()
    return sorted(_STRATEGIES)


def registered_strategy_metadata() -> dict[str, dict[str, str]]:
    """Return metadata for registered strategy classes."""
    register_builtin_strategies()
    return {
        name: {
            "class_name": strategy_cls.__name__,
            "module": strategy_cls.__module__,
            "strategy_name": str(
                getattr(strategy_cls, "strategy_name", strategy_cls.__name__)
            ),
            "strategy_type": str(getattr(strategy_cls, "strategy_type", "unknown")),
            "signal_schema_version": str(
                getattr(strategy_cls, "signal_schema_version", "1.0")
            ),
            "action_schema_version": str(
                getattr(strategy_cls, "action_schema_version", "1.0")
            ),
        }
        for name, strategy_cls in sorted(_STRATEGIES.items())
    }


def register_builtin_strategies() -> None:
    """Register packaged example strategies once."""
    global _BUILTINS_REGISTERED
    if _BUILTINS_REGISTERED:
        return
    from tools.strategy.examples.trade_decomposition import TradeDecompositionStrategy
    from tools.strategy.examples.trend_following import TrendFollowingStrategy

    register_strategy_class("TrendFollowingStrategy", TrendFollowingStrategy)
    register_strategy_class("TradeDecompositionStrategy", TradeDecompositionStrategy)
    _BUILTINS_REGISTERED = True


def register_builtin_strategy_tools(*, request_id: str | None = None) -> dict[str, Any]:
    """
    Register packaged strategy classes in the in-process registry.

    Use this AI tool when an agent or workflow needs packaged example strategy
    classes available for backtests or metadata discovery. It does not load
    external code and has no broker side effects.

    Args:
        request_id: Optional workflow/request ID for tracing.

    Returns:
        Standard HaruQuant tool response containing registered strategy names.
    """

    def operation() -> dict[str, Any]:
        register_builtin_strategies()
        return {"registered": list_registered_strategy_names()}

    return execute_tool_boundary(
        tool_name="register_builtin_strategy_tools",
        request_id=request_id,
        operation=operation,
        success_message="Built-in strategy classes registered.",
    )


def list_strategy_names(*, request_id: str | None = None) -> dict[str, Any]:
    """
    List registered strategy names.

    Use this AI tool when an agent needs to discover which strategies are
    available without receiving unsafe class objects or executable code.

    Args:
        request_id: Optional workflow/request ID for tracing.

    Returns:
        Standard HaruQuant tool response containing sorted strategy names.
    """

    def operation() -> dict[str, Any]:
        return {"strategies": list_registered_strategy_names()}

    return execute_tool_boundary(
        tool_name="list_strategy_names",
        request_id=request_id,
        operation=operation,
        success_message="Registered strategy names returned.",
    )


def get_strategy_metadata(
    strategy_name: str | None = None,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Return metadata for one or all registered strategies.

    Use this AI tool when an agent needs strategy type, class, module, and schema
    details without direct access to Python class objects.

    Args:
        strategy_name: Optional registered strategy name. If omitted, metadata
            for all registered strategies is returned.
        request_id: Optional workflow/request ID for tracing.

    Returns:
        Standard HaruQuant tool response containing strategy metadata.
    """

    def operation() -> dict[str, Any]:
        metadata = registered_strategy_metadata()
        if strategy_name is None:
            return {"strategies": metadata}
        if strategy_name not in metadata:
            raise LookupError(f"Unknown strategy: {strategy_name}.")
        return {"strategy": metadata[strategy_name]}

    return execute_tool_boundary(
        tool_name="get_strategy_metadata",
        request_id=request_id,
        operation=operation,
        success_message="Strategy metadata returned.",
    )
