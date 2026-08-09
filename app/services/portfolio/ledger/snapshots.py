"""Ledger snapshots as rebuild accelerators, never alternative truth.

Implements ``TC-IMP-PORT-15``. A snapshot records a materialized balance view
over a bounded entry range and must always agree with a rebuild from the raw
entries. If a snapshot disagrees, the rebuild wins and the snapshot is treated
as stale; the ledger never substitutes a snapshot for canonical entry truth.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.services.portfolio.ledger.postings import recompute_balances
from app.utils import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LedgerSnapshot:
    """Materialized balance accelerator over a bounded entry range.

    Attributes:
        snapshot_id: Snapshot identity.
        account_ids: Accounts covered.
        entry_range_start: Inclusive lower entry-sequence bound.
        entry_range_end: Inclusive upper entry-sequence bound.
        balances: Mapping of ``(account_id, currency)`` to signed balance.
        material_hash: Stable digest of the snapshot material.
    """

    snapshot_id: str
    account_ids: tuple[str, ...]
    entry_range_start: int
    entry_range_end: int
    balances: Mapping[tuple[str, str], Decimal]
    material_hash: str


def build_snapshot(
    *,
    snapshot_id: str,
    entries: Sequence[Mapping[str, object]],
    entry_range_start: int,
    entry_range_end: int,
) -> LedgerSnapshot:
    """Build a validated snapshot over a bounded entry range.

    Args:
        snapshot_id: Snapshot identity.
        entries: Ordered leg mappings in the bounded range.
        entry_range_start: Inclusive lower entry-sequence bound.
        entry_range_end: Inclusive upper entry-sequence bound.

    Returns:
        Frozen snapshot.

    Raises:
        ValueError: If the entry range is non-positive or unordered.
    """
    logger.info("Building ledger snapshot %s", snapshot_id)
    if entry_range_start <= 0 or entry_range_end < entry_range_start:
        raise ValueError("snapshot entry range must be positive and ordered")
    balances = recompute_balances(entries)
    account_ids = tuple(sorted({account for account, _ in balances}))
    material_hash = _snapshot_hash(
        snapshot_id=snapshot_id,
        entry_range_start=entry_range_start,
        entry_range_end=entry_range_end,
        balances=balances,
    )
    return LedgerSnapshot(
        snapshot_id=snapshot_id,
        account_ids=account_ids,
        entry_range_start=entry_range_start,
        entry_range_end=entry_range_end,
        balances=balances,
        material_hash=material_hash,
    )


def validate_snapshot(
    snapshot: LedgerSnapshot, entries: Sequence[Mapping[str, object]]
) -> bool:
    """Return whether a snapshot agrees with a rebuild from raw entries.

    The rebuild is authoritative; a snapshot that disagrees is stale and must
    not be used as truth.

    Args:
        snapshot: Candidate snapshot.
        entries: Ordered leg mappings in the snapshot's bounded range.

    Returns:
        ``True`` if the snapshot balances match the rebuild.
    """
    logger.debug("Validating ledger snapshot %s", snapshot.snapshot_id)
    rebuilt = recompute_balances(entries)
    return snapshot.balances == rebuilt


def _snapshot_hash(
    *,
    snapshot_id: str,
    entry_range_start: int,
    entry_range_end: int,
    balances: Mapping[tuple[str, str], Decimal],
) -> str:
    """Return a stable digest of snapshot material.

    Args:
        snapshot_id: Snapshot identity.
        entry_range_start: Inclusive lower entry-sequence bound.
        entry_range_end: Inclusive upper entry-sequence bound.
        balances: Snapshot balances.

    Returns:
        Lowercase SHA-256 digest.
    """
    from app.utils import canonical_digest

    material = {
        "snapshot_id": snapshot_id,
        "entry_range_start": entry_range_start,
        "entry_range_end": entry_range_end,
        "balances": {
            f"{account}|{currency}": str(amount)
            for (account, currency), amount in sorted(balances.items())
        },
    }
    return canonical_digest(material)


__all__: tuple[str, ...] = (
    "LedgerSnapshot",
    "build_snapshot",
    "validate_snapshot",
)
