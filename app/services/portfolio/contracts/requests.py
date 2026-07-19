"""Strict Portfolio construction request and supporting value rows."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import ClassVar, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic import ValidationError as PydanticValidationError

from app.services.portfolio.exceptions import PortfolioError
from app.utils import logger

ConstructionMethod = Literal["fixed", "equal", "inverse_volatility"]
RuntimeProfile = Literal["simulation", "paper", "live"]
ExecutionRoute = Literal["sim", "paper", "live"]
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _text(value: str, field: str) -> str:
    """Validate non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.

    Returns:
        Validated text.

    Raises:
        ValueError: If text is empty or untrimmed.
    """
    logger.debug("Validating Portfolio text field %s", field)
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Safe field label for validation.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the value is naive or non-UTC.
    """
    logger.debug("Validating Portfolio UTC field %s", field)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


def _decimal(value: Decimal, field: str) -> Decimal:
    """Validate one finite Decimal.

    Args:
        value: Candidate exact numeric value.
        field: Safe field label for validation.

    Returns:
        Validated finite Decimal.

    Raises:
        ValueError: If the value is non-finite.
    """
    logger.debug("Validating Portfolio Decimal field %s", field)
    if not value.is_finite():
        message = f"{field} must be finite"
        raise ValueError(message)
    return value


def _hash(value: str, field: str) -> str:
    """Validate lowercase SHA-256 hexadecimal.

    Args:
        value: Candidate digest.
        field: Safe field label for validation.

    Returns:
        Validated digest.

    Raises:
        ValueError: If the digest shape is invalid.
    """
    logger.debug("Validating Portfolio digest field %s", field)
    if _SHA256.fullmatch(value) is None:
        message = f"{field} must be lowercase SHA-256 hexadecimal"
        raise ValueError(message)
    return value


