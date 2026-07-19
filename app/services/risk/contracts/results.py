"""Strict Risk-owned result and state contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.risk.contracts.enums import DecisionState, LimitStatus, RiskErrorCode
from app.utils import is_sensitive_key, logger

_SHA256_HEX_LENGTH = 64


def _utc(value: datetime) -> datetime:
    """Require aware UTC time.

    Args:
        value: Time to validate.

    Returns:
        Validated time.

    Raises:
        ValueError: If time is not aware UTC.
    """
    logger.debug("Validating Risk result UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


class _ResultModel(BaseModel):
    """Private strict immutable Risk result base."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
    )


class RiskLimitResult(_ResultModel):
    """One ordered policy-limit result without approval authority."""

    limit_id: str
    status: LimitStatus
    observed_value: Decimal | None
    threshold_value: Decimal | None
    reason_code: RiskErrorCode | None
    evidence_refs: tuple[str, ...]
    precedence: int

    @model_validator(mode="after")
    def _validate_limit(self) -> RiskLimitResult:
        """Validate status and reason consistency.

        Returns:
            Validated result.

        Raises:
            ValueError: If state and reason conflict.
        """
        logger.debug("Validating ordered Risk limit result")
        failing = self.status in {
            LimitStatus.FAIL,
            LimitStatus.BLOCKED,
            LimitStatus.NEEDS_MORE_EVIDENCE,
        }
        if failing != (self.reason_code is not None):
            raise ValueError("limit reason is inconsistent with status")
        if self.precedence < 0:
            raise ValueError("precedence must be non-negative")
        return self


class PositionSizingResult(_ResultModel):
    """Deterministic sizing recommendation that never grants approval."""

    method: str
    requested_size: Decimal | None
    calculated_size: Decimal
    normalized_size: Decimal
    constraints_applied: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    fallback_used: bool
    fallback_reason: str | None
    correlation_adjustment: Decimal | None
    approved: Literal[False] = False

    @model_validator(mode="after")
    def _validate_sizing(self) -> PositionSizingResult:
        """Validate sizing result invariants.

        Returns:
            Validated result.

        Raises:
            ValueError: If values or fallback disclosure conflict.
        """
        logger.debug("Validating position-sizing result")
        if self.calculated_size < 0 or self.normalized_size < 0:
            raise ValueError("sizes must be non-negative")
        if self.fallback_used != (self.fallback_reason is not None):
            raise ValueError("fallback disclosure is inconsistent")
        return self


class RegimeAssessment(_ResultModel):
    """Classified Risk regime with equal-or-stricter modifiers."""

    assessment_id: str
    states: Mapping[str, Literal["normal", "elevated", "high", "unknown"]]
    previous_states: Mapping[str, str]
    transitions: tuple[str, ...]
    modifiers: Mapping[str, Decimal]
    evidence_refs: tuple[str, ...]
    missing_fields: tuple[str, ...]
    assessed_at: datetime

    @model_validator(mode="after")
    def _validate_regime(self) -> RegimeAssessment:
        """Validate regime time and tightening modifiers.

        Returns:
            Validated assessment.

        Raises:
            ValueError: If a modifier loosens limits.
        """
        logger.debug("Validating regime assessment")
        _utc(self.assessed_at)
        if any(value <= 0 or value > 1 for value in self.modifiers.values()):
            raise ValueError("regime modifiers may only tighten")
        return self


class ScenarioResult(_ResultModel):
    """Registered deterministic advisory scenario result version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.scenario_result.v1"] = "risk.scenario_result.v1"
    scenario_id: str
    baseline: Mapping[str, Decimal]
    projected: Mapping[str, Decimal]
    differences: Mapping[str, Decimal]
    assumptions: tuple[str, ...]
    seed: int | None
    policy_version: str
    evidence_refs: tuple[str, ...]
    warnings: tuple[str, ...]
    generated_at: datetime
    advisory_only: Literal[True] = True
    approved: Literal[False] = False

    @field_validator("generated_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate generation time.

        Args:
            value: Time to validate.

        Returns:
            Validated time.
        """
        logger.debug("Validating ScenarioResult time")
        return _utc(value)


