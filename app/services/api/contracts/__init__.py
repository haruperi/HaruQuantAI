"""Public UI/API boundary contracts."""

from app.services.api.contracts.catalog import (
    ROUTE_CONTRACT_REGISTRY,
    RouteContractRegistry,
    register_route_contract,
)
from app.services.api.contracts.models import (
    ApiError,
    ApiErrorCode,
    ApiMetadata,
    ApiResponse,
    ApiStatus,
    GovernedRequestContext,
    HealthDependencyCheck,
    Liveness,
    PageContext,
    Readiness,
    RouteContract,
    StreamEvent,
)

__all__ = (
    "ROUTE_CONTRACT_REGISTRY",
    "ApiError",
    "ApiErrorCode",
    "ApiMetadata",
    "ApiResponse",
    "ApiStatus",
    "GovernedRequestContext",
    "HealthDependencyCheck",
    "Liveness",
    "PageContext",
    "Readiness",
    "RouteContract",
    "RouteContractRegistry",
    "StreamEvent",
    "register_route_contract",
)
