"""Unit tests for versioned Trading events."""

# ruff: noqa: INP001

from datetime import UTC, datetime

import pytest
from app.services.trading.state import TradingEvent
from pydantic import ValidationError


def _event_data() -> dict[str, object]:
    """Return complete event evidence."""
    return {
        "event_id": "event-001",
        "event_type": "send_attempted",
        "aggregate_version": 0,
        "route": "sim",
        "tenant_id": "tenant-001",
        "authority_id": "simulator",
        "occurred_at": datetime(2026, 7, 19, 8, 0, tzinfo=UTC),
        "request_id": "request-001",
        "workflow_id": "workflow-001",
        "correlation_id": "correlation-001",
        "payload": {"order_id": "order-001"},
    }


def test_event_requires_trace_and_utc_time() -> None:
    """Events require complete trace evidence and timezone-aware UTC time."""
    missing_trace = _event_data()
    missing_trace.pop("workflow_id")
    with pytest.raises(ValidationError):
        TradingEvent.model_validate(missing_trace)
    naive_time = _event_data()
    naive_time["occurred_at"] = datetime(2026, 7, 19, 8, 0, tzinfo=UTC).replace(
        tzinfo=None
    )
    with pytest.raises(ValidationError, match="timezone-aware UTC"):
        TradingEvent.model_validate(naive_time)


def test_event_rejects_sensitive_payload_key() -> None:
    """Event redaction evidence rejects an unredacted protected key."""
    data = _event_data()
    data["payload"] = {"api_secret": "x"}
    with pytest.raises(ValidationError, match="unredacted sensitive keys"):
        TradingEvent.model_validate(data)
