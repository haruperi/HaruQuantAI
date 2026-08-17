"""Composition of governed Trading mutations behind the API boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Final, cast

from app.services.api.identity import get_username_for_principal
from app.services.api.workstation.settings.account_mode import resolve_execution_route
from app.services.api.workstation.trading.schemas import TradingAccountProfileResponse
from app.services.trading import (
    cancel_all_orders,
    cancel_order,
    close_position,
    create_trading_dependencies,
    create_trading_request,
    list_execution_sessions,
    resolve_active_execution_session,
    submit_order,
)
from app.utils import generate_id, get_logger, utc_now

logger = get_logger(__name__)

type AuthContext = Any
type _MutationOperation = Callable[[str, object, AuthContext], Awaitable[object]]
type _PreflightOperation = Callable[[object, AuthContext], Awaitable[object]]
type _AccountProfileOperation = Callable[[AuthContext], Awaitable[object]]
type _ModeBrokerConnector = Callable[[str], Awaitable[object]]

_ACCOUNT_SNAPSHOT_MAX_AGE_SECONDS = 30
_PLATFORM_MODE_BY_ROUTE: Final = MappingProxyType(
    {"sim": "SIMULATION", "demo": "DEMO", "live": "REAL"}
)


def _field(value: object, name: str, default: object = None) -> object:
    """Read one public mapping or attribute field.

    Returns:
        Requested field value or the supplied default.
    """
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _read_simulation_account_state(
    request: object,
) -> tuple[object, Any, dict[str, str]]:
    """Build Data-owned account evidence from one historical session snapshot.

    Returns:
        Account snapshot, replay timestamp, and immutable replay identity refs.

    Raises:
        RuntimeError: If the session or its current replay evidence is absent.
    """
    from datetime import timedelta

    from app.services.data import build_account_state_snapshot
    from app.services.simulator import read_live_simulation_state

    session_id = getattr(request, "simulation_session_id", None)
    if not isinstance(session_id, str) or not session_id:
        raise RuntimeError("SIMULATION_SESSION_REQUIRED")
    response = cast("Any", read_live_simulation_state(session_id))
    if response.status != "success" or response.data is None:
        raise RuntimeError("SIMULATION_SESSION_UNAVAILABLE")
    state = cast("Any", response.data)
    replay_time = state.get("replay_timestamp")
    if replay_time is None:
        raise RuntimeError("SIMULATION_REPLAY_CURSOR_UNAVAILABLE")
    engine = cast("Any", state["account_state"])
    account = cast("Any", engine["account"])
    positions = tuple(
        {
            "position_id": str(_field(item, "position_id")),
            "symbol": str(_field(item, "symbol")),
            "side": (
                "LONG"
                if str(_field(item, "side")).upper() in {"BUY", "LONG"}
                else "SHORT"
            ),
            "quantity": _field(item, "quantity"),
            "entry_price": _field(item, "entry_price"),
        }
        for item in engine["positions"]
    )
    orders = tuple(
        {
            "order_id": str(_field(item, "client_order_id")),
            "symbol": str(_field(item, "symbol")),
            "side": str(_field(item, "side")),
            "state": "pending",
            "quantity": _field(item, "approved_volume"),
            "price": _field(item, "price") or _field(item, "stop_price"),
        }
        for item in engine["pending_orders"]
    )
    snapshot = build_account_state_snapshot(
        account_id=cast("Any", request).account_id,
        currency=str(account["account_currency"]),
        balances=(
            {
                "asset": str(account["account_currency"]),
                "total": account["balance"],
                "available": account["free_margin"],
            },
        ),
        equity=account["equity"],
        margin_used=account["used_margin"],
        margin_available=account["free_margin"],
        positions=positions,
        orders=orders,
        connected=True,
        trading_allowed=not bool(state["complete"]),
        source_id="simulator",
        snapshot_at=replay_time,
        expires_at=replay_time + timedelta(seconds=_ACCOUNT_SNAPSHOT_MAX_AGE_SECONDS),
        request_id=cast("Any", request).request_id,
    )
    refs = {
        "simulation_session_id": session_id,
        "dataset_revision": str(state["dataset_revision"]),
        "replay_cursor": str(state["cursor"]),
    }
    return snapshot, replay_time, refs


def build_api_trading_dependencies(**values: object) -> object:
    """Build a complete Trading-owned dependency container.

    Args:
        **values: Exact Trading state, broker, Risk, evidence, and lifecycle ports.

    Returns:
        Opaque dependency container accepted by Trading mutation functions.
    """
    return create_trading_dependencies(**values)


def build_simulation_execution_source() -> Callable[[object], Awaitable[object]]:
    """Bind Trading's direct SIM port to a historical Simulator session.

    Returns:
        Async operation accepting one unchanged Trading OrderIntent.
    """

    async def _execute(intent: object) -> object:
        """Submit one exact intent to its explicitly selected session.

        Returns:
            Simulator-produced Trading execution receipt.

        Raises:
            RuntimeError: If no simulation session identity is supplied or the
                Simulator refuses the session-bound mutation.
        """
        from app.services.simulator import submit_live_simulation_order

        session_id = getattr(intent, "simulation_session_id", None)
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError("SIMULATION_SESSION_REQUIRED")
        response = cast("Any", await submit_live_simulation_order(session_id, intent))
        if response.status != "success" or response.data is None:
            raise RuntimeError("SIMULATION_EXECUTION_REFUSED")
        return response.data

    return _execute


def build_trading_mutation_source(
    dependencies: object | None,
    *,
    runtime_policy: object | None = None,
) -> _MutationOperation:
    """Build one governed Trading mutation dispatcher.

    Args:
        dependencies: Complete Trading-owned dependency container.
        runtime_policy: Validated gateway runtime settings. When supplied,
            every mutation's declared route is checked against the active
            account mode before delegation; when omitted the check is skipped
            and Trading's own gates remain the only authority.

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
        await _require_platform_mode_match(cast("Any", boundary_request).route)
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
    What it can do is refuse to forward a request whose own declared ``route``
    contradicts the mode the application is actually in, so a request can never
    elect its own execution context.

    That mode is the operator-selected ``ACCOUNT_MODE``, not bootstrap
    configuration. No separate live-enablement flag is consulted: Risk is the
    sole authority on whether any order - manual or automatic - may proceed,
    and demo versus live is decided by which credentials the operator supplied.

    Args:
        policy: Validated gateway runtime settings, or ``None`` when no policy
            was composed.
        boundary_request: Validated Trading mutation boundary DTO.

    Raises:
        RuntimeError: If the request contradicts the active account mode.
    """
    if policy is None:
        return
    declared_route = getattr(boundary_request, "route", None)
    if declared_route is None:
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISSING")
    if declared_route != resolve_execution_route(request_id=generate_id("req")):
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISMATCH")


# The elected account mode names both the Risk profile the policy is scoped to
# and the route it is compatible with. Trading calls the virtual profile
# `simulation` where the route names it `sim`.
_RISK_PROFILE_BY_ROUTE: Final = MappingProxyType(
    {"sim": "simulation", "demo": "demo", "live": "live"}
)


async def _connect_mode_broker(route: str) -> object:
    """Connect the broker the active account mode actually executes through.

    Demo and live are the same MT5 execution path and differ only by the
    credentials the operator supplied. Because they are the same path, the
    label and the credentials have to agree: relaying a demo-credentialled
    order while stamping it live - or the reverse - would make the registry
    marking that separates them a lie. A mismatch therefore fails closed.

    Args:
        route: Execution route of the active account mode.

    Returns:
        Connected broker adapter for the active mode.

    Raises:
        RuntimeError: If the configured MT5 environment contradicts the elected
            mode, or the sim venue is requested but not composed.
    """
    from app.services.brokers import (
        create_connected_broker,
        resolve_provider_connection_config,
    )

    if route == "sim":
        # The sim route requires a Brokers `sim`/`simulation` authority that no
        # production component implements yet, so it is refused rather than
        # silently served by a real broker.
        raise RuntimeError("SIM_EXECUTION_VENUE_UNAVAILABLE")
    wants_live = route == "live"
    config = resolve_provider_connection_config("mt5", allow_live=wants_live)
    if (str(config.environment) == "live") != wants_live:
        logger.error("Configured MT5 environment contradicts the elected mode")
        raise RuntimeError("ACCOUNT_MODE_CREDENTIAL_MISMATCH")
    return await create_connected_broker("mt5", allow_live=wants_live)


async def _read_platform_trade_mode(route: str) -> str:
    """Read the execution venue's provider-authored mode.

    Args:
        route: Operator-selected execution route.

    Returns:
        Canonical provider trade mode.

    Raises:
        RuntimeError: If provider mode evidence is unavailable or malformed.
    """
    if route == "sim":
        return "SIMULATION"
    from app.services.brokers import disconnect_broker, get_broker_account_info

    adapter = await _connect_mode_broker(route)
    try:
        response = cast("Any", await get_broker_account_info(cast("Any", adapter)))
        if response.status != "success" or response.data is None:
            raise RuntimeError("TRADING_ACCOUNT_PROFILE_UNAVAILABLE")
        details = cast("Any", response.data).details
        trade_mode = (
            details.get("trade_mode")
            if callable(getattr(details, "get", None))
            else None
        )
        if trade_mode not in {"DEMO", "REAL", "CONTEST"}:
            raise RuntimeError("TRADING_ACCOUNT_PROFILE_MALFORMED")
        return cast("str", trade_mode)
    finally:
        await disconnect_broker(cast("Any", adapter))


async def _require_platform_mode_match(route: str) -> None:
    """Fail closed unless selected and provider-authored modes agree.

    Raises:
        RuntimeError: If platform evidence is unavailable or does not match.
    """
    actual = await _read_platform_trade_mode(route)
    if actual != _PLATFORM_MODE_BY_ROUTE.get(route):
        logger.error("Provider-authored account mode contradicts the elected mode")
        raise RuntimeError("ACCOUNT_MODE_PLATFORM_MISMATCH")


def build_trading_account_profile_source(
    connect_mode_broker: _ModeBrokerConnector | None = None,
) -> _AccountProfileOperation:
    """Build the active mode's provider-authored account identity read.

    Returns:
        Async operation returning the minimal Header account profile.
    """

    async def _read(auth: AuthContext) -> object:
        """Read the active account name and execution environment.

        Returns:
            Validated minimal account-profile response.

        Raises:
            RuntimeError: If MT5 identity is unavailable.
            TypeError: If MT5 account details are structurally malformed.
        """
        route = resolve_execution_route(request_id=generate_id("req"))
        session = resolve_active_execution_session(
            principal_id=auth.principal_id,
            environment_id=auth.tenant_or_environment,
            mode=route,
        )
        if session is None:
            candidates = list_execution_sessions(
                principal_id=auth.principal_id,
                environment_id=auth.tenant_or_environment,
                mode=route,
            )
            session = next(
                (item for item in candidates if getattr(item, "is_default", False)),
                None,
            )
        session_name = (
            None if session is None else str(getattr(session, "name", "")).strip()
        ) or None
        if route == "sim":
            username = get_username_for_principal(
                auth.principal_id, request_id=generate_id("req")
            )
            balance_value = getattr(session, "sim_initial_balance", None)
            leverage_value = getattr(session, "sim_leverage", None)
            currency_value = getattr(session, "sim_account_currency", None)
            configuration_complete = session is not None and all(
                getattr(session, field, None)
                for field in (
                    "provider_account_ref",
                    "simulation_session_id",
                    "dataset_ref",
                    "dataset_revision",
                    "dataset_hash",
                )
            )
            return TradingAccountProfileResponse(
                account_name=username,
                session_name=session_name,
                trade_mode="SIMULATION",
                selected_mode="sim",
                mode_compatible=configuration_complete,
                environment_label="Simulation Environment",
                source="simulator",
                currency=currency_value,
                balance=balance_value,
                equity=balance_value,
                profit=Decimal(0) if balance_value is not None else None,
                margin=Decimal(0) if balance_value is not None else None,
                free_margin=balance_value,
                margin_level=None,
                leverage=leverage_value,
                retrieved_at=utc_now(),
            )
        from app.services.brokers import disconnect_broker, get_broker_account_info

        connector = connect_mode_broker or _connect_mode_broker
        adapter = await connector(route)
        try:
            response = cast("Any", await get_broker_account_info(cast("Any", adapter)))
            if response.status != "success" or response.data is None:
                raise RuntimeError("TRADING_ACCOUNT_PROFILE_UNAVAILABLE")
            account = cast("Any", response.data)
            details = account.details
            if not callable(getattr(details, "get", None)):
                raise TypeError("TRADING_ACCOUNT_PROFILE_MALFORMED")
            name = details.get("name")
            trade_mode = details.get("trade_mode")
            profit = details.get("profit")
            margin_level = details.get("margin_level")
            leverage = details.get("leverage")
            if not isinstance(name, str) or not name.strip() or name == "N/A":
                raise RuntimeError("TRADING_ACCOUNT_PROFILE_MALFORMED")
            if trade_mode not in {"DEMO", "REAL", "CONTEST"}:
                raise RuntimeError("TRADING_ACCOUNT_PROFILE_MALFORMED")
            labels = {
                "DEMO": "Demo Environment",
                "REAL": "Live Environment",
                "CONTEST": "Contest Environment",
            }
            return TradingAccountProfileResponse(
                account_name=name.strip(),
                session_name=session_name,
                trade_mode=trade_mode,
                selected_mode=cast("Any", route),
                mode_compatible=trade_mode == _PLATFORM_MODE_BY_ROUTE[route],
                environment_label=labels[trade_mode],
                source="mt5",
                currency=account.currency,
                balance=account.balance,
                equity=account.equity,
                profit=None if profit is None else Decimal(str(profit)),
                margin=account.margin,
                free_margin=account.free_margin,
                margin_level=(
                    None if margin_level is None else Decimal(str(margin_level))
                ),
                leverage=None if leverage is None else Decimal(str(leverage)),
                retrieved_at=account.retrieved_at,
            )
        finally:
            await disconnect_broker(cast("Any", adapter))

    return _read


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
    (``app.services.risk.review_manual_order``). Every route is reviewed the
    same way: Risk is the sole authority on whether an order may proceed, so
    no route is refused ahead of that review.

    Returns:
        Async route operation producing a real Risk decision/verdict pair.

    Raises:
        RuntimeError: If the broker or account snapshot is unavailable.
    """

    async def _preflight(boundary_request: object, auth: AuthContext) -> object:
        """Review one candidate order and return its real decision/verdict.

        Returns:
            A mapping matching ``OrderPreflightResponse``.

        Raises:
            RuntimeError: If required account or approval evidence is
                unavailable. Live routing is not refused here; Risk is the
                sole authority on whether the order may proceed.
        """
        from app.services.brokers import disconnect_broker
        from app.services.data import (
            build_account_snapshot_request,
            get_account_state_snapshot,
        )
        from app.services.risk import (
            build_personal_account_risk_config,
            review_manual_order,
        )

        request = cast("Any", boundary_request)
        await _require_platform_mode_match(request.route)

        replay_time = None
        replay_refs = None
        if request.route == "sim":
            account_snapshot, replay_time, replay_refs = _read_simulation_account_state(
                request
            )
        else:
            adapter = await _connect_mode_broker(request.route)
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
                await disconnect_broker(cast("Any", adapter))
            if snapshot_response.status != "success" or snapshot_response.data is None:
                raise RuntimeError("ACCOUNT_SNAPSHOT_UNAVAILABLE")
            account_snapshot = snapshot_response.data

        decision, verdict = cast(
            "tuple[Any, Any]",
            review_manual_order(
                account_snapshot=account_snapshot,
                proposal_symbol=request.symbol,
                proposal_side=request.side,
                proposal_order_type=request.order_type,
                proposal_quantity=request.quantity,
                proposal_current_price=request.current_price,
                proposal_stop_distance=request.stop_distance,
                portfolio_id=request.portfolio_id,
                route=request.route,
                risk_config=build_personal_account_risk_config(
                    _RISK_PROFILE_BY_ROUTE[request.route], request.route
                ),
                secret_resolver=lambda _ref: _resolve_approval_signing_key(
                    request.request_id
                ),
                auth=auth,
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
                market_evidence_time=replay_time,
                temporal_context=(
                    "historical_simulation" if request.route == "sim" else "runtime"
                ),
                historical_evidence_refs=replay_refs,
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
        RuntimeError: If required account or approval evidence is unavailable.
            Live routing is not refused here; Risk is the sole authority on
            whether the cancellation may proceed.
    """
    from app.services.brokers import disconnect_broker
    from app.services.data import (
        build_account_snapshot_request,
        get_account_state_snapshot,
    )
    from app.services.risk import (
        build_personal_account_risk_config,
        review_cancel_authorization,
    )

    request = cast("Any", boundary_request)
    await _require_platform_mode_match(request.route)

    adapter = await _connect_mode_broker(request.route)
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
        await disconnect_broker(cast("Any", adapter))
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
            risk_config=build_personal_account_risk_config(
                _RISK_PROFILE_BY_ROUTE[request.route], request.route
            ),
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
            RuntimeError: If required account or approval evidence is
                unavailable. Live routing is not refused here; Risk is the
                sole authority on whether the order may proceed.
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
            RuntimeError: If required account or approval evidence is
                unavailable. Live routing is not refused here; Risk is the
                sole authority on whether the order may proceed.
        """
        request = cast("Any", boundary_request)
        return await _authorize_cancellation(
            request, auth, action="cancel_all_orders", action_scope={}
        )

    return _preflight


__all__ = (
    "build_api_trading_dependencies",
    "build_simulation_execution_source",
    "build_trading_account_profile_source",
    "build_trading_cancel_all_preflight_source",
    "build_trading_cancel_order_preflight_source",
    "build_trading_mutation_source",
    "build_trading_preflight_source",
)
