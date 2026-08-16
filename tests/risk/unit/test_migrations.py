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
    """Register ordered checksummed migrations covering all Risk durable state."""
    assert len(_RISK_MIGRATION_STEPS) == 4
    step1 = _RISK_MIGRATION_STEPS[0]
    assert step1.domain == "risk"
    assert step1.migration_id == "risk-0001-initial-state"
    assert (
        step1.checksum
        == hashlib.sha256("\n".join(step1.statements).encode("utf-8")).hexdigest()
    )
    sql1 = " ".join(step1.statements)
    for table in _RISK_TABLES:
        assert table in sql1
    assert "active INTEGER NOT NULL CHECK (active IN (0, 1))" in sql1

    step2 = _RISK_MIGRATION_STEPS[1]
    assert step2.domain == "risk"
    assert step2.migration_id == "risk-0002-schema-constraints"
    assert (
        step2.checksum
        == hashlib.sha256("\n".join(step2.statements).encode("utf-8")).hexdigest()
    )
    sql2 = " ".join(step2.statements)
    for table in _RISK_TABLES:
        assert f"{table}__new" in sql2
    assert "json_valid(payload_json)" in sql2
    assert "WHERE state = 'active'" in sql2
    assert "WHERE decision_id IS NOT NULL" in sql2

    step3 = _RISK_MIGRATION_STEPS[2]
    assert step3.domain == "risk"
    assert step3.migration_id == "risk-0003-route-vocabulary"
    assert (
        step3.checksum
        == hashlib.sha256("\n".join(step3.statements).encode("utf-8")).hexdigest()
    )
    assert "'demo'" in " ".join(step3.statements)

    step4 = _RISK_MIGRATION_STEPS[3]
    assert step4.domain == "risk"
    assert step4.migration_id == "risk-0004-manual-order-preflight"
    assert (
        step4.checksum
        == hashlib.sha256("\n".join(step4.statements).encode("utf-8")).hexdigest()
    )
    sql4 = " ".join(step4.statements)
    assert "risk_capacity_reservations" in sql4
    assert "risk_equity_history" in sql4
    assert sql4.count("STRICT") == 2


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


def test_migration_step_one_defines_no_destructive_statement() -> None:
    """Keep Risk step 0001 schema evolution additive."""
    sql = " ".join(_RISK_MIGRATION_STEPS[0].statements).upper()
    assert "DROP " not in sql
    assert "DELETE " not in sql
    assert "ALTER " not in sql


def test_private_storage_ports_have_no_public_exports() -> None:
    """Keep receiver-owned persistence protocols outside the public API."""
    assert storage.__all__ == []
