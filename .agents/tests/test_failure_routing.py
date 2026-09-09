"""Tests for deterministic failure classification and correction bounds."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "failure_routing.py"
SPEC = importlib.util.spec_from_file_location("hq_failure_routing", MODULE_PATH)
assert SPEC
assert SPEC.loader
routing = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = routing
SPEC.loader.exec_module(routing)


def test_implementation_fix_routes_directly_twice_then_escalates() -> None:
    """Direct correction must be bounded before Planner escalation."""
    first = routing.route_failure(
        routing.FailureClass.IMPLEMENTATION_FIX, direct_corrections=0
    )
    second = routing.route_failure(
        routing.FailureClass.IMPLEMENTATION_FIX, direct_corrections=1
    )
    exhausted = routing.route_failure(
        routing.FailureClass.IMPLEMENTATION_FIX, direct_corrections=2
    )

    assert first.target == second.target == "EXECUTOR"
    assert not first.exhausted and not second.exhausted
    assert exhausted.target == "PLANNER"
    assert exhausted.exhausted


def test_design_change_always_routes_to_planner() -> None:
    """A design decision must never be repaired as implementation detail."""
    result = routing.route_failure(routing.FailureClass.DESIGN_CHANGE)

    assert result.target == "PLANNER"
    assert result.requires_reasoning


@pytest.mark.parametrize(
    "failure_class",
    [
        routing.FailureClass.ADMINISTRATIVE_RETRY,
        routing.FailureClass.ENVIRONMENT_FAILURE,
    ],
)
def test_non_reasoning_retry_is_allowed_once(
    failure_class: routing.FailureClass,
) -> None:
    """Exact controller operations receive at most one retry."""
    first = routing.route_failure(failure_class, operation_retries=0)
    exhausted = routing.route_failure(failure_class, operation_retries=1)

    assert first.target == "CONTROLLER_RETRY"
    assert not first.requires_reasoning
    assert exhausted.target == "STOP"
    assert exhausted.exhausted


def test_administrative_paths_refuse_product_or_policy_changes() -> None:
    """Administrative recovery cannot become source-edit authority."""
    routing.validate_administrative_paths(
        [
            ".agents/runs/run-1/retry.json",
            ".agents/logs/run-1/attempt.log",
            ".agents/task/next-agent.md",
        ]
    )

    for forbidden in (
        "app/services/orders/service.py",
        ".agents/protocol.toml",
        ".secrets.baseline",
        ".agents/task/reviewer.md",
        "../outside",
    ):
        with pytest.raises(ValueError, match="cannot modify"):
            routing.validate_administrative_paths([forbidden])


def test_environment_operation_retries_once_only() -> None:
    """Transient process launch failure receives one identical retry."""
    calls = 0

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 2:
            raise OSError("transient")
        return "ok"

    assert routing.run_bounded_environment_operation(operation) == "ok"
    assert calls == 2

    with pytest.raises(OSError, match="persistent"):
        routing.run_bounded_environment_operation(
            lambda: (_ for _ in ()).throw(OSError("persistent"))
        )
