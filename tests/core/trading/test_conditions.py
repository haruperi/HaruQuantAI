"""Tests for verified scalar condition comparator."""

from __future__ import annotations

import pytest
from app.core.trading.conditions import ConditionComparator

TRUTH_TABLE_CELLS = [
    # delta, operator, expected
    (-1.0, ">", False),
    (-1.0, "<", True),
    (-1.0, "=", False),
    (-1.0, ">=", False),
    (-1.0, "<=", True),
    (-1.0, "<>", True),
    (0.0, ">", False),
    (0.0, "<", False),
    (0.0, "=", True),
    (0.0, ">=", True),
    (0.0, "<=", True),
    (0.0, "<>", False),
    (1.0, ">", True),
    (1.0, "<", False),
    (1.0, "=", False),
    (1.0, ">=", True),
    (1.0, "<=", False),
    (1.0, "<>", True),
    (float("nan"), ">", False),
    (float("nan"), "<", False),
    (float("nan"), "=", False),
    (float("nan"), ">=", False),
    (float("nan"), "<=", False),
    (float("nan"), "<>", True),
]


@pytest.mark.parametrize("delta,comparator,expected", TRUTH_TABLE_CELLS)
def test_condition_truth_table(delta: float, comparator: str, expected: bool) -> None:
    """Parametrize all 24 cells of the condition comparator truth table."""
    result = ConditionComparator.validate(delta, comparator)
    assert result is expected


def test_signed_zero_and_unknown_operator() -> None:
    """Verify signed zero equality and exact unknown-comparator error messages."""
    # Signed zero behavior
    assert ConditionComparator.validate(0.0, "=") is True
    assert ConditionComparator.validate(-0.0, "=") is True
    assert ConditionComparator.validate(0.0, "<>") is False
    assert ConditionComparator.validate(-0.0, "<>") is False

    # Unknown comparator error messages
    with pytest.raises(ValueError, match=r"^Unknown comparator '!='$"):
        ConditionComparator.validate(0.0, "!=")

    with pytest.raises(ValueError, match=r"^Unknown comparator ' >'$"):
        ConditionComparator.validate(0.0, " >")
