"""Runnable usage evidence for Optimization result requirements."""

from app.services.optimization.evidence import (
    EvidenceAssemblyRequest,
    FinalDecision,
    OptimizationResult,
    build_optimization_evidence,
    build_report_package,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request


def test_usage_contracts_final_decision() -> None:
    """Consume the advisory decision catalog."""
    assert FinalDecision.RESEARCH_ONLY.value == "research_only"


def test_usage_contracts_evidence_assembly_request() -> None:
    """Construct supplied evidence without side effects."""
    assert isinstance(evidence_request(), EvidenceAssemblyRequest)


def test_usage_contracts_optimization_result() -> None:
    """Consume the versioned advisory result."""
    result = build_optimization_evidence(evidence_request())
    assert isinstance(result, OptimizationResult)
    assert result.contract_version == "v1"


def test_usage_assemble_build_optimization_evidence() -> None:
    """Assemble a canonical result from supplied evidence."""
    assert build_optimization_evidence(evidence_request()).reproducibility_hash


def test_usage_handoff_build_report_package() -> None:
    """Build chart-ready and table-ready handoff data."""
    result = build_optimization_evidence(evidence_request())
    assert build_report_package(result)["schema_id"] == "optimization.result.v1"
