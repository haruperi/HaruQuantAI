"""Research-owned artifact metadata migration definitions."""

from __future__ import annotations

import hashlib

from app.services.data import MigrationRequest, MigrationStep
from app.utils import ConfigurationError, logger

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
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ")"
)

_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_artifacts_sha256 "
    "ON research_artifacts (sha256)"
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Compute a stable sha256 checksum over canonical joined statements.

    Args:
        statements: Ordered SQL statements.

    Returns:
        Lowercase hex digest.
    """
    material = "\n-- statement --\n".join(statements)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


RESEARCH_MIGRATION_STEPS: tuple[MigrationStep, ...] = (
    MigrationStep(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum((_CREATE_STATEMENT, _INDEX_STATEMENT)),
        statements=(_CREATE_STATEMENT, _INDEX_STATEMENT),
    ),
)


def build_research_migration_request(request_id: str) -> MigrationRequest:
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
    return MigrationRequest(
        domain=_DOMAIN,
        steps=RESEARCH_MIGRATION_STEPS,
        request_id=request_id,
    )


__all__ = (
    "RESEARCH_MIGRATION_STEPS",
    "build_research_migration_request",
)
