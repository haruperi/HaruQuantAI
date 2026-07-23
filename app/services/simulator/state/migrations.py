"""Simulation-owned schema migration definitions.

Only the run-identity table is declared. The canonical journal is append-only
JSONL (`JOURNAL_FORMAT = "jsonl-v1"`); no table backs it, because a SQLite
journal sidecar is an explicit Phase 1 exclusion.
"""

from hashlib import sha256

from app.services.data.persistence.contracts import (
    MigrationStep,
)

_STATEMENTS = (
    "CREATE TABLE IF NOT EXISTS simulation_runs ("
    "request_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, "
    "run_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, "
    "result_payload TEXT)",
)

SIMULATION_MIGRATIONS = (
    MigrationStep(
        domain="simulation",
        migration_id="simulation-0001-state",
        checksum=f"sha256:{sha256('\n'.join(_STATEMENTS).encode('utf-8')).hexdigest()}",
        statements=_STATEMENTS,
    ),
)

__all__ = ["SIMULATION_MIGRATIONS"]
