"""Agentic-owned workflow-store schema definitions executed by Data.

Agentic declares its additive schema; Data owns migration execution, the
immutable ledger, checksums, and write locks. This module declares values only
— it opens no connection and executes nothing.

Conformed to the authoritative schema model in ``docs/schema`` (Domain 13). The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-AGT-001``.
"""

from __future__ import annotations

import hashlib

from app.services.data import build_migration_request, build_migration_step
from app.utils import get_logger

logger = get_logger(__name__)

_DOMAIN = "agentic"
_MIGRATION_ID = "001_agentic_workflow_v1"

_RUNS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_workflow_runs ("
    "run_id TEXT PRIMARY KEY, "
    "task_id TEXT NOT NULL, "
    "workflow_name TEXT NOT NULL, "
    "workflow_version TEXT NOT NULL, "
    "state TEXT NOT NULL, "
    "current_node TEXT NOT NULL, "
    "sequence INTEGER NOT NULL, "
    "revision INTEGER NOT NULL, "
    "attempts INTEGER NOT NULL, "
    "idempotency_key TEXT NOT NULL UNIQUE, "
    "created_at TEXT NOT NULL, "
    "updated_at TEXT NOT NULL, "
    "deadline_at TEXT NOT NULL, "
    "terminal_reason TEXT, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "correlation_id TEXT NOT NULL DEFAULT ''"
    ") STRICT"
)

_CHECKPOINTS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_workflow_checkpoints ("
    "checkpoint_id TEXT PRIMARY KEY, "
    "task_id TEXT NOT NULL, "
    "workflow_name TEXT NOT NULL, "
    "workflow_version TEXT NOT NULL, "
    "node_id TEXT NOT NULL, "
    "sequence INTEGER NOT NULL, "
    "state TEXT NOT NULL, "
    "expected_version INTEGER NOT NULL, "
    "state_payload_hash TEXT NOT NULL, "
    "canonical_hash TEXT NOT NULL, "
    "contract_version TEXT NOT NULL, "
    "request_id TEXT NOT NULL, "
    "workflow_id TEXT NOT NULL, "
    "causation_id TEXT, "
    "schema_id TEXT NOT NULL, "
    "created_at TEXT NOT NULL, "
    "correlation_id TEXT NOT NULL DEFAULT ''"
    ") STRICT"
)

_RUNS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_workflow_runs_task "
    "ON agentic_workflow_runs (task_id)"
)

_CHECKPOINTS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_workflow_checkpoints_task "
    "ON agentic_workflow_checkpoints (task_id, sequence)"
)

_STATEMENTS: tuple[str, ...] = (
    _RUNS_STATEMENT,
    _CHECKPOINTS_STATEMENT,
    _RUNS_INDEX_STATEMENT,
    _CHECKPOINTS_INDEX_STATEMENT,
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


AGENTIC_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def get_agentic_migration_statements() -> tuple[str, ...]:
    """Return the ordered Agentic workflow-store statements.

    Returns:
        Ordered additive schema statements.
    """
    return _STATEMENTS


def build_agentic_migration_request(request_id: str) -> object:
    """Return the deterministic Agentic-owned workflow-store migration.

    Execution is delegated to Data's `run_domain_migrations` by an approved
    composition root; Agentic never executes a migration itself.

    Args:
        request_id: Canonical `req-` prefixed request identifier.

    Returns:
        A validated migration request for the agentic domain.
    """
    logger.debug("Building the Agentic workflow-store migration request")
    request: object = build_migration_request(
        domain=_DOMAIN,
        steps=AGENTIC_MIGRATION_STEPS,
        request_id=request_id,
    )
    return request
