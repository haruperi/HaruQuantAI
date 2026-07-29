"""Agentic-owned experiment-ledger schema definitions executed by Data.

Agentic declares its additive schema; Data owns migration execution, the
immutable ledger, checksums, and write locks. This module declares values only
— it opens no connection and executes nothing.

The holdout table is what makes `FR-AGENTIC-040`'s scarcity rule enforceable
across processes: its unique constraint on the protocol digest is the record
that a thesis's one look at holdout has been spent.
"""

from __future__ import annotations

import hashlib

from app.services.data import build_migration_request, build_migration_step
from app.utils import get_logger

logger = get_logger(__name__)

_DOMAIN = "agentic"
_MIGRATION_ID = "002_agentic_experiment_v1"

_SPECS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_experiment_specs ("
    "spec_id TEXT PRIMARY KEY, "
    "task_id TEXT NOT NULL, "
    "thesis_id TEXT NOT NULL, "
    "spec_hash TEXT NOT NULL UNIQUE, "
    "seed INTEGER NOT NULL, "
    "embargo_seconds INTEGER NOT NULL, "
    "baseline_ref TEXT NOT NULL, "
    "cost_model_ref TEXT NOT NULL, "
    "falsification_outcome TEXT NOT NULL, "
    "created_at TEXT NOT NULL"
    ")"
)

_RUNS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_experiment_runs ("
    "run_id TEXT PRIMARY KEY, "
    "spec_hash TEXT NOT NULL, "
    "task_id TEXT NOT NULL, "
    "evidence_class TEXT NOT NULL, "
    "request_hash TEXT NOT NULL, "
    "config_hash TEXT NOT NULL, "
    "engine_version TEXT NOT NULL, "
    "journal_ref TEXT NOT NULL, "
    "artifact_manifest_ref TEXT NOT NULL, "
    "created_at TEXT NOT NULL"
    ")"
)

# One row per protocol. The unique constraint is the enforcement point: a
# second look at holdout for the same pre-registered protocol cannot be
# recorded, so it cannot be performed.
_HOLDOUT_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_experiment_holdout_use ("
    "spec_hash TEXT PRIMARY KEY, "
    "task_id TEXT NOT NULL, "
    "run_id TEXT NOT NULL, "
    "consumed_at TEXT NOT NULL"
    ")"
)

_VERDICTS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_experiment_verdicts ("
    "verdict_id TEXT PRIMARY KEY, "
    "spec_id TEXT NOT NULL, "
    "spec_hash TEXT NOT NULL, "
    "task_id TEXT NOT NULL, "
    "outcome TEXT NOT NULL, "
    "holdout_consumed INTEGER NOT NULL, "
    "canonical_hash TEXT NOT NULL, "
    "created_at TEXT NOT NULL"
    ")"
)

_RUNS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_experiment_runs_spec "
    "ON agentic_experiment_runs (spec_hash, evidence_class)"
)

_VERDICTS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_experiment_verdicts_spec "
    "ON agentic_experiment_verdicts (spec_hash)"
)

_STATEMENTS: tuple[str, ...] = (
    _SPECS_STATEMENT,
    _RUNS_STATEMENT,
    _HOLDOUT_STATEMENT,
    _VERDICTS_STATEMENT,
    _RUNS_INDEX_STATEMENT,
    _VERDICTS_INDEX_STATEMENT,
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Compute a stable digest over canonical joined statements.

    Args:
        statements: Ordered SQL statements.

    Returns:
        Lowercase hexadecimal digest.
    """
    material = "\n-- statement --\n".join(statements)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


AGENTIC_EXPERIMENT_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def get_experiment_migration_statements() -> tuple[str, ...]:
    """Return the ordered Agentic experiment-ledger statements.

    Returns:
        Ordered additive schema statements.
    """
    return _STATEMENTS


def build_experiment_migration_request(request_id: str) -> object:
    """Return the deterministic Agentic-owned experiment-ledger migration.

    Execution is delegated to Data's `run_domain_migrations` by an approved
    composition root; Agentic never executes a migration itself.

    Args:
        request_id: Canonical `req-` prefixed request identifier.

    Returns:
        A validated migration request for the agentic domain.
    """
    logger.debug("Building the Agentic experiment-ledger migration request")
    request: object = build_migration_request(
        domain=_DOMAIN,
        steps=AGENTIC_EXPERIMENT_MIGRATION_STEPS,
        request_id=request_id,
    )
    return request
