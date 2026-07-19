"""Typed bounded-search requests and results."""

from __future__ import annotations

import math
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.optimization.execution import BacktestExecutionContext  # noqa: TC001
from app.services.optimization.parameters import (  # noqa: TC001
    ParameterSpace,
    ParameterValue,
)
from app.services.optimization.scoring import (  # noqa: TC001
    CandidateScore,
    ObjectiveName,
)
from app.utils import logger

_SHA256_HEX_LENGTH = 64


class SearchMethod(StrEnum):
    """Supported V1 parameter-search methods."""

    GRID = "grid"
    RANDOM = "random"


class CandidateState(StrEnum):
    """Terminal state of one evaluated candidate."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"


class SearchRequest(BaseModel):
    """Complete bounded deterministic search request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    space: ParameterSpace
    execution_context: BacktestExecutionContext
    method: SearchMethod
    objective: ObjectiveName
    enabled_objectives: frozenset[ObjectiveName]
    seed: int | None = None
    candidate_count: int | None = None
    max_candidates: int
    max_parameter_space_expansion: int
    max_constraint_count: int
    max_runtime_seconds: float
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_request(self) -> SearchRequest:
        """Validate method-specific bounds and objective enablement.

        Returns:
            Validated search request.

        Raises:
            ValueError: If method, objective, seed, or bounds conflict.
        """
        logger.debug("Validating Optimization search request")
        if self.objective not in self.enabled_objectives:
            raise ValueError("selected objective must be enabled")
        if (
            self.max_candidates <= 0
            or self.max_parameter_space_expansion <= 0
            or self.max_constraint_count <= 0
            or not math.isfinite(self.max_runtime_seconds)
            or self.max_runtime_seconds <= 0
        ):
            raise ValueError("search resource bounds must be finite and positive")
        if self.method is SearchMethod.RANDOM:
            if self.seed is None or self.candidate_count is None:
                raise ValueError("random search requires seed and candidate_count")
            if not 0 < self.candidate_count <= self.max_candidates:
                raise ValueError("random candidate_count exceeds its bound")
        elif self.seed is not None or self.candidate_count is not None:
            raise ValueError("grid search cannot define random-only fields")
        return self


class CandidateResult(BaseModel):
    """One accepted, rejected, or failed search candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_hash: str
    executable_parameters: Mapping[str, ParameterValue]
    state: CandidateState
    score: CandidateScore | None = None
    reason_code: str | None = None
    evidence: Mapping[str, object] | None = None

    @model_validator(mode="after")
    def _validate_candidate(self) -> CandidateResult:
        """Validate terminal-state evidence relationships.

        Returns:
            Validated candidate result.

        Raises:
            ValueError: If identity or state evidence conflicts.
        """
        logger.debug("Validating Optimization candidate result")
        if len(self.candidate_hash) != _SHA256_HEX_LENGTH:
            raise ValueError("candidate result hash is malformed")
        if self.state is CandidateState.ACCEPTED:
            if self.score is None or self.reason_code is not None:
                raise ValueError("accepted candidates require score only")
        elif self.score is not None or not self.reason_code:
            raise ValueError("rejected and failed candidates require a reason only")
        return self


class SearchSummary(BaseModel):
    """Completed deterministic bounded-search evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    search_id: str
    request_hash: str
    method: SearchMethod
    objective: ObjectiveName
    candidates: tuple[CandidateResult, ...]
    best_candidate_hash: str | None
    runtime_ms: float
    warnings: tuple[str, ...] = ()

    @field_validator("runtime_ms")
    @classmethod
    def _validate_runtime(cls, value: float) -> float:
        """Validate measured search runtime.

        Args:
            value: Runtime in milliseconds.

        Returns:
            Finite non-negative runtime.

        Raises:
            ValueError: If runtime is invalid.
        """
        logger.debug("Validating Optimization search runtime")
        if not math.isfinite(value) or value < 0:
            raise ValueError("search runtime must be finite and non-negative")
        return value

    @model_validator(mode="after")
    def _validate_summary(self) -> SearchSummary:
        """Validate search identity, uniqueness, and best candidate.

        Returns:
            Validated search summary.

        Raises:
            ValueError: If summary evidence is inconsistent.
        """
        logger.debug("Validating Optimization search summary")
        if not self.search_id.startswith("search-"):
            raise ValueError("search_id must use the search prefix")
        if len(self.request_hash) != _SHA256_HEX_LENGTH:
            raise ValueError("request_hash is malformed")
        hashes = tuple(item.candidate_hash for item in self.candidates)
        if len(set(hashes)) != len(hashes):
            raise ValueError("search candidates must be unique")
        accepted = {
            item.candidate_hash
            for item in self.candidates
            if item.state is CandidateState.ACCEPTED
        }
        if (
            self.best_candidate_hash is not None
            and self.best_candidate_hash not in accepted
        ):
            raise ValueError("best candidate must reference accepted evidence")
        if accepted and self.best_candidate_hash is None:
            raise ValueError("accepted search requires a best candidate")
        return self


__all__ = [
    "CandidateResult",
    "CandidateState",
    "SearchMethod",
    "SearchRequest",
    "SearchSummary",
]
