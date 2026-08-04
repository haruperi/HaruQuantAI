"""Durable Agentic lifecycle store over Agentic-owned relational records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.lifecycle.models import (
    ArtifactState,
    LifecycleRecord,
    PromotionEvidencePacket,
)
from app.agentic.persistence import (
    create_agentic_persistence_store,
    create_lifecycle_packet_record,
    create_lifecycle_record,
    read_lifecycle_packet_record,
    read_lifecycle_records,
)


def _encode(value: object) -> str:
    """Encode one validated lifecycle model.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a validated model.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Agentic lifecycle state must be a validated model")
    return value.model_dump_json()


class DurableLifecycleStore:
    """Data-backed implementation of the Agentic lifecycle-store port."""

    def __init__(self) -> None:
        """Build the relational persistence handle."""
        self._store = create_agentic_persistence_store(
            {
                "lifecycle": (_encode, LifecycleRecord.model_validate_json),
                "packet": (_encode, PromotionEvidencePacket.model_validate_json),
            }
        )

    def append_record(self, record: LifecycleRecord) -> LifecycleRecord:
        """Append one transition at the declared next position.

        Returns:
            Persisted record.

        Raises:
            ValueError: If the sequence is not the next free position.
        """
        if record.sequence != self.next_sequence(record.artifact_hash):
            raise ValueError("Agentic lifecycle sequence is not appendable")
        create_lifecycle_record(
            self._store,
            key=record.record_id,
            partition=record.artifact_hash,
            sequence=record.sequence,
            value=record,
        )
        return record

    def list_records(self, artifact_hash: str) -> tuple[LifecycleRecord, ...]:
        """List one artifact's lifecycle history.

        Returns:
            Ordered transition records.
        """
        return cast(
            "tuple[LifecycleRecord, ...]",
            read_lifecycle_records(
                self._store,
                artifact_hash,
                1_000,
            ),
        )

    def current_state(self, artifact_hash: str) -> ArtifactState | None:
        """Return an artifact's most recent state.

        Returns:
            Current state or ``None``.
        """
        records = self.list_records(artifact_hash)
        return records[-1].state if records else None

    def next_sequence(self, artifact_hash: str) -> int:
        """Return the next free lifecycle position.

        Returns:
            Positive sequence number.
        """
        return len(self.list_records(artifact_hash)) + 1

    def save_packet(self, packet: PromotionEvidencePacket) -> PromotionEvidencePacket:
        """Persist one immutable promotion packet.

        Returns:
            Persisted packet.
        """
        create_lifecycle_packet_record(
            self._store,
            packet.packet_hash,
            packet,
        )
        return packet

    def load_packet(self, packet_hash: str) -> PromotionEvidencePacket | None:
        """Load one promotion packet by digest.

        Returns:
            Packet or ``None``.
        """
        return cast(
            "PromotionEvidencePacket | None",
            read_lifecycle_packet_record(
                self._store,
                packet_hash,
            ),
        )


__all__ = ("DurableLifecycleStore",)
