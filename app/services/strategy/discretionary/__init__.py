"""Discretionary Manual Order strategy identity and bootstrap registration."""

from app.services.strategy.discretionary.registration import (
    get_discretionary_strategy_id,
    register_discretionary_strategy,
    strategy_version_for,
)

__all__ = [
    "get_discretionary_strategy_id",
    "register_discretionary_strategy",
    "strategy_version_for",
]
