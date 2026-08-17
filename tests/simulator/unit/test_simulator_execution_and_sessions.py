"""Unit tests for Simulator execution, provider semantics, live sessions, and scheduler state."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.simulator.execution.lifecycle import (
    deterministic_lifecycle_ticket,
)
from app.services.simulator.execution.provider_semantics import (
    select_provider_revision,
)
from app.services.simulator.state.live_sessions import (
    reset_live_simulation_sessions,
)


def test_simulator_execution_lifecycle_ticket() -> None:
    """Verify deterministic_lifecycle_ticket generation."""
    ticket = deterministic_lifecycle_ticket("order", {"id": "1", "symbol": "EURUSD"})
    assert ticket.startswith("sim-order-")

    with pytest.raises(ValueError, match="lifecycle ticket material is incomplete"):
        deterministic_lifecycle_ticket("", {})


def test_simulator_provider_semantics_revision() -> None:
    """Verify select_provider_revision error on empty revisions."""
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="provider revision coverage is not unique"):
        select_provider_revision([], at=now)


def test_simulator_reset_live_sessions() -> None:
    """Verify reset_live_simulation_sessions clears active sessions."""
    reset_live_simulation_sessions()
