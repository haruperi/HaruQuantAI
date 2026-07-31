"""Executable Trading validation usage example.

Demonstrates FEAT-TRD-03 order validation and execution readiness.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_account_state_snapshot
from app.services.risk import (
    create_kill_switch_state,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.trading import (
    assess_execution_readiness,
    build_execution_plan,
    create_readiness_assessment,
    create_route_snapshot,
    create_trading_request,
    get_route_snapshot,
    validate_order_request,
)

# Private type-only aliases; Risk exposes functions, not contract classes.
KillSwitchState = object
RiskDecisionPackage = object
ReadinessAssessment = Any
RouteSnapshot = Any
TradingRequest = Any

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


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


def _request() -> TradingRequest:
    """Build complete validated order material."""
    return create_trading_request(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        action="submit_order",
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        intent_id="usage-intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity=Decimal("1.00"),
        risk_decision_id="usage-risk-001",
        action_policy_verdict_id="usage-verdict-001",
        approval_token_ref="usage-approval-001",
        idempotency_key="usage-key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
        instrument_min_quantity=Decimal("0.01"),
        instrument_max_quantity=Decimal("100.00"),
        instrument_quantity_step=Decimal("0.01"),
    )


def _account() -> object:
    """Build current Data-owned account evidence."""
    return build_account_state_snapshot(
        account_id="usage-account-001",
        currency="USD",
        balances=(),
        equity=Decimal(10000),
        margin_available=Decimal(9000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="simulator",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-dd37fc1c2cd6d665f9a7a7f9a2482efe3347c7bb51ac073ef12ef9b7eb511055",
    )


def _symbol_capability() -> dict[str, object]:
    """Build explicit Broker feature and symbol metadata evidence."""
    return {
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "quantity_unit": "units",
    }


def _snapshot() -> RouteSnapshot:
    """Build current explicit route facts."""
    return create_route_snapshot(
        route="sim",
        provider_id=None,
        account_id="usage-account-001",
        symbol="EURUSD",
        facts={"quote": {"bid": "1.0999", "ask": "1.1001"}},
        source_id="usage-data-source-001",
        authority_id="simulator",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        available=True,
        fresh=True,
        capabilities=("submit_order",),
    )


def _risk() -> RiskDecisionPackage:
    """Build a real approving Risk decision package."""
    return create_risk_decision_package(
        decision_id="usage-risk-001",
        intent_id="usage-intent-001",
        state=get_decision_state("APPROVE"),
        requested_size=Decimal("1.00"),
        approved_size=Decimal("1.00"),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "usage-snapshot-001"},
        config_hash="a" * 64,
        concurrency_disclosure="risk-store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        token=None,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _switch() -> KillSwitchState:
    """Build inactive real Risk kill-switch state."""
    return create_kill_switch_state(
        state_id="usage-switch-001",
        scope_level="global",
        scope={},
        state="inactive",
        reason="usage-evidence",
        version=1,
        updated_at=NOW,
    )


def _policy() -> dict[str, object]:
    """Build JSON-safe Risk action-policy projection."""
    return {
        "allowed": True,
        "verdict_id": "usage-verdict-001",
        "action": "submit_order",
        "expires_at": (NOW + timedelta(minutes=1)).isoformat(),
    }


def fr_trd_024() -> None:
    """FR-TRD-024: Stage 2 — Validate order request parameters and preconditions."""
    _header("Stage 2: Pre-route Validation - Validate Order Request (FR-TRD-024)")
    validated = validate_order_request(_request(), _account(), _symbol_capability())
    print(_format_result(validated))
    print(f"Data -> status='{validated.status}'")


def fr_trd_026() -> None:
    """FR-TRD-026: Stage 1 — Get timestamped route snapshot facts."""
    _header("Stage 1: Facts Loading - Get Route Snapshot (FR-TRD-026)")

    def source(_route: object, _provider: object) -> dict[str, object]:
        return _snapshot().model_dump(mode="python")

    route_snap = get_route_snapshot(_request(), source)  # type: ignore[arg-type]
    print(_format_result(route_snap))
    print(f"Data -> status='{route_snap.status}'")


def fr_trd_027() -> None:
    """FR-TRD-027: Stage 2 — Assess execution readiness across required evidence."""
    _header("Stage 2: Readiness Evaluation - Assess Execution Readiness (FR-TRD-027)")
    assessment = assess_execution_readiness(
        _request(),
        _snapshot(),
        _risk(),
        _switch(),
        _policy(),  # type: ignore[arg-type]
        {
            "route_snapshot": Decimal(30),
            "risk_decision": Decimal(30),
            "kill_switch": Decimal(30),
        },
    )
    print(_format_result(assessment))
    print(f"Data -> status='{assessment.status}'")


def fr_trd_028() -> None:
    """FR-TRD-028: Stage 3 — Build deterministic execution plan without side-effects."""
    _header("Stage 3: Plan Construction - Build Execution Plan (FR-TRD-028)")
    readiness = create_readiness_assessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "usage-risk-001"},
        assessed_at=NOW,
    )
    plan = build_execution_plan(_request(), readiness)
    print(_format_result(plan))
    print(f"Data -> status='{plan.status}'")


def fr_trd_059() -> None:
    """FR-TRD-059: Stage 3 — Expose immutable RouteSnapshot contract."""
    _header("Stage 3: Route Snapshot DTO - Construct RouteSnapshot (FR-TRD-059)")
    snap = _snapshot()
    print(_format_result(snap))
    print(f"Data -> available={snap.available}, fresh={snap.fresh}")


def fr_trd_060() -> None:
    """FR-TRD-060: Stage 3 — Expose ReadinessAssessment DTO."""
    _header("Stage 3: Readiness DTO - Construct ReadinessAssessment (FR-TRD-060)")
    readiness = create_readiness_assessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "usage-risk-001"},
        assessed_at=NOW,
    )
    print(_format_result(readiness))
    print(f"Data -> passed={readiness.passed}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-03 — validation/ — Validation, Readiness, and Plans\n\n"
        "Purpose: Validate order requests, evaluate execution readiness, and construct deterministic execution plans.\n\n"
        "Module flow:\n"
        "-> Stage 1: Facts loading, quote inspection, and capability gathering\n"
        "-> Stage 2: Fail-closed order validation and multi-factor readiness evaluation\n"
        "-> Stage 3: Execution plan construction and DTO representation"
    )

    # Stage 1: Facts loading
    fr_trd_026()

    # Stage 2: Fail-closed validation & Readiness evaluation
    fr_trd_024()
    fr_trd_027()

    # Stage 3: Execution plan construction & DTO representation
    fr_trd_028()
    fr_trd_059()
    fr_trd_060()


if __name__ == "__main__":
    main()
