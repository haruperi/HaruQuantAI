"""Integration evidence for swap accrual into the signed transaction ledger."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator import (
    build_transaction_posting,
    calculate_rollover_swap,
    create_transaction_ledger,
    post_transaction,
)


def test_rollover_accrual_posts_exact_signed_swap() -> None:
    """Accrued swap becomes one evidenced conserved transaction."""
    rollover = datetime(2026, 8, 12, tzinfo=UTC)
    result = calculate_rollover_swap(
        rollover_at=rollover,
        server_timezone="UTC",
        side="LONG",
        volume=Decimal(1),
        rate=Decimal(-2),
        weekday_ratios={day: Decimal(3 if day == 2 else 1) for day in range(7)},
        unit="ACCOUNT_CURRENCY",
        point_value=None,
        fx_rate=None,
        posting_mode="ACCRUAL_ONLY",
        position_id="position-1",
    )
    ledger = create_transaction_ledger(Decimal(100), "USD")
    posting = build_transaction_posting(
        economic_at=rollover,
        source_at=rollover,
        account_currency="USD",
        amount=Decimal(str(result["accrued_amount"])),
        kind="swap",
        source_sequence=0,
        evidence_reference="provider-specification-revision",
        causal_position_id="position-1",
    )
    snapshot = post_transaction(ledger, posting)
    assert snapshot["balance"] == "94"
    assert snapshot["conservation"] == "0"