class RiskApprovalToken(_ResultModel):
    """Signed scoped Risk approval token without key material."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.approval_token.v1"] = "risk.approval_token.v1"
    token_id: str
    decision_id: str
    config_hash: str
    action: str
    scope: Mapping[str, str]
    approver_id: str
    issued_at: datetime
    expires_at: datetime
    nonce: str
    signature: str
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_token(self) -> RiskApprovalToken:
        """Validate token lifetime and bindings.

        Returns:
            Validated token.

        Raises:
            ValueError: If lifetime or scope is invalid.
        """
        logger.debug("Validating Risk approval token")
        _utc(self.issued_at)
        _utc(self.expires_at)
        if self.expires_at <= self.issued_at or not self.scope:
            raise ValueError("token requires valid lifetime and scope")
        return self


class ActionPolicyVerdict(_ResultModel):
    """Risk-owned action permission bound to durable token reservation."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.action_policy_verdict.v1"] = (
        "risk.action_policy_verdict.v1"
    )
    verdict_id: str
    action: str
    scope: Mapping[str, str]
    policy_version: str
    attestation_id: str
    decision_id: str
    reservation_id: str
    allowed: bool
    reasons: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_verdict(self) -> ActionPolicyVerdict:
        """Validate durable reservation and expiry.

        Returns:
            Validated verdict.

        Raises:
            ValueError: If reservation or lifetime is absent.
        """
        logger.debug("Validating action-policy verdict")
        _utc(self.issued_at)
        _utc(self.expires_at)
        if self.expires_at <= self.issued_at or not self.reservation_id:
            raise ValueError("verdict requires reservation and valid expiry")
        if self.allowed and self.reasons:
            raise ValueError("allowed verdict cannot contain denial reasons")
        return self


class RiskDecisionPackage(_ResultModel):
    """Canonical RiskDecision version 1 package."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.risk_decision_package.v1"] = (
        "risk.risk_decision_package.v1"
    )
    decision_id: str
    intent_id: str | None
    state: DecisionState
    requested_size: Decimal | None
    approved_size: Decimal | None
    ordered_checks: tuple[RiskLimitResult, ...]
    primary_failure_limit: str | None
    composite_breach_flags: tuple[str, ...]
    evidence_refs: Mapping[str, str]
    config_hash: str
    concurrency_disclosure: str
    recommendations: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    token: RiskApprovalToken | None
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_decision(self) -> RiskDecisionPackage:
        """Validate verdict, size, reason, and token consistency.

        Returns:
            Validated decision.

        Raises:
            ValueError: If decision invariants conflict.
        """
        logger.debug("Validating canonical Risk decision package")
        _utc(self.issued_at)
        _utc(self.expires_at)
        if self.expires_at <= self.issued_at or not self.evidence_refs:
            raise ValueError("decision requires provenance and valid expiry")
        approving = self.state is DecisionState.APPROVE
        trade_decision = self.intent_id is not None
        if (
            approving
            and trade_decision
            and (self.approved_size is None or self.approved_size <= 0)
        ):
            raise ValueError("trade approval requires positive approved size")
        if approving and not trade_decision and self.approved_size is not None:
            raise ValueError("current-state compliance cannot carry approved size")
        if not approving and self.approved_size is not None:
            raise ValueError("non-approval cannot carry approved size")
        if self.token is not None and not approving:
            raise ValueError("token requires approving decision")
        return self


class KillSwitchState(_ResultModel):
    """Canonical scoped Risk kill-switch state version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.kill_switch_state.v1"] = "risk.kill_switch_state.v1"
    state_id: str
    scope_level: Literal["global", "portfolio", "strategy", "symbol"]
    scope: Mapping[str, str]
    state: Literal["active", "inactive", "unknown"]
    reason: str
    version: int
    updated_at: datetime

    @model_validator(mode="after")
    def _validate_state(self) -> KillSwitchState:
        """Validate canonical state version and time.

        Returns:
            Validated state.

        Raises:
            ValueError: If version or scope is invalid.
        """
        logger.debug("Validating kill-switch state")
        _utc(self.updated_at)
        if self.version < 0 or (self.scope_level != "global" and not self.scope):
            raise ValueError("kill-switch state version or scope is invalid")
        return self


