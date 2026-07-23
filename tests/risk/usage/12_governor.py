"""Executable canonical Risk governor usage example.

Demonstrates constructing the governor with injected dependencies, reviewing one
proposed trade in fixed precedence, and running the current-state portfolio
governor without any execution side effect.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.market_context_contracts import MarketContextEvidence
from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    KillSwitchState,
    PortfolioRiskSnapshot,
    ProposedTrade,
    RegimeAssessment,
    RiskApprovalToken,
    RiskAuditRecord,
)
from app.services.risk.governor import RiskGovernor
from app.services.strategy import TradeIntent
from app.utils import AuthContext, canonical_json

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


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


class _ExampleTokenStore:
    """Minimal single-process durable token store for this example."""

    def __init__(self) -> None:
        self.tokens: dict[str, RiskApprovalToken] = {}
        self.consumed: set[str] = set()

    def save_issued(
        self, token: RiskApprovalToken, *, timeout_seconds: Decimal | None
    ) -> Literal["saved", "already_saved", "conflict"]:
        del timeout_seconds
        current = self.tokens.get(token.token_id)
        if current is None:
            self.tokens[token.token_id] = token
            return "saved"
        return "already_saved" if current == token else "conflict"

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
        del timeout_seconds
        token = self.tokens.get(token_id)
        if token is None:
            return "missing"
        if token_id in self.consumed:
            return "already_consumed"
        if now >= token.expires_at:
            return "expired"
        self.consumed.add(token_id)
        return "consumed"

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
    """Build a healthy snapshot carrying exact governor trace identifiers."""
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
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
    )


def _intent() -> TradeIntent:
    """Build one immutable Strategy risk-increase trade intent."""
    return TradeIntent(
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


def _proposal(config: RiskConfig) -> ProposedTrade:
    """Build a Risk-owned proposal bound exactly to the embedded intent."""
    return ProposedTrade(
        intent=_intent(),
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


def _regime() -> RegimeAssessment:
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
    return RegimeAssessment(
        assessment_id="regime-1",
        states=states,
        previous_states=states,
        transitions=(),
        modifiers={},
        evidence_refs=("snapshot-1", MARKET_REQUEST_ID),
        missing_fields=(),
        assessed_at=NOW,
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


def _auth(config: RiskConfig) -> AuthContext:
    """Build an authenticated context with exact governor trace identity."""
    return AuthContext(
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


def _attestation(config: RiskConfig) -> ApprovalAttestation:
    """Build authorized human approval evidence bound to this decision."""
    return ApprovalAttestation(
        attestation_id="attestation-1",
        principal_id="operator-1",
        action="submit_order",
        scope={"account_id": "account-1", "symbol": "EURUSD"},
        policy_ref=compute_config_hash(config),
        policy_version=config.policy_version,
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )


def _governor(config: RiskConfig) -> RiskGovernor:
    """Construct the governor with fully injected Risk dependencies."""
    audit = RiskAuditChain(config, _ExampleAuditStore(), lambda: NOW, canonical_json)
    approvals = ApprovalTokenService(
        config,
        _ExampleTokenStore(),
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    return RiskGovernor(config, approvals, audit, lambda: NOW)


def example_governor() -> None:
    """Demonstrate pre-trade review and current-state portfolio governance."""
    print("=" * 80)
    print("Risk Example 12: Canonical Risk Governor")
    print("=" * 80)

    config = _config()
    governor = _governor(config)
    snapshot = _snapshot(config)

    decision = governor.review_trade_risk(
        _proposal(config),
        snapshot,
        _market(),
        _regime(),
        (_inactive_kill_switch(),),
        _auth(config),
        attestation=_attestation(config),
        now=NOW,
    )
    print(f"Trade review verdict: {decision.state}")
    print(
        f"Approved size: {decision.approved_size}, "
        f"primary failure: {decision.primary_failure_limit}"
    )

    current = governor.run_portfolio_risk_governor(
        snapshot,
        _market(),
        _regime(),
        (_inactive_kill_switch(),),
        _auth(config),
        now=NOW,
    )
    print(f"Portfolio governor verdict: {current.state}")
    print(f"Current-state approved size is absent: {current.approved_size is None}")


def main() -> None:
    """Run the canonical Risk governor usage example."""
    example_governor()


if __name__ == "__main__":
    main()
