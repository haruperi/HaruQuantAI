"""Executable Risk allocation review and budget-activation usage example.

Demonstrates independent review of a self-contained Portfolio projection and
compare-and-swap activation of the authoritative Risk budget projection.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.market_context_contracts import MarketContextEvidence
from app.services.risk.allocation import (
    activate_allocation_budget,
    review_allocation_proposal,
)
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    KillSwitchState,
    PortfolioRiskSnapshot,
    RiskAuditRecord,
)
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


class _ExampleAuditStore:
    """Minimal append-only audit store for this example."""

    def __init__(self) -> None:
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        del timeout_seconds
        return tuple(self.records)


class _ExampleAllocationStore:
    """Minimal version-exact allocation review and budget store."""

    def __init__(self) -> None:
        self.review: AllocationRiskDecision | None = None
        self.active: AllocationRiskDecision | None = None

    def save_review_if_absent(
        self,
        decision: AllocationRiskDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        del timeout_seconds
        if self.review is not None:
            return False
        self.review = decision
        return True

    def get_active(
        self, portfolio_id: str, *, timeout_seconds: Decimal | None
    ) -> AllocationRiskDecision | None:
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
        del timeout_seconds
        current = None if self.active is None else self.active.reviewed_version
        if current != expected_predecessor_version:
            return False
        self.active = decision
        return True


def _config() -> RiskConfig:
    """Build a complete simulation-profile Risk configuration."""
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
    """Build fresh complete Data-owned market-context evidence."""
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
    """Build a healthy immutable portfolio risk snapshot."""
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
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash=compute_config_hash(config),
        evidence_refs={"account": "account-evidence-1"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def _review_request(config: RiskConfig) -> AllocationReviewRequest:
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


def _inactive_kill_switch() -> KillSwitchState:
    """Build one inactive applicable canonical kill-switch state."""
    return KillSwitchState(
        state_id="global-state-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )


def example_allocation() -> None:
    """Demonstrate allocation review followed by budget activation."""
    print("=" * 80)
    print("Risk Example 9: Allocation Review and Budget Activation")
    print("=" * 80)

    config = _config()
    store = _ExampleAllocationStore()
    audit = RiskAuditChain(config, _ExampleAuditStore(), lambda: NOW, canonical_json)

    decision = review_allocation_proposal(
        _review_request(config),
        _snapshot(config),
        _market(),
        config,
        store,
        audit,
        now=NOW,
    )
    print(f"Allocation verdict: {decision.state}")
    print(
        f"Decision ID: {decision.decision_id}, "
        f"reviewed version: {decision.reviewed_version}"
    )

    activation = AllocationBudgetActivationRequest(
        portfolio_id="portfolio-1",
        allocation_version="allocation-v1",
        decision_id=decision.decision_id,
        scope={"portfolio_id": "portfolio-1"},
        effective_at=NOW,
        predecessor_version=None,
        request_id="activation-request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    active = activate_allocation_budget(
        activation,
        decision,
        (_inactive_kill_switch(),),
        config,
        store,
        audit,
        now=NOW,
    )
    print(f"Activated version: {active.reviewed_version}")
    print(f"Durably active: {store.active is not None}")


def main() -> None:
    """Run the Risk allocation review and activation usage example."""
    example_allocation()


if __name__ == "__main__":
    main()
