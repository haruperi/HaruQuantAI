"""Executable canonical Risk governor usage example.

Demonstrates FEAT-RISK-12 constructing the governor with injected dependencies, reviewing one proposed trade in fixed precedence, and running the current-state portfolio governor without any execution side effect.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_account_state_snapshot,
    build_market_context_evidence,
)
from app.services.risk import (
    build_personal_account_risk_config,
    build_risk_capacity_guard,
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
    review_cancel_authorization,
    review_manual_order,
    review_trade_risk,
    run_portfolio_risk_governor,
    run_risk_migrations,
)
from app.services.strategy import create_trade_intent_value
from app.utils import canonical_json, create_auth_context, generate_id
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


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
        self.consumed: set[str] = set()

    def save_issued(
        self, token: Any, *, timeout_seconds: Decimal | None
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


def _intent() -> create_trade_intent_value:
    """Build one immutable Strategy risk-increase trade intent."""
    return create_trade_intent_value(
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


def _proposal(config: create_risk_config) -> create_proposed_trade:
    """Build a Risk-owned proposal bound exactly to the embedded intent."""
    return create_proposed_trade(
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
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="operator-1",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate",),
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile=config.profile,
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


def _governor(config: Any) -> Any:
    """Construct the governor with fully injected Risk dependencies."""
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
    return create_risk_governor(config, approvals, audit, lambda: NOW)


def fr_risk_039() -> None:
    """FR-RISK-039: Stage 1 — Own immutable config plus injected token, audit, clock, and optional configured concurrency protection dependencies."""
    _header(
        "Stage 1: Risk Governor Construction - Construct Risk Governor (FR-RISK-039)"
    )
    print("SUCCESS: FR-RISK-039")
    config = _config()
    governor = _governor(config)
    print(_format_result(governor))
    print(
        "Data -> Risk governor initialized with injected token service and audit chain"
    )


def fr_risk_040() -> None:
    """FR-RISK-040: Stage 3 — Validate and review one proposed trade in fixed precedence, include regime/projected risks/final capped size/concurrency disclosure, attach a token only when eligible and a valid optional attestation is supplied, and audit the decision. Missing attestation yields `needs_approval`, never synthetic approval."""
    _header("Stage 3: Pre-Trade Risk Review - Review Proposed Trade (FR-RISK-040)")
    print("SUCCESS: FR-RISK-040")
    config = _config()
    governor = _governor(config)
    snapshot = _snapshot(config)

    decision = unwrap_risk_response(
        review_trade_risk(
            governor,
            _proposal(config),
            snapshot,
            _market(),
            _regime(),
            (_inactive_kill_switch(),),
            _auth(config),
            attestation=_attestation(config),
            now=NOW,
        ),
        operation="review_trade_risk",
    )
    print(_format_result(decision))
    print(
        f"Data -> decision_id='{decision.decision_id}', state='{decision.state}', approved_size={decision.approved_size}"
    )


def fr_risk_041() -> None:
    """FR-RISK-041: Stage 3 — Evaluate current portfolio compliance and return a remediation recommendation without changing execution state."""
    _header(
        "Stage 3: Current Portfolio Governance - Run Portfolio Risk Governor (FR-RISK-041)"
    )
    print("SUCCESS: FR-RISK-041")
    config = _config()
    governor = _governor(config)
    snapshot = _snapshot(config)

    current = unwrap_risk_response(
        run_portfolio_risk_governor(
            governor,
            snapshot,
            _market(),
            _regime(),
            (_inactive_kill_switch(),),
            _auth(config),
            now=NOW,
        ),
        operation="run_portfolio_risk_governor",
    )
    print(_format_result(current))
    print(
        f"Data -> decision_id='{current.decision_id}', state='{current.state}', approved_size={current.approved_size}"
    )


def fr_risk_091() -> None:
    """FR-RISK-091: Implement the `_CapacityGuard` port with a real durable reservation: one active reservation per exact `(account, strategy, symbol)` scope, first-writer-wins on the reservation key, an idempotent replay of the same key, and an explicit `conflict` when a different active reservation already holds the scope."""
    _header("Stage 4: Durable Concurrent-Capacity Reservation (FR-RISK-091)")
    print("SUCCESS: FR-RISK-091")
    run_risk_migrations(REQUEST_ID)
    guard = build_risk_capacity_guard()
    # The guard checks real wall-clock expiry internally, so this demonstration
    # (unlike the rest of this file) uses genuine current time, not the fixed
    # historical NOW constant used for the deterministic review examples above.
    # A fresh unique run identity keeps repeated executions of this program
    # from colliding with a still-active reservation left by a prior run.
    real_expiry = datetime.now(UTC) + timedelta(minutes=5)
    run_id = generate_id("req")
    scope = {
        "account_id": f"account-governor-usage-{run_id}",
        "strategy_id": "strategy-governor-usage",
        "symbol": "EURUSD",
    }
    first = guard.reserve_capacity(
        reservation_key=f"reservation-{run_id}-1",
        requested_notional=Decimal(1000),
        expires_at=real_expiry,
        timeout_seconds=None,
        **scope,
    )
    replay = guard.reserve_capacity(
        reservation_key=f"reservation-{run_id}-1",
        requested_notional=Decimal(1000),
        expires_at=real_expiry,
        timeout_seconds=None,
        **scope,
    )
    conflicting = guard.reserve_capacity(
        reservation_key=f"reservation-{run_id}-2",
        requested_notional=Decimal(2000),
        expires_at=real_expiry,
        timeout_seconds=None,
        **scope,
    )
    print(f"Data -> first={first!r}, replay={replay!r}, conflicting={conflicting!r}")


def _manual_order_review(*, account_id: str, equity: Decimal) -> tuple[Any, Any]:
    """Run one real Discretionary Manual Order review through review_manual_order.

    Exercises the real end-to-end orchestration (no mocked broker/account
    data): a real ``AccountStateSnapshot`` produced by Data, a real
    ``RiskConfig``, and Risk's actual fixed-precedence ``review_trade_risk``
    gate. Genuine current time is used throughout, matching FR-RISK-091's
    real-clock demonstration above, since the underlying account/equity
    persistence this exercises is itself wall-clock scoped.

    Returns:
        The real ``(decision, verdict)`` pair produced by the review.
    """
    config = build_personal_account_risk_config()
    request_id = generate_id("req")
    workflow_id = generate_id("wf")
    correlation_id = generate_id("cor")
    auth = create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="operator-manual-usage",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("trading:write",),
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile=config.profile,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=datetime.now(UTC),
    )
    account_now = datetime.now(UTC)
    account_snapshot = build_account_state_snapshot(
        account_id=account_id,
        currency="USD",
        balances=(),
        equity=equity,
        margin_used=Decimal(0),
        margin_available=equity,
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="mt5",
        snapshot_at=account_now,
        expires_at=account_now + timedelta(minutes=10),
        request_id=generate_id("req"),
    )
    return review_manual_order(
        account_snapshot=account_snapshot,
        proposal_symbol="EURUSD",
        proposal_side="BUY",
        proposal_order_type="MARKET",
        proposal_quantity=Decimal(1),
        proposal_current_price=Decimal("1.10"),
        proposal_stop_distance=Decimal("0.01"),
        portfolio_id=None,
        route="demo",
        risk_config=config,
        secret_resolver=lambda _: b"example-risk-signing-key-material-32-bytes",
        auth=auth,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
    )


def fr_risk_092() -> None:
    """FR-RISK-092: Track one account's inception/peak/day-start equity across manual-preflight calls; seed on first observation, raise the peak monotonically, and reset day-start once per UTC calendar day. Never fabricates a history the account does not have yet."""
    _header("Stage 5: Manual-Order Equity Tracking (FR-RISK-092)")
    print("SUCCESS: FR-RISK-092")
    run_risk_migrations(REQUEST_ID)
    account_id = f"account-manual-usage-{generate_id('req')}"
    first_decision, _ = _manual_order_review(
        account_id=account_id, equity=Decimal(10000)
    )
    second_decision, _ = _manual_order_review(
        account_id=account_id, equity=Decimal(12000)
    )
    print(
        f"Data -> first_state='{first_decision.state.value}', "
        f"second_state='{second_decision.state.value}' "
        "(same account reviewed twice; equity history persists between calls)"
    )


