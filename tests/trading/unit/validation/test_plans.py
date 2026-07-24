"""Unit tests for deterministic Trading execution plans."""

# ruff: noqa: INP001
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.validation import ReadinessAssessment, build_execution_plan

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def test_plan_is_deterministic() -> None:
    """Identical validated material produces identical canonical intent."""
    request = TradingRequest(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        action="submit_order",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity=Decimal("1.00"),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    readiness = ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "risk-001"},
        assessed_at=NOW,
    )
    first = build_execution_plan(request, readiness)
    second = build_execution_plan(request, readiness)
    assert first == second
    assert first.approved_volume == first.risk_approved_volume
    assert first.order_type == request.order_type
    assert first.quantity_unit == request.quantity_unit
    blocked = readiness.model_copy(
        update={"passed": False, "failed_check_codes": ("BLOCKED",)}
    )
    with pytest.raises(TradingError) as blocked_error:
        build_execution_plan(request, blocked)
    assert blocked_error.value.trading_code == "GATE_BLOCKED"
    missing = request.model_copy(update={"quantity": None})
    with pytest.raises(TradingError) as invalid_error:
        build_execution_plan(missing, readiness)
    assert invalid_error.value.trading_code == "INVALID_REQUEST"
