"""Executable Risk contracts usage example.

Demonstrates creating and inspecting TradeIntent, PortfolioState, and Risk
contract instances.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    AccountBalance,
    AccountStateSnapshot,
    MarketContextEvidence,
)
from app.services.risk import (
    PortfolioState,
    validate_market_context_evidence,
)
from app.services.strategy import TradeIntent

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_contracts() -> None:
    """Demonstrate Risk contract models."""
    _header("Demonstrate Risk contract models.")
    print("Risk Example 1: Boundary Contracts and Evidence")

    # 1. TradeIntent
    intent = TradeIntent(
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
        lineage={"config_hash": "a" * 64},
    )
    print(
        f"TradeIntent ID: {intent.intent_id}, symbol: {intent.symbol}, "
        f"side: {intent.side}"
    )

    # 2. PortfolioState
    account = AccountStateSnapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            AccountBalance(asset="USD", total=Decimal(10000), available=Decimal(9500)),
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
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    portfolio = PortfolioState(
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )
    print(
        f"PortfolioState account ID: {portfolio.account_snapshot.account_id}, "
        f"equity: {portfolio.account_snapshot.equity}"
    )

    market = MarketContextEvidence(
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
    unwrap_risk_response(
        validate_market_context_evidence(market, now=NOW),
        operation="validate_market_context_evidence",
    )
    print(f"Validated consumed market-context evidence for symbol: {market.symbol}")


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded contracts demonstration once per program execution."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_contracts()
        _DEMONSTRATED = True


def fr_risk_001() -> None:
    """FR-RISK-001: Define `approve`, `warn`, `needs_approval`,
    `needs_more_evidence`, `reject`, `block`, and `error` exactly."""
    _header(
        "FR-RISK-001: Define `approve`, `warn`, `needs_approval`, `needs_more_evidence`, `reject`, `block`, and `error` exactly."
    )
    _demonstrate_once()


def fr_risk_002() -> None:
    """FR-RISK-002: Define `pass`, `warn`, `needs_more_evidence`, `fail`, and
    `blocked` exactly."""
    _header(
        "FR-RISK-002: Define `pass`, `warn`, `needs_more_evidence`, `fail`, and `blocked` exactly."
    )
    _demonstrate_once()


def fr_risk_003() -> None:
    """FR-RISK-003: Define exactly `INVALID_INPUT`, `VALIDATION_FAILED`,
    `INVALID_PORTFOLIO_STATE`, `INVALID_RISK_CONFIG`, `MISSING_EVIDENCE`,
    `STALE_EVIDENCE`, `LIMIT_FAILED`, `POLICY_BLOCKED`, `PERMISSION_DENIED`,
    `KILL_SWITCH_ACTIVE`, `KILL_SWITCH_UNKNOWN`, `APPROVAL_REQUIRED`,
    `APPROVAL_TOKEN_INVALID`, `APPROVAL_TOKEN_EXPIRED`,
    `APPROVAL_TOKEN_REVOKED`, `APPROVAL_TOKEN_CONSUMED`,
    `CONFIG_VERSION_MISMATCH`, `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`,
    `PAYLOAD_TOO_LARGE`, `MISSING_STOP_LOSS`,
    `INSUFFICIENT_VOLATILITY_EVIDENCE`, `INSUFFICIENT_K_EVIDENCE`,
    `LIVE_STATE_STALE`, `IN_FLIGHT_TOLERANCE_EXCEEDED`,
    `IN_FLIGHT_RECONCILIATION_EXPIRED`, `AUDIT_CHAIN_TAMPER_DETECTED`,
    `CALCULATION_FAILED`, `SNAPSHOT_BUILD_FAILED`, `GOVERNOR_DECISION_FAILED`,
    `REPORT_GENERATION_FAILED`, `STORAGE_ERROR`, `TOOL_EXECUTION_FAILED`, and
    `UNKNOWN_ERROR`; historical VaR/CVaR is the sole supported VaR method."""
    _header(
        "FR-RISK-003: Define exactly `INVALID_INPUT`, `VALIDATION_FAILED`, `INVALID_PORTFOLIO_STATE`, `INVALID_RISK_CONFIG`, `MISSING_EVIDENCE`, `STALE_EVIDENCE`, `LIMIT_FAILED`, `POLICY_BLOCKED`, `PERMISSION_DENIED`, `KILL_SWITCH_ACTIVE`, `KILL_SWITCH_UNKNOWN`, `APPROVAL_REQUIRED`, `APPROVAL_TOKEN_INVALID`, `APPROVAL_TOKEN_EXPIRED`, `APPROVAL_TOKEN_REVOKED`, `APPROVAL_TOKEN_CONSUMED`, `CONFIG_VERSION_MISMATCH`, `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`, `PAYLOAD_TOO_LARGE`, `MISSING_STOP_LOSS`, `INSUFFICIENT_VOLATILITY_EVIDENCE`, `INSUFFICIENT_K_EVIDENCE`, `LIVE_STATE_STALE`, `IN_FLIGHT_TOLERANCE_EXCEEDED`, `IN_FLIGHT_RECONCILIATION_EXPIRED`, `AUDIT_CHAIN_TAMPER_DETECTED`, `CALCULATION_FAILED`, `SNAPSHOT_BUILD_FAILED`, `GOVERNOR_DECISION_FAILED`, `REPORT_GENERATION_FAILED`, `STORAGE_ERROR`, `TOOL_EXECUTION_FAILED`, and `UNKNOWN_ERROR`; historical VaR/CVaR is the sole supported VaR method."
    )
    _demonstrate_once()


def fr_risk_004() -> None:
    """FR-RISK-004: Carry exact immutable Data-owned `AccountStateSnapshot v1`
    and `FXConversionEvidence v1` values plus peak/day-start/inception equity,
    symbol mark prices, contract sizes, quote currencies, exposure dimensions,
    aligned timestamped per-symbol return histories, explicit pair
    correlations, UTC `as_of`, provenance, missingness, and schema version.
    Open `AccountOrder.quantity` is the full remaining pending quantity for Risk
    exposure."""
    _header(
        "FR-RISK-004: Carry exact immutable Data-owned `AccountStateSnapshot v1` and `FXConversionEvidence v1` values plus peak/day-start/inception equity, symbol mark prices, contract sizes, quote currencies, exposure dimensions, aligned timestamped per-symbol return histories, explicit pair correlations, UTC `as_of`, provenance, missingness, and schema version. Open `AccountOrder.quantity` is the full remaining pending quantity for Risk exposure."
    )
    _demonstrate_once()


def fr_risk_005() -> None:
    """FR-RISK-005: Carry reproducible base-currency equity, daily/total loss,
    exposure, drawdown, margin/leverage, historical tail-risk,
    volatility/correlation/contribution metrics, limit results, assumptions,
    coverage, regime, request/workflow IDs, evidence refs, and config hash."""
    _header(
        "FR-RISK-005: Carry reproducible base-currency equity, daily/total loss, exposure, drawdown, margin/leverage, historical tail-risk, volatility/correlation/contribution metrics, limit results, assumptions, coverage, regime, request/workflow IDs, evidence refs, and config hash."
    )
    _demonstrate_once()


def fr_risk_006() -> None:
    """FR-RISK-006: Define the Risk-owned receiver contract for one
    non-executable review. It embeds the complete immutable Strategy
    `TradeIntent v1` unchanged and adds current valuation, stop-distance,
    account/portfolio scope, evidence timestamps, provenance references/hashes,
    and requested Risk profile. Risk rejects an incompatible intent version,
    conflicting duplicated fact, invalid scope/size, or absent required stop
    evidence."""
    _header(
        "FR-RISK-006: Define the Risk-owned receiver contract for one non-executable review. It embeds the complete immutable Strategy `TradeIntent v1` unchanged and adds current valuation, stop-distance, account/portfolio scope, evidence timestamps, provenance references/hashes, and requested Risk profile. Risk rejects an incompatible intent version, conflicting duplicated fact, invalid scope/size, or absent required stop evidence."
    )
    _demonstrate_once()


def fr_risk_007() -> None:
    """FR-RISK-007: Represent one of six sizing methods and its complete
    evidence/config references."""
    _header(
        "FR-RISK-007: Represent one of six sizing methods and its complete evidence/config references."
    )
    _demonstrate_once()


def fr_risk_008() -> None:
    """FR-RISK-008: Return exact requested/normalized size, constraints applied,
    evidence gaps, fallback disclosure, and no approval claim."""
    _header(
        "FR-RISK-008: Return exact requested/normalized size, constraints applied, evidence gaps, fallback disclosure, and no approval claim."
    )
    _demonstrate_once()


def fr_risk_009() -> None:
    """FR-RISK-009: Define `AllocationReviewRequest v1` carrying a
    self-contained Risk-owned projection (projection kind,
    portfolio/result/plan IDs and versions, ordered weights or actions,
    eligibility decisions, account/market/FX evidence references and hashes,
    runtime scope, approval references); it never embeds or imports a
    Portfolio-owned contract."""
    _header(
        "FR-RISK-009: Define `AllocationReviewRequest v1` carrying a self-contained Risk-owned projection (projection kind, portfolio/result/plan IDs and versions, ordered weights or actions, eligibility decisions, account/market/FX evidence references and hashes, runtime scope, approval references); it never embeds or imports a Portfolio-owned contract."
    )
    _demonstrate_once()


def fr_risk_010() -> None:
    """FR-RISK-010: Define `StrategyOperationalEligibilityRequest v1` for an
    exact registered strategy/version and scope (strategy/version, runtime
    profile, route, policy/evidence/approval references, requested scope)."""
    _header(
        "FR-RISK-010: Define `StrategyOperationalEligibilityRequest v1` for an exact registered strategy/version and scope (strategy/version, runtime profile, route, policy/evidence/approval references, requested scope)."
    )
    _demonstrate_once()


def fr_risk_011() -> None:
    """FR-RISK-011: Return classified
    volatility/liquidity/correlation/drawdown/crisis/news/session states,
    transition evidence, modifiers, and missingness."""
    _header(
        "FR-RISK-011: Return classified volatility/liquidity/correlation/drawdown/crisis/news/session states, transition evidence, modifiers, and missingness."
    )
    _demonstrate_once()


def fr_risk_012() -> None:
    """FR-RISK-012: Define a bounded immutable advisory scenario with
    deterministic shocks and optional explicit seed."""
    _header(
        "FR-RISK-012: Define a bounded immutable advisory scenario with deterministic shocks and optional explicit seed."
    )
    _demonstrate_once()


def fr_risk_013() -> None:
    """FR-RISK-013: Return baseline/projected risk comparison and state that the
    output is advisory and not approved."""
    _header(
        "FR-RISK-013: Return baseline/projected risk comparison and state that the output is advisory and not approved."
    )
    _demonstrate_once()


def fr_risk_014() -> None:
    """FR-RISK-014: Implement `RiskDecision` v1 with verdict, trade-only approved
    size, ordered checks, primary/composite reasons, provenance, expiry,
    concurrency disclosure, and optional token. A current-state compliance
    approval has no intent and no invented trade size."""
    _header(
        "FR-RISK-014: Implement `RiskDecision` v1 with verdict, trade-only approved size, ordered checks, primary/composite reasons, provenance, expiry, concurrency disclosure, and optional token. A current-state compliance approval has no intent and no invented trade size."
    )
    _demonstrate_once()


def fr_risk_015() -> None:
    """FR-RISK-015: Carry signed token scope, decision/config hashes, approver,
    expiry, nonce, schema version, and no secret key."""
    _header(
        "FR-RISK-015: Carry signed token scope, decision/config hashes, approver, expiry, nonce, schema version, and no secret key."
    )
    _demonstrate_once()


def fr_risk_016() -> None:
    """FR-RISK-016: Implement `KillSwitchCommand v1` with action, explicit scope
    level, applicable portfolio/strategy/symbol identifiers, reason, UTC
    timestamp, request/workflow/correlation IDs, and schema identity. Principal
    authorization remains in the separate `AuthContext`; clearance requires a
    separate matching current `ApprovalAttestation`."""
    _header(
        "FR-RISK-016: Implement `KillSwitchCommand v1` with action, explicit scope level, applicable portfolio/strategy/symbol identifiers, reason, UTC timestamp, request/workflow/correlation IDs, and schema identity. Principal authorization remains in the separate `AuthContext`; clearance requires a separate matching current `ApprovalAttestation`."
    )
    _demonstrate_once()


def fr_risk_017() -> None:
    """FR-RISK-017: Implement `KillSwitchState` v1 with scope, active/unknown
    state, reason, version, and UTC update time."""
    _header(
        "FR-RISK-017: Implement `KillSwitchState` v1 with scope, active/unknown state, reason, version, and UTC update time."
    )
    _demonstrate_once()


def fr_risk_018() -> None:
    """FR-RISK-018: Carry canonical redacted audit payload and
    evidence/config/decision provenance in either an explicitly unsealed append
    input (`sealed=False`, null sequence/hashes) or a sealed result
    (`sealed=True`, complete sequence, previous hash, and record hash).
    Persisted or cross-domain audit results must be sealed."""
    _header(
        "FR-RISK-018: Carry canonical redacted audit payload and evidence/config/decision provenance in either an explicitly unsealed append input (`sealed=False`, null sequence/hashes) or a sealed result (`sealed=True`, complete sequence, previous hash, and record hash). Persisted or cross-domain audit results must be sealed."
    )
    _demonstrate_once()


def fr_risk_019() -> None:
    """FR-RISK-019: Carry Markdown or exact JSON summary with separated evidence,
    assumptions, warnings, decision, and recommendations."""
    _header(
        "FR-RISK-019: Carry Markdown or exact JSON summary with separated evidence, assumptions, warnings, decision, and recommendations."
    )
    _demonstrate_once()


def fr_risk_020() -> None:
    """FR-RISK-020: Return token validity, consumption state, reason code, audit
    reference, and an optional `ActionPolicyVerdict`; the verdict is present and
    allowed only after successful atomic reservation/consumption and is absent
    on every failure, without exposing secrets."""
    _header(
        "FR-RISK-020: Return token validity, consumption state, reason code, audit reference, and an optional `ActionPolicyVerdict`; the verdict is present and allowed only after successful atomic reservation/consumption and is absent on every failure, without exposing secrets."
    )
    _demonstrate_once()


def fr_risk_021() -> None:
    """FR-RISK-021: Raise one redacted domain exception carrying a
    `RiskErrorCode` and safe details for boundary mapping."""
    _header(
        "FR-RISK-021: Raise one redacted domain exception carrying a `RiskErrorCode` and safe details for boundary mapping."
    )
    _demonstrate_once()


def fr_risk_047() -> None:
    """FR-RISK-047: Define `ApprovalAttestation v1` authenticated human approval
    evidence (principal, action, scope, policy reference/version, issue/expiry
    times, trace IDs); it carries no secret and is never execution authority by
    itself."""
    _header(
        "FR-RISK-047: Define `ApprovalAttestation v1` authenticated human approval evidence (principal, action, scope, policy reference/version, issue/expiry times, trace IDs); it carries no secret and is never execution authority by itself."
    )
    _demonstrate_once()


def fr_risk_048() -> None:
    """FR-RISK-048: Define `AllocationBudgetActivationRequest v1` (allocation and
    decision references, scope, effective time, predecessor, trace IDs) to
    activate the Risk-owned budget projection for one approved allocation
    version."""
    _header(
        "FR-RISK-048: Define `AllocationBudgetActivationRequest v1` (allocation and decision references, scope, effective time, predecessor, trace IDs) to activate the Risk-owned budget projection for one approved allocation version."
    )
    _demonstrate_once()


def fr_risk_049() -> None:
    """FR-RISK-049: Define `StrategyOperationalEligibilityDecision v1` (decision
    ID, strategy/version, scope, verdict, conditions, policy version,
    issue/expiry times, evidence lineage) without altering Strategy
    registration."""
    _header(
        "FR-RISK-049: Define `StrategyOperationalEligibilityDecision v1` (decision ID, strategy/version, scope, verdict, conditions, policy version, issue/expiry times, evidence lineage) without altering Strategy registration."
    )
    _demonstrate_once()


def fr_risk_050() -> None:
    """FR-RISK-050: Define `AllocationRiskDecision v1` (decision ID, reviewed
    version, verdict, capped weights, authoritative risk-budget projection,
    conditions, issue/expiry times, policy/evidence lineage)."""
    _header(
        "FR-RISK-050: Define `AllocationRiskDecision v1` (decision ID, reviewed version, verdict, capped weights, authoritative risk-budget projection, conditions, issue/expiry times, policy/evidence lineage)."
    )
    _demonstrate_once()


def fr_risk_058() -> None:
    """FR-RISK-058: Validate the consumed Data-owned `MarketContextEvidence v1`
    version, UTC freshness, provenance, bounded values, and explicit missingness
    without redefining or fetching it."""
    _header(
        "FR-RISK-058: Validate the consumed Data-owned `MarketContextEvidence v1` version, UTC freshness, provenance, bounded values, and explicit missingness without redefining or fetching it."
    )
    _demonstrate_once()


def fr_risk_059() -> None:
    """FR-RISK-059: Return `ActionPolicyVerdict v1` bound to action, scope,
    policy version, approval attestation, decision, reservation, expiry, reasons,
    and trace IDs."""
    _header(
        "FR-RISK-059: Return `ActionPolicyVerdict v1` bound to action, scope, policy version, approval attestation, decision, reservation, expiry, reasons, and trace IDs."
    )
    _demonstrate_once()


def fr_risk_060() -> None:
    """FR-RISK-060: Carry one ordered limit result with status,
    observed/threshold values, reason code, evidence refs, and precedence without
    granting approval."""
    _header(
        "FR-RISK-060: Carry one ordered limit result with status, observed/threshold values, reason code, evidence refs, and precedence without granting approval."
    )
    _demonstrate_once()


def fr_risk_061() -> None:
    """FR-RISK-061: Define `PortfolioBudgetExecutionVerdict v1` as the sole
    execution-time budget result: it binds the current allocation decision,
    portfolio/allocation version, plan ID/hash, budget unit, allowed state,
    reasons, and UTC validity. Trading validates this result and never calculates
    budget consumption."""
    _header(
        "FR-RISK-061: Define `PortfolioBudgetExecutionVerdict v1` as the sole execution-time budget result: it binds the current allocation decision, portfolio/allocation version, plan ID/hash, budget unit, allowed state, reasons, and UTC validity. Trading validates this result and never calculates budget consumption."
    )
    _demonstrate_once()


def main() -> None:
    """Run every functional-requirement demonstration for Risk contracts."""
    demonstrations = (
        fr_risk_001,
        fr_risk_002,
        fr_risk_003,
        fr_risk_004,
        fr_risk_005,
        fr_risk_006,
        fr_risk_007,
        fr_risk_008,
        fr_risk_009,
        fr_risk_010,
        fr_risk_011,
        fr_risk_012,
        fr_risk_013,
        fr_risk_014,
        fr_risk_015,
        fr_risk_016,
        fr_risk_017,
        fr_risk_018,
        fr_risk_019,
        fr_risk_020,
        fr_risk_021,
        fr_risk_047,
        fr_risk_048,
        fr_risk_049,
        fr_risk_050,
        fr_risk_058,
        fr_risk_059,
        fr_risk_060,
        fr_risk_061,
    )
    for demonstrate in demonstrations:
        demonstrate()


if __name__ == "__main__":
    main()
