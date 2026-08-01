"""Durable Agentic memory store over Data-owned runtime records."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel

from app.agentic.context_memory.models import MemoryRecord
from app.services.data import (
    build_agentic_runtime_store,
    execute_runtime_store_operation,
)
from app.utils import canonical_digest


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


def _key(*values: str) -> str:
    """Derive one storage-safe identifier.

    Returns:
        Bounded key.
    """
    return f"record-{canonical_digest(values)}"


class DurableMemoryStore:
    """Data-backed implementation of the Agentic memory-store port."""

    def __init__(self) -> None:
        """Build the lazy Data runtime handle."""
        self._store = build_agentic_runtime_store(
            {"memory": (_encode, MemoryRecord.model_validate_json)}
        )

    def append(self, record: MemoryRecord) -> MemoryRecord:
        """Append one governed memory record.

        Returns:
            Appended record.
        """
        records = self.list_records(record.store_class, record.task_id)
        execute_runtime_store_operation(
            self._store,
            "append",
            collection="memory-records",
            key=_key(record.record_id),
            partition=_key(record.store_class, record.task_id),
            sequence=len(records) + 1,
            kind="memory",
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
            execute_runtime_store_operation(
                self._store,
                "list",
                collection="memory-records",
                partition=_key(store_class, task_id),
                limit=1_000,
            ),
        )


__all__ = ("DurableMemoryStore",)
