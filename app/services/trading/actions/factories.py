"""Function-only construction for Trading action dependencies."""

from __future__ import annotations

from typing import Any, cast

from app.services.trading.actions.dependencies import TradingDependencies
from app.services.trading.state import create_execution_position_store


def create_trading_dependencies(**values: object) -> TradingDependencies:
    """Construct one validated Trading dependency container.

    Args:
        **values: Dependency and runtime-policy values.

    Returns:
        Internal immutable dependency container.
    """
    material = dict(values)
    material.setdefault("execution_positions", create_execution_position_store())
    return TradingDependencies(**cast("Any", material))


__all__ = ["create_trading_dependencies"]
