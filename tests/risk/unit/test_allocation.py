"""Unit tests for allocation review and Risk-budget activation policy."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import MarketContextEvidence
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    DecisionState,
    KillSwitchState,
    PortfolioRiskSnapshot,
    RiskAuditRecord,
    RiskDomainError,
)
from app.services.risk.policy import (
    activate_allocation_budget,
    review_allocation_proposal,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-" + "c" * 64


class _AllocationStore:
    """Atomic in-memory allocation review and activation store."""

    def __init__(self) -> None:
        """Initialize empty durable state."""
        self.review: AllocationRiskDecision | None = None
        self.active: AllocationRiskDecision | None = None
        self.activation_calls = 0

    def save_review_if_absent(
        self,
        decision: AllocationRiskDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist the first allocation review.

        Args:
            decision: Review to persist.
            timeout_seconds: Configured store timeout.

        Returns:
            Whether the store was empty.
        """
        del timeout_seconds
        if self.review is not None:
            return False
        self.review = decision
        return True

    def get_active(
        self, portfolio_id: str, *, timeout_seconds: Decimal | None
    ) -> AllocationRiskDecision | None:
        """Return the current active decision for the portfolio.

        Args:
            portfolio_id: Portfolio identity.
            timeout_seconds: Configured store timeout.

        Returns:
            Active decision or None.
        """
        del timeout_seconds
        if self.active is not None and self.active.portfolio_id == portfolio_id:
            return self.active
        return None

    def activate_compare_and_swap(
        self,
        decision: AllocationRiskDecision,
        *,
        expected_predecessor_version: str | None,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Activate only when the predecessor matches current state.

        Args:
            decision: Approved activation value.
            expected_predecessor_version: Required predecessor.
            timeout_seconds: Configured store timeout.

        Returns:
            Whether compare-and-swap succeeded.
        """
        del timeout_seconds
        self.activation_calls += 1
        current = None if self.active is None else self.active.reviewed_version
        if current != expected_predecessor_version:
            return False
        self.active = decision
        return True


class _Audit:
    """Capturing audit coordinator for allocation tests."""

    def __init__(self) -> None:
        """Initialize empty captured records."""
        self.records: list[RiskAuditRecord] = []

    def append(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Capture and return one allocation event.

        Args:
            record: Unsealed event.

        Returns:
            Captured event.
        """
        self.records.append(record)
        return record


def _config() -> RiskConfig:
    """Build a complete simulation allocation policy."""
    return RiskConfig(
        profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3,
        var_lookback=3,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _snapshot(config: RiskConfig) -> PortfolioRiskSnapshot:
    """Build exact portfolio evidence for allocation review."""
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        daily_loss=Decimal(0),
        total_loss=Decimal(0),
        gross_exposure=Decimal(1000),
        net_exposure=Decimal(1000),
        drawdown=Decimal(0),
        margin_utilization=Decimal("0.10"),
        effective_leverage=Decimal("0.10"),
        historical_var=Decimal(50),
        historical_cvar=Decimal(70),
        volatility=Decimal("0.01"),
        portfolio_correlation=Decimal("0.10"),
        exposure_by_dimension={"symbol:EURUSD": Decimal(1000)},
        contributions={"EURUSD": Decimal(1)},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash=compute_config_hash(config),
        evidence_refs={"account": "account-evidence-1"},
        request_id="snapshot-request-1",
        workflow_id="workflow-1",
    )


def _market() -> MarketContextEvidence:
    """Build complete fresh market evidence."""
    return MarketContextEvidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "fixture"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _review_request(config: RiskConfig) -> AllocationReviewRequest:
    """Build one cap-breaching self-contained allocation request."""
    return AllocationReviewRequest(
        projection_kind="construction",
        portfolio_id="portfolio-1",
        portfolio_version="allocation-v1",
        result_id="construction-1",
        plan_id=None,
        ordered_components=(
            {
                "component_id": "component-1",
                "dimension": "symbol:EURUSD",
                "weight": "0.20",
            },
        ),
        eligibility_decision_refs=("eligibility-1",),
        account_evidence_ref="account-evidence-1",
        market_evidence_ref=MARKET_REQUEST_ID,
        fx_evidence_refs=(),
        evidence_hashes={"snapshot_config": compute_config_hash(config)},
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        requested_at=NOW,
        request_id="allocation-request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def test_allocation_review_enforces_caps() -> None:
    """Reject an excessive weight while preserving the safely capped projection."""
    config = _config()
    store = _AllocationStore()
    audit = _Audit()
    decision = review_allocation_proposal(
        _review_request(config),
        _snapshot(config),
        _market(),
        config,
        store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    assert decision.state is DecisionState.REJECT
    assert decision.capped_weights["symbol:EURUSD"] == Decimal("0.10")
    assert decision.risk_budget_projection["symbol:EURUSD"] == Decimal(1000)
    assert store.review == decision
    assert len(audit.records) == 1


def test_allocation_rejects_malformed_component_schema() -> None:
    """Reject an allocation component that does not use the exact V1 fields."""
    config = _config()
    malformed = _review_request(config).model_copy(
        update={"ordered_components": ({"component_id": "only-id"},)}
    )
    with pytest.raises(RiskDomainError):
        review_allocation_proposal(
            malformed,
            _snapshot(config),
            _market(),
            config,
            _AllocationStore(),
            _Audit(),  # type: ignore[arg-type]
            now=NOW,
        )


def test_budget_activation_is_version_exact_and_atomic() -> None:
    """Reject a version mismatch before CAS and atomically activate an exact review."""
    config = _config()
    review_store = _AllocationStore()
    audit = _Audit()
    reviewed = review_allocation_proposal(
        _review_request(config),
        _snapshot(config),
        _market(),
        config,
        review_store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    values = reviewed.model_dump(mode="python")
    values.update(state=DecisionState.APPROVE, conditions=())
    approved = AllocationRiskDecision.model_validate(values)
    base = {
        "portfolio_id": "portfolio-1",
        "allocation_version": "allocation-v1",
        "decision_id": approved.decision_id,
        "scope": {"portfolio_id": "portfolio-1"},
        "effective_at": NOW,
        "predecessor_version": None,
        "request_id": "activation-request-1",
        "workflow_id": "workflow-1",
        "correlation_id": "correlation-1",
    }
    inactive = KillSwitchState(
        state_id="kill-global",
        scope_level="global",
        scope={},
        state="inactive",
        reason="clear",
        version=1,
        updated_at=NOW,
    )
    activation_store = _AllocationStore()
    mismatch = AllocationBudgetActivationRequest(
        **{**base, "allocation_version": "wrong-version"}
    )
    with pytest.raises(RiskDomainError):
        activate_allocation_budget(
            mismatch,
            approved,
            (inactive,),
            config,
            activation_store,
            audit,  # type: ignore[arg-type]
            now=NOW,
        )
    assert activation_store.activation_calls == 0

    active_switch = inactive.model_copy(update={"state": "active"})
    with pytest.raises(RiskDomainError):
        activate_allocation_budget(
            AllocationBudgetActivationRequest(**base),
            approved,
            (active_switch,),
            config,
            activation_store,
            audit,  # type: ignore[arg-type]
            now=NOW,
        )
    assert activation_store.activation_calls == 0

    active = activate_allocation_budget(
        AllocationBudgetActivationRequest(**base),
        approved,
        (inactive,),
        config,
        activation_store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    assert active.active is True
    assert activation_store.active == active
    assert activation_store.activation_calls == 1
