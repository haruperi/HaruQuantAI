"""Tests for Optimization robustness assessment."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.robustness import assess_strategy_robustness


def test_assess_strategy_robustness_reports_missing_evidence() -> None:
    """Assessment labels absent Monte Carlo evidence without inventing a check."""
    result = assess_strategy_robustness(
        monte_carlo=None,
        stress_checks=({"name": "cost", "passed": True},),
    )
    assert result["robustness_percentage"] == 100.0
    assert result["warnings"] == ("monte_carlo_evidence_missing",)
    with pytest.raises(ValueError, match="at least one"):
        assess_strategy_robustness(monte_carlo=None, stress_checks=())
