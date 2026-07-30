"""Executable Optimization evidence usage example.

Demonstrates assembling optimization evidence, final decisions, and report
package generation.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization import (
    build_optimization_evidence,
    build_report_package,
    dump_optimization_value,
)
from tests.optimization.usage._support import evidence_request


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_evidence() -> None:
    """Demonstrate optimization evidence assembly."""
    _header("Demonstrate optimization evidence assembly.")
    print("Optimization Example 7: Evidence Assembly and Report Packages")

    # 1. Final decision catalog
    req = evidence_request()
    print(f"Genuine search evidence ID: {req.search.search_id}")

    # 2. Evidence assembly request
    print(
        "Evidence assembly input:",
        {
            "search_id": req.search.search_id,
            "candidate_count": len(req.search.candidates),
            "chart_data": req.chart_data,
            "audit_references": req.audit_references,
        },
    )

    # 3. Build optimization evidence
    result = build_optimization_evidence(req)
    values = dump_optimization_value(result)
    print(
        "Built OptimizationResult evidence:",
        {
            "search_id": values["search_id"],
            "reproducibility_hash": values["reproducibility_hash"],
            "ranked_candidates": tuple(
                {
                    "parameters": candidate["executable_parameters"],
                    "score": candidate["score"]["value"],
                    "simulation_run_id": candidate["evidence"]["simulation_run_id"],
                }
                for candidate in values["ranked_candidates"]
            ),
            "warnings": values["warnings"],
            "final_decision": values["final_decision"],
        },
    )

    # 4. Build report package handoff
    pkg = build_report_package(result)
    print(f"Report package schema ID: {pkg['schema_id']}")


def main() -> None:
    """Run Optimization evidence usage example."""
    example_evidence()


if __name__ == "__main__":
    main()
