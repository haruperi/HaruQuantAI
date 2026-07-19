"""Tests for versioned Optimization evidence contracts."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.evidence import (
    EvidenceAssemblyRequest,
    FinalDecision,
    OptimizationResult,
    build_optimization_evidence,
)
from app.services.optimization.search import run_bounded_search
from pydantic import ValidationError
from tests.optimization.unit.test_search_contracts import search_request
from tests.optimization.unit.test_sweep import FakeAdapter


def evidence_request(**overrides: object) -> EvidenceAssemblyRequest:
    """Build valid baseline supplied search evidence."""
    payload: dict[str, object] = {
        "search": run_bounded_search(search_request(), FakeAdapter()),
        "chart_data": {"objective": [1.0]},
        "audit_references": ("audit-1",),
    }
    payload.update(overrides)
    return EvidenceAssemblyRequest.model_validate(payload)


def test_final_decision_values_are_canonical() -> None:
    """Only approved synchronous advisory decisions exist."""
    assert {item.value for item in FinalDecision} == {
        "ready_for_risk_review",
        "validation_needed",
        "research_only",
        "rejected",
        "failed",
    }


def test_evidence_request_rejects_non_json_data() -> None:
    """Provider objects cannot cross the evidence boundary."""
    with pytest.raises((ValidationError, ValueError), match="JSON-safe"):
        evidence_request(chart_data={"provider": object()})


def test_optimization_result_is_advisory() -> None:
    """Result diagnostics cannot claim trade or Strategy authority."""
    result = build_optimization_evidence(evidence_request())
    payload = result.model_dump(mode="python")
    payload["diagnostics"] = {"approved_for_live": True}
    with pytest.raises(ValidationError, match="execution authority"):
        OptimizationResult.model_validate(payload)
