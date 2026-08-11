"""Unit tests for Analytics emergency response analysis."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.analytics.emergency_response.analysis import (
    analyze_emergency_response,
)


def test_analyze_emergency_response_complete_sequence() -> None:
    """Complete required sequence calculates duration and survival evidence."""
    t1 = datetime(2026, 8, 11, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 8, 11, 10, 5, tzinfo=UTC)
    events = [
        {"kind": "perceived", "occurred_at": t1},
        {"kind": "acknowledged", "occurred_at": "2026-08-11T10:02:00+00:00"},
        {"kind": "resolved", "occurred_at": t2, "survival": True},
    ]
    required = ["perceived", "acknowledged", "resolved"]
    result = analyze_emergency_response(events, required_sequence=required)

    assert result["sequence_status"] == "complete"
    assert result["resolution_seconds"] == 300.0
    assert result["survival"] is True


def test_analyze_emergency_response_incomplete_sequence() -> None:
    """Incomplete sequence returns incomplete status and None resolution seconds."""
    events = [
        {"kind": "perceived", "occurred_at": "2026-08-11T10:00:00+00:00"},
    ]
    required = ["perceived", "acknowledged", "resolved"]
    result = analyze_emergency_response(events, required_sequence=required)

    assert result["sequence_status"] == "incomplete"
    assert result["resolution_seconds"] is None
    assert result["survival"] is None
