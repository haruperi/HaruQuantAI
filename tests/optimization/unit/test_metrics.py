"""Tests for Optimization metric evidence."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.scoring import (
    ObjectiveName,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
)
from tests.analytics.usage.test_usage_reports import _report


def test_calculate_candidate_score_rejects_unknown_objective() -> None:
    """A disabled objective fails rather than falling back."""
    report, _ = _report()
    with pytest.raises(ValueError, match="not enabled"):
        calculate_candidate_score(
            report,
            candidate_hash="a" * 64,
            objective=ObjectiveName.NET_PNL,
            enabled_objectives=frozenset({ObjectiveName.SHARPE_RATIO}),
        )


def test_calculate_candidate_score_consumes_analytics_metric() -> None:
    """Optimization projects, but does not recompute, Analytics evidence."""
    report, _ = _report()
    score = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective=ObjectiveName.NET_PNL,
        enabled_objectives=frozenset({ObjectiveName.NET_PNL}),
    )
    assert score.available
    assert score.value == score.metrics["net_pnl"]


def test_calculate_deflated_sharpe_handles_insufficient_data() -> None:
    """Short evidence returns unavailable rather than a fabricated zero."""
    assert (
        calculate_deflated_sharpe(
            sharpe=1.0,
            variance=0.2,
            skewness=0.0,
            kurtosis=3.0,
            sample_count=2,
            nominal_trials=10,
        )
        is None
    )


def test_count_nominal_trials_deduplicates_hashes() -> None:
    """Repeated candidates count once after deduplication."""
    assert count_nominal_trials(("a" * 64, "a" * 64, "b" * 64)) == 2
