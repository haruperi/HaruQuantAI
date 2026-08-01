"""Route and stream contract registry helpers for API drift checks."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from app.services.api.contracts.models import (
    RouteContract,
    RouteSideEffect,
    RouteStability,
)

RouteContractMap = dict[str, RouteContract]
_PATH_PARAMETER_PATTERN = re.compile(r"\{[^/{}]+\}")


def _route_key(method: str, path: str) -> str:
    """Build a normalized route key from method and path.

    Args:
        method: HTTP method.
        path: Route path.

    Returns:
        Normalized route key string.
    """
    return f"{method.upper()} {path.rstrip('/')}"


class RouteContractRegistry:
    """Small deterministic registry for `RouteContract` declarations."""

    def __init__(self, contracts: Iterable[RouteContract]) -> None:
        """Create a deterministic contract registry.

        Args:
            contracts: Deterministic iterable of route contracts.
        """
        self._contracts: RouteContractMap = {}
        self._route_ids: dict[str, str] = {}
        self._templates: list[tuple[str, re.Pattern[str], RouteContract]] = []
        for contract in contracts:
            self.register_route_contract(contract)

    def get(self, method: str, path: str) -> RouteContract | None:
        """Get a registered contract by method and path.

        Args:
            method: HTTP method.
            path: Route path.

        Returns:
            Matching route contract, or ``None`` if no contract exists.
        """
        normalized_method = method.upper()
        exact = self._contracts.get(_route_key(normalized_method, path))
        if exact is not None:
            return exact
        for template_method, pattern, contract in self._templates:
            if template_method == normalized_method and pattern.fullmatch(path):
                return contract
        return None

    def register_route_contract(self, contract: RouteContract) -> None:
        """Register one contract and reject duplicates or collisions.

        Args:
            contract: Route contract to register.

        Raises:
            ValueError: Duplicate route key or duplicate route identifier.
        """
        key = _route_key(contract.method, contract.path)
        existing = self._contracts.get(key)
        if existing is not None and existing.route_id != contract.route_id:
            message = (
                "duplicate route declaration for different contract id: "
                + contract.route_id
            )
            raise ValueError(message)
        if (
            contract.route_id in self._route_ids
            and self._route_ids[contract.route_id] != key
        ):
            message = f"duplicate route_id for a different route: {contract.route_id}"
            raise ValueError(message)
        self._contracts[key] = contract
        self._route_ids[contract.route_id] = key
        if _PATH_PARAMETER_PATTERN.search(contract.path):
            escaped = re.escape(contract.path)
            expression = _PATH_PARAMETER_PATTERN.sub(
                "[^/]+",
                escaped.replace(r"\{", "{").replace(r"\}", "}"),
            )
            self._templates.append(
                (contract.method, re.compile(f"^{expression}$"), contract)
            )

    def all(self) -> Iterator[RouteContract]:
        """Yield all registered contracts in insertion order.

        Returns:
            An iterator over registered contracts.
        """
        return iter(tuple(self._contracts.values()))

    @property
    def size(self) -> int:
        """Return the number of registered route contracts."""
        return len(self._contracts)


def _contract(
    route_id: str,
    method: str,
    path: str,
    owner: str,
    permission: str | None = None,
    *,
    side_effect: RouteSideEffect = RouteSideEffect.READ,
    idempotency_policy: str | None = None,
    governance_scope: str = "none",
    success_statuses: tuple[int, ...] = (200,),
) -> RouteContract:
    """Build one complete internal route declaration.

    Returns:
        Validated route contract.
    """
    authenticated = permission is not None
    writes = side_effect in {RouteSideEffect.WRITE, RouteSideEffect.GOVERNED_WRITE}
    if path.startswith("/api/v1/auth/"):
        rate_limit = "authentication"
    elif side_effect == RouteSideEffect.GOVERNED_WRITE:
        rate_limit = "governed_write"
    elif owner in {"optimization", "simulation", "research"} and method != "GET":
        rate_limit = "compute"
    else:
        rate_limit = "read"
    return RouteContract(
        route_id=route_id,
        method=method,
        path=path,
        owner=owner,
        stability=RouteStability.STABLE,
        side_effect=side_effect,
        auth_required=authenticated,
        permission=permission,
        governance_scope=governance_scope,  # type: ignore[arg-type]
        idempotency_policy=idempotency_policy,  # type: ignore[arg-type]
        rate_limit=rate_limit,
        audit_events=writes,
        response_contract="ApiResponse.v1",
        request_contract="BoundaryRequest.v1" if method != "GET" else None,
        success_statuses=success_statuses,
        error_statuses=(400, 401, 403, 409, 422, 429, 500, 503),
    )


_KNOWN_ROUTE_CONTRACTS: tuple[RouteContract, ...] = (
    _contract(
        "api.auth.register",
        "POST",
        "/api/v1/auth/register",
        "api",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="optional",
        success_statuses=(201,),
    ),
    _contract(
        "api.auth.login",
        "POST",
        "/api/v1/auth/login",
        "api",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="optional",
    ),
    _contract(
        "api.auth.logout",
        "POST",
        "/api/v1/auth/logout",
        "api",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="optional",
        success_statuses=(204,),
    ),
    _contract(
        "api.health.liveness",
        "GET",
        "/api/v1/health/liveness",
        "api",
        side_effect=RouteSideEffect.NONE,
    ),
    _contract(
        "api.health.readiness",
        "GET",
        "/api/v1/health/readiness",
        "api",
        "ops:read",
        side_effect=RouteSideEffect.NONE,
    ),
    _contract(
        "api.metrics",
        "GET",
        "/api/v1/metrics",
        "api",
        "ops:metrics:read",
        side_effect=RouteSideEffect.NONE,
    ),
    _contract("api.settings.read", "GET", "/api/v1/settings", "api", "settings:read"),
    _contract(
        "api.settings.update",
        "PUT",
        "/api/v1/settings",
        "api",
        "settings:write",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
    ),
    _contract("api.data.symbols", "GET", "/api/v1/data/symbols", "data", "data:read"),
    _contract(
        "api.strategies.catalogue",
        "GET",
        "/api/v1/strategies",
        "strategy",
        "strategy:read",
    ),
    _contract(
        "api.strategies.versions",
        "GET",
        "/api/v1/strategies/{strategy_id}/versions",
        "strategy",
        "strategy:read",
    ),
    _contract(
        "api.research.run", "POST", "/api/v1/research/run", "research", "research:run"
    ),
    *(
        _contract(
            f"api.dashboard.{name.replace('-', '_').replace('/', '_')}",
            "GET",
            f"/api/v1/dashboard/{name}",
            owner,
            "dashboard:read",
        )
        for name, owner in (
            ("broker", "brokers"),
            ("equity-curve", "analytics"),
            ("summary", "analytics"),
            ("system/resources", "utils"),
            ("market-hours", "data"),
            ("forex-calendar", "data"),
        )
    ),
    _contract(
        "api.operator.audit_events",
        "GET",
        "/api/v1/operator/audit-events",
        "data",
        "ops:audit:read",
    ),
    _contract(
        "api.operator.events",
        "GET",
        "/api/v1/operator/events",
        "trading",
        "ops:events:read",
    ),
    _contract(
        "api.operator.approvals",
        "POST",
        "/api/v1/operator/approvals",
        "api",
        "ops:approve",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        success_statuses=(201,),
    ),
)


ROUTE_CONTRACT_REGISTRY = RouteContractRegistry(_KNOWN_ROUTE_CONTRACTS)


def create_canonical_route_contract_registry() -> RouteContractRegistry:
    """Create an unmodified registry for canonical application composition.

    Returns:
        Fresh registry containing exactly the approved HTTP surface.
    """
    return RouteContractRegistry(_KNOWN_ROUTE_CONTRACTS)


def register_route_contract(contract: RouteContract) -> None:
    """Register one contract into the package-level registry."""
    ROUTE_CONTRACT_REGISTRY.register_route_contract(contract)


__all__ = (
    "ROUTE_CONTRACT_REGISTRY",
    "RouteContractMap",
    "RouteContractRegistry",
    "create_canonical_route_contract_registry",
    "register_route_contract",
)
