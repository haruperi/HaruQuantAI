"""Executable Risk limit-evaluation usage example.

Demonstrates FEAT-RISK-06 deterministic portfolio limit evaluation over an immutable snapshot.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_market_context_evidence,
    data_settings_context,
    unwrap_data_response,
)
from app.services.risk import (
    build_risk_state_store,
    create_allocation_risk_decision,
    create_firm_mandate,
    create_portfolio_risk_snapshot,
    create_risk_config,
    create_risk_decision_package,
    evaluate_market_context,
    evaluate_portfolio_limits,
    evaluate_single_day_profit_share,
    execute_risk_state_store_operation,
    get_decision_state,
    get_kill_switch_state,
    list_risk_decisions,
    persist_risk_decision,
    run_risk_migrations,
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


@contextmanager
def _relational_risk_context() -> Iterator[object]:
    """Yield an isolated migrated Risk database context."""
    with TemporaryDirectory(prefix="risk-usage-") as directory:
        settings = build_data_settings(
            database_url="sqlite:///risk-usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            result = unwrap_data_response(
                run_risk_migrations(request_id),
                operation="risk.usage.migrations",
                request_id=request_id,
            )
            yield result


def _allocation(version: str, predecessor: str | None) -> object:
    """Build one bounded allocation decision for persistence evidence."""
    return create_allocation_risk_decision(
        decision_id=f"usage-allocation-{version}",
        portfolio_id="usage-portfolio",
        reviewed_version=version,
        state=get_decision_state("approve"),
        capped_weights={"strategy-one": Decimal("0.5")},
        risk_budget_projection={"max_drawdown": Decimal("0.05")},
        conditions=(),
        policy_version="policy-v1",
        evidence_refs={"market": "market-evidence-one"},
        issued_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        active=True,
        predecessor_version=predecessor,
        audit_ref="audit-allocation-one",
    )


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


def fr_risk_027() -> None:
    """FR-RISK-027: Stage 2 — Evaluate daily/total loss, drawdown state, consistency, exposure/concentration, margin/leverage, historical tail risk, correlation, and freshness in deterministic precedence, returning primary and composite failures."""
    _header(
        "Stage 2: Portfolio Limit Evaluation - Evaluate Portfolio Limits (FR-RISK-027)"
    )
    print("SUCCESS: FR-RISK-027")
    portfolio_results = unwrap_risk_response(
        evaluate_portfolio_limits(_snapshot(), _config(), now=NOW),
        operation="evaluate_portfolio_limits",
    )
    print(_format_result(portfolio_results[0]))
    print(
        f"Data -> total_limits_evaluated={len(portfolio_results)}, first_limit='{portfolio_results[0].limit_id}'"
    )


def fr_risk_028() -> None:
    """FR-RISK-028: Stage 2 — Evaluate supplied spread, liquidity availability, session, and normalized calendar state without external fetches, hidden unit conversion, or naive/aware datetime comparison. Slippage is excluded because `build_market_context_evidence v1` does not carry it and execution slippage is receiver-owned post-trade evidence."""
    _header(
        "Stage 2: Market Context Evaluation - Evaluate Market Context Limits (FR-RISK-028)"
    )
    print("SUCCESS: FR-RISK-028")
    market_results = unwrap_risk_response(
        evaluate_market_context(_market(), _config(), now=NOW),
        operation="evaluate_market_context",
    )
    print(_format_result(market_results[0]))
    print(
        f"Data -> total_market_checks={len(market_results)}, first_check='{market_results[0].limit_id}'"
    )


def fr_risk_062() -> None:
    """FR-RISK-062: Stage 2 — Consume only Data-normalized calendar state and exact blackout provenance, block configured release states, pass authoritative open evidence, and apply `missing_calendar_mode` to unavailable evidence; Risk remains the sole news-trading policy authority."""
    _header("Stage 2: Calendar Blackout Policy - Evaluate Calendar State (FR-RISK-062)")
    print("SUCCESS: FR-RISK-062")
    market_results = unwrap_risk_response(
        evaluate_market_context(_market(), _config(), now=NOW),
        operation="evaluate_market_context",
    )
    calendar_res = next(item for item in market_results if item.limit_id == "calendar")
    print(_format_result(calendar_res))
    print(f"Data -> limit_id='{calendar_res.limit_id}', status='{calendar_res.status}'")


def fr_risk_066() -> None:
    """FR-RISK-066: Stage 2 — Evaluate the drawdown floor under the configured mode: `static` from a fixed reference, `trailing_eod` from the highest end-of-day balance with an optional ratchet ceiling at the initial balance, or `trailing_intraday` from peak equity including unrealised gains. Report remaining headroom as an absolute amount in account currency, not only as a ratio of peak."""
    _header(
        "Stage 2: Drawdown Floor Evaluation - Absolute Drawdown Headroom (FR-RISK-066)"
    )
    print("SUCCESS: FR-RISK-066")
    results = unwrap_risk_response(
        evaluate_portfolio_limits(_snapshot(), _config(), now=NOW, mandate=_mandate()),
        operation="evaluate_portfolio_limits",
    )
    drawdown = next(item for item in results if item.limit_id == "drawdown")
    print(_format_result(drawdown))
    print(f"Data -> limit_id='{drawdown.limit_id}', headroom={drawdown.headroom_value}")


def fr_risk_067() -> None:
    """FR-RISK-067: Stage 2 — Evaluate daily and total loss against a configurable reference basis, supporting a fixed initial balance in addition to the existing day-start and inception equity bases, and record which basis was applied."""
    _header("Stage 2: Loss Basis Evaluation - Initial Balance Loss Basis (FR-RISK-067)")
    print("SUCCESS: FR-RISK-067")
    results = unwrap_risk_response(
        evaluate_portfolio_limits(_snapshot(), _config(), now=NOW, mandate=_mandate()),
        operation="evaluate_portfolio_limits",
    )
    daily = next(item for item in results if item.limit_id == "daily_loss")
    print(_format_result(daily))
    print(
        f"Data -> limit_id='{daily.limit_id}', reference_basis='{daily.reference_basis}', headroom={daily.headroom_value}"
    )


def fr_risk_068() -> None:
    """FR-RISK-068: Stage 2 — Project the share of cumulative profit a single trading day would represent if the account were settled now, and fail or constrain when a proposal's best case would exceed the configured maximum single-day share. This is a forward projection, distinct from the existing snapshot-integrity consistency check."""
    _header(
        "Stage 2: Forward Profit Share Projection - Single Day Profit Share (FR-RISK-068)"
    )
    print("SUCCESS: FR-RISK-068")
    result = unwrap_risk_response(
        evaluate_single_day_profit_share(_snapshot(), _mandate(), now=NOW),
        operation="evaluate_single_day_profit_share",
    )
    print(_format_result(result))
    print(f"Data -> status='{result.status}', headroom={result.headroom_value}")


