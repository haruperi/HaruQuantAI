"""Tests for Optimization evidence assembly."""

# ruff: noqa: INP001

from app.services.optimization.evidence import (
    FinalDecision,
    build_optimization_evidence,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request


def test_build_evidence_labels_missing_sections() -> None:
    """Missing validation sections remain explicit and block readiness."""
    result = build_optimization_evidence(evidence_request())
    assert result.final_decision is FinalDecision.VALIDATION_NEEDED
    assert "walk_forward_evidence_missing" in result.warnings
    assert result.diagnostics["walk_forward"] is None
