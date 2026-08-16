"""Composition of governed Trading mutations behind the API boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from app.services.trading import (
    cancel_all_orders,
    cancel_order,
    close_position,
    create_trading_dependencies,
    create_trading_request,
    submit_order,
)

type AuthContext = Any
type _MutationOperation = Callable[[str, object, AuthContext], Awaitable[object]]
type _PreflightOperation = Callable[[object, AuthContext], Awaitable[object]]

_ACCOUNT_SNAPSHOT_MAX_AGE_SECONDS = 30


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
            ``execution_route`` and
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
            "cancel_all_orders": cancel_all_orders,
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
    ``route`` contradicts the deployment it is running in, so a demo
    deployment can never relay a live-routed command
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
    declared_route = getattr(boundary_request, "route", None)
    expected_route = getattr(policy, "execution_route", None)

    if declared_route is None or expected_route in (None, "none"):
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISSING")
    if declared_route != expected_route:
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISMATCH")
    if declared_route == "live" and not getattr(policy, "allow_live_mutations", False):
        raise RuntimeError("TRADING_LIVE_MUTATIONS_DISABLED")


def _resolve_approval_signing_key(request_id: str) -> bytes:
    """Resolve the real, encrypted-at-rest Risk approval-token signing key.

    Returns:
        Raw signing key bytes.

    Raises:
        ValueError: If the credential slot has not been configured yet.
    """
    from app.services.api.composition.runtime_settings import build_credential_key_set
    from app.services.api.identity import resolve_credential_reference
    from app.services.api.workstation.settings.bootstrap import get_api_settings
    from app.utils import derive_stable_id

    reference_id = derive_stable_id("id", "api-credential:system:risk_approval_signing")
    material = resolve_credential_reference(
        f"secret://{reference_id}",
        owner_id="system",
        key_set=build_credential_key_set(get_api_settings()),
        request_id=request_id,
    )
    signing_key = material.get("signing_key")
    if signing_key is None:
        raise ValueError("risk approval signing key is not configured")
    return signing_key.get_secret_value().encode("utf-8")


def build_trading_preflight_source() -> _PreflightOperation:
    """Build one manual-order Risk preflight dispatcher.

    Connects a real broker adapter, reads a real account snapshot, and
    reviews the candidate order through Risk's genuine fixed-precedence gate
    (``app.services.risk.review_manual_order``). Live routing is refused
    deterministically: no verified live ``RiskConfig`` exists in this
    deployment yet (AGENTS.md section 3, "No Live Action by Default").

    Returns:
        Async route operation producing a real Risk decision/verdict pair.

    Raises:
        RuntimeError: If the route is live, or the broker/account snapshot
            is unavailable.
    """

    async def _preflight(boundary_request: object, auth: AuthContext) -> object:
        """Review one candidate order and return its real decision/verdict.

        Returns:
            A mapping matching ``OrderPreflightResponse``.

        Raises:
            RuntimeError: If live routing is requested or evidence is
                unavailable.
        """
        from app.services.brokers import create_connected_broker, disconnect_broker
        from app.services.data import (
            build_account_snapshot_request,
            get_account_state_snapshot,
        )
        from app.services.risk import (
            build_personal_account_risk_config,
            review_manual_order,
        )

        request = cast("Any", boundary_request)
        if request.route == "live":
            raise RuntimeError("MANUAL_ORDER_LIVE_NOT_CONFIGURED")

        adapter = await create_connected_broker("mt5")
        try:
            snapshot_response = get_account_state_snapshot(
                build_account_snapshot_request(
                    source_id="mt5",
                    account_id=request.account_id,
                    max_age_seconds=_ACCOUNT_SNAPSHOT_MAX_AGE_SECONDS,
                    request_id=request.request_id,
                ),
                adapter,
            )
        finally:
            await disconnect_broker(adapter)
        if snapshot_response.status != "success" or snapshot_response.data is None:
            raise RuntimeError("ACCOUNT_SNAPSHOT_UNAVAILABLE")

        decision, verdict = cast(
            "tuple[Any, Any]",
            review_manual_order(
                account_snapshot=snapshot_response.data,
                proposal_symbol=request.symbol,
                proposal_side=request.side,
                proposal_order_type=request.order_type,
                proposal_quantity=request.quantity,
                proposal_current_price=request.current_price,
                proposal_stop_distance=request.stop_distance,
                portfolio_id=request.portfolio_id,
                route=request.route,
                risk_config=build_personal_account_risk_config(),
                secret_resolver=lambda _ref: _resolve_approval_signing_key(
                    request.request_id
                ),
                auth=auth,
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
            ),
        )
        return {
            "state": decision.state.value,
            "risk_decision_id": decision.decision_id,
            "action_policy_verdict_id": verdict.verdict_id
            if verdict is not None
            else None,
            "approval_token_ref": decision.token.token_id
            if decision.token is not None
            else None,
            "reasons": tuple(decision.composite_breach_flags),
            "expires_at": decision.expires_at,
        }

    return _preflight


async def _authorize_cancellation(
    boundary_request: object,
    auth: AuthContext,
    *,
    action: str,
    action_scope: dict[str, str],
) -> object:
    """Connect a real broker, read a real snapshot, and authorize one cancellation.

    Shared by the single-order and bulk cancel-all preflight dispatchers —
    both authorize through the same real Risk current-state gate
    (``app.services.risk.review_cancel_authorization``); only the action
    identity and its extra scope differ.

    Returns:
        A mapping matching ``OrderPreflightResponse``/``CancelAllPreflightResponse``.

    Raises:
        RuntimeError: If live routing is requested or evidence is unavailable.
    """
    from app.services.brokers import create_connected_broker, disconnect_broker
    from app.services.data import (
        build_account_snapshot_request,
        get_account_state_snapshot,
    )
    from app.services.risk import (
        build_personal_account_risk_config,
        review_cancel_authorization,
    )

    request = cast("Any", boundary_request)
    if request.route == "live":
        raise RuntimeError("MANUAL_ORDER_LIVE_NOT_CONFIGURED")

    adapter = await create_connected_broker("mt5")
    try:
        snapshot_response = get_account_state_snapshot(
            build_account_snapshot_request(
                source_id="mt5",
                account_id=request.account_id,
                max_age_seconds=_ACCOUNT_SNAPSHOT_MAX_AGE_SECONDS,
                request_id=request.request_id,
            ),
            adapter,
        )
    finally:
        await disconnect_broker(adapter)
    if snapshot_response.status != "success" or snapshot_response.data is None:
        raise RuntimeError("ACCOUNT_SNAPSHOT_UNAVAILABLE")

    decision, verdict = cast(
        "tuple[Any, Any]",
        review_cancel_authorization(
            account_snapshot=snapshot_response.data,
            representative_symbol=request.representative_symbol,
            action=action,
            action_scope=action_scope,
            portfolio_id=request.portfolio_id,
            risk_config=build_personal_account_risk_config(),
            secret_resolver=lambda _ref: _resolve_approval_signing_key(
                request.request_id
            ),
            auth=auth,
            request_id=request.request_id,
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
        ),
    )
    return {
        "state": decision.state.value,
        "risk_decision_id": decision.decision_id,
        "action_policy_verdict_id": verdict.verdict_id if verdict is not None else None,
        "approval_token_ref": decision.token.token_id
        if decision.token is not None
        else None,
        "reasons": tuple(decision.composite_breach_flags),
        "expires_at": decision.expires_at,
    }


def build_trading_cancel_order_preflight_source() -> _PreflightOperation:
    """Build one single-order cancellation Risk preflight dispatcher.

    A working order's own original submit-scoped approval token is not
    preserved once consumed, so cancelling it needs its own real
    authorization rather than reusing that stale reference.

    Returns:
        Async route operation producing a real Risk decision/verdict pair.

    Raises:
        RuntimeError: If the route is live, or the broker/account snapshot
            is unavailable.
    """

    async def _preflight(boundary_request: object, auth: AuthContext) -> object:
        """Authorize one candidate single-order cancellation.

        Returns:
            A mapping matching ``OrderPreflightResponse``.

        Raises:
            RuntimeError: If live routing is requested or evidence is
                unavailable.
        """
        request = cast("Any", boundary_request)
        return await _authorize_cancellation(
            request,
            auth,
            action="cancel_order",
            action_scope={"target_broker_order_id": request.target_broker_order_id},
        )

    return _preflight


def build_trading_cancel_all_preflight_source() -> _PreflightOperation:
    """Build one bulk cancel-all-orders Risk preflight dispatcher.

    Connects a real broker adapter, reads a real account snapshot, and
    authorizes the bulk cancellation through Risk's genuine current-state gate
    (``app.services.risk.review_cancel_authorization``). Live routing is
    refused deterministically, matching ``build_trading_preflight_source``.

    Returns:
        Async route operation producing a real Risk decision/verdict pair.

    Raises:
        RuntimeError: If the route is live, or the broker/account snapshot
            is unavailable.
    """

    async def _preflight(boundary_request: object, auth: AuthContext) -> object:
        """Authorize one candidate bulk cancellation and return its real outcome.

        Returns:
            A mapping matching ``CancelAllPreflightResponse``.

        Raises:
            RuntimeError: If live routing is requested or evidence is
                unavailable.
        """
        request = cast("Any", boundary_request)
        return await _authorize_cancellation(
            request, auth, action="cancel_all_orders", action_scope={}
        )

    return _preflight


__all__ = (
    "build_api_trading_dependencies",
    "build_trading_cancel_all_preflight_source",
    "build_trading_cancel_order_preflight_source",
    "build_trading_mutation_source",
    "build_trading_preflight_source",
)
