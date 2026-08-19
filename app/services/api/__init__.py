"""Approved package-root boundary for the UI/API domain."""

from collections.abc import Callable, Mapping
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from app.services.api.alerts import (
    build_kill_switch_activation_alert,
    build_unknown_broker_state_alert,
    deliver_critical_alert,
)
from app.services.api.middleware import (
    build_request_context_middleware as _build_request_context_middleware,
)
from app.services.api.middleware import (
    build_secret_redaction_middleware as _build_secret_redaction_middleware,
)
from app.services.api.workstation.operational import (
    build_workstation_read_model,
    execute_workstation_command,
)

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import ASGIApp

    from app.services.api.alerts.models import (
        CriticalAlertDeliveryResult,
        CriticalAlertError,
        CriticalAlertTrigger,
        CriticalOperationalAlert,
    )
    from app.services.api.contracts.catalog import RouteContractRegistry
    from app.services.api.contracts.models import (
        ApiError,
        ApiMetadata,
        ApiResponse,
        GovernedRequestContext,
        HealthDependencyCheck,
        Liveness,
        PageContext,
        Readiness,
        RouteContract,
        StreamEvent,
    )
    from app.services.api.middleware.redaction import EventEmitter
    from app.services.api.observability.exposition import MetricSnapshot
    from app.services.api.observability.sinks import MetricSink
    from app.services.api.workstation.research.schemas import ResearchRunRequest
type AuthContext = Any

__all__ = (
    "authenticate_api_user",
    "build_analytics_workbench_composition",
    "build_analytics_workbench_source",
    "build_api_agentic_dependencies",
    "build_api_error",
    "build_api_metadata",
    "build_api_optimization_dependencies",
    "build_api_portfolio_dependencies",
    "build_api_response",
    "build_api_risk_dependencies",
    "build_api_settings",
    "build_api_simulation_dependencies",
    "build_api_strategy_dependencies",
    "build_api_trading_dependencies",
    "build_authoritative_auth_context",
    "build_broker_connection_config",
    "build_critical_alert_delivery_result",
    "build_critical_alert_trigger",
    "build_critical_operational_alert",
    "build_governed_request_context",
    "build_health_dependency_check",
    "build_in_process_api_graph",
    "build_kill_switch_activation_alert",
    "build_metric_snapshot",
    "build_page_context",
    "build_request_context_middleware",
    "build_research_run_request",
    "build_route_contract",
    "build_route_contract_registry",
    "build_secret_redaction_middleware",
    "build_simulation_workbench_live_authority",
    "build_simulation_workbench_registry",
    "build_simulation_workbench_source",
    "build_stream_event",
    "build_system_broker_connection_config",
    "build_unknown_broker_state_alert",
    "build_workstation_read_model",
    "check_clock_drift",
    "consume_api_approval",
    "create_account_watchlist",
    "create_api_app",
    "create_api_approval",
    "create_api_session",
    "create_in_process_metric_sink",
    "create_stream_manager",
    "delete_account_watchlist",
    "deliver_critical_alert",
    "execute_workstation_command",
    "export_prometheus_metrics",
    "finalize_api_idempotency_key",
    "get_account_watchlist",
    "get_api_identity_error_type",
    "get_api_settings",
    "get_canonical_route_contract_registry",
    "get_credential_manifest",
    "get_critical_alert_error_type",
    "get_default_watchlist_symbols",
    "get_legacy_settings_classification",
    "get_liveness",
    "get_metrics",
    "get_readiness",
    "get_required_in_process_provider_names",
    "get_route_contract_registry",
    "get_system_credential_statuses",
    "get_system_settings",
    "get_system_settings_manifest",
    "get_user_settings",
    "hash_api_password",
    "list_account_watchlists",
    "normalize_stream_event",
    "record_metric",
    "recover_api_session_identity",
    "register_api_user",
    "register_route_contract",
    "rename_account_watchlist",
    "replace_account_watchlist_items",
    "require_api_permission",
    "reserve_api_idempotency_key",
    "resolve_api_credential_reference",
    "resolve_system_credential_slot",
    "revoke_api_session",
    "run_api_migrations",
    "set_default_account_watchlist",
    "store_api_credential",
    "store_system_credential",
    "update_system_settings",
    "update_user_settings",
    "validate_api_csrf",
    "validate_api_session",
    "validate_governed_api_request",
    "validate_metric_labels",
    "verify_api_password",
)


