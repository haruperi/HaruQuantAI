"""Immutable Portfolio construction results and structured outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, Self

from pydantic import field_serializer, field_validator, model_validator

from app.services.portfolio.contracts.requests import (
    ConstructionMethod,
    PortfolioContractModel,
    _decimal,
    _hash,
    _text,
    _utc,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.portfolio.exceptions import PortfolioErrorPayload


class PortfolioComponentWeight(PortfolioContractModel):
    """Constructed capital and proposed Risk-budget metadata.

    Attributes:
        component_id: Stable Portfolio component identity.
        strategy_id: Strategy identity.
        strategy_version: Exact Strategy version.
        capital_weight: Target capital metadata weight.
        proposed_risk_budget_weight: Non-authoritative proposed budget weight.
    """

    component_id: str
    strategy_id: str
    strategy_version: str
    capital_weight: Decimal
    proposed_risk_budget_weight: Decimal

    @field_validator("component_id", "strategy_id", "strategy_version")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one component identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating constructed component identity")
        return _text(value, "component identity")

    @field_validator("capital_weight", "proposed_risk_budget_weight")
    @classmethod
    def _validate_weight(cls, value: Decimal) -> Decimal:
        """Validate one bounded weight basis value.

        Args:
            value: Candidate weight.

        Returns:
            Validated non-negative finite weight.

        Raises:
            ValueError: If the weight is negative.
        """
        logger.debug("Validating constructed Portfolio weight")
        parsed = _decimal(value, "component weight")
        if parsed < 0:
            raise ValueError("component weight must be non-negative")
        return parsed


class PortfolioConstructionResult(PortfolioContractModel):
    """Published deterministic Portfolio construction candidate.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        result_id: Immutable result identity.
        portfolio_id: Portfolio identity.
        portfolio_version: Immutable requested version.
        scope: Governed scope.
        status: Final constructed status.
        component_weights: Ordered constructed weights.
        method: Construction method.
        config_hash: Complete policy configuration digest.
        evidence_hash: Complete evidence-lineage digest.
        strategy_lineage_hash: Strategy reference digest.
        canonical_hash: Digest over all result material except itself.
        created_at: UTC construction time.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional parent action identity.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.construction_result.v1"] = (
        "portfolio.construction_result.v1"
    )
    result_id: str
    portfolio_id: str
    portfolio_version: str
    scope: Mapping[str, str]
    status: Literal["constructed"]
    component_weights: tuple[PortfolioComponentWeight, ...]
    method: ConstructionMethod
    config_hash: str
    evidence_hash: str
    strategy_lineage_hash: str
    canonical_hash: str
    created_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None

    @field_validator(
        "result_id",
        "portfolio_id",
        "portfolio_version",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one construction result identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating Portfolio construction result identity")
        return _text(value, "construction result identity")

    @field_validator("causation_id")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate optional causation identity.

        Args:
            value: Candidate optional identity.

        Returns:
            Validated identity or ``None``.
        """
        logger.debug("Validating result causation identity")
        return None if value is None else _text(value, "causation_id")

    @field_validator(
        "config_hash",
        "evidence_hash",
        "strategy_lineage_hash",
        "canonical_hash",
    )
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one result digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        logger.debug("Validating Portfolio construction result digest")
        return _hash(value, "construction result hash")

    @field_validator("created_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate result creation time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating Portfolio result creation time")
        return _utc(value, "created_at")

    @field_validator("scope", mode="after")
    @classmethod
    def _freeze_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze the non-empty result scope.

        Args:
            value: Candidate scope.

        Returns:
            Frozen sorted scope.

        Raises:
            ValueError: If the scope is empty.
        """
        logger.debug("Freezing Portfolio construction result scope")
        if not value:
            raise ValueError("result scope is required")
        return MappingProxyType(dict(sorted(value.items())))

    @field_serializer("scope", when_used="json")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize result scope deterministically.

        Args:
            value: Frozen scope.

        Returns:
            Plain ordered scope.
        """
        logger.debug("Serializing Portfolio result scope")
        return dict(value)

    @model_validator(mode="after")
    def _validate_result(self) -> Self:
        """Validate result ordering and weight totals.

        Returns:
            Validated construction result.

        Raises:
            ValueError: If component ordering or totals are invalid.
        """
        logger.info("Validating complete Portfolio construction result")
        component_ids = tuple(item.component_id for item in self.component_weights)
        if not component_ids or component_ids != tuple(sorted(component_ids)):
            raise ValueError("result components must be non-empty and ordered")
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("result components must be unique")
        for field in ("capital_weight", "proposed_risk_budget_weight"):
            total = sum(
                (getattr(item, field) for item in self.component_weights),
                Decimal(0),
            )
            if total != Decimal(1):
                raise ValueError("published component weights must total exactly one")
        return self


@dataclass(frozen=True, slots=True)
class PortfolioOutcome[T]:
    """Structured success or error envelope for Portfolio operations.

    Attributes:
        ok: Whether the operation succeeded.
        request_id: Request trace identity.
        correlation_id: Correlation trace identity.
        value: Success value when `ok` is true.
        error: Structured failure when `ok` is false.
        audit_event_id: Optional emitted audit event identity.
    """

    ok: bool
    request_id: str
    correlation_id: str
    value: T | None = None
    error: PortfolioErrorPayload | None = None
    audit_event_id: str | None = None

    def __post_init__(self) -> None:
        """Validate envelope exclusivity and trace identities.

        Raises:
            ValueError: If value/error exclusivity is violated.
        """
        logger.debug("Validating Portfolio operation outcome")
        _text(self.request_id, "request_id")
        _text(self.correlation_id, "correlation_id")
        if self.ok != (self.error is None) or (self.value is None) == self.ok:
            raise ValueError(
                "Portfolio outcome must contain exactly one value or error"
            )


__all__: tuple[str, ...] = (
    "PortfolioComponentWeight",
    "PortfolioConstructionResult",
    "PortfolioOutcome",
)
