"""System-level runtime initialization validation."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Final

from app.kernel.errors import CapabilityUnavailableError
from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_common_error_catalog,
    get_logger,
    success_response,
)

if TYPE_CHECKING:
    from app.kernel.profiles import ProfileReadiness

logger = get_logger(__name__)

_EXECUTION_ROUTE_BY_PROFILE: Final[dict[str, str]] = {
    "research": "none",
    "simulation": "sim",
    "demo": "demo",
    "live": "live",
}
_ERROR_CODE: Final[str] = "SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"
_ERROR_DETAIL: Final[str] = "RUNTIME_PROFILE_EXECUTION_ROUTE_INCOMPATIBLE"
_ERROR_MESSAGE: Final[str] = "Runtime profile and execution route are incompatible"
_SUCCESS_MESSAGE: Final[str] = "Runtime profile and execution route are compatible"


def validate_runtime_configuration(
    *,
    runtime_profile: str,
    execution_route: str,
) -> object:
    """Validate the authoritative runtime profile and route pairing.

    Args:
        runtime_profile: Runtime profile selected by Utils-owned configuration.
        execution_route: Execution route selected by Trading-owned configuration.

    Returns:
        A successful response containing raw ``None`` when the pair is
        compatible, or a value-free structured error response otherwise.
    """
    start_time = time.perf_counter_ns()
    request_id = generate_id("req")
    expected_route = _EXECUTION_ROUTE_BY_PROFILE.get(runtime_profile)
    is_compatible = expected_route is not None and execution_route == expected_route
    if is_compatible:
        logger.info("Accepted runtime profile and execution route")
    else:
        logger.warning("Rejected runtime profile and execution route")
    metadata = build_response_metadata(
        name="app.runtime.validate_runtime_configuration",
        domain="app",
        risk_level="none",
        request_id=request_id,
        start_time=start_time,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
    )
    if not is_compatible:
        return error_response(
            code=_ERROR_CODE,
            details={"detail": _ERROR_DETAIL},
            message=_ERROR_MESSAGE,
            metadata=metadata,
            catalog=get_common_error_catalog(),
        )
    return success_response(
        None,
        message=_SUCCESS_MESSAGE,
        metadata=metadata,
    )


def validate_runtime_capability_readiness(
    *,
    runtime_profile: str,
    execution_route: str,
    readiness: tuple[ProfileReadiness, ...],
) -> object:
    """Validate runtime profile, execution route, and capability readiness.

    Args:
        runtime_profile: Runtime profile selected by Utils-owned configuration.
        execution_route: Execution route selected by Trading-owned configuration.
        readiness: Tuple of ProfileReadiness assessment objects.

    Returns:
        A successful response when the pair is compatible and capability
        requirements are satisfied, or a value-free structured error response otherwise.

    Raises:
        ValueError: If runtime_profile is not found exactly once in readiness.
        CapabilityUnavailableError: If the matched profile is not ready.
    """
    config_result = validate_runtime_configuration(
        runtime_profile=runtime_profile,
        execution_route=execution_route,
    )
    if getattr(config_result, "status", None) != "success":
        return config_result
    if isinstance(config_result, dict) and not config_result.get("success", True):
        return config_result

    matching = [
        r
        for r in readiness
        if r.profile == runtime_profile or str(r.profile.value) == runtime_profile
    ]
    if len(matching) != 1:
        msg = f"profile readiness missing or duplicated: {runtime_profile}"
        raise ValueError(msg)

    profile_readiness = matching[0]
    if not profile_readiness.ready:
        sorted_missing = sorted(profile_readiness.missing, key=lambda m: m.capability)
        raise CapabilityUnavailableError(sorted_missing[0])

    return config_result
