"""Unit tests for traced owner-contract Portfolio workflow coordination."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from app.services.analytics import (
    PortfolioRebalanceMeasurementRequest,
    build_portfolio_rebalance_measurement,
)
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioRebalancePlan,
)
from app.services.portfolio.exceptions import PortfolioError
from app.services.portfolio.orchestration import (
    PortfolioWorkflowDependencies,
    PortfolioWorkflowService,
)
from app.services.portfolio.rebalancing import RebalancingService
from app.services.portfolio.state import PortfolioRepository, scope_key
from app.services.risk import (
    AllocationReviewRequest,
    AllocationRiskDecision,
    DecisionState,
)
from app.services.trading import (
    PortfolioRebalanceExecutionRequest,
    StandardTradingEnvelope,
)
from app.utils import AuditEvent, logger
from tests.portfolio.unit.test_allocation import (
    _activator,
    _inactive_kill_switch,
)
from tests.portfolio.unit.test_rebalancing import (
    RecordingPlanRepository,
    _assess,
)
from tests.portfolio.unit.test_repository import FakePortfolioStore


class WorkflowRecorder:
    """Record Risk, Trading, Analytics, and audit workflow calls."""

    def __init__(self, now: datetime, allocation: ActivePortfolioAllocation) -> None:
        """Initialize deterministic owner-receiver fakes.

        Args:
            now: Stable workflow time.
            allocation: Current active Portfolio allocation.
        """
        logger.debug("Initializing Portfolio workflow receiver recorder")
        self.now = now
        self.allocation = allocation
        self.risk_calls = 0
        self.trading_calls = 0
        self.analytics_calls = 0
        self.fail_analytics_once = False
        self.fail_trading = False
        self.envelopes: dict[str, StandardTradingEnvelope] = {}
        self.last_risk_request: AllocationReviewRequest | None = None
        self.last_trading_request: PortfolioRebalanceExecutionRequest | None = None
        self.last_analytics_request: PortfolioRebalanceMeasurementRequest | None = None

    def risk_review(self, request) -> AllocationRiskDecision:
        """Return one current Risk approval for the exact reviewed version.

        Args:
            request: Receiver-owned Risk allocation review request.

        Returns:
            Current approving Risk allocation decision.
        """
        logger.info("Recording Portfolio workflow Risk review")
        self.risk_calls += 1
        self.last_risk_request = request
        return AllocationRiskDecision(
            decision_id="risk-rebalance-1",
            portfolio_id=request.portfolio_id,
            reviewed_version=request.portfolio_version,
            state=DecisionState.APPROVE,
            capped_weights={
                row.component_id: row.capital_weight
                for row in self.allocation.component_weights
            },
            risk_budget_projection={
                row.component_id: Decimal("0.5")
                for row in self.allocation.component_weights
            },
            conditions=(),
            policy_version="risk-policy-1",
            evidence_refs={"plan": str(request.plan_id)},
            issued_at=self.now,
            expires_at=self.now + timedelta(minutes=10),
            active=True,
            predecessor_version=None,
            audit_ref="risk-audit-1",
        )

    async def trading_execute(self, request) -> StandardTradingEnvelope:
        """Return one reconciled successful Trading execution envelope.

        Args:
            request: Receiver-owned Trading rebalance request.

        Returns:
            Redacted successful Trading envelope.

        Raises:
            RuntimeError: When the test selects an uncertain receiver outcome.
        """
        logger.info("Recording Portfolio workflow Trading execution")
        self.trading_calls += 1
        self.last_trading_request = request
        if self.fail_trading:
            raise RuntimeError("uncertain Trading receiver outcome")
        envelope = StandardTradingEnvelope(
            status="success",
            message="Reconciled Portfolio reductions completed",
            data={
                "plan_id": request.plan_id,
                "outcomes": tuple(
                    {"action_id": row["action_id"], "status": "success", "data": {}}
                    for row in request.actions
                ),
            },
            errors=(),
            warnings=(),
            audit_metadata={
                "operation": "execute_portfolio_rebalance",
                "request_id": request.request_id,
                "correlation_id": request.correlation_id,
                "redaction_applied": True,
            },
        )
        self.envelopes[f"trading-execution:{request.request_id}"] = envelope
        return envelope

    def trading_source(self, reference: str) -> StandardTradingEnvelope:
        """Return immutable previously recorded Trading facts.

        Args:
            reference: Stable Trading execution reference.

        Returns:
            Previously recorded Trading envelope.
        """
        logger.debug("Reading recorded Portfolio workflow Trading facts")
        return self.envelopes[reference]

    def analytics_measure(self, request):
        """Measure immutable Trading facts, optionally failing once.

        Args:
            request: Receiver-owned Analytics measurement request.

        Returns:
            Deterministic Analytics measurement evidence.

        Raises:
            RuntimeError: When the test selects one measurement outage.
        """
        logger.info("Recording Portfolio workflow Analytics measurement")
        self.analytics_calls += 1
        self.last_analytics_request = request
        if self.fail_analytics_once and self.analytics_calls == 1:
            raise RuntimeError("Analytics unavailable")
        return build_portfolio_rebalance_measurement(request)

    @staticmethod
    def audit_persist(event: AuditEvent) -> str:
        """Persist one deterministic audit identity.

        Args:
            event: Complete redacted Utils audit event.

        Returns:
            Exact event identity.
        """
        logger.debug("Persisting recorded Portfolio workflow audit")
        assert event.payload["redaction_applied"] is True
        return event.event_id


def _unused(*args, **kwargs):
    """Fail if an unrelated workflow receiver is unexpectedly called.

    Args:
        *args: Unexpected positional arguments.
        **kwargs: Unexpected keyword arguments.

    Raises:
        AssertionError: Always, because the port is unused in these tests.
    """
    logger.error("Unexpected Portfolio workflow dependency call")
    del args, kwargs
    raise AssertionError("unexpected Portfolio workflow dependency")


def _service(
    active: ActivePortfolioAllocation,
    now: datetime,
    settings,
) -> tuple[PortfolioWorkflowService, WorkflowRecorder, FakePortfolioStore]:
    """Build a workflow service over deterministic owner receivers.

    Args:
        active: Current active allocation.
        now: Stable workflow time.
        settings: Explicit Portfolio settings.

    Returns:
        Workflow service, receiver recorder, and in-memory state store.
    """
    logger.debug("Building Portfolio workflow test service")
    recorder = WorkflowRecorder(now, active)
    store = FakePortfolioStore()
    store.allocations[(active.portfolio_id, active.allocation_version)] = active
    store.active_scopes[scope_key(active.scope)] = (active, 1)
    dependencies = PortfolioWorkflowDependencies(
        strategy_reference_source=_unused,
        eligibility_decision_source=_unused,
        construction_evidence_source=_unused,
        simulation_runner=_unused,
        risk_reviewer=recorder.risk_review,
        risk_budget_activator=_activator,
        kill_switch_source=lambda _scope: (_inactive_kill_switch(now),),
        trading_executor=recorder.trading_execute,
        trading_execution_source=recorder.trading_source,
        analytics_measurer=recorder.analytics_measure,
        audit_persister=recorder.audit_persist,
        clock=lambda: now,
    )
    return (
        PortfolioWorkflowService(settings, PortfolioRepository(store), dependencies),
        recorder,
        store,
    )


def _plan(
    active: ActivePortfolioAllocation,
    now: datetime,
    settings,
) -> PortfolioRebalancePlan:
    """Build one current reduce-only plan with canonical Utils trace IDs.

    Args:
        active: Current active allocation.
        now: Stable workflow time.
        settings: Explicit Portfolio settings.

    Returns:
        Immutable review-required plan.
    """
    logger.debug("Building Portfolio workflow rebalance plan")
    plan = _assess(
        RebalancingService(settings, RecordingPlanRepository()),  # type: ignore[arg-type]
        active,
        now,
        {"component-a": Decimal("0.6"), "component-b": Decimal("0.5")},
    )
    return PortfolioRebalancePlan.model_validate(
        {
            **plan.model_dump(mode="python"),
            "request_id": "req-11111111-1111-4111-8111-111111111111",
            "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
            "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        }
    )


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        AnyIO backend name.
    """
    logger.debug("Selecting asyncio for Portfolio workflow tests")
    return "asyncio"


