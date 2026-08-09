"""Unit tests for no-trade success-state classification."""

from datetime import UTC, datetime

from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.no_trade_state import (
    build_no_trade_outcome,
    classify_no_trade_outcome,
    parse_no_trade_outcome,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_build_and_parse_round_trip() -> None:
    """Round-trip a NoTradeOutcome v1 mapping through build/parse."""
    built = build_no_trade_outcome(
        decision_id="decision-1",
        outcome_kind="safe_stand_down",
        failed_rule_ids=("kill_switch",),
        rationale="mandatory gate",
        evaluated_at=NOW,
    )
    parsed = parse_no_trade_outcome(built)
    assert parsed["schema_id"] == "risk.no_trade_outcome.v1"
    assert parsed["outcome_kind"] == "safe_stand_down"


def test_all_mandatory_failures_classify_as_safe_stand_down() -> None:
    """Classify a rejection driven only by mandatory gates as a safe stand-down."""
    outcome = unwrap_risk_response(
        classify_no_trade_outcome(
            "decision-1", ["kill_switch", "drawdown_state"], now=NOW
        ),
        operation="classify_no_trade_outcome",
    )
    assert outcome["outcome_kind"] == "safe_stand_down"


def test_avoidable_execution_failure_classifies_as_failed_gameplay() -> None:
    """Classify a rejection with an avoidable stop-placement mistake as failed gameplay."""
    outcome = unwrap_risk_response(
        classify_no_trade_outcome(
            "decision-1", ["kill_switch", "stop_noise_distance"], now=NOW
        ),
        operation="classify_no_trade_outcome",
    )
    assert outcome["outcome_kind"] == "failed_gameplay"


def test_unregistered_rule_fails_closed_to_failed_gameplay() -> None:
    """Fail closed to failed gameplay for an unregistered failed rule identity."""
    outcome = unwrap_risk_response(
        classify_no_trade_outcome("decision-1", ["unregistered_rule"], now=NOW),
        operation="classify_no_trade_outcome",
    )
    assert outcome["outcome_kind"] == "failed_gameplay"


def test_empty_failed_rules_fails_validation() -> None:
    """Reject classification with no supplied failed rule identities."""
    response = classify_no_trade_outcome("decision-1", [], now=NOW)
    assert response.status == "error"
