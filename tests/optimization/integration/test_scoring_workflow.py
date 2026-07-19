"""WF-OPT-003 scoring, ranking, and overfit integration."""

# ruff: noqa: INP001

from app.services.optimization.scoring import (
    ObjectiveName,
    assess_overfit_evidence,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
    rank_candidates,
)
from app.utils import logger
from tests.analytics.usage.test_usage_reports import _report


def test_scoring_workflow_preserves_metric_and_trial_evidence() -> None:
    """Analytics evidence feeds score, DSR, ranking, and overfit diagnostics."""
    logger.debug("Testing WF-OPT-003 scoring workflow")
    report, _ = _report()
    first = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective=ObjectiveName.NET_PNL,
        enabled_objectives=frozenset({ObjectiveName.NET_PNL}),
    )
    second = first.model_copy(update={"candidate_hash": "b" * 64})
    trials = count_nominal_trials((first.candidate_hash, second.candidate_hash))
    deflated = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=1.0,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=trials,
    )
    ranked = rank_candidates((second, first))
    diagnostics = assess_overfit_evidence(
        in_sample=ranked[0],
        out_of_sample=ranked[0],
        nominal_trials=trials,
        deflated_sharpe=deflated,
        minimum_trade_count=1,
    )
    assert ranked[0].candidate_hash == "a" * 64
    assert diagnostics["nominal_trials"] == 2
