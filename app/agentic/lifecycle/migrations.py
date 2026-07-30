"""Agentic-owned lifecycle-ledger schema definitions executed by Data.

Agentic declares its additive schema; Data owns migration execution, the
immutable ledger, checksums, and write locks. This module declares values only
— it opens no connection and executes nothing.

The transition table is what makes `FR-AGENTIC-054`'s append-only rule
enforceable across processes. Its composite primary key is
`(artifact_hash, sequence)`: a second write at a position already recorded is
rejected by the store rather than by a convention, so history cannot be
rewritten by a later process that never saw the earlier one. Keying on the
artefact **digest** rather than its identifier is what makes state
non-inheritable — a materially changed artefact has a different digest and
therefore an empty history.
"""

from __future__ import annotations

import hashlib

from app.services.data import build_migration_request, build_migration_step
from app.utils import get_logger

logger = get_logger(__name__)

_DOMAIN = "agentic"
_MIGRATION_ID = "003_agentic_lifecycle_v1"

# One row per transition. The composite primary key is the enforcement point:
# an artefact's history is append-only because position `n` can be written once.
_TRANSITIONS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_lifecycle_transitions ("
    "artifact_hash TEXT NOT NULL, "
    "sequence INTEGER NOT NULL, "
    "record_id TEXT NOT NULL UNIQUE, "
    "artifact_id TEXT NOT NULL, "
    "previous_state TEXT, "
    "state TEXT NOT NULL, "
    "packet_hash TEXT, "
    "termination_reason TEXT, "
    "actor_id TEXT NOT NULL, "
    "rationale TEXT NOT NULL, "
    "recorded_at TEXT NOT NULL, "
    "PRIMARY KEY (artifact_hash, sequence)"
    ")"
)

_PACKETS_STATEMENT = (
    "CREATE TABLE IF NOT EXISTS agentic_promotion_packets ("
    "packet_hash TEXT PRIMARY KEY, "
    "packet_id TEXT NOT NULL, "
    "task_id TEXT NOT NULL, "
    "artifact_hash TEXT NOT NULL, "
    "simulation_manifest_ref TEXT NOT NULL, "
    "lifetime_trial_ceiling INTEGER NOT NULL, "
    "approver_id TEXT NOT NULL, "
    "approval_environment TEXT NOT NULL, "
    "assembled_at TEXT NOT NULL"
    ")"
)

_TRANSITIONS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_lifecycle_transitions_state "
    "ON agentic_lifecycle_transitions (artifact_hash, state)"
)

_PACKETS_INDEX_STATEMENT = (
    "CREATE INDEX IF NOT EXISTS idx_agentic_promotion_packets_artifact "
    "ON agentic_promotion_packets (artifact_hash)"
)

_STATEMENTS: tuple[str, ...] = (
    _TRANSITIONS_STATEMENT,
    _PACKETS_STATEMENT,
    _TRANSITIONS_INDEX_STATEMENT,
    _PACKETS_INDEX_STATEMENT,
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


AGENTIC_LIFECYCLE_MIGRATION_STEPS: tuple[object, ...] = (
    build_migration_step(
        domain=_DOMAIN,
        migration_id=_MIGRATION_ID,
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def get_lifecycle_migration_statements() -> tuple[str, ...]:
    """Return the ordered Agentic lifecycle-ledger statements.

    Returns:
        Ordered additive schema statements.
    """
    return _STATEMENTS


def build_lifecycle_migration_request(request_id: str) -> object:
    """Return the deterministic Agentic-owned lifecycle-ledger migration.

    Execution is delegated to Data's `run_domain_migrations` by an approved
    composition root; Agentic never executes a migration itself.

    Args:
        request_id: Canonical `req-` prefixed request identifier.

    Returns:
        A validated migration request for the agentic domain.
    """
    logger.debug("Building the Agentic lifecycle-ledger migration request")
    request: object = build_migration_request(
        domain=_DOMAIN,
        steps=AGENTIC_LIFECYCLE_MIGRATION_STEPS,
        request_id=request_id,
    )
    return request
