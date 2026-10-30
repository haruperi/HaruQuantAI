"""Unit tests for RunCyclesCondition.

Description:
    Validates boundary conditions, signed 32-bit overflow wrapping, string representation,
    and comparator error propagation for RunCyclesCondition.

Purpose:
    FEAT-TASK-CONDITIONS: Validate run cycles condition evaluator.

Key Capabilities:
    - FR-task-conditions-cycles: Test boundary, display, and error cases.
"""

from __future__ import annotations

import pytest
from app.workspace.task_manager.conditions.cycles import RunCyclesCondition


def test_boundaries() -> None:
    """Validate boundary conditions and 32-bit integer overflow wrapping."""
    # run_cycles=99 -> True (delta = -1 < 0)
    c99 = RunCyclesCondition.evaluate(99)
    assert c99.met is True
    assert c99.last_checked_value == "99"

    # run_cycles=100 -> False (delta = 0 not < 0)
    c100 = RunCyclesCondition.evaluate(100)
    assert c100.met is False
    assert c100.last_checked_value == "100"

    # run_cycles=101 -> False (delta = 1 not < 0)
    c101 = RunCyclesCondition.evaluate(101)
    assert c101.met is False
    assert c101.last_checked_value == "101"

    # Overflow fixture: run_cycles=2147483647, number=-2147483648, comparator='>' -> False
    # delta wraps to -1, which is not > 0
    c_overflow = RunCyclesCondition.evaluate(
        2147483647,
        comparator=">",
        number=-2147483648,
    )
    assert c_overflow.met is False
    assert c_overflow.last_checked_value == "2147483647"


def test_comparator_error() -> None:
    """Unknown comparator raises ValueError directly from ConditionComparator."""
    with pytest.raises(ValueError, match="Unknown comparator '!='"):
        RunCyclesCondition.evaluate(100, comparator="!=")
