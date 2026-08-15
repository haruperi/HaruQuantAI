"""Explicit construction of the Simulation run dependency bundle."""

# ruff: noqa: DOC201 - protocol adapter methods return their injected port values.

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from app.services.simulator.state.store import SimulationStateStore

type _Port = Callable[..., object]


@dataclass(frozen=True, slots=True)
class _SimulationDependencies:
    """Concrete adapter over explicitly supplied owner-domain public ports."""

    state_store: SimulationStateStore
    artifact_root: Path
    fast_research_enabled: bool
    audit_port: _Port
    market_data_port: _Port
    tick_series_port: _Port
    indicators_port: _Port
    strategy_port: _Port
    risk_port: _Port
    order_intents_port: _Port
    execution_profile_port: _Port
    symbol_specification_port: _Port
    cost_model_port: _Port
    fx_evidence_port: _Port
    approved_requests_port: _Port | None = None
    trading_action_port: _Port | None = None
    terminal_action_port: _Port | None = None
    initial_authority_state_port: _Port | None = None
    account_activity_port: _Port | None = None

    def persist_audit_event(self, event: object) -> object:
        """Persist one bounded audit event through the supplied Data port."""
        return self.audit_port(event)

    def load_market_data(self, request: object) -> object:
        """Load referenced market evidence through Data."""
        return self.market_data_port(request)

    def generate_tick_series(self, dataset: object, request: object) -> object:
        """Generate official tick evidence through Data."""
        return self.tick_series_port(dataset, request)

    def calculate_indicators(self, dataset: object, request: object) -> object:
        """Calculate indicator evidence through Indicators."""
        return self.indicators_port(dataset, request)

    def evaluate_strategy(
        self,
        dataset: object,
        indicators: tuple[object, ...],
        request: object,
    ) -> object:
        """Evaluate the registered Strategy against supplied evidence."""
        return self.strategy_port(dataset, indicators, request)

    def review_risk(self, intents: tuple[object, ...], request: object) -> object:
        """Review proposed intents through Risk."""
        return self.risk_port(intents, request)

    def build_order_intents(
        self, decisions: tuple[object, ...], request: object
    ) -> object:
        """Build Simulation order intents through Trading."""
        return self.order_intents_port(decisions, request)

    def resolve_execution_profile(self, request: object) -> object:
        """Resolve the referenced execution profile."""
        return self.execution_profile_port(request)

    def resolve_symbol_specification(self, request: object) -> object:
        """Resolve the referenced symbol specification."""
        return self.symbol_specification_port(request)

    def resolve_cost_model(self, request: object) -> object:
        """Resolve the referenced cost model."""
        return self.cost_model_port(request)

    def resolve_fx_evidence(self, evidence_ids: tuple[str, ...]) -> object:
        """Resolve exact Data-owned FX evidence identifiers."""
        return self.fx_evidence_port(evidence_ids)

    def build_approved_requests(
        self,
        intents: tuple[object, ...],
        decisions: tuple[object, ...],
        request: object,
    ) -> object:
        """Build request v2 values through the injected Trading root operation.

        Raises:
            ValueError: If canonical v2 composition is absent.
        """
        if self.approved_requests_port is None:
            raise ValueError("approved_requests port is required for canonical v2 runs")
        return self.approved_requests_port(intents, decisions, request)

    async def execute_trading_action(
        self, approved_request: object, engine: object, request: object
    ) -> object:
        """Await one public Trading action against the run-scoped authority.

        Raises:
            TypeError: If the port result is not awaitable.
            ValueError: If canonical v2 composition is absent.
        """
        if self.trading_action_port is None:
            raise ValueError("trading_action port is required for canonical v2 runs")
        result = self.trading_action_port(approved_request, engine, request)
        if not hasattr(result, "__await__"):
            raise TypeError("trading_action port must return an awaitable")
        return await result

    async def execute_terminal_action(
        self, position: Mapping[str, object], engine: object, request: object
    ) -> object:
        """Await one Risk-authorized public Trading terminal-close action.

        Raises:
            TypeError: If the port result is not awaitable.
            ValueError: If terminal composition is absent.
        """
        if self.terminal_action_port is None:
            raise ValueError(
                "terminal_action port is required for terminal liquidation"
            )
        result = self.terminal_action_port(position, engine, request)
        if not hasattr(result, "__await__"):
            raise TypeError("terminal_action port must return an awaitable")
        return await result

    def load_initial_authority_state(self, request: object) -> object:
        """Load the one complete snapshot shared by Trading and Simulation.

        Raises:
            ValueError: If canonical v2 composition is absent.
        """
        if self.initial_authority_state_port is None:
            raise ValueError("initial_authority_state port is required for v2 runs")
        return self.initial_authority_state_port(request)

    def load_account_activity(self, request: object) -> object:
        """Load every ordered foreign/manual activity event for the run interval.

        Raises:
            ValueError: If canonical v2 composition is absent.
        """
        if self.account_activity_port is None:
            raise ValueError("account_activity port is required for v2 runs")
        return self.account_activity_port(request)


def build_simulation_run_dependencies(
    *,
    state_store: object,
    artifact_root: Path,
    fast_research_enabled: bool,
    ports: Mapping[str, _Port],
) -> object:
    """Build one complete Simulation dependency bundle.

    Args:
        state_store: Concrete implementation of the Simulation persistence port.
        artifact_root: Bounded artifact directory owned by Simulation.
        fast_research_enabled: Whether non-canonical fast research is enabled.
        ports: Exact owner-operation mapping required by a canonical run.

    Returns:
        Opaque dependency bundle accepted by ``run_backtest``.

    Raises:
        TypeError: If the supplied state store does not implement its protocol.
        ValueError: If port names are missing, unknown, or non-callable.
    """
    required = (
        "audit",
        "market_data",
        "tick_series",
        "indicators",
        "strategy",
        "risk",
        "order_intents",
        "execution_profile",
        "symbol_specification",
        "cost_model",
        "fx_evidence",
    )
    optional = (
        "approved_requests",
        "trading_action",
        "terminal_action",
        "initial_authority_state",
        "account_activity",
    )
    if not isinstance(state_store, SimulationStateStore):
        raise TypeError("state_store must implement SimulationStateStore")
    if not set(required).issubset(ports) or not set(ports).issubset(
        {*required, *optional}
    ):
        raise ValueError("ports must match the canonical Simulation dependency set")
    if any(not callable(ports[name]) for name in ports):
        raise ValueError("Simulation dependency ports must be callable")
    return _SimulationDependencies(
        state_store=state_store,
        artifact_root=artifact_root,
        fast_research_enabled=fast_research_enabled,
        audit_port=ports["audit"],
        market_data_port=ports["market_data"],
        tick_series_port=ports["tick_series"],
        indicators_port=ports["indicators"],
        strategy_port=ports["strategy"],
        risk_port=ports["risk"],
        order_intents_port=ports["order_intents"],
        execution_profile_port=ports["execution_profile"],
        symbol_specification_port=ports["symbol_specification"],
        cost_model_port=ports["cost_model"],
        fx_evidence_port=ports["fx_evidence"],
        approved_requests_port=ports.get("approved_requests"),
        trading_action_port=ports.get("trading_action"),
        terminal_action_port=ports.get("terminal_action"),
        initial_authority_state_port=ports.get("initial_authority_state"),
        account_activity_port=ports.get("account_activity"),
    )


__all__ = ("build_simulation_run_dependencies",)
