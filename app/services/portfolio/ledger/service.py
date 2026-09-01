"""Ledger service coordinating ingestion, posting, and balance computation.

Implements the public service behavior for ``FEAT-PORT-09``. The service is a
deterministic, stateless coordinator: it receives economic events, emits
balanced posting batches, and computes reproducible account/cash balances.
Persistence is delegated through the Portfolio state store; this module owns
no database connection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from app.composition.logging import get_logger
from app.services.portfolio.ledger.balances import CashBalance, cash_balance
from app.services.portfolio.ledger.ingestion import ingest_event
from app.services.portfolio.ledger.postings import (
    build_reversal_batch,
    is_balanced,
    recompute_balances,
)
from app.services.portfolio.ledger.snapshots import (
    LedgerSnapshot,
    build_snapshot,
    validate_snapshot,
)

logger = get_logger(__name__)


class LedgerService:
    """Deterministic ledger coordinator over injected recorded state.

    The service holds no connection. It receives a read-only view of recorded
    ingestion keys (for exactly-once enforcement) and emits posting batches
    that the caller persists atomically.
    """

    def __init__(self) -> None:
        """Construct the stateless ledger coordinator."""
        logger.debug("Constructing LedgerService")

    def post_entries(
        self,
        *,
        source_event_id: str,
        source_sequence: int,
        entries: Sequence[Mapping[str, object]],
        posted_at: datetime,
        request_id: str,
        correlation_id: str,
        recorded_keys: Mapping[str, str],
        next_entry_sequence: int,
        reversal_of: str | None = None,
    ) -> dict[str, object]:
        """Ingest and emit one balanced posting batch.

        Args:
            source_event_id: External economic event identity.
            source_sequence: Exactly-once monotonic event sequence.
            entries: Ordered leg mappings.
            posted_at: UTC posting timestamp.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.
            recorded_keys: Recorded ``ingestion_key -> material_hash`` bindings.
            next_entry_sequence: Internal monotonically increasing entry index.
            reversal_of: Optional prior batch reversed by this correction.

        Returns:
            Posting batch mapping (empty when the event is an idempotent replay).

        Raises:
            ValueError: If the legs are unbalanced or the event conflicts.
        """
        logger.info("Posting ledger entries for event %s", source_event_id)
        if not is_balanced(entries):
            raise ValueError("ledger entries must balance to zero per currency")
        _key, batch = ingest_event(
            source_event_id=source_event_id,
            source_sequence=source_sequence,
            entries=entries,
            posted_at=posted_at,
            request_id=request_id,
            correlation_id=correlation_id,
            existing_keys=recorded_keys,
            next_entry_sequence=next_entry_sequence,
            reversal_of=reversal_of,
        )
        return batch

    def reverse_batch(
        self,
        *,
        original: Mapping[str, object],
        source_event_id: str,
        source_sequence: int,
        entry_sequence: int,
        posted_at: datetime,
        request_id: str,
        correlation_id: str,
    ) -> dict[str, object]:
        """Emit an append-only reversal (correction) batch.

        Args:
            original: Original batch mapping to reverse.
            source_event_id: External economic event identity.
            source_sequence: Exactly-once monotonic event sequence.
            entry_sequence: Internal monotonically increasing entry index.
            posted_at: UTC posting timestamp.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.

        Returns:
            Reversal ``PostingBatch v1`` mapping.
        """
        logger.info("Reversing ledger batch %s", original.get("batch_id", "?"))
        return build_reversal_batch(
            original=original,
            batch_id=f"reversal-{source_event_id}-{source_sequence}",
            source_event_id=source_event_id,
            source_sequence=source_sequence,
            entry_sequence=entry_sequence,
            posted_at=posted_at,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def account_cash(
        self,
        entries: Sequence[Mapping[str, object]],
        account_id: str,
        currency: str,
    ) -> CashBalance:
        """Return the reproducible cash balance for one account/currency.

        Args:
            entries: Ordered leg mappings.
            account_id: Account to compute for.
            currency: Cash currency.

        Returns:
            Frozen cash-balance view.
        """
        return cash_balance(entries, account_id, currency)

    def all_balances(
        self, entries: Sequence[Mapping[str, object]]
    ) -> dict[tuple[str, str], Decimal]:
        """Rebuild every account/currency signed balance.

        Args:
            entries: Ordered leg mappings.

        Returns:
            Mapping of ``(account_id, currency)`` to signed balance.
        """
        return recompute_balances(entries)

    def snapshot(
        self,
        *,
        snapshot_id: str,
        entries: Sequence[Mapping[str, object]],
        entry_range_start: int,
        entry_range_end: int,
    ) -> LedgerSnapshot:
        """Build a rebuild-validated snapshot accelerator.

        Args:
            snapshot_id: Snapshot identity.
            entries: Ordered leg mappings in the bounded range.
            entry_range_start: Inclusive lower entry-sequence bound.
            entry_range_end: Inclusive upper entry-sequence bound.

        Returns:
            Frozen snapshot.
        """
        return build_snapshot(
            snapshot_id=snapshot_id,
            entries=entries,
            entry_range_start=entry_range_start,
            entry_range_end=entry_range_end,
        )

    def verify_snapshot(
        self, snapshot: LedgerSnapshot, entries: Sequence[Mapping[str, object]]
    ) -> bool:
        """Return whether a snapshot agrees with a rebuild.

        Args:
            snapshot: Candidate snapshot.
            entries: Ordered leg mappings in the snapshot's bounded range.

        Returns:
            ``True`` if the snapshot matches the rebuild.
        """
        return validate_snapshot(snapshot, entries)


def create_ledger_service() -> LedgerService:
    """Return a ``LedgerService`` coordinator.

    Returns:
        New ledger coordinator handle.
    """
    logger.debug("Creating ledger service handle")
    return LedgerService()


__all__: tuple[str, ...] = (
    "LedgerService",
    "create_ledger_service",
)
