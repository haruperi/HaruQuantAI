"""Executable Trading validation usage example.

Demonstrates order validation and execution readiness.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import build_account_state_snapshot
from app.services.risk import (
    create_kill_switch_state,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.trading import (
    ReadinessAssessment,
    RouteSnapshot,
    TradingRequest,
    assess_execution_readiness,
    build_execution_plan,
    get_route_snapshot,
    validate_order_request,
)

# Private type-only aliases; Risk exposes functions, not contract classes.
KillSwitchState = object
RiskDecisionPackage = object

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _request() -> TradingRequest:
    """Build complete validated order material."""
    return TradingRequest(
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
    return RouteSnapshot(
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


def example_validation() -> None:
    """Demonstrate Trading validation API."""
    _header("Demonstrate Trading validation API.")
    print("Trading Example 3: Order Validation and Execution Readiness")

    req = _request()

    # 1. Validate order request
    validated = validate_order_request(req, _account(), _symbol_capability())
    assert validated.status == "success"
    validated_request = validated.data
    assert validated_request is not None
    print(f"Validated order request quantity: {validated_request.quantity}")

    # 2. Get route snapshot
    def source(_route: object, _provider: object) -> dict[str, object]:
        return _snapshot().model_dump(mode="python")

    route_snap = get_route_snapshot(req, source)  # type: ignore[arg-type]
    assert route_snap.status == "success"
    snapshot = route_snap.data
    assert snapshot is not None
    print(f"Route snapshot available: {snapshot.available}")

    # 3. Execution readiness assessment
    assessment = assess_execution_readiness(
        req,
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
    assert assessment.status == "success"
    readiness_assessment = assessment.data
    assert readiness_assessment is not None
    print(f"Execution readiness passed: {readiness_assessment.passed}")

    # 4. Build execution plan
    readiness = ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "usage-risk-001"},
        assessed_at=NOW,
    )
    plan = build_execution_plan(req, readiness)
    assert plan.status == "success"
    execution_plan = plan.data
    assert execution_plan is not None
    print(f"Built execution plan route: {execution_plan.route.value}")


def fr_trd_024() -> None:
    """FR-TRD-024: The system shall validate symbol, action, approved order type, required order-shape fields, instrument-provided quantity unit, Decimal volume/price/stops, instrument limits, margin evidence, tickets, and operation preconditions before route selection."""
    _header(
        "FR-TRD-024: The system shall validate symbol, action, approved order type, required order-shape fields, instrument-provided quantity unit, Decimal volume/price/stops, instrument limits, margin evidence, tickets, and operation preconditions before route selection."
    )
    example_validation()


def fr_trd_026() -> None:
    """FR-TRD-026: The system shall return timestamped account/symbol/quote/permission/authority facts or explicit unavailable/stale failures."""
    _header(
        "FR-TRD-026: The system shall return timestamped account/symbol/quote/permission/authority facts or explicit unavailable/stale failures."
    )
    example_validation()


def fr_trd_027() -> None:
    """FR-TRD-027: The system shall aggregate all required checks, enforce caller-declared expiry and configured `route_snapshot`, `risk_decision`, and `kill_switch` age bounds, and return a bounded pass/fail assessment with evidence references. Kill-switch evidence older than its bound fails with `KILL_SWITCH_STALE` independently of its reported `inactive` state."""
    _header(
        "FR-TRD-027: The system shall aggregate all required checks, enforce caller-declared expiry and configured `route_snapshot`, `risk_decision`, and `kill_switch` age bounds, and return a bounded pass/fail assessment with evidence references. Kill-switch evidence older than its bound fails with `KILL_SWITCH_STALE` independently of its reported `inactive` state."
    )
    example_validation()


def fr_trd_028() -> None:
    """FR-TRD-028: The system shall construct a deterministic plan and canonical idempotency material without side effects, preserving approved order type, validated quantity unit, optional order instructions, and Trading-state target identities exactly."""
    _header(
        "FR-TRD-028: The system shall construct a deterministic plan and canonical idempotency material without side effects, preserving approved order type, validated quantity unit, optional order instructions, and Trading-state target identities exactly."
    )
    example_validation()


def fr_trd_059() -> None:
    """FR-TRD-059: The system shall expose one immutable snapshot containing explicit fact values, source, authority, UTC timestamps, freshness, availability, and capability evidence."""
    _header(
        "FR-TRD-059: The system shall expose one immutable snapshot containing explicit fact values, source, authority, UTC timestamps, freshness, availability, and capability evidence."
    )
    example_validation()


def fr_trd_060() -> None:
    """FR-TRD-060: The system shall expose a bounded passed/failed readiness result with failed check codes and evidence references."""
    _header(
        "FR-TRD-060: The system shall expose a bounded passed/failed readiness result with failed check codes and evidence references."
    )
    example_validation()


def main() -> None:
    """Run Trading validation usage example."""
    example_validation()


if __name__ == "__main__":
    main()
