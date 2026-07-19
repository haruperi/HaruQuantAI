"""Versioned contracts for Optimization results and handoffs."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.optimization.robustness import MonteCarloResult  # noqa: TC001
from app.services.optimization.search import SearchSummary  # noqa: TC001
from app.services.optimization.validation import WalkForwardResult  # noqa: TC001
from app.utils import canonical_json, logger

_SHA256_HEX_LENGTH = 64


class FinalDecision(StrEnum):
    """Synchronous advisory Optimization decisions."""

    READY_FOR_RISK_REVIEW = "ready_for_risk_review"
    VALIDATION_NEEDED = "validation_needed"
    RESEARCH_ONLY = "research_only"
    REJECTED = "rejected"
    FAILED = "failed"


class EvidenceAssemblyRequest(BaseModel):
    """Supplied evidence required to assemble an Optimization result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    search: SearchSummary
    walk_forward: WalkForwardResult | None = None
    monte_carlo: MonteCarloResult | None = None
    robustness: Mapping[str, object] | None = None
    analytics_evidence: Mapping[str, object] | None = None
    risk_evidence: Mapping[str, object] | None = None
    chart_data: Mapping[str, object] | None = None
    audit_references: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_request(self) -> EvidenceAssemblyRequest:
        """Validate JSON safety and source-evidence identity.

        Returns:
            Validated evidence assembly request.

        Raises:
            ValueError: If supplied evidence is non-canonical or contradictory.
        """
        logger.debug("Validating Optimization evidence assembly request")
        try:
            canonical_json(self.model_dump(mode="json"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Optimization evidence must be JSON-safe") from exc
        if any(not value.strip() for value in self.audit_references):
            raise ValueError("audit references cannot be blank")
        return self


class OptimizationResult(BaseModel):
    """Advisory Optimization result contract version one."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["optimization.result.v1"] = "optimization.result.v1"
    search_id: str
    reproducibility_hash: str
    ranked_candidates: tuple[Mapping[str, object], ...]
    diagnostics: Mapping[str, object]
    warnings: tuple[str, ...]
    chart_data: Mapping[str, object]
    audit_references: tuple[str, ...]
    final_decision: FinalDecision

    @field_validator("reproducibility_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate the canonical SHA-256 evidence identity.

        Args:
            value: Candidate evidence hash.

        Returns:
            Validated lowercase hash.

        Raises:
            ValueError: If the hash is malformed.
        """
        logger.debug("Validating Optimization reproducibility hash")
        if len(value) != _SHA256_HEX_LENGTH or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("reproducibility hash must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def _validate_result(self) -> OptimizationResult:
        """Validate advisory JSON-safe result evidence.

        Returns:
            Validated Optimization result.

        Raises:
            ValueError: If identity, authority, or serialization is invalid.
        """
        logger.debug("Validating Optimization result v1")
        if not self.search_id.startswith("search-"):
            raise ValueError("Optimization result requires canonical search identity")
        prohibited = {"trade_authority", "strategy_mutation", "approved_for_live"}
        if prohibited.intersection(self.diagnostics):
            raise ValueError("Optimization result cannot claim execution authority")
        try:
            canonical_json(self.model_dump(mode="json"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Optimization result must be JSON-safe") from exc
        return self


__all__ = ["EvidenceAssemblyRequest", "FinalDecision", "OptimizationResult"]
