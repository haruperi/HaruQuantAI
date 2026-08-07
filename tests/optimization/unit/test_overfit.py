"""Tests for overfit evidence assembly."""

import pytest
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


def test_assess_overfit_validates_bounds_and_objective_identity() -> None:
    """Reject incompatible objectives and invalid caller-supplied bounds."""
    incompatible = _score(0.5, 30).model_copy(update={"objective": "net_pnl"})
    with pytest.raises(ValueError, match="same objective"):
        assess_overfit_evidence(
            in_sample=_score(1.0, 30),
            out_of_sample=incompatible,
            nominal_trials=1,
            deflated_sharpe=0.5,
            minimum_trade_count=30,
        )
    for trials, minimum, dsr, message in (
        (0, 30, 0.5, "bounds must be positive"),
        (1, 0, 0.5, "bounds must be positive"),
        (1, 30, 1.1, "must be a probability"),
    ):
        with pytest.raises(ValueError, match=message):
            assess_overfit_evidence(
                in_sample=_score(1.0, 30),
                out_of_sample=_score(0.5, 30),
                nominal_trials=trials,
                deflated_sharpe=dsr,
                minimum_trade_count=minimum,
            )


def test_assess_overfit_handles_zero_baseline_and_adequate_evidence() -> None:
    """Keep zero-baseline degradation unavailable and accept adequate trades."""
    result = assess_overfit_evidence(
        in_sample=_score(0.0, 40),
        out_of_sample=_score(0.5, 40),
        nominal_trials=2,
        deflated_sharpe=0.75,
        minimum_trade_count=30,
        extra_evidence={"folds": 3},
    )
    assert result["degradation"] is None
    assert result["trade_count_adequate"] is True
    assert result["extra_evidence"] == {"folds": 3}
