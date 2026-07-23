"""Immutable dependency container for Trading action orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerSymbolInfo,
)
from app.services.data.contracts import MarketDataset
from app.services.data.evidence.account_contracts import (
    AccountStateSnapshot,
)
from app.services.indicators import IndicatorResult
from app.services.risk.contracts import (
    ActionPolicyVerdict,
    AllocationRiskDecision,
    KillSwitchCommand,
    KillSwitchState,
    PortfolioBudgetExecutionVerdict,
    RiskDecisionPackage,
    StrategyOperationalEligibilityDecision,
)
from app.services.strategy import TradeIntent
from app.services.trading.contracts import (
    ExecutionReceipt,
    OrderIntent,
    PortfolioRebalanceExecutionRequest,
    TradingError,
    TradingRequest,
    TradingRoute,
)
from app.services.trading.contracts.models import JsonValue
from app.services.trading.reconciliation import AuthoritySnapshot
from app.utils import logger

if TYPE_CHECKING:
    from app.services.trading.live import LiveSession
    from app.services.trading.monitoring import OperationalEvent
    from app.services.trading.state import TradingStateStore

type SymbolCapability = tuple[Mapping[str, JsonValue], BrokerSymbolInfo]
type SimulationDispatch = Callable[[OrderIntent], Awaitable[ExecutionReceipt]]
type AccountStateSource = Callable[[TradingRequest], AccountStateSnapshot]
type SymbolCapabilitySource = Callable[
    [TradingRoute, str | None, str], SymbolCapability
]
type ActionPolicySource = Callable[[TradingRequest], ActionPolicyVerdict | None]
type KillSwitchStateSource = Callable[[TradingRequest], Sequence[KillSwitchState]]
type RebalanceAllocationSource = Callable[
    [PortfolioRebalanceExecutionRequest], AllocationRiskDecision | None
]
type RebalanceBudgetSource = Callable[
    [PortfolioRebalanceExecutionRequest], PortfolioBudgetExecutionVerdict | None
]
type RebalanceEligibilitySource = Callable[
    [PortfolioRebalanceExecutionRequest],
    Sequence[StrategyOperationalEligibilityDecision],
]
type RebalanceActionResolver = Callable[
    [PortfolioRebalanceExecutionRequest, Mapping[str, JsonValue]],
    TradingRequest,
]
type KillSwitchTransition = Callable[
    [KillSwitchCommand, ActionPolicyVerdict], Awaitable[KillSwitchState]
]
type ReconciliationSource = Callable[[TradingRequest], AuthoritySnapshot]
type MarketDataSource = Callable[[Mapping[str, JsonValue]], Awaitable[MarketDataset]]
type EvaluationAccountSource = Callable[
    [Mapping[str, JsonValue]], Awaitable[AccountStateSnapshot]
]
type IndicatorSource = Callable[
    [MarketDataset, Mapping[str, JsonValue]], Awaitable[IndicatorResult]
]
type StrategySource = Callable[
    [MarketDataset, AccountStateSnapshot, IndicatorResult, Mapping[str, JsonValue]],
    Awaitable[TradeIntent | None],
]
type RiskSource = Callable[
    [TradeIntent, AccountStateSnapshot, Mapping[str, JsonValue]],
    Awaitable[RiskDecisionPackage],
]
type ChildRiskDecisionSource = Callable[[TradingRequest], RiskDecisionPackage | None]


@dataclass(frozen=True, slots=True, kw_only=True)
class TradingDependencies:
    """Carry every explicit authority and read port used by Trading actions.

    Attributes:
        store: Trading-owned state persistence port.
        connection: Composition-created Broker connection for paper/live.
        broker_adapter: Injected asynchronous Broker adapter for paper/live.
        simulation_dispatch: Injected Simulation mutation port for sim.
        live_session: Stateful live/paper gate owner.
        clock: Aware UTC clock.
        idempotency_retention_seconds: Required positive reservation lifetime.
        concurrency_lock_timeout_seconds: Required positive active-lock bound.
        broker_operation_timeout_seconds: Validated positive dispatch timeout.
        max_staleness_seconds: Required per-evidence freshness bounds.
        event_sink: Operational evidence publication port.
        account_state_source: Current normalized Data account-state reader.
        symbol_capability_source: Normalized supported order types and symbol info.
        action_policy_source: Current Risk action-policy reader.
        kill_switch_state_source: Applicable Risk switch hierarchy reader.
        allocation_decision_source: Current Risk allocation reader.
        budget_verdict_source: Current plan-bound Risk budget reader.
        eligibility_source: Current Risk strategy-eligibility reader.
        rebalance_action_resolver: Trading-owned exposure-to-order resolver.
        kill_switch_transition: Risk-owned switch transition port.
        reconciliation_source: Read-only route-authority snapshot port.
        market_data_source: Data market-dataset evaluation port.
        evaluation_account_source: Data account-snapshot evaluation port.
        indicator_source: Indicators evaluation port.
        strategy_source: Strategy TradeIntent evaluation port.
        risk_source: Risk decision evaluation port.
        child_risk_decision_source: Exact per-child emergency Risk authority.
    """

    store: TradingStateStore
    connection: BrokerConnectionConfig | None
    broker_adapter: BrokerAdapter | None
    simulation_dispatch: SimulationDispatch | None
    live_session: LiveSession | None
    clock: Callable[[], datetime]
    idempotency_retention_seconds: int
    concurrency_lock_timeout_seconds: Decimal
    broker_operation_timeout_seconds: Decimal
    max_staleness_seconds: Mapping[str, Decimal]
    event_sink: Callable[[OperationalEvent], None]
    account_state_source: AccountStateSource
    symbol_capability_source: SymbolCapabilitySource
    action_policy_source: ActionPolicySource
    kill_switch_state_source: KillSwitchStateSource
    allocation_decision_source: RebalanceAllocationSource
    budget_verdict_source: RebalanceBudgetSource
    eligibility_source: RebalanceEligibilitySource
    rebalance_action_resolver: RebalanceActionResolver
    kill_switch_transition: KillSwitchTransition
    reconciliation_source: ReconciliationSource
    market_data_source: MarketDataSource
    evaluation_account_source: EvaluationAccountSource
    indicator_source: IndicatorSource
    strategy_source: StrategySource
    risk_source: RiskSource
    child_risk_decision_source: ChildRiskDecisionSource

    def __post_init__(self) -> None:
        """Reject explicit absence without resolving any dependency.

        Raises:
            TradingError: If a declared required read or authority port is absent.
        """
        logger.debug("Constructing immutable TradingDependencies")
        required: tuple[object, ...] = (
            self.store,
            self.clock,
            self.event_sink,
            self.account_state_source,
            self.symbol_capability_source,
            self.action_policy_source,
            self.kill_switch_state_source,
            self.allocation_decision_source,
            self.budget_verdict_source,
            self.eligibility_source,
            self.rebalance_action_resolver,
            self.kill_switch_transition,
            self.reconciliation_source,
            self.market_data_source,
            self.evaluation_account_source,
            self.indicator_source,
            self.strategy_source,
            self.risk_source,
            self.child_risk_decision_source,
        )
        if any(dependency is None for dependency in required):
            raise TradingError(
                "SERVICE_UNAVAILABLE", "A required Trading dependency is absent"
            )
        decimal_bounds = (
            self.concurrency_lock_timeout_seconds,
            self.broker_operation_timeout_seconds,
        )
        if (
            isinstance(self.idempotency_retention_seconds, bool)
            or not isinstance(self.idempotency_retention_seconds, int)
            or self.idempotency_retention_seconds <= 0
            or any(
                not isinstance(value, Decimal) or not value.is_finite() or value <= 0
                for value in decimal_bounds
            )
        ):
            raise TradingError(
                "CONFIGURATION_INVALID", "Trading runtime bounds are invalid"
            )
        if set(self.max_staleness_seconds) != {
            "route_snapshot",
            "risk_decision",
            "kill_switch",
        } or any(
            not isinstance(value, Decimal) or not value.is_finite() or value <= 0
            for value in self.max_staleness_seconds.values()
        ):
            raise TradingError(
                "CONFIGURATION_INVALID", "Trading staleness bounds are invalid"
            )


__all__ = ["TradingDependencies"]
