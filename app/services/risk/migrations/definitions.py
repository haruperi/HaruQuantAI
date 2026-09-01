"""Risk-owned migration definitions executed by Data infrastructure.

Conformed to the authoritative schema model in ``app/services/risk/README.md``. The
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

from app.composition.logging import get_logger
from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)

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


_STATEMENTS_0002 = (
    """CREATE TABLE risk_policy_versions__new (
        config_hash TEXT PRIMARY KEY,
        policy_version TEXT NOT NULL,
        profile TEXT NOT NULL CHECK (
            profile IN ('research', 'simulation', 'paper', 'live')
        ),
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        effective_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_policy_versions__new (
        config_hash, policy_version, profile, payload_json,
        effective_at, request_id, correlation_id, created_at, updated_at
    ) SELECT config_hash, policy_version, profile, payload_json,
        effective_at, request_id, correlation_id, created_at, updated_at
    FROM risk_policy_versions""",
    "DROP TABLE risk_policy_versions",
    "ALTER TABLE risk_policy_versions__new RENAME TO risk_policy_versions",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_policy_profile "
        "ON risk_policy_versions(profile, effective_at DESC)"
    ),
    """CREATE TABLE risk_audit_records__new (
        record_id TEXT PRIMARY KEY,
        sequence INTEGER NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        evidence_refs_json TEXT NOT NULL CHECK (json_valid(evidence_refs_json)),
        config_hash TEXT NOT NULL,
        decision_id TEXT,
        occurred_at TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        record_hash TEXT NOT NULL UNIQUE,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_audit_records__new (
        record_id, sequence, event_type, payload_json, evidence_refs_json,
        config_hash, decision_id, occurred_at, previous_hash, record_hash,
        request_id, correlation_id, created_at
    ) SELECT record_id, sequence, event_type, payload_json, evidence_refs_json,
        config_hash, decision_id, occurred_at, previous_hash, record_hash,
        request_id, correlation_id, created_at
    FROM risk_audit_records""",
    "DROP TABLE risk_audit_records",
    "ALTER TABLE risk_audit_records__new RENAME TO risk_audit_records",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_audit_decision "
        "ON risk_audit_records(decision_id) WHERE decision_id IS NOT NULL"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_audit_seq "
        "ON risk_audit_records(sequence DESC)"
    ),
    """CREATE TABLE risk_eligibility_decisions__new (
        decision_id TEXT PRIMARY KEY,
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        expires_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_eligibility_decisions__new (
        decision_id, strategy_id, strategy_version, payload_json,
        expires_at, request_id, correlation_id, created_at
    ) SELECT decision_id, strategy_id, strategy_version, payload_json,
        expires_at, request_id, correlation_id, created_at
    FROM risk_eligibility_decisions""",
    "DROP TABLE risk_eligibility_decisions",
    "ALTER TABLE risk_eligibility_decisions__new RENAME TO risk_eligibility_decisions",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_eligibility_strategy "
        "ON risk_eligibility_decisions(strategy_id, strategy_version)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_eligibility_expiry "
        "ON risk_eligibility_decisions(expires_at)"
    ),
    """CREATE TABLE risk_allocation_decisions__new (
        decision_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        reviewed_version TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        predecessor_version TEXT,
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(portfolio_id, reviewed_version)
    ) STRICT""",
    """INSERT INTO risk_allocation_decisions__new (
        decision_id, portfolio_id, reviewed_version, active,
        predecessor_version, payload_json, request_id, correlation_id, created_at
    ) SELECT decision_id, portfolio_id, reviewed_version, active,
        predecessor_version, payload_json, request_id, correlation_id, created_at
    FROM risk_allocation_decisions""",
    "DROP TABLE risk_allocation_decisions",
    "ALTER TABLE risk_allocation_decisions__new RENAME TO risk_allocation_decisions",
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_risk_allocation_active "
        "ON risk_allocation_decisions(portfolio_id) WHERE active = 1"
    ),
    """CREATE TABLE risk_kill_switch_states__new (
        state_id TEXT PRIMARY KEY,
        scope_level TEXT NOT NULL CHECK (
            scope_level IN ('global', 'portfolio', 'strategy', 'symbol')
        ),
        scope_json TEXT NOT NULL CHECK (json_valid(scope_json)),
        state TEXT NOT NULL CHECK (state IN ('active', 'inactive')),
        version INTEGER NOT NULL,
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_kill_switch_states__new (
        state_id, scope_level, scope_json, state, version, payload_json,
        request_id, correlation_id, created_at, updated_at
    ) SELECT state_id, scope_level, scope_json, state, version, payload_json,
        request_id, correlation_id, created_at, updated_at
    FROM risk_kill_switch_states""",
    "DROP TABLE risk_kill_switch_states",
    "ALTER TABLE risk_kill_switch_states__new RENAME TO risk_kill_switch_states",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_kill_tripped "
        "ON risk_kill_switch_states(scope_level) WHERE state = 'active'"
    ),
    """CREATE TABLE risk_approval_tokens__new (
        token_id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        scope_json TEXT NOT NULL CHECK (json_valid(scope_json)),
        state TEXT NOT NULL CHECK (
            state IN ('issued', 'reserved', 'consumed', 'expired', 'revoked')
        ),
        reservation_id TEXT,
        expires_at TEXT NOT NULL,
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_approval_tokens__new (
        token_id, decision_id, scope_json, state, reservation_id, expires_at,
        payload_json, request_id, correlation_id, created_at, updated_at
    ) SELECT token_id, decision_id, scope_json, state, reservation_id, expires_at,
        payload_json, request_id, correlation_id, created_at, updated_at
    FROM risk_approval_tokens""",
    "DROP TABLE risk_approval_tokens",
    "ALTER TABLE risk_approval_tokens__new RENAME TO risk_approval_tokens",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_tokens_open "
        "ON risk_approval_tokens(expires_at) "
        "WHERE state IN ('issued', 'reserved')"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_tokens_decision "
        "ON risk_approval_tokens(decision_id)"
    ),
    """CREATE TABLE risk_decision_snapshots__new (
        record_id TEXT PRIMARY KEY,
        record_type TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        occurred_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_decision_snapshots__new (
        record_id, record_type, config_hash, payload_json, occurred_at,
        request_id, correlation_id, created_at
    ) SELECT record_id, record_type, config_hash, payload_json, occurred_at,
        request_id, correlation_id, created_at
    FROM risk_decision_snapshots""",
    "DROP TABLE risk_decision_snapshots",
    "ALTER TABLE risk_decision_snapshots__new RENAME TO risk_decision_snapshots",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_snapshots_config "
        "ON risk_decision_snapshots(config_hash, occurred_at DESC)"
    ),
)

_STATEMENTS_0003 = (
    """CREATE TABLE risk_policy_versions__route_vocabulary (
        config_hash TEXT PRIMARY KEY,
        policy_version TEXT NOT NULL,
        profile TEXT NOT NULL CHECK (
            profile IN ('research', 'simulation', 'demo', 'live')
        ),
        payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
        effective_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    """INSERT INTO risk_policy_versions__route_vocabulary (
        config_hash, policy_version, profile, payload_json,
        effective_at, request_id, correlation_id, created_at, updated_at
    ) SELECT config_hash, policy_version,
        CASE profile WHEN 'paper' THEN 'demo' ELSE profile END,
        CASE
            WHEN profile = 'paper' THEN replace(payload_json, '"paper"', '"demo"')
            ELSE payload_json
        END,
        effective_at, request_id, correlation_id, created_at, updated_at
    FROM risk_policy_versions""",
    "DROP TABLE risk_policy_versions",
    (
        "ALTER TABLE risk_policy_versions__route_vocabulary "
        "RENAME TO risk_policy_versions"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_policy_profile "
        "ON risk_policy_versions(profile, effective_at DESC)"
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


_STATEMENTS_0004 = (
    """CREATE TABLE IF NOT EXISTS risk_capacity_reservations (
        reservation_key TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        strategy_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        requested_notional TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_capacity_expiry "
        "ON risk_capacity_reservations(expires_at)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_risk_capacity_scope "
        "ON risk_capacity_reservations(account_id, strategy_id, symbol)"
    ),
    """CREATE TABLE IF NOT EXISTS risk_equity_history (
        account_id TEXT PRIMARY KEY,
        inception_equity TEXT NOT NULL,
        peak_equity TEXT NOT NULL,
        day_start_equity TEXT NOT NULL,
        day_start_date TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT""",
)


_RISK_MIGRATION_STEPS = (
    build_migration_step(
        domain="risk",
        migration_id="risk-0001-initial-state",
        checksum=_checksum(_STATEMENTS),
        statements=_STATEMENTS,
    ),
    build_migration_step(
        domain="risk",
        migration_id="risk-0002-schema-constraints",
        checksum=_checksum(_STATEMENTS_0002),
        statements=_STATEMENTS_0002,
    ),
    build_migration_step(
        domain="risk",
        migration_id="risk-0003-route-vocabulary",
        checksum=_checksum(_STATEMENTS_0003),
        statements=_STATEMENTS_0003,
    ),
    build_migration_step(
        domain="risk",
        migration_id="risk-0004-manual-order-preflight",
        checksum=_checksum(_STATEMENTS_0004),
        statements=_STATEMENTS_0004,
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
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = ("run_risk_migrations",)
