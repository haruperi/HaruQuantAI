"""Tests for overfit evidence assembly."""

# ruff: noqa: INP001

from app.services.optimization.scoring import CandidateScore, assess_overfit_evidence


def _score(value: float, trades: int) -> CandidateScore:
    """Build a controlled score fixture."""
    return CandidateScore(
        candidate_hash="a" * 64,
        objective="sharpe_ratio",
        direction="maximize",
        value=value,
        available=True,
        trade_count=trades,
        metrics={"sharpe_ratio": value},
    )


def test_assess_overfit_evidence_reports_insufficient_data() -> None:
    """Missing DSR and short trade evidence remain explicit caveats."""
    result = assess_overfit_evidence(
        in_sample=_score(1.0, 10),
        out_of_sample=_score(0.5, 10),
        nominal_trials=5,
        deflated_sharpe=None,
        minimum_trade_count=30,
    )
    assert result["trade_count_adequate"] is False
    assert "deflated_sharpe_unavailable" in result["caveats"]
