"""Unit tests for Trading-owned additive migration definitions."""

# ruff: noqa: INP001
import pytest
from app.services.trading.state import (
    TRADING_SCHEMA_VERSION,
    TradingEvent,
    get_trading_migrations,
    run_trading_migrations,
)


def test_schema_version_matches_events() -> None:
    """Trading schema version matches versioned event contracts."""
    assert TRADING_SCHEMA_VERSION == "v1"
    assert TradingEvent.model_fields["event_version"].default == "v1"


def test_migrations_are_ordered_and_forward_only() -> None:
    """The applied initial schema is followed by the guarded ledger rebuild."""
    steps = get_trading_migrations()
    assert steps.status == "success"
    assert steps.data is not None
    steps = steps.data
    assert tuple(step.migration_id for step in steps) == tuple(
        sorted(step.migration_id for step in steps)
    )
    assert all(step.domain == "trading" for step in steps)
    statements = tuple(
        statement.lstrip().upper() for step in steps for statement in step.statements
    )
    assert not any(statement.startswith("DELETE ") for statement in statements)
    assert tuple(step.migration_id for step in steps) == (
        "001_initial_trading_schema",
        "002_closed_position_ledger",
        "003_execution_lifecycle",
        "004_order_lifecycle_states",
    )
    replacement = tuple(item for item in statements if "POSITIONS__NEW" in item)
    assert replacement
    assert any("SLIPPAGE_POINTS INTEGER NOT NULL" in item for item in replacement)
    assert any(item == "DROP TABLE TRADING_FILLS" for item in statements)
    assert any(item == "DROP TABLE TRADING_ORDER_TRANSITIONS" for item in statements)


def test_authoritative_runner_requires_a_request_id() -> None:
    """The side-effect boundary rejects unauditable migration requests."""
    with pytest.raises(ValueError, match="request_id must not be empty"):
        run_trading_migrations(request_id=" ")
