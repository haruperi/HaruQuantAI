"""Immutable Economic Calendar schema consolidation migration."""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationStep

_STATEMENTS = (
    "ALTER TABLE data_economic_events RENAME TO data_economic_events_legacy",
    """
    CREATE TABLE data_economic_events (
        event_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        country TEXT NOT NULL,
        scheduled_at TEXT NOT NULL,
        original_scheduled_at TEXT NOT NULL,
        impact INTEGER NOT NULL CHECK (impact BETWEEN 1 AND 3),
        actual TEXT,
        forecast TEXT,
        previous TEXT,
        revised_previous TEXT,
        provider TEXT NOT NULL,
        source_url TEXT,
        first_seen_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        request_id TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    INSERT INTO data_economic_events (
        event_id, title, country, scheduled_at, original_scheduled_at, impact,
        actual, forecast, previous, revised_previous, provider, source_url,
        first_seen_at, updated_at, request_id
    )
    SELECT
        provider || ':' || provider_event_id,
        name,
        COALESCE(currency, country, 'ALL'),
        scheduled_at,
        COALESCE(original_scheduled_at, scheduled_at),
        impact,
        COALESCE(actual_raw, actual),
        COALESCE(forecast_raw, forecast),
        COALESCE(previous_raw, previous),
        revised_previous,
        provider,
        source_url,
        COALESCE(updated_at, scheduled_at),
        COALESCE(updated_at, scheduled_at),
        ''
    FROM data_economic_events_legacy
    """.strip(),
    "DROP TABLE data_economic_events_legacy",
    (
        "CREATE INDEX idx_economic_events_scheduled "
        "ON data_economic_events (scheduled_at)"
    ),
    (
        "CREATE INDEX idx_economic_events_scope "
        "ON data_economic_events (country, impact, scheduled_at)"
    ),
    """
    CREATE TABLE data_economic_calendar_coverage (
        provider TEXT NOT NULL,
        range_start TEXT NOT NULL,
        range_end TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('complete', 'partial')),
        source_revision TEXT NOT NULL,
        synchronized_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        PRIMARY KEY (provider, range_start, range_end),
        CHECK (range_start < range_end)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX idx_economic_coverage_range "
        "ON data_economic_calendar_coverage (range_start, range_end, status)"
    ),
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Return the immutable ordered-statement checksum."""
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


ECONOMIC_CALENDAR_V2_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="007_economic_calendar_database_first",
    checksum=_checksum(_STATEMENTS),
    statements=_STATEMENTS,
)

__all__ = ["ECONOMIC_CALENDAR_V2_MIGRATION_STEP"]
