"""Immutable Economic Calendar event-definition migration."""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationStep

_STATEMENTS = (
    """
    CREATE TABLE data_economic_event_definitions (
        provider TEXT NOT NULL,
        provider_definition_id TEXT NOT NULL,
        country TEXT NOT NULL,
        title TEXT NOT NULL,
        source_url TEXT NOT NULL,
        source_original TEXT,
        source_latest TEXT,
        measures TEXT,
        effect TEXT,
        frequency TEXT,
        also_called TEXT,
        event_type TEXT,
        first_seen_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_verified_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        PRIMARY KEY (provider, provider_definition_id),
        UNIQUE (provider, source_url)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX idx_economic_definitions_match "
        "ON data_economic_event_definitions (provider, country, title)"
    ),
    "ALTER TABLE data_economic_events ADD COLUMN provider_definition_id TEXT",
    (
        "CREATE INDEX idx_economic_events_definition "
        "ON data_economic_events (provider, provider_definition_id)"
    ),
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Return the immutable ordered-statement checksum.

    Args:
        statements: The ``statements`` argument.

    Returns:
        The result produced by the operation.
    """
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


ECONOMIC_EVENT_DEFINITIONS_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="009_economic_event_definitions",
    checksum=_checksum(_STATEMENTS),
    statements=_STATEMENTS,
)

__all__ = ["ECONOMIC_EVENT_DEFINITIONS_MIGRATION_STEP"]
