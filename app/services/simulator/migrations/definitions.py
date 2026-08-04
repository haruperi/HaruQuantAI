"""Simulator-owned schema migration definitions.

The run-identity table and completed-run playback-session cursor table are
declared. The canonical journal remains append-only JSONL
(``JOURNAL_FORMAT = "jsonl-v1"``); no table backs the journal itself.

The table is renamed ``simulation_runs`` -> ``sim_runs`` under the ratified
``sim_`` namespace. The ledger domain is corrected ``simulation`` ->
``simulator`` to match the owning package, and the checksum drops its
``sha256:`` prefix so every domain stores a bare digest. The step has never been
applied to a database, so these are definition edits rather than rename
migrations; see ``FR-SIM-091`` and ``FR-SIM-092``.
"""

from hashlib import sha256
from typing import Any

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

SIMULATION_MIGRATIONS: tuple[Any, ...] = (
    build_migration_step(
        domain="simulator",
        migration_id="001_simulator_state_v1",
        checksum=sha256("\n".join(_STATEMENTS).encode("utf-8")).hexdigest(),
        statements=_STATEMENTS,
    ),
)

_PLAYBACK_SESSION_STATEMENTS = (
    (
        "CREATE TABLE IF NOT EXISTS sim_sessions ("
        "session_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, "
        "status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'expired')), "
        "cursor INTEGER NOT NULL CHECK(cursor >= -1), "
        "created_at TEXT NOT NULL, expires_at TEXT NOT NULL, "
        "FOREIGN KEY(run_id) REFERENCES sim_runs(run_id)"
        ") STRICT"
    ),
    "CREATE INDEX IF NOT EXISTS idx_sim_sessions_run ON sim_sessions(run_id)",
    (
        "CREATE INDEX IF NOT EXISTS idx_sim_sessions_expiry "
        "ON sim_sessions(status, expires_at)"
    ),
)

SIMULATION_MIGRATIONS += (
    build_migration_step(
        domain="simulator",
        migration_id="002_simulator_playback_sessions_v1",
        checksum=sha256(
            "\n".join(_PLAYBACK_SESSION_STATEMENTS).encode("utf-8")
        ).hexdigest(),
        statements=_PLAYBACK_SESSION_STATEMENTS,
    ),
)

__all__ = ["SIMULATION_MIGRATIONS"]
