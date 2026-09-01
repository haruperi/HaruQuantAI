"""Executable Risk allocation review and budget-activation usage example.

Demonstrates FEAT-RISK-09 independent review of a self-contained Portfolio projection and compare-and-swap activation of the authoritative Risk budget projection.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.serialization import canonical_json
from app.services.data import build_market_context_evidence
from app.services.risk import (
    activate_allocation_budget,
    compute_config_hash,
    create_allocation_budget_activation_request,
    create_allocation_review_request,
    create_kill_switch_state,
    create_portfolio_risk_snapshot,
    create_risk_audit_chain,
    create_risk_audit_record,
    create_risk_config,
    review_allocation_proposal,
)
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class _ExampleAuditStore:
    """Minimal append-only audit store for this example."""

    def __init__(self) -> None:
        self.records: list[create_risk_audit_record] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: Any,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        del timeout_seconds
        return tuple(self.records)


class _ExampleAllocationStore:
    """Minimal version-exact allocation review and budget store."""

    def __init__(self) -> None:
        self.review: Any | None = None
        self.active: Any | None = None

    def save_review_if_absent(
        self,
        decision: Any,
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
    ) -> Any | None:
        del timeout_seconds
        if self.active is not None and self.active.portfolio_id == portfolio_id:
            return self.active
        return None

    def activate_compare_and_swap(
        self,
        decision: Any,
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


def _config() -> create_risk_config:
    """Build a complete simulation-profile Risk configuration."""
    return create_risk_config(
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


def _market() -> build_market_context_evidence:
    """Build fresh complete Data-owned market-context evidence."""
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
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _snapshot(config: create_risk_config) -> create_portfolio_risk_snapshot:
    """Build a healthy immutable portfolio risk snapshot."""
    return create_portfolio_risk_snapshot(
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
        config_hash=unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        ),
        evidence_refs={"account": "account-evidence-1"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def _review_request(config: create_risk_config) -> create_allocation_review_request:
    """Build a self-contained within-cap allocation review request."""
    return create_allocation_review_request(
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


def _inactive_kill_switch() -> create_kill_switch_state:
    """Build one inactive applicable canonical kill-switch state."""
    return create_kill_switch_state(
        state_id="global-state-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )


def fr_risk_030() -> None:
    """FR-RISK-030: Stage 3 — Produce and atomically persist `AllocationRiskDecision v1`, enforce caps for the exact reviewed Portfolio version, and append its Risk audit record without constructing or applying a Portfolio allocation."""
    _header("Stage 3: Allocation Review - Review Allocation Proposal (FR-RISK-030)")
    print("SUCCESS: FR-RISK-030")
    config = _config()
    store = _ExampleAllocationStore()
    audit = create_risk_audit_chain(
        config, _ExampleAuditStore(), lambda: NOW, canonical_json
    )

    decision = unwrap_risk_response(
        review_allocation_proposal(
            _review_request(config),
            _snapshot(config),
            _market(),
            config,
            store,
            audit,
            now=NOW,
        ),
        operation="review_allocation_proposal",
    )
    print(_format_result(decision))
    print(f"Data -> decision_id='{decision.decision_id}', state='{decision.state}'")


def fr_risk_051() -> None:
    """FR-RISK-051: Stage 3 — Atomically compare-and-swap the authoritative risk-budget projection only for the exact approved allocation version and predecessor; version, expiry, active/unknown kill-switch, or concurrency conflict blocks activation, and success is audit-chained."""
    _header("Stage 3: Budget Activation - Activate Allocation Budget (FR-RISK-051)")
    print("SUCCESS: FR-RISK-051")
    config = _config()
    store = _ExampleAllocationStore()
    audit = create_risk_audit_chain(
        config, _ExampleAuditStore(), lambda: NOW, canonical_json
    )

    decision = unwrap_risk_response(
        review_allocation_proposal(
            _review_request(config),
            _snapshot(config),
            _market(),
            config,
            store,
            audit,
            now=NOW,
        ),
        operation="review_allocation_proposal",
    )

    activation = create_allocation_budget_activation_request(
        portfolio_id="portfolio-1",
        allocation_version="allocation-v1",
        decision_id=decision.decision_id,
        scope={"portfolio_id": "portfolio-1"},
        effective_at=NOW,
        predecessor_version=None,
        request_id="req-44444444-4444-4444-8444-444444444444",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    active = unwrap_risk_response(
        activate_allocation_budget(
            activation,
            decision,
            (_inactive_kill_switch(),),
            config,
            store,
            audit,
            now=NOW,
        ),
        operation="activate_allocation_budget",
    )
    print(_format_result(active))
    print(
        f"Data -> decision_id='{active.decision_id}', reviewed_version='{active.reviewed_version}', active={active.active}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-09 — allocation/ — Allocation Proposal Review and Budget Activation\n\n"
        "Purpose: Review a self-contained Portfolio projection and atomically compare-and-swap the authoritative Risk budget projection.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted allocation review request and portfolio snapshot\n"
        "-> Stage 2: Validate allocation caps, evidence, and policy\n"
        "-> Stage 3: Return AllocationRiskDecision and activate allocation budget"
    )
    fr_risk_030()
    fr_risk_051()


if __name__ == "__main__":
    main()
