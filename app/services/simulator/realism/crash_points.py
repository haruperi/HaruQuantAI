"""Deterministic crash-boundary and unknown-outcome recovery harness."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

_CRASH_POINTS = (
    "after_pre_audit",
    "after_command_submission",
    "after_authority_acceptance",
    "after_response_receipt",
    "after_receipt_persistence",
    "after_projection_update",
    "after_watermark_advancement",
)


def get_points() -> tuple[str, ...]:
    """Return every registered deterministic crash point."""
    return _CRASH_POINTS


def create_state(
    *, command_id: str, crash_point: str, outcome: str, mutation_attempts: int = 1
) -> Mapping[str, object]:
    """Create one immutable exposure-blocked crash recovery state."""
    if not command_id or command_id != command_id.strip():
        raise ValueError("crash recovery command identity is required")
    if crash_point not in _CRASH_POINTS:
        raise ValueError("unknown deterministic crash point")
    if outcome not in {"accepted", "not_found", "unknown"} or mutation_attempts != 1:
        raise ValueError("crash outcome or mutation-attempt count is invalid")
    return MappingProxyType(
        {
            "command_id": command_id,
            "crash_point": crash_point,
            "outcome": outcome,
            "mutation_attempts": mutation_attempts,
            "recovery_state": "RECOVERY_LOCKED",
            "exposure_blocked": True,
        }
    )


def recover(
    state: Mapping[str, object],
    *,
    authority_query: Callable[[str], str],
    kill_switch_active: bool = False,
) -> Mapping[str, object]:
    """Converge by querying authority without repeating the uncertain mutation."""
    if (
        state.get("mutation_attempts") != 1
        or state.get("recovery_state") != "RECOVERY_LOCKED"
    ):
        raise ValueError("unknown-outcome recovery state is invalid")
    command_id = str(state["command_id"])
    outcome = str(state["outcome"])
    if outcome == "unknown":
        outcome = authority_query(command_id)
    if outcome not in {"accepted", "not_found"}:
        raise ValueError("authority query did not resolve the unknown outcome")
    return MappingProxyType(
        {
            **dict(state),
            "outcome": outcome,
            "recovery_state": "VERIFIED",
            "exposure_blocked": kill_switch_active,
            "new_mutation_allowed": not kill_switch_active,
            "mutation_attempts": 1,
            "authority_queries": 1 if state["outcome"] == "unknown" else 0,
        }
    )


__all__ = []