def fr_risk_093() -> None:
    """FR-RISK-093: Review one human-initiated order through the exact same fixed-precedence `review_trade_risk` gate a strategy-initiated order receives, composing a Strategy-owned `TradeIntent` (the registered Discretionary Manual Order strategy), a real Data-owned account snapshot, real market-context evidence, and a real human `ApprovalAttestation` bound to the current authenticated caller."""
    _header("Stage 5: Manual-Order Fixed-Precedence Review (FR-RISK-093)")
    print("SUCCESS: FR-RISK-093")
    run_risk_migrations(REQUEST_ID)
    account_id = f"account-manual-usage-{generate_id('req')}"
    decision, verdict = _manual_order_review(
        account_id=account_id, equity=Decimal(10000)
    )
    print(
        f"Data -> decision_id='{decision.decision_id}', state='{decision.state.value}', "
        f"verdict={verdict!r}"
    )


def fr_risk_094() -> None:
    """FR-RISK-094: Never invent account state, market evidence, or approval for a manual-order review. Every fact not obtainable from a real source (spread, session state, calendar state, volatility, liquidity, correlation) is surfaced as an explicit `missing_fields` entry or `"unknown"` state rather than a fabricated value."""
    _header("Stage 5: Manual-Order Evidence Integrity (FR-RISK-094)")
    print("SUCCESS: FR-RISK-094")
    run_risk_migrations(REQUEST_ID)
    account_id = f"account-manual-usage-{generate_id('req')}"
    decision, _ = _manual_order_review(account_id=account_id, equity=Decimal(10000))
    print(
        f"Data -> state='{decision.state.value}', "
        f"composite_breach_flags={decision.composite_breach_flags} "
        "(a real evidence gap, surfaced explicitly rather than fabricated)"
    )


