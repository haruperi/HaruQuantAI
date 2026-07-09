"""Unit tests for shared gate step contracts."""

from __future__ import annotations

import pytest
from app.services.trading.gates._common import (
    GateName,
    GateStepResult,
    GateStepStatus,
    blocked_step,
    diagnostic_skipped_step,
    passed_step,
)


def test_gate_step_result_requires_reason_code_when_blocked() -> None:
    """A blocked gate step result must carry a reason code."""
    with pytest.raises(ValueError, match="reason_code"):
        GateStepResult(gate=GateName.COMPLIANCE, status=GateStepStatus.BLOCKED)


def test_gate_step_result_allows_blocked_with_reason_code() -> None:
    """A blocked gate step result with a reason code is valid."""
    result = GateStepResult(
        gate=GateName.COMPLIANCE,
        status=GateStepStatus.BLOCKED,
        reason_code="POLICY_BLOCKED",
    )
    assert result.reason_code == "POLICY_BLOCKED"


def test_passed_step_builder() -> None:
    """passed_step builds a passing gate step result."""
    result = passed_step(gate=GateName.LOCAL_SCHEMA_VALIDATION)
    assert result.status is GateStepStatus.PASSED
    assert result.reason_code is None


def test_blocked_step_builder() -> None:
    """blocked_step builds a blocking gate step result with a reason code."""
    result = blocked_step(
        gate=GateName.COMPLIANCE, reason_code="POLICY_BLOCKED", message="restricted"
    )
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "POLICY_BLOCKED"


def test_diagnostic_skipped_step_builder() -> None:
    """diagnostic_skipped_step marks the gate as diagnostic-only (TRD-FR-087)."""
    result = diagnostic_skipped_step(gate=GateName.MARKET_TURBULENCE)
    assert result.status is GateStepStatus.SKIPPED
    assert result.diagnostic_after_failure is True
    assert result.mutates_state is False
    assert result.calls_broker is False
    assert result.requires_network is False
