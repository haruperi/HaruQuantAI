"""Canonical FastAPI application construction."""

from collections.abc import Callable, Mapping
from functools import partial
from typing import Any, cast

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.services.api.composition.broker_config import (
    build_system_broker_connection_config,
)
from app.services.api.composition.capabilities import (
    get_capability_attribute,
    import_capability_module,
)
from app.services.api.composition.in_process import (
    build_in_process_graph,
    get_graph_closers,
    get_graph_overrides,
    get_graph_probes,
)
from app.services.api.composition.lifecycle import lifespan
from app.services.api.composition.owner_sources import (
    read_audit_events,
    read_dashboard_snapshot,
    read_risk_state,
    read_simulation_result,
    read_trading_events,
    read_trading_session,
)
from app.services.api.composition.runtime_settings import build_credential_key_set
from app.services.api.contracts.catalog import create_canonical_route_contract_registry
from app.services.api.health.routes import router as health_router
from app.services.api.identity import (
    IdentityError,
    build_auth_context,
    require_auth_context,
    validate_csrf,
    validate_session,
)
from app.services.api.identity.routes import router as auth_router
from app.services.api.middleware.context import (
    CANONICAL_CONTEXT_STATE_KEY,
    RequestContextMiddleware,
)
from app.services.api.middleware.deadlines import DeadlineMiddleware
from app.services.api.middleware.envelope import get_canonical_envelope_middleware
from app.services.api.middleware.rate_limits import RateLimitMiddleware
from app.services.api.middleware.redaction import SecretRedactionMiddleware
from app.services.api.middleware.runtime_settings import RuntimeSettingsMiddleware
from app.services.api.observability.routes import router as observability_router
from app.services.api.widgets.dashboards.routes import router as dashboards_router
from app.services.api.widgets.data.orchestration import build_dataset_source
from app.services.api.widgets.data.routes import router as data_router
from app.services.api.widgets.data.stream_routes import router as data_stream_router
from app.services.api.widgets.event_delivery.orchestration import (
    create_stream_connection_manager,
)
from app.services.api.widgets.indicators.routes import router as indicators_router
from app.services.api.widgets.markets.routes import router as markets_router
from app.services.api.widgets.operational.routes import router as workstation_router
from app.services.api.widgets.operator.routes import router as operator_router
from app.services.api.widgets.risk.orchestration import build_risk_command_source
from app.services.api.widgets.risk.routes import router as risk_router
from app.services.api.widgets.settings.account_mode import resolve_runtime_profile
from app.services.api.widgets.settings.bootstrap import (
    ApiSettings,
    get_api_settings,
)
from app.services.api.widgets.settings.routes import router as settings_router
from app.services.api.widgets.simulation.live_orchestration import (
    build_live_simulation_source,
)
from app.services.api.widgets.simulation.live_routes import (
    router as simulation_live_router,
)
from app.services.api.widgets.simulation.orchestration import (
    build_simulation_run_source,
    build_simulation_session_source,
)
from app.services.api.widgets.simulation.routes import router as simulation_router
from app.services.api.widgets.simulation.session_routes import (
    router as simulation_sessions_router,
)
from app.services.api.widgets.simulator.batching import (
    build_batch_runner,
)
from app.services.api.widgets.simulator.completion import (
    build_catalogue_completion_sink,
)
from app.services.api.widgets.simulator.orchestration import (
    build_api_backtest_registry,
    build_data_runtime_context,
    build_simulator_run_source,
    build_simulator_strategy_source,
)
from app.services.api.widgets.simulator.provenance import (
    RunProvenanceIndex,
)
from app.services.api.widgets.simulator.registry import (
    SimulationWorkbenchRegistry,
    build_simulation_workbench_registry,
)
from app.services.api.widgets.simulator.reproduction import (
    build_reproduction_runner,
)
from app.services.api.widgets.simulator.routes import router as simulator_router
from app.services.api.widgets.simulator.workbench_orchestration import (
    build_simulation_workbench_live_authority,
    build_simulation_workbench_source,
)
from app.services.api.widgets.simulator.workbench_routes import (
    router as simulation_workbench_router,
)
from app.services.api.widgets.strategies.orchestration import (
    build_strategy_mutation_source,
)
from app.services.api.widgets.strategies.routes import router as strategies_router
from app.services.api.widgets.trading.activity import (
    router as trading_activity_router,
)
from app.services.api.widgets.trading.orchestration import (
    build_trading_account_profile_source,
    build_trading_cancel_all_preflight_source,
    build_trading_cancel_order_preflight_source,
    build_trading_mutation_source,
    build_trading_preflight_source,
)
from app.services.api.widgets.trading.routes import router as trading_router
from app.services.api.widgets.watchlists.routes import router as watchlists_router
from app.utils import generate_id, utc_now


