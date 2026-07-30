"""Executable Risk decision-reuse revalidation usage example.

Demonstrates confirming that a prior canonical decision is still reusable, and
that a material change to the reviewed proposal deterministically invalidates it.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import build_market_context_evidence
from app.services.risk import (
    compute_config_hash,
    create_approval_attestation,
    create_approval_token_service,
    create_kill_switch_state,
    create_portfolio_risk_snapshot,
    create_proposed_trade,
    create_regime_assessment,
    create_risk_audit_chain,
    create_risk_config,
    create_risk_governor,
    revalidate_risk_decision,
    review_trade_risk,
)
from app.services.strategy import create_trade_intent_value
from app.utils import canonical_json, create_auth_context

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


class _ExampleAuditStore:
    """Minimal append-only audit store for this example."""

    def __init__(self) -> None:
        self.records: list[Any] = []

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


class _ExampleTokenStore:
    """Minimal single-process durable token store for this example."""

    def __init__(self) -> None:
        self.tokens: dict[str, Any] = {}

    def save_issued(
        self, token: Any, *, timeout_seconds: Decimal | None
    ) -> Literal["saved", "already_saved", "conflict"]:
        del timeout_seconds
        self.tokens[token.token_id] = token
        return "saved"

    def consume_if_active(
        self,
        token_id: str,
        *,
        expected_signature: str,
        reservation_id: str,
        workflow_id: str,
        action: str,
        scope: dict[str, str],
        now: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal[
        "consumed", "missing", "expired", "revoked", "already_consumed", "conflict"
    ]:
        del expected_signature, reservation_id, workflow_id, action, scope
        del now, timeout_seconds
        return "consumed" if token_id in self.tokens else "missing"

    def revoke_intersecting(
        self,
        scope: dict[str, str],
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        del scope, reason, revoked_at, timeout_seconds
        return 0


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
    """Build a healthy snapshot carrying exact governor trace identifiers."""
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
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
    )


def _proposal(config: create_risk_config) -> create_proposed_trade:
    """Build a Risk-owned proposal bound exactly to the embedded intent."""
    intent = create_trade_intent_value(
        intent_id="intent-1",
        decision_id="strategy-decision-1",
        idempotency_key="intent-key-1",
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        strategy_sequence=1,
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        limit_price=None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode="fixed_risk",
        quantity_hint=Decimal(1),
        notional_hint=None,
        signal_timestamp=NOW,
        decision_timestamp=NOW,
        parent_intent_id=None,
        stop_loss=Decimal("1.09"),
        take_profit=None,
        expiration=NOW + timedelta(minutes=1),
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref=None,
        lineage={"strategy_config": "a" * 64},
    )
    return create_proposed_trade(
        intent=intent,
        account_id="account-1",
        portfolio_id="portfolio-1",
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile=config.profile,
        evidence_refs={"market": MARKET_REQUEST_ID},
        provenance={"source": "strategy"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )


def _regime() -> create_regime_assessment:
    """Build one fully known normal regime assessment."""
    states = dict.fromkeys(
        (
            "volatility",
            "liquidity",
            "correlation",
            "drawdown",
            "crisis",
            "news",
            "session",
        ),
        "normal",
    )
    return create_regime_assessment(
        assessment_id="regime-1",
        states=states,
        previous_states=states,
        transitions=(),
        modifiers={},
        evidence_refs=("snapshot-1", MARKET_REQUEST_ID),
        missing_fields=(),
        assessed_at=NOW,
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


def _auth(config: create_risk_config) -> create_auth_context:
    """Build an authenticated context with exact governor trace identity."""
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="operator-1",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate",),
        scopes=("risk",),
        tenant_or_environment=config.profile,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )


def _attestation(config: create_risk_config) -> create_approval_attestation:
    """Build authorized human approval evidence bound to this decision."""
    return create_approval_attestation(
        attestation_id="attestation-1",
        principal_id="operator-1",
        action="submit_order",
        scope={"account_id": "account-1", "symbol": "EURUSD"},
        policy_ref=unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        ),
        policy_version=config.policy_version,
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )


def fr_risk_042() -> None:
    """FR-RISK-042: Compare proposal/evidence/config/time with a prior decision
    and invalidate material changes, expiry, skew, stale state, config mismatch,
    or reconciliation expiry without granting action authority."""
    _header(
        "FR-RISK-042: Compare proposal/evidence/config/time with a prior decision and invalidate material changes, expiry, skew, stale state, config mismatch, or reconciliation expiry without granting action authority."
    )
    print("Risk Example 11: Decision Reuse Revalidation")

    config = _config()
    audit = create_risk_audit_chain(
        config, _ExampleAuditStore(), lambda: NOW, canonical_json
    )
    approvals = create_approval_token_service(
        config,
        _ExampleTokenStore(),
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    governor = create_risk_governor(config, approvals, audit, lambda: NOW)

    proposal = _proposal(config)
    snapshot = _snapshot(config)
    decision = unwrap_risk_response(
        review_trade_risk(
            governor,
            proposal,
            snapshot,
            _market(),
            _regime(),
            (_inactive_kill_switch(),),
            _auth(config),
            attestation=_attestation(config),
            now=NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )

    reuse = unwrap_risk_response(
        revalidate_risk_decision(decision, proposal, snapshot, config, now=NOW),
        operation="revalidate_risk_decision",
    )
    print(
        f"Unchanged proposal reusable: {reuse.reusable}, "
        f"refresh required: {reuse.refresh_required}"
    )

    changed = proposal.model_copy(update={"requested_size": Decimal(2)})
    response = revalidate_risk_decision(decision, changed, snapshot, config, now=NOW)
    if response.status == "error" and response.error is not None:
        print(f"Material size change blocked reuse with code: {response.error.code}")


def main() -> None:
    """Run the FR-RISK-042 decision-reuse demonstration."""
    fr_risk_042()


if __name__ == "__main__":
    main()
