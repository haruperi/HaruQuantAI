"""Unit tests for GoToEvaluatedCondition.

Description:
    Validates boundary conditions, double-precision float delta (no 32-bit wrapping),
    and comparator error propagation for GoToEvaluatedCondition.

Purpose:
    FEAT-TASK-CONDITIONS: Validate GoTo evaluated cycles condition evaluator.

Key Capabilities:
    - FR-task-conditions-goto-evaluated: Test boundary, double precision, and error cases.
"""

from __future__ import annotations

import pytest
from app.workspace.task_manager.conditions.go_to_evaluated import (
    GoToEvaluatedCondition,
)


def test_boundaries() -> None:
    """Validate boundary conditions and double-precision delta calculation."""
    # evaluated_cycles=99 -> True
    c99 = GoToEvaluatedCondition.evaluate(99)
    assert c99.met is True
    assert c99.last_checked_value == "99"

    # evaluated_cycles=100 -> False
    c100 = GoToEvaluatedCondition.evaluate(100)
    assert c100.met is False
    assert c100.last_checked_value == "100"

    # At evaluated_cycles=2147483647, number=-2147483648, comparator='>' -> True
    # Subtraction uses double precision: 2147483647 - (-2147483648) = 4294967295.0 > 0
    c_large = GoToEvaluatedCondition.evaluate(
        2147483647,
        comparator=">",
        number=-2147483648,
    )
    assert c_large.met is True
    assert c_large.last_checked_value == "2147483647"


def test_comparator_error() -> None:
    """Unknown comparator raises ValueError directly from ConditionComparator."""
    with pytest.raises(ValueError, match="Unknown comparator '!='"):
        GoToEvaluatedCondition.evaluate(100, comparator="!=")