async def _connect_trading_account_profile_broker(route: str) -> object:
    """Connect MT5 from the API's authoritative persisted provider settings.

    Args:
        route: Elected demo or live account route.

    Returns:
        Connected Brokers-owned MT5 adapter.

    Raises:
        ValueError: If configuration, construction, or connection fails.
    """
    from app.services.brokers import (
        connect_broker,
        create_broker_adapter,
        disconnect_broker,
        get_broker_id,
    )

    config = cast(
        "Any",
        build_system_broker_connection_config(
            "mt5",
            request_id=generate_id("req"),
            environment=route,
        ),
    )
    response = cast(
        "Any",
        create_broker_adapter(cast("Any", get_broker_id("mt5")), config),
    )
    if response.error is not None or response.data is None:
        raise ValueError("broker adapter construction failed")
    adapter = response.data
    connected = cast("Any", await connect_broker(adapter))
    if connected.error is not None:
        await disconnect_broker(adapter)
        raise ValueError("broker adapter connection failed")
    return adapter


_SESSION_COOKIE = "hq_session"
# Optional capabilities resolve tolerantly: when one is absent its module is
# ``None``, its router is not mounted, and its provider is never declared, so
# the gateway loses that capability instead of failing to compose.
_AGENTIC_ORCHESTRATION = import_capability_module(
    "app.services.api.widgets.agentic.orchestration", capability_id="agentic"
)
_AGENTIC_ROUTES = import_capability_module(
    "app.services.api.widgets.agentic.routes", capability_id="agentic"
)
_ANALYTICS_ORCHESTRATION = import_capability_module(
    "app.services.api.widgets.analytics.orchestration", capability_id="analytics"
)
_ANALYTICS_ROUTES = import_capability_module(
    "app.services.api.widgets.analytics.routes", capability_id="analytics"
)
_OPTIMIZATION_ORCHESTRATION = import_capability_module(
    "app.services.api.widgets.optimization.orchestration", capability_id="optimization"
)
_OPTIMIZATION_ROUTES = import_capability_module(
    "app.services.api.widgets.optimization.routes", capability_id="optimization"
)
_PORTFOLIO_ORCHESTRATION = import_capability_module(
    "app.services.api.widgets.portfolio.orchestration", capability_id="portfolio"
)
_PORTFOLIO_ROUTES = import_capability_module(
    "app.services.api.widgets.portfolio.routes", capability_id="portfolio"
)
_RESEARCH_ORCHESTRATION = import_capability_module(
    "app.services.api.widgets.research.orchestration", capability_id="research"
)
_RESEARCH_ROUTES = import_capability_module(
    "app.services.api.widgets.research.routes", capability_id="research"
)

agentic_router = get_capability_attribute(_AGENTIC_ROUTES, "router")
analytics_workbench_router = get_capability_attribute(_ANALYTICS_ROUTES, "router")
optimization_router = get_capability_attribute(_OPTIMIZATION_ROUTES, "router")
portfolio_router = get_capability_attribute(_PORTFOLIO_ROUTES, "router")
research_router = get_capability_attribute(_RESEARCH_ROUTES, "router")