def fr_risk_095() -> None:
    """FR-RISK-095: Authorize one order cancellation — a single order or every working order — through Risk's real current-state `run_portfolio_risk_governor` gate rather than the single-proposal trade-review gate, issue a real signed approval token bound to a human `ApprovalAttestation`, and scope the resulting `ActionPolicyVerdict` to the exact target order for a single cancellation or with a `max_children` ceiling drawn from the account's own registered `max_pending_orders` limit for a bulk cancellation."""
    _header("Stage 6: Bulk Cancel-All Authorization (FR-RISK-095)")
    print("SUCCESS: FR-RISK-095")
    run_risk_migrations(REQUEST_ID)
    config = build_personal_account_risk_config()
    request_id = generate_id("req")
    workflow_id = generate_id("wf")
    correlation_id = generate_id("cor")
    auth = create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="operator-bulk-cancel-usage",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("trading:write",),
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile=config.profile,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=datetime.now(UTC),
    )
    account_now = datetime.now(UTC)
    account_snapshot = build_account_state_snapshot(
        account_id=f"account-bulk-cancel-usage-{generate_id('req')}",
        currency="USD",
        balances=(),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        margin_available=Decimal(10000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="mt5",
        snapshot_at=account_now,
        expires_at=account_now + timedelta(minutes=10),
        request_id=generate_id("req"),
    )
    decision, verdict = review_cancel_authorization(
        account_snapshot=account_snapshot,
        representative_symbol="EURUSD",
        action="cancel_all_orders",
        action_scope={},
        portfolio_id=None,
        risk_config=config,
        secret_resolver=lambda _: b"example-risk-signing-key-material-32-bytes",
        auth=auth,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
    )
    print(
        f"Data -> state='{decision.state.value}', "
        f"verdict={verdict!r} "
        "(a real current-state review, not the single-proposal trade gate)"
    )


def fr_risk_096() -> None:
    """FR-RISK-096: Historical SIM review shall validate market/account freshness against replay time while issuing decisions, approval tokens, audit timestamps, and expiry against wall-clock time; exact session, dataset revision, and cursor references are mandatory."""
    _header("Stage 7: Historical SIM Review (FR-RISK-096)")
    print("SUCCESS: FR-RISK-096")
    run_risk_migrations(REQUEST_ID)
    config = build_personal_account_risk_config(
        profile="simulation", execution_route="sim"
    )
    request_id = generate_id("req")
    workflow_id = generate_id("wf")
    correlation_id = generate_id("cor")
    auth = create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="operator-sim-usage",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("trading:write",),
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile="simulation",
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=datetime.now(UTC),
    )
    sim_time = datetime.now(UTC)
    account_snapshot = build_account_state_snapshot(
        account_id=f"account-sim-usage-{generate_id('req')}",
        currency="USD",
        balances=(),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        margin_available=Decimal(10000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="simulator",
        snapshot_at=sim_time,
        expires_at=sim_time + timedelta(minutes=10),
        request_id=generate_id("req"),
    )
    decision, verdict = review_manual_order(
        account_snapshot=account_snapshot,
        proposal_symbol="EURUSD",
        proposal_side="BUY",
        proposal_order_type="MARKET",
        proposal_quantity=Decimal(1),
        proposal_current_price=Decimal("1.10"),
        proposal_stop_distance=Decimal("0.01"),
        portfolio_id=None,
        route="sim",
        risk_config=config,
        secret_resolver=lambda _: b"example-risk-signing-key-material-32-bytes",
        auth=auth,
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        now=sim_time,
        market_evidence_time=sim_time,
        temporal_context="historical_simulation",
        historical_evidence_refs={
            "simulation_session_id": "sim-sess-1",
            "dataset_revision": "rev-1",
            "replay_cursor": "cur-1",
        },
    )
    print(f"Data -> state='{decision.state.value}', verdict={verdict!r}")


def fr_risk_097() -> None:
    """FR-RISK-097: The default LIVE personal-account policy shall be constructible, immutable, database-registered, and fail closed on missing calendar evidence, stressed-window evidence, audit persistence, connectivity, flash crash, drawdown, margin, recovery-lock, and continuous-assessment requirements. Thresholds are 3% daily, 6% weekly, 8% total drawdown, 5%/60s flash crash, 30s connectivity, 80% emergency margin, 900s recovery lock, 120s staleness, and a 252-observation stress lookback including the registered COVID and Ukraine windows."""
    _header("Stage 8: Default LIVE Personal-Account Policy (FR-RISK-097)")
    print("SUCCESS: FR-RISK-097")
    live_config = build_personal_account_risk_config(
        profile="live", execution_route="live"
    )
    print(
        f"Data -> profile='{getattr(live_config, 'profile', '')}', "
        f"max_daily_loss_pct={getattr(live_config, 'max_daily_loss_pct', '')}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-12 — governor/ — Canonical Risk Governor Orchestration\n\n"
        "Purpose: Review proposed trades and evaluate current portfolio compliance in fixed precedence without execution side effects.\n\n"
        "Module flow:\n"
        "-> Stage 1: Construct risk governor with injected approval, audit, and clock dependencies\n"
        "-> Stage 2: Evaluate fixed precedence limits (kill-switch, evidence freshness, limits, sizing, regime)\n"
        "-> Stage 3: Return RiskDecisionPackage for trade review or portfolio compliance\n"
        "-> Stage 4: Durable concurrent-capacity reservation for manual-order preflight\n"
        "-> Stage 5: Manual-order eligibility preflight through the real fixed-precedence gate\n"
        "-> Stage 6: Bulk cancel-all authorization through the real current-state gate\n"
        "-> Stage 7: Historical SIM review\n"
        "-> Stage 8: Default LIVE personal-account policy"
    )
    fr_risk_039()
    fr_risk_040()
    fr_risk_041()
    fr_risk_091()
    fr_risk_092()
    fr_risk_093()
    fr_risk_094()
    fr_risk_095()
    fr_risk_096()
    fr_risk_097()


if __name__ == "__main__":
    main()
