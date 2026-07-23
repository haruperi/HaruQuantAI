"""Typed results used by the Optimization public operations."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.optimization.robustness import (
    ExecutionStressRequest,
    MonteCarloRequest,
    MonteCarloResult,
)
from app.utils import canonical_json, logger


class ExecutionStressAnalysisRequest(BaseModel):
    """Explicit stress request paired with same-unit outcome records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcomes: tuple[Mapping[str, object], ...]
    stress: ExecutionStressRequest

    @model_validator(mode="after")
    def _validate_request(self) -> ExecutionStressAnalysisRequest:
        """Validate non-empty JSON-safe stress inputs.

        Returns:
            Validated stress analysis request.

        Raises:
            ValueError: If outcome evidence is empty or non-JSON-safe.
        """
        logger.debug("Validating Optimization public stress analysis request")
        if not self.outcomes:
            raise ValueError("stress analysis outcomes cannot be empty")
        try:
            canonical_json(self.model_dump(mode="json"), max_items=None)
        except (TypeError, ValueError) as exc:
            raise ValueError("stress analysis request must be JSON-safe") from exc
        return self


class RobustnessAnalysisResult(BaseModel):
    """Versioned public robustness evidence without hidden calculations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["optimization.robustness.v1"] = "optimization.robustness.v1"
    monte_carlo: MonteCarloResult | None = None
    stressed_outcomes: tuple[Mapping[str, object], ...] = ()
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_result(self) -> RobustnessAnalysisResult:
        """Require exactly one supported robustness evidence form.

        Returns:
            Validated robustness result.

        Raises:
            ValueError: If both or neither evidence forms are supplied.
        """
        logger.debug("Validating Optimization public robustness result")
        if (self.monte_carlo is None) == (not self.stressed_outcomes):
            raise ValueError("robustness result requires exactly one evidence form")
        return self


class OptimizationComparison(BaseModel):
    """Typed comparison of compatible Optimization results."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["optimization.comparison.v1"] = "optimization.comparison.v1"
    search_ids: tuple[str, ...]
    decisions: tuple[str, ...]
    best_candidate_hashes: tuple[str | None, ...]


class ParameterStabilityEvidence(BaseModel):
    """Typed exact-match parameter stability evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_count: int
    stable_parameters: tuple[str, ...]
    varying_parameters: tuple[str, ...]
    stability_percentage: float

    @model_validator(mode="after")
    def _validate_evidence(self) -> ParameterStabilityEvidence:
        """Validate finite bounded stability evidence.

        Returns:
            Validated parameter stability evidence.

        Raises:
            ValueError: If counts or percentage are invalid.
        """
        logger.debug("Validating Optimization parameter stability evidence")
        maximum_percentage = 100
        if (
            self.candidate_count <= 0
            or not math.isfinite(self.stability_percentage)
            or not 0 <= self.stability_percentage <= maximum_percentage
            or set(self.stable_parameters).intersection(self.varying_parameters)
        ):
            raise ValueError("parameter stability evidence is inconsistent")
        return self


class OverfitParameterEvidence(BaseModel):
    """Typed parameter-level IS/OOS degradation evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    threshold: float
    degradation: Mapping[str, float | None]
    flagged_parameters: tuple[str, ...]


class RobustnessScore(BaseModel):
    """Typed percentage over supplied applicable Boolean checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    passed_checks: int
    applicable_checks: int
    percentage: float


RobustnessRequest = MonteCarloRequest | ExecutionStressAnalysisRequest

__all__ = [
    "ExecutionStressAnalysisRequest",
    "OptimizationComparison",
    "OverfitParameterEvidence",
    "ParameterStabilityEvidence",
    "RobustnessAnalysisResult",
    "RobustnessRequest",
    "RobustnessScore",
]
