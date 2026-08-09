"""Canonical FastAPI application construction."""

from collections.abc import Callable, Mapping
from functools import partial
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.services.api._settings import ApiSettings, get_api_settings
from app.services.api.composition.agentic_dependencies import build_agentic_source
from app.services.api.composition.data_dependencies import build_dataset_source
from app.services.api.composition.in_process import (
    build_in_process_graph,
    get_graph_closers,
    get_graph_overrides,
    get_graph_probes,
)
from app.services.api.composition.lifecycle import lifespan
from app.services.api.composition.live_simulation_dependencies import (
    build_live_simulation_source,
)
from app.services.api.composition.optimization_dependencies import (
    build_optimization_source,
)
from app.services.api.composition.owner_sources import (
    read_audit_events,
    read_dashboard_snapshot,
    read_risk_state,
    read_simulation_result,
    read_trading_events,
    read_trading_session,
)
from app.services.api.composition.portfolio_dependencies import build_portfolio_source
from app.services.api.composition.risk_dependencies import build_risk_command_source
from app.services.api.composition.runtime_settings import build_credential_key_set
from app.services.api.composition.simulation_dependencies import (
    build_simulation_run_source,
    build_simulation_session_source,
)
from app.services.api.composition.strategy_dependencies import (
    build_strategy_mutation_source,
)
from app.services.api.composition.trading_dependencies import (
    build_trading_mutation_source,
)
from app.services.api.contracts.catalog import create_canonical_route_contract_registry
from app.services.api.identity import (
    IdentityError,
    build_auth_context,
    require_auth_context,
    validate_csrf,
    validate_session,
)
from app.services.api.middleware.context import (
    CANONICAL_CONTEXT_STATE_KEY,
    RequestContextMiddleware,
)
from app.services.api.middleware.deadlines import DeadlineMiddleware
from app.services.api.middleware.envelope import get_canonical_envelope_middleware
from app.services.api.middleware.rate_limits import RateLimitMiddleware
from app.services.api.middleware.redaction import SecretRedactionMiddleware
from app.services.api.routes import (
    agentic_router,
    auth_router,
    dashboards_router,
    data_router,
    data_stream_router,
    health_router,
    indicators_router,
    observability_router,
    operator_router,
    optimization_router,
    portfolio_router,
    research_router,
    risk_router,
    settings_router,
    simulation_live_router,
    simulation_router,
    simulation_sessions_router,
    strategies_router,
    trading_router,
    workstation_router,
)
from app.services.api.streams import create_stream_connection_manager
from app.utils import generate_id, utc_now

_SESSION_COOKIE = "hq_session"
_ROUTERS = (
    auth_router,
    health_router,
    indicators_router,
    settings_router,
    data_router,
    data_stream_router,
    strategies_router,
    research_router,
    simulation_live_router,
    simulation_router,
    simulation_sessions_router,
    portfolio_router,
    risk_router,
    trading_router,
    optimization_router,
    dashboards_router,
    operator_router,
    observability_router,
    agentic_router,
    workstation_router,
)


def _build_canonical_graph(
    *,
    settings: ApiSettings,
    simulation_dependencies: object | None = None,
    trading_dependencies: object | None = None,
    portfolio_dependencies: object | None = None,
    optimization_dependencies: object | None = None,
    agentic_dependencies: object | None = None,
    strategy_dependencies: object | None = None,
    risk_dependencies: object | None = None,
) -> object:
    """Build the exact owner-backed graph for the reduced backend v1.

    Returns:
        Validated in-process graph containing all retained owner sources.
    """
    return build_in_process_graph(
        {
            "agentic.source": build_agentic_source(agentic_dependencies),
            "dashboard.source": read_dashboard_snapshot,
            "data.dataset_source": build_dataset_source(),
            "operator.audit_source": read_audit_events,
            "operator.event_source": read_trading_events,
            "optimization.source": build_optimization_source(optimization_dependencies),
            "portfolio.source": build_portfolio_source(portfolio_dependencies),
            "risk.command_source": build_risk_command_source(risk_dependencies),
            "risk.source": read_risk_state,
            "simulation.live_source": build_live_simulation_source(
                simulation_dependencies
            ),
            "simulation.result_source": partial(
                read_simulation_result,
                artifact_root=settings.simulation_artifact_root,
            ),
            "simulation.run_source": build_simulation_run_source(
                simulation_dependencies
            ),
            "simulation.session_source": build_simulation_session_source(
                simulation_dependencies
            ),
            "strategy.mutation_source": build_strategy_mutation_source(
                strategy_dependencies
            ),
            "trading.mutation_source": build_trading_mutation_source(
                trading_dependencies, runtime_policy=settings
            ),
            "trading.session_source": read_trading_session,
        }
    )


