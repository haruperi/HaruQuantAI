"""Unit evidence for the socket-free broker dashboard snapshot."""

from datetime import datetime

from app.services.brokers import get_broker_dashboard_snapshot


def test_dashboard_snapshot_reports_unavailable_without_socket() -> None:
    """Return the explicit unavailable snapshot with a UTC observation time."""
    snapshot = get_broker_dashboard_snapshot()

    assert set(snapshot) == {"view", "owner", "status", "reason", "observed_at"}
    assert snapshot["view"] == "broker"
    assert snapshot["owner"] == "brokers"
    assert snapshot["status"] == "unavailable"
    assert snapshot["reason"] == "BROKER_SESSION_CONTEXT_REQUIRED"
    observed_at = snapshot["observed_at"]
    assert isinstance(observed_at, datetime)
    assert observed_at.tzinfo is not None
