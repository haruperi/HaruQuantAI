"""Injected-store port for governed Agentic memory.

Agentic declares the persistence operations it needs and implements no database
writer, matching the Portfolio and Risk precedents. The in-memory reference
store is a deterministic development and evidence double; durability is a
property of the concrete store a composition root injects.

Writes are redacted before persistence and appended, never overwritten. A
correction is a new record naming the one it supersedes. Working memory cannot
be retrieved outside its task or after its TTL.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.agentic.context_memory.models import (
    EvidenceClaim,
    MemoryRecord,
    derive_content_hash,
)
from app.utils import derive_stable_id, get_logger, redact_mapping_value, utc_now

logger = get_logger(__name__)


@runtime_checkable
class AgenticMemoryStore(Protocol):
    """Append-only persistence operations required by Agentic memory."""

    def append(self, record: MemoryRecord) -> MemoryRecord:
        """Append one governed memory record.

        Args:
            record: Redacted governed record.

        Returns:
            The appended record.
        """
        ...

    def append_claim(self, claim: EvidenceClaim) -> EvidenceClaim:
        """Append one immutable governed evidence claim.

        Args:
            claim: Validated evidence claim.

        Returns:
            The appended claim.
        """
        ...

    def list_claims(self, task_id: str) -> tuple[EvidenceClaim, ...]:
        """List governed evidence claims for one task.

        Args:
            task_id: Owning task identity.

        Returns:
            Point-in-time ordered claims.
        """
        ...

    def list_records(
        self,
        store_class: str,
        task_id: str,
    ) -> tuple[MemoryRecord, ...]:
        """List records in one store for one task, in write order.

        Args:
            store_class: Owning store.
            task_id: Owning task identity.

        Returns:
            Ordered appended records.
        """
        ...


class _InMemoryMemoryStore:
    """Deterministic non-durable append-only reference store."""

    def __init__(self) -> None:
        """Initialise empty append-only record state."""
        self._records: list[MemoryRecord] = []
        self._claims: list[EvidenceClaim] = []

    def append_claim(self, claim: EvidenceClaim) -> EvidenceClaim:
        """Append one immutable governed evidence claim.

        Returns:
            The appended claim.

        Raises:
            ValueError: If the claim identity already exists.
        """
        if any(stored.claim_id == claim.claim_id for stored in self._claims):
            message = f"evidence claim {claim.claim_id} already exists"
            raise ValueError(message)
        self._claims.append(claim)
        return claim

    def list_claims(self, task_id: str) -> tuple[EvidenceClaim, ...]:
        """List governed evidence claims for one task.

        Returns:
            Point-in-time ordered claims.
        """
        return tuple(claim for claim in self._claims if claim.task_id == task_id)

    def append(self, record: MemoryRecord) -> MemoryRecord:
        """Append one governed memory record.

        Args:
            record: Redacted governed record.

        Returns:
            The appended record.

        Raises:
            ValueError: If the record identity already exists.
        """
        if any(stored.record_id == record.record_id for stored in self._records):
            message = f"memory record {record.record_id} already exists"
            raise ValueError(message)
        self._records.append(record)
        return record

    def list_records(
        self,
        store_class: str,
        task_id: str,
    ) -> tuple[MemoryRecord, ...]:
        """List records in one store for one task, in write order.

        Args:
            store_class: Owning store.
            task_id: Owning task identity.

        Returns:
            Ordered appended records.
        """
        return tuple(
            record
            for record in self._records
            if record.store_class == store_class and record.task_id == task_id
        )


def build_in_memory_memory_store() -> AgenticMemoryStore:
    """Build the deterministic non-durable governed memory store.

    Returns:
        A store satisfying the `AgenticMemoryStore` port.
    """
    logger.debug("Building the in-memory Agentic memory store")
    return _InMemoryMemoryStore()


def store_memory(
    store: AgenticMemoryStore,
    store_class: str,
    task_id: str,
    author_role_id: str,
    content: Mapping[str, str],
    scope: Mapping[str, str],
    retention_class: str,
    sensitivity: str = "internal",
    source_evidence_refs: tuple[str, ...] = (),
    expires_at: datetime | None = None,
    supersedes: str | None = None,
    injection_status: str = "clean",
    at_time: datetime | None = None,
) -> MemoryRecord:
    """Redact and append one governed memory record.

    Every write is redacted before persistence, so sensitive material never
    reaches the store even if an agent proposes it.

    Args:
        store: Injected append-only memory store.
        store_class: Owning store.
        task_id: Owning task identity.
        author_role_id: Registered role proposing the write.
        content: Candidate content.
        scope: Governed scope the record belongs to.
        retention_class: Declared retention class.
        sensitivity: Declared sensitivity class.
        source_evidence_refs: Supporting evidence references.
        expires_at: TTL expiry, required for working memory.
        supersedes: Record this one corrects.
        injection_status: Injection classification of the content.
        at_time: Optional write time; current UTC when omitted.

    Returns:
        The appended redacted record.

    Raises:
        TypeError: If redaction did not return a mapping.
    """
    now = at_time if at_time is not None else utc_now()
    redaction = redact_mapping_value(dict(content))
    # The redaction result exposes its value as an opaque object; narrow it
    # explicitly rather than assuming a mapping came back.
    redacted_source = redaction.value
    if not isinstance(redacted_source, Mapping):
        message = "redaction did not return a mapping"
        raise TypeError(message)
    redacted_content = {str(key): str(value) for key, value in redacted_source.items()}
    if redaction.redacted_paths:
        logger.warning(
            "Redacted %d sensitive paths before persisting memory for task %s",
            len(redaction.redacted_paths),
            task_id,
        )
    # Identity derives from the content digest, not merely the write instant:
    # two distinct records written in the same instant for the same task would
    # otherwise collide.
    content_hash = derive_content_hash(redacted_content)
    record = MemoryRecord(
        record_id=derive_stable_id(
            "id",
            f"memory:{store_class}:{task_id}:{now.isoformat()}:{content_hash}",
        ),
        store_class=store_class,  # type: ignore[arg-type]
        task_id=task_id,
        scope=dict(scope),
        author_role_id=author_role_id,
        content=redacted_content,
        source_evidence_refs=source_evidence_refs,
        created_at=now,
        expires_at=expires_at,
        retention_class=retention_class,
        sensitivity=sensitivity,  # type: ignore[arg-type]
        injection_status=injection_status,  # type: ignore[arg-type]
        redacted_paths=tuple(redaction.redacted_paths),
        content_hash=content_hash,
        supersedes=supersedes,
    )
    logger.info(
        "Appending %s memory record for task %s",
        store_class,
        task_id,
    )
    return store.append(record)


def store_evidence_claim(
    store: AgenticMemoryStore,
    claim: EvidenceClaim,
) -> EvidenceClaim:
    """Append one already-validated immutable evidence claim.

    Args:
        store: Injected governed memory store.
        claim: Claim built through the public contract builder.

    Returns:
        The appended claim.
    """
    logger.info("Appending governed evidence claim for task %s", claim.task_id)
    return store.append_claim(claim)


def retrieve_evidence_claims(
    store: AgenticMemoryStore,
    task_id: str,
) -> tuple[EvidenceClaim, ...]:
    """Retrieve point-in-time ordered evidence claims for one task.

    Args:
        store: Injected governed memory store.
        task_id: Owning task identity.

    Returns:
        Bounded claims belonging to the task.
    """
    return store.list_claims(task_id)


def retrieve_memory(
    store: AgenticMemoryStore,
    store_class: str,
    task_id: str,
    at_time: datetime | None = None,
) -> tuple[MemoryRecord, ...]:
    """Retrieve bounded governed memory for one declared task scope.

    Freshness is re-verified at retrieval rather than trusting stored recency:
    an expired record is never returned, and working memory is unavailable
    outside its owning task by construction.

    Args:
        store: Injected append-only memory store.
        store_class: Owning store.
        task_id: Owning task identity.
        at_time: Optional retrieval time; current UTC when omitted.

    Returns:
        Ordered live records, superseded and expired records excluded.
    """
    now = at_time if at_time is not None else utc_now()
    records = store.list_records(store_class, task_id)
    superseded = {
        record.supersedes for record in records if record.supersedes is not None
    }
    live = tuple(
        record
        for record in records
        if record.record_id not in superseded
        and (record.expires_at is None or record.expires_at > now)
    )
    logger.info(
        "Retrieved %d live %s records for task %s",
        len(live),
        store_class,
        task_id,
    )
    return live
