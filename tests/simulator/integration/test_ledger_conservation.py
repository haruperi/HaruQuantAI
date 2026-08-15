"""Integration evidence for cold transaction-ledger replay."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator import (
    build_transaction_posting,
    create_transaction_ledger,
    post_transaction,
    restore_transaction_ledger,
    serialize_transaction_ledger,
)


def test_cold_restore_is_byte_equivalent_and_conserved() -> None:
    """Every restored posting and total is identical to the source state."""
    ledger = create_transaction_ledger(Decimal(100), "USD")
    for sequence, (kind, amount) in enumerate(
        (("profit", Decimal(10)), ("commission", Decimal(-2)))
    ):
        post_transaction(
            ledger,
            build_transaction_posting(
                economic_at=datetime(2026, 8, 15, tzinfo=UTC),
                source_at=datetime(2026, 8, 15, tzinfo=UTC),
                account_currency="USD",
                amount=amount,
                kind=kind,
                source_sequence=sequence,
                evidence_reference=f"evidence-{sequence}",
            ),
        )
    first = serialize_transaction_ledger(ledger)
    second = serialize_transaction_ledger(restore_transaction_ledger(first))
    assert second == first
    assert second["balance"] == "108"
    assert second["conservation"] == "0"
