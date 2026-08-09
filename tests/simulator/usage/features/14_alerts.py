"""Standalone usage for FEAT-SIM-14 simulated alert lifecycle."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    build_simulation_alert,
    evaluate_emergency_controls,
    group_simulation_alerts,
    transition_simulation_alert,
)


def _alert() -> object:
    """Build one bounded inactive alert."""
    now = datetime.now(UTC)
    return build_simulation_alert(
        alert_id="alert-usage",
        source_event_id="event-usage",
        root_cause_id="root-usage",
        severity="critical",
        first_observed_at=now,
        perceived_at=now + timedelta(milliseconds=5),
    )


def fr_sim_129() -> None:
    """FR-SIM-129: Simulator shall define immutable `AlertEvent v1` identity, severity, source, root cause, observation, perception, acknowledgement, resolution, clearing, latching, and bounded detail evidence."""
    alert = _alert()
    print(f"SUCCESS: FR-SIM-129 alert built; Data -> {alert.alert_id}")


def fr_sim_130() -> None:
    """FR-SIM-130: Simulator shall enforce `INACTIVE`, `ACTIVE_UNACKNOWLEDGED`, `ACTIVE_ACKNOWLEDGED`, `RESOLVED`, and `CLEARED` alert transitions with resolution-before-clear latching."""
    alert = _alert()
    now = alert.perceived_at
    alert = transition_simulation_alert(alert, "ACTIVE_UNACKNOWLEDGED", occurred_at=now)
    alert = transition_simulation_alert(alert, "ACTIVE_ACKNOWLEDGED", occurred_at=now)
    alert = transition_simulation_alert(alert, "RESOLVED", occurred_at=now)
    alert = transition_simulation_alert(alert, "CLEARED", occurred_at=now)
    print(f"SUCCESS: FR-SIM-130 lifecycle completed; Data -> {alert.state}")


def fr_sim_131() -> None:
    """FR-SIM-131: Simulator shall group derivative alert symptoms under deterministic root-cause incidents with stable severity, observation-time, and identity ordering."""
    grouped = group_simulation_alerts((_alert(),))
    print(f"SUCCESS: FR-SIM-131 root cause grouped; Data -> {tuple(grouped)}")


def fr_sim_132() -> None:
    """FR-SIM-132: Simulator shall preserve the first player perception timestamp separately from causal and venue timing for fair response-time scoring."""
    alert = _alert()
    print(
        f"SUCCESS: FR-SIM-132 perception preserved; Data -> {alert.perceived_at.isoformat()}"
    )


def fr_sim_133() -> None:
    """FR-SIM-133: Simulator shall keep cancel, close, reduce, and kill-switch controls available during lock states while blocking risk-increasing and unknown actions."""
    controls = evaluate_emergency_controls(
        ("cancel_order", "submit_order", "engage_kill_switch"), locked=True
    )
    print(f"SUCCESS: FR-SIM-133 controls evaluated; Data -> {dict(controls)}")


def main() -> None:
    """Run every FEAT-SIM-14 requirement demonstration."""
    print("FEATURE: FEAT-SIM-14 — Alert Lifecycle")
    fr_sim_129()
    fr_sim_130()
    fr_sim_131()
    fr_sim_132()
    fr_sim_133()


if __name__ == "__main__":
    main()
