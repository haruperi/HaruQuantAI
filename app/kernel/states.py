"""Component states and legal state transitions for the microkernel.

Traces to: P4-T06, P5-T02, Gate G5
"""

from __future__ import annotations

from enum import StrEnum

from app.kernel.errors import LifecycleError


class ComponentState(StrEnum):
    """Lifecycle states of a provider component."""

    DISCOVERED = "DISCOVERED"
    DISABLED = "DISABLED"
    RESOLVING = "RESOLVING"
    WAITING_FOR_DEPENDENCY = "WAITING_FOR_DEPENDENCY"
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    DRAINING = "DRAINING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    FAILED_CLEANUP = "FAILED_CLEANUP"
    QUARANTINED = "QUARANTINED"
    VERSION_INCOMPATIBLE = "VERSION_INCOMPATIBLE"


_ALLOWED_TRANSITIONS: dict[ComponentState, frozenset[ComponentState]] = {
    ComponentState.DISCOVERED: frozenset(
        {
            ComponentState.DISABLED,
            ComponentState.RESOLVING,
        }
    ),
    ComponentState.DISABLED: frozenset(
        {
            ComponentState.RESOLVING,
            ComponentState.STOPPED,
        }
    ),
    ComponentState.RESOLVING: frozenset(
        {
            ComponentState.WAITING_FOR_DEPENDENCY,
            ComponentState.STARTING,
            ComponentState.FAILED,
            ComponentState.VERSION_INCOMPATIBLE,
        }
    ),
    ComponentState.WAITING_FOR_DEPENDENCY: frozenset(
        {
            ComponentState.STARTING,
            ComponentState.FAILED,
        }
    ),
    ComponentState.STARTING: frozenset(
        {
            ComponentState.ACTIVE,
            ComponentState.DEGRADED,
            ComponentState.FAILED,
            ComponentState.FAILED_CLEANUP,
        }
    ),
    ComponentState.ACTIVE: frozenset(
        {
            ComponentState.DEGRADED,
            ComponentState.DRAINING,
        }
    ),
    ComponentState.DEGRADED: frozenset(
        {
            ComponentState.ACTIVE,
            ComponentState.DRAINING,
        }
    ),
    ComponentState.DRAINING: frozenset(
        {
            ComponentState.STOPPING,
            ComponentState.FAILED,
        }
    ),
    ComponentState.STOPPING: frozenset(
        {
            ComponentState.STOPPED,
            ComponentState.FAILED_CLEANUP,
        }
    ),
    ComponentState.FAILED: frozenset(
        {
            ComponentState.STOPPING,
            ComponentState.QUARANTINED,
        }
    ),
    ComponentState.FAILED_CLEANUP: frozenset(
        {
            ComponentState.QUARANTINED,
        }
    ),
    ComponentState.VERSION_INCOMPATIBLE: frozenset(
        {
            ComponentState.DISABLED,
        }
    ),
    ComponentState.STOPPED: frozenset(
        {
            ComponentState.RESOLVING,
        }
    ),
    ComponentState.QUARANTINED: frozenset(),
}


def transition_component(
    current: ComponentState, target: ComponentState
) -> ComponentState:
    """Validate and transition component state to target state.

    Args:
        current: Current component state.
        target: Target component state.

    Returns:
        The target component state (or current state if self-transition).

    Raises:
        LifecycleError: If transition is not legally permitted.
    """
    if current == target:
        return current

    allowed = _ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        msg = f"invalid component transition: {current} -> {target}"
        raise LifecycleError(msg)

    return target


__all__ = (
    "ComponentState",
    "transition_component",
)