def build_api_metadata(**values: object) -> ApiMetadata:
    """Build a validated API metadata envelope.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import ApiMetadata

    return ApiMetadata.model_validate(values)


def build_api_error(**values: object) -> ApiError:
    """Build a validated API error envelope.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import ApiError

    return ApiError.model_validate(values)


def build_api_response(**values: object) -> ApiResponse[object]:
    """Build a validated API response envelope.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import ApiResponse

    return ApiResponse[object].model_validate(values)


def build_governed_request_context(**values: object) -> GovernedRequestContext:
    """Build a validated governed-request context contract.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import GovernedRequestContext

    return GovernedRequestContext.model_validate(values)


def build_page_context(**values: object) -> PageContext:
    """Build a validated page context.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import PageContext

    return PageContext.model_validate(values)


def build_research_run_request(**values: object) -> ResearchRunRequest:
    """Build a validated `ResearchRunRequest`.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.workstation.research.schemas import ResearchRunRequest

    return ResearchRunRequest.model_validate(values)


def build_route_contract(**values: object) -> RouteContract:
    """Build a validated route contract declaration.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import RouteContract

    return RouteContract.model_validate(values)


def build_health_dependency_check(**values: object) -> HealthDependencyCheck:
    """Build one validated readiness-dependency check.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import HealthDependencyCheck

    return HealthDependencyCheck.model_validate(values)


def build_route_contract_registry(
    contracts: tuple[RouteContract, ...] | list[RouteContract] = (),
) -> RouteContractRegistry:
    """Build a deterministic route-contract registry.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.catalog import RouteContractRegistry

    return RouteContractRegistry(tuple(contracts))


def build_stream_event(**values: object) -> StreamEvent:
    """Build a validated stream event envelope.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.contracts.models import StreamEvent

    return StreamEvent.model_validate(values)


def get_route_contract_registry() -> RouteContractRegistry:
    """Return the canonical process-wide route contract registry."""
    from app.services.api.contracts.catalog import ROUTE_CONTRACT_REGISTRY

    return ROUTE_CONTRACT_REGISTRY


def get_canonical_route_contract_registry() -> RouteContractRegistry:
    """Return a fresh unmodified canonical route registry."""
    from app.services.api.contracts.catalog import (
        create_canonical_route_contract_registry,
    )

    return create_canonical_route_contract_registry()


def register_route_contract(contract: RouteContract) -> None:
    """Register one route contract in the canonical API registry."""
    from app.services.api.contracts import (
        register_route_contract as _register_route_contract,
    )

    _register_route_contract(contract)


def build_critical_operational_alert(**values: object) -> CriticalOperationalAlert:
    """Build a validated `CriticalOperationalAlert` through API accessors.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.alerts.models import CriticalOperationalAlert

    return CriticalOperationalAlert.model_validate(values)


def build_critical_alert_delivery_result(
    **values: object,
) -> CriticalAlertDeliveryResult:
    """Build a validated `CriticalAlertDeliveryResult`.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.alerts.models import CriticalAlertDeliveryResult

    return CriticalAlertDeliveryResult.model_validate(values)


