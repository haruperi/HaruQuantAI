"""Unit tests for ResultsCountCondition.

Description:
    Validates boundary conditions, missing databank errors, signed 32-bit overflow
    wrapping, and comparator error propagation for ResultsCountCondition.

Purpose:
    FEAT-TASK-CONDITIONS: Validate databank results count condition evaluator.

Key Capabilities:
    - FR-task-conditions-results: Test boundary, missing bank, and error cases.
"""

from __future__ import annotations

import pytest
from app.workspace.task_manager.conditions.results import ResultsCountCondition


def test_boundaries() -> None:
    """Validate boundary conditions, missing databank exception, and 32-bit delta wrapping."""
    # databank_counts={'Results': 99} -> True at defaults
    c99 = ResultsCountCondition.evaluate({"Results": 99})
    assert c99.met is True
    assert c99.last_checked_value == "99"

    # databank_counts={'Results': 100} -> False at defaults
    c100 = ResultsCountCondition.evaluate({"Results": 100})
    assert c100.met is False
    assert c100.last_checked_value == "100"

    # Missing databank 'M' raises exact ValueError("Databank M doesn't exist")
    with pytest.raises(ValueError, match=r"^Databank M doesn't exist$"):
        ResultsCountCondition.evaluate({"Results": 99}, databank="M")

    # Overflow fixture: Results=2147483647, number=-2147483648, comparator='>' -> False
    # delta wraps to -1, which is not > 0
    c_overflow = ResultsCountCondition.evaluate(
        {"Results": 2147483647},
        comparator=">",
        number=-2147483648,
    )
    assert c_overflow.met is False
    assert c_overflow.last_checked_value == "2147483647"


def test_comparator_error() -> None:
    """Unknown comparator raises ValueError directly from ConditionComparator."""
    with pytest.raises(ValueError, match="Unknown comparator '!='"):
        ResultsCountCondition.evaluate({"Results": 100}, comparator="!=")
