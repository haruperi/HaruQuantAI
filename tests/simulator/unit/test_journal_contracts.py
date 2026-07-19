"""Unit tests for immutable Simulation journal events."""
# ruff: noqa: INP001

from datetime import UTC, datetime

import pytest
from app.services.simulator.journal import JournalEvent


def test_journal_event_rejects_secret_payload() -> None:
    """Reject sensitive-key evidence at the journal boundary."""
    with pytest.raises(ValueError, match="sensitive"):
        JournalEvent(
            run_id="run-test",
            sequence=0,
            occurred_at=datetime(2025, 1, 1, tzinfo=UTC),
            event_type="run_started",
            payload={"access_token": "unsafe"},
            previous_hash="0" * 64,
            event_hash="1" * 64,
            correlation_id="cor-test",
            causation_id=None,
        )