@pytest.mark.anyio
async def test_submit_rebalance_uses_owner_requests_once_and_measures(
    active_allocation,
    portfolio_now,
    portfolio_settings,
) -> None:
    """Authorized submission calls each receiver once and returns measured truth."""
    logger.info("Testing owner-contract Portfolio rebalance workflow")
    service, recorder, _ = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    result = await service.submit_rebalance(
        _plan(active_allocation, portfolio_now, portfolio_settings),
        account_evidence_ref="account-1",
        market_evidence_ref="market-1",
        fx_evidence_refs=(),
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        approval_token_ref="approval-token-ref-1",
        trading_request_id="trading-request-1",
        valid_until=portfolio_now + timedelta(minutes=5),
    )
    assert result.status == "measured"
    assert (
        recorder.risk_calls == recorder.trading_calls == recorder.analytics_calls == 1
    )


@pytest.mark.anyio
async def test_measurement_failure_preserves_execution_and_recomputes_without_trading(
    active_allocation,
    portfolio_now,
    portfolio_settings,
) -> None:
    """Analytics outage preserves execution and recomputation never calls Trading."""
    logger.info("Testing Portfolio executed-but-unmeasured recomputation")
    service, recorder, _ = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    recorder.fail_analytics_once = True
    executed = await service.submit_rebalance(
        _plan(active_allocation, portfolio_now, portfolio_settings),
        account_evidence_ref="account-1",
        market_evidence_ref="market-1",
        fx_evidence_refs=(),
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        approval_token_ref="approval-token-ref-1",
        trading_request_id="trading-request-1",
        valid_until=portfolio_now + timedelta(minutes=5),
    )
    assert executed.status == "executed_unmeasured"
    measured = service.recompute_measurement(
        executed.plan_id,
        trading_request_id="trading-request-1",
    )
    assert measured.status == "measured"
    assert recorder.trading_calls == 1
    assert recorder.analytics_calls == 2


@pytest.mark.anyio
async def test_uncertain_trading_outcome_is_never_retried(
    active_allocation,
    portfolio_now,
    portfolio_settings,
) -> None:
    """A potentially accepted Trading mutation fails after exactly one call."""
    logger.info("Testing Portfolio mutation no-retry rule")
    service, recorder, _ = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    recorder.fail_trading = True
    with pytest.raises(PortfolioError, match="PORT_UNCERTAIN_OUTCOME"):
        await service.submit_rebalance(
            _plan(active_allocation, portfolio_now, portfolio_settings),
            account_evidence_ref="account-1",
            market_evidence_ref="market-1",
            fx_evidence_refs=(),
            runtime_profile="simulation",
            execution_route="sim",
            approval_refs=(),
            approval_token_ref="approval-token-ref-1",
            trading_request_id="trading-request-1",
            valid_until=portfolio_now + timedelta(minutes=5),
        )
    assert recorder.trading_calls == 1
    assert recorder.analytics_calls == 0
