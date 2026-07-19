"""Unit tests for Trading-owned additive migration definitions."""

# ruff: noqa: INP001

from app.services.trading.state import (
    TRADING_SCHEMA_VERSION,
    TradingEvent,
    get_trading_migrations,
)


def test_schema_version_matches_events() -> None:
    """Trading schema version matches versioned event contracts."""
    assert TRADING_SCHEMA_VERSION == "v1"
    assert TradingEvent.model_fields["event_version"].default == "v1"


def test_migrations_are_additive_and_ordered() -> None:
    """Migration definitions are owned, ordered, and free of destructive SQL."""
    steps = get_trading_migrations()
    assert tuple(step.migration_id for step in steps) == tuple(
        sorted(step.migration_id for step in steps)
    )
    assert all(step.domain == "trading" for step in steps)
    statements = " ".join(
        statement.upper() for step in steps for statement in step.statements
    )
    assert "DROP " not in statements
    assert "DELETE " not in statements
