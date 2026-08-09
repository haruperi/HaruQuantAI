"""Idempotent lifecycle-event ledger postings."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal


def build_lifecycle_postings(
    event_id: str, event_kind: str, amount: Decimal, currency: str
) -> Mapping[str, object]:
    """Build a balanced immutable posting batch for a lifecycle event.

    Returns:
        Idempotent balanced posting evidence.
    """
    return {
        "event_id": event_id,
        "event_kind": event_kind,
        "idempotency_key": f"lifecycle:{event_id}",
        "postings": (
            {"side": "debit", "amount": str(amount), "currency": currency},
            {"side": "credit", "amount": str(amount), "currency": currency},
        ),
    }
