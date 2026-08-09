"""Standalone usage evidence for FEAT-UTIL-12."""

from datetime import UTC, datetime

from app.utils import build_reservation, derive_idempotency_key, evaluate_reservation


def main() -> None:
    """Run idempotency derivation and duplicate evaluation."""
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    key = derive_idempotency_key(owner="simulator:orders", intent={"order": "ord-demo"})
    reservation = build_reservation(key=key, reserved_at=instant, ttl_seconds=60)
    result = evaluate_reservation(
        key=key,
        owner="simulator:orders",
        prior_reservation=reservation,
        observed_at=instant,
    )
    print("SUCCESS: FEAT-UTIL-12 idempotency completed")
    print(f"Data -> reservation_verdict={result}")


if __name__ == "__main__":
    main()
