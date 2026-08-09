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

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)
from app.utils import get_logger

logger = get_logger(__name__)

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

_SECURED_SESSION_STATEMENTS = (
    (
        "ALTER TABLE sim_sessions ADD COLUMN session_kind TEXT NOT NULL "
        "DEFAULT 'playback' CHECK(session_kind IN ('playback', 'secured'))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'Standard' "
        "CHECK(mode IN ('Guided', 'Standard', 'Expert', 'Challenge'))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN recovery_state TEXT NOT NULL "
        "DEFAULT 'RUNNING' CHECK(recovery_state IN ('STARTING', "
        "'RECOVERY_LOCKED', 'RESTORING', 'RECONCILING', 'VERIFIED', "
        "'EXPLICIT_REARM', 'RUNNING', 'INTEGRITY_FAILURE'))"
    ),
    "ALTER TABLE sim_sessions ADD COLUMN secured_at TEXT",
    (
        "ALTER TABLE sim_sessions ADD COLUMN clock_state_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(clock_state_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN scenario_state_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(scenario_state_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN replay_identity_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(replay_identity_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN checklist_state_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(checklist_state_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN alert_state_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(alert_state_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN emergency_state_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(emergency_state_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN counters_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(counters_json))"
    ),
    (
        "ALTER TABLE sim_sessions ADD COLUMN branch_lineage_json TEXT NOT NULL "
        "DEFAULT '{}' CHECK(json_valid(branch_lineage_json))"
    ),
    (
        "CREATE TABLE IF NOT EXISTS sim_session_checkpoints ("
        "session_id TEXT NOT NULL, sequence INTEGER NOT NULL CHECK(sequence >= 0), "
        "checkpoint_hash TEXT NOT NULL, previous_hash TEXT, "
        "replay_identity_json TEXT NOT NULL CHECK(json_valid(replay_identity_json)), "
        "state_payload_json TEXT NOT NULL CHECK(json_valid(state_payload_json)), "
        "created_at TEXT NOT NULL, PRIMARY KEY(session_id, sequence), "
        "UNIQUE(checkpoint_hash), "
        "FOREIGN KEY(session_id) REFERENCES sim_sessions(session_id)"
        ") STRICT"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_sim_session_checkpoints_hash "
        "ON sim_session_checkpoints(session_id, checkpoint_hash)"
    ),
)

SIMULATION_MIGRATIONS += (
    build_migration_step(
        domain="simulator",
        migration_id="003_simulator_secured_sessions_v1",
        checksum=sha256(
            "\n".join(_SECURED_SESSION_STATEMENTS).encode("utf-8")
        ).hexdigest(),
        statements=_SECURED_SESSION_STATEMENTS,
    ),
)


def run_simulator_migrations(request_id: str) -> object:
    """Apply the complete immutable Simulator migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    logger.info("Running Simulator-owned schema migrations")
    request = build_migration_request(
        domain="simulator",
        steps=SIMULATION_MIGRATIONS,
        request_id=request_id,
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = ["SIMULATION_MIGRATIONS", "run_simulator_migrations"]
