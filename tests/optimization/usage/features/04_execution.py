"""Executable Optimization execution usage example.

Demonstrates FEAT-OPT-04 backtest execution adapter interface, candidate execution request, and candidate execution.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import get_analytics_value_field
from app.services.optimization import execute_candidate, get_optimization_value_field
from tests.optimization.usage._support import genuine_execution_bundle


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


def fr_opt_013() -> None:
    """FR-OPT-013: Stage 1 — Execution Adapter Contract.

    The system shall define a versioned BacktestExecutionAdapter interface connecting to Simulation and Analytics.
    """
    _header("Stage 1: Adapter Contract - Execution Adapter Boundary (FR-OPT-013)")
    _, req, _ = genuine_execution_bundle()
    print(_format_result(req))
    print(f"Data -> contract_version='{req.contract_version}'")


def fr_opt_014() -> None:
    """FR-OPT-014: Stage 2 — Candidate Execution Request Mapping.

    The system shall construct typed candidate execution requests with immutable data and strategy hashes.
    """
    _header("Stage 2: Request Mapping - Map Execution Request (FR-OPT-014)")
    dataset, req, _ = genuine_execution_bundle()
    print(_format_result(req))
    print(
        f"Data -> dataset_record_count={dataset.record_count}, symbol='{dataset.symbol}'"
    )


def fr_opt_015() -> None:
    """FR-OPT-015: Stage 3 — Candidate Backtest Execution.

    The system shall execute candidate parameter sets through the injected Simulation adapter and obtain Analytics evidence.
    """
    _header("Stage 3: Candidate Execution - Execute Candidate (FR-OPT-015)")
    _, req, adapter = genuine_execution_bundle()
    res = execute_candidate(req, adapter, deterministic_only=True)
    report = get_optimization_value_field(res, "analytics_report")
    sections = get_analytics_value_field(report, "sections")
    pnl_section = next(section for section in sections if section.section_key == "pnl")
    print(_format_result(res))
    print(
        f"Data -> candidate_hash='{res.candidate_hash}', "
        f"simulation_run_id='{res.simulation_run_id}', "
        f"pnl_metrics_count={len(pnl_section.metrics)}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-04 — execution/ — Simulation Execution Boundary\n\n"
        "Purpose: Define the versioned BacktestExecutionAdapter interface and execute candidates through Simulation and Analytics.\n\n"
        "Module flow:\n"
        "-> Stage 1: Backtest execution adapter contract definition\n"
        "-> Stage 2: Candidate execution request construction and validation\n"
        "-> Stage 3: Candidate execution through adapter and Analytics report extraction"
    )

    # Stage 1: Adapter Contract
    fr_opt_013()

    # Stage 2: Request Mapping
    fr_opt_014()

    # Stage 3: Candidate Execution
    fr_opt_015()


if __name__ == "__main__":
    main()
