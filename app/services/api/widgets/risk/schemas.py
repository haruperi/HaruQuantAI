"""Risk gateway request schemas."""

from collections.abc import Mapping
from typing import Any, Literal

from app.services.api.contracts.models import _BaseApiContract


class KillSwitchCommandRequest(_BaseApiContract):
    """Operator kill-switch command projection.

    Risk remains the sole kill-switch authority. The gateway authenticates a
    human operator, requires a distinct-principal approval, and forwards the
    command; it never computes, overrides, or clears canonical safety state.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.kill_switch_command_request.v1"] = (
        "api.kill_switch_command_request.v1"
    )
    scope_level: str
    scope: Mapping[str, str]
    command: Mapping[str, object]
    attestation: Mapping[str, Any] | None = None


__all__ = ("KillSwitchCommandRequest",)