def build_critical_alert_trigger(member_name: str) -> CriticalAlertTrigger:
    """Resolve one public alert trigger member by name.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.alerts.models import CriticalAlertTrigger

    return CriticalAlertTrigger[member_name]


def get_critical_alert_error_type() -> type[CriticalAlertError]:
    """Return the alert construction error class."""
    from app.services.api.alerts.models import CriticalAlertError

    return CriticalAlertError


def create_in_process_metric_sink(
    *,
    max_series: int | None = None,
    max_label_cardinality: int | None = None,
) -> MetricSink:
    """Create one explicit in-process metric sink with optional limits.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.observability import (
        create_in_process_metric_sink as _create_sink,
    )

    return _create_sink(
        max_series=max_series,
        max_label_cardinality=max_label_cardinality,
    )


def record_metric(
    name: str,
    value: Decimal,
    *,
    labels: Mapping[str, str],
    sink: MetricSink,
) -> None:
    """Record one validated metric through an explicit sink."""
    from app.services.api.observability import record_metric as _record_metric

    _record_metric(
        name=name,
        value=value,
        labels=labels,
        sink=sink,
    )


def validate_metric_labels(labels: Mapping[str, str]) -> None:
    """Validate metric labels before sink mutation."""
    from app.services.api.observability import (
        validate_metric_labels as _validate_metric_labels,
    )

    _validate_metric_labels(labels)


def build_metric_snapshot(sink: MetricSink) -> MetricSnapshot:
    """Build one bounded, immutable metric snapshot.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.observability import (
        build_metric_snapshot as _build_metric_snapshot,
    )

    return _build_metric_snapshot(sink)


def export_prometheus_metrics(snapshot: MetricSnapshot) -> str:
    """Render one deterministic Prometheus exposition payload.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.observability import (
        export_prometheus_metrics as _export_prometheus_metrics,
    )

    return _export_prometheus_metrics(snapshot)


def get_metrics(
    context: AuthContext,
    *,
    sink: MetricSink,
) -> object:
    """Render a redacted metric exposition response from one injected sink.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.observability import get_metrics as _get_metrics

    return _get_metrics(context, sink=sink)


def check_clock_drift(
    reference: datetime,
    *,
    tolerance_seconds: Decimal | int | str | None = None,
) -> Decimal:
    """Measure signed local-clock drift as a readiness-only diagnostic.

    Returns:
        The validated, bounded result.
    """
    if tolerance_seconds is None:
        from app.services.api.health.clock import CLOCK_DRIFT_TOLERANCE_SECONDS

        tolerance_seconds = CLOCK_DRIFT_TOLERANCE_SECONDS
    from app.services.api.health.clock import check_clock_drift as _check_clock_drift

    return _check_clock_drift(
        reference,
        tolerance_seconds=tolerance_seconds,
    )


def get_liveness() -> ApiResponse[Liveness]:
    """Build a bounded public liveness response.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.health.probes import get_liveness as _get_liveness

    return _get_liveness()


def get_readiness(context: AuthContext) -> ApiResponse[Readiness]:
    """Build a bounded protected readiness response after ops authorization.

    Returns:
        The validated, bounded result.
    """
    from app.services.api.health.probes import get_readiness as _get_readiness

    return _get_readiness(context)


def build_request_context_middleware(
    app: ASGIApp,
    *,
    route_contract_registry: RouteContractRegistry | None = None,
    auth_context_provider: Callable[[Request], object] | None = None,
    request_id_header: str = "x-request-id",
    correlation_id_header: str = "x-correlation-id",
) -> object:
    """Build a request-context middleware from explicit constructor inputs.

    Returns:
        The validated, bounded result.
    """
    return _build_request_context_middleware(
        app,
        route_contract_registry=route_contract_registry,
        auth_context_provider=auth_context_provider,
        request_id_header=request_id_header,
        correlation_id_header=correlation_id_header,
    )


def build_secret_redaction_middleware(
    app: ASGIApp,
    *,
    redaction_policy: object | None = None,
    event_emitter: EventEmitter | None = None,
) -> object:
    """Build a secret-redaction middleware from explicit constructor inputs.

    Returns:
        The validated, bounded result.
    """
    return _build_secret_redaction_middleware(
        app,
        redaction_policy=cast("Any", redaction_policy),
        event_emitter=event_emitter,
    )


