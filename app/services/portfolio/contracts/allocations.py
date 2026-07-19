"""Active Portfolio allocation and immutable rebalance plan contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Self

from pydantic import field_serializer, field_validator, model_validator

from app.services.portfolio.contracts.requests import (
    PortfolioContractModel,
    _decimal,
    _hash,
    _text,
    _utc,
)
from app.services.portfolio.contracts.results import (
    PortfolioComponentWeight,  # noqa: TC001
)
from app.utils import logger

PlanStatus = Literal[
    "no_action",
    "review_required",
    "blocked",
    "executed",
    "executed_unmeasured",
    "measured",
]


class ActivePortfolioAllocation(PortfolioContractModel):
    """Canonical immutable governed allocation version.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        allocation_id: Immutable allocation identity.
        portfolio_id: Portfolio identity.
        allocation_version: Immutable allocation version.
        scope: Exact governed scope.
        construction_result_id: Construction candidate reference.
        construction_result_hash: Candidate canonical digest.
        component_weights: Ordered capital/proposed-budget metadata.
        simulation_result_id: Simulation validation reference.
        simulation_result_hash: Simulation result digest.
        risk_decision_id: Risk allocation decision reference.
        risk_budget_projection_ref: Risk authoritative projection reference.
        approval_attestation_id: Conditional human approval reference.
        predecessor_version: Previously active version.
        rollback_of_version: Historical version selected by rollback.
        activated_at: UTC activation time.
        expires_at: UTC allocation expiry.
        idempotency_key: Activation idempotency identity.
        canonical_hash: Allocation canonical digest.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        audit_ref: Required audit evidence reference.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.active_allocation.v1"] = (
        "portfolio.active_allocation.v1"
    )
    allocation_id: str
    portfolio_id: str
    allocation_version: str
    scope: Mapping[str, str]
    construction_result_id: str
    construction_result_hash: str
    component_weights: tuple[PortfolioComponentWeight, ...]
    simulation_result_id: str
    simulation_result_hash: str
    risk_decision_id: str
    risk_budget_projection_ref: str
    approval_attestation_id: str | None = None
    predecessor_version: str | None = None
    rollback_of_version: str | None = None
    activated_at: datetime
    expires_at: datetime
    idempotency_key: str
    canonical_hash: str
    request_id: str
    workflow_id: str
    correlation_id: str
    audit_ref: str

    @field_validator(
        "allocation_id",
        "portfolio_id",
        "allocation_version",
        "construction_result_id",
        "simulation_result_id",
        "risk_decision_id",
        "risk_budget_projection_ref",
        "idempotency_key",
        "request_id",
        "workflow_id",
        "correlation_id",
        "audit_ref",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required allocation text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        logger.debug("Validating active allocation identity")
        return _text(value, "active allocation identity")

    @field_validator(
        "approval_attestation_id",
        "predecessor_version",
        "rollback_of_version",
    )
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate optional allocation reference.

        Args:
            value: Candidate optional text.

        Returns:
            Validated text or ``None``.
        """
        logger.debug("Validating optional active allocation reference")
        return None if value is None else _text(value, "allocation reference")

    @field_validator(
        "construction_result_hash",
        "simulation_result_hash",
        "canonical_hash",
    )
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one allocation digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        logger.debug("Validating active allocation digest")
        return _hash(value, "allocation hash")

    @field_validator("activated_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one allocation UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating active allocation timestamp")
        return _utc(value, "allocation timestamp")

    @field_validator("scope", mode="after")
    @classmethod
    def _freeze_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze a non-empty allocation scope.

        Args:
            value: Candidate scope.

        Returns:
            Frozen sorted scope.

        Raises:
            ValueError: If scope is empty.
        """
        logger.debug("Freezing active allocation scope")
        if not value:
            raise ValueError("active allocation scope is required")
        return MappingProxyType(dict(sorted(value.items())))

    @field_serializer("scope", when_used="json")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize active allocation scope.

        Args:
            value: Frozen scope mapping.

        Returns:
            Plain ordered mapping.
        """
        logger.debug("Serializing active allocation scope")
        return dict(value)

    @model_validator(mode="after")
    def _validate_allocation(self) -> Self:
        """Validate active allocation history and expiry invariants.

        Returns:
            Validated active allocation.

        Raises:
            ValueError: If history, ordering, or time relationships are invalid.
        """
        logger.info("Validating complete active Portfolio allocation")
        if self.expires_at <= self.activated_at:
            raise ValueError("active allocation expiry must follow activation")
        component_ids = tuple(item.component_id for item in self.component_weights)
        if not component_ids or component_ids != tuple(sorted(component_ids)):
            raise ValueError("allocation components must be non-empty and ordered")
        if self.rollback_of_version is not None and self.predecessor_version is None:
            raise ValueError("rollback requires a predecessor version")
        if self.rollback_of_version == self.allocation_version:
            raise ValueError("rollback cannot reference the new version")
        return self


class DriftObservation(PortfolioContractModel):
    """Actual-versus-target Risk-budget drift for one component.

    Attributes:
        component_id: Component identity.
        target_risk_budget: Target authoritative budget fraction.
        actual_risk_budget: Actual exposure fraction.
        drift: Signed actual-minus-target difference.
        threshold_breached: Whether absolute drift reaches the configured threshold.
    """

    component_id: str
    target_risk_budget: Decimal
    actual_risk_budget: Decimal
    drift: Decimal
    threshold_breached: bool

    @field_validator("component_id")
    @classmethod
    def _validate_component(cls, value: str) -> str:
        """Validate drift component identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating drift component identity")
        return _text(value, "component_id")

    @field_validator("target_risk_budget", "actual_risk_budget", "drift")
    @classmethod
    def _validate_value(cls, value: Decimal) -> Decimal:
        """Validate one finite drift value.

        Args:
            value: Candidate Decimal.

        Returns:
            Validated finite Decimal.
        """
        logger.debug("Validating Portfolio drift Decimal")
        return _decimal(value, "drift value")

    @model_validator(mode="after")
    def _validate_observation(self) -> Self:
        """Validate exact drift arithmetic.

        Returns:
            Validated drift observation.

        Raises:
            ValueError: If exposure values or drift conflict.
        """
        logger.debug("Validating Portfolio drift observation")
        if self.target_risk_budget < 0 or self.actual_risk_budget < 0:
            raise ValueError("Risk-budget exposure cannot be negative")
        if self.drift != self.actual_risk_budget - self.target_risk_budget:
            raise ValueError("drift must equal actual minus target")
        return self


class PortfolioRebalanceAction(PortfolioContractModel):
    """One deterministic reduce-only Portfolio plan action.

    Attributes:
        action_id: Immutable action identity.
        component_id: Component identity.
        action: Fixed reduce-exposure classification.
        reduce_only: Fixed safety property.
        current_exposure: Observed current exposure.
        target_exposure: Approved target exposure.
        reduction_amount: Exact current-minus-target reduction.
        eligibility_decision_id: Current Risk eligibility reference.
    """

    action_id: str
    component_id: str
    action: Literal["reduce_exposure"]
    reduce_only: Literal[True]
    current_exposure: Decimal
    target_exposure: Decimal
    reduction_amount: Decimal
    eligibility_decision_id: str

    @field_validator("action_id", "component_id", "eligibility_decision_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one action identity.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        logger.debug("Validating Portfolio rebalance action identity")
        return _text(value, "rebalance action identity")

    @field_validator("current_exposure", "target_exposure", "reduction_amount")
    @classmethod
    def _validate_exposure(cls, value: Decimal) -> Decimal:
        """Validate a finite non-negative action exposure.

        Args:
            value: Candidate exposure.

        Returns:
            Validated exposure.

        Raises:
            ValueError: If the exposure is negative.
        """
        logger.debug("Validating Portfolio rebalance action exposure")
        parsed = _decimal(value, "rebalance exposure")
        if parsed < 0:
            raise ValueError("rebalance exposure cannot be negative")
        return parsed

    @model_validator(mode="after")
    def _validate_action(self) -> Self:
        """Validate exact positive reduction arithmetic.

        Returns:
            Validated reduce-only action.

        Raises:
            ValueError: If the action does not reduce exposure exactly.
        """
        logger.debug("Validating complete reduce-only action")
        if self.current_exposure <= self.target_exposure:
            raise ValueError("reduce-only action requires excess exposure")
        if self.reduction_amount != self.current_exposure - self.target_exposure:
            raise ValueError("reduction amount must equal current minus target")
        return self


class PortfolioRebalancePlan(PortfolioContractModel):
    """Immutable version-bound drift assessment and reduce-only plan."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.rebalance_plan.v1"] = "portfolio.rebalance_plan.v1"
    plan_id: str
    plan_version: str
    portfolio_id: str
    allocation_version: str
    scope: Mapping[str, str]
    observations: tuple[DriftObservation, ...]
    actions: tuple[PortfolioRebalanceAction, ...]
    status: PlanStatus
    block_reasons: tuple[str, ...]
    evidence_hash: str
    config_hash: str
    canonical_hash: str
    observed_at: datetime
    created_at: datetime
    risk_decision_id: str | None = None
    trading_execution_ref: str | None = None
    analytics_measurement_ref: str | None = None
    request_id: str
    workflow_id: str
    correlation_id: str

    @field_validator(
        "plan_id",
        "plan_version",
        "portfolio_id",
        "allocation_version",
        "request_id",
        "workflow_id",
        "correlation_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required plan identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating Portfolio rebalance plan identity")
        return _text(value, "rebalance plan identity")

    @field_validator(
        "risk_decision_id",
        "trading_execution_ref",
        "analytics_measurement_ref",
    )
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate optional plan outcome reference.

        Args:
            value: Candidate optional reference.

        Returns:
            Validated reference or ``None``.
        """
        logger.debug("Validating optional rebalance plan reference")
        return None if value is None else _text(value, "plan reference")

    @field_validator("evidence_hash", "config_hash", "canonical_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one plan digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        logger.debug("Validating Portfolio rebalance plan digest")
        return _hash(value, "rebalance plan hash")

    @field_validator("observed_at", "created_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one plan UTC timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating Portfolio rebalance plan timestamp")
        return _utc(value, "rebalance plan timestamp")

    @field_validator("scope", mode="after")
    @classmethod
    def _freeze_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Freeze the non-empty plan scope.

        Args:
            value: Candidate scope.

        Returns:
            Frozen sorted scope.

        Raises:
            ValueError: If scope is empty.
        """
        logger.debug("Freezing Portfolio rebalance plan scope")
        if not value:
            raise ValueError("rebalance plan scope is required")
        return MappingProxyType(dict(sorted(value.items())))

    @field_serializer("scope", when_used="json")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize plan scope deterministically.

        Args:
            value: Frozen scope mapping.

        Returns:
            Plain ordered mapping.
        """
        logger.debug("Serializing Portfolio rebalance plan scope")
        return dict(value)

    @field_validator("block_reasons")
    @classmethod
    def _validate_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate unique ordered safe block reasons.

        Args:
            value: Candidate reason codes.

        Returns:
            Validated reason codes.

        Raises:
            ValueError: If reason codes are duplicated or unordered.
        """
        logger.debug("Validating Portfolio rebalance block reasons")
        validated = tuple(_text(item, "block reason") for item in value)
        if len(set(validated)) != len(validated) or validated != tuple(
            sorted(validated)
        ):
            raise ValueError("block reasons must be unique and ordered")
        return validated

    @model_validator(mode="after")
    def _validate_plan(self) -> Self:
        """Validate plan ordering and lifecycle references.

        Returns:
            Validated rebalance plan.

        Raises:
            ValueError: If status, actions, references, or times conflict.
        """
        logger.info("Validating complete Portfolio rebalance plan")
        if self.created_at < self.observed_at:
            raise ValueError("plan cannot be created before observation")
        observation_ids = tuple(item.component_id for item in self.observations)
        action_ids = tuple(item.action_id for item in self.actions)
        if not observation_ids or observation_ids != tuple(sorted(observation_ids)):
            raise ValueError("drift observations must be non-empty and ordered")
        if action_ids != tuple(sorted(action_ids)) or len(set(action_ids)) != len(
            action_ids
        ):
            raise ValueError("rebalance actions must be unique and ordered")
        if self.status == "no_action" and (self.actions or self.block_reasons):
            raise ValueError("no-action plan cannot carry actions or blockers")
        if self.status == "review_required" and not self.actions:
            raise ValueError("review-required plan must carry reductions")
        if self.status == "blocked" and not self.block_reasons:
            raise ValueError("blocked plan requires reasons")
        if self.status in {
            "executed",
            "executed_unmeasured",
            "measured",
        } and (self.risk_decision_id is None or self.trading_execution_ref is None):
            raise ValueError("executed plan requires Risk and Trading references")
        if self.status == "measured" and self.analytics_measurement_ref is None:
            raise ValueError("measured plan requires Analytics reference")
        return self


__all__: tuple[str, ...] = (
    "ActivePortfolioAllocation",
    "DriftObservation",
    "PlanStatus",
    "PortfolioRebalanceAction",
    "PortfolioRebalancePlan",
)
