"""Data-owned immutable research-source schema migration."""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationStep

_STATEMENTS = (
    """
    CREATE TABLE data_research_sources (
        document_id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        source_kind TEXT NOT NULL,
        external_id TEXT NOT NULL,
        title TEXT NOT NULL,
        source_url TEXT NOT NULL,
        asset_scope_json TEXT NOT NULL,
        issuer_scope_json TEXT NOT NULL,
        language TEXT NOT NULL,
        event_at TEXT,
        published_at TEXT NOT NULL,
        first_seen_at TEXT NOT NULL,
        available_at TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK (revision > 0),
        previous_document_id TEXT,
        original_hash TEXT NOT NULL,
        normalized_hash TEXT NOT NULL,
        original_content BLOB NOT NULL,
        normalized_text TEXT NOT NULL,
        license_id TEXT NOT NULL,
        retention_until TEXT NOT NULL,
        trust_status TEXT NOT NULL,
        manipulation_status TEXT NOT NULL,
        injection_status TEXT NOT NULL,
        currency TEXT,
        unit TEXT,
        provenance_json TEXT NOT NULL,
        UNIQUE (source_id, external_id, normalized_hash)
    ) STRICT
    """.strip(),
    """
    CREATE INDEX idx_data_research_sources_decision
    ON data_research_sources (available_at, source_kind, source_id, document_id)
    """.strip(),
)


def _checksum() -> str:
    """Return the immutable statement checksum."""
    return hashlib.sha256("\n-- statement --\n".join(_STATEMENTS).encode()).hexdigest()


RESEARCH_SOURCE_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="003_research_sources",
    checksum=_checksum(),
    statements=_STATEMENTS,
)

_PROVIDER_STATEMENTS = (
    """
    ALTER TABLE data_research_sources
    ADD COLUMN document_kind TEXT NOT NULL DEFAULT 'document'
    """.strip(),
    """
    ALTER TABLE data_research_sources
    ADD COLUMN macro_series_scope_json TEXT NOT NULL DEFAULT '[]'
    """.strip(),
    """
    ALTER TABLE data_research_sources
    ADD COLUMN parser_version TEXT NOT NULL DEFAULT 'generic-v1'
    """.strip(),
    """
    ALTER TABLE data_research_sources
    ADD COLUMN record_status TEXT NOT NULL DEFAULT 'active'
    CHECK (record_status IN ('active', 'superseded', 'tombstoned'))
    """.strip(),
    """
    CREATE TABLE data_research_observations (
        observation_id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        series_id TEXT NOT NULL,
        observation_period TEXT NOT NULL,
        value_json TEXT NOT NULL,
        unit TEXT,
        published_at TEXT NOT NULL,
        available_at TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK (revision > 0),
        previous_observation_id TEXT,
        content_hash TEXT NOT NULL,
        parser_version TEXT NOT NULL,
        trust_status TEXT NOT NULL,
        provenance_json TEXT NOT NULL,
        UNIQUE (
            source_id, series_id, observation_period, content_hash
        )
    ) STRICT
    """.strip(),
    """
    CREATE INDEX idx_data_research_observations_decision
    ON data_research_observations (
        available_at, source_id, series_id, observation_id
    )
    """.strip(),
    """
    CREATE TABLE data_verified_research_sources (
        source_id TEXT NOT NULL,
        parser_version TEXT NOT NULL,
        verified_at TEXT NOT NULL,
        external_record_id TEXT NOT NULL,
        fixture_sha256 TEXT NOT NULL,
        environments_json TEXT NOT NULL,
        license_policy TEXT NOT NULL,
        PRIMARY KEY (source_id, parser_version)
    ) STRICT
    """.strip(),
)

RESEARCH_PROVIDER_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="004_research_source_providers",
    checksum=hashlib.sha256(
        "\n-- statement --\n".join(_PROVIDER_STATEMENTS).encode()
    ).hexdigest(),
    statements=_PROVIDER_STATEMENTS,
)

__all__ = (
    "RESEARCH_PROVIDER_MIGRATION_STEP",
    "RESEARCH_SOURCE_MIGRATION_STEP",
)
