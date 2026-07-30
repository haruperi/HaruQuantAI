"""Function-only construction for Trading action dependencies."""

from __future__ import annotations

from typing import Any, cast

from app.services.trading.actions.dependencies import TradingDependencies


def create_trading_dependencies(**values: object) -> TradingDependencies:
    """Construct one validated Trading dependency container.

    Args:
        **values: Dependency and runtime-policy values.

    Returns:
        Internal immutable dependency container.
    """
    return TradingDependencies(**cast("Any", values))


__all__ = ["create_trading_dependencies"]
