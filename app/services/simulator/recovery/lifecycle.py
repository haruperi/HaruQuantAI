"""Fail-closed secured-session recovery state machine."""

from __future__ import annotations

from typing import Literal

from app.kernel.state import attempt_transition, build_transition_table
from app.services.simulator.errors import SimulationError

RecoveryState = Literal[
    "STARTING",
    "RECOVERY_LOCKED",
    "RESTORING",
    "RECONCILING",
    "VERIFIED",
    "EXPLICIT_REARM",
    "RUNNING",
    "INTEGRITY_FAILURE",
]

_RECOVERY_TRANSITIONS = build_transition_table(
    {
        "STARTING": ("RECOVERY_LOCKED",),
        "RECOVERY_LOCKED": ("RESTORING", "INTEGRITY_FAILURE"),
        "RESTORING": ("RECONCILING", "INTEGRITY_FAILURE"),
        "RECONCILING": ("VERIFIED", "INTEGRITY_FAILURE"),
        "VERIFIED": ("EXPLICIT_REARM",),
        "EXPLICIT_REARM": ("RUNNING",),
        "RUNNING": (),
        "INTEGRITY_FAILURE": (),
    },
    terminal_states=("RUNNING", "INTEGRITY_FAILURE"),
)


def transition_recovery_state(
    source: RecoveryState, target: RecoveryState
) -> RecoveryState:
    """Attempt one declared recovery transition.

    Args:
        source: Current recovery state.
        target: Requested recovery state.

    Returns:
        Accepted target state.

    Raises:
        SimulationError: If the transition is undeclared or regressive.
    """
    result = attempt_transition(_RECOVERY_TRANSITIONS, source, target)
    if result["outcome"] != "ACCEPTED":
        raise SimulationError(
            "SIM_RECOVERY_STATE_INVALID", "Recovery lifecycle transition denied"
        )
    return target


__all__ = ["transition_recovery_state"]
