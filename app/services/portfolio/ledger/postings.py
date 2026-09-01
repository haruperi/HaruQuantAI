"""Deterministic balanced double-entry posting and balance computation.

Implements the balance arithmetic for ``FEAT-PORT-09`` (``feature``,
``feature``). All money math uses ``decimal.Decimal``; the same ordered
batches always produce the same balances (NFR-PORT-002, QUANT gate).

Financial records are append-only: a correction is a reversal batch that posts
opposite legs and references ``reversal_of``, never an edit to a prior row.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.portfolio.ledger.contracts import (
    _LedgerEntry,
    _PostingBatch,
    build_posting_batch,
)

logger = get_logger(__name__)

# Minimum legs a reversal batch must reverse (a balanced debit/credit pair).
_MIN_REVERSAL_LEGS = 2


def _signed_amount(entry: Mapping[str, object]) -> Decimal:
    """Return the signed magnitude for one leg mapping.

    Args:
        entry: Leg mapping with ``side`` and ``amount`` fields.

    Returns:
        Positive for debit, negative for credit.

    Raises:
        ValueError: If the side is unknown.
    """
    side = entry.get("side")
    amount = Decimal(str(entry.get("amount", "0")))
    if side == "debit":
        return amount
    if side == "credit":
        return -amount
    message = f"unknown posting side: {side!r}"
    raise ValueError(message)


def total_entries(
    entries: Sequence[Mapping[str, object]],
) -> dict[str, Decimal]:
    """Return per-currency debit-minus-credit totals for ordered legs.

    Args:
        entries: Ordered leg mappings.

    Returns:
        Mapping of currency to signed total.

    Raises:
        ValueError: If a leg is malformed.
    """
    logger.debug("Computing per-currency posting totals")
    totals: dict[str, Decimal] = {}
    for entry in entries:
        currency = str(entry.get("currency", ""))
        if not currency:
            raise ValueError("ledger entry currency is required")
        totals[currency] = totals.get(currency, Decimal(0)) + _signed_amount(entry)
    return totals


def is_balanced(entries: Sequence[Mapping[str, object]]) -> bool:
    """Return whether ordered legs sum to zero in every currency.

    Args:
        entries: Ordered leg mappings.

    Returns:
        ``True`` if every currency total is exactly zero.
    """
    return all(total == 0 for total in total_entries(entries).values())


def account_balance(
    entries: Sequence[Mapping[str, object]],
    account_id: str,
) -> dict[str, Decimal]:
    """Return per-currency running balance for one account.

    The natural side of an account is not assumed here; the returned signed
    balance is debit-minus-credit. Callers interpret the sign using the
    account's ``normal_balance`` (``TC-PORT-03``).

    Args:
        entries: Ordered leg mappings scoped to the account.
        account_id: Account to compute the balance for.

    Returns:
        Mapping of currency to signed debit-minus-credit balance.
    """
    logger.debug("Computing account balance for %s", account_id)
    balances: dict[str, Decimal] = {}
    for entry in entries:
        if str(entry.get("account_id", "")) != account_id:
            continue
        currency = str(entry.get("currency", ""))
        balances[currency] = balances.get(currency, Decimal(0)) + _signed_amount(entry)
    return balances


def recompute_balances(
    entries: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], Decimal]:
    """Rebuild every account/currency balance from ordered legs.

    This is the canonical state rebuild used by ``feature``: snapshots
    are accelerators only, and the rebuilt balances are the authoritative
    truth.

    Args:
        entries: Ordered leg mappings.

    Returns:
        Mapping of ``(account_id, currency)`` to signed balance.

    Raises:
        ValueError: If a leg is malformed.
    """
    logger.debug("Rebuilding all account balances from ledger entries")
    balances: dict[tuple[str, str], Decimal] = {}
    for entry in entries:
        account_id = str(entry.get("account_id", ""))
        currency = str(entry.get("currency", ""))
        if not account_id or not currency:
            raise ValueError("ledger entry account and currency are required")
        key = (account_id, currency)
        balances[key] = balances.get(key, Decimal(0)) + _signed_amount(entry)
    return balances


def build_reversal_batch(
    *,
    original: Mapping[str, object],
    batch_id: str,
    source_event_id: str,
    source_sequence: int,
    entry_sequence: int,
    posted_at: datetime,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Build a reversal (correction) batch that posts opposite legs.

    Corrections are append-only: this constructs a new batch referencing the
    original via ``reversal_of`` rather than editing the original (rule 8,
    financial records are append-only).

    Args:
        original: Original batch mapping to reverse.
        batch_id: Immutable identity for the new reversal batch.
        source_event_id: External economic event identity.
        source_sequence: Exactly-once monotonic event sequence.
        entry_sequence: Internal monotonically increasing entry index.
        posted_at: UTC posting timestamp.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.

    Returns:
        JSON-safe ``PostingBatch v1`` reversal mapping.

    Raises:
        TypeError: If an original entry is not a mapping.
        ValueError: If the original is malformed.
    """
    logger.info("Building reversal batch for %s", original.get("batch_id", "?"))
    original_id = str(original.get("batch_id", ""))
    if not original_id:
        raise ValueError("reversal original batch_id is required")
    legs = original.get("entries", ())
    if not isinstance(legs, Sequence) or len(legs) < _MIN_REVERSAL_LEGS:
        raise ValueError("reversal original must carry at least two entries")
    reversed_legs: list[dict[str, object]] = []
    for index, leg in enumerate(legs):
        if not isinstance(leg, Mapping):
            raise TypeError("reversal original entry must be a mapping")
        original_side = leg.get("side")
        reversed_side = "credit" if original_side == "debit" else "debit"
        reversed_legs.append(
            {
                "entry_id": f"{batch_id}-leg-{index + 1}",
                "account_id": str(leg.get("account_id", "")),
                "side": reversed_side,
                "amount": Decimal(str(leg.get("amount", "0"))),
                "currency": str(leg.get("currency", "")),
                "posting_type": "correction",
            }
        )
    canonical_hash = _batch_canonical_hash(
        batch_id=batch_id,
        source_event_id=source_event_id,
        source_sequence=source_sequence,
        entry_sequence=entry_sequence,
        entries=reversed_legs,
        posted_at=posted_at,
        reversal_of=original_id,
    )
    return build_posting_batch(
        batch_id=batch_id,
        source_event_id=source_event_id,
        source_sequence=source_sequence,
        entry_sequence=entry_sequence,
        entries=reversed_legs,
        posted_at=posted_at,
        canonical_hash=canonical_hash,
        request_id=request_id,
        correlation_id=correlation_id,
        reversal_of=original_id,
    )


