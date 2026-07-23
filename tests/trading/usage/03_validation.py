"""Executable Trading validation usage example.

Demonstrates order validation and execution readiness.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.account_contracts import (
    AccountStateSnapshot,
)
from app.services.risk import KillSwitchState, RiskDecisionPackage
from app.services.risk.contracts import DecisionState
from app.services.trading.contracts import TradingRequest
from app.services.trading.validation import (
    ReadinessAssessment,
    RouteSnapshot,
    assess_execution_readiness,
    build_execution_plan,
    get_route_snapshot,
    validate_order_request,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _request() -> TradingRequest:
    """Build complete validated order material."""
    return TradingRequest(
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
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


def _account() -> AccountStateSnapshot:
    """Build current Data-owned account evidence."""
    return AccountStateSnapshot(
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
    return RiskDecisionPackage(
        decision_id="usage-risk-001",
        intent_id="usage-intent-001",
        state=DecisionState.APPROVE,
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
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
    )


def _switch() -> KillSwitchState:
    """Build inactive real Risk kill-switch state."""
    return KillSwitchState(
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
    print("=" * 80)
    print("Trading Example 3: Order Validation and Execution Readiness")
    print("=" * 80)

    req = _request()

    # 1. Validate order request
    validated = validate_order_request(req, _account(), _symbol_capability())
    print(f"Validated order request quantity: {validated.quantity}")

    # 2. Get route snapshot
    def source(_route: object, _provider: object) -> dict[str, object]:
        return _snapshot().model_dump(mode="python")

    route_snap = get_route_snapshot(req, source)  # type: ignore[arg-type]
    print(f"Route snapshot available: {route_snap.available}")

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
    print(f"Execution readiness passed: {assessment.passed}")

    # 4. Build execution plan
    readiness = ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "usage-risk-001"},
        assessed_at=NOW,
    )
    plan = build_execution_plan(req, readiness)
    print(f"Built execution plan route: {plan.route.value}")


def main() -> None:
    """Run Trading validation usage example."""
    example_validation()


if __name__ == "__main__":
    main()
