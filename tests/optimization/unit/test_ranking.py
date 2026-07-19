"""Tests for deterministic Optimization ranking."""

# ruff: noqa: INP001

from app.services.optimization.scoring import (
    CandidateScore,
    rank_candidates,
    select_pareto_candidates,
)


def _score(candidate_hash: str, value: float, trades: int) -> CandidateScore:
    """Build one net-PnL candidate score."""
    return CandidateScore(
        candidate_hash=candidate_hash,
        objective="net_pnl",
        direction="maximize",
        value=value,
        available=True,
        trade_count=trades,
        metrics={"net_pnl": value},
    )


def test_rank_candidates_uses_canonical_tie_breakers() -> None:
    """Trade count and then hash break equal objective values."""
    candidates = (
        _score("b" * 64, 1.0, 10),
        _score("a" * 64, 1.0, 10),
        _score("c" * 64, 1.0, 20),
    )
    assert tuple(item.candidate_hash for item in rank_candidates(candidates)) == (
        "c" * 64,
        "a" * 64,
        "b" * 64,
    )


def test_select_pareto_candidates_is_deterministic() -> None:
    """Only non-dominated source indices are selected."""
    candidates = (
        {"net_pnl": 10.0, "max_drawdown": 0.2},
        {"net_pnl": 9.0, "max_drawdown": 0.1},
        {"net_pnl": 8.0, "max_drawdown": 0.3},
    )
    assert select_pareto_candidates(candidates, ("net_pnl", "max_drawdown")) == (0, 1)
