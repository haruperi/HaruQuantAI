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
        ResearchRunRequest,
        RouteContract,
        StreamEvent,
    )
    from app.services.api.middleware.redaction import EventEmitter
    from app.services.api.observability.exposition import MetricSnapshot
    from app.services.api.observability.sinks import MetricSink
type AuthContext = Any

__all__ = (
    "build_api_error",
    "build_api_metadata",
    "build_api_response",
    "build_critical_alert_delivery_result",
    "build_critical_alert_trigger",
    "build_critical_operational_alert",
    "build_governed_request_context",
    "build_health_dependency_check",
    "build_kill_switch_activation_alert",
    "build_metric_snapshot",
    "build_page_context",
    "build_request_context_middleware",
    "build_research_run_request",
    "build_route_contract",
    "build_route_contract_registry",
    "build_secret_redaction_middleware",
    "build_stream_event",
    "build_unknown_broker_state_alert",
    "check_clock_drift",
    "create_in_process_metric_sink",
    "deliver_critical_alert",
    "export_prometheus_metrics",
    "get_critical_alert_error_type",
    "get_liveness",
    "get_metrics",
    "get_readiness",
    "get_route_contract_registry",
    "record_metric",
    "register_route_contract",
    "validate_metric_labels",
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
    from app.services.api.contracts.models import ResearchRunRequest

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
