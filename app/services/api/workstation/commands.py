"""Optimistic, fail-closed workstation command delegation."""

from __future__ import annotations

from collections.abc import Callable, Mapping


def execute_workstation_command(
    command: Mapping[str, object],
    *,
    current_version: int,
    owner_handler: Callable[[Mapping[str, object]], object],
) -> Mapping[str, object]:
    """Validate expected version and delegate exactly once to the owner.

    Returns:
        Stable accepted, rejected, or unknown outcome.
    """
    expected = command.get("expected_version")
    if not isinstance(expected, int):
        return {
            "status": "rejected",
            "reason": "EXPECTED_VERSION_REQUIRED",
            "retryable": False,
        }
    if expected != current_version:
        return {
            "status": "rejected",
            "reason": "STALE_WORKSTATION_VERSION",
            "retryable": True,
            "current_version": current_version,
        }
    if not command.get("idempotency_key") or not command.get("correlation_id"):
        return {
            "status": "rejected",
            "reason": "COMMAND_EVIDENCE_REQUIRED",
            "retryable": False,
        }
    result = owner_handler(command)
    if result is None:
        return {
            "status": "unknown",
            "reason": "OWNER_RESULT_AMBIGUOUS",
            "retryable": False,
        }
    return {
        "status": "accepted",
        "result": result,
        "correlation_id": command["correlation_id"],
    }
