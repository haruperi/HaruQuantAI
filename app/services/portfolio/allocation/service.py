"""Governed Portfolio allocation activation and rollback service."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.services.portfolio.contracts import ActivePortfolioAllocation
from app.services.portfolio.exceptions import PortfolioError
from app.services.risk import (
    AllocationBudgetActivationRequest,
    ApprovalAttestation,
    ApprovalValidationResult,
    DecisionState,
    KillSwitchState,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.portfolio.config import PortfolioSettings
    from app.services.portfolio.contracts import PortfolioConstructionResult
    from app.services.portfolio.state import AuditOutboxRecord, PortfolioRepository
    from app.services.risk import AllocationRiskDecision
    from app.services.simulator import PortfolioSimulationResult

type RiskBudgetActivator = Callable[
    [AllocationBudgetActivationRequest, "AllocationRiskDecision"],
    "AllocationRiskDecision",
]


def _digest(value: object) -> str:
    """Hash supported canonical allocation material.

    Args:
        value: Supported primitive allocation material.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing governed Portfolio allocation material")
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class AllocationService:
    """Activate exactly one immutable allocation after all gates pass."""

    def __init__(
        self,
        settings: PortfolioSettings,
        repository: PortfolioRepository,
        risk_budget_activator: RiskBudgetActivator,
    ) -> None:
        """Initialize allocation governance dependencies.

        Args:
            settings: Complete explicit Portfolio settings.
            repository: Portfolio-owned repository.
            risk_budget_activator: Risk receiver operation.
        """
        logger.info("Initializing Portfolio allocation service")
        self._settings = settings
        self._repository = repository
        self._activate_risk_budget = risk_budget_activator

    def _validate_gates(
        self,
        candidate: PortfolioConstructionResult,
        simulation: PortfolioSimulationResult,
        risk_decision: AllocationRiskDecision,
        kill_switches: Sequence[KillSwitchState],
        approval_attestation: ApprovalAttestation | None,
        approval_validation: ApprovalValidationResult | None,
        runtime_profile: str,
        activated_at: datetime,
    ) -> None:
        """Validate Simulation, Risk, kill-switch, and human approval gates.

        Args:
            candidate: Complete construction candidate.
            simulation: Completed Simulation validation.
            risk_decision: Current Risk allocation authorization.
            kill_switches: Applicable canonical Risk kill-switch states.
            approval_attestation: Conditional authenticated human evidence.
            approval_validation: Conditional Risk validation result.
            runtime_profile: Requested runtime profile.
            activated_at: Injected activation time.

        Raises:
            PortfolioError: If any activation gate is absent or invalid.
        """
        logger.info("Validating all Portfolio activation gates")
        if activated_at.tzinfo is None or activated_at.utcoffset() != timedelta(0):
            raise PortfolioError("PORT_INVALID_INPUT", "ACTIVATED_AT_NOT_UTC")
        if (
            simulation.status != "completed"
            or simulation.portfolio_id != candidate.portfolio_id
            or simulation.construction_result_id != candidate.result_id
            or simulation.construction_version != candidate.portfolio_version
        ):
            raise PortfolioError("PORT_SIMULATION_INVALID", "CANDIDATE_BINDING")
        if (
            risk_decision.portfolio_id != candidate.portfolio_id
            or risk_decision.reviewed_version != candidate.portfolio_version
            or risk_decision.state is not DecisionState.APPROVE
            or risk_decision.active
            or risk_decision.issued_at > activated_at
            or risk_decision.expires_at <= activated_at
            or activated_at - risk_decision.issued_at
            > timedelta(
                seconds=self._settings.portfolio_allocation_decision_ttl_seconds
            )
        ):
            raise PortfolioError("PORT_RISK_AUTHORIZATION_INVALID", "DECISION")
        if not kill_switches or any(item.state != "inactive" for item in kill_switches):
            raise PortfolioError("PORT_KILL_SWITCH_ACTIVE", "ACTIVATION")
        policy_ref = self._settings.portfolio_activation_approval_policy.get(
            runtime_profile
        )
        if policy_ref is None:
            raise PortfolioError("PORT_CONFIG_INVALID", "APPROVAL_POLICY")
        if runtime_profile == "simulation":
            if policy_ref != "automatic_within_policy":
                raise PortfolioError("PORT_CONFIG_INVALID", "SIMULATION_APPROVAL")
            return
        if runtime_profile not in {"paper", "live"}:
            raise PortfolioError("PORT_INVALID_INPUT", "RUNTIME_PROFILE")
        if (
            approval_attestation is None
            or approval_validation is None
            or not approval_validation.valid
            or not approval_validation.consumed
            or approval_attestation.policy_ref != policy_ref
            or dict(approval_attestation.scope) != dict(candidate.scope)
            or approval_attestation.action != "portfolio.activate"
            or approval_attestation.expires_at <= activated_at
        ):
            raise PortfolioError("PORT_APPROVAL_REQUIRED", "ACTIVATION")

    def activate(
        self,
        candidate: PortfolioConstructionResult,
        *,
        simulation: PortfolioSimulationResult,
        risk_decision: AllocationRiskDecision,
        kill_switches: Sequence[KillSwitchState],
        approval_attestation: ApprovalAttestation | None,
        approval_validation: ApprovalValidationResult | None,
        runtime_profile: str,
        activated_at: datetime,
        expires_at: datetime,
        idempotency_key: str,
        expected_predecessor: str | None,
        expected_revision: int,
        audit_ref: str,
        audit_record: AuditOutboxRecord,
        rollback_of_version: str | None = None,
    ) -> ActivePortfolioAllocation:
        """Activate one new governed immutable allocation version.

        Args:
            candidate: Complete construction candidate.
            simulation: Completed Simulation validation.
            risk_decision: Current Risk allocation authorization.
            kill_switches: Applicable Risk kill-switch states.
            approval_attestation: Conditional human approval evidence.
            approval_validation: Conditional Risk approval validation.
            runtime_profile: Requested runtime profile.
            activated_at: Injected UTC activation time.
            expires_at: Explicit UTC allocation expiry.
            idempotency_key: Deterministic activation identity.
            expected_predecessor: Caller-observed predecessor version.
            expected_revision: Caller-observed active-scope revision.
            audit_ref: Required audit evidence reference.
            audit_record: Redacted atomic audit outbox record.
            rollback_of_version: Historical version selected by rollback.

        Returns:
            Activated immutable allocation.

        Raises:
            PortfolioError: If a gate, Risk mutation, or persistence fails.
        """
        logger.info("Activating governed Portfolio allocation")
        self._validate_gates(
            candidate,
            simulation,
            risk_decision,
            kill_switches,
            approval_attestation,
            approval_validation,
            runtime_profile,
            activated_at,
        )
        if expires_at <= activated_at:
            raise PortfolioError("PORT_INVALID_INPUT", "ALLOCATION_EXPIRY")
        activation_request = AllocationBudgetActivationRequest(
            portfolio_id=candidate.portfolio_id,
            allocation_version=candidate.portfolio_version,
            decision_id=risk_decision.decision_id,
            scope=candidate.scope,
            effective_at=activated_at,
            predecessor_version=expected_predecessor,
            request_id=candidate.request_id,
            workflow_id=candidate.workflow_id,
            correlation_id=candidate.correlation_id,
        )
        try:
            activated_risk = self._activate_risk_budget(
                activation_request,
                risk_decision,
            )
        except PortfolioError:
            raise
        except Exception as error:
            raise PortfolioError(
                "PORT_DEPENDENCY_FAILED",
                "RISK_BUDGET_ACTIVATION",
            ) from error
        if (
            not activated_risk.active
            or activated_risk.state is not DecisionState.APPROVE
            or activated_risk.decision_id != risk_decision.decision_id
        ):
            raise PortfolioError("PORT_RISK_AUTHORIZATION_INVALID", "ACTIVATION")
        material = {
            "approval_attestation_id": (
                None
                if approval_attestation is None
                else approval_attestation.attestation_id
            ),
            "candidate_hash": candidate.canonical_hash,
            "expires_at": expires_at,
            "idempotency_key": idempotency_key,
            "predecessor_version": expected_predecessor,
            "risk_decision_id": activated_risk.decision_id,
            "rollback_of_version": rollback_of_version,
            "simulation_result_hash": simulation.result_hash,
        }
        canonical_hash = _digest(material)
        allocation = ActivePortfolioAllocation(
            allocation_id=f"portfolio-allocation-{canonical_hash[:32]}",
            portfolio_id=candidate.portfolio_id,
            allocation_version=candidate.portfolio_version,
            scope=candidate.scope,
            construction_result_id=candidate.result_id,
            construction_result_hash=candidate.canonical_hash,
            component_weights=candidate.component_weights,
            simulation_result_id=simulation.result_id,
            simulation_result_hash=simulation.result_hash,
            risk_decision_id=activated_risk.decision_id,
            risk_budget_projection_ref=activated_risk.decision_id,
            approval_attestation_id=(
                None
                if approval_attestation is None
                else approval_attestation.attestation_id
            ),
            predecessor_version=expected_predecessor,
            rollback_of_version=rollback_of_version,
            activated_at=activated_at,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            canonical_hash=canonical_hash,
            request_id=candidate.request_id,
            workflow_id=candidate.workflow_id,
            correlation_id=candidate.correlation_id,
            audit_ref=audit_ref,
        )
        return self._repository.activate(
            allocation,
            expected_predecessor=expected_predecessor,
            expected_revision=expected_revision,
            audit_record=audit_record,
        )


__all__: tuple[str, ...] = ("AllocationService", "RiskBudgetActivator")
