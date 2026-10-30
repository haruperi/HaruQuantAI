"""Unit tests for RuntimeCondition.

Description:
    Validates boundary conditions, elapsed time formatting displays, and comparator
    error propagation for RuntimeCondition.

Purpose:
    FEAT-TASK-CONDITIONS: Validate project runtime duration condition evaluator.

Key Capabilities:
    - FR-task-conditions-runtime: Test boundaries, displays, and error cases.
"""

from __future__ import annotations

import pytest
from app.workspace.task_manager.conditions.runtime import RuntimeCondition


def test_boundaries() -> None:
    """Validate boundary conditions around 120 minutes (7,200,000 ms)."""
    # running_ms=7199999 -> True (delta = -1 < 0)
    c_under = RuntimeCondition.evaluate(7199999)
    assert c_under.met is True
    assert c_under.last_checked_value == "1h 59m"

    # running_ms=7200000 -> False (delta = 0 not < 0)
    c_exact = RuntimeCondition.evaluate(7200000)
    assert c_exact.met is False
    assert c_exact.last_checked_value == "2h 0m"

    # running_ms=7200001 -> False (delta = 1 not < 0)
    c_over = RuntimeCondition.evaluate(7200001)
    assert c_over.met is False
    assert c_over.last_checked_value == "2h 0m"


def test_displays() -> None:
    """Validate exact formatted time displays across unit boundaries."""
    assert RuntimeCondition.evaluate(0).last_checked_value == "0s"
    assert RuntimeCondition.evaluate(59000).last_checked_value == "59s"
    assert RuntimeCondition.evaluate(60000).last_checked_value == "1m 0s"
    assert RuntimeCondition.evaluate(3600000).last_checked_value == "1h 0m"
    assert RuntimeCondition.evaluate(86400000).last_checked_value == "1d 0h 0m"


def test_comparator_error() -> None:
    """Unknown comparator raises ValueError directly from ConditionComparator."""
    with pytest.raises(ValueError, match="Unknown comparator '!='"):
        RuntimeCondition.evaluate(60000, comparator="!=")
