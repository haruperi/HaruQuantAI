"""Latched alert lifecycle using the Utils state-machine contract."""

# ruff: noqa: TC001

from __future__ import annotations

from datetime import datetime

from app.kernel.state import attempt_transition, build_transition_table
from app.services.simulator.alerts.contracts import AlertEvent, AlertState
from app.services.simulator.errors import SimulationError

_ALERT_TRANSITIONS = build_transition_table(
    {
        "INACTIVE": ("ACTIVE_UNACKNOWLEDGED",),
        "ACTIVE_UNACKNOWLEDGED": ("ACTIVE_ACKNOWLEDGED", "RESOLVED"),
        "ACTIVE_ACKNOWLEDGED": ("RESOLVED",),
        "RESOLVED": ("CLEARED", "ACTIVE_UNACKNOWLEDGED"),
        "CLEARED": (),
    },
    terminal_states=("CLEARED",),
)


def transition_simulation_alert(
    alert: AlertEvent, target: AlertState, *, occurred_at: datetime
) -> AlertEvent:
    """Attempt one declared alert transition with latching enforcement.

    Args:
        alert: Current alert projection.
        target: Requested lifecycle state.
        occurred_at: Aware transition timestamp.

    Returns:
        Updated immutable alert.

    Raises:
        SimulationError: If the transition or timestamp is invalid.
    """
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise SimulationError("SIM_ALERT_TRANSITION_INVALID", "Alert time is naive")
    latest_at = (
        alert.cleared_at
        or alert.resolved_at
        or alert.acknowledged_at
        or alert.first_observed_at
    )
    if occurred_at < latest_at:
        raise SimulationError(
            "SIM_ALERT_TRANSITION_INVALID", "Alert time precedes current state"
        )
    result = attempt_transition(_ALERT_TRANSITIONS, alert.state, target)
    if result["outcome"] != "ACCEPTED":
        raise SimulationError(
            "SIM_ALERT_TRANSITION_INVALID", "Alert lifecycle transition denied"
        )
    if target == "CLEARED" and alert.latched and alert.resolved_at is None:
        raise SimulationError(
            "SIM_ALERT_TRANSITION_INVALID", "Latched alert must resolve before clear"
        )
    updates: dict[str, object] = {"state": target}
    if target == "ACTIVE_ACKNOWLEDGED":
        updates["acknowledged_at"] = occurred_at
    elif target == "RESOLVED":
        updates["resolved_at"] = occurred_at
    elif target == "CLEARED":
        updates["cleared_at"] = occurred_at
    elif target == "ACTIVE_UNACKNOWLEDGED" and alert.state == "RESOLVED":
        updates.update(
            {"acknowledged_at": None, "resolved_at": None, "cleared_at": None}
        )
    return alert.model_copy(update=updates)


__all__ = ["transition_simulation_alert"]
