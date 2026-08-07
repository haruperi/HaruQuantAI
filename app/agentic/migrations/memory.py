"""Agentic-owned evidence and memory-store schema definitions executed by Data.

Conformed to the authoritative schema model in ``docs/schema`` (Domain 13). The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-AGT-002``.
"""

from __future__ import annotations

import hashlib

from app.services.data import build_migration_request, build_migration_step
from app.utils import get_logger

logger = get_logger(__name__)

_DOMAIN = "agentic"
_MIGRATION_ID = "002_agentic_context_memory_v1"

_EVIDENCE_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_evidence_claims ("
    "claim_id TEXT PRIMARY KEY, "
    "task_id TEXT NOT NULL, "
    "statement TEXT NOT NULL, "
    "source_ref TEXT NOT NULL, "
    "source_trust TEXT NOT NULL, "
    "licence_ref TEXT NOT NULL, "
    "available_at TEXT NOT NULL, "
    "observed_at TEXT NOT NULL, "
    "content_hash TEXT NOT NULL, "
    "confidence_basis TEXT NOT NULL, "
    "falsifier TEXT NOT NULL, "
    "injection_status TEXT NOT NULL, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "correlation_id TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)

_MEMORY_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_memory_records ("
    "record_id TEXT PRIMARY KEY, "
    "store_class TEXT NOT NULL, "
    "task_id TEXT NOT NULL, "
    "author_role_id TEXT NOT NULL, "
    "content_json TEXT NOT NULL, "
    "scope_json TEXT NOT NULL, "
    "source_evidence_refs_json TEXT NOT NULL, "
    "created_at TEXT NOT NULL, "
    "expires_at TEXT, "
    "retention_class TEXT NOT NULL, "
    "sensitivity TEXT NOT NULL, "
    "injection_status TEXT NOT NULL, "
    "redacted_paths_json TEXT NOT NULL, "
    "content_hash TEXT NOT NULL, "
    "supersedes TEXT, "
    "correlation_id TEXT NOT NULL DEFAULT ''"
    ") STRICT"
)

_EVIDENCE_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_evidence_claims_task "
    "ON agentic_evidence_claims (task_id, available_at)"
)

_MEMORY_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_memory_records_scope "
    "ON agentic_memory_records (store_class, task_id, expires_at)"
)

_STATEMENTS: tuple[str, ...] = (
    _EVIDENCE_STATEMENT,
    _MEMORY_STATEMENT,
    _EVIDENCE_INDEX_STATEMENT,
    _MEMORY_INDEX_STATEMENT,
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Compute a stable digest over canonical joined statements.

    Args:
        statements: Ordered SQL statements.

    Returns:
        Lowercase hexadecimal digest.
    """
    material = "\n-- statement --\n".join(statements)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


AGENTIC_MEMORY_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def get_agentic_memory_migration_statements() -> tuple[str, ...]:
    """Return the ordered Agentic evidence and memory-store statements.

    Returns:
        Ordered additive schema statements.
    """
    return _STATEMENTS


def build_agentic_memory_migration_request(request_id: str) -> object:
    """Return the deterministic Agentic-owned memory-store migration.

    Args:
        request_id: Canonical `req-` prefixed request identifier.

    Returns:
        A validated migration request for the agentic domain.
    """
    logger.debug("Building the Agentic memory-store migration request")
    request: object = build_migration_request(
        domain=_DOMAIN,
        steps=AGENTIC_MEMORY_MIGRATION_STEPS,
        request_id=request_id,
    )
    return request
