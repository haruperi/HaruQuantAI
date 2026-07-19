"""Tests for typed Optimization public-operation results."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.optimization.public_api.contracts import (
    ExecutionStressAnalysisRequest,
    RobustnessAnalysisResult,
)
from app.services.optimization.robustness import ExecutionStressRequest
from pydantic import ValidationError


def test_stress_analysis_request_requires_outcomes() -> None:
    """Public execution stress requires explicit same-unit outcomes."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        ExecutionStressAnalysisRequest(
            outcomes=(),
            stress=ExecutionStressRequest(kind="spread", value=Decimal("0.1")),
        )


def test_robustness_result_requires_one_evidence_form() -> None:
    """Public robustness results cannot be empty or contradictory."""
    with pytest.raises(ValidationError, match="exactly one"):
        RobustnessAnalysisResult()
