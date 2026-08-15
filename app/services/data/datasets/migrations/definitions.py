"""Provider-specification revision schema owned by FEAT-DATA-02."""

import hashlib

from app.services.data.persistence.contracts import MigrationStep

_STATEMENTS = (
    """
CREATE TABLE IF NOT EXISTS data_provider_specification_revisions (
    revision_id TEXT PRIMARY KEY,
    broker TEXT NOT NULL,
    server TEXT NOT NULL,
    environment TEXT NOT NULL,
    account_digest TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    snapshot_checksum TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    retrieval_provenance TEXT NOT NULL,
    historical_provenance_json TEXT,
    payload_json TEXT NOT NULL,
    supersedes_revision_id TEXT,
    request_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (effective_to IS NULL OR effective_from < effective_to),
    UNIQUE (
        broker, server, environment, account_digest, provider_symbol,
        effective_from
    ),
    UNIQUE (snapshot_checksum),
    FOREIGN KEY (supersedes_revision_id)
        REFERENCES data_provider_specification_revisions(revision_id)
) STRICT
""".strip(),
    """
CREATE INDEX IF NOT EXISTS idx_data_provider_specification_identity_interval
ON data_provider_specification_revisions (
    broker, server, environment, account_digest, provider_symbol,
    effective_from, effective_to
)
""".strip(),
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Return the stable checksum for the ordered schema statements.

    Args:
        statements: Ordered immutable SQL statements.

    Returns:
        SHA-256 checksum of the migration material.
    """
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


PROVIDER_SPECIFICATION_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="010_provider_specification_revisions",
    checksum=_checksum(_STATEMENTS),
    statements=_STATEMENTS,
)

__all__ = ["PROVIDER_SPECIFICATION_MIGRATION_STEP"]