class RiskAuditRecord(_ResultModel):
    """Unsealed audit input or sealed tamper-evident Risk record."""

    record_id: str
    event_type: str
    payload: Mapping[str, object]
    evidence_refs: Mapping[str, str]
    config_hash: str
    decision_id: str | None
    occurred_at: datetime
    sequence: int | None
    previous_hash: str | None
    record_hash: str | None
    sealed: bool
    request_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_record(self) -> RiskAuditRecord:
        """Validate redaction and sealed-state invariants.

        Returns:
            Validated record.

        Raises:
            ValueError: If protected keys or hash state is invalid.
        """
        logger.debug("Validating Risk audit record")
        _utc(self.occurred_at)
        if any(is_sensitive_key(key) for key in self.payload):
            raise ValueError("audit payload contains protected key")
        seal_fields = (self.sequence, self.previous_hash, self.record_hash)
        if self.sealed != all(value is not None for value in seal_fields):
            raise ValueError("audit sealed state is inconsistent")
        if not self.sealed and any(value is not None for value in seal_fields):
            raise ValueError("unsealed record cannot contain chain fields")
        if self.sealed:
            if self.sequence is None or self.sequence < 0:
                raise ValueError("sealed sequence is invalid")
            for digest in (self.previous_hash, self.record_hash):
                if digest is None or len(digest) != _SHA256_HEX_LENGTH:
                    raise ValueError("sealed hash must be SHA-256 hex")
        return self


class RiskReport(_ResultModel):
    """Focused Risk Markdown or JSON report."""

    report_id: str
    format: Literal["markdown", "json"]
    content: str | Mapping[str, object]
    evidence: tuple[str, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    decision: tuple[str, ...]
    recommendations: tuple[str, ...]
    approval_claimed: bool
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate report generation time.

        Args:
            value: Time to validate.

        Returns:
            Validated time.
        """
        logger.debug("Validating Risk report time")
        return _utc(value)


class ApprovalValidationResult(_ResultModel):
    """Durable approval-token validation and consumption outcome."""

    valid: bool
    consumed: bool
    reason_code: RiskErrorCode | None
    audit_ref: str | None
    reservation_id: str | None
    action_policy_verdict: ActionPolicyVerdict | None

    @model_validator(mode="after")
    def _validate_result(self) -> ApprovalValidationResult:
        """Validate success, reason, and verdict consistency.

        Returns:
            Validated result.

        Raises:
            ValueError: If outcome fields conflict.
        """
        logger.debug("Validating approval validation result")
        if self.valid:
            if not self.consumed or self.reason_code is not None:
                raise ValueError("valid token must be consumed without reason")
            if self.action_policy_verdict is None:
                raise ValueError("valid token requires action-policy verdict")
        elif self.action_policy_verdict is not None or self.reason_code is None:
            raise ValueError("invalid token requires reason and no verdict")
        return self


class DecisionReuseValidationResult(_ResultModel):
    """Non-authorizing decision and evidence reuse validation result."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.decision_reuse_validation_result.v1"] = (
        "risk.decision_reuse_validation_result.v1"
    )
    reusable: bool
    refresh_required: bool
    reason_code: RiskErrorCode | None
    decision_id: str
    config_hash: str
    evidence_refs: Mapping[str, str]
    validated_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_reuse(self) -> DecisionReuseValidationResult:
        """Validate reusable and refresh-required outcome consistency.

        Returns:
            Validated non-authorizing reuse result.

        Raises:
            ValueError: If outcome and reason fields conflict.
        """
        logger.debug("Validating non-authorizing Risk decision reuse result")
        _utc(self.validated_at)
        if not self.evidence_refs:
            raise ValueError("decision reuse validation requires evidence")
        if self.reusable and (self.refresh_required or self.reason_code is not None):
            raise ValueError("reusable decision cannot require refresh or a reason")
        if not self.reusable and self.reason_code is None:
            raise ValueError("non-reusable decision requires a reason")
        return self