class PortfolioContractModel(BaseModel):
    """Private strict immutable behavior shared by Portfolio contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        allow_inf_nan=False,
    )

    def __init__(self, **data: object) -> None:
        """Validate contract input and normalize validation failures.

        Args:
            data: Candidate contract fields.

        Raises:
            PortfolioError: If contract validation fails.
        """
        logger.debug("Validating Portfolio contract %s", type(self).__name__)
        try:
            super().__init__(**data)
        except PydanticValidationError as error:
            raise PortfolioError("PORT_INVALID_INPUT", "CONTRACT_VALIDATION") from error


class StrategyAllocationRef(PortfolioContractModel):
    """Exact immutable Strategy and Risk eligibility reference.

    Attributes:
        component_id: Portfolio-local stable component identity.
        strategy_id: Strategy-owned immutable identity.
        strategy_version: Exact Strategy version.
        registry_record_hash: Strategy registry record digest.
        eligibility_decision_id: Risk eligibility decision reference.
    """

    component_id: str
    strategy_id: str
    strategy_version: str
    registry_record_hash: str
    eligibility_decision_id: str

    @field_validator(
        "component_id",
        "strategy_id",
        "strategy_version",
        "eligibility_decision_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one identity field.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating Strategy allocation identity")
        return _text(value, "strategy allocation identity")

    @field_validator("registry_record_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate the registry digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        logger.debug("Validating Strategy registry digest")
        return _hash(value, "registry_record_hash")


class EvidenceReferenceSet(PortfolioContractModel):
    """Complete owner-reference and freshness lineage for construction.

    Attributes:
        account_snapshot_id: Data account snapshot reference.
        account_snapshot_hash: Account snapshot digest.
        account_snapshot_as_of: Account snapshot observation time.
        market_dataset_id: Data market dataset reference.
        market_dataset_hash: Market dataset digest.
        market_dataset_as_of: Market evidence observation time.
        analytics_evidence_id: Analytics evidence reference.
        analytics_evidence_hash: Analytics evidence digest.
        analytics_evidence_as_of: Analytics evidence observation time.
        fx_evidence_ids: Ordered Data FX evidence references.
        fx_evidence_hashes: Ordered digest aligned to each FX reference.
    """

    account_snapshot_id: str
    account_snapshot_hash: str
    account_snapshot_as_of: datetime
    market_dataset_id: str
    market_dataset_hash: str
    market_dataset_as_of: datetime
    analytics_evidence_id: str
    analytics_evidence_hash: str
    analytics_evidence_as_of: datetime
    fx_evidence_ids: tuple[str, ...]
    fx_evidence_hashes: tuple[str, ...]

    @field_validator(
        "account_snapshot_id",
        "market_dataset_id",
        "analytics_evidence_id",
    )
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one evidence identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating Portfolio evidence identity")
        return _text(value, "evidence identity")

    @field_validator(
        "account_snapshot_hash",
        "market_dataset_hash",
        "analytics_evidence_hash",
    )
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate one evidence digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        logger.debug("Validating Portfolio evidence digest")
        return _hash(value, "evidence hash")

    @field_validator(
        "account_snapshot_as_of",
        "market_dataset_as_of",
        "analytics_evidence_as_of",
    )
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one evidence timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating Portfolio evidence time")
        return _utc(value, "evidence timestamp")

    @model_validator(mode="after")
    def _validate_fx(self) -> Self:
        """Validate ordered aligned FX lineage.

        Returns:
            Validated evidence reference set.

        Raises:
            ValueError: If FX identities and hashes are inconsistent.
        """
        logger.debug("Validating Portfolio FX evidence lineage")
        ids = tuple(_text(item, "fx evidence id") for item in self.fx_evidence_ids)
        hashes = tuple(
            _hash(item, "fx evidence hash") for item in self.fx_evidence_hashes
        )
        if len(ids) != len(hashes) or len(set(ids)) != len(ids):
            raise ValueError("FX evidence identities and hashes must align uniquely")
        if ids != tuple(sorted(ids)):
            raise ValueError("FX evidence identities must be ordered")
        return self


class FixedWeightInput(PortfolioContractModel):
    """Explicit fixed construction weights for one component.

    Attributes:
        component_id: Referenced component identity.
        capital_weight: Target capital metadata weight.
        proposed_risk_budget_weight: Non-authoritative proposed Risk budget weight.
    """

    component_id: str
    capital_weight: Decimal
    proposed_risk_budget_weight: Decimal

    @field_validator("component_id")
    @classmethod
    def _validate_component(cls, value: str) -> str:
        """Validate the component identity.

        Args:
            value: Candidate identity.

        Returns:
            Validated identity.
        """
        logger.debug("Validating fixed-weight component identity")
        return _text(value, "component_id")

    @field_validator("capital_weight", "proposed_risk_budget_weight")
    @classmethod
    def _validate_weight(cls, value: Decimal) -> Decimal:
        """Validate a finite non-negative weight.

        Args:
            value: Candidate weight.

        Returns:
            Validated weight.

        Raises:
            ValueError: If weight is negative or non-finite.
        """
        logger.debug("Validating fixed Portfolio weight")
        parsed = _decimal(value, "weight")
        if parsed < 0:
            raise ValueError("weight must be non-negative")
        return parsed


class PortfolioConstructionRequest(PortfolioContractModel):
    """Portfolio-owned deterministic construction command.

    Attributes:
        contract_version: Compatibility version.
        schema_id: Namespaced schema identity.
        request_id: Request trace identity.
        workflow_id: Workflow trace identity.
        correlation_id: Correlation trace identity.
        causation_id: Optional parent action identity.
        portfolio_id: Stable Portfolio identity.
        portfolio_version: Caller-selected immutable version.
        scope: Exact governed scope.
        components: Ordered component references.
        method: Approved construction method.
        fixed_weights: Conditional fixed method values.
        evidence: Complete evidence reference lineage.
        measurement_start: UTC evidence window start.
        measurement_end: UTC evidence window end.
        base_currency: ISO-like three-letter base currency.
        runtime_profile: Requested governed runtime profile.
        execution_route: Compatible execution route.
        simulation_policy_version: Exact simulation policy version.
        requested_at: UTC command time.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["portfolio.construction_request.v1"] = (
        "portfolio.construction_request.v1"
    )
    request_id: str
    workflow_id: str
    correlation_id: str
    causation_id: str | None = None
    portfolio_id: str
    portfolio_version: str
    scope: Mapping[str, str]
    components: tuple[StrategyAllocationRef, ...]
    method: ConstructionMethod
    fixed_weights: tuple[FixedWeightInput, ...]
    evidence: EvidenceReferenceSet
    measurement_start: datetime
    measurement_end: datetime
    base_currency: str
    runtime_profile: RuntimeProfile
    execution_route: ExecutionRoute
    simulation_policy_version: str
    requested_at: datetime

    _TEXT_FIELDS: ClassVar[tuple[str, ...]] = (
        "request_id",
        "workflow_id",
        "correlation_id",
        "portfolio_id",
        "portfolio_version",
        "simulation_policy_version",
    )

    @field_validator(*_TEXT_FIELDS)
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required request text.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        logger.debug("Validating Portfolio construction request text")
        return _text(value, "construction request text")

    @field_validator("causation_id")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate optional causation identity.

        Args:
            value: Candidate optional identity.

        Returns:
            Validated identity or ``None``.
        """
        logger.debug("Validating Portfolio causation identity")
        return None if value is None else _text(value, "causation_id")

    @field_validator("scope", mode="after")
    @classmethod
    def _freeze_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze construction scope.

        Args:
            value: Candidate scope mapping.

        Returns:
            Frozen scope mapping.

        Raises:
            ValueError: If scope is empty.
        """
        logger.debug("Validating Portfolio construction scope")
        if not value:
            raise ValueError("Portfolio scope is required")
        return MappingProxyType(
            {
                _text(key, "scope key"): _text(item, "scope value")
                for key, item in sorted(value.items())
            }
        )

    @field_serializer("scope", when_used="json")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize frozen scope deterministically.

        Args:
            value: Frozen scope mapping.

        Returns:
            Plain ordered mapping.
        """
        logger.debug("Serializing Portfolio construction scope")
        return dict(value)

    @field_validator("measurement_start", "measurement_end", "requested_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate request UTC time.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        logger.debug("Validating Portfolio construction timestamp")
        return _utc(value, "construction timestamp")

    @field_validator("base_currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        """Validate uppercase three-letter base currency.

        Args:
            value: Candidate currency.

        Returns:
            Validated currency.

        Raises:
            ValueError: If currency shape is invalid.
        """
        logger.debug("Validating Portfolio base currency")
        currency_code_length = 3
        if (
            len(value) != currency_code_length
            or not value.isalpha()
            or value != value.upper()
        ):
            raise ValueError("base_currency must be three uppercase letters")
        return value

    @model_validator(mode="after")
    def _validate_request(self) -> Self:
        """Validate method, ordering, profile, and window invariants.

        Returns:
            Validated construction request.

        Raises:
            ValueError: If request relationships are inconsistent.
        """
        logger.info("Validating complete Portfolio construction request")
        if self.measurement_start >= self.measurement_end:
            raise ValueError("measurement window must increase")
        if self.requested_at < self.measurement_end:
            raise ValueError("request cannot precede measurement evidence")
        component_ids = tuple(item.component_id for item in self.components)
        strategy_refs = tuple(
            (item.strategy_id, item.strategy_version) for item in self.components
        )
        if not component_ids or len(set(component_ids)) != len(component_ids):
            raise ValueError("components must be non-empty and unique")
        if len(set(strategy_refs)) != len(strategy_refs):
            raise ValueError("strategy versions must be unique")
        if component_ids != tuple(sorted(component_ids)):
            raise ValueError("components must be ordered by component_id")
        weight_ids = tuple(item.component_id for item in self.fixed_weights)
        if self.method == "fixed" and weight_ids != component_ids:
            raise ValueError("fixed method requires one ordered weight per component")
        if self.method != "fixed" and self.fixed_weights:
            raise ValueError("non-fixed methods cannot carry fixed weights")
        expected_route = {
            "simulation": "sim",
            "paper": "paper",
            "live": "live",
        }[self.runtime_profile]
        if self.execution_route != expected_route:
            raise ValueError("runtime profile and execution route are incompatible")
        return self


__all__: tuple[str, ...] = (
    "ConstructionMethod",
    "EvidenceReferenceSet",
    "ExecutionRoute",
    "FixedWeightInput",
    "PortfolioConstructionRequest",
    "PortfolioContractModel",
    "RuntimeProfile",
    "StrategyAllocationRef",
)
