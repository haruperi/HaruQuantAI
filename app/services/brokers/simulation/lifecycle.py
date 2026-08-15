"""Lifecycle delegation and local-state synchronization helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.brokers.canonical_contracts import BrokerConnectionState

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts import StandardResponse


def lifecycle_state_from_response(
    operation: str, response: StandardResponse[object]
) -> BrokerConnectionState | None:
    """Derive local guard state from one authoritative lifecycle response.

    Args:
        operation: Canonical lifecycle operation name.
        response: Authority response returned for that operation.

    Returns:
        State to retain locally, or ``None`` when the response cannot prove one.
    """
    if response.status != "success":
        return BrokerConnectionState.FAILED
    if operation in {"connect", "reconnect"}:
        return BrokerConnectionState.READY
    if operation in {"disconnect", "finalize_session"}:
        return BrokerConnectionState.DISCONNECTED
    status = response.data
    if operation == "get_connection_status" and status is not None:
        candidate = getattr(status, "state", None)
        if isinstance(candidate, BrokerConnectionState):
            return candidate
    return None


__all__ = ("lifecycle_state_from_response",)
