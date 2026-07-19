"""Unit tests for Risk-owned migration definitions."""

import hashlib

from app.services.risk.audit import storage
from app.services.risk.audit.migrations import _RISK_MIGRATION_STEPS


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
    for table in (
        "risk_policy_versions",
        "risk_audit_records",
        "risk_eligibility_decisions",
        "risk_allocation_decisions",
        "risk_kill_switch_states",
        "risk_approval_tokens",
        "risk_decision_snapshots",
    ):
        assert table in sql


def test_private_storage_ports_have_no_public_exports() -> None:
    """Keep receiver-owned persistence protocols outside the public API."""
    assert storage.__all__ == []
