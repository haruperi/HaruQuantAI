"""Authenticated Trading session and governed mutation HTTP boundaries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api.identity import (
    get_username_for_principal,
    require_auth_context,
    require_human_permission,
    run_idempotent_write_async,
)
from app.services.api.workstation.markets import resolve_runtime_source_id
from app.services.api.workstation.settings.account_mode import resolve_execution_route
from app.services.api.workstation.trading.schemas import (
    CancelAllPreflightRequest,
    CancelOrderPreflightRequest,
    ExecutionSessionActionRequest,
    ExecutionSessionConfigurationRequest,
    ExecutionSessionCreateRequest,
    ExecutionSessionUpdateRequest,
    OrderPreflightRequest,
    TradingInstrumentConstraintsResponse,
    TradingMutationRequest,
)
from app.services.brokers import get_broker_capability_catalogue
from app.services.data import (
    build_symbol_metadata_request,
    get_symbol_metadata,
    list_verified_datasets,
)
from app.services.trading import (
    archive_execution_session,
    assign_simulation_session_identity,
    complete_simulation_session_configuration,
    create_execution_session,
    get_execution_session,
    get_execution_session_events,
    list_execution_sessions,
    set_default_execution_session,
    start_execution_session,
    stop_execution_session,
    update_execution_session_metadata,
)
from app.utils import generate_id

type AuthContext = Any
type _SessionSource = Callable[[str, str, str, AuthContext], object | None]
type _MutationSource = Callable[[str, object, AuthContext], Awaitable[object]]
type _PreflightSource = Callable[[object, AuthContext], Awaitable[object]]
type _AccountProfileSource = Callable[[AuthContext], Awaitable[object]]


def _positive_decimal_or_none(metadata: object, *names: str) -> Decimal | None:
    """Read the first positive provider decimal, preserving missingness.

    Args:
        metadata: Provider-authored metadata object.
        *names: Candidate provider field names in priority order.

    Returns:
        The first positive finite decimal, otherwise ``None``.
    """
    for name in names:
        value = getattr(metadata, name, None)
        if isinstance(value, bool) or value is None:
            continue
        try:
            decimal_value = Decimal(str(value))
        except InvalidOperation, ValueError:
            continue
        if decimal_value.is_finite() and decimal_value > 0:
            return decimal_value
    return None


def _nonnegative_int_or_none(value: object) -> int | None:
    """Preserve one provider-authored non-negative integer when valid.

    Args:
        value: Candidate provider value.

    Returns:
        The integer, otherwise ``None``.
    """
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else None
    )


def _available_text_or_none(value: object) -> str | None:
    """Preserve one available provider text value when valid.

    Args:
        value: Candidate provider value.

    Returns:
        Trimmed provider text, otherwise ``None``.
    """
    if (
        not isinstance(value, str)
        or not value.strip()
        or "not available" in value.lower()
    ):
        return None
    return value.strip()


router = APIRouter(prefix="/api/v1/trading", tags=["trading"])

# A request whose declared runtime contradicts the deployment is a caller
# error, not an outage: it is refused deterministically rather than reported
# as an unavailable dependency.
_RUNTIME_POLICY_REFUSALS = frozenset(
    {
        "TRADING_RUNTIME_PROFILE_MISMATCH",
        "TRADING_EXECUTION_ROUTE_MISMATCH",
        "TRADING_LIVE_MUTATIONS_DISABLED",
        "ACCOUNT_MODE_PLATFORM_MISMATCH",
    }
)


def _trading_session_source() -> _SessionSource:
    """Fail closed until composition injects aggregate Trading session reads.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_SESSION_UNAVAILABLE",
    )


def _trading_mutation_source() -> _MutationSource:
    """Fail closed until composition injects governed Trading execution.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_MUTATIONS_UNAVAILABLE",
    )


def _trading_preflight_source() -> _PreflightSource:
    """Fail closed until composition injects the real Risk preflight review.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_PREFLIGHT_UNAVAILABLE",
    )


def _trading_account_profile_source() -> _AccountProfileSource:
    """Fail closed until the MT5 account-profile reader is composed.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_ACCOUNT_PROFILE_UNAVAILABLE",
    )


def _trading_cancel_order_preflight_source() -> _PreflightSource:
    """Fail closed until composition injects the real single-cancel Risk review.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_CANCEL_ORDER_PREFLIGHT_UNAVAILABLE",
    )


