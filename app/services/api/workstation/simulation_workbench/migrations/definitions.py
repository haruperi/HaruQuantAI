"""Authoritative Simulation Workbench-owned persistence migration manifest.

The four tables are additive and forward-only. They store principal-scoped
catalogue metadata and immutable owner references only; no calculated
metric, trade ledger, full report, or full Simulation result column
exists. Applied steps are immutable: any statement change must ship under
a new migration id with its own checksum.
"""

import hashlib

from app.services.data import build_migration_step
from app.utils import canonical_json

_SIMULATION_WORKBENCH_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS api_simulation_results (
        run_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL CHECK (principal_id <> ''),
        origin_kind TEXT NOT NULL CHECK (
            origin_kind IN (
                'canonical_job', 'batch', 'practice', 'reproduction', 'portfolio'
            )
        ),
        origin_id TEXT,
        job_id TEXT,
        batch_id TEXT,
        session_id TEXT,
        strategy_id TEXT,
        strategy_version TEXT,
        strategy_label TEXT,
        symbols TEXT NOT NULL DEFAULT '[]',
        timeframe TEXT,
        measurement_start TEXT,
        measurement_end TEXT,
        status TEXT NOT NULL CHECK (
            status IN ('queued', 'running', 'completed', 'failed', 'cancelled')
        ),
        result_ref TEXT,
        report_id TEXT,
        report_ref TEXT,
        artifact_manifest_ref TEXT,
        quality_status TEXT,
        evidence_class TEXT NOT NULL CHECK (
            evidence_class IN (
                'canonical', 'practice', 'advisory', 'playback', 'fast_research'
            )
        ),
        created_at TEXT NOT NULL,
        completed_at TEXT,
        name TEXT,
        alias TEXT,
        description TEXT,
        tags TEXT NOT NULL DEFAULT '[]',
        run_reason TEXT,
        archive_state TEXT NOT NULL DEFAULT 'active'
            CHECK (archive_state IN ('active', 'archived')),
        updated_at TEXT NOT NULL,
        FOREIGN KEY (principal_id) REFERENCES api_accounts(user_id)
            ON DELETE RESTRICT
    ) STRICT
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_simulation_results_principal "
    "ON api_simulation_results(principal_id, created_at DESC, run_id DESC)",
    "CREATE INDEX IF NOT EXISTS idx_api_simulation_results_batch "
    "ON api_simulation_results(batch_id)",
    """
    CREATE TABLE IF NOT EXISTS api_simulation_sessions (
        session_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL CHECK (principal_id <> ''),
        run_id TEXT NOT NULL,
        mode TEXT NOT NULL CHECK (mode <> ''),
        evidence_class TEXT NOT NULL CHECK (evidence_class <> ''),
        status TEXT NOT NULL CHECK (status <> ''),
        cursor INTEGER NOT NULL,
        tick_count INTEGER NOT NULL,
        completed INTEGER NOT NULL CHECK (completed IN (0, 1)),
        durable INTEGER NOT NULL CHECK (durable IN (0, 1)),
        state_hash TEXT,
        closed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (principal_id) REFERENCES api_accounts(user_id)
            ON DELETE RESTRICT,
        FOREIGN KEY (run_id) REFERENCES api_simulation_results(run_id)
            ON DELETE RESTRICT
    ) STRICT
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_simulation_sessions_principal "
    "ON api_simulation_sessions(principal_id, created_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS api_simulation_batches (
        batch_id TEXT PRIMARY KEY,
        principal_id TEXT NOT NULL CHECK (principal_id <> ''),
        status TEXT NOT NULL CHECK (
            status IN ('queued', 'running', 'completed', 'failed', 'cancelled')
        ),
        concurrency INTEGER NOT NULL CHECK (concurrency BETWEEN 1 AND 8),
        name TEXT,
        total_count INTEGER NOT NULL CHECK (total_count BETWEEN 1 AND 100),
        completed_count INTEGER NOT NULL DEFAULT 0,
        failed_count INTEGER NOT NULL DEFAULT 0,
        cancelled_count INTEGER NOT NULL DEFAULT 0,
        finished_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (principal_id) REFERENCES api_accounts(user_id)
            ON DELETE RESTRICT
    ) STRICT
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_simulation_batches_principal "
    "ON api_simulation_batches(principal_id, created_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS api_simulation_batch_items (
        batch_id TEXT NOT NULL,
        position INTEGER NOT NULL CHECK (position >= 0),
        run_id TEXT,
        job_id TEXT,
        status TEXT NOT NULL CHECK (
            status IN ('queued', 'running', 'completed', 'failed', 'cancelled')
        ),
        error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (batch_id, position),
        FOREIGN KEY (batch_id) REFERENCES api_simulation_batches(batch_id)
            ON DELETE RESTRICT
    ) STRICT, WITHOUT ROWID
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_simulation_batch_items_batch "
    "ON api_simulation_batch_items(batch_id, position)",
)
_SIMULATION_WORKBENCH_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0011",
            "sql": _SIMULATION_WORKBENCH_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()


def get_simulation_workbench_migration_steps() -> tuple[object, ...]:
    """Return the immutable Simulation Workbench migration definitions.

    Returns:
        Ordered forward-only migration steps with identity-bound checksums.
    """
    return (
        build_migration_step(
            domain="api",
            migration_id="api-0011",
            checksum=_SIMULATION_WORKBENCH_CHECKSUM,
            statements=_SIMULATION_WORKBENCH_STATEMENTS,
        ),
    )


__all__ = ("get_simulation_workbench_migration_steps",)