def _bearer_or_cookie(request: Request) -> str:
    """Extract one opaque supported authentication credential.

    Returns:
        Opaque session credential.

    Raises:
        HTTPException: If no supported credential is present.
    """
    token = request.cookies.get(_SESSION_COOKIE)
    authorization = request.headers.get("authorization", "")
    if token is None and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AUTHENTICATION_REQUIRED",
        )
    return token


def _resolve_auth_context(request: Request) -> object:
    """Build authority only from a persisted validated session.

    Returns:
        Utils-owned immutable authentication context.

    Raises:
        HTTPException: If session validation fails.
    """
    context = getattr(request.state, CANONICAL_CONTEXT_STATE_KEY, None)
    request_id = str(getattr(context, "request_id", ""))
    correlation_id = str(getattr(context, "correlation_id", ""))
    token = _bearer_or_cookie(request)
    try:
        user = validate_session(
            token,
            request_id=request_id,
        )
        if request.cookies.get(_SESSION_COOKIE) is not None and request.method not in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            csrf_token = request.headers.get("x-csrf-token", "")
            validate_csrf(token, csrf_token, request_id=request_id)
    except IdentityError as error:
        code = (
            "CSRF_INVALID"
            if str(error) == "CSRF_INVALID"
            else "AUTHENTICATION_REQUIRED"
        )
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
                if code == "CSRF_INVALID"
                else status.HTTP_401_UNAUTHORIZED
            ),
            detail=code,
        ) from error
    return build_auth_context(
        principal={
            "principal_id": user.user_id,
            "principal_type": "USER",
            "roles": user.roles,
            "permissions": user.permissions,
            "scopes": user.scopes,
            "tenant_or_environment": user.tenant_or_environment,
            "runtime_profile": user.runtime_profile,
        },
        trace={
            "issued_at": utc_now(),
            "request_id": request_id,
            "workflow_id": generate_id("wf"),
            "correlation_id": correlation_id,
        },
    )


def _request_auth_context(request: Request) -> object:
    """Return middleware-validated authentication state.

    Returns:
        Validated authentication context.

    Raises:
        HTTPException: If middleware did not authenticate the request.
    """
    context = getattr(request.state, "api_auth_context", None)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AUTHENTICATION_REQUIRED",
        )
    return context


