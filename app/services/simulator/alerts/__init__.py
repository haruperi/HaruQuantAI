"""Simulated alert lifecycle feature API."""

from app.services.simulator.alerts.contracts import AlertEvent, build_simulation_alert
from app.services.simulator.alerts.controls import evaluate_emergency_controls
from app.services.simulator.alerts.grouping import group_simulation_alerts
from app.services.simulator.alerts.lifecycle import transition_simulation_alert

__all__ = [
    "AlertEvent",
    "build_simulation_alert",
    "evaluate_emergency_controls",
    "group_simulation_alerts",
    "transition_simulation_alert",
]
