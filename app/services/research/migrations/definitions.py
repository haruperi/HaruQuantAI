"""Research-owned artifact metadata migration definitions.

Conformed to the authoritative schema model in ``app/services/research/README.md``. The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-RES-105`` and
``FR-RES-106``.

The model adopts this domain's shape rather than the reverse. ``research_artifacts``
is a **file manifest** keyed by ``relative_path``, not a general artifact catalog:
it records what was written, how large it was, whether the write was atomic, and
which audit event authorised it.
"""

from __future__ import annotations

import hashlib

from app.composition.logging import get_logger
from app.services.data import build_migration_request, build_migration_step
from app.services.research.contracts.errors import (
    ConfigurationError,
)

logger = get_logger(__name__)

_DOMAIN = "research"
_MIGRATION_ID = "001_research_artifacts_v1"
_EXPECTANCY_MIGRATION_ID = "002_research_expectancy_profiles_v1"
_GOVERNED_EVIDENCE_MIGRATION_ID = "003_research_governed_evidence_v1"
_RUN_STORE_MIGRATION_ID = "004_research_runs_v1"

_CREATE_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_artifacts ("
    "relative_path TEXT PRIMARY KEY, "
    "format TEXT NOT NULL, "
    "size_bytes INTEGER NOT NULL, "
    "sha256 TEXT NOT NULL, "
    "atomic INTEGER NOT NULL, "
    "schema_version TEXT NOT NULL, "
    "audit_event_id TEXT NOT NULL, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "correlation_id TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)

_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_artifacts_sha256 "
    "ON research_artifacts (sha256)"
)

_AUDIT_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_artifacts_audit "
    "ON research_artifacts (audit_event_id)"
)

_STATEMENTS = (_CREATE_STATEMENT, _INDEX_STATEMENT, _AUDIT_INDEX_STATEMENT)

# ``research_expectancy_profiles`` owns the approved-expectancy governance
# lifecycle (``OD-RES-01``). It replaces the brittle ``relative_path`` business
# key with a stable surrogate ``profile_id`` so Strategy's exact-version
# reference and Risk's eligibility lookup resolve to one authoritative row.
# Profiles are append-only lifecycle records: corrections advance
# ``governance_state`` to ``revoked``/``superseded`` rather than mutating or
# deleting history (settled decision: financial records are append-only).
_CREATE_EXPECTANCY_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_expectancy_profiles ("
    "profile_id TEXT PRIMARY KEY, "
    "exact_version TEXT NOT NULL, "
    "strategy_ref TEXT NOT NULL, "
    "hypothesis TEXT NOT NULL, "
    "match_keys_json TEXT NOT NULL CHECK (json_valid(match_keys_json)), "
    "envelope_json TEXT NOT NULL CHECK (json_valid(envelope_json)), "
    "governance_state TEXT NOT NULL CHECK (governance_state IN "
    "('draft','under_review','approved','suspended','expired','revoked')), "
    "reviewer TEXT NOT NULL DEFAULT '', "
    "decision TEXT NOT NULL DEFAULT '', "
    "reason TEXT NOT NULL DEFAULT '', "
    "superseded_by TEXT NOT NULL DEFAULT '', "
    "evidence_ref TEXT NOT NULL, "
    "canonical_hash TEXT NOT NULL, "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), "
    "updated_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), "
    "UNIQUE (exact_version)"
    ") STRICT"
)

_EXPECTANCY_MATCH_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_expectancy_strategy "
    "ON research_expectancy_profiles (strategy_ref, governance_state)"
)

_EXPECTANCY_STATEMENTS = (
    _CREATE_EXPECTANCY_STATEMENT,
    _EXPECTANCY_MATCH_INDEX_STATEMENT,
)

_CREATE_EXPECTANCY_TRANSITIONS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_expectancy_transitions ("
    "transition_id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "profile_id TEXT NOT NULL, "
    "source_state TEXT NOT NULL, "
    "target_state TEXT NOT NULL, "
    "reviewer TEXT NOT NULL, "
    "decision TEXT NOT NULL, "
    "reason TEXT NOT NULL, "
    "superseded_by TEXT NOT NULL DEFAULT '', "
    "request_id TEXT NOT NULL, "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), "
    "FOREIGN KEY (profile_id) REFERENCES research_expectancy_profiles(profile_id)"
    ") STRICT"
)
_CREATE_DRIFT_EVIDENCE_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_performance_drift_evidence ("
    "evidence_id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "profile_id TEXT NOT NULL, "
    "evidence_json TEXT NOT NULL CHECK (json_valid(evidence_json)), "
    "canonical_hash TEXT NOT NULL UNIQUE, "
    "request_id TEXT NOT NULL, "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)
_CREATE_STRESS_EVIDENCE_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_stress_scenario_evidence ("
    "scenario_id TEXT NOT NULL, "
    "canonical_hash TEXT NOT NULL, "
    "evidence_json TEXT NOT NULL CHECK (json_valid(evidence_json)), "
    "request_id TEXT NOT NULL, "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), "
    "PRIMARY KEY (scenario_id, canonical_hash)"
    ") STRICT"
)
_GOVERNED_EVIDENCE_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_drift_profile "
    "ON research_performance_drift_evidence (profile_id, evidence_id)"
)
_GOVERNED_EVIDENCE_STATEMENTS = (
    _CREATE_EXPECTANCY_TRANSITIONS_STATEMENT,
    _CREATE_DRIFT_EVIDENCE_STATEMENT,
    _CREATE_STRESS_EVIDENCE_STATEMENT,
    _GOVERNED_EVIDENCE_INDEX_STATEMENT,
)


