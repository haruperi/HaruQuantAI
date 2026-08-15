"""Unit evidence for signed conserved transaction postings."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator import (
    build_transaction_posting,
    create_transaction_ledger,
    post_transaction,
    restore_transaction_ledger,
    serialize_transaction_ledger,
)
from pydantic import ValidationError

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _posting(kind: str, amount: Decimal, sequence: int) -> object:
    """Build one posting fixture."""
    return build_transaction_posting(
        economic_at=NOW,
        source_at=NOW,
        account_currency="USD",
        amount=amount,
        kind=kind,
        source_sequence=sequence,
        evidence_reference=f"evidence-{sequence}",
    )


@pytest.mark.parametrize(
    ("kind", "amount"),
    [
        ("profit", Decimal(10)),
        ("commission", Decimal(-1)),
        ("fees", Decimal(-1)),
        ("swap", Decimal(-1)),
        ("tax", Decimal(-1)),
        ("rebates", Decimal(1)),
        ("deposit", Decimal(10)),
        ("withdrawal", Decimal(-10)),
        ("credit", Decimal(10)),
        ("correction", Decimal(-1)),
    ],
)
def test_fr_sim_179_240_every_transaction_is_signed_and_conserved(
    kind: str, amount: Decimal
) -> None:
    """FR-SIM-179/240: every named type preserves sign and conservation."""
    ledger = create_transaction_ledger(Decimal(100), "USD")
    snapshot = post_transaction(ledger, _posting(kind, amount, 0))
    assert snapshot["conservation"] == "0"
    assert snapshot["balance"] == str(Decimal(100) + amount)


def test_fr_sim_180_missing_or_invalid_evidence_fails_closed() -> None:
    """FR-SIM-180: costs cannot exist without explicit evidence."""
    with pytest.raises(ValidationError, match="evidence"):
        build_transaction_posting(
            economic_at=NOW,
            source_at=NOW,
            account_currency="USD",
            amount=Decimal(-1),
            kind="commission",
            source_sequence=0,
            evidence_reference="",
        )


def test_duplicate_sequence_currency_and_restore_are_guarded() -> None:
    """Ledger admission is atomic and restore is byte-equivalent."""
    ledger = create_transaction_ledger(Decimal(100), "USD")
    posting = _posting("profit", Decimal(5), 0)
    post_transaction(ledger, posting)
    with pytest.raises(ValueError, match="duplicate"):
        post_transaction(ledger, posting)
    wrong_currency = build_transaction_posting(
        economic_at=NOW,
        source_at=NOW,
        account_currency="EUR",
        amount=Decimal(1),
        kind="profit",
        source_sequence=1,
        evidence_reference="evidence-eur",
    )
    with pytest.raises(ValueError, match="currency"):
        post_transaction(ledger, wrong_currency)
    state = serialize_transaction_ledger(ledger)
    assert serialize_transaction_ledger(restore_transaction_ledger(state)) == state
