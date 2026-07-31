"""Executable Optimization parameters usage example.

Demonstrates FEAT-OPT-01 parameter space definition, range construction, constraint evaluation, executable parameter resolution, and hashing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    candidate_hash,
    evaluate_constraints,
    get_executable_parameters,
    parameter_space_hash,
    validate_parameter_space,
)
from tests.optimization.usage._support import conditional_parameter_space


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _usage_space() -> Any:
    """Construct a demonstration parameter space."""
    return conditional_parameter_space()


def fr_opt_001() -> None:
    """FR-OPT-001: Stage 1 — Parameter Range & Space Construction.

    The system shall define parameter ranges, conditional parameters, and safe constraints without using Utils.
    """
    _header("Stage 1: Parameter Range & Space - Define Parameter Space (FR-OPT-001)")
    space = _usage_space()
    print(_format_result(space))
    print(
        f"Data -> parameters_count={len(getattr(space, 'parameters', ())) if hasattr(space, 'parameters') else 0}"
    )


def fr_opt_002() -> None:
    """FR-OPT-002: Stage 2 — Parameter Space Validation.

    The system shall validate parameter space definitions and fail fast on invalid combinations.
    """
    _header("Stage 2: Space Validation - Validate Parameter Space (FR-OPT-002)")
    space = _usage_space()
    validate_parameter_space(space, max_expansion=10, max_constraints=3)
    print(_format_result(space))
    print("Data -> space_validated=True")


def fr_opt_003() -> None:
    """FR-OPT-003: Stage 2 — Constraint Evaluation.

    The system shall evaluate logical constraints against candidate parameter dictionaries.
    """
    _header(
        "Stage 2: Constraint Evaluation - Evaluate Candidate Constraints (FR-OPT-003)"
    )
    space = _usage_space()
    candidate = {"enabled": True, "period": 3}
    valid = evaluate_constraints(candidate, space.constraints)
    print(_format_result(valid))
    print(f"Data -> candidate={candidate}, constraint_evaluation={valid}")


def fr_opt_004() -> None:
    """FR-OPT-004: Stage 3 — Executable Parameter Resolution.

    The system shall resolve conditional parameter dependencies into final executable parameter sets.
    """
    _header(
        "Stage 3: Parameter Resolution - Resolve Executable Parameters (FR-OPT-004)"
    )
    space = _usage_space()
    inactive_candidate = {"enabled": False, "period": 3}
    exec_params = get_executable_parameters(inactive_candidate, space)
    print(_format_result(exec_params))
    print(f"Data -> executable_parameters={exec_params}")


def fr_opt_005() -> None:
    """FR-OPT-005: Stage 3 — Parameter Space & Candidate Hashing.

    The system shall generate canonical SHA-256 hashes for parameter spaces and candidate provenance.
    """
    _header("Stage 3: Provenance Hashing - Parameter & Candidate Hashing (FR-OPT-005)")
    space = _usage_space()
    sp_hash = parameter_space_hash(space)
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
    print(_format_result(sp_hash))
    print(f"Data -> space_hash='{sp_hash}', candidate_hash='{cand_hash}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-01 — parameters/ — Parameter Space and Provenance\n\n"
        "Purpose: Define parameter spaces, validate safe constraints, resolve conditional parameters, and generate canonical provenance hashes.\n\n"
        "Module flow:\n"
        "-> Stage 1: Parameter range and space construction\n"
        "-> Stage 2: Parameter space validation and constraint evaluation\n"
        "-> Stage 3: Executable parameter resolution and SHA-256 provenance hashing"
    )

    # Stage 1: Space construction
    fr_opt_001()

    # Stage 2: Validation & Constraints
    fr_opt_002()
    fr_opt_003()

    # Stage 3: Resolution & Hashing
    fr_opt_004()
    fr_opt_005()


if __name__ == "__main__":
    main()