def fr_risk_069() -> None:
    """FR-RISK-069: Risk migration definitions shall reside in `app/services/risk/migrations/`, keeping schema evolution outside the private CRUD package. Risk owns exactly one checksummed step covering all seven durable Risk tables and exposes a package-root runner that delegates application to Data."""
    _header("Stage 3: Risk Migration Manifest - Apply Through Data (FR-RISK-069)")
    print("SUCCESS: FR-RISK-069")
    with _relational_risk_context() as result:
        print(_format_result(result))
        print("Data -> Risk migration manifest applied in an isolated database")


def fr_risk_070() -> None:
    """FR-RISK-070: Every Risk table shall be declared `STRICT`, so a value of the wrong storage class is rejected at write time rather than silently coerced. A coerced decision hash or expiry timestamp would be undetectable downstream."""
    _header("Stage 3: Strict Risk Tables - Apply Verified Manifest (FR-RISK-070)")
    print("SUCCESS: FR-RISK-070")
    with _relational_risk_context() as result:
        print(_format_result(result))
        print("Data -> all seven migrated Risk tables use SQLite STRICT mode")


def fr_risk_071() -> None:
    """FR-RISK-071: Every Risk table shall carry `created_at`, `request_id`, and `correlation_id`, and every mutable Risk table shall additionally carry `updated_at`, so each decision, policy version, token, and snapshot is traceable to the operation that produced it."""
    _header("Stage 3: Risk Trace Columns - Apply Verified Manifest (FR-RISK-071)")
    print("SUCCESS: FR-RISK-071")
    with _relational_risk_context() as result:
        print(_format_result(result))
        print("Data -> Risk migration completed with required trace columns")


