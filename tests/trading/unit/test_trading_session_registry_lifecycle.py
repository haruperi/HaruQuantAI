"""Unit tests for Trading session registry and lifecycle operations."""

from __future__ import annotations

import pytest
from app.services.trading.session_registry.lifecycle import (
    _record,
)
from app.services.trading.session_registry.registry import (
    create_execution_session,
)


def test_trading_create_execution_session_validation() -> None:
    """Verify create_execution_session validation for SIM mode."""
    with pytest.raises(
        ValueError, match="SIM sessions require initial balance and leverage"
    ):
        create_execution_session(
            principal_id="user-1",
            environment_id="env-1",
            name="Session 1",
            mode="sim",
            provider="simulated",
            request_id="req-1",
            sim_initial_balance=None,
            sim_leverage=None,
        )


def test_trading_session_lifecycle_record_unavailable() -> None:
    """Verify _record raises when session is missing."""
    with pytest.raises(ValueError, match="execution session is unavailable"):
        _record("nonexistent_session_id")
