"""Runnable usage examples for Optimization scoring."""

from app.services.optimization.scoring import (
    CandidateScore,
    ObjectiveName,
    assess_overfit_evidence,
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
    rank_candidates,
    select_pareto_candidates,
)
from tests.analytics.usage.test_usage_reports import _report


def _score(value: float = 1.0) -> CandidateScore:
    """Build one usage score."""
    return CandidateScore(
        candidate_hash="a" * 64,
        objective="sharpe_ratio",
        direction="maximize",
        value=value,
        available=True,
        trade_count=40,
        metrics={"sharpe_ratio": value},
    )


def test_usage_contracts_objective_name() -> None:
    """Select a canonical objective."""
    assert ObjectiveName.SHARPE_RATIO.value == "sharpe_ratio"


def test_usage_contracts_candidate_score() -> None:
    """Construct immutable candidate evidence."""
    assert _score().available


def test_usage_metrics_calculate_candidate_score() -> None:
    """Project a score from Analytics evidence."""
    report, _ = _report()
    result = calculate_candidate_score(
        report,
        candidate_hash="a" * 64,
        objective=ObjectiveName.NET_PNL,
        enabled_objectives=frozenset({ObjectiveName.NET_PNL}),
    )
    assert result.available


def test_usage_metrics_calculate_deflated_sharpe() -> None:
    """Calculate published-method multiple-testing evidence."""
    value = calculate_deflated_sharpe(
        sharpe=1.0,
        variance=0.2,
        skewness=0.0,
        kurtosis=3.0,
        sample_count=100,
        nominal_trials=10,
    )
    assert value is not None


def test_usage_metrics_count_nominal_trials() -> None:
    """Count unique candidate identities."""
    assert count_nominal_trials(("a" * 64, "b" * 64)) == 2


def test_usage_ranking_rank_candidates() -> None:
    """Rank candidates with canonical tie breaking."""
    assert rank_candidates((_score(),))[0].value == 1.0


def test_usage_ranking_select_pareto_candidates() -> None:
    """Select an explicit Pareto front."""
    assert select_pareto_candidates(({"net_pnl": 1.0},), ("net_pnl",)) == (0,)


def test_usage_overfit_assess_overfit_evidence() -> None:
    """Assemble advisory overfit diagnostics."""
    assert assess_overfit_evidence(
        in_sample=_score(),
        out_of_sample=_score(0.8),
        nominal_trials=2,
        deflated_sharpe=0.7,
        minimum_trade_count=30,
    )["trade_count_adequate"]
