"""Early fail-closed safety constants."""

from __future__ import annotations

LIVE_TRADING_ENABLED = False
REQUIRE_APPROVAL_FOR_LIVE = True
DEFAULT_ENVIRONMENT = "development"

BLOCKED_LIVE_REASON = (
    "Live trading is disabled in the lightweight ADK implementation phase."
)


def live_trading_available() -> bool:
    """Return whether live trading is globally enabled."""
    return LIVE_TRADING_ENABLED
