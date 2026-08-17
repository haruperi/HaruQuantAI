"""Unit tests for Research point-in-time evidence projection gate."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.research.contracts.errors import ValidationError
from app.services.research.data.pit_projection import project_point_in_time_evidence


def test_project_point_in_time_evidence_branches() -> None:
    """Verify project_point_in_time_evidence error branches and availability checks."""
    now = datetime.now(UTC)

    # Naive decision time
    with pytest.raises(ValidationError, match="PIT_DECISION_TIME_NAIVE"):
        project_point_in_time_evidence([], decision_time_utc=datetime.now())  # noqa: DTZ005

    # Not a mapping
    with pytest.raises(ValidationError, match="PIT_RECORD_NOT_MAPPING"):
        project_point_in_time_evidence(["not_a_mapping"], decision_time_utc=now)

    # Invalid timestamp format
    bad_record = [{"available_at": "invalid-iso-date"}]
    with pytest.raises(ValidationError, match="PIT_AVAILABLE_AT_INVALID"):
        project_point_in_time_evidence(bad_record, decision_time_utc=now)

    # Filtered records
    records = [
        {"available_at": None, "id": 1},
        {"available_at": "2020-01-01T00:00:00", "id": 2},
        {"available_at": "2099-01-01T00:00:00Z", "id": 3},
        {"available_at": "2020-01-01T00:00:00Z", "id": 4},
        {"available_at": now, "id": 5},
    ]
    projected = project_point_in_time_evidence(records, decision_time_utc=now)
    assert len(projected) == 2
    assert tuple(r["id"] for r in projected) == (4, 5)
