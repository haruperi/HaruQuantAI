"""Unit tests for Risk-owned migration definitions."""

import hashlib

from app.services.risk.audit import storage
from app.services.risk.migrations.definitions import _RISK_MIGRATION_STEPS

_RISK_TABLES = (
    "risk_policy_versions",
    "risk_audit_records",
    "risk_eligibility_decisions",
    "risk_allocation_decisions",
    "risk_kill_switch_states",
    "risk_approval_tokens",
    "risk_decision_snapshots",
)


def test_migration_definition_is_stable_and_complete() -> None:
    """Register one checksummed migration covering all Risk durable state."""
    assert len(_RISK_MIGRATION_STEPS) == 1
    step = _RISK_MIGRATION_STEPS[0]
    assert step.domain == "risk"
    assert step.migration_id == "risk-0001-initial-state"
    assert (
        step.checksum
        == hashlib.sha256("\n".join(step.statements).encode("utf-8")).hexdigest()
    )
    sql = " ".join(step.statements)
    for table in _RISK_TABLES:
        assert table in sql
    assert "active INTEGER NOT NULL CHECK (active IN (0, 1))" in sql


def test_every_risk_table_is_strict_and_audited() -> None:
    """Conform Risk tables to the authoritative schema model conventions."""
    statements = _RISK_MIGRATION_STEPS[0].statements
    creates = [s for s in statements if s.lstrip().upper().startswith("CREATE TABLE")]
    assert len(creates) == len(_RISK_TABLES)
    for statement in creates:
        assert statement.rstrip().endswith("STRICT")
        assert "created_at TEXT NOT NULL" in statement
        assert "request_id TEXT NOT NULL" in statement
        assert "correlation_id TEXT NOT NULL" in statement


def test_migration_defines_no_destructive_statement() -> None:
    """Keep Risk schema evolution additive."""
    sql = " ".join(_RISK_MIGRATION_STEPS[0].statements).upper()
    assert "DROP " not in sql
    assert "DELETE " not in sql
    assert "ALTER " not in sql


def test_private_storage_ports_have_no_public_exports() -> None:
    """Keep receiver-owned persistence protocols outside the public API."""
    assert storage.__all__ == []
