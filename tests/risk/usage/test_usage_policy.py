"""Runnable usage examples for the public Risk Policy API."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from app.services.data.contracts import MarketContextEvidence
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    DecisionState,
    KillSwitchState,
    PortfolioRiskSnapshot,
    RiskAuditRecord,
    StrategyOperationalEligibilityDecision,
    StrategyOperationalEligibilityRequest,
)
from app.services.risk.policy import (
    activate_allocation_budget,
    evaluate_market_context,
    evaluate_portfolio_limits,
    review_allocation_proposal,
    review_strategy_admission,
)
from app.services.strategy import (
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyRef,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-" + "c" * 64
HASH_A = "a" * 64
HASH_B = "b" * 64


class _Audit:
    """Example audit receiver that captures material events."""

    def __init__(self) -> None:
        """Initialize empty captured events."""
        self.records: list[RiskAuditRecord] = []

    def append(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Capture one unsealed event.

        Args:
            record: Material event to capture.

        Returns:
            Captured event.
        """
        self.records.append(record)
        return record


class _EligibilityStore:
    """Example receiver-owned eligibility decision store."""

    def __init__(self) -> None:
        """Initialize without a saved decision."""
        self.decision: StrategyOperationalEligibilityDecision | None = None

    def save_if_absent(
        self,
        decision: StrategyOperationalEligibilityDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Save the first example decision.

        Args:
            decision: Decision to save.
            timeout_seconds: Configured receiver timeout.

        Returns:
            Whether the store was empty.
        """
        del timeout_seconds
        if self.decision is not None:
            return False
        self.decision = decision
        return True


class _AllocationStore:
    """Example receiver-owned allocation review and active-budget store."""

    def __init__(self) -> None:
        """Initialize empty review and active state."""
        self.review: AllocationRiskDecision | None = None
        self.active: AllocationRiskDecision | None = None

    def save_review_if_absent(
        self,
        decision: AllocationRiskDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Save the first example allocation review.

        Args:
            decision: Review decision.
            timeout_seconds: Configured receiver timeout.

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
        """Return the active example budget.

        Args:
            portfolio_id: Portfolio identity.
            timeout_seconds: Configured receiver timeout.

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
        """Activate when the expected predecessor matches.

        Args:
            decision: Exact approved allocation decision.
            expected_predecessor_version: Required active version.
            timeout_seconds: Configured receiver timeout.

        Returns:
            Whether activation succeeded.
        """
        del timeout_seconds
        current = None if self.active is None else self.active.reviewed_version
        if current != expected_predecessor_version:
            return False
        self.active = decision
        return True


def _config() -> RiskConfig:
    """Build a complete simulation Policy configuration."""
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
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _snapshot(config: RiskConfig) -> PortfolioRiskSnapshot:
    """Build a healthy immutable example portfolio snapshot."""
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        daily_loss=Decimal(100),
        total_loss=Decimal(200),
        gross_exposure=Decimal(1000),
        net_exposure=Decimal(1000),
        drawdown=Decimal("0.02"),
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


def _registration() -> ValidatedStrategyRef:
    """Build an approved simulation Strategy reference."""
    validation = StrategyValidationPolicy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    manifest = StrategyManifest(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        owner_ref="team-alpha",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
        permitted_environments=(StrategyEnvironment.SIMULATION,),
        source_hash=HASH_A,
        artifact_hash=HASH_A,
        dependency_hash=HASH_A,
        provenance_refs=("build-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5,
    )
    return ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.SIMULATION,
        policy_version=validation.policy_version,
        validation_policy=validation,
        registry_record_hash=HASH_B,
        request_id="strategy-request-1",
        correlation_id="correlation-1",
    )


def _allocation_request(config: RiskConfig) -> AllocationReviewRequest:
    """Build a self-contained within-cap allocation review request."""
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
                "weight": "0.05",
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


def test_usage_limits_portfolio() -> None:
    """Evaluate ordered configured portfolio limits."""
    config = _config()
    results = evaluate_portfolio_limits(_snapshot(config), config, now=NOW)
    assert results[0].limit_id == "freshness"


def test_usage_limits_market_context() -> None:
    """Evaluate only supplied normalized market context."""
    results = evaluate_market_context(_market(), _config(), now=NOW)
    assert [item.limit_id for item in results] == [
        "freshness",
        "session",
        "calendar",
        "spread",
        "liquidity_availability",
    ]


def test_usage_admission_review() -> None:
    """Review and persist Strategy operational eligibility."""
    audit = _Audit()
    decision = review_strategy_admission(
        StrategyOperationalEligibilityRequest(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            runtime_profile="simulation",
            execution_route="sim",
            policy_version="policy-1",
            registration_ref=HASH_B,
            evidence_refs={"market": MARKET_REQUEST_ID},
            approval_refs=(),
            requested_scope={"symbol": "EURUSD"},
            requested_at=NOW,
            request_id="admission-request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        ),
        _registration(),
        _market(),
        _config(),
        _EligibilityStore(),
        cast("RiskAuditChain", audit),
        now=NOW,
    )
    assert decision.state is DecisionState.APPROVE


def test_usage_allocation_review() -> None:
    """Review and persist a self-contained allocation projection."""
    config = _config()
    decision = review_allocation_proposal(
        _allocation_request(config),
        _snapshot(config),
        _market(),
        config,
        _AllocationStore(),
        cast("RiskAuditChain", _Audit()),
        now=NOW,
    )
    assert decision.state is DecisionState.APPROVE


def test_usage_budget_activation() -> None:
    """Activate the exact approved Risk-budget projection by CAS."""
    config = _config()
    audit = _Audit()
    store = _AllocationStore()
    decision = review_allocation_proposal(
        _allocation_request(config),
        _snapshot(config),
        _market(),
        config,
        store,
        cast("RiskAuditChain", audit),
        now=NOW,
    )
    active = activate_allocation_budget(
        AllocationBudgetActivationRequest(
            portfolio_id="portfolio-1",
            allocation_version="allocation-v1",
            decision_id=decision.decision_id,
            scope={"portfolio_id": "portfolio-1"},
            effective_at=NOW,
            predecessor_version=None,
            request_id="activation-request-1",
            workflow_id="workflow-1",
            correlation_id="correlation-1",
        ),
        decision,
        (
            KillSwitchState(
                state_id="kill-global",
                scope_level="global",
                scope={},
                state="inactive",
                reason="clear",
                version=1,
                updated_at=NOW,
            ),
        ),
        config,
        store,
        cast("RiskAuditChain", audit),
        now=NOW,
    )
    assert active.active is True
