"""Unit tests for Risk Governance contracts serialization helpers."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.risk.models.contracts import ProposedTrade
from app.services.risk.models.serialization import (
    from_canonical_risk_payload,
    to_canonical_risk_payload,
    validate_risk_model_round_trip,
)


def test_to_canonical_risk_payload() -> None:
    """Test to_canonical_risk_payload conversion logic."""
    trade = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.5"),
        price=Decimal("1.0850"),
        timestamp=datetime(2026, 7, 8, 10, 0, 0, tzinfo=UTC),
    )
    payload = to_canonical_risk_payload(trade)
    assert isinstance(payload, dict)
    assert payload["volume"] == 1.5
    assert payload["price"] == 1.0850
    assert payload["timestamp"] == "2026-07-08T10:00:00+00:00"


def test_from_canonical_risk_payload() -> None:
    """Test restoring model from canonical payload."""
    payload = {
        "strategy_id": "strat-1",
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 1.5,
        "price": 1.0850,
        "timestamp": "2026-07-08T10:00:00+00:00",
    }
    trade = from_canonical_risk_payload(payload, ProposedTrade)
    assert isinstance(trade, ProposedTrade)
    assert trade.volume == Decimal("1.5")
    assert trade.price == Decimal("1.085")
    assert trade.timestamp == datetime(2026, 7, 8, 10, 0, 0, tzinfo=UTC)


def test_validate_risk_model_round_trip() -> None:
    """Test round-trip validation success and failure cases."""
    trade = ProposedTrade(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.5"),
        price=Decimal("1.0850"),
    )
    res = validate_risk_model_round_trip(trade)
    assert res["valid"] is True

    # Test error fallback by passing an incompatible model.
    # We can test round-trip on a custom mock class that doesn't validate properly.
    class BrokenContract(ProposedTrade):
        def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
            # Returns data that will fail validation upon loading
            return {"symbol": 12345}  # invalid type for symbol to trigger error

    broken = BrokenContract(
        strategy_id="strat-1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.5"),
    )
    res = validate_risk_model_round_trip(broken)
    assert res["valid"] is False
    assert "ROUND_TRIP_ERROR" in res["code"]