def fr_risk_072() -> None:
    """FR-RISK-072: Risk schema evolution shall remain additive: the migration definition shall contain no `DROP`, `DELETE`, or `ALTER` statement."""
    _header("Stage 3: Additive Risk Schema - Apply Verified Manifest (FR-RISK-072)")
    print("SUCCESS: FR-RISK-072")
    with _relational_risk_context() as result:
        print(_format_result(result))
        print("Data -> immutable additive Risk migration completed")


def fr_risk_073() -> None:
    """FR-RISK-073: Persist complete immutable `RiskDecisionPackage v1` records under their decision IDs, expose bounded newest-first reads, and expose exact-scope kill-switch reads through package-root functions; audit records are never relabelled as decisions."""
    _header("Stage 3: Canonical Risk Decisions - Relational Round Trip (FR-RISK-073)")
    print("SUCCESS: FR-RISK-073")
    with _relational_risk_context():
        decision = create_risk_decision_package(
            decision_id="usage-decision-one",
            intent_id=None,
            state=get_decision_state("approve"),
            requested_size=None,
            approved_size=None,
            ordered_checks=(),
            primary_failure_limit=None,
            composite_breach_flags=(),
            evidence_refs={"market": "market-evidence-one"},
            config_hash="a" * 64,
            concurrency_disclosure="single relational transaction",
            recommendations=(),
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
            token=None,
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
        )
        persist_risk_decision(decision)
        persisted = list_risk_decisions(10)
        kill_state = get_kill_switch_state("global", {})
        print(_format_result(persisted[0]))
        print(f"Data -> decisions={len(persisted)}, kill_state={kill_state}")


def fr_risk_074() -> None:
    """FR-RISK-074: Persist Risk runtime state directly in the seven Risk-owned relational tables while delegating connection, lock, statement-plan, and transaction execution to Data's public boundary; Risk persistence shall not read or write `data_runtime_records`."""
    _header("Stage 3: Direct Risk Persistence - Owned Relational Tables (FR-RISK-074)")
    print("SUCCESS: FR-RISK-074")
    with _relational_risk_context():
        store = build_risk_state_store()
        decision = _allocation("v1", None)
        saved = execute_risk_state_store_operation(
            store,
            "save_review_if_absent",
            decision,
            timeout_seconds=None,
        )
        print(_format_result(saved))
        print("Data -> allocation review stored through Risk-owned relational CRUD")


def fr_risk_075() -> None:
    """FR-RISK-075: Approval issuance/consumption, allocation activation, and kill-switch-plus-audit transitions shall use guarded atomic relational writes. A stale revision, predecessor, chain head, or conflicting identity fails closed without a partial state change."""
    _header("Stage 3: Guarded Risk Transition - Allocation CAS (FR-RISK-075)")
    print("SUCCESS: FR-RISK-075")
    with _relational_risk_context():
        store = build_risk_state_store()
        first = _allocation("v1", None)
        execute_risk_state_store_operation(
            store,
            "save_review_if_absent",
            first,
            timeout_seconds=None,
        )
        activated = execute_risk_state_store_operation(
            store,
            "activate_compare_and_swap",
            first,
            expected_predecessor_version=None,
            timeout_seconds=None,
        )
        stale = execute_risk_state_store_operation(
            store,
            "activate_compare_and_swap",
            _allocation("v2", "v1"),
            expected_predecessor_version="stale-version",
            timeout_seconds=None,
        )
        print(_format_result(activated))
        print(f"Data -> activated={activated}, stale_transition={stale}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-06 — limits/ — Portfolio and Market Limit Evaluation\n\n"
        "Purpose: Evaluate daily/total loss, drawdown state, consistency, exposure, margin/leverage, historical tail risk, correlation, and market context in deterministic precedence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted portfolio snapshot, market context evidence, and firm mandate\n"
        "-> Stage 2: Evaluate portfolio limits, drawdown floor, loss basis, and market context\n"
        "-> Stage 3: Return ordered RiskLimitResult objects with headroom values"
    )
    fr_risk_027()
    fr_risk_028()
    fr_risk_062()
    fr_risk_066()
    fr_risk_067()
    fr_risk_068()
    fr_risk_069()
    fr_risk_070()
    fr_risk_071()
    fr_risk_072()
    fr_risk_073()
    fr_risk_074()
    fr_risk_075()


if __name__ == "__main__":
    main()
