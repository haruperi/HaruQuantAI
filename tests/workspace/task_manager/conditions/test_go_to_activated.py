"""Unit tests for GoToActivatedCondition.

Description:
    Validates boundary conditions, double-precision float delta (no 32-bit wrapping),
    and comparator error propagation for GoToActivatedCondition.

Purpose:
    FEAT-TASK-CONDITIONS: Validate GoTo activated cycles condition evaluator.

Key Capabilities:
    - FR-task-conditions-goto-activated: Test boundary, double precision, and error cases.
"""

from __future__ import annotations

import pytest
from app.workspace.task_manager.conditions.go_to_activated import (
    GoToActivatedCondition,
)


def test_boundaries() -> None:
    """Validate boundary conditions and double-precision delta calculation."""
    # activated_cycles=99 -> True
    c99 = GoToActivatedCondition.evaluate(99)
    assert c99.met is True
    assert c99.last_checked_value == "99"

    # activated_cycles=100 -> False
    c100 = GoToActivatedCondition.evaluate(100)
    assert c100.met is False
    assert c100.last_checked_value == "100"

    # At activated_cycles=2147483647, number=-2147483648, comparator='>' -> True
    # Subtraction uses double precision: 2147483647 - (-2147483648) = 4294967295.0 > 0
    c_large = GoToActivatedCondition.evaluate(
        2147483647,
        comparator=">",
        number=-2147483648,
    )
    assert c_large.met is True
    assert c_large.last_checked_value == "2147483647"


def test_comparator_error() -> None:
    """Unknown comparator raises ValueError directly from ConditionComparator."""
    with pytest.raises(ValueError, match="Unknown comparator '!='"):
        GoToActivatedCondition.evaluate(100, comparator="!=")
