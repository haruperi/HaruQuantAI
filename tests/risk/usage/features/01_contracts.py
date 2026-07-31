"""Executable Risk contracts usage example.

Demonstrates FEAT-RISK-01 versioned contracts, evidence validation, canonical enums, and domain errors.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_account_state_snapshot,
    build_market_context_evidence,
)
from app.services.risk import (
    create_action_policy_verdict,
    create_allocation_budget_activation_request,
    create_allocation_review_request,
    create_allocation_risk_decision,
    create_approval_attestation,
    create_approval_validation_result,
    create_kill_switch_command,
    create_kill_switch_state,
    create_portfolio_budget_execution_verdict,
    create_portfolio_risk_snapshot,
    create_portfolio_state,
    create_position_sizing_request,
    create_position_sizing_result,
    create_proposed_trade,
    create_regime_assessment,
    create_risk_approval_token,
    create_risk_audit_record,
    create_risk_decision_package,
    create_risk_domain_error,
    create_risk_limit_result,
    create_risk_report,
    create_scenario_definition,
    create_scenario_result,
    create_strategy_operational_eligibility_decision,
    create_strategy_operational_eligibility_request,
    get_decision_state,
    get_limit_status,
    get_risk_error_code,
    validate_market_context_evidence,
)
from app.services.strategy import create_trade_intent_value
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = "req-12345678-1234-4234-8234-123456789abc"
WORKFLOW_ID = "wf-12345678-1234-4234-8234-123456789abc"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
HASH_64 = "a" * 64


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


def _make_intent():
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
        lineage={"strategy_config": HASH_64},
    )


# --- Stage 1: Untrusted Mapping & Inputs ---


def fr_risk_004() -> None:
    """FR-RISK-004: Stage 1 — Carry exact immutable Data-owned `build_account_state_snapshot v1` and `build_fx_conversion_evidence v1` values plus peak/day-start/inception equity, symbol mark prices, contract sizes, quote currencies, exposure dimensions, aligned timestamped per-symbol return histories, explicit pair correlations, UTC `as_of`, provenance, missingness, and schema version. Open `build_account_order.quantity` is the full remaining pending quantity for Risk exposure."""
    _header("Stage 1: Portfolio State Inputs - Construct Portfolio State (FR-RISK-004)")
    account = build_account_state_snapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            {"asset": "USD", "total": Decimal(10000), "available": Decimal(9500)},
        ),
        equity=Decimal(10000),
        margin_used=Decimal(500),
        margin_available=Decimal(9500),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
    )
    portfolio = create_portfolio_state(
        account_snapshot=account,
        peak_equity=Decimal(10000),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
    )
    print(_format_result(portfolio))
    print(
        f"Data -> account_id='{portfolio.account_snapshot.account_id}', equity={portfolio.account_snapshot.equity}"
    )


def fr_risk_006() -> None:
    """FR-RISK-006: Stage 1 — Define the Risk-owned receiver contract for one non-executable review. It embeds the complete immutable Strategy `create_trade_intent_value v1` unchanged and adds current valuation, stop-distance, account/portfolio scope, evidence timestamps, provenance references/hashes, and requested Risk profile. Risk rejects an incompatible intent version, conflicting duplicated fact, invalid scope/size, or absent required stop evidence."""
    _header("Stage 1: Trade Proposal Input - Proposed Trade Contract (FR-RISK-006)")
    intent = _make_intent()
    proposed = create_proposed_trade(
        intent=intent,
        account_id="account-1",
        portfolio_id="portfolio-1",
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile="research",
        evidence_refs={"market": MARKET_REQUEST_ID},
        provenance={"source": "strategy"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(proposed))
    print(
        f"Data -> intent_id='{proposed.intent.intent_id}', symbol='{proposed.intent.symbol}'"
    )


def fr_risk_007() -> None:
    """FR-RISK-007: Stage 1 — Represent one of six sizing methods and its complete evidence/config references."""
    _header("Stage 1: Sizing Request Input - Sizing Request Contract (FR-RISK-007)")
    req = create_position_sizing_request(
        method="fixed_risk",
        requested_size=None,
        fixed_lot=None,
        risk_amount=Decimal(1000),
        risk_fraction=None,
        stop_distance=Decimal(100),
        unit_value=Decimal(10),
        milestone_multiplier=None,
        win_rate=None,
        payoff_ratio=None,
        trade_count=None,
        volatility_multiplier=None,
        asset_volatility=None,
        broker_min_size=Decimal("0.01"),
        broker_max_size=Decimal(100),
        broker_size_step=Decimal("0.01"),
        evidence_refs={"snapshot": "snap-1"},
        request_id=REQUEST_ID,
    )
    print(_format_result(req))
    print(f"Data -> method='{req.method}'")


def fr_risk_009() -> None:
    """FR-RISK-009: Stage 1 — Define `create_allocation_review_request v1` carrying a self-contained Risk-owned projection (projection kind, portfolio/result/plan IDs and versions, ordered weights or actions, eligibility decisions, account/market/FX evidence references and hashes, runtime scope, approval references); it never embeds or imports a Portfolio-owned contract."""
    _header(
        "Stage 1: Allocation Request Input - Allocation Review Request (FR-RISK-009)"
    )
    req = create_allocation_review_request(
        projection_kind="construction",
        portfolio_id="portfolio-1",
        portfolio_version="allocation-v1",
        result_id="construction-1",
        plan_id=None,
        ordered_components=(
            {"component_id": "c1", "dimension": "symbol:EURUSD", "weight": "0.05"},
        ),
        eligibility_decision_refs=("eligibility-1",),
        account_evidence_ref="account-evidence-1",
        market_evidence_ref=MARKET_REQUEST_ID,
        fx_evidence_refs=(),
        evidence_hashes={"snapshot_config": HASH_64},
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(req))
    print(f"Data -> request_id='{req.request_id}', portfolio_id='{req.portfolio_id}'")


def fr_risk_010() -> None:
    """FR-RISK-010: Stage 1 — Define `create_strategy_operational_eligibility_request v1` for an exact registered strategy/version and scope (strategy/version, runtime profile, route, policy/evidence/approval references, requested scope)."""
    _header(
        "Stage 1: Admission Request Input - Strategy Operational Eligibility Request (FR-RISK-010)"
    )
    req = create_strategy_operational_eligibility_request(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        runtime_profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        registration_ref=HASH_64,
        evidence_refs={"market": MARKET_REQUEST_ID},
        approval_refs=(),
        requested_scope={"symbol": "EURUSD"},
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(req))
    print(
        f"Data -> strategy_id='{req.strategy_id}', strategy_version='{req.strategy_version}'"
    )


def fr_risk_012() -> None:
    """FR-RISK-012: Stage 1 — Define a bounded immutable advisory scenario with deterministic shocks and optional explicit seed."""
    _header("Stage 1: Scenario Input - Advisory Scenario Definition (FR-RISK-012)")
    scen = create_scenario_definition(
        scenario_id="equity-stress",
        shocks={"equity": Decimal("-0.10")},
        randomized=True,
        seed=42,
        assumptions=("declared ten-percent equity shock",),
    )
    print(_format_result(scen))
    print(f"Data -> scenario_id='{scen.scenario_id}', seed={scen.seed}")


def fr_risk_016() -> None:
    """FR-RISK-016: Stage 1 — Implement `create_kill_switch_command v1` with action, explicit scope level, applicable portfolio/strategy/symbol identifiers, reason, UTC timestamp, request/workflow/correlation IDs, and schema identity. Principal authorization remains in the separate `create_auth_context`; clearance requires a separate matching current `create_approval_attestation`."""
    _header("Stage 1: Kill Switch Input - Kill Switch Command (FR-RISK-016)")
    cmd = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="Emergency halt",
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(cmd))
    print(
        f"Data -> action='{cmd.action}', scope_level='{cmd.scope_level}', reason='{cmd.reason}'"
    )


def fr_risk_047() -> None:
    """FR-RISK-047: Stage 1 — Define `create_approval_attestation v1` authenticated human approval evidence (principal, action, scope, policy reference/version, issue/expiry times, trace IDs); it carries no secret and is never execution authority by itself."""
    _header("Stage 1: Attestation Input - Approval Attestation (FR-RISK-047)")
    att = create_approval_attestation(
        attestation_id="attest-1",
        principal_id="user-1",
        action="clear_kill_switch",
        scope={"scope_level": "global"},
        policy_ref=HASH_64,
        policy_version="v1",
        issued_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(att))
    print(
        f"Data -> attestation_id='{att.attestation_id}', principal_id='{att.principal_id}'"
    )


def fr_risk_048() -> None:
    """FR-RISK-048: Stage 1 — Define `create_allocation_budget_activation_request v1` (allocation and decision references, scope, effective time, predecessor, trace IDs) to activate the Risk-owned budget projection for one approved allocation version."""
    _header(
        "Stage 1: Budget Activation Input - Allocation Budget Activation Request (FR-RISK-048)"
    )
    req = create_allocation_budget_activation_request(
        portfolio_id="portfolio-1",
        allocation_version="allocation-v1",
        decision_id="dec-1",
        scope={"portfolio_id": "portfolio-1"},
        effective_at=NOW,
        predecessor_version=None,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(req))
    print(f"Data -> request_id='{req.request_id}', decision_id='{req.decision_id}'")


# --- Stage 2: Strict Contract & Validation ---


def fr_risk_001() -> None:
    """FR-RISK-001: Stage 2 — Define `approve`, `warn`, `needs_approval`, `needs_more_evidence`, `reject`, `block`, and `error` exactly."""
    _header("Stage 2: Enum Validation - DecisionState (FR-RISK-001)")
    state_cls = get_decision_state("approve")
    print(_format_result(state_cls))
    print("Data -> DecisionState value='approve'")


def fr_risk_002() -> None:
    """FR-RISK-002: Stage 2 — Define `pass`, `warn`, `needs_more_evidence`, `fail`, and `blocked` exactly."""
    _header("Stage 2: Enum Validation - LimitStatus (FR-RISK-002)")
    status_cls = get_limit_status("pass")
    print(_format_result(status_cls))
    print("Data -> LimitStatus value='pass'")


def fr_risk_003() -> None:
    """FR-RISK-003: Stage 2 — Define exactly `INVALID_INPUT`, `VALIDATION_FAILED`, `INVALID_PORTFOLIO_STATE`, `INVALID_RISK_CONFIG`, `MISSING_EVIDENCE`, `STALE_EVIDENCE`, `LIMIT_FAILED`, `POLICY_BLOCKED`, `PERMISSION_DENIED`, `KILL_SWITCH_ACTIVE`, `KILL_SWITCH_UNKNOWN`, `APPROVAL_REQUIRED`, `APPROVAL_TOKEN_INVALID`, `APPROVAL_TOKEN_EXPIRED`, `APPROVAL_TOKEN_REVOKED`, `APPROVAL_TOKEN_CONSUMED`, `CONFIG_VERSION_MISMATCH`, `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`, `PAYLOAD_TOO_LARGE`, `MISSING_STOP_LOSS`, `INSUFFICIENT_VOLATILITY_EVIDENCE`, `INSUFFICIENT_K_EVIDENCE`, `LIVE_STATE_STALE`, `IN_FLIGHT_TOLERANCE_EXCEEDED`, `IN_FLIGHT_RECONCILIATION_EXPIRED`, `AUDIT_CHAIN_TAMPER_DETECTED`, `CALCULATION_FAILED`, `SNAPSHOT_BUILD_FAILED`, `GOVERNOR_DECISION_FAILED`, `REPORT_GENERATION_FAILED`, `STORAGE_ERROR`, `TOOL_EXECUTION_FAILED`, and `UNKNOWN_ERROR`; historical VaR/CVaR is the sole supported VaR method."""
    _header("Stage 2: Enum Validation - RiskErrorCode (FR-RISK-003)")
    code_val = get_risk_error_code("INVALID_INPUT")
    print(_format_result(code_val))
    print("Data -> RiskErrorCode value='INVALID_INPUT'")


def fr_risk_021() -> None:
    """FR-RISK-021: Stage 2 — Raise one redacted domain exception carrying a `RiskErrorCode` and safe details for boundary mapping."""
    _header("Stage 2: Coded Exception - RiskDomainError (FR-RISK-021)")
    err = create_risk_domain_error(
        get_risk_error_code("INVALID_INPUT"), details="Test detail"
    )
    print(_format_result(err))
    print(f"Data -> code='{err.code}', details='{err.details}'")


def fr_risk_058() -> None:
    """FR-RISK-058: Stage 2 — Validate the consumed Data-owned `build_market_context_evidence v1` version, UTC freshness, provenance, bounded values, and explicit missingness without redefining or fetching it."""
    _header(
        "Stage 2: Market Context Validation - validate_market_context_evidence (FR-RISK-058)"
    )
    market = build_market_context_evidence(
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
    res = unwrap_risk_response(
        validate_market_context_evidence(market, now=NOW),
        operation="validate_market_context_evidence",
    )
    print(_format_result(res))
    print(
        f"Data -> symbol='{market.symbol}', session_state='{market.session_state}', validated={res}"
    )


# --- Stage 3: Immutable Output Contracts & Results ---


def fr_risk_005() -> None:
    """FR-RISK-005: Stage 3 — Carry reproducible base-currency equity, daily/total loss, exposure, drawdown, margin/leverage, historical tail-risk, volatility/correlation/contribution metrics, limit results, assumptions, coverage, regime, request/workflow IDs, evidence refs, and config hash."""
    _header("Stage 3: Portfolio Snapshot Result - PortfolioRiskSnapshot (FR-RISK-005)")
    snap = create_portfolio_risk_snapshot(
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
        config_hash=HASH_64,
        evidence_refs={"account": "account-evidence-1"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
    )
    print(_format_result(snap))
    print(f"Data -> equity={snap.equity}, gross_exposure={snap.gross_exposure}")


def fr_risk_008() -> None:
    """FR-RISK-008: Stage 3 — Return exact requested/normalized size, constraints applied, evidence gaps, fallback disclosure, and no approval claim."""
    _header("Stage 3: Sizing Output - PositionSizingResult (FR-RISK-008)")
    res = create_position_sizing_result(
        method="fixed_risk",
        requested_size=Decimal("0.1"),
        calculated_size=Decimal("0.1"),
        normalized_size=Decimal("0.1"),
        constraints_applied=("broker_max",),
        evidence_gaps=(),
        fallback_used=False,
        fallback_reason=None,
        correlation_adjustment=None,
        approved=False,
    )
    print(_format_result(res))
    print(f"Data -> normalized_size={res.normalized_size}, approved={res.approved}")


def fr_risk_011() -> None:
    """FR-RISK-011: Stage 3 — Return classified volatility/liquidity/correlation/drawdown/crisis/news/session states, transition evidence, modifiers, and missingness."""
    _header("Stage 3: Regime Assessment Output - RegimeAssessment (FR-RISK-011)")
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
    reg = create_regime_assessment(
        assessment_id="regime-1",
        states=states,
        previous_states=states,
        transitions=(),
        modifiers={"max_size": Decimal("0.5")},
        evidence_refs=("snapshot-1", MARKET_REQUEST_ID),
        missing_fields=(),
        assessed_at=NOW,
    )
    print(_format_result(reg))
    print(
        f"Data -> assessed_at='{reg.assessed_at}', missing_fields={len(reg.missing_fields)}"
    )


def fr_risk_013() -> None:
    """FR-RISK-013: Stage 3 — Return baseline/projected risk comparison and state that the output is advisory and not approved."""
    _header("Stage 3: Scenario Output - ScenarioResult (FR-RISK-013)")
    res = create_scenario_result(
        scenario_id="equity-stress",
        baseline={"equity": Decimal(10000)},
        projected={"equity": Decimal(9000)},
        differences={"equity": Decimal(-1000)},
        assumptions=("declared shock",),
        seed=42,
        policy_version="v1",
        evidence_refs=("snap-1",),
        warnings=(),
        generated_at=NOW,
    )
    print(_format_result(res))
    print(
        f"Data -> scenario_id='{res.scenario_id}', difference={res.differences['equity']}"
    )


def fr_risk_014() -> None:
    """FR-RISK-014: Stage 3 — Implement `RiskDecision` v1 with verdict, trade-only approved size, ordered checks, primary/composite reasons, provenance, expiry, concurrency disclosure, and optional token. A current-state compliance approval has no intent and no invented trade size."""
    _header("Stage 3: Risk Decision Package - RiskDecisionPackage (FR-RISK-014)")
    dec = create_risk_decision_package(
        decision_id="dec-1",
        intent_id=None,
        state=get_decision_state("approve"),
        requested_size=None,
        approved_size=None,
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"market": MARKET_REQUEST_ID},
        config_hash=HASH_64,
        concurrency_disclosure="none",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        token=None,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(dec))
    print(f"Data -> decision_id='{dec.decision_id}', state='{dec.state}'")


def fr_risk_015() -> None:
    """FR-RISK-015: Stage 3 — Carry signed token scope, decision/config hashes, approver, expiry, nonce, schema version, and no secret key."""
    _header("Stage 3: Approval Token Output - RiskApprovalToken (FR-RISK-015)")
    tok = create_risk_approval_token(
        token_id="tok-1",
        decision_id="dec-1",
        config_hash=HASH_64,
        action="trade",
        scope={"scope_level": "global"},
        approver_id="risk_governor",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        nonce="nonce-1",
        signature="sig-1",
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(tok))
    print(f"Data -> token_id='{tok.token_id}', action='{tok.action}'")


def fr_risk_017() -> None:
    """FR-RISK-017: Stage 3 — Implement `create_kill_switch_state` v1 with scope, active/unknown state, reason, version, and UTC update time."""
    _header(
        "Stage 3: Kill Switch State Output - create_kill_switch_state (FR-RISK-017)"
    )
    st = create_kill_switch_state(
        state_id="kill-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="Normal operation",
        version=1,
        updated_at=NOW,
    )
    print(_format_result(st))
    print(f"Data -> state_id='{st.state_id}', state='{st.state}'")


def fr_risk_018() -> None:
    """FR-RISK-018: Stage 3 — Carry canonical redacted audit payload and evidence/config/decision provenance in either an explicitly unsealed append input (`sealed=False`, null sequence/hashes) or a sealed result (`sealed=True`, complete sequence, previous hash, and record hash). Persisted or cross-domain audit results must be sealed."""
    _header("Stage 3: Audit Record Output - RiskAuditRecord (FR-RISK-018)")
    rec = create_risk_audit_record(
        record_id="rec-1",
        event_type="trade_review",
        payload={"verdict": "approve"},
        evidence_refs={"market": MARKET_REQUEST_ID},
        config_hash=HASH_64,
        decision_id="dec-1",
        occurred_at=NOW,
        sequence=1,
        previous_hash="0" * 64,
        record_hash="c" * 64,
        sealed=True,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(rec))
    print(
        f"Data -> record_id='{rec.record_id}', sealed={rec.sealed}, sequence={rec.sequence}"
    )


def fr_risk_019() -> None:
    """FR-RISK-019: Stage 3 — Carry Markdown or exact JSON summary with separated evidence, assumptions, warnings, decision, and recommendations."""
    _header("Stage 3: Risk Report Output - RiskReport (FR-RISK-019)")
    rep = create_risk_report(
        report_id="rep-1",
        format="markdown",
        content="# Risk Report\nVerdict: approve",
        evidence=("snap-1",),
        assumptions=(),
        warnings=(),
        decision=("approve",),
        recommendations=(),
        approval_claimed=False,
        generated_at=NOW,
    )
    print(_format_result(rep))
    print(f"Data -> report_id='{rep.report_id}', format='{rep.format}'")


def fr_risk_020() -> None:
    """FR-RISK-020: Stage 3 — Return token validity, consumption state, reason code, audit reference, and an optional `ActionPolicyVerdict`; the verdict is present and allowed only after successful atomic reservation/consumption and is absent on every failure, without exposing secrets."""
    _header(
        "Stage 3: Approval Validation Result - ApprovalValidationResult (FR-RISK-020)"
    )
    verdict = create_action_policy_verdict(
        verdict_id="verdict-1",
        action="trade",
        scope={"scope_level": "global"},
        policy_version="v1",
        attestation_id="attest-1",
        decision_id="dec-1",
        reservation_id="res-1",
        allowed=True,
        reasons=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    val = create_approval_validation_result(
        valid=True,
        consumed=True,
        reason_code=None,
        audit_ref="rec-1",
        reservation_id="res-1",
        action_policy_verdict=verdict,
    )
    print(_format_result(val))
    print(f"Data -> valid={val.valid}, consumed={val.consumed}")


def fr_risk_049() -> None:
    """FR-RISK-049: Stage 3 — Define `StrategyOperationalEligibilityDecision v1` (decision ID, strategy/version, scope, verdict, conditions, policy version, issue/expiry times, evidence lineage) without altering Strategy registration."""
    _header(
        "Stage 3: Eligibility Decision Output - StrategyOperationalEligibilityDecision (FR-RISK-049)"
    )
    dec = create_strategy_operational_eligibility_decision(
        decision_id="dec-elig-1",
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        scope={"symbol": "EURUSD"},
        state=get_decision_state("approve"),
        conditions=(),
        policy_version="v1",
        evidence_refs={"market": MARKET_REQUEST_ID},
        issued_at=NOW,
        expires_at=NOW + timedelta(days=1),
        suspended=False,
        audit_ref="rec-1",
    )
    print(_format_result(dec))
    print(f"Data -> decision_id='{dec.decision_id}', state='{dec.state}'")


def fr_risk_050() -> None:
    """FR-RISK-050: Stage 3 — Define `AllocationRiskDecision v1` (decision ID, reviewed version, verdict, capped weights, authoritative risk-budget projection, conditions, issue/expiry times, policy/evidence lineage)."""
    _header(
        "Stage 3: Allocation Decision Output - AllocationRiskDecision (FR-RISK-050)"
    )
    dec = create_allocation_risk_decision(
        decision_id="dec-alloc-1",
        portfolio_id="portfolio-1",
        reviewed_version="1.0.0",
        state=get_decision_state("approve"),
        capped_weights={"strategy-1": Decimal("0.5")},
        risk_budget_projection={"max_drawdown": Decimal("0.05")},
        conditions=(),
        policy_version="v1",
        evidence_refs={"market": MARKET_REQUEST_ID},
        issued_at=NOW,
        expires_at=NOW + timedelta(days=1),
        active=True,
        predecessor_version=None,
        audit_ref="rec-1",
    )
    print(_format_result(dec))
    print(f"Data -> decision_id='{dec.decision_id}', state='{dec.state}'")


def fr_risk_059() -> None:
    """FR-RISK-059: Stage 3 — Return `ActionPolicyVerdict v1` bound to action, scope, policy version, approval attestation, decision, reservation, expiry, reasons, and trace IDs."""
    _header("Stage 3: Action Policy Verdict - ActionPolicyVerdict (FR-RISK-059)")
    ver = create_action_policy_verdict(
        verdict_id="verdict-1",
        action="trade",
        scope={"scope_level": "global"},
        policy_version="v1",
        attestation_id="attest-1",
        decision_id="dec-1",
        reservation_id="res-1",
        allowed=True,
        reasons=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(ver))
    print(f"Data -> allowed={ver.allowed}, action='{ver.action}'")


def fr_risk_060() -> None:
    """FR-RISK-060: Stage 3 — Carry one ordered limit result with status, observed/threshold values, reason code, evidence refs, and precedence without granting approval."""
    _header("Stage 3: Risk Limit Result - RiskLimitResult (FR-RISK-060)")
    lim = create_risk_limit_result(
        limit_id="limit-1",
        status=get_limit_status("pass"),
        observed_value=Decimal("0.02"),
        threshold_value=Decimal("0.10"),
        reason_code=None,
        evidence_refs=("snapshot_1",),
        precedence=1,
    )
    print(_format_result(lim))
    print(f"Data -> limit_id='{lim.limit_id}', status='{lim.status}'")


def fr_risk_061() -> None:
    """FR-RISK-061: Stage 3 — Define `PortfolioBudgetExecutionVerdict v1` as the sole execution-time budget result: it binds the current allocation decision, portfolio/allocation version, plan ID/hash, budget unit, allowed state, reasons, and UTC validity. Trading validates this result and never calculates budget consumption."""
    _header(
        "Stage 3: Budget Execution Verdict - PortfolioBudgetExecutionVerdict (FR-RISK-061)"
    )
    ver = create_portfolio_budget_execution_verdict(
        verdict_id="verdict-1",
        allocation_decision_id="dec-alloc-1",
        portfolio_id="port-1",
        allocation_version="1.0.0",
        plan_id="plan-1",
        plan_hash=HASH_64,
        budget_unit="USD",
        allowed=True,
        reasons=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    print(_format_result(ver))
    print(f"Data -> allowed={ver.allowed}, portfolio_id='{ver.portfolio_id}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-01 — contracts/ — Versioned Contracts and Deterministic Errors\n\n"
        "Purpose: Define strict Pydantic V2 contracts, exact Decimal serialization, canonical enums, one coded domain exception, and the public response boundary without business I/O.\n\n"
        "Module flow:\n"
        "-> Stage 1: Untrusted mapping and request inputs\n"
        "-> Stage 2: Strict contract/version/finite-value validation\n"
        "-> Stage 3: Immutable typed value or coded error contracts"
    )

    # 1. Stage 1: Request & Input mapping
    fr_risk_004()
    fr_risk_006()
    fr_risk_007()
    fr_risk_009()
    fr_risk_010()
    fr_risk_012()
    fr_risk_016()
    fr_risk_047()
    fr_risk_048()

    # 2. Stage 2: Enum & Fail-closed validation
    fr_risk_001()
    fr_risk_002()
    fr_risk_003()
    fr_risk_021()
    fr_risk_058()

    # 3. Stage 3: Immutable output contracts & results
    fr_risk_005()
    fr_risk_008()
    fr_risk_011()
    fr_risk_013()
    fr_risk_014()
    fr_risk_015()
    fr_risk_017()
    fr_risk_018()
    fr_risk_019()
    fr_risk_020()
    fr_risk_049()
    fr_risk_050()
    fr_risk_059()
    fr_risk_060()
    fr_risk_061()


if __name__ == "__main__":
    main()
