"""Tests for safe parameter constraints."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.optimization.parameters import (
    ParameterRange,
    ParameterSpace,
    evaluate_constraints,
    get_executable_parameters,
    validate_parameter_space,
)


def _space() -> ParameterSpace:
    """Build a conditional parameter fixture."""
    return ParameterSpace(
        parameters=(
            ParameterRange(name="enabled", kind="boolean"),
            ParameterRange(
                name="period",
                kind="integer",
                minimum=Decimal(1),
                maximum=Decimal(3),
                step=Decimal(1),
                active_when="enabled == True",
            ),
        ),
        constraints=("period >= 1",),
    )


def test_validate_parameter_space_fails_closed() -> None:
    """Expansion caps are enforced before candidate generation."""
    with pytest.raises(ValueError, match="expansion"):
        validate_parameter_space(_space(), max_expansion=2, max_constraints=2)


def test_evaluate_constraints_blocks_unsafe_ast() -> None:
    """Calls and attributes are outside the expression grammar."""
    with pytest.raises(ValueError, match="unsafe"):
        evaluate_constraints({"period": 2}, ("period.__class__()",))


def test_get_executable_parameters_excludes_inactive_values() -> None:
    """Inactive values remain metadata but do not reach execution."""
    result = get_executable_parameters(
        {"enabled": False, "period": 3},
        _space(),
    )
    assert result == {"enabled": False}


def test_validate_parameter_space_rejects_activation_cycle() -> None:
    """Activation dependencies must form a directed acyclic graph."""
    space = ParameterSpace(
        parameters=(
            ParameterRange(name="first", kind="boolean", active_when="second"),
            ParameterRange(name="second", kind="boolean", active_when="first"),
        )
    )
    with pytest.raises(ValueError, match="cyclic"):
        validate_parameter_space(space, max_expansion=10, max_constraints=10)
