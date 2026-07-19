"""Bounded readiness assessment across route and Risk evidence."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.risk import KillSwitchState, RiskDecisionPackage
from app.services.risk.contracts import DecisionState
from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.contracts.models import JsonValue
from app.services.trading.validation.snapshots import RouteSnapshot
from app.utils import logger, to_json_safe

_MAX_FAILED_CHECKS = 32


class ReadinessAssessment(BaseModel):
    """Immutable bounded pass/fail readiness result.

    Attributes:
        passed: Whether every mandatory readiness check passed.
        failed_check_codes: Ordered finite failed-check evidence.
        evidence_refs: Exact source references used by the assessment.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: bool
    failed_check_codes: tuple[str, ...]
    evidence_refs: Mapping[str, JsonValue]
    assessed_at: datetime

    @field_validator("failed_check_codes")
    @classmethod
    def _validate_codes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate bounded unique failed-check codes.

        Args:
            value: Candidate failed-check codes.

        Returns:
            Validated ordered codes.

        Raises:
            ValueError: If codes are blank, duplicated, or unbounded.
        """
        logger.debug("Validating ReadinessAssessment failed codes")
        if len(value) > _MAX_FAILED_CHECKS:
            raise ValueError("readiness failed-check evidence is unbounded")
        if any(not item or item != item.strip() for item in value):
            raise ValueError("readiness check codes must be non-empty and trimmed")
        if len(set(value)) != len(value):
            raise ValueError("readiness check codes must be unique")
        return value

    @field_validator("evidence_refs", mode="before")
    @classmethod
    def _validate_refs(cls, value: Mapping[str, object]) -> Mapping[str, JsonValue]:
        """Validate and freeze readiness evidence references.

        Args:
            value: Candidate evidence references.

        Returns:
            Immutable JSON-safe references.

        Raises:
            TypeError: If references do not serialize to a mapping.
        """
        logger.debug("Validating ReadinessAssessment evidence references")
        safe = to_json_safe(value)
        if not isinstance(safe, dict):
            raise TypeError("readiness evidence references must be a mapping")
        return MappingProxyType(safe)

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        """Validate pass/fail consistency.

        Returns:
            Validated assessment.

        Raises:
            ValueError: If pass state conflicts with failed checks.
        """
        logger.debug("Validating ReadinessAssessment consistency")
        if self.passed == bool(self.failed_check_codes):
            raise ValueError("readiness pass state conflicts with failed checks")
        if not self.evidence_refs:
            raise ValueError("readiness assessment requires evidence references")
        return self


def _policy_time(value: JsonValue) -> datetime | None:
    """Parse an action-policy UTC expiry without inventing evidence.

    Args:
        value: JSON-safe expiry evidence.

    Returns:
        Parsed timestamp or ``None`` when malformed.
    """
    logger.debug("Parsing Trading action-policy expiry evidence")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed


def _append_snapshot_failures(
    failed: list[str],
    request: TradingRequest,
    snapshot: RouteSnapshot,
    max_staleness_seconds: Decimal,
) -> None:
    """Append failed route-evidence check codes.

    Args:
        failed: Mutable ordered failed-code accumulator.
        request: Governed Trading request.
        snapshot: Explicit route evidence.
        max_staleness_seconds: Exact positive route-evidence age bound.
    """
    logger.debug("Checking Trading route readiness evidence")
    if not snapshot.available or not snapshot.fresh:
        failed.append("ROUTE_EVIDENCE_UNAVAILABLE")
    age = Decimal(str((request.system_time - snapshot.observed_at).total_seconds()))
    if snapshot.expires_at <= request.system_time or age > max_staleness_seconds:
        failed.append("ROUTE_EVIDENCE_STALE")
    if request.action not in snapshot.capabilities:
        failed.append("ACTION_CAPABILITY_MISSING")


def _append_risk_failures(
    failed: list[str],
    request: TradingRequest,
    risk_decision: RiskDecisionPackage,
    kill_switch_state: KillSwitchState,
    max_staleness_seconds: Decimal,
    kill_switch_max_staleness_seconds: Decimal,
) -> None:
    """Append failed Risk-decision and kill-switch check codes.

    Args:
        failed: Mutable ordered failed-code accumulator.
        request: Governed Trading request.
        risk_decision: Risk-owned decision package.
        kill_switch_state: Risk-owned switch state.
        max_staleness_seconds: Exact positive Risk-decision age bound.
        kill_switch_max_staleness_seconds: Exact positive kill-switch age bound.
    """
    logger.debug("Checking Trading Risk readiness evidence")
    if risk_decision.decision_id != request.risk_decision_id:
        failed.append("RISK_DECISION_MISMATCH")
    if risk_decision.state is not DecisionState.APPROVE:
        failed.append("RISK_NOT_APPROVED")
    age = Decimal(str((request.system_time - risk_decision.issued_at).total_seconds()))
    if risk_decision.expires_at <= request.system_time or age > max_staleness_seconds:
        failed.append("RISK_DECISION_STALE")
    if request.quantity is not None and risk_decision.approved_size != request.quantity:
        failed.append("RISK_SIZE_MISMATCH")
    if risk_decision.intent_id != request.intent_id:
        failed.append("RISK_INTENT_MISMATCH")
    if kill_switch_state.state != "inactive":
        failed.append("KILL_SWITCH_BLOCKING")
    kill_switch_age = Decimal(
        str((request.system_time - kill_switch_state.updated_at).total_seconds())
    )
    if kill_switch_age > kill_switch_max_staleness_seconds:
        failed.append("KILL_SWITCH_STALE")


def _append_policy_failures(
    failed: list[str],
    request: TradingRequest,
    action_policy: Mapping[str, JsonValue],
) -> None:
    """Append failed action-policy check codes.

    Args:
        failed: Mutable ordered failed-code accumulator.
        request: Governed Trading request.
        action_policy: Risk-owned action-policy projection.
    """
    logger.debug("Checking Trading action-policy readiness evidence")
    if action_policy.get("allowed") is not True:
        failed.append("ACTION_POLICY_DENIED")
    if action_policy.get("verdict_id") != request.action_policy_verdict_id:
        failed.append("ACTION_POLICY_MISMATCH")
    if action_policy.get("action") != request.action:
        failed.append("ACTION_POLICY_SCOPE_MISMATCH")
    policy_expiry = _policy_time(action_policy.get("expires_at"))
    if policy_expiry is None or policy_expiry <= request.system_time:
        failed.append("ACTION_POLICY_STALE")


def assess_execution_readiness(
    request: TradingRequest,
    snapshot: RouteSnapshot,
    risk_decision: RiskDecisionPackage,
    kill_switch_state: KillSwitchState,
    action_policy: Mapping[str, JsonValue],
    max_staleness_seconds: Mapping[str, Decimal],
) -> ReadinessAssessment:
    """Aggregate all mandatory execution readiness evidence.

    Args:
        request: Governed canonical request.
        snapshot: Explicit route facts.
        risk_decision: Risk-owned canonical decision package.
        kill_switch_state: Risk-owned canonical switch state.
        action_policy: Risk-owned action-policy verdict projection.
        max_staleness_seconds: Exact positive bounds for route, Risk, and
            kill-switch evidence.

    Returns:
        Bounded deterministic pass/fail assessment.

    Raises:
        TradingError: If required staleness policy is absent or invalid.
    """
    logger.info("Assessing mandatory Trading execution readiness")
    required_bounds = {"route_snapshot", "risk_decision", "kill_switch"}
    if set(max_staleness_seconds) != required_bounds or any(
        not isinstance(value, Decimal) or not value.is_finite() or value <= 0
        for value in max_staleness_seconds.values()
    ):
        raise TradingError(
            "CONFIGURATION_INVALID", "Readiness staleness policy is invalid"
        )
    failed: list[str] = []
    _append_snapshot_failures(
        failed,
        request,
        snapshot,
        max_staleness_seconds["route_snapshot"],
    )
    _append_risk_failures(
        failed,
        request,
        risk_decision,
        kill_switch_state,
        max_staleness_seconds["risk_decision"],
        max_staleness_seconds["kill_switch"],
    )
    _append_policy_failures(failed, request, action_policy)
    return ReadinessAssessment(
        passed=not failed,
        failed_check_codes=tuple(failed),
        evidence_refs={
            "snapshot_source_id": snapshot.source_id,
            "snapshot_authority_id": snapshot.authority_id,
            "risk_decision_id": risk_decision.decision_id,
            "kill_switch_state_id": kill_switch_state.state_id,
            "action_policy_verdict_id": action_policy.get("verdict_id"),
        },
        assessed_at=request.system_time,
    )


__all__ = ["ReadinessAssessment", "assess_execution_readiness"]
