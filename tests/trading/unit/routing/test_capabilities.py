"""Unit tests for fail-closed Trading authority capability validation."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import OrderIntent, TradingError
from app.services.trading.routing.capabilities import (
    validate_adapter_capability as _validate_adapter_capability,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def validate_adapter_capability(
    intent: OrderIntent, capability: dict[str, object]
) -> None:
    """Validate capability with the explicit ratified runtime timeout."""
    _validate_adapter_capability(
        intent,
        capability,  # type: ignore[arg-type]
        operation_timeout_seconds=Decimal(10),
    )


def _intent() -> OrderIntent:
    """Build one complete paper-route executable intent."""
    return OrderIntent(
        client_order_id="client-order-001",
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        route="paper",
        provider_id="mt5",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        source_intent_id="intent-001",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lots",
        approved_volume=Decimal("1.00"),
        risk_approved_volume=Decimal("1.00"),
        idempotency_hash="a" * 64,
        canonical_material_version="v1",
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _capability() -> dict[str, object]:
    """Build complete approved adapter capability evidence."""
    return {
        "provider_id": "mt5",
        "contract_version": "v1",
        "schema_id": "brokers.adapter.v1",
        "provider_api_version": "5",
        "supported_actions": ["submit_order"],
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "security_profile": "approved",
        "operation_timeout_seconds": "10",
        "malformed_response_policy": "unknown_outcome",
        "rate_limit_policy": "provider_retry_after",
        "mutation_retry_policy": "reconcile_before_retry",
        "redaction_applied": True,
    }


def test_missing_security_contract_blocks() -> None:
    """Missing security or order-type evidence blocks adapter use."""
    capability = _capability()
    validate_adapter_capability(_intent(), capability)
    incompatible_values: tuple[tuple[str, object], ...] = (
        ("provider_id", "ctrader"),
        ("contract_version", "v2"),
        ("schema_id", "brokers.adapter.v2"),
        ("supported_actions", ["cancel_order"]),
        ("supported_order_types", ["LIMIT"]),
        ("security_profile", "unapproved"),
        ("operation_timeout_seconds", "11"),
        ("operation_timeout_seconds", 10.0),
        ("malformed_response_policy", "accept"),
        ("mutation_retry_policy", "blind_retry"),
        ("redaction_applied", False),
    )
    for field, value in incompatible_values:
        incompatible = _capability()
        incompatible[field] = value
        with pytest.raises(TradingError) as captured:
            validate_adapter_capability(_intent(), incompatible)
        assert captured.value.trading_code == "ADAPTER_INCOMPATIBLE"
    for missing_field in (
        "provider_api_version",
        "security_profile",
        "rate_limit_policy",
    ):
        incomplete = _capability()
        incomplete.pop(missing_field)
        with pytest.raises(TradingError) as captured:
            validate_adapter_capability(_intent(), incomplete)
        assert captured.value.trading_code == "ADAPTER_INCOMPATIBLE"