def _capability_builder(module: object | None, attribute: str) -> Callable[..., Any]:
    """Return one required builder from a resolved optional capability module.

    Args:
        module: Resolved capability module.
        attribute: Builder attribute name.

    Returns:
        Callable builder owned by the present capability.

    Raises:
        RuntimeError: If the capability is absent and the builder is requested.
    """
    builder = get_capability_attribute(cast("Any", module), attribute)
    if builder is None:
        message = f"capability builder unavailable: {attribute}"
        raise RuntimeError(message)
    return cast("Callable[..., Any]", builder)


_ROUTERS = tuple(
    router
    for router in (
        auth_router,
        health_router,
        indicators_router,
        markets_router,
        settings_router,
        data_router,
        data_stream_router,
        strategies_router,
        research_router,
        simulation_live_router,
        simulation_router,
        simulation_sessions_router,
        simulator_router,
        simulation_workbench_router,
        analytics_workbench_router,
        portfolio_router,
        risk_router,
        trading_router,
        trading_activity_router,
        optimization_router,
        dashboards_router,
        operator_router,
        observability_router,
        agentic_router,
        watchlists_router,
        workstation_router,
    )
    if router is not None
)


def _build_canonical_graph(
    *,
    settings: ApiSettings,
    simulator_state_provider: Callable[[], object],
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
    provenance = RunProvenanceIndex()
    workbench_registry = cast(
        "SimulationWorkbenchRegistry", build_simulation_workbench_registry()
    )
    runtime_context = build_data_runtime_context(simulator_state_provider)
    backtest_registry = build_api_backtest_registry(
        runtime_context,
        completion_sink=build_catalogue_completion_sink(
            workbench_registry, provenance=provenance.resolve
        ),
    )
    simulator_run_source = build_simulator_run_source(backtest_registry)
    providers: dict[str, object] = {
        "dashboard.source": read_dashboard_snapshot,
        "data.dataset_source": build_dataset_source(),
        "operator.audit_source": read_audit_events,
        "operator.event_source": read_trading_events,
        "risk.command_source": build_risk_command_source(risk_dependencies),
        "risk.source": read_risk_state,
        "simulation.live_source": build_live_simulation_source(simulation_dependencies),
        "simulation.result_source": partial(
            read_simulation_result,
            artifact_root=settings.simulation_artifact_root,
        ),
        "simulation.run_source": build_simulation_run_source(simulation_dependencies),
        "simulation.session_source": build_simulation_session_source(
            simulation_dependencies
        ),
        "simulator.run_source": simulator_run_source,
        "simulator.strategy_source": build_simulator_strategy_source(),
        "simulator.workbench_source": build_simulation_workbench_source(
            registry=workbench_registry,
            live_authority=build_simulation_workbench_live_authority(
                simulation_dependencies,
                reproduction_runner=build_reproduction_runner(
                    simulator_run_source, provenance=provenance.record
                ),
            ),
            batch_runner=build_batch_runner(
                simulator_run_source,
                provenance=provenance.record,
                runtime_context=runtime_context,
            ),
        ),
        "strategy.mutation_source": build_strategy_mutation_source(
            strategy_dependencies
        ),
        "trading.account_profile_source": build_trading_account_profile_source(
            _connect_trading_account_profile_broker
        ),
        "trading.cancel_all_preflight_source": (
            build_trading_cancel_all_preflight_source()
        ),
        "trading.cancel_order_preflight_source": (
            build_trading_cancel_order_preflight_source()
        ),
        "trading.mutation_source": build_trading_mutation_source(
            trading_dependencies, runtime_policy=settings
        ),
        "trading.preflight_source": build_trading_preflight_source(),
        "trading.session_source": read_trading_session,
    }
    if _AGENTIC_ORCHESTRATION is not None:
        providers["agentic.source"] = _capability_builder(
            _AGENTIC_ORCHESTRATION, "build_agentic_source"
        )(agentic_dependencies)
    if _ANALYTICS_ORCHESTRATION is not None:
        providers["analytics.workbench.source"] = _capability_builder(
            _ANALYTICS_ORCHESTRATION, "build_analytics_workbench_composition"
        )(settings)
    if _OPTIMIZATION_ORCHESTRATION is not None:
        providers["optimization.source"] = _capability_builder(
            _OPTIMIZATION_ORCHESTRATION, "build_optimization_source"
        )(optimization_dependencies)
    if _PORTFOLIO_ORCHESTRATION is not None:
        providers["portfolio.source"] = _capability_builder(
            _PORTFOLIO_ORCHESTRATION, "build_portfolio_source"
        )(portfolio_dependencies)
    if _RESEARCH_ORCHESTRATION is not None:
        build_registry = _capability_builder(
            _RESEARCH_ORCHESTRATION, "build_research_registry"
        )
        build_runtime_context = _capability_builder(
            _RESEARCH_ORCHESTRATION, "build_research_runtime_context"
        )
        providers["research.source"] = _capability_builder(
            _RESEARCH_ORCHESTRATION, "build_research_source"
        )(build_registry(build_runtime_context(simulator_state_provider)))
    return build_in_process_graph(providers)


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
    """Build authority from a persisted session or auto-login in dev mode.

    Returns:
        Utils-owned immutable authentication context.

    Raises:
        HTTPException: If session validation fails and dev auto-login is inactive.
        IdentityError: If session validation fails.
    """
    settings: ApiSettings = (
        getattr(request.app.state, "api_settings", None) or get_api_settings()
    )
    context = getattr(request.state, CANONICAL_CONTEXT_STATE_KEY, None)
    request_id = str(getattr(context, "request_id", ""))
    correlation_id = str(getattr(context, "correlation_id", ""))
    try:
        token = _bearer_or_cookie(request)
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
        return build_auth_context(
            principal={
                "principal_id": user.user_id,
                "principal_type": "USER",
                "roles": user.roles,
                "permissions": user.permissions,
                "scopes": user.scopes,
                "tenant_or_environment": user.tenant_or_environment,
                # The account row records the profile the account was created
                # under; the operator-selected ACCOUNT_MODE is what the
                # application is actually running as, and every downstream
                # authority checks this claim, so the elected mode is the claim.
                "runtime_profile": resolve_runtime_profile(request_id=request_id),
            },
            trace={
                "issued_at": utc_now(),
                "request_id": request_id,
                "workflow_id": generate_id("wf"),
                "correlation_id": correlation_id,
            },
        )
    except (HTTPException, IdentityError) as error:
        if settings.environment == "dev" and settings.dev_auto_login:
            route_contracts = create_canonical_route_contract_registry()
            all_permissions = tuple(
                sorted(
                    {
                        contract.permission
                        for contract in route_contracts.all()
                        if contract.permission is not None
                    }
                )
            )
            return build_auth_context(
                principal={
                    "principal_id": "usr_haruquantai",
                    "principal_type": "USER",
                    "roles": ("admin", "operator", "researcher"),
                    "permissions": all_permissions,
                    "scopes": ("*",),
                    "tenant_or_environment": "development",
                    "runtime_profile": resolve_runtime_profile(request_id=request_id),
                },
                trace={
                    "issued_at": utc_now(),
                    "request_id": request_id,
                    "workflow_id": generate_id("wf"),
                    "correlation_id": correlation_id,
                },
            )
        if isinstance(error, HTTPException):
            raise
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
        simulator_state_provider=lambda: application.state,
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
        application.include_router(cast("APIRouter", router))
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
    application.add_middleware(RuntimeSettingsMiddleware)
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
