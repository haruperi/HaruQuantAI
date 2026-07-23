"""Executable Optimization evidence usage example.

Demonstrates assembling optimization evidence, final decisions, and report package generation.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization.evidence import (
    EvidenceAssemblyRequest,
    FinalDecision,
    build_optimization_evidence,
    build_report_package,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request


def example_evidence() -> None:
    """Demonstrate optimization evidence assembly."""
    print("=" * 80)
    print("Optimization Example 7: Evidence Assembly and Report Packages")
    print("=" * 80)

    # 1. Final decision catalog
    print(f"Final Decision Enum: {FinalDecision.RESEARCH_ONLY.value}")

    # 2. Evidence assembly request
    req = evidence_request()
    print(
        f"Is EvidenceAssemblyRequest instance: {isinstance(req, EvidenceAssemblyRequest)}"
    )

    # 3. Build optimization evidence
    result = build_optimization_evidence(req)
    print(f"Built OptimizationResult contract version: {result.contract_version}")
    print(f"Reproducibility hash: {result.reproducibility_hash[:8]}...")

    # 4. Build report package handoff
    pkg = build_report_package(result)
    print(f"Report package schema ID: {pkg['schema_id']}")


def main() -> None:
    """Run Optimization evidence usage example."""
    example_evidence()


if __name__ == "__main__":
    main()
