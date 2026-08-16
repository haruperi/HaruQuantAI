"""Integration tests for weekly and exceptional provider sessions."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.simulator.execution.provider_semantics import is_provider_session_open

NOW = datetime(2026, 8, 17, 10, tzinfo=UTC)


def _revision(payload: dict[str, object]) -> dict[str, object]:
    return {
        "complete_coverage": True,
        "effective_from": NOW - timedelta(days=1),
        "effective_to": NOW + timedelta(days=2),
        "payload": payload,
    }


def test_dated_closure_overrides_weekly_session() -> None:
    """Verified dated closures override ordinary weekly availability."""
    payload = {
        "weekly_sessions": {"0": (("09:00", "17:00"),)},
        "dated_exceptions": {NOW.date().isoformat(): None},
        "exception_coverage": (NOW.date().isoformat(),),
        "exception_coverage_required": True,
    }
    assert not is_provider_session_open(_revision(payload), at=NOW)


def test_missing_dated_session_exception_blocks_canonical_execution() -> None:
    """A possible exceptional interval without dated proof fails closed."""
    payload = {
        "weekly_sessions": {"0": (("09:00", "17:00"),)},
        "dated_exceptions": {},
        "exception_coverage": (),
        "exception_coverage_required": True,
    }
    with pytest.raises(ValueError, match="uncovered"):
        is_provider_session_open(_revision(payload), at=NOW)
