"""Route and stream contract registry helpers for API drift checks."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from app.services.api.contracts.models import (
    RouteContract,
    RouteSideEffect,
    RouteStability,
)

RouteContractMap = dict[str, RouteContract]


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
        return self._contracts.get(_route_key(method, path))

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


_KNOWN_ROUTE_CONTRACTS: tuple[RouteContract, ...] = (
    RouteContract(
        route_id="api.liveness",
        method="GET",
        path="/api/health/liveness",
        owner="api",
        stability=RouteStability.STABLE,
        side_effect=RouteSideEffect.NONE,
        auth_required=False,
        governance_scope="none",
        response_contract="ApiResponse.v1",
    ),
    RouteContract(
        route_id="api.readiness",
        method="GET",
        path="/api/health/readiness",
        owner="api",
        stability=RouteStability.STABLE,
        side_effect=RouteSideEffect.NONE,
        auth_required=True,
        governance_scope="none",
        permission="ops:read",
        response_contract="ApiResponse.v1",
    ),
    RouteContract(
        route_id="api.metrics",
        method="GET",
        path="/api/metrics",
        owner="api",
        stability=RouteStability.STABLE,
        side_effect=RouteSideEffect.NONE,
        auth_required=True,
        governance_scope="none",
        permission="ops:metrics:read",
        response_contract="ApiResponse.v1",
    ),
)


ROUTE_CONTRACT_REGISTRY = RouteContractRegistry(_KNOWN_ROUTE_CONTRACTS)


def register_route_contract(contract: RouteContract) -> None:
    """Register one contract into the package-level registry."""
    ROUTE_CONTRACT_REGISTRY.register_route_contract(contract)


__all__ = (
    "ROUTE_CONTRACT_REGISTRY",
    "RouteContractMap",
    "RouteContractRegistry",
    "register_route_contract",
)
