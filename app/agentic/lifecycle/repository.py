"""Lifecycle-ledger persistence port and its deterministic in-memory double.

Agentic declares the port; a composition root binds the durable implementation
Data owns. Following the Portfolio and Risk precedents, no domain outside Data
implements a database writer, so this module holds a Protocol and an in-memory
double only.

`append_record` is the enforcement point for `FR-AGENTIC-054`. It accepts a
record only at the next free position for that artefact digest and refuses a
position already written, which is what makes the history append-only rather
than merely conventionally so. The durable table backs the same rule with a
composite primary key, so the property survives a restart.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.utils import get_logger

if TYPE_CHECKING:
    from app.agentic.lifecycle.models import (
        ArtifactState,
        LifecycleRecord,
        PromotionEvidencePacket,
    )

logger = get_logger(__name__)


@runtime_checkable
class AgenticLifecycleStore(Protocol):
    """Durable append-only ledger of artefact transitions and packets."""

    def append_record(self, record: LifecycleRecord) -> LifecycleRecord:
        """Append one transition at the next free position.

        Args:
            record: Validated immutable transition record.

        Returns:
            The persisted record.

        Raises:
            ValueError: If the position is already written or out of order.
        """
        ...

    def list_records(self, artifact_hash: str) -> tuple[LifecycleRecord, ...]:
        """List one artefact's complete history, oldest first.

        Args:
            artifact_hash: Digest of the exact artefact.

        Returns:
            Ordered transition records, empty when unrecorded.
        """
        ...

    def current_state(self, artifact_hash: str) -> ArtifactState | None:
        """Return one artefact's current state.

        Args:
            artifact_hash: Digest of the exact artefact.

        Returns:
            The most recent state, or None when unrecorded.
        """
        ...

    def next_sequence(self, artifact_hash: str) -> int:
        """Return the next free position in one artefact's history.

        Args:
            artifact_hash: Digest of the exact artefact.

        Returns:
            The next sequence value, one for an unrecorded artefact.
        """
        ...

    def save_packet(self, packet: PromotionEvidencePacket) -> PromotionEvidencePacket:
        """Persist one assembled promotion evidence packet.

        Args:
            packet: Validated immutable packet.

        Returns:
            The persisted packet.

        Raises:
            ValueError: If a different packet already claims the digest.
        """
        ...

    def load_packet(self, packet_hash: str) -> PromotionEvidencePacket | None:
        """Load one packet by its assembly digest.

        Args:
            packet_hash: Assembly digest.

        Returns:
            The packet, or None when unrecorded.
        """
        ...


class _InMemoryLifecycleStore:
    """Deterministic in-process lifecycle ledger for tests and usage."""

    def __init__(self) -> None:
        """Initialize the empty ledger."""
        self._records: dict[str, list[LifecycleRecord]] = {}
        self._packets: dict[str, PromotionEvidencePacket] = {}

    def append_record(self, record: LifecycleRecord) -> LifecycleRecord:
        """Append one transition at the next free position.

        Args:
            record: Validated immutable transition record.

        Returns:
            The persisted record.

        Raises:
            ValueError: If the position is already written or out of order.
        """
        history = self._records.setdefault(record.artifact_hash, [])
        expected = len(history) + 1
        if record.sequence != expected:
            message = (
                f"lifecycle position {record.sequence} is not appendable for "
                f"artefact {record.artifact_hash}; the next free position is "
                f"{expected}"
            )
            raise ValueError(message)
        history.append(record)
        return record

    def list_records(self, artifact_hash: str) -> tuple[LifecycleRecord, ...]:
        """List one artefact's complete history, oldest first.

        Args:
            artifact_hash: Digest of the exact artefact.

        Returns:
            Ordered transition records, empty when unrecorded.
        """
        return tuple(self._records.get(artifact_hash, ()))

    def current_state(self, artifact_hash: str) -> ArtifactState | None:
        """Return one artefact's current state.

        Args:
            artifact_hash: Digest of the exact artefact.

        Returns:
            The most recent state, or None when unrecorded.
        """
        history = self._records.get(artifact_hash)
        if not history:
            return None
        return history[-1].state

    def next_sequence(self, artifact_hash: str) -> int:
        """Return the next free position in one artefact's history.

        Args:
            artifact_hash: Digest of the exact artefact.

        Returns:
            The next sequence value, one for an unrecorded artefact.
        """
        return len(self._records.get(artifact_hash, ())) + 1

    def save_packet(self, packet: PromotionEvidencePacket) -> PromotionEvidencePacket:
        """Persist one assembled promotion evidence packet.

        Args:
            packet: Validated immutable packet.

        Returns:
            The persisted packet.

        Raises:
            ValueError: If a different packet already claims the digest.
        """
        existing = self._packets.get(packet.packet_hash)
        if existing is not None and existing.packet_id != packet.packet_id:
            message = f"promotion packet digest {packet.packet_hash} already recorded"
            raise ValueError(message)
        self._packets[packet.packet_hash] = packet
        return packet

    def load_packet(self, packet_hash: str) -> PromotionEvidencePacket | None:
        """Load one packet by its assembly digest.

        Args:
            packet_hash: Assembly digest.

        Returns:
            The packet, or None when unrecorded.
        """
        return self._packets.get(packet_hash)


def build_in_memory_lifecycle_store() -> AgenticLifecycleStore:
    """Build the deterministic in-process lifecycle ledger.

    Returns:
        A store satisfying `AgenticLifecycleStore`.
    """
    logger.debug("Building the in-memory Agentic lifecycle store")
    return _InMemoryLifecycleStore()
