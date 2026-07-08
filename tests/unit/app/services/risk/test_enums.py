"""Unit tests for Risk Governance enums and catalogs."""

from app.services.risk.models.enums import (
    KillSwitchReason,
    KillSwitchStateEnum,
    RiskAction,
    RiskDecisionStatus,
    RiskMode,
    RiskReasonCode,
    RiskSeverity,
    list_risk_reason_codes,
    risk_severity_rank,
)


def test_decision_status_values() -> None:
    """Test RiskDecisionStatus enum values."""
    assert RiskDecisionStatus.APPROVE.value == "approve"
    assert RiskDecisionStatus.REJECT.value == "reject"
    assert RiskDecisionStatus.BLOCK.value == "block"


def test_modes_and_actions() -> None:
    """Test RiskMode and RiskAction enum values."""
    assert RiskMode.PAPER.value == "paper"
    assert RiskMode.FULL_LIVE.value == "full_live"
    assert RiskAction.EXECUTE_TRADE.value == "execute_trade"


def test_reason_code_descriptions() -> None:
    """Test RiskReasonCode descriptions."""
    assert RiskReasonCode.OK.description == "Evaluation passed successfully."
    assert "news" in RiskReasonCode.NEWS_BLACKOUT.description.lower()


def test_list_reason_codes() -> None:
    """Test list_risk_reason_codes helper function."""
    codes = list_risk_reason_codes()
    assert isinstance(codes, tuple)
    assert len(codes) > 0
    assert RiskReasonCode.OK in codes


def test_severity_ranks() -> None:
    """Test risk_severity_rank mapping logic."""
    assert risk_severity_rank(RiskSeverity.INFO) == 0
    assert risk_severity_rank(RiskSeverity.EMERGENCY_HALT) == 5
    assert risk_severity_rank("unknown_severity") == -1  # type: ignore[arg-type]


def test_kill_switch_enums() -> None:
    """Test KillSwitchStateEnum and KillSwitchReason."""
    assert KillSwitchStateEnum.ACTIVE.value == "active"
    assert KillSwitchReason.MANUAL_HALT.value == "manual_halt"
