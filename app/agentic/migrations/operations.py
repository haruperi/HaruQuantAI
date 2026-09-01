"""Agentic-owned operations schema definitions executed by Data.

Conformed to the authoritative schema model in ``app/agentic/README.md``. The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-AGT-004``.
"""

from __future__ import annotations

import hashlib

from app.composition.logging import get_logger
from app.services.data import build_migration_request, build_migration_step

logger = get_logger(__name__)

_DOMAIN = "agentic"
_MIGRATION_ID = "004_agentic_operations_v1"

# One row per assembled trace. Keyed on the trace digest so an assembly of the
# same evidence is the same row rather than a duplicate view of it.
_TRACES_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_operations_traces ("
    "trace_hash TEXT PRIMARY KEY, "
    "trace_id TEXT NOT NULL, "
    "correlation_id TEXT NOT NULL, "
    "task_id TEXT NOT NULL, "
    "run_id TEXT NOT NULL, "
    "spans_json TEXT NOT NULL, "
    "redacted_paths_json TEXT NOT NULL, "
    "record_count INTEGER NOT NULL, "
    "observed_cost TEXT NOT NULL, "
    "assembled_at TEXT NOT NULL, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)

# One classified incident per kind per correlated run. The unique constraint is
# the enforcement point: a second containment cannot quietly replace the first
# and its evidence.
_INCIDENTS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_operations_incidents ("
    "incident_id TEXT PRIMARY KEY, "
    "task_id TEXT NOT NULL, "
    "run_id TEXT NOT NULL, "
    "correlation_id TEXT NOT NULL, "
    "kind TEXT NOT NULL, "
    "trigger TEXT NOT NULL, "
    "containment_action TEXT NOT NULL, "
    "contained_state TEXT NOT NULL, "
    "quarantined_role_id TEXT, "
    "checkpoint_ref TEXT NOT NULL, "
    "preserved_evidence_refs_json TEXT NOT NULL, "
    "detected_at TEXT NOT NULL, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), "
    "UNIQUE (run_id, correlation_id, kind)"
    ") STRICT"
)

_REPLAYS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_operations_replays ("
    "replay_id TEXT PRIMARY KEY, "
    "run_id TEXT NOT NULL, "
    "task_id TEXT NOT NULL, "
    "environment TEXT NOT NULL, "
    "requested_by TEXT NOT NULL, "
    "requested_at TEXT NOT NULL, "
    "verified_references_json TEXT NOT NULL, "
    "side_effects_attempted INTEGER NOT NULL, "
    "executed INTEGER NOT NULL, "
    "completed_at TEXT NOT NULL, "
    "request_id TEXT NOT NULL DEFAULT '', "
    "correlation_id TEXT NOT NULL DEFAULT '', "
    "created_at TEXT NOT NULL DEFAULT "
    "(strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
    ") STRICT"
)

_INCIDENTS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_operations_incidents_run "
    "ON agentic_operations_incidents (run_id, kind)"
)

_TRACES_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_operations_traces_correlation "
    "ON agentic_operations_traces (correlation_id)"
)

_STATEMENTS: tuple[str, ...] = (
    _TRACES_STATEMENT,
    _INCIDENTS_STATEMENT,
    _REPLAYS_STATEMENT,
    _INCIDENTS_INDEX_STATEMENT,
    _TRACES_INDEX_STATEMENT,
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


AGENTIC_OPERATIONS_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def get_operations_migration_statements() -> tuple[str, ...]:
    """Return the ordered Agentic operations statements.

    Returns:
        Ordered additive schema statements.
    """
    return _STATEMENTS


def build_operations_migration_request(request_id: str) -> object:
    """Return the deterministic Agentic-owned operations migration.

    Args:
        request_id: Canonical `req-` prefixed request identifier.

    Returns:
        A validated migration request for the agentic domain.
    """
    logger.debug("Building the Agentic operations migration request")
    request: object = build_migration_request(
        domain=_DOMAIN,
        steps=AGENTIC_OPERATIONS_MIGRATION_STEPS,
        request_id=request_id,
    )
    return request
