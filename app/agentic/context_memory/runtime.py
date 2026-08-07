"""Durable Agentic memory store over Agentic-owned relational records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.context_memory.models import EvidenceClaim, MemoryRecord
from app.agentic.persistence import (
    create_agentic_persistence_store,
    create_evidence_claim,
    create_memory_record,
    read_evidence_claims,
    read_memory_records,
)


def _encode(value: object) -> str:
    """Encode one validated memory record.

    Returns:
        JSON text.

    Raises:
        TypeError: If the value is not a memory record.
    """
    if not isinstance(value, BaseModel):
        raise TypeError("Agentic memory state must be a validated model")
    return value.model_dump_json()


class DurableMemoryStore:
    """Data-backed implementation of the Agentic memory-store port."""

    def __init__(self) -> None:
        """Build the relational persistence handle."""
        self._store = create_agentic_persistence_store(
            {
                "evidence": (_encode, EvidenceClaim.model_validate_json),
                "memory": (_encode, MemoryRecord.model_validate_json),
            }
        )

    def append_claim(self, claim: EvidenceClaim) -> EvidenceClaim:
        """Append one governed evidence claim.

        Returns:
            Appended claim.
        """
        create_evidence_claim(self._store, claim)
        return claim

    def list_claims(self, task_id: str) -> tuple[EvidenceClaim, ...]:
        """List governed evidence claims for one task.

        Returns:
            Point-in-time ordered claims.
        """
        return cast(
            "tuple[EvidenceClaim, ...]",
            read_evidence_claims(self._store, task_id, 1_000),
        )

    def append(self, record: MemoryRecord) -> MemoryRecord:
        """Append one governed memory record.

        Returns:
            Appended record.
        """
        records = self.list_records(record.store_class, record.task_id)
        create_memory_record(
            self._store,
            key=record.record_id,
            partition=record.task_id,
            sequence=len(records) + 1,
            value=record,
        )
        return record

    def list_records(self, store_class: str, task_id: str) -> tuple[MemoryRecord, ...]:
        """List governed memory records in write order.

        Returns:
            Ordered records.
        """
        return cast(
            "tuple[MemoryRecord, ...]",
            read_memory_records(
                self._store,
                store_class,
                task_id,
                1_000,
            ),
        )


__all__ = ("DurableMemoryStore",)
