"""Unit tests for idempotency primitives."""

from datetime import UTC, datetime

from app.utils import build_reservation, derive_idempotency_key, evaluate_reservation


def test_in_flight_duplicate_is_distinct_from_completed() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    key = derive_idempotency_key(owner="trading:orders", intent={"order": "ord-1"})
    reservation = build_reservation(key=key, reserved_at=now, ttl_seconds=30)
    verdict = evaluate_reservation(
        key=key, owner="trading:orders", prior_reservation=reservation, observed_at=now
    )
    assert verdict == {
        "verdict": "DUPLICATE_IN_FLIGHT",
        "prior_result": None,
        "may_apply_effect": False,
    }
