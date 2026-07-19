"""Runnable usage examples for Optimization parameters."""

from decimal import Decimal

from app.services.optimization.parameters import (
    ParameterRange,
    ParameterSpace,
    candidate_hash,
    evaluate_constraints,
    get_executable_parameters,
    parameter_space_hash,
    validate_parameter_space,
)


def _usage_space() -> ParameterSpace:
    """Construct the bounded example parameter space."""
    return ParameterSpace(
        parameters=(
            ParameterRange(name="enabled", kind="boolean"),
            ParameterRange(
                name="period",
                kind="integer",
                minimum=Decimal(2),
                maximum=Decimal(4),
                step=Decimal(1),
                active_when="enabled == True",
            ),
        ),
        constraints=("period >= 2",),
    )


def test_usage_contracts_parameter_range() -> None:
    """Construct one bounded range."""
    assert _usage_space().parameters[1].name == "period"


def test_usage_contracts_parameter_space() -> None:
    """Construct a complete parameter space."""
    assert len(_usage_space().parameters) == 2


def test_usage_constraints_validate_parameter_space() -> None:
    """Validate limits before generation."""
    validate_parameter_space(_usage_space(), max_expansion=10, max_constraints=3)


def test_usage_constraints_evaluate_constraints() -> None:
    """Evaluate safe candidate constraints."""
    assert evaluate_constraints(
        {"enabled": True, "period": 3},
        _usage_space().constraints,
    )


def test_usage_constraints_get_executable_parameters() -> None:
    """Project a candidate to active values."""
    assert get_executable_parameters(
        {"enabled": False, "period": 3},
        _usage_space(),
    ) == {"enabled": False}


def test_usage_hashing_parameter_space_hash() -> None:
    """Calculate a reproducible space digest."""
    assert len(parameter_space_hash(_usage_space())) == 64


def test_usage_hashing_candidate_hash() -> None:
    """Calculate a candidate digest from complete provenance."""
    assert (
        len(
            candidate_hash(
                strategy_hash="a" * 64,
                data_hash="b" * 64,
                cost_model_hash="c" * 64,
                realism_hash="d" * 64,
                objective_hash="e" * 64,
                engine_type="event_driven",
                engine_version="v1",
                module_version="v1",
                space_hash=parameter_space_hash(_usage_space()),
                executable_parameters={"enabled": True, "period": 3},
            )
        )
        == 64
    )