def build_simulation_workbench_source(**values: object) -> object:
    """Build the Simulation Workbench dispatch source.

    Returns:
        Callable dispatching one allowlisted workbench operation.
    """
    from app.services.api.workstation.simulation_workbench.orchestration import (
        build_simulation_workbench_source as _build,
    )

    return _build(**cast("Any", values))


def build_simulation_workbench_live_authority(
    dependencies: object | None = None, **values: object
) -> object:
    """Build the interactive live-session authority for the workbench.

    Args:
        dependencies: Composed Simulator run dependency bundle.
        **values: Optional ``reproduction_runner`` composition seam.

    Returns:
        Callable dispatching one named interactive operation.
    """
    from app.services.api.workstation.simulation_workbench.orchestration import (
        build_simulation_workbench_live_authority as _build,
    )

    return _build(dependencies, **cast("Any", values))


def build_simulation_workbench_registry(**values: object) -> object:
    """Build the Simulation Workbench catalogue transition registry.

    Returns:
        Opaque registry consumed by the gateway orchestration.
    """
    from app.services.api.workstation.simulation_workbench.registry import (
        build_simulation_workbench_registry as _build,
    )

    return _build(**cast("Any", values))


def build_analytics_workbench_source(**values: object) -> object:
    """Build the Analytics Workbench dispatch source.

    Returns:
        Callable dispatching one allowlisted Analytics Workbench operation.
    """
    from app.services.api.workstation.analytics_workbench.orchestration import (
        build_analytics_workbench_source as _build,
    )

    return _build(**cast("Any", values))


def build_analytics_workbench_composition(settings: object) -> object:
    """Build the production Analytics Workbench source from runtime settings.

    Args:
        settings: API runtime settings owning the simulation artifact root.

    Returns:
        Dispatch source with catalogue-backed report and result readers.
    """
    from app.services.api.workstation.analytics_workbench.orchestration import (
        build_analytics_workbench_composition as _build,
    )

    return _build(settings)


def build_api_settings(**values: object) -> object:
    """Build validated immutable API settings.

    Returns:
        Validated API settings.
    """
    from app.services.api.workstation.settings.bootstrap import ApiSettings

    return ApiSettings.model_validate(values)


def get_api_settings() -> object:
    """Return process-cached validated API settings.

    Returns:
        Validated API settings.
    """
    from app.services.api.workstation.settings.bootstrap import (
        get_api_settings as _get_api_settings,
    )

    return _get_api_settings()


def create_api_app(
    config: object | None = None,
    *,
    in_process_graph: object | None = None,
    dependency_overrides: Mapping[Callable[..., object], Callable[..., object]]
    | None = None,
    simulation_dependencies: object | None = None,
    trading_dependencies: object | None = None,
    portfolio_dependencies: object | None = None,
    optimization_dependencies: object | None = None,
    agentic_dependencies: object | None = None,
) -> object:
    """Construct the canonical application through the package boundary.

    Returns:
        Canonical FastAPI application.
    """
    from app.services.api.composition import create_app
    from app.services.api.workstation.settings.bootstrap import ApiSettings

    typed_config = config if isinstance(config, ApiSettings) else None
    return create_app(
        typed_config,
        in_process_graph=in_process_graph,
        dependency_overrides=dependency_overrides,
        simulation_dependencies=simulation_dependencies,
        trading_dependencies=trading_dependencies,
        portfolio_dependencies=portfolio_dependencies,
        optimization_dependencies=optimization_dependencies,
        agentic_dependencies=agentic_dependencies,
    )


def build_api_portfolio_dependencies(**values: object) -> object:
    """Compose the complete Portfolio receiver-owned dependency bundle.

    Returns:
        Opaque Portfolio dependency bundle.
    """
    from app.services.api.composition import (
        build_api_portfolio_dependencies as build,
    )

    return build(**cast("Any", values))


