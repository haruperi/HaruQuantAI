"""Composition of the governed Risk kill-switch command behind the API boundary.

Risk is the sole kill-switch authority. ``apply_kill_switch_command`` requires
seven receiver-owned collaborators — an approval-token service, an audit chain,
a state store, and the Risk configuration among them — none of which the gateway
may construct implicitly or substitute a default for. This module accepts the
complete bundle as an explicit composition dependency and exposes one dispatcher
that reads the current canonical state, forwards the command, and returns the
Risk-authored result.

The canonical application binds ``risk.command_source`` to ``None`` by default,
so the command route fails closed (HTTP 503) until a bundle is supplied via
``create_app(..., risk_dependencies=...)``. This honours "No Live Action by
Default": a deployment that has not deliberately composed kill-switch authority
cannot mutate safety state over HTTP. Kill-switch *reads* are unaffected.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast

from app.kernel.time import utc_now
from app.services.risk import (
    apply_kill_switch_command,
    create_kill_switch_command,
    get_kill_switch_state,
)

type AuthContext = Any
type _RiskOperation = Callable[..., object]

_REQUIRED_PORTS = ("approvals", "audit", "store", "config")


def build_api_risk_dependencies(
    *,
    approvals: object,
    audit: object,
    store: object,
    config: object,
) -> object:
    """Build the Risk kill-switch receiver-owned dependency bundle.

    Args:
        approvals: Risk-owned approval-token service.
        audit: Risk-owned audit chain.
        store: Risk-owned kill-switch state store.
        config: Risk-owned configuration value.

    Returns:
        Opaque bundle accepted by the Risk command dispatcher.
    """
    return {
        "approvals": approvals,
        "audit": audit,
        "store": store,
        "config": config,
    }


def build_risk_command_source(bundle: object | None) -> _RiskOperation:
    """Build one Risk kill-switch command dispatcher.

    Args:
        bundle: Composed Risk dependency bundle, or ``None`` when the canonical
            application has not composed kill-switch command authority.

    Returns:
        Route operation dispatcher bound to the composed bundle.
    """

    def _operation(operation: str, *args: object) -> object:
        """Apply one governed kill-switch command through Risk.

        Args:
            operation: Canonical operation name; only ``kill_switch`` is
                registered.
            *args: ``(boundary_request, auth_context, attestation)`` inputs.

        Returns:
            Risk-authored canonical kill-switch state.

        Raises:
            RuntimeError: If no Risk command bundle is composed or the bundle is
                missing a required port.
            ValueError: If the requested operation is not registered.
        """
        if operation != "kill_switch":
            raise ValueError("unsupported Risk operation")
        if bundle is None:
            raise RuntimeError("RISK_COMMAND_RUNTIME_UNAVAILABLE")
        ports = cast("Mapping[str, object]", bundle)
        if any(ports.get(name) is None for name in _REQUIRED_PORTS):
            raise RuntimeError("RISK_COMMAND_RUNTIME_UNAVAILABLE")

        boundary = cast("Any", args[0])
        auth_context = cast("AuthContext", args[1])
        attestation = args[2]
        current = get_kill_switch_state(boundary.scope_level, dict(boundary.scope))
        if current is None:
            raise RuntimeError("KILL_SWITCH_STATE_UNAVAILABLE")
        command = create_kill_switch_command(**dict(boundary.command))
        return apply_kill_switch_command(
            command,
            cast("Any", current),
            auth_context,
            cast("Any", ports["approvals"]),
            cast("Any", ports["audit"]),
            cast("Any", ports["store"]),
            cast("Any", ports["config"]),
            attestation=cast("Any", attestation),
            now=utc_now(),
        )

    return _operation


__all__ = ("build_api_risk_dependencies", "build_risk_command_source")