def create_app(
    config: ApiSettings | None = None,
    *,
    in_process_graph: object | None = None,
    dependency_overrides: Mapping[Callable[..., object], Callable[..., object]]
    | None = None,
    optional_startup_probes: Mapping[str, Callable[[], object]] | None = None,
    owned_resource_closers: tuple[Callable[[], object], ...] = (),
    simulation_dependencies: object | None = None,
    trading_dependencies: object | None = None,
    portfolio_dependencies: object | None = None,
    optimization_dependencies: object | None = None,
    agentic_dependencies: object | None = None,
    strategy_dependencies: object | None = None,
    risk_dependencies: object | None = None,
) -> FastAPI:
    """Construct the single canonical UI/API application.

    Args:
        config: Validated runtime settings.
        in_process_graph: Opaque validated in-process owner dependency graph.
        dependency_overrides: Explicit owner-domain adapter dependencies.
        optional_startup_probes: Named dependencies allowed to degrade.
        owned_resource_closers: Gateway-owned resource shutdown hooks.
        simulation_dependencies: Complete Simulator receiver-owned port bundle.
        trading_dependencies: Complete Trading receiver-owned dependency bundle.
        portfolio_dependencies: Complete Portfolio receiver-owned dependency
            bundle (opaque ``PortfolioService`` handle).
        optimization_dependencies: Complete Optimization receiver-owned
            dependency bundle, or ``None`` to fail every Optimization route
            closed with HTTP 503.
        agentic_dependencies: Complete Agentic ``AgenticDependencies`` bundle,
            or ``None`` to fail every Agentic route closed with HTTP 503.
        strategy_dependencies: Strategy validation-policy bundle, or ``None`` to
            fail Strategy mutation routes closed with HTTP 503.
        risk_dependencies: Risk kill-switch command bundle, or ``None`` to fail
            the kill-switch command route closed with HTTP 503.

    Returns:
        Fully composed FastAPI application.

    Raises:
        ValueError: If legacy and canonical dependency bindings are mixed.
    """
    settings = config or get_api_settings()
    route_contracts = create_canonical_route_contract_registry()
    application = FastAPI(
        title="HaruQuantAI API",
        version=settings.api_version,
        lifespan=lifespan,
    )
    application.state.api_settings = settings
    application.state.api_credential_key_set = build_credential_key_set(settings)
    application.state.api_active_credential_key_id = settings.active_credential_key_id
    application.state.api_route_contract_registry = route_contracts
    application.state.api_stream_connection_manager = create_stream_connection_manager(
        max_connections_per_actor=settings.stream_max_connections_per_actor,
        max_connections_process=settings.stream_max_connections_process,
        resume_window=settings.stream_resume_window,
    )
    if in_process_graph is not None and dependency_overrides:
        raise ValueError(
            "in_process_graph and dependency_overrides cannot be supplied together"
        )
    graph = in_process_graph or _build_canonical_graph(
        settings=settings,
        simulation_dependencies=simulation_dependencies,
        trading_dependencies=trading_dependencies,
        portfolio_dependencies=portfolio_dependencies,
        optimization_dependencies=optimization_dependencies,
        agentic_dependencies=agentic_dependencies,
        strategy_dependencies=strategy_dependencies,
        risk_dependencies=risk_dependencies,
    )
    graph_overrides = dict(get_graph_overrides(graph))
    graph_overrides.update(dependency_overrides or {})
    application.state.api_required_startup_probes = dict(get_graph_probes(graph))
    application.state.api_optional_startup_probes = dict(optional_startup_probes or {})
    graph_closers = get_graph_closers(graph)
    application.state.api_owned_resource_closers = (
        *graph_closers,
        *owned_resource_closers,
    )
    for router in _ROUTERS:
        application.include_router(router)
    application.dependency_overrides[require_auth_context] = _request_auth_context
    for dependency, override in (
        graph_overrides or dict(dependency_overrides or {})
    ).items():
        application.dependency_overrides[dependency] = override
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.ui_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-CSRF-Token",
            "X-Request-ID",
            "X-Correlation-ID",
        ],
    )
    application.add_middleware(SecretRedactionMiddleware)
    application.add_middleware(
        RateLimitMiddleware,
        limits=settings.rate_limits_by_class,
    )
    application.add_middleware(
        DeadlineMiddleware,
        timeout_seconds=settings.api_endpoint_timeout_seconds,
    )
    application.add_middleware(
        RequestContextMiddleware,
        auth_context_provider=cast("Any", _resolve_auth_context),
        route_contract_registry=route_contracts,
    )
    application.add_middleware(get_canonical_envelope_middleware())
    return application


app = create_app()

__all__ = ("app", "create_app")
