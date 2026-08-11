"""Focused branch coverage for economic-calendar store normalization."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar import store


def test_missing_intervals_merges_complete_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return only gaps after merging complete overlapping intervals."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=10)
    rows = (
        {
            "range_start": (start - timedelta(days=1)).isoformat(),
            "range_end": (start + timedelta(days=2)).isoformat(),
            "status": "complete",
        },
        {
            "range_start": (start + timedelta(days=1)).isoformat(),
            "range_end": (start + timedelta(days=4)).isoformat(),
            "status": "complete",
        },
        {
            "range_start": (start + timedelta(days=5)).isoformat(),
            "range_end": (start + timedelta(days=6)).isoformat(),
            "status": "partial",
        },
        {
            "range_start": (start + timedelta(days=7)).isoformat(),
            "range_end": (end + timedelta(days=1)).isoformat(),
            "status": "complete",
        },
    )
    monkeypatch.setattr(
        store,
        "read_economic_calendar_coverage_records",
        lambda **_: SimpleNamespace(rows=rows),
    )

    missing = store.EconomicEventStore().missing_intervals(
        start,
        end,
        request_id="req-test",
    )

    assert missing == ((start + timedelta(days=4), start + timedelta(days=7)),)


def test_missing_intervals_and_stored_rows_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject invalid windows and malformed persisted rows."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(DataError):
        store.EconomicEventStore().missing_intervals(
            start,
            start,
            request_id="req-test",
        )
    response = store.from_row({"provider": None})
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "FILE_CORRUPTED"
    monkeypatch.setattr(
        store,
        "read_economic_calendar_coverage_records",
        lambda **_: SimpleNamespace(rows=()),
    )
    assert store.EconomicEventStore().missing_intervals(
        start,
        start + timedelta(days=1),
        request_id="req-test",
    ) == ((start, start + timedelta(days=1)),)
