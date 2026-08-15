"""Integration evidence that Trading producers preserve order-policy v2."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading import (
    build_execution_plan,
    create_readiness_assessment,
    create_trading_request_v2,
)

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def test_fr_trd_112_execution_plan_preserves_v2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-TRD-112: the plan producer emits v2 with exact independent policies."""

    def get_field(_snapshot: object, field: str) -> object:
        return {
            "filling_modes": ("IOC",),
            "expiration_modes": ("SPECIFIED_DAY",),
            "checksum": "c" * 64,
        }[field]

    monkeypatch.setattr(
        "app.services.brokers.get_provider_specification_snapshot_field", get_field
    )
    request = create_trading_request_v2(
        provider_specification=object(),
        fill_policy="IOC",
        time_policy="SPECIFIED_DAY",
        expiration=NOW + timedelta(days=1),
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
        quantity=Decimal(1),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="key-001",
        canonical_material_version="v2",
        system_time=NOW,
        valid_until=NOW + timedelta(days=2),
    )
    readiness = create_readiness_assessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"risk_decision_id": "risk-001"},
        assessed_at=NOW,
    )
    response = build_execution_plan(request, readiness)
    assert response.status == "success"
    assert response.data.contract_version == "v2"
    assert (response.data.fill_policy, response.data.time_policy) == (
        "IOC",
        "SPECIFIED_DAY",
    )
    assert response.data.provider_specification_checksum == "c" * 64
