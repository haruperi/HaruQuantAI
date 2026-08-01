"""Immutable migration manifest for Data-owned runtime records."""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationRequest, MigrationStep
from app.services.data.persistence.migrations import run_domain_migrations

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS hq_runtime_records (
        namespace TEXT NOT NULL,
        collection_name TEXT NOT NULL,
        record_key TEXT NOT NULL,
        partition_key TEXT NOT NULL,
        sequence_number INTEGER NOT NULL,
        codec_kind TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK (revision > 0),
        PRIMARY KEY (namespace, collection_name, record_key),
        UNIQUE (namespace, collection_name, partition_key, sequence_number)
    )""",
    """CREATE INDEX IF NOT EXISTS idx_hq_runtime_records_partition
       ON hq_runtime_records(
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
            domain="data-runtime",
            migration_id="001-runtime-records",
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
            domain="data-runtime",
            steps=get_runtime_store_migration_steps(),
            request_id=request_id,
        )
    )


__all__ = ("get_runtime_store_migration_steps", "run_runtime_store_migrations")
