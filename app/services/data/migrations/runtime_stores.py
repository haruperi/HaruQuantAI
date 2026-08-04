"""Immutable migration manifest for Data-owned runtime records.

Conformed to the authoritative schema model in ``docs/schema`` (Domain 3). The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-DATA-151``.

Two corrections land here. The table is renamed ``hq_runtime_records`` ->
``data_runtime_records``: ``hq_`` is not a ratified namespace and names no
domain. The ledger domain is corrected ``data-runtime`` -> ``data``: the former
matched no folder, no prefix, and no entry in the system data-ownership record.
"""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import run_domain_migrations

_DOMAIN = "data"
_MIGRATION_ID = "005-runtime-records"

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS data_runtime_records (
        namespace TEXT NOT NULL,
        collection_name TEXT NOT NULL,
        record_key TEXT NOT NULL,
        partition_key TEXT NOT NULL,
        sequence_number INTEGER NOT NULL,
        codec_kind TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK (revision > 0),
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        PRIMARY KEY (namespace, collection_name, record_key),
        UNIQUE (namespace, collection_name, partition_key, sequence_number)
    ) STRICT""",
    """CREATE INDEX IF NOT EXISTS idx_data_runtime_records_partition
       ON data_runtime_records(
           namespace, collection_name, partition_key, sequence_number
       )""",
)


def get_runtime_store_migration_steps() -> tuple[MigrationStep, ...]:
    """Return the immutable runtime-store migration manifest.

    Returns:
        Ordered migration steps as opaque Data contract values.
    """
    checksum = hashlib.sha256("\n".join(_STATEMENTS).encode()).hexdigest()
    return (
        MigrationStep(
            domain=_DOMAIN,
            migration_id=_MIGRATION_ID,
            checksum=checksum,
            statements=_STATEMENTS,
        ),
    )


def run_runtime_store_migrations(request_id: str) -> object:
    """Apply the Data-owned runtime-store migration manifest.

    Args:
        request_id: Correlation-safe migration request identity.

    Returns:
        Standard Data migration response.
    """
    return run_domain_migrations(
        MigrationRequest(
            domain=_DOMAIN,
            steps=get_runtime_store_migration_steps(),
            request_id=request_id,
        )
    )
