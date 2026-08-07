"""Research-owned artifact metadata migration definitions.

Conformed to the authoritative schema model in ``app/services/research/README.md``. The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-RES-105`` and
``FR-RES-106``.

The model adopts this domain's shape rather than the reverse. ``research_artifacts``
is a **file manifest** keyed by ``relative_path``, not a general artifact catalog:
it records what was written, how large it was, whether the write was atomic, and
which audit event authorised it.
"""

from __future__ import annotations

import hashlib

from app.services.data import build_migration_request, build_migration_step
from app.services.research.contracts.errors import (
    ConfigurationError,
)
from app.utils import get_logger

logger = get_logger(__name__)

_DOMAIN = "research"
_MIGRATION_ID = "001_research_artifacts_v1"

_CREATE_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_artifacts ("
    "relative_path TEXT PRIMARY KEY, "
    "format TEXT NOT NULL, "
    "size_bytes INTEGER NOT NULL, "
    "sha256 TEXT NOT NULL, "
    "atomic INTEGER NOT NULL, "
    "schema_version TEXT NOT NULL, "
    "audit_event_id TEXT NOT NULL, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "correlation_id TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)

_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_artifacts_sha256 "
    "ON research_artifacts (sha256)"
)

_AUDIT_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_artifacts_audit "
    "ON research_artifacts (audit_event_id)"
)

_STATEMENTS = (_CREATE_STATEMENT, _INDEX_STATEMENT, _AUDIT_INDEX_STATEMENT)


def _checksum(statements: tuple[str, ...]) -> str:
    """Compute a stable sha256 checksum over canonical joined statements.

    Args:
        statements: Ordered SQL statements.

    Returns:
        Lowercase hex digest.
    """
    material = "\n-- statement --\n".join(statements)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


RESEARCH_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def build_research_migration_request(request_id: str) -> object:
    """Return the deterministic Research-owned artifact metadata migration.

    Execution is delegated to Data's ``run_domain_migrations`` by callers.

    Args:
        request_id: Canonical ``req-`` prefixed request identifier.

    Returns:
        Validated ``MigrationRequest`` for the research domain.

    Raises:
        ConfigurationError: If the request id is invalid.
    """
    logger.info("Building Research artifact migration request")
    if not request_id or request_id != request_id.strip():
        raise ConfigurationError("RES_CONFIGURATION_INVALID", "INVALID_REQUEST_ID")
    return build_migration_request(
        domain=_DOMAIN,
        steps=RESEARCH_MIGRATION_STEPS,
        request_id=request_id,
    )


__all__ = (
    "RESEARCH_MIGRATION_STEPS",
    "build_research_migration_request",
)
