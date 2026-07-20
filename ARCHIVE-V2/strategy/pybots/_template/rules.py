"""Pure strategy rules.

Replace all placeholder functions after copying this package. Do not import brokers,
databases, Risk Governor services, or execution clients here.
"""

from __future__ import annotations

from app.services.strategy import MarketContext
from app.services.strategy.config import StrategyConfig


def long_entry_signal(context: MarketContext, config: StrategyConfig) -> bool:
    """Return True only when a completed-bar long-entry condition is met."""
    del context, config
    return False


def short_entry_signal(context: MarketContext, config: StrategyConfig) -> bool:
    """Return True only when a completed-bar short-entry condition is met."""
    del context, config
    return False


def long_exit_signal(context: MarketContext, config: StrategyConfig) -> bool:
    """Return True only when a long position should be exited."""
    del context, config
    return False


def short_exit_signal(context: MarketContext, config: StrategyConfig) -> bool:
    """Return True only when a short position should be exited."""
    del context, config
    return False