def build_api_strategy_dependencies(**values: object) -> object:
    """Compose the Strategy validation-policy bundle for governed mutations.

    Returns:
        Opaque Strategy dependency bundle.
    """
    from app.services.api.composition import (
        build_api_strategy_dependencies as build,
    )

    return build(**cast("Any", values))


def build_api_risk_dependencies(**values: object) -> object:
    """Compose the Risk kill-switch command authority bundle.

    Returns:
        Opaque Risk dependency bundle.
    """
    from app.services.api.composition import (
        build_api_risk_dependencies as build,
    )

    return build(**cast("Any", values))


def build_api_agentic_dependencies(**values: object) -> object:
    """Compose the complete Agentic ``AgenticDependencies`` bundle.

    Returns:
        Opaque Agentic dependency bundle.
    """
    from app.services.api.composition import (
        build_api_agentic_dependencies as build,
    )

    return build(**cast("Any", values))


def build_api_optimization_dependencies(**values: object) -> object:
    """Compose the complete Optimization receiver-owned dependency bundle.

    Returns:
        Opaque Optimization dependency bundle.
    """
    from app.services.api.composition import (
        build_api_optimization_dependencies as build,
    )

    return build(**cast("Any", values))


def build_api_simulation_dependencies(**values: object) -> object:
    """Compose the complete Simulator receiver-owned dependency bundle.

    Returns:
        Opaque Simulator dependency bundle.
    """
    from app.services.api.composition import build_api_simulation_dependencies as build

    return build(**cast("Any", values))


def build_api_trading_dependencies(**values: object) -> object:
    """Compose the complete Trading-owned dependency container.

    Returns:
        Opaque Trading dependency container.
    """
    from app.services.api.composition import build_api_trading_dependencies as build

    return build(**cast("Any", values))


def build_in_process_api_graph(
    providers: Mapping[str, object],
    *,
    owned_resource_closers: tuple[Callable[[], object], ...] = (),
) -> object:
    """Build one validated in-process owner dependency graph.

    Returns:
        Opaque graph accepted by :func:`create_api_app`.
    """
    from app.services.api.composition import build_in_process_graph

    return build_in_process_graph(
        providers,
        owned_resource_closers=owned_resource_closers,
    )


def get_required_in_process_provider_names() -> tuple[str, ...]:
    """Return the exact required in-process provider manifest.

    Returns:
        Stable provider-name tuple.
    """
    from app.services.api.composition import get_required_provider_names

    return get_required_provider_names()


def hash_api_password(password: str) -> str:
    """Hash one API-owned password without fallback.

    Returns:
        Serialized memory-hard password hash.
    """
    from app.services.api.identity import hash_password

    return hash_password(password)


def authenticate_api_user(**values: object) -> object:
    """Authenticate one API-owned account.

    Returns:
        Current server-authoritative user claims.
    """
    from app.services.api.identity import authenticate_user

    return authenticate_user(**cast("Any", values))


def verify_api_password(password: str, encoded_hash: str) -> bool:
    """Verify one API-owned password hash.

    Returns:
        Whether the password matches.
    """
    from app.services.api.identity import verify_password

    return verify_password(password, encoded_hash)


def register_api_user(**values: object) -> object:
    """Register one UI/API-owned user account.

    Returns:
        Secret-free authenticated user claims.
    """
    from app.services.api.identity import register_user

    return register_user(**cast("Any", values))


def create_api_session(user: object, **values: object) -> object:
    """Create and persist one opaque API session.

    Returns:
        One-time opaque session credential.
    """
    from app.services.api.identity import create_session

    return create_session(cast("Any", user), **cast("Any", values))