class StrategyOperationalEligibilityDecision(_ResultModel):
    """Scoped Risk-owned operational eligibility decision version 1."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.strategy_operational_eligibility_decision.v1"] = (
        "risk.strategy_operational_eligibility_decision.v1"
    )
    decision_id: str
    strategy_id: str
    strategy_version: str
    scope: Mapping[str, str]
    state: DecisionState
    conditions: tuple[str, ...]
    policy_version: str
    evidence_refs: Mapping[str, str]
    issued_at: datetime
    expires_at: datetime
    suspended: bool
    audit_ref: str

    @model_validator(mode="after")
    def _validate_decision(self) -> StrategyOperationalEligibilityDecision:
        """Validate eligibility lifetime and state.

        Returns:
            Validated decision.

        Raises:
            ValueError: If eligibility fields conflict.
        """
        logger.debug("Validating strategy eligibility decision")
        _utc(self.issued_at)
        _utc(self.expires_at)
        if self.expires_at <= self.issued_at or not self.scope:
            raise ValueError("eligibility requires scope and valid expiry")
        if self.suspended and self.state is DecisionState.APPROVE:
            raise ValueError("suspended eligibility cannot approve")
        return self


class AllocationRiskDecision(_ResultModel):
    """Risk-owned allocation decision and authoritative budget projection."""

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.allocation_risk_decision.v1"] = (
        "risk.allocation_risk_decision.v1"
    )
    decision_id: str
    portfolio_id: str
    reviewed_version: str
    state: DecisionState
    capped_weights: Mapping[str, Decimal]
    risk_budget_projection: Mapping[str, Decimal]
    conditions: tuple[str, ...]
    policy_version: str
    evidence_refs: Mapping[str, str]
    issued_at: datetime
    expires_at: datetime
    active: bool
    predecessor_version: str | None
    audit_ref: str

    @model_validator(mode="after")
    def _validate_decision(self) -> AllocationRiskDecision:
        """Validate allocation decision and projection consistency.

        Returns:
            Validated decision.

        Raises:
            ValueError: If projection or state is inconsistent.
        """
        logger.debug("Validating allocation Risk decision")
        _utc(self.issued_at)
        _utc(self.expires_at)
        if self.expires_at <= self.issued_at:
            raise ValueError("allocation decision expiry is invalid")
        if any(
            not value.is_finite() or value < 0 for value in self.capped_weights.values()
        ):
            raise ValueError("capped weights must be finite and non-negative")
        if any(
            not value.is_finite() or value < 0
            for value in self.risk_budget_projection.values()
        ):
            raise ValueError("risk-budget projection must be finite and non-negative")
        if self.active and self.state is not DecisionState.APPROVE:
            raise ValueError("only approved allocation can be active")
        return self


__all__ = [
    "ActionPolicyVerdict",
    "AllocationRiskDecision",
    "ApprovalValidationResult",
    "DecisionReuseValidationResult",
    "KillSwitchState",
    "PositionSizingResult",
    "RegimeAssessment",
    "RiskApprovalToken",
    "RiskAuditRecord",
    "RiskDecisionPackage",
    "RiskLimitResult",
    "RiskReport",
    "ScenarioResult",
    "StrategyOperationalEligibilityDecision",
]
