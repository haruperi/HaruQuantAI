"""Executable Optimization evidence usage example.

Demonstrates FEAT-OPT-07 assembling optimization evidence, final decisions, and report package generation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization import (
    build_optimization_evidence,
    build_report_package,
    dump_optimization_value,
)
from tests.optimization.usage._support import evidence_request


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


def fr_opt_045() -> None:
    """FR-OPT-045: Stage 1 — Final Decision Catalog.

    The system shall support canonical final decision classifications without background-job lifecycle.
    """
    _header("Stage 1: Decision Catalog - Synchronous Final Decisions (FR-OPT-045)")
    decisions = (
        "ready_for_risk_review",
        "validation_needed",
        "research_only",
        "rejected",
        "failed",
    )
    print(_format_result(decisions))
    print(f"Data -> final_decisions={decisions}")


def fr_opt_046() -> None:
    """FR-OPT-046: Stage 1 — Evidence Request Modeling.

    The system shall model evidence assembly requests carrying search, WFA, MC, and chart inputs.
    """
    _header("Stage 1: Evidence Input - Model Evidence Request (FR-OPT-046)")
    req = evidence_request()
    print(_format_result(req))
    print(
        f"Data -> search_id='{req.search.search_id}', candidate_count={len(req.search.candidates)}"
    )


def fr_opt_047() -> None:
    """FR-OPT-047: Stage 3 — OptimizationResult v1 Construction.

    The system shall define advisory `OptimizationResult v1` envelopes with search ID, reproducibility hash, and decision.
    """
    _header("Stage 3: Evidence Result - Build Optimization Evidence (FR-OPT-047)")
    req = evidence_request()
    result = build_optimization_evidence(req)
    values = dump_optimization_value(result)
    print(_format_result(result))
    print(
        f"Data -> search_id='{values.get('search_id')}', final_decision='{values.get('final_decision')}'"
    )


def fr_opt_048() -> None:
    """FR-OPT-048: Stage 3 — Baseline Evidence Assembly.

    The system shall assemble versioned baseline evidence and reproducibility hash without recomputing metrics.
    """
    _header("Stage 3: Baseline Assembly - Assemble Baseline Evidence (FR-OPT-048)")
    req = evidence_request()
    result = build_optimization_evidence(req)
    print(_format_result(result))
    print(f"Data -> reproducibility_hash='{result.reproducibility_hash}'")


def fr_opt_049() -> None:
    """FR-OPT-049: Stage 3 — Report Package Handoff.

    The system shall package chart-ready series and tables into report packages without recomputation.
    """
    _header("Stage 3: Report Handoff - Build Report Package (FR-OPT-049)")
    req = evidence_request()
    result = build_optimization_evidence(req)
    pkg = build_report_package(result)
    print(_format_result(pkg))
    print(
        f"Data -> report_package_schema_id='{pkg.get('schema_id') if isinstance(pkg, dict) else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-OPT-07 — evidence/ — Versioned Results and Handoffs\n\n"
        "Purpose: Assemble versioned OptimizationResult evidence, final decision classifications, baseline summary reproducibility hashes, and report packages.\n\n"
        "Module flow:\n"
        "-> Stage 1: Final decision catalog and evidence assembly request mapping\n"
        "-> Stage 2: Ranked candidate and diagnostic payload aggregation\n"
        "-> Stage 3: OptimizationResult v1 envelope construction and report package handoff building"
    )

    # Stage 1: Decision Catalog & Request Mapping
    fr_opt_045()
    fr_opt_046()

    # Stage 3: Result Building, Baseline & Report Handoff
    fr_opt_047()
    fr_opt_048()
    fr_opt_049()


if __name__ == "__main__":
    main()