def validate_api_session(session_token: str, **values: object) -> object:
    """Validate one opaque API session.

    Returns:
        Current authenticated user claims.
    """
    from app.services.api.identity import validate_session

    return validate_session(session_token, **cast("Any", values))


def recover_api_session_identity(session_token: str, **values: object) -> object:
    """Recover non-secret display identity from one opaque API session.

    Returns:
        Current user identity and exact session expiry.
    """
    from app.services.api.identity import recover_session_identity

    return recover_session_identity(session_token, **cast("Any", values))


def revoke_api_session(session_token: str, **values: object) -> None:
    """Idempotently revoke one opaque API session."""
    from app.services.api.identity import revoke_session

    revoke_session(session_token, **cast("Any", values))


def store_api_credential(**values: object) -> object:
    """Encrypt and persist one API-owned credential.

    Returns:
        Secret-free credential record.
    """
    from app.services.api.identity import store_credential

    return store_credential(**cast("Any", values))


def resolve_api_credential_reference(reference: str, **values: object) -> object:
    """Resolve an authorized opaque credential reference.

    Returns:
        In-memory secret values for immediate composition.
    """
    from app.services.api.identity import resolve_credential_reference

    return resolve_credential_reference(
        reference,
        **cast("Any", values),
    )


def resolve_system_credential_slot(slot: str, *, request_id: str) -> object:
    """Resolve one system credential slot for immediate in-process composition.

    Args:
        slot: Manifest-approved system credential slot.
        request_id: Canonical request identifier.

    Returns:
        In-memory secret values for immediate use by an authorized composition.

    Raises:
        ValueError: If bootstrap encryption-key configuration is unavailable.
        TypeError: If the typed API settings snapshot is unavailable.
        IdentityError: If the credential is unavailable or cannot be verified.
    """
    from app.services.api.composition.runtime_settings import build_credential_key_set
    from app.services.api.identity import resolve_credential_reference
    from app.services.api.workstation.settings.bootstrap import ApiSettings
    from app.utils import derive_stable_id

    reference_id = derive_stable_id("id", f"api-credential:system:{slot}")
    settings = get_api_settings()
    if not isinstance(settings, ApiSettings):
        raise TypeError("API settings are unavailable")
    return resolve_credential_reference(
        f"secret://{reference_id}",
        owner_id="system",
        key_set=build_credential_key_set(settings),
        request_id=request_id,
    )


def get_credential_manifest() -> object:
    """Return secret-free credential-slot definitions.

    Returns:
        Ordered credential manifest mappings.
    """
    from app.services.api.identity import get_credential_manifest as _get_manifest

    return _get_manifest()


def get_system_credential_statuses(**values: object) -> object:
    """Return secret-free status for system credential slots.

    Returns:
        Ordered credential status mappings.
    """
    from app.services.api.identity import (
        get_system_credential_statuses as _get_statuses,
    )

    return _get_statuses(**cast("Any", values))


def store_system_credential(
    slot: str,
    material: Mapping[str, str],
    **values: object,
) -> object:
    """Validate, encrypt, and persist one system credential slot.

    Returns:
        Secret-free credential metadata.
    """
    from app.services.api.identity import store_system_credential as _store_credential

    return _store_credential(
        slot,
        material,
        **cast("Any", values),
    )


def build_broker_connection_config(**values: object) -> object:
    """Resolve credentials and construct a Brokers-owned connection config.

    Returns:
        Immutable Brokers-owned connection configuration.
    """
    from app.services.api.composition import (
        build_broker_connection_config as _build_broker_connection_config,
    )

    return _build_broker_connection_config(**cast("Any", values))


def build_system_broker_connection_config(broker_id: str, *, request_id: str) -> object:
    """Build a provider config from stored system settings and credentials.

    Args:
        broker_id: Exact Brokers provider identifier.
        request_id: Canonical request identifier.

    Returns:
        Immutable Brokers-owned non-production connection configuration.
    """
    from app.services.api.composition import (
        build_system_broker_connection_config as _build_system_config,
    )

    return _build_system_config(broker_id, request_id=request_id)


