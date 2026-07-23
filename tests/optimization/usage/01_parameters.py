"""Executable Optimization parameters usage example.

Demonstrates parameter space definition, range construction, constraint evaluation,
executable parameter resolution, and hashing.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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
    """Construct a demonstration parameter space."""
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


def example_parameters() -> None:
    """Demonstrate parameter space definition, validation, and evaluation."""
    print("=" * 80)
    print("Optimization Example 1: Parameter Space and Provenance Hashing")
    print("=" * 80)

    space = _usage_space()
    print(f"Parameter space contains {len(space.parameters)} parameter ranges.")

    # Validate parameter space
    validate_parameter_space(space, max_expansion=10, max_constraints=3)
    print("Parameter space validated successfully.")

    # Evaluate constraints
    candidate = {"enabled": True, "period": 3}
    valid = evaluate_constraints(candidate, space.constraints)
    print(f"Candidate {candidate} constraint evaluation: {valid}")

    # Project to executable parameters
    inactive_candidate = {"enabled": False, "period": 3}
    exec_params = get_executable_parameters(inactive_candidate, space)
    print(f"Inactive candidate projected parameters: {exec_params}")

    # Hashes
    sp_hash = parameter_space_hash(space)
    print(f"Parameter space hash: {sp_hash}")

    cand_hash = candidate_hash(
        strategy_hash="a" * 64,
        data_hash="b" * 64,
        cost_model_hash="c" * 64,
        realism_hash="d" * 64,
        objective_hash="e" * 64,
        engine_type="event_driven",
        engine_version="v1",
        module_version="v1",
        space_hash=sp_hash,
        executable_parameters={"enabled": True, "period": 3},
    )
    print(f"Candidate provenance hash: {cand_hash}")


def main() -> None:
    """Run Optimization parameters usage example."""
    example_parameters()


if __name__ == "__main__":
    main()
