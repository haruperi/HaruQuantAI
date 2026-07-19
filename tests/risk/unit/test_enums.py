"""Unit tests for the stable Risk enum vocabulary."""

from app.services.risk.contracts import DecisionState, LimitStatus


def test_decision_state_values_are_stable() -> None:
    """Keep the decision-state wire values exact and ordered."""
    assert tuple(item.value for item in DecisionState) == (
        "approve",
        "warn",
        "needs_approval",
        "needs_more_evidence",
        "reject",
        "block",
        "error",
    )


def test_limit_status_values_are_stable() -> None:
    """Keep the limit-status wire values exact and ordered."""
    assert tuple(item.value for item in LimitStatus) == (
        "pass",
        "warn",
        "needs_more_evidence",
        "fail",
        "blocked",
    )