def _trading_cancel_all_preflight_source() -> _PreflightSource:
    """Fail closed until composition injects the real bulk-cancel Risk review.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_CANCEL_ALL_PREFLIGHT_UNAVAILABLE",
    )


def _require_configured_route(route: str) -> None:
    """Require a request to name the route the application is currently in.

    Demo and live share one execution path and differ only by the credentials
    in the composed ``BrokerConnectionConfig``. The boundary therefore does not
    ban a route; it refuses a route the operator has not selected, so a request
    can never elect its own execution context.

    That route follows the operator-selected ``ACCOUNT_MODE`` rather than
    bootstrap configuration: selecting LIVE is what puts the application on the
    live route, and supplying live rather than demo credentials is what makes
    it a live account. ``ALLOW_LIVE_MUTATIONS`` is deliberately not consulted
    here - it governs the unattended background Trading loop, where no operator
    is present to elect the mode.

    Args:
        route: Execution route declared by the request.

    Raises:
        HTTPException: If the declared route is not the active route.
    """
    if route != resolve_execution_route(request_id=generate_id("req")):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EXECUTION_ROUTE_NOT_CONFIGURED",
        )


def _require_matching_idempotency_key(
    declared_key: str,
    idempotency_key: str | None,
) -> None:
    """Require the transport idempotency header to match the request body.

    Args:
        declared_key: Idempotency key declared inside the request body.
        idempotency_key: Idempotency key supplied as a transport header.

    Raises:
        HTTPException: If the header is absent or disagrees with the body.
    """
    if idempotency_key is None or idempotency_key != declared_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )


def _session_payload(value: object) -> object:
    """Serialize one private Trading projection at the HTTP boundary.

    Returns:
        JSON-compatible serialized dict or raw object.
    """
    dump = getattr(value, "model_dump", None)
    return dump(mode="json") if callable(dump) else value


def _owned_session(session_id: str, auth: AuthContext) -> object:
    """Require an execution session to belong to the authenticated scope.

    Returns:
        Verified owned execution session instance.

    Raises:
        HTTPException: If session is not found or not owned.
    """
    value = get_execution_session(session_id)
    if value is None:
        raise HTTPException(status_code=404, detail="EXECUTION_SESSION_NOT_FOUND")
    if (
        getattr(value, "principal_id", None) != auth.principal_id
        or getattr(value, "environment_id", None) != auth.tenant_or_environment
    ):
        raise HTTPException(status_code=404, detail="EXECUTION_SESSION_NOT_FOUND")
    return value


@router.get("/execution-sessions", response_model=None)
def _list_execution_sessions(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    mode: Annotated[Literal["sim", "demo", "live"] | None, Query()] = None,
) -> object:
    """List the caller's durable non-archived execution sessions.

    Returns:
        List of session projection payloads.
    """
    require_human_permission(auth, "trading:read")
    values = list_execution_sessions(
        principal_id=auth.principal_id,
        environment_id=auth.tenant_or_environment,
        mode=mode,
    )
    return [_session_payload(value) for value in values]


@router.post("/execution-sessions", response_model=None, status_code=201)
def _create_execution_session(
    body: ExecutionSessionCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Create one stopped execution-session definition.

    Returns:
        Created Trading session projection payload.
    """
    require_human_permission(auth, "trading:write")
    request_id = generate_id("req")
    username = (
        get_username_for_principal(auth.principal_id, request_id=request_id)
        if body.mode == "sim"
        else None
    )
    value = create_execution_session(
        principal_id=auth.principal_id,
        environment_id=auth.tenant_or_environment,
        request_id=request_id,
        simulation_username=username,
        **body.model_dump(mode="python"),
    )
    return _session_payload(value)


