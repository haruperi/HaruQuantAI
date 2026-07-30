"""Unit tests for allocation review and Risk-budget activation policy."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data import build_market_context_evidence
from app.services.risk.allocation import (
    activate_allocation_budget,
    review_allocation_proposal,
)
from app.services.risk.allocation.budget import (
    _cap_for,
    _parse_component,
    _parse_components,
    _review_state,
)
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    DecisionState,
    KillSwitchState,
    LimitStatus,
    PortfolioRiskSnapshot,
    RiskAuditRecord,
    RiskDomainError,
)
from app.services.risk.contracts.responses import unwrap_risk_response

from tests.risk._support import _risk_success

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


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

    def append(self, record: RiskAuditRecord):
        """Capture and return one allocation event.

        Args:
            record: Unsealed event.

        Returns:
            Captured event.
        """
        self.records.append(record)
        return _risk_success(record)


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
        config_hash=unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        ),
        evidence_refs={"account": "account-evidence-1"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def _market() -> object:
    """Build complete fresh market evidence."""
    return build_market_context_evidence(
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
        evidence_hashes={
            "snapshot_config": unwrap_risk_response(
                compute_config_hash(config), operation="compute_config_hash"
            )
        },
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        requested_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def test_allocation_review_enforces_caps() -> None:
    """Reject an excessive weight while preserving the safely capped projection."""
    config = _config()
    store = _AllocationStore()
    audit = _Audit()
    decision = unwrap_risk_response(
        review_allocation_proposal(
            _review_request(config),
            _snapshot(config),
            _market(),
            config,
            store,
            audit,  # type: ignore[arg-type]
            now=NOW,
        ),
        operation="review_allocation_proposal",
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
    response = review_allocation_proposal(
        malformed,
        _snapshot(config),
        _market(),
        config,
        _AllocationStore(),
        _Audit(),  # type: ignore[arg-type]
        now=NOW,
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "INVALID_INPUT"


def test_allocation_helpers_cover_exact_policy_branches() -> None:
    """Exercise invalid components, default caps, and ordered review precedence."""
    config = _config()
    with pytest.raises(RiskDomainError, match="ALLOCATION_COMPONENT_WEIGHT_INVALID"):
        _parse_component(
            {
                "component_id": "bad",
                "dimension": "symbol:EURUSD",
                "weight": "not-decimal",
            }
        )
    with pytest.raises(RiskDomainError, match="ALLOCATION_COMPONENT_VALUE_INVALID"):
        _parse_component(
            {
                "component_id": "bad",
                "dimension": "unknown:EURUSD",
                "weight": "0.1",
            }
        )
    component = {
        "component_id": "same",
        "dimension": "symbol:EURUSD",
        "weight": "0.1",
    }
    with pytest.raises(RiskDomainError, match="ALLOCATION_COMPONENTS_MUST_BE_UNIQUE"):
        _parse_components((component, component))
    assert _cap_for("portfolio:main", config) == Decimal(1)
    assert _cap_for("symbol:EURUSD", config) == config.max_symbol_concentration
    assert _cap_for("strategy:alpha", config) == config.max_dimension_concentration
    assert (
        _review_state((), cap_breached=False, total_invalid=True)[0]
        is DecisionState.REJECT
    )
    assert (
        _review_state((), cap_breached=True, total_invalid=False)[0]
        is DecisionState.REJECT
    )
    assert (
        _review_state(
            (LimitStatus.BLOCKED,),
            cap_breached=False,
            total_invalid=False,
        )[0]
        is DecisionState.BLOCK
    )
    assert (
        _review_state(
            (LimitStatus.NEEDS_MORE_EVIDENCE,),
            cap_breached=False,
            total_invalid=False,
        )[0]
        is DecisionState.NEEDS_MORE_EVIDENCE
    )
    assert (
        _review_state(
            (LimitStatus.WARN,),
            cap_breached=False,
            total_invalid=False,
        )[0]
        is DecisionState.WARN
    )


def test_budget_activation_is_version_exact_and_atomic() -> None:
    """Reject a version mismatch before CAS and atomically activate an exact review."""
    config = _config()
    review_store = _AllocationStore()
    audit = _Audit()
    reviewed = unwrap_risk_response(
        review_allocation_proposal(
            _review_request(config),
            _snapshot(config),
            _market(),
            config,
            review_store,
            audit,  # type: ignore[arg-type]
            now=NOW,
        ),
        operation="review_allocation_proposal",
    )
    values = reviewed.model_dump(warnings=False, mode="python")
    values.update(state=DecisionState.APPROVE, conditions=())
    approved = AllocationRiskDecision.model_validate(values)
    base = {
        "portfolio_id": "portfolio-1",
        "allocation_version": "allocation-v1",
        "decision_id": approved.decision_id,
        "scope": {"portfolio_id": "portfolio-1"},
        "effective_at": NOW,
        "predecessor_version": None,
        "request_id": "req-44444444-4444-4444-8444-444444444444",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
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
    response = activate_allocation_budget(
        mismatch,
        approved,
        (inactive,),
        config,
        activation_store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    assert response.status == "error"
    assert activation_store.activation_calls == 0

    active_switch = inactive.model_copy(update={"state": "active"})
    response = activate_allocation_budget(
        AllocationBudgetActivationRequest(**base),
        approved,
        (active_switch,),
        config,
        activation_store,
        audit,  # type: ignore[arg-type]
        now=NOW,
    )
    assert response.status == "error"
    assert activation_store.activation_calls == 0

    active = unwrap_risk_response(
        activate_allocation_budget(
            AllocationBudgetActivationRequest(**base),
            approved,
            (inactive,),
            config,
            activation_store,
            audit,  # type: ignore[arg-type]
            now=NOW,
        ),
        operation="activate_allocation_budget",
    )
    assert active.active is True
    assert activation_store.active == active
    assert activation_store.activation_calls == 1
