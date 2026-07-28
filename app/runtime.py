"""System-level runtime initialization validation."""

import time
from typing import Any, Final

from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_common_error_catalog,
    get_logger,
    success_response,
)

logger = get_logger(__name__)

_EXECUTION_ROUTE_BY_PROFILE: Final[dict[str, str]] = {
    "research": "none",
    "simulation": "sim",
    "paper": "paper",
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
) -> Any:
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
        response = error_response(
            code=_ERROR_CODE,
            details={"detail": _ERROR_DETAIL},
            message=_ERROR_MESSAGE,
            metadata=metadata,
            catalog=get_common_error_catalog(),
        )
        return response
    return success_response(
        None,
        message=_SUCCESS_MESSAGE,
        metadata=metadata,
    )
