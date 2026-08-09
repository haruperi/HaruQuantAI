"""Unit evidence for FEAT-SIM-14 alert lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.simulator import (
    build_simulation_alert,
    evaluate_emergency_controls,
    group_simulation_alerts,
    transition_simulation_alert,
)
from app.services.simulator.errors import SimulationError


def _alert(alert_id: str, root: str = "root-1") -> object:
    """Build one inactive critical test alert."""
    now = datetime.now(UTC)
    return build_simulation_alert(
        alert_id=alert_id,
        source_event_id=f"event-{alert_id}",
        root_cause_id=root,
        severity="critical",
        first_observed_at=now,
        perceived_at=now + timedelta(milliseconds=10),
    )


def test_latched_lifecycle_requires_resolution_before_clear() -> None:
    """Advance through activation, acknowledgement, resolution, and clear."""
    alert = _alert("a")
    now = alert.perceived_at
    alert = transition_simulation_alert(alert, "ACTIVE_UNACKNOWLEDGED", occurred_at=now)
    with pytest.raises(SimulationError, match="transition denied"):
        transition_simulation_alert(alert, "CLEARED", occurred_at=now)
    alert = transition_simulation_alert(alert, "ACTIVE_ACKNOWLEDGED", occurred_at=now)
    alert = transition_simulation_alert(alert, "RESOLVED", occurred_at=now)
    alert = transition_simulation_alert(alert, "CLEARED", occurred_at=now)
    assert alert.state == "CLEARED"


def test_root_cause_grouping_and_emergency_controls() -> None:
    """Group symptoms and keep only risk-reducing controls during locks."""
    grouped = group_simulation_alerts((_alert("a"), _alert("b")))
    assert tuple(grouped) == ("root-1",)
    controls = evaluate_emergency_controls(
        ("cancel_order", "submit_order", "engage_kill_switch"), locked=True
    )
    assert controls == {
        "cancel_order": True,
        "submit_order": False,
        "engage_kill_switch": True,
    }


def test_alert_transition_rejects_regressive_time() -> None:
    """Reject lifecycle timestamps before the alert observation."""
    alert = _alert("a")
    with pytest.raises(SimulationError, match="precedes current state"):
        transition_simulation_alert(
            alert,
            "ACTIVE_UNACKNOWLEDGED",
            occurred_at=alert.first_observed_at - timedelta(microseconds=1),
        )