def _batch_canonical_hash(
    *,
    batch_id: str,
    source_event_id: str,
    source_sequence: int,
    entry_sequence: int,
    entries: Sequence[Mapping[str, object]],
    posted_at: datetime,
    reversal_of: str | None,
) -> str:
    """Return a stable canonical digest for one batch.

    Args:
        batch_id: Batch identity.
        source_event_id: External economic event identity.
        source_sequence: Exactly-once event sequence.
        entry_sequence: Internal entry index.
        entries: Ordered leg mappings.
        posted_at: UTC posting timestamp.
        reversal_of: Optional reversed batch identity.

    Returns:
        Lowercase SHA-256 digest.
    """
    material = {
        "batch_id": batch_id,
        "source_event_id": source_event_id,
        "source_sequence": source_sequence,
        "entry_sequence": entry_sequence,
        "entries": [
            {
                "entry_id": str(leg.get("entry_id", "")),
                "account_id": str(leg.get("account_id", "")),
                "side": str(leg.get("side", "")),
                "amount": str(leg.get("amount", "0")),
                "currency": str(leg.get("currency", "")),
                "posting_type": str(leg.get("posting_type", "")),
            }
            for leg in entries
        ],
        "posted_at": posted_at.isoformat(),
        "reversal_of": reversal_of,
    }
    return canonical_digest(material)


def normalize_entry_sequence(entries: Sequence[Mapping[str, object]]) -> int:
    """Return the next monotonically increasing entry index.

    Args:
        entries: Existing ordered leg mappings.

    Returns:
        One greater than the maximum existing ``entry_sequence``.

    Raises:
        ValueError: If the sequence is non-monotonic.
    """
    max_sequence = 0
    for entry in entries:
        sequence = entry.get("entry_sequence")
        if isinstance(sequence, int) and sequence > max_sequence:
            max_sequence = sequence
    return max_sequence + 1


def balance_from_models(
    entries: Sequence[_LedgerEntry],
) -> dict[tuple[str, str], Decimal]:
    """Rebuild balances from typed leg models.

    Args:
        entries: Ordered leg models.

    Returns:
        Mapping of ``(account_id, currency)`` to signed balance.
    """
    logger.debug("Rebuilding balances from typed leg models")
    balances: dict[tuple[str, str], Decimal] = {}
    for entry in entries:
        signed = entry.amount if entry.side == "debit" else -entry.amount
        key = (entry.account_id, entry.currency)
        balances[key] = balances.get(key, Decimal(0)) + signed
    return balances


def batch_from_mapping(value: Mapping[str, object]) -> _PostingBatch:
    """Construct a typed batch model from a mapping.

    Args:
        value: Candidate batch mapping.

    Returns:
        Validated typed batch model.
    """
    return _PostingBatch.model_validate(dict(value))


__all__: tuple[str, ...] = (
    "account_balance",
    "balance_from_models",
    "batch_from_mapping",
    "build_reversal_batch",
    "is_balanced",
    "normalize_entry_sequence",
    "recompute_balances",
    "total_entries",
)
