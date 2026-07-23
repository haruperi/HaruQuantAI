"""Risk-owned migration definitions executed by Data infrastructure."""

import hashlib

from app.services.data.persistence.contracts import (
    MigrationStep,
)
from app.utils import logger

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS risk_policy_versions (
        config_hash TEXT PRIMARY KEY,
        policy_version TEXT NOT NULL,
        profile TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        effective_at TEXT NOT NULL
    )""",
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
        correlation_id TEXT NOT NULL
    )""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_audit_decision "
        "ON risk_audit_records(decision_id)"
    ),
    """CREATE TABLE IF NOT EXISTS risk_eligibility_decisions (
        decision_id TEXT PRIMARY KEY,
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS risk_allocation_decisions (
        decision_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        reviewed_version TEXT NOT NULL,
        active INTEGER NOT NULL,
        predecessor_version TEXT,
        payload_json TEXT NOT NULL,
        UNIQUE(portfolio_id, reviewed_version)
    )""",
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
        payload_json TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS risk_approval_tokens (
        token_id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        scope_json TEXT NOT NULL,
        state TEXT NOT NULL,
        reservation_id TEXT,
        expires_at TEXT NOT NULL,
        payload_json TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS risk_decision_snapshots (
        record_id TEXT PRIMARY KEY,
        record_type TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL
    )""",
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
    MigrationStep(
        domain="risk",
        migration_id="risk-0001-initial-state",
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
)

__all__: list[str] = []
