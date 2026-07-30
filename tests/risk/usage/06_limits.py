"""Executable Risk limit-evaluation usage example.

Demonstrates deterministic portfolio limit evaluation over an immutable snapshot.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import build_market_context_evidence
from app.services.risk import (
    create_firm_mandate,
    create_portfolio_risk_snapshot,
    create_risk_config,
    evaluate_market_context,
    evaluate_portfolio_limits,
    evaluate_single_day_profit_share,
)

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _snapshot() -> create_portfolio_risk_snapshot:
    """Build immutable portfolio risk snapshot."""
    return create_portfolio_risk_snapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        initial_balance=Decimal(10000),
        daily_loss=Decimal(0),
        total_loss=Decimal(0),
        cumulative_profit=Decimal(500),
        current_day_profit=Decimal(100),
        proposal_best_case_profit=Decimal(100),
        gross_exposure=Decimal(0),
        net_exposure=Decimal(0),
        drawdown=Decimal(0),
        peak_equity=Decimal(10000),
        highest_eod_balance=Decimal(10000),
        margin_utilization=Decimal(0),
        effective_leverage=Decimal(0),
        historical_var=None,
        historical_cvar=None,
        volatility=None,
        portfolio_correlation=Decimal(0),
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash="a" * 64,
        evidence_refs={"account": "account-evidence-1"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def _config() -> create_risk_config:
    """Build risk policy config."""
    return create_risk_config(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
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


def example_limits() -> None:
    """Demonstrate evaluating portfolio and market-context limits."""
    _header("Demonstrate evaluating portfolio and market-context limits.")
    print("Risk Example 6: Deterministic Limit Evaluation")

    snapshot = _snapshot()
    config = _config()

    portfolio_results = unwrap_risk_response(
        evaluate_portfolio_limits(snapshot, config, now=NOW),
        operation="evaluate_portfolio_limits",
    )
    print(f"Evaluated portfolio limit results: {len(portfolio_results)}")
    print(f"Ordered portfolio statuses: {[r.status for r in portfolio_results]}")

    market_results = unwrap_risk_response(
        evaluate_market_context(_market(), config, now=NOW),
        operation="evaluate_market_context",
    )
    print(f"Evaluated market-context results: {len(market_results)}")
    print(f"Ordered market statuses: {[r.status for r in market_results]}")


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded limits demonstration once."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_limits()
        _DEMONSTRATED = True


def fr_risk_027() -> None:
    """FR-RISK-027: Evaluate daily/total loss, drawdown state, consistency,
    exposure/concentration, margin/leverage, historical tail risk, correlation,
    and freshness in deterministic precedence, returning primary and composite
    failures."""
    _header(
        "FR-RISK-027: Evaluate daily/total loss, drawdown state, consistency, exposure/concentration, margin/leverage, historical tail risk, correlation, and freshness in deterministic precedence, returning primary and composite failures."
    )
    _demonstrate_once()


def fr_risk_028() -> None:
    """FR-RISK-028: Evaluate supplied spread, liquidity availability, session,
    and normalized calendar state without external fetches, hidden unit
    conversion, or naive/aware datetime comparison. Slippage is excluded because
    `build_market_context_evidence v1` does not carry it and execution slippage is
    receiver-owned post-trade evidence."""
    _header(
        "FR-RISK-028: Evaluate supplied spread, liquidity availability, session, and normalized calendar state without external fetches, hidden unit conversion, or naive/aware datetime comparison. Slippage is excluded because `build_market_context_evidence v1` does not carry it and execution slippage is receiver-owned post-trade evidence."
    )
    _demonstrate_once()


def fr_risk_062() -> None:
    """FR-RISK-062: Consume only Data-normalized calendar state and exact
    blackout provenance, block configured release states, pass authoritative open
    evidence, and apply `missing_calendar_mode` to unavailable evidence; Risk
    remains the sole news-trading policy authority."""
    _header(
        "FR-RISK-062: Consume only Data-normalized calendar state and exact blackout provenance, block configured release states, pass authoritative open evidence, and apply missing_calendar_mode to unavailable evidence; Risk remains the sole news-trading policy authority."
    )
    _demonstrate_once()


def _mandate() -> create_firm_mandate:
    """Build a verified mandate for the forward checks."""
    return create_firm_mandate(
        account_id="account-1",
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="funded",
        initial_balance=Decimal(10000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
        consistency_rule={
            "type": "max_single_day_share_of_profit",
            "value": Decimal("0.4"),
            "evaluated": "retrospective",
            "applies_in_phase": ("funded",),
        },
    )


def fr_risk_066() -> None:
    """FR-RISK-066: Evaluate the drawdown floor under the configured mode:
    `static` from a fixed reference, `trailing_eod` from the highest end-of-day
    balance with an optional ratchet ceiling at the initial balance, or
    `trailing_intraday` from peak equity including unrealised gains. Report
    remaining headroom as an absolute amount in account currency, not only as
    a ratio of peak."""
    _header("FR-RISK-066: Absolute drawdown headroom")
    mandate = _mandate()
    results = unwrap_risk_response(
        evaluate_portfolio_limits(_snapshot(), _config(), now=NOW, mandate=mandate),
        operation="evaluate_portfolio_limits",
    )
    drawdown = next(item for item in results if item.limit_id == "drawdown")
    print(f"Drawdown headroom in account currency: {drawdown.headroom_value}")


def fr_risk_067() -> None:
    """FR-RISK-067: Evaluate daily and total loss against a configurable
    reference basis, supporting a fixed initial balance in addition to the
    existing day-start and inception equity bases, and record which basis was
    applied."""
    _header("FR-RISK-067: Initial-balance loss basis")
    mandate = _mandate()
    results = unwrap_risk_response(
        evaluate_portfolio_limits(_snapshot(), _config(), now=NOW, mandate=mandate),
        operation="evaluate_portfolio_limits",
    )
    daily = next(item for item in results if item.limit_id == "daily_loss")
    print(f"Daily-loss reference basis: {daily.reference_basis}")
    print(f"Daily-loss headroom: {daily.headroom_value}")


def fr_risk_068() -> None:
    """FR-RISK-068: Project the share of cumulative profit a single trading day
    would represent if the account were settled now, and fail or constrain
    when a proposal's best case would exceed the configured maximum single-day
    share. This is a forward projection, distinct from the existing
    snapshot-integrity consistency check."""
    _header("FR-RISK-068: Forward single-day profit-share projection")
    result = unwrap_risk_response(
        evaluate_single_day_profit_share(_snapshot(), _mandate(), now=NOW),
        operation="evaluate_single_day_profit_share",
    )
    print(f"Projected share status: {result.status}")
    print(f"Projected share headroom: {result.headroom_value}")


def main() -> None:
    """Run every functional-requirement demonstration for Risk limits."""
    for demonstrate in (
        fr_risk_027,
        fr_risk_028,
        fr_risk_062,
        fr_risk_066,
        fr_risk_067,
        fr_risk_068,
    ):
        demonstrate()


if __name__ == "__main__":
    main()
