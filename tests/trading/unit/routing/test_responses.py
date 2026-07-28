"""Unit tests for conservative Trading authority response classification."""

# ruff: noqa: INP001
from datetime import UTC, datetime

from app.services.trading.routing.responses import classify_authority_response

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
POLICY = {
    "malformed_response_policy": "unknown_outcome",
    "mutation_retry_policy": "reconcile_before_retry",
}


def _raw() -> dict[str, object]:
    """Build representable response trace material."""
    return {
        "receipt_id": "receipt-001",
        "intent_id": "intent-001",
        "client_order_id": "client-order-001",
        "route": "paper",
        "authority": "mt5",
        "status": "success",
        "requested_quantity": "1.00",
        "filled_quantity": "0",
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "authority_timestamp": NOW.isoformat(),
        "received_at": NOW.isoformat(),
    }


def test_malformed_success_is_unknown_outcome() -> None:
    """Success without authority identity cannot become acceptance."""
    receipt = classify_authority_response(  # type: ignore[arg-type]
        _raw(),
        POLICY,  # type: ignore[arg-type]
    )
    assert receipt.status == "success"
    assert receipt.data is not None
    classified_receipt = receipt.data
    assert classified_receipt.status == "unknown_outcome"
    assert classified_receipt.reconciliation_required
    assert not classified_receipt.retry_safe
    rate_limited = _raw()
    rate_limited.update({"rate_limited": True, "status": "rejected"})
    limited_receipt = classify_authority_response(  # type: ignore[arg-type]
        rate_limited,
        POLICY,  # type: ignore[arg-type]
    )
    assert limited_receipt.data is not None
    assert limited_receipt.data.response_classification == "rate_limited"
    classified_cases = (
        ("accepted", "0", "broker-order-001", "accepted"),
        ("partial", "0.50", "broker-order-001", "partial"),
        ("filled", "1.00", "broker-order-001", "filled"),
        ("rejected", "0", None, "rejected"),
        ("unknown_outcome", "0", None, "unknown_outcome"),
        ("unexpected", "0", None, "unknown_outcome"),
    )
    for status, filled, order_id, expected in classified_cases:
        response = _raw()
        response.update(
            {
                "status": status,
                "filled_quantity": filled,
                "provider_order_id": order_id,
            }
        )
        classified = classify_authority_response(  # type: ignore[arg-type]
            response,
            POLICY,  # type: ignore[arg-type]
        )
        assert classified.status == "success"
        assert classified.data is not None
        assert classified.data.status == expected
    timed_out = _raw()
    timed_out["timed_out"] = True
    assert (
        classify_authority_response(  # type: ignore[arg-type]
            timed_out,
            POLICY,  # type: ignore[arg-type]
        ).data.response_classification  # type: ignore[union-attr]
        == "timeout"
    )
    ambiguous = _raw()
    ambiguous["ambiguous"] = True
    assert (
        classify_authority_response(  # type: ignore[arg-type]
            ambiguous,
            POLICY,  # type: ignore[arg-type]
        ).data.response_classification  # type: ignore[union-attr]
        == "ambiguous"
    )