def get_user_settings(user_id: str, **values: object) -> object:
    """Read one user's versioned settings.

    Returns:
        Current settings record.
    """
    from app.services.api.identity import get_user_settings as _get_user_settings

    return _get_user_settings(user_id, **cast("Any", values))


def get_system_settings(**values: object) -> object:
    """Read the global versioned non-secret system settings.

    Returns:
        Current global settings record.
    """
    from app.services.api.identity import get_system_settings as _get_system_settings

    return _get_system_settings(**cast("Any", values))


def get_system_settings_manifest() -> object:
    """Return secret-free system-settings field definitions.

    Returns:
        Ordered system-settings manifest mappings.
    """
    from app.services.api.identity import get_system_settings_manifest as _get_manifest

    return _get_manifest()


def get_legacy_settings_classification() -> object:
    """Return the exhaustive legacy-file migration classification.

    Returns:
        Source paths classified as system, credential, or external bootstrap.
    """
    from app.services.api.identity import (
        get_legacy_settings_classification as _get_classification,
    )

    return _get_classification()


def update_user_settings(
    user_id: str,
    settings: Mapping[str, str],
    **values: object,
) -> object:
    """Optimistically replace one user's settings.

    Returns:
        Updated versioned settings record.
    """
    from app.services.api.identity import update_user_settings as _update_settings

    return _update_settings(
        user_id,
        settings,
        **cast("Any", values),
    )


def update_system_settings(
    settings: Mapping[str, str],
    **values: object,
) -> object:
    """Optimistically replace global non-secret system settings.

    Returns:
        Updated global settings record.
    """
    from app.services.api.identity import (
        update_system_settings as _update_system_settings,
    )

    return _update_system_settings(
        settings,
        **cast("Any", values),
    )


def run_api_migrations(request_id: str) -> object:
    """Run the immutable API-owned migration manifest.

    Returns:
        Data-owned migration response.
    """
    from app.services.api.composition.migrations import (
        run_api_migrations as _run_api_migrations,
    )

    return _run_api_migrations(request_id)


def create_stream_manager(**values: object) -> object:
    """Create a bounded ordered stream connection manager.

    Returns:
        Internal stream manager through its function-only public factory.
    """
    from app.services.api.workstation.event_delivery import (
        create_stream_connection_manager as _create_manager,
    )

    return _create_manager(**cast("Any", values))


def normalize_stream_event(event: object, trace: object) -> StreamEvent:
    """Normalize one owner event into the canonical stream envelope.

    Returns:
        Validated stream event.
    """
    from app.services.api.workstation.event_delivery import (
        build_stream_event as _build_stream_event,
    )

    return _build_stream_event(event, trace)


def build_authoritative_auth_context(
    *,
    principal: object,
    trace: object,
) -> object:
    """Build a Utils-owned context from verified authority claims.

    Returns:
        Immutable authenticated request context.
    """
    from app.services.api.identity import build_auth_context

    return build_auth_context(
        principal=cast("Any", principal),
        trace=cast("Any", trace),
    )


def require_api_permission(context: object, permission: str) -> None:
    """Require one exact backend permission."""
    from app.services.api.identity import require_permission

    require_permission(cast("Any", context), permission)


def validate_governed_api_request(context: object, governed: object) -> None:
    """Validate governed evidence without granting owner authority."""
    from app.services.api.identity import validate_governed_request

    validate_governed_request(
        cast("Any", context),
        cast("Any", governed),
    )


def create_api_approval(**values: object) -> object:
    """Create one scoped distinct-principal approval.

    Returns:
        Persisted secret-free approval record.
    """
    from app.services.api.identity import create_approval

    return create_approval(**cast("Any", values))


