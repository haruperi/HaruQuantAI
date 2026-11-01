"""Unit tests for FullPosition close size sentinel formula."""

from __future__ import annotations

from typing import Any

from app.extend.formulas.close_size.full_position import FullPosition


class ExplodingStrategy:
    """Mock strategy that raises on any attribute access."""

    def __getattribute__(self, name: str) -> Any:
        raise RuntimeError(f"Unexpected strategy attribute access: {name}")


def test_returns_zero_for_both_directions() -> None:
    """Evaluate directions -1 and 1, ensuring both yield float 0.0."""
    evaluator = FullPosition()
    assert evaluator.evaluate_formula(None, "EURUSD", 1.1234, -1) == 0.0
    assert evaluator.evaluate_formula(None, "EURUSD", 1.1234, 1) == 0.0


def test_does_not_access_strategy() -> None:
    """Ensure strategy attributes are not accessed or mutated."""
    evaluator = FullPosition()
    strategy = ExplodingStrategy()
    assert evaluator.evaluate_formula(strategy, "GBPUSD", 1.3000, 1) == 0.0


def test_has_no_state() -> None:
    """Ensure evaluator is stateless across calls with different symbols/prices."""
    evaluator = FullPosition()
    res1 = evaluator.evaluate_formula(None, "USDJPY", 145.50, 1)
    res2 = evaluator.evaluate_formula(None, "AUDUSD", 0.6500, -1)
    assert res1 == 0.0
    assert res2 == 0.0
