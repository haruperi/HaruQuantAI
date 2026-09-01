"""Health probes and public service readiness contracts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any, Final, Literal, NoReturn

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.kernel.time import utc_now
from app.services.api.contracts.models import (
    ApiErrorCode,
    ApiMetadata,
    ApiResponse,
    ApiStatus,
    HealthDependencyCheck,
    Liveness,
    Readiness,
)
from app.services.api.health.clock import (
    CLOCK_DRIFT_TOLERANCE_SECONDS,
    check_clock_drift,
)
from app.services.api.identity import require_human_permission

logger = get_logger(__name__)
type AuthContext = Any

_DEPENDENCY_TOLERANCE_SECONDS: Final[Decimal] = CLOCK_DRIFT_TOLERANCE_SECONDS
_DEPENDENCY_REFERENCE: Callable[[], datetime] = utc_now


def _readiness_dependency_reference() -> datetime:
    """Read one drift reference timestamp from the injected provider.

    Returns:
        The validated, bounded result.
    """
    return _DEPENDENCY_REFERENCE()


def _build_liveness(now: datetime) -> Liveness:
    """Build one bounded liveness payload.

    Returns:
        The validated, bounded result.
    """
    return Liveness(status="healthy", checked_at=now)


def _build_process_dependency(now: datetime) -> HealthDependencyCheck:
    """Build the required process-level dependency probe.

    Returns:
        The validated, bounded result.
    """
    return HealthDependencyCheck(
        component="api.process",
        required=True,
        healthy=True,
        checked_at=now,
    )


def _build_clock_dependency(
    now: datetime,
    *,
    reference: datetime,
) -> tuple[HealthDependencyCheck, Decimal]:
    """Build the optional clock probe and signed drift.

    Returns:
        The validated, bounded result.
    """
    drift = check_clock_drift(
        reference,
        tolerance_seconds=_DEPENDENCY_TOLERANCE_SECONDS,
    )
    healthy = drift.copy_abs() <= _DEPENDENCY_TOLERANCE_SECONDS
    reason = None
    if not healthy:
        reason = (
            f"clock drift exceeds tolerance: {drift} seconds "
            f"(<= {_DEPENDENCY_TOLERANCE_SECONDS})"
        )
    return (
        HealthDependencyCheck(
            component="api.clock",
            required=False,
            healthy=healthy,
            checked_at=now,
            reason=reason,
        ),
        drift,
    )


def _collect_readiness_dependencies(
    *,
    now: datetime,
) -> tuple[tuple[HealthDependencyCheck, ...], Decimal]:
    """Collect one required and one optional dependency probe.

    Returns:
        The validated, bounded result.
    """
    reference = _readiness_dependency_reference()
    clock_probe, clock_drift = _build_clock_dependency(now, reference=reference)
    dependencies = (
        _build_process_dependency(now),
        clock_probe,
    )
    return dependencies, clock_drift


def _dependency_unavailable(*, detail: str, code: str) -> NoReturn:
    """Return a deterministic dependency-unavailable response.

    Raises:
        HTTPException: If the declared validation fails.
    """
    logger.warning("Readiness dependency unavailable: %s", detail)
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=code)


def _build_readiness_response(
    now: datetime,
    dependencies: tuple[HealthDependencyCheck, ...],
    clock_drift_seconds: Decimal,
) -> Readiness:
    """Convert probes into one bounded readiness payload.

    Returns:
        The validated, bounded result.
    """
    optional_failed = [
        dep for dep in dependencies if not dep.required and not dep.healthy
    ]
    readiness_status: Literal["ready", "degraded"] = "ready"
    if optional_failed:
        readiness_status = "degraded"
    return Readiness(
        status=readiness_status,
        checked_at=now,
        clock_drift_seconds=clock_drift_seconds,
        dependencies=dependencies,
    )


def _response_metadata(
    *,
    route: str,
    operation: str,
    request_id: str,
    trace_id: str | None = None,
) -> ApiMetadata:
    """Build a bounded metadata envelope.

    Returns:
        The validated, bounded result.
    """
    return ApiMetadata(
        request_id=request_id,
        route=route,
        operation=operation,
        trace_id=trace_id,
    )


def get_liveness() -> ApiResponse[Liveness]:
    """Return coarse process liveness and stable health status."""
    now = utc_now()
    payload = _build_liveness(now)
    metadata = ApiMetadata(
        request_id=generate_id("req"),
        route="/api/v1/health/liveness",
        operation="api.get_liveness",
        trace_id=None,
    )
    return ApiResponse(
        status=ApiStatus.SUCCESS,
        message="service is healthy",
        data=payload,
        metadata=metadata,
    )


def get_readiness(context: AuthContext) -> ApiResponse[Readiness]:
    """Return protected readiness with required and optional dependency checks.

    Args:
        context: Authenticated human context with `ops:read` permission.

    Returns:
        API response containing one bounded readiness payload.

    Raises:
        HTTPException: If authorization or required dependency checks fail.
    """
    require_human_permission(context, "ops:read")
    now = utc_now()
    try:
        dependencies, clock_drift = _collect_readiness_dependencies(now=now)
    except ValidationError as error:
        _dependency_unavailable(
            detail=str(error),
            code=ApiErrorCode.DEPENDENCY_UNAVAILABLE,
        )

    required_failures = [
        dep for dep in dependencies if dep.required and not dep.healthy
    ]
    if required_failures:
        _dependency_unavailable(
            detail=required_failures[0].reason or "required dependency unavailable",
            code=ApiErrorCode.DEPENDENCY_UNAVAILABLE,
        )

    payload = _build_readiness_response(
        now=now,
        dependencies=dependencies,
        clock_drift_seconds=clock_drift,
    )
    metadata = _response_metadata(
        route="/api/v1/health/readiness",
        operation="api.get_readiness",
        request_id=context.request_id,
        trace_id=context.correlation_id,
    )
    return ApiResponse(
        status=ApiStatus.SUCCESS,
        message="service readiness assessed",
        data=payload,
        metadata=metadata,
    )
