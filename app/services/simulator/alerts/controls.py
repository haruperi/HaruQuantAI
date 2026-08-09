"""Emergency-control availability during simulation lock states."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType

_RISK_REDUCING = frozenset(
    {"cancel_order", "close_position", "reduce_position", "engage_kill_switch"}
)


def evaluate_emergency_controls(
    actions: Sequence[str], *, locked: bool
) -> Mapping[str, bool]:
    """Return fail-closed control availability for one lock state.

    Args:
        actions: Requested control identities.
        locked: Whether the simulation is in a lock state.

    Returns:
        Immutable action-to-availability mapping. Unknown actions are unavailable
        while locked; risk-reducing controls always remain available.
    """
    return MappingProxyType(
        {
            action: (not locked or action in _RISK_REDUCING)
            for action in dict.fromkeys(actions)
        }
    )


__all__ = ["evaluate_emergency_controls"]
