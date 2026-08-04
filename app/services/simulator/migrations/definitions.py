"""Simulator-owned schema migration definitions.

Only the run-identity table is declared. The canonical journal is append-only
JSONL (``JOURNAL_FORMAT = "jsonl-v1"``); no table backs it, because a SQLite
journal sidecar is an explicit Phase 1 exclusion. The authoritative schema model
in ``docs/schema`` defers to that exclusion rather than proposing a timeline
table.

The table is renamed ``simulation_runs`` -> ``sim_runs`` under the ratified
``sim_`` namespace. The ledger domain is corrected ``simulation`` ->
``simulator`` to match the owning package, and the checksum drops its
``sha256:`` prefix so every domain stores a bare digest. The step has never been
applied to a database, so these are definition edits rather than rename
migrations; see ``FR-SIM-091`` and ``FR-SIM-092``.
"""

from hashlib import sha256

from app.services.data import build_migration_step

_STATEMENTS = (
    (
        "CREATE TABLE IF NOT EXISTS sim_runs ("
        "request_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, "
        "run_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, "
        "result_payload TEXT, "
        "correlation_id TEXT NOT NULL DEFAULT '', "
        "created_at TEXT NOT NULL DEFAULT "
        "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), "
        "updated_at TEXT NOT NULL DEFAULT "
        "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
        ") STRICT"
    ),
    "CREATE INDEX IF NOT EXISTS idx_sim_runs_status ON sim_runs(status)",
)

SIMULATION_MIGRATIONS = (
    build_migration_step(
        domain="simulator",
        migration_id="001_simulator_state_v1",
        checksum=sha256("\n".join(_STATEMENTS).encode("utf-8")).hexdigest(),
        statements=_STATEMENTS,
    ),
)

__all__ = ["SIMULATION_MIGRATIONS"]