@router.patch("/execution-sessions/{session_id}", response_model=None)
def _update_execution_session(
    session_id: str,
    body: ExecutionSessionUpdateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Update mutable registry metadata with optimistic locking.

    Returns:
        Updated Trading session projection payload.
    """
    require_human_permission(auth, "trading:write")
    _owned_session(session_id, auth)
    value = update_execution_session_metadata(
        session_id, request_id=generate_id("req"), **body.model_dump(mode="python")
    )
    return _session_payload(value)


@router.post("/execution-sessions/{session_id}/default", response_model=None)
def _default_execution_session(
    session_id: str,
    body: ExecutionSessionActionRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Select the default session for its mode.

    Returns:
        Updated Trading session projection payload.
    """
    require_human_permission(auth, "trading:write")
    _owned_session(session_id, auth)
    return _session_payload(
        set_default_execution_session(
            session_id,
            expected_version=body.expected_version,
            request_id=generate_id("req"),
        )
    )


@router.delete("/execution-sessions/{session_id}", response_model=None)
def _archive_execution_session(
    session_id: str,
    body: ExecutionSessionActionRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Archive a stopped session while retaining its evidence.

    Returns:
        Archived Trading session projection payload.
    """
    require_human_permission(auth, "trading:write")
    _owned_session(session_id, auth)
    return _session_payload(
        archive_execution_session(
            session_id,
            expected_version=body.expected_version,
            request_id=generate_id("req"),
        )
    )


@router.get("/execution-sessions/{session_id}/events", response_model=None)
def _execution_session_events(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Read the immutable lifecycle journal for one session.

    Returns:
        List of session lifecycle event projections.
    """
    require_human_permission(auth, "trading:read")
    _owned_session(session_id, auth)
    return list(get_execution_session_events(session_id))


@router.post(
    "/execution-sessions/{session_id}/complete-configuration", response_model=None
)
def _complete_execution_session_configuration(
    session_id: str,
    body: ExecutionSessionConfigurationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Complete identity and dataset lineage for one stopped legacy SIM.

    Returns:
        Completed Trading session projection.

    Raises:
        HTTPException: If the selected dataset is not currently verified.
    """
    require_human_permission(auth, "trading:write")
    _owned_session(session_id, auth)
    match = next(
        (
            item
            for item in list_verified_datasets(request_id=generate_id("req"))
            if item["dataset_id"] == body.dataset_ref
            and item["revision"] == body.dataset_revision
            and item["content_hash"] == body.dataset_hash
        ),
        None,
    )
    if match is None:
        raise HTTPException(status_code=422, detail="SIM_DATASET_NOT_VERIFIED")
    request_id = generate_id("req")
    username = get_username_for_principal(auth.principal_id, request_id=request_id)
    value = complete_simulation_session_configuration(
        session_id,
        expected_version=body.expected_version,
        username=username,
        account_name=username,
        dataset_ref=body.dataset_ref,
        dataset_revision=body.dataset_revision,
        dataset_hash=body.dataset_hash,
        request_id=request_id,
    )
    return _session_payload(value)


@router.post("/execution-sessions/{session_id}/start", response_model=None)
async def _start_execution_session(
    session_id: str,
    body: ExecutionSessionActionRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    profile_source: Annotated[
        _AccountProfileSource, Depends(_trading_account_profile_source)
    ],
) -> object:
    """Verify provider mode and start one foreground execution session.

    Returns:
        Running Trading session projection payload.

    Raises:
        HTTPException: If verification fails or a state conflict occurs.
    """
    require_human_permission(auth, "trading:write")
    session = _owned_session(session_id, auth)
    expected_version = body.expected_version
    if (
        getattr(session, "mode", None) == "sim"
        and getattr(session, "simulation_session_id", None) is None
    ):
        request_id = generate_id("req")
        session = assign_simulation_session_identity(
            session_id,
            expected_version=expected_version,
            username=get_username_for_principal(
                auth.principal_id, request_id=request_id
            ),
            request_id=request_id,
        )
        expected_version = int(cast("Any", session).version)

    async def verify(_: object) -> dict[str, object]:
        profile = await profile_source(auth)
        session_mode = getattr(session, "mode", None)
        selected_mode = getattr(profile, "selected_mode", None)
        dataset_verified = True
        candidate_configured = True
        if session_mode == "sim":
            candidate_configured = all(
                getattr(session, field, None) is not None
                for field in (
                    "provider_account_ref",
                    "simulation_session_id",
                    "dataset_ref",
                    "dataset_revision",
                    "dataset_hash",
                    "sim_initial_balance",
                    "sim_leverage",
                    "sim_account_currency",
                )
            )
            dataset_verified = any(
                item["dataset_id"] == getattr(session, "dataset_ref", None)
                and item["revision"] == getattr(session, "dataset_revision", None)
                and item["content_hash"] == getattr(session, "dataset_hash", None)
                for item in list_verified_datasets(request_id=generate_id("req"))
            )
        profile_compatible = (
            candidate_configured
            if session_mode == "sim"
            else bool(getattr(profile, "mode_compatible", False))
        )
        return {
            "verified": (
                profile_compatible
                and selected_mode == session_mode
                and dataset_verified
            ),
            "mode": selected_mode,
            "simulation_session_id": getattr(session, "simulation_session_id", None),
            "account_name": getattr(profile, "account_name", None),
        }

    try:
        value = await start_execution_session(
            session_id,
            expected_version=expected_version,
            authority_start=verify,
            request_id=generate_id("req"),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return _session_payload(value)


@router.post("/execution-sessions/{session_id}/stop", response_model=None)
async def _stop_execution_session(
    session_id: str,
    body: ExecutionSessionActionRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Stop admission for one running logical execution session.

    Returns:
        Stopped Trading session projection payload.
    """
    require_human_permission(auth, "trading:write")
    _owned_session(session_id, auth)

    async def reconcile(_: object) -> dict[str, object]:
        # Session stop disables new admission; broker-owned positions remain
        # durable at the provider and are reconciled on the next verified start.
        return {"safe_to_stop": True}

    value = await stop_execution_session(
        session_id,
        expected_version=body.expected_version,
        authority_stop=reconcile,
        request_id=generate_id("req"),
    )
    return _session_payload(value)


def _governed_preflight(
    body: TradingMutationRequest,
    idempotency_key: str | None,
) -> None:
    """Enforce boundary policy before delegating a Trading mutation.

    Args:
        body: Governed Trading mutation request.
        idempotency_key: Idempotency key supplied as a transport header.

    Raises:
        HTTPException: If production, configuration, or idempotency policy fails.
    """
    _require_configured_route(body.route)
    _require_matching_idempotency_key(body.idempotency_key, idempotency_key)


@router.get("/session", response_model=None)
def _get_session(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_SessionSource, Depends(_trading_session_source)],
    authority_id: Annotated[str, Query(min_length=1, max_length=200)],
    route: Annotated[Literal["sim", "demo", "live"], Query()] = "demo",
) -> object:
    """Return one exact-scope aggregate Trading session projection.

    Returns:
        Trading-owned aggregate projection.

    Raises:
        HTTPException: If authorization fails or state is absent.
    """
    require_human_permission(auth, "trading:read")
    result = source(route, auth.tenant_or_environment, authority_id, auth)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TRADING_SESSION_NOT_FOUND",
        )
    return result


@router.get("/account-profile", response_model=None)
async def _get_account_profile(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AccountProfileSource, Depends(_trading_account_profile_source)],
) -> object:
    """Return the active Simulator or MT5 account identity for the shell.

    Returns:
        Minimal provider-authored account profile.

    Raises:
        HTTPException: If authorization, composition, or provider evidence fails.
        RuntimeError: If an unexpected provider failure is reported.
        TypeError: If unexpected provider account material is malformed.
    """
    require_human_permission(auth, "trading:read")
    try:
        return await source(auth)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TRADING_ACCOUNT_PROFILE_UNAVAILABLE",
        ) from error
    except (RuntimeError, TypeError) as error:
        if str(error) not in {
            "TRADING_ACCOUNT_PROFILE_MALFORMED",
            "TRADING_ACCOUNT_PROFILE_UNAVAILABLE",
        }:
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/instruments/{symbol}/constraints", response_model=None)
def _get_instrument_constraints(
    symbol: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return provider-authored constraints for one exact trading symbol.

    Returns:
        Validated browser-facing instrument constraints.

    Raises:
        HTTPException: If authorization or complete provider evidence is absent.
    """
    require_human_permission(auth, "trading:read")
    request_id = generate_id("req")
    source_id = resolve_runtime_source_id(request_id=request_id)
    response = get_symbol_metadata(
        build_symbol_metadata_request(
            source_id=source_id,
            symbol=symbol,
            request_id=request_id,
        )
    )
    metadata = getattr(response, "data", None)
    if getattr(response, "status", None) != "success" or metadata is None:
        raise HTTPException(
            status_code=503,
            detail="INSTRUMENT_CONSTRAINTS_UNAVAILABLE",
        )

    def required_decimal(*names: str) -> Decimal:
        """Read one positive provider decimal without supplying a fallback.

        Returns:
            Positive provider-authored decimal value.

        Raises:
            HTTPException: If none of the named fields contains a positive value.
        """
        for name in names:
            value = getattr(metadata, name, None)
            if isinstance(value, bool) or value is None:
                continue
            try:
                decimal_value = Decimal(str(value))
            except InvalidOperation, ValueError:
                continue
            if decimal_value.is_finite() and decimal_value > 0:
                return decimal_value
        raise HTTPException(status_code=503, detail="INSTRUMENT_CONSTRAINTS_INCOMPLETE")

    catalogue = getattr(get_broker_capability_catalogue(), "data", {})
    provider = next(
        (
            values
            for key, values in catalogue.items()
            if str(getattr(key, "value", key)) == source_id
        ),
        (),
    )
    place_order = next(
        (
            item
            for item in provider
            if str(getattr(getattr(item, "capability", None), "value", ""))
            == "place_order"
        ),
        None,
    )
    order_types = tuple(getattr(place_order, "supported_order_types", ()))
    if place_order is None or not order_types or source_id != "mt5":
        raise HTTPException(status_code=503, detail="INSTRUMENT_ROUTE_UNAVAILABLE")
    stops_level = getattr(metadata, "trade_stops_level", None)
    supports_protection = isinstance(stops_level, int | float) and not isinstance(
        stops_level, bool
    )
    return TradingInstrumentConstraintsResponse(
        symbol=str(getattr(metadata, "provider_symbol", symbol)),
        source_id=source_id,
        quantity_unit="lots",
        min_quantity=required_decimal("min_quantity", "volume_min"),
        max_quantity=required_decimal("max_quantity", "volume_max"),
        quantity_step=required_decimal("quantity_step", "volume_step"),
        price_tick=required_decimal("price_step", "trade_tick_size", "point"),
        digits=_nonnegative_int_or_none(getattr(metadata, "digits", None)),
        pip_size=_positive_decimal_or_none(metadata, "pip_size"),
        trade_tick_size=_positive_decimal_or_none(
            metadata, "trade_tick_size", "price_step", "point"
        ),
        trade_tick_value_profit=_positive_decimal_or_none(
            metadata, "trade_tick_value_profit"
        ),
        trade_tick_value_loss=_positive_decimal_or_none(
            metadata, "trade_tick_value_loss"
        ),
        trade_contract_size=_positive_decimal_or_none(metadata, "trade_contract_size"),
        profit_currency=_available_text_or_none(
            getattr(metadata, "currency_profit", None)
        ),
        supported_order_types=order_types,
        supported_time_in_force=tuple(
            getattr(place_order, "supported_time_in_force", ())
        ),
        supports_stop_loss=supports_protection,
        supports_take_profit=supports_protection,
        retrieved_at=metadata.retrieved_at,
    )


@router.post("/orders", response_model=None)
async def _submit_order(
    body: TradingMutationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Submit one governed non-production Trading order.

    Returns:
        Trading-owned mutation receipt.

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, idempotency_key)
    if body.action != "submit_order":
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("submit_order", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/preflight", response_model=None)
async def _preflight_order(
    body: OrderPreflightRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PreflightSource, Depends(_trading_preflight_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Review one candidate human-initiated order through Risk's real gate.

    Produces the ``risk_decision_id``/``action_policy_verdict_id``/
    ``approval_token_ref`` a subsequent ``POST /orders`` needs — it never
    submits an order itself.

    Returns:
        The real Risk decision/verdict pair.

    Raises:
        HTTPException: If boundary governance, live routing, or evidence
            availability fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _require_configured_route(body.route)
    _require_matching_idempotency_key(body.idempotency_key, idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/preflight",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(body, auth),
        )
    except RuntimeError as error:
        if str(error) == "ACCOUNT_MODE_PLATFORM_MISMATCH":
            raise HTTPException(status_code=409, detail=str(error)) from error
        if str(error) == "MANUAL_ORDER_LIVE_NOT_CONFIGURED":
            raise HTTPException(status_code=403, detail=str(error)) from error
        if str(error) == "ACCOUNT_SNAPSHOT_UNAVAILABLE":
            raise HTTPException(status_code=503, detail=str(error)) from error
        if str(error) != "TRADING_PREFLIGHT_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/cancel-all/preflight", response_model=None)
async def _preflight_cancel_all_orders(
    body: CancelAllPreflightRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PreflightSource, Depends(_trading_cancel_all_preflight_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Authorize one candidate bulk cancel-all-orders action through Risk.

    Produces the ``risk_decision_id``/``action_policy_verdict_id``/
    ``approval_token_ref`` a subsequent ``POST /orders/cancel-all`` needs — it
    never cancels an order itself.

    Returns:
        The real Risk decision/verdict pair.

    Raises:
        HTTPException: If boundary governance, live routing, or evidence
            availability fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _require_configured_route(body.route)
    _require_matching_idempotency_key(body.idempotency_key, idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/cancel-all/preflight",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(body, auth),
        )
    except RuntimeError as error:
        if str(error) == "ACCOUNT_MODE_PLATFORM_MISMATCH":
            raise HTTPException(status_code=409, detail=str(error)) from error
        if str(error) == "MANUAL_ORDER_LIVE_NOT_CONFIGURED":
            raise HTTPException(status_code=403, detail=str(error)) from error
        if str(error) == "ACCOUNT_SNAPSHOT_UNAVAILABLE":
            raise HTTPException(status_code=503, detail=str(error)) from error
        if str(error) != "TRADING_CANCEL_ALL_PREFLIGHT_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/cancel-all", response_model=None)
async def _cancel_all_orders(
    body: TradingMutationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Cancel every eligible governed non-production Trading order.

    Returns:
        Trading-owned bulk mutation receipt (ordered child results and any
        skipped orders).

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, idempotency_key)
    if body.action != "cancel_all_orders":
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/cancel-all",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("cancel_all_orders", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/{order_id}/preflight", response_model=None)
async def _preflight_cancel_order(
    order_id: str,
    body: CancelOrderPreflightRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[
        _PreflightSource, Depends(_trading_cancel_order_preflight_source)
    ],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Authorize one candidate single-order cancellation through Risk.

    Produces the ``risk_decision_id``/``action_policy_verdict_id``/
    ``approval_token_ref`` a subsequent ``DELETE /orders/{order_id}`` needs —
    it never cancels an order itself.

    Returns:
        The real Risk decision/verdict pair.

    Raises:
        HTTPException: If boundary governance, live routing, evidence
            availability, or a mismatched order id fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    if body.target_broker_order_id != order_id:
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    _require_configured_route(body.route)
    _require_matching_idempotency_key(body.idempotency_key, idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/{order_id}/preflight",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(body, auth),
        )
    except RuntimeError as error:
        if str(error) == "ACCOUNT_MODE_PLATFORM_MISMATCH":
            raise HTTPException(status_code=409, detail=str(error)) from error
        if str(error) == "MANUAL_ORDER_LIVE_NOT_CONFIGURED":
            raise HTTPException(status_code=403, detail=str(error)) from error
        if str(error) == "ACCOUNT_SNAPSHOT_UNAVAILABLE":
            raise HTTPException(status_code=503, detail=str(error)) from error
        if str(error) != "TRADING_CANCEL_ORDER_PREFLIGHT_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.delete("/orders/{order_id}", response_model=None)
async def _cancel_order(
    order_id: str,
    body: TradingMutationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Cancel one governed non-production Trading order.

    Returns:
        Trading-owned mutation receipt.

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, idempotency_key)
    if body.action != "cancel_order" or body.target_broker_order_id != order_id:
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="DELETE",
            route="/api/v1/trading/orders/{order_id}",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("cancel_order", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/positions/{position_id}/close", response_model=None)
async def _close_position(
    position_id: str,
    body: TradingMutationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Close one governed non-production Trading position.

    Returns:
        Trading-owned mutation receipt.

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, idempotency_key)
    if body.action != "close_position" or body.target_broker_position_id != position_id:
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/positions/{position_id}/close",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("close_position", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


__all__ = ("router",)
