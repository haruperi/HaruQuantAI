"""Unit tests for shadow-routing execution comparison primitives."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.execution.shadow import (
    ShadowIntentRecord,
    compare_shadow_fill,
    record_shadow_intent,
)
from app.services.trading.security.error_mapping import TradingMappedError


@pytest.mark.parametrize(
    "field_name",
    ["request_id", "symbol", "side", "recorded_at"],
)
def test_shadow_intent_record_rejects_blank_fields(field_name: str) -> None:
    """ShadowIntentRecord fails closed when any identifier field is blank."""
    fields: dict[str, object] = {
        "request_id": "req-1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": Decimal("0.10"),
        "expected_price": Decimal("1.10000"),
        "recorded_at": "2026-07-09T10:00:00Z",
    }
    fields[field_name] = " "
    with pytest.raises(ValueError, match="must be non-empty"):
        ShadowIntentRecord(**fields)  # type: ignore[arg-type]


def test_record_shadow_intent_defaults_payload_to_empty_dict() -> None:
    """record_shadow_intent defaults payload to an empty dict when omitted."""
    record = record_shadow_intent(
        request_id="req-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
        expected_price=Decimal("1.10000"),
        recorded_at="2026-07-09T10:00:00Z",
    )
    assert record.payload == {}


def test_compare_shadow_fill_rejects_non_positive_reference_price() -> None:
    """compare_shadow_fill rejects a non-positive live reference price."""
    intent = record_shadow_intent(
        request_id="req-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
        expected_price=Decimal("1.10000"),
        recorded_at="2026-07-09T10:00:00Z",
    )
    with pytest.raises(TradingMappedError):
        compare_shadow_fill(
            intent=intent,
            live_reference_price=Decimal(0),
            expected_balance_after=Decimal(10000),
            live_balance=Decimal(10000),
        )


def test_compare_shadow_fill_computes_price_and_balance_drift() -> None:
    """compare_shadow_fill computes signed price and balance drift."""
    intent = record_shadow_intent(
        request_id="req-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("0.10"),
        expected_price=Decimal("1.10000"),
        recorded_at="2026-07-09T10:00:00Z",
    )
    comparison = compare_shadow_fill(
        intent=intent,
        live_reference_price=Decimal("1.10110"),
        expected_balance_after=Decimal("10000.00"),
        live_balance=Decimal("9998.00"),
    )
    expected_drift = Decimal("1.10110") - Decimal("1.10000")
    assert comparison.price_drift == expected_drift
    assert comparison.price_drift_bps == (
        expected_drift / Decimal("1.10000")
    ) * Decimal(10_000)
    assert comparison.balance_drift == Decimal("-2.00")
