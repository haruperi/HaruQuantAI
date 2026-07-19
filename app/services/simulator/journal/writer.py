"""Hash-chained append and atomic finalization for Simulation journals."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from hashlib import sha256
from typing import TYPE_CHECKING

from app.services.simulator.errors import SimulationError
from app.services.simulator.journal.contracts import JournalEvent
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.simulator.state import SimulationStateStore

_GENESIS_HASH = "0" * 64

JOURNAL_FORMAT = "jsonl-v1"
JOURNAL_FSYNC_INTERVAL = 100
JOURNAL_SIDECAR_MODE = "disabled"


def _event_hash(material: Mapping[str, object]) -> str:
    """Hash canonical journal event material.

    Args:
        material: Event fields excluding ``event_hash``.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing canonical Simulation journal material")
    return sha256(canonical_json(material).encode("utf-8")).hexdigest()


class JournalWriter:
    """Per-run journal writer that owns sequence and hash continuity."""

    def __init__(
        self,
        store: SimulationStateStore,
        run_id: str,
        request_id: str,
        correlation_id: str,
    ) -> None:
        """Initialize an isolated writer.

        Args:
            store: Injected Simulation state store.
            run_id: Stable run identity.
            request_id: Stable request identity.
            correlation_id: Stable correlation identity.
        """
        logger.info("Initializing JournalWriter for run %s", run_id)
        self._store = store
        self._run_id = run_id
        self._request_id = request_id
        self._correlation_id = correlation_id
        self._sequence = 0
        self._tail_hash = _GENESIS_HASH
        self._unflushed = 0
        self._finalized = False

    def append(
        self,
        event_type: str,
        payload: Mapping[str, object],
        occurred_at: datetime,
        causation_id: str | None = None,
    ) -> JournalEvent:
        """Create and durably append the next canonical event.

        Args:
            event_type: Stable event classification.
            payload: Secret-safe event evidence.
            occurred_at: UTC occurrence time.
            causation_id: Optional predecessor identity.

        Returns:
            Immutable appended event.

        Raises:
            SimulationError: If the writer is finalized or persistence fails.
        """
        logger.info("Appending Simulation journal event %s", event_type)
        if self._finalized:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal is already finalized"
            )
        material: dict[str, object] = {
            "run_id": self._run_id,
            "sequence": self._sequence,
            "occurred_at": occurred_at,
            "event_type": event_type,
            "payload": dict(payload) | {"request_id": self._request_id},
            "previous_hash": self._tail_hash,
            "correlation_id": self._correlation_id,
            "causation_id": causation_id,
            "schema_version": "v1",
        }
        event = JournalEvent.model_validate(
            material | {"event_hash": _event_hash(material)}
        )
        canonical_event = canonical_json(
            event.model_dump(mode="python", warnings=False)
        )
        self._store.append_journal(self._run_id, canonical_event)
        self._sequence += 1
        self._tail_hash = event.event_hash
        self._unflushed += 1
        if self._unflushed >= JOURNAL_FSYNC_INTERVAL:
            self._flush()
        return event

    def _flush(self) -> None:
        """Force the injected store to make appended events durable.

        Group commit bounds the number of events that can be lost to at most
        ``JOURNAL_FSYNC_INTERVAL`` while keeping one synchronous write per
        batch rather than per event.

        Raises:
            SimulationError: If the store cannot make the batch durable.
        """
        logger.info("Flushing %d Simulation journal events", self._unflushed)
        self._store.flush_journal(self._run_id)
        self._unflushed = 0

    def finalize(self) -> str:
        """Atomically finalize the journal and return its checksum.

        Returns:
            Lowercase SHA-256 journal checksum.

        Raises:
            SimulationError: If empty, repeated, or persistence fails.
        """
        logger.info("Finalizing Simulation JournalWriter for %s", self._run_id)
        if self._finalized or self._sequence == 0:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Journal cannot be finalized"
            )
        if self._unflushed:
            self._flush()
        checksum = self._store.finalize_journal(
            self._run_id,
            self._sequence,
            self._tail_hash,
        )
        self._finalized = True
        return checksum


__all__ = [
    "JOURNAL_FORMAT",
    "JOURNAL_FSYNC_INTERVAL",
    "JOURNAL_SIDECAR_MODE",
    "JournalWriter",
]
