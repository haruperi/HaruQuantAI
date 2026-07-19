"""Tests for Optimization parameter contracts."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.optimization.parameters import ParameterRange, ParameterSpace
from pydantic import ValidationError


def test_parameter_range_rejects_invalid_bounds() -> None:
    """Numeric ranges require ordered finite bounds and a positive step."""
    with pytest.raises(ValidationError):
        ParameterRange(
            name="period",
            kind="integer",
            minimum=Decimal(10),
            maximum=Decimal(1),
            step=Decimal(1),
        )


def test_parameter_space_rejects_duplicate_names() -> None:
    """Duplicate definitions are ambiguous and rejected."""
    item = ParameterRange(name="enabled", kind="boolean")
    with pytest.raises(ValidationError):
        ParameterSpace(parameters=(item, item))


def test_parameter_range_supports_conditional_underlying_kind() -> None:
    """Activation is orthogonal to the underlying value kind."""
    item = ParameterRange(
        name="period",
        kind="integer",
        minimum=Decimal(1),
        maximum=Decimal(3),
        step=Decimal(1),
        active_when="enabled == True",
    )
    assert item.kind == "integer"
    assert item.active_when == "enabled == True"
