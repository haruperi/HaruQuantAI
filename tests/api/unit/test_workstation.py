"""Tests for FEAT-API-10 workstation contracts."""

from datetime import UTC, datetime

from app.services.api import build_workstation_read_model, execute_workstation_command


def test_read_model_preserves_unknown_panels() -> None:
    """Absent owner panels remain explicit unknown values."""
    result = build_workstation_read_model(
        version=2,
        as_of=datetime.now(UTC),
        panels={"market": {"status": "known"}},
        freshness={},
    )
    assert result["version"] == 2
    assert result["panels"]["portfolio"]["status"] == "unknown"


def test_command_rejects_stale_and_delegates_once() -> None:
    """Optimistic versioning blocks stale commands and delegates once."""
    calls: list[object] = []
    stale = execute_workstation_command(
        {"expected_version": 1}, current_version=2, owner_handler=calls.append
    )
    assert stale["reason"] == "STALE_WORKSTATION_VERSION"
    accepted = execute_workstation_command(
        {"expected_version": 2, "idempotency_key": "k", "correlation_id": "c"},
        current_version=2,
        owner_handler=lambda value: calls.append(value) or {"ok": True},
    )
    assert accepted["status"] == "accepted"
    assert len(calls) == 1
