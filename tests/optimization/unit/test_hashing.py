"""Tests for parameter provenance hashing."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.optimization.parameters import (
    ParameterRange,
    ParameterSpace,
    candidate_hash,
    parameter_space_hash,
)


def test_parameter_space_hash_is_order_invariant() -> None:
    """Definition order does not change canonical space identity."""
    first = ParameterRange(name="first", kind="boolean")
    second = ParameterRange(name="second", kind="fixed", fixed_value="x")
    left = parameter_space_hash(ParameterSpace(parameters=(first, second)))
    right = parameter_space_hash(ParameterSpace(parameters=(second, first)))
    assert left == right


def test_candidate_hash_excludes_inactive_parameters() -> None:
    """Only caller-supplied executable values affect candidate identity."""
    arguments = {
        "strategy_hash": "a" * 64,
        "data_hash": "b" * 64,
        "cost_model_hash": "c" * 64,
        "realism_hash": "d" * 64,
        "objective_hash": "e" * 64,
        "engine_type": "event_driven",
        "engine_version": "v1",
        "module_version": "v1",
        "space_hash": "f" * 64,
    }
    left = candidate_hash(
        **arguments,
        executable_parameters={"period": Decimal("2.0")},
    )
    right = candidate_hash(
        **arguments,
        executable_parameters={"period": Decimal("2.00000000")},
    )
    assert left == right
