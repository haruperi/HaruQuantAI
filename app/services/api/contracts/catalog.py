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
    auth_required: bool | None = None,
    response_contract: str = "ApiResponse.v1",
) -> RouteContract:
    """Build one complete internal route declaration.

    Returns:
        Validated route contract.
    """
    authenticated = permission is not None if auth_required is None else auth_required
    writes = side_effect in {RouteSideEffect.WRITE, RouteSideEffect.GOVERNED_WRITE}
    if path.startswith("/api/v1/auth/"):
        rate_limit = "authentication"
    elif side_effect == RouteSideEffect.STREAM:
        rate_limit = "stream"
    elif side_effect == RouteSideEffect.GOVERNED_WRITE:
        rate_limit = "governed_write"
    elif owner in {"optimization", "simulator", "research"} and method != "GET":
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
        response_contract=response_contract,
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
        "api.auth.me",
        "GET",
        "/api/v1/auth/me",
        "api",
        auth_required=True,
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
        "api.data.stream",
        "GET",
        "/api/v1/data/stream",
        "data",
        "data:read",
        side_effect=RouteSideEffect.STREAM,
        response_contract="StreamEvent.v1",
    ),
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
    _contract(
        "api.simulation.run",
        "POST",
        "/api/v1/simulation/run",
        "simulator",
        "simulation:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="SimulationResult.v1",
    ),
    _contract(
        "api.simulation.portfolio_run",
        "POST",
        "/api/v1/simulation/portfolio-run",
        "simulator",
        "simulation:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="PortfolioSimulationResult.v1",
    ),
    _contract(
        "api.simulation.result",
        "GET",
        "/api/v1/simulation/results/{run_id}",
        "simulator",
        "simulation:read",
        response_contract="SimulationResult.v1",
    ),
    _contract(
        "api.simulation.session_create",
        "POST",
        "/api/v1/simulation/sessions",
        "simulator",
        "simulation:read",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="SimulationPlaybackSession.v1",
    ),
    _contract(
        "api.simulation.session_frames",
        "GET",
        "/api/v1/simulation/sessions/{session_id}/frames",
        "simulator",
        "simulation:read",
        side_effect=RouteSideEffect.STREAM,
        response_contract="StreamEvent.v1",
    ),
    _contract(
        "api.risk.kill_switch",
        "GET",
        "/api/v1/risk/kill-switch",
        "risk",
        "risk:read",
        response_contract="KillSwitchState.v1",
    ),
    _contract(
        "api.risk.decisions",
        "GET",
        "/api/v1/risk/decisions",
        "risk",
        "risk:read",
        response_contract="RiskDecisionPackage.v1",
    ),
    _contract(
        "api.trading.session",
        "GET",
        "/api/v1/trading/session",
        "trading",
        "trading:read",
        response_contract="TradingProjection.v1",
    ),
    _contract(
        "api.trading.submit_order",
        "POST",
        "/api/v1/trading/orders",
        "trading",
        "trading:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="ExecutionReceipt.v1",
    ),
    _contract(
        "api.trading.cancel_order",
        "DELETE",
        "/api/v1/trading/orders/{order_id}",
        "trading",
        "trading:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="ExecutionReceipt.v1",
    ),
    _contract(
        "api.trading.close_position",
        "POST",
        "/api/v1/trading/positions/{position_id}/close",
        "trading",
        "trading:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="ExecutionReceipt.v1",
    ),
    _contract(
        "api.portfolio.definition_register",
        "POST",
        "/api/v1/portfolio/{portfolio_id}/definitions",
        "portfolio",
        "portfolio:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="PortfolioDefinition.v1",
    ),
    _contract(
        "api.portfolio.definition",
        "GET",
        "/api/v1/portfolio/{portfolio_id}/definitions/{portfolio_version}",
        "portfolio",
        "portfolio:read",
        response_contract="PortfolioDefinition.v1",
    ),
    _contract(
        "api.portfolio.construct",
        "POST",
        "/api/v1/portfolio/construct",
        "portfolio",
        "portfolio:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="PortfolioConstructionResult.v1",
    ),
    _contract(
        "api.portfolio.status",
        "GET",
        "/api/v1/portfolio/{portfolio_id}/status",
        "portfolio",
        "portfolio:read",
        response_contract="ActivePortfolioAllocation.v1",
    ),
    _contract(
        "api.portfolio.history",
        "GET",
        "/api/v1/portfolio/{portfolio_id}/history",
        "portfolio",
        "portfolio:read",
        response_contract="ActivePortfolioAllocation.v1",
    ),
    _contract(
        "api.simulation.live_session_create",
        "POST",
        "/api/v1/simulation/live-sessions",
        "simulator",
        "simulation:run",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="LiveSimulationSession.v1",
    ),
    _contract(
        "api.simulation.live_session_read",
        "GET",
        "/api/v1/simulation/live-sessions/{session_id}",
        "simulator",
        "simulation:read",
        response_contract="LiveSimulationSession.v1",
    ),
    _contract(
        "api.simulation.live_session_step",
        "POST",
        "/api/v1/simulation/live-sessions/{session_id}/step",
        "simulator",
        "simulation:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="optional",
        response_contract="LiveSimulationSession.v1",
    ),
    _contract(
        "api.simulation.live_session_branch",
        "POST",
        "/api/v1/simulation/live-sessions/{session_id}/branch",
        "simulator",
        "simulation:run",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="LiveSimulationSession.v1",
    ),
    _contract(
        "api.simulation.live_session_close",
        "DELETE",
        "/api/v1/simulation/live-sessions/{session_id}",
        "simulator",
        "simulation:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="optional",
        response_contract="LiveSimulationSession.v1",
    ),
    _contract(
        "api.strategies.register",
        "POST",
        "/api/v1/strategies",
        "strategy",
        "strategy:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="StrategyMutationResult.v1",
    ),
    _contract(
        "api.strategies.update_parameters",
        "PATCH",
        "/api/v1/strategies/{strategy_id}/parameters",
        "strategy",
        "strategy:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="StrategyMutationResult.v1",
    ),
    _contract(
        "api.data.prepare_dataset",
        "POST",
        "/api/v1/data/datasets/prepare",
        "data",
        "data:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="StorageManifest.v1",
    ),
    _contract(
        "api.data.import_dialects",
        "GET",
        "/api/v1/data/imports/dialects",
        "data",
        "data:read",
    ),
    _contract(
        "api.data.import_dataset",
        "POST",
        "/api/v1/data/imports",
        "data",
        "data:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="StorageManifest.v1",
    ),
    _contract(
        "api.risk.apply_kill_switch",
        "POST",
        "/api/v1/risk/kill-switch",
        "risk",
        "risk:kill_switch",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="KillSwitchState.v1",
    ),
    _contract(
        "api.portfolio.activate",
        "POST",
        "/api/v1/portfolio/{portfolio_id}/activate",
        "portfolio",
        "portfolio:activate",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="ActivePortfolioAllocation.v1",
    ),
    _contract(
        "api.portfolio.rollback",
        "POST",
        "/api/v1/portfolio/{portfolio_id}/rollback",
        "portfolio",
        "portfolio:activate",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="ActivePortfolioAllocation.v1",
    ),
    _contract(
        "api.portfolio.drift",
        "POST",
        "/api/v1/portfolio/{portfolio_id}/drift",
        "portfolio",
        "portfolio:read",
        response_contract="PortfolioDriftObservation.v1",
    ),
    _contract(
        "api.portfolio.rebalance",
        "POST",
        "/api/v1/portfolio/rebalance",
        "portfolio",
        "portfolio:rebalance",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="PortfolioRebalancePlan.v1",
    ),
    _contract(
        "api.portfolio.recompute_measurement",
        "POST",
        "/api/v1/portfolio/measurement/recompute",
        "portfolio",
        "portfolio:write",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
        response_contract="PortfolioMeasurement.v1",
    ),
    _contract(
        "api.optimization.parameter_sweep",
        "POST",
        "/api/v1/optimization/parameter-sweep",
        "optimization",
        "optimization:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="OptimizationResult.v1",
    ),
    _contract(
        "api.optimization.walk_forward",
        "POST",
        "/api/v1/optimization/walk-forward",
        "optimization",
        "optimization:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="OptimizationResult.v1",
    ),
    _contract(
        "api.optimization.walk_forward_matrix",
        "POST",
        "/api/v1/optimization/walk-forward-matrix",
        "optimization",
        "optimization:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="OptimizationResult.v1",
    ),
    _contract(
        "api.optimization.robustness",
        "POST",
        "/api/v1/optimization/robustness",
        "optimization",
        "optimization:run",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
        response_contract="OptimizationRobustnessResult.v1",
    ),
    _contract(
        "api.optimization.result",
        "GET",
        "/api/v1/optimization/results/{search_id}",
        "optimization",
        "optimization:read",
        response_contract="OptimizationResult.v1",
    ),
    _contract(
        "api.optimization.compare",
        "POST",
        "/api/v1/optimization/compare",
        "optimization",
        "optimization:read",
    ),
    _contract(
        "api.optimization.stability",
        "POST",
        "/api/v1/optimization/stability",
        "optimization",
        "optimization:read",
    ),
    _contract(
        "api.optimization.overfit",
        "POST",
        "/api/v1/optimization/overfit",
        "optimization",
        "optimization:read",
    ),
    _contract(
        "api.optimization.rank",
        "POST",
        "/api/v1/optimization/rank",
        "optimization",
        "optimization:read",
    ),
    _contract(
        "api.optimization.robustness_score",
        "POST",
        "/api/v1/optimization/robustness-score",
        "optimization",
        "optimization:read",
    ),
    _contract(
        "api.optimization.handoff",
        "POST",
        "/api/v1/optimization/handoff",
        "optimization",
        "optimization:read",
    ),
    _contract(
        "api.agentic.submit_run",
        "POST",
        "/api/v1/agentic/runs",
        "agentic",
        "agentic:submit",
        side_effect=RouteSideEffect.WRITE,
        idempotency_policy="required",
    ),
    _contract(
        "api.agentic.inspect_run",
        "GET",
        "/api/v1/agentic/runs/{run_id}",
        "agentic",
        "agentic:read_run",
    ),
    _contract(
        "api.agentic.cancel_run",
        "DELETE",
        "/api/v1/agentic/runs/{run_id}",
        "agentic",
        "agentic:cancel_run",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
    ),
    _contract(
        "api.agentic.audit_run",
        "GET",
        "/api/v1/agentic/runs/{run_id}/audit",
        "agentic",
        "agentic:read_audit",
    ),
    _contract(
        "api.agentic.approve_handoff",
        "POST",
        "/api/v1/agentic/handoffs/approve",
        "agentic",
        "agentic:approve_promotion",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
    ),
    _contract(
        "api.agentic.quarantine_agent",
        "POST",
        "/api/v1/agentic/incidents/quarantine",
        "agentic",
        "agentic:operate",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
    ),
    _contract(
        "api.agentic.disable",
        "POST",
        "/api/v1/agentic/disable",
        "agentic",
        "agentic:operate",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
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
    _contract(
        "api.indicators.list",
        "GET",
        "/api/v1/indicators",
        "indicators",
        "indicators:read",
    ),
    _contract(
        "api.indicators.capabilities",
        "GET",
        "/api/v1/indicators/capabilities",
        "indicators",
        "indicators:read",
    ),
    _contract(
        "api.indicators.get_spec",
        "GET",
        "/api/v1/indicators/{indicator_id}",
        "indicators",
        "indicators:read",
    ),
    _contract(
        "api.workstation.read",
        "GET",
        "/api/v1/workstation",
        "api",
        "workstation:read",
    ),
    _contract(
        "api.workstation.command",
        "POST",
        "/api/v1/workstation/commands",
        "api",
        "workstation:command",
        side_effect=RouteSideEffect.GOVERNED_WRITE,
        idempotency_policy="required",
        governance_scope="required",
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
