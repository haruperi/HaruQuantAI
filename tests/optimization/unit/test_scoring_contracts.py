"""Tests for Optimization scoring contracts."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.scoring import CandidateScore, ObjectiveName
from pydantic import ValidationError


def test_objective_name_values_are_canonical() -> None:
    """Objectives match Analytics metric keys exactly."""
    assert {item.value for item in ObjectiveName} == {
        "net_pnl",
        "profit_factor",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "max_drawdown",
    }


def test_candidate_score_rejects_non_finite_value() -> None:
    """Infinity is never valid score evidence."""
    with pytest.raises(ValidationError):
        CandidateScore(
            candidate_hash="a" * 64,
            objective="net_pnl",
            direction="maximize",
            value=float("inf"),
            available=True,
            trade_count=10,
            metrics={},
        )
