"""Tests for explicit Optimization execution stress."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.optimization.robustness import (
    ExecutionStressRequest,
    apply_execution_cost_stress,
)


def test_apply_execution_cost_stress_does_not_mutate_input() -> None:
    """Cost stress copies records and preserves caller-owned input."""
    outcomes = [{"trade_id": "one", "pnl": Decimal(5)}]
    stressed = apply_execution_cost_stress(
        outcomes,
        ExecutionStressRequest(kind="commission", value=Decimal(1)),
    )
    assert outcomes == [{"trade_id": "one", "pnl": Decimal(5)}]
    assert stressed[0]["pnl"] == Decimal(4)