def consume_api_approval(approval_id: str, **values: object) -> object:
    """Atomically consume one exact scoped approval.

    Returns:
        Consumed approval record.
    """
    from app.services.api.identity import consume_approval

    return consume_approval(approval_id, **cast("Any", values))


def reserve_api_idempotency_key(**values: object) -> object:
    """Reserve a principal/method/route scoped idempotency key.

    Returns:
        Reservation or terminal replay decision.
    """
    from app.services.api.identity import reserve_idempotency_key

    return reserve_idempotency_key(**cast("Any", values))


def finalize_api_idempotency_key(**values: object) -> None:
    """Persist one terminal replay-safe idempotency response."""
    from app.services.api.identity import finalize_idempotency_key

    finalize_idempotency_key(**cast("Any", values))


def validate_api_csrf(
    session_token: str,
    csrf_token: str,
    **values: object,
) -> None:
    """Validate a double-submit token against a persisted session."""
    from app.services.api.identity import validate_csrf

    validate_csrf(
        session_token,
        csrf_token,
        **cast("Any", values),
    )


def get_default_watchlist_symbols() -> tuple[str, ...]:
    """Return the immutable default-watchlist seed symbols."""
    from app.services.api.workstation.watchlists import DEFAULT_WATCHLIST_SYMBOLS

    return DEFAULT_WATCHLIST_SYMBOLS


def get_api_identity_error_type() -> type[Exception]:
    """Return the API identity error type without exporting a class."""
    from app.services.api.identity import IdentityError

    return IdentityError


def list_account_watchlists(
    account_id: str, *, source_id: str, request_id: str
) -> tuple[object, ...]:
    """List one account's watchlists through the API public boundary.

    Returns:
        Account-owned watchlists in display order.
    """
    from app.services.api.workstation.watchlists import list_watchlists

    return cast(
        "tuple[object, ...]",
        list_watchlists(account_id, source_id=source_id, request_id=request_id),
    )


def get_account_watchlist(
    watchlist_id: str, account_id: str, *, request_id: str
) -> object:
    """Return one account-owned watchlist."""
    from app.services.api.workstation.watchlists import get_watchlist

    return get_watchlist(watchlist_id, account_id, request_id=request_id)


def create_account_watchlist(account_id: str, name: str, *, request_id: str) -> object:
    """Create one account-owned watchlist.

    Returns:
        Created watchlist.
    """
    from app.services.api.workstation.watchlists import create_watchlist

    return create_watchlist(account_id, name, request_id=request_id)


def rename_account_watchlist(
    watchlist_id: str,
    account_id: str,
    name: str,
    *,
    request_id: str,
) -> object:
    """Rename one account-owned watchlist.

    Returns:
        Renamed watchlist.
    """
    from app.services.api.workstation.watchlists import rename_watchlist

    return rename_watchlist(watchlist_id, account_id, name, request_id=request_id)


def set_default_account_watchlist(
    watchlist_id: str, account_id: str, *, request_id: str
) -> object:
    """Promote one account-owned watchlist to the default.

    Returns:
        Updated default watchlist.
    """
    from app.services.api.workstation.watchlists import set_default_watchlist

    return set_default_watchlist(watchlist_id, account_id, request_id=request_id)


def replace_account_watchlist_items(
    watchlist_id: str,
    account_id: str,
    symbols: tuple[str, ...],
    *,
    source_id: str,
    request_id: str,
) -> object:
    """Replace one account-owned watchlist's ordered symbols.

    Returns:
        Updated watchlist.
    """
    from app.services.api.workstation.watchlists import replace_watchlist_items

    return replace_watchlist_items(
        watchlist_id,
        account_id,
        symbols,
        source_id=source_id,
        request_id=request_id,
    )


def delete_account_watchlist(
    watchlist_id: str, account_id: str, *, request_id: str
) -> None:
    """Delete one non-default account watchlist."""
    from app.services.api.workstation.watchlists import delete_watchlist

    delete_watchlist(watchlist_id, account_id, request_id=request_id)
