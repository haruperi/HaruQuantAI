"""Composition of governed Trading mutations behind the API boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from app.services.trading import (
    cancel_order,
    close_position,
    create_trading_dependencies,
    create_trading_request,
    submit_order,
)

type AuthContext = Any
type _MutationOperation = Callable[[str, object, AuthContext], Awaitable[object]]


def build_api_trading_dependencies(**values: object) -> object:
    """Build a complete Trading-owned dependency container.

    Args:
        **values: Exact Trading state, broker, Risk, evidence, and lifecycle ports.

    Returns:
        Opaque dependency container accepted by Trading mutation functions.
    """
    return create_trading_dependencies(**values)


def build_trading_mutation_source(
    dependencies: object | None,
    *,
    runtime_policy: object | None = None,
) -> _MutationOperation:
    """Build one governed Trading mutation dispatcher.

    Args:
        dependencies: Complete Trading-owned dependency container.
        runtime_policy: Validated gateway runtime settings carrying
            ``runtime_profile``, ``execution_route``, and
            ``allow_live_mutations``. When supplied, every mutation is checked
            against it before delegation; when omitted the check is skipped and
            Trading's own gates remain the only authority.

    Returns:
        Async route operation delegating exclusively to Trading public functions.
    """

    async def _mutate(
        operation: str, boundary_request: object, _auth: AuthContext
    ) -> object:
        """Validate and delegate one governed mutation.

        Returns:
            Trading-owned mutation receipt.

        Raises:
            RuntimeError: If Trading dependencies are unavailable or the request
                does not match the composed runtime policy.
            ValueError: If the requested operation is unsupported.
        """
        if dependencies is None:
            raise RuntimeError("TRADING_MUTATIONS_UNAVAILABLE")
        _enforce_runtime_policy(runtime_policy, boundary_request)
        request = create_trading_request(
            **cast("Any", boundary_request).model_dump(mode="python", warnings=False)
        )
        operations = {
            "submit_order": submit_order,
            "cancel_order": cancel_order,
            "close_position": close_position,
        }
        try:
            selected = operations[operation]
        except KeyError as error:
            raise ValueError("unsupported Trading mutation") from error
        return await selected(request, cast("Any", dependencies))

    return _mutate


def _enforce_runtime_policy(policy: object | None, boundary_request: object) -> None:
    """Reject a mutation whose declared runtime disagrees with the deployment.

    The gateway does not decide whether a trade is safe — Trading and Risk do.
    What it can do is refuse to forward a request whose own declared
    ``runtime_profile`` or ``execution_route`` contradicts the deployment it is
    running in, so a paper deployment can never relay a live-routed command
    even if a caller asks for one. Live routing additionally requires
    ``allow_live_mutations``, matching the settings-level rule in
    ``_settings.py`` and AGENTS.md section 3.

    Args:
        policy: Validated gateway runtime settings, or ``None`` when no policy
            was composed.
        boundary_request: Validated Trading mutation boundary DTO.

    Raises:
        RuntimeError: If the request contradicts the composed runtime policy.
    """
    if policy is None:
        return
    declared_profile = getattr(boundary_request, "runtime_profile", None)
    declared_route = getattr(boundary_request, "execution_route", None)
    expected_profile = getattr(policy, "runtime_profile", None)
    expected_route = getattr(policy, "execution_route", None)

    if declared_profile is not None and declared_profile != expected_profile:
        raise RuntimeError("TRADING_RUNTIME_PROFILE_MISMATCH")
    if declared_route is not None and declared_route != expected_route:
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISMATCH")
    if declared_route == "live" and not getattr(policy, "allow_live_mutations", False):
        raise RuntimeError("TRADING_LIVE_MUTATIONS_DISABLED")


__all__ = ("build_api_trading_dependencies", "build_trading_mutation_source")
