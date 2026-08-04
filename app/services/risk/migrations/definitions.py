"""Risk-owned migration definitions executed by Data infrastructure.

Conformed to the authoritative schema model in ``docs/schema`` (Domain 6). The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-RISK-069`` through
``FR-RISK-072``.

The model adopts the live table names and the eligibility/allocation split
rather than the reverse: eligibility ("may this strategy trade at all?") and
allocation ("how much budget does this portfolio get?") are answered by
different authorities on different cadences, and collapsing them would lose a
real distinction.
"""

import hashlib

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)
from app.utils import get_logger

logger = get_logger(__name__)

RISK_SCHEMA_VERSION = "v1"

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS risk_policy_versions (
        config_hash TEXT PRIMARY KEY,
        policy_version TEXT NOT NULL,
        profile TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        effective_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_policy_profile "
        "ON risk_policy_versions(profile, effective_at DESC)"
    ),
    """CREATE TABLE IF NOT EXISTS risk_audit_records (
        record_id TEXT PRIMARY KEY,
        sequence INTEGER NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        evidence_refs_json TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        decision_id TEXT,
        occurred_at TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        record_hash TEXT NOT NULL UNIQUE,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_audit_decision "
        "ON risk_audit_records(decision_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_audit_seq "
        "ON risk_audit_records(sequence DESC)"
    ),
    """CREATE TABLE IF NOT EXISTS risk_eligibility_decisions (
        decision_id TEXT PRIMARY KEY,
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_eligibility_strategy "
        "ON risk_eligibility_decisions(strategy_id, strategy_version)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_eligibility_expiry "
        "ON risk_eligibility_decisions(expires_at)"
    ),
    """CREATE TABLE IF NOT EXISTS risk_allocation_decisions (
        decision_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        reviewed_version TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        predecessor_version TEXT,
        payload_json TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(portfolio_id, reviewed_version)
    ) STRICT""",
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_risk_allocation_active "
        "ON risk_allocation_decisions(portfolio_id) WHERE active = 1"
    ),
    """CREATE TABLE IF NOT EXISTS risk_kill_switch_states (
        state_id TEXT PRIMARY KEY,
        scope_level TEXT NOT NULL,
        scope_json TEXT NOT NULL,
        state TEXT NOT NULL,
        version INTEGER NOT NULL,
        payload_json TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_kill_tripped "
        "ON risk_kill_switch_states(scope_level) WHERE state = 'tripped'"
    ),
    """CREATE TABLE IF NOT EXISTS risk_approval_tokens (
        token_id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        scope_json TEXT NOT NULL,
        state TEXT NOT NULL,
        reservation_id TEXT,
        expires_at TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_tokens_open "
        "ON risk_approval_tokens(expires_at) "
        "WHERE state IN ('issued', 'reserved')"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_tokens_decision "
        "ON risk_approval_tokens(decision_id)"
    ),
    """CREATE TABLE IF NOT EXISTS risk_decision_snapshots (
        record_id TEXT PRIMARY KEY,
        record_type TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_snapshots_config "
        "ON risk_decision_snapshots(config_hash, occurred_at DESC)"
    ),
)


def _checksum(statements: tuple[str, ...]) -> str:
    """Calculate the deterministic migration checksum.

    Args:
        statements: Ordered SQL statements.

    Returns:
        SHA-256 checksum.
    """
    logger.debug("Calculating Risk migration definition checksum")
    return hashlib.sha256("\n".join(statements).encode("utf-8")).hexdigest()


_RISK_MIGRATION_STEPS = (
    build_migration_step(
        domain="risk",
        migration_id="risk-0001-initial-state",
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)


def run_risk_migrations(request_id: str) -> object:
    """Apply the immutable Risk migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    logger.info("Running Risk-owned schema migrations")
    request = build_migration_request(
        domain="risk",
        steps=_RISK_MIGRATION_STEPS,
        request_id=request_id,
    )
    return run_domain_migrations(request)


__all__ = ("run_risk_migrations",)