# ``research_experiments``, ``research_runs``, and ``research_run_batches`` own
# the workbench ledger (``FEAT-API-26``). A Research run is expensive evidence,
# so it outlives the process that produced it: without these tables a restart
# would discard every experiment, run, and report while their artifacts stayed
# on disk with nothing pointing at them.
#
# Rows are principal-scoped and append-mostly: a run row is inserted when the
# run is queued and updated in place only as its own lifecycle advances.
_CREATE_EXPERIMENTS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_experiments ("
    "experiment_id TEXT PRIMARY KEY, "
    "principal_id TEXT NOT NULL, "
    "name TEXT NOT NULL, "
    "hypothesis TEXT NOT NULL, "
    "notes TEXT NOT NULL DEFAULT '', "
    "tags_json TEXT NOT NULL CHECK (json_valid(tags_json)), "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)

_CREATE_RUNS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_runs ("
    "run_id TEXT PRIMARY KEY, "
    "experiment_id TEXT NOT NULL, "
    "principal_id TEXT NOT NULL, "
    "batch_id TEXT NOT NULL DEFAULT '', "
    "status TEXT NOT NULL CHECK (status IN "
    "('queued','running','completed','failed','cancelled')), "
    "hypothesis TEXT NOT NULL, "
    "symbol TEXT NOT NULL, "
    "timeframe TEXT NOT NULL, "
    "preset TEXT NOT NULL, "
    "selected_stages_json TEXT NOT NULL "
    "CHECK (json_valid(selected_stages_json)), "
    "reason TEXT NOT NULL DEFAULT '', "
    "force_rerun INTEGER NOT NULL DEFAULT 0, "
    "request_json TEXT NOT NULL CHECK (json_valid(request_json)), "
    "report_json TEXT NOT NULL DEFAULT '' , "
    "dataset_json TEXT NOT NULL DEFAULT '', "
    "configuration_json TEXT NOT NULL DEFAULT '', "
    "artifacts_json TEXT NOT NULL DEFAULT '', "
    "error_json TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL, "
    "started_at TEXT NOT NULL DEFAULT '', "
    "completed_at TEXT NOT NULL DEFAULT '', "
    "FOREIGN KEY (experiment_id) REFERENCES research_experiments(experiment_id)"
    ") STRICT"
)

_CREATE_RUN_BATCHES_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS research_run_batches ("
    "batch_id TEXT PRIMARY KEY, "
    "experiment_id TEXT NOT NULL, "
    "principal_id TEXT NOT NULL, "
    "symbols_json TEXT NOT NULL CHECK (json_valid(symbols_json)), "
    "trigger TEXT NOT NULL, "
    "reason TEXT NOT NULL DEFAULT '', "
    "request_json TEXT NOT NULL CHECK (json_valid(request_json)), "
    "rejections_json TEXT NOT NULL CHECK (json_valid(rejections_json)), "
    "created_at TEXT NOT NULL"
    ") STRICT"
)

_EXPERIMENT_OWNER_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_experiments_owner "
    "ON research_experiments (principal_id, created_at)"
)

_RUN_OWNER_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_runs_owner "
    "ON research_runs (principal_id, created_at)"
)

_RUN_EXPERIMENT_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_runs_experiment "
    "ON research_runs (experiment_id, created_at)"
)

_RUN_BATCH_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_research_runs_batch ON research_runs (batch_id)"
)

_RUN_STORE_STATEMENTS = (
    _CREATE_EXPERIMENTS_STATEMENT,
    _CREATE_RUNS_STATEMENT,
    _CREATE_RUN_BATCHES_STATEMENT,
    _EXPERIMENT_OWNER_INDEX_STATEMENT,
    _RUN_OWNER_INDEX_STATEMENT,
    _RUN_EXPERIMENT_INDEX_STATEMENT,
    _RUN_BATCH_INDEX_STATEMENT,
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Compute a stable sha256 checksum over canonical joined statements.

    Args:
        statements: Ordered SQL statements.

    Returns:
        Lowercase hex digest.
    """
    material = "\n-- statement --\n".join(statements)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


RESEARCH_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_EXPECTANCY_MIGRATION_ID,
        checksum=_checksum(_EXPECTANCY_STATEMENTS),
        statements=_EXPECTANCY_STATEMENTS,
    ),
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_GOVERNED_EVIDENCE_MIGRATION_ID,
        checksum=_checksum(_GOVERNED_EVIDENCE_STATEMENTS),
        statements=_GOVERNED_EVIDENCE_STATEMENTS,
    ),
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_RUN_STORE_MIGRATION_ID,
        checksum=_checksum(_RUN_STORE_STATEMENTS),
        statements=_RUN_STORE_STATEMENTS,
    ),
)


def build_research_migration_request(request_id: str) -> object:
    """Return the deterministic Research-owned artifact metadata migration.

    Execution is delegated to Data's ``run_domain_migrations`` by callers.

    Args:
        request_id: Canonical ``req-`` prefixed request identifier.

    Returns:
        Validated ``MigrationRequest`` for the research domain.

    Raises:
        ConfigurationError: If the request id is invalid.
    """
    logger.info("Building Research artifact migration request")
    if not request_id or request_id != request_id.strip():
        raise ConfigurationError("RES_CONFIGURATION_INVALID", "INVALID_REQUEST_ID")
    return build_migration_request(
        domain=_DOMAIN,
        steps=RESEARCH_MIGRATION_STEPS,
        request_id=request_id,
    )


__all__ = (
    "RESEARCH_MIGRATION_STEPS",
    "build_research_migration_request",
)
