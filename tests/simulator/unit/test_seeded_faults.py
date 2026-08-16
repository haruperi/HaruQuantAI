"""Scenario-owned seeded transport and delivery fault evidence."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator import build_seeded_fault_event, create_realism_stream


def test_seeded_fault_is_scenario_owned_and_journalled() -> None:
    """FR-SIM-229: scenario creates deterministic calibrated fault evidence."""
    stream = create_realism_stream({"seed": 9, "symbol": "EURUSD"}, "fault")
    event = build_seeded_fault_event(
        stream=stream,
        fault_type="ambiguous_response",
        probability=Decimal(1),
        occurred_at=datetime(2025, 1, 1, tzinfo=UTC),
        artifact_checksum="a" * 64,
    )
    assert event is not None
    assert event.event_type == "ambiguous_response"
    assert event.payload["journal_event_type"] == "seeded_scenario_fault"


def test_fault_vocabulary_and_probability_fail_closed() -> None:
    """FR-SIM-229: non-scenario fault kinds and invalid probability are rejected."""
    stream = create_realism_stream({"seed": 9}, "fault")
    with pytest.raises(ValueError, match="scenario-owned"):
        build_seeded_fault_event(
            stream=stream,
            fault_type="invented",
            probability=Decimal(1),
            occurred_at=datetime(2025, 1, 1, tzinfo=UTC),
            artifact_checksum="a" * 64,
        )
