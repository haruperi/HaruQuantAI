"""Exactly-once ledger economic-event ingestion.

Implements ``feature``. The ledger consumes Trading/Broker/Simulator
economic events exactly once using the ``(source_event_id, source_sequence)``
invariant: a replayed event with identical material is idempotent, and a
replayed key carrying changed material is rejected (``PORT_IDEMPOTENCY_CONFLICT``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.portfolio.ledger.contracts import build_posting_batch

logger = get_logger(__name__)


def event_identity(source_event_id: str, source_sequence: int) -> str:
    """Return the stable exactly-once ingestion key for one event.

    Args:
        source_event_id: External economic event identity.
        source_sequence: Monotonic per-event sequence.

    Returns:
        Deterministic ingestion key.
    """
    return canonical_digest(
        {"source_event_id": source_event_id, "source_sequence": source_sequence}
    )


def material_hash(material: Mapping[str, object]) -> str:
    """Return a canonical digest of one event's posting material.

    Args:
        material: Event posting material.

    Returns:
        Lowercase SHA-256 digest.
    """
    return canonical_digest(dict(material))


def ingest_event(
    *,
    source_event_id: str,
    source_sequence: int,
    entries: Sequence[Mapping[str, object]],
    posted_at: datetime,
    request_id: str,
    correlation_id: str,
    existing_keys: Mapping[str, str],
    next_entry_sequence: int,
    reversal_of: str | None = None,
) -> tuple[str, dict[str, object]]:
    """Ingest one economic event exactly once and emit a posting batch.

    Fail-closed semantics: if the event key is already recorded with identical
    material, the ingestion is idempotent (no new batch); if the key is
    recorded with different material, ingestion is rejected.

    Args:
        source_event_id: External economic event identity.
        source_sequence: Exactly-once monotonic event sequence.
        entries: Ordered leg mappings.
        posted_at: UTC posting timestamp.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.
        existing_keys: Recorded ``ingestion_key -> material_hash`` bindings.
        next_entry_sequence: Internal monotonically increasing entry index.
        reversal_of: Optional prior batch reversed by this correction batch.

    Returns:
        Tuple of ``(ingestion_key, posting_batch_mapping)``.

    Raises:
        ValueError: If the event conflicts with recorded material.
    """
    logger.info(
        "Ingesting ledger event %s sequence %s", source_event_id, source_sequence
    )
    key = event_identity(source_event_id, source_sequence)
    leg_material = [
        {
            "account_id": str(leg.get("account_id", "")),
            "side": str(leg.get("side", "")),
            "amount": str(leg.get("amount", "0")),
            "currency": str(leg.get("currency", "")),
            "posting_type": str(leg.get("posting_type", "")),
        }
        for leg in entries
    ]
    digest = material_hash(
        {
            "entries": leg_material,
            "reversal_of": reversal_of,
        }
    )
    recorded = existing_keys.get(key)
    if recorded is not None:
        if recorded != digest:
            logger.error("Ledger event conflicts with recorded material")
            raise ValueError("ledger event material conflicts")
        logger.info("Ledger event already recorded; idempotent no-op")
        return key, {}
    batch_id = f"batch-{key[:24]}"
    canonical = canonical_digest(
        {
            "batch_id": batch_id,
            "source_event_id": source_event_id,
            "source_sequence": source_sequence,
            "entry_sequence": next_entry_sequence,
            "entries": leg_material,
            "posted_at": str(posted_at),
            "reversal_of": reversal_of,
        }
    )
    batch = build_posting_batch(
        batch_id=batch_id,
        source_event_id=source_event_id,
        source_sequence=source_sequence,
        entry_sequence=next_entry_sequence,
        entries=entries,
        posted_at=posted_at,
        canonical_hash=canonical,
        request_id=request_id,
        correlation_id=correlation_id,
        reversal_of=reversal_of,
    )
    return key, batch


def detect_sequence_gap(sequences: Sequence[int]) -> int | None:
    """Return the first missing positive integer in an ordered sequence.

    Used to surface a gap in a source-event stream rather than silently
    accepting a discontinuous sequence.

    Args:
        sequences: Ordered recorded sequences for one source event.

    Returns:
        The first missing sequence number, or ``None`` if contiguous.
    """
    if not sequences:
        return None
    ordered = sorted(sequences)
    expected = 1
    for value in ordered:
        if value > expected:
            return expected
        if value == expected:
            expected += 1
    return None


__all__: tuple[str, ...] = (
    "detect_sequence_gap",
    "event_identity",
    "ingest_event",
    "material_hash",
)
