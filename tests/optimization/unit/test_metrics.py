"""Tests for Optimization metric evidence."""

import pytest
from app.services.optimization.scoring import (
    ObjectiveName,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
)

from tests.analytics._support import _report


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


def test_metric_input_failures_are_explicit() -> None:
    """Reject unsupported objective types, non-finite evidence, and bad hashes."""
    report, _ = _report()
    with pytest.raises(TypeError, match="known ObjectiveName"):
        calculate_candidate_score(
            report,
            candidate_hash="a" * 64,
            objective=object(),  # type: ignore[arg-type]
            enabled_objectives=frozenset({ObjectiveName.NET_PNL}),
        )
    with pytest.raises(ValueError, match="finite"):
        calculate_deflated_sharpe(
            sharpe=float("nan"),
            variance=0.2,
            skewness=0.0,
            kurtosis=3.0,
            sample_count=10,
            nominal_trials=2,
        )
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_deflated_sharpe(
            sharpe=1.0,
            variance=-0.1,
            skewness=0.0,
            kurtosis=3.0,
            sample_count=10,
            nominal_trials=2,
        )
    with pytest.raises(ValueError, match="malformed"):
        count_nominal_trials(("not-a-hash",))


def test_deflated_sharpe_covers_single_trial_and_invalid_denominator() -> None:
    """Calculate one valid probability and reject an invalid denominator."""
    probability = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=30,
        nominal_trials=1,
    )
    assert probability is not None
    assert 0 <= probability <= 1
    assert (
        calculate_deflated_sharpe(
            sharpe=1.0,
            variance=0.2,
            skewness=2.0,
            kurtosis=1.0,
            sample_count=30,
            nominal_trials=2,
        )
        is None
    )
