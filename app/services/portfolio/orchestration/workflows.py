"""Cross-domain Portfolio workflow coordination through owner-public contracts."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from app.services.analytics import (
    PortfolioAllocationEvidence,
    PortfolioRebalanceMeasurementEvidence,
    PortfolioRebalanceMeasurementRequest,
)
from app.services.portfolio.allocation import AllocationService, RiskBudgetActivator
from app.services.portfolio.construction import ConstructionService
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioConstructionRequest,
    PortfolioConstructionResult,
    PortfolioRebalancePlan,
)
from app.services.portfolio.evidence import (
    ValidatedConstructionEvidence,
    revalidate_activation_evidence,
    validate_construction_evidence,
)
from app.services.portfolio.exceptions import PortfolioError
from app.services.portfolio.rebalancing import RebalancingService
from app.services.risk import (
    AllocationReviewRequest,
    AllocationRiskDecision,
    ApprovalAttestation,
    ApprovalValidationResult,
    DecisionState,
    KillSwitchState,
    StrategyOperationalEligibilityDecision,
)
from app.services.simulator import PortfolioBacktestRequestV1, PortfolioSimulationResult
from app.services.strategy import ValidatedStrategyRef
from app.services.trading import (
    PortfolioRebalanceExecutionRequest,
    StandardTradingEnvelope,
    TradingRoute,
)
from app.utils import AuditEvent, canonical_json, generate_id, logger

if TYPE_CHECKING:
    from app.services.data.contracts import (
        AccountStateSnapshot,
        FXConversionEvidence,
        MarketDataset,
    )
    from app.services.portfolio.config import PortfolioSettings
    from app.services.portfolio.state import AuditOutboxRecord, PortfolioRepository


@dataclass(frozen=True, slots=True)
class ConstructionEvidenceInputs:
    """Resolved owner-public evidence needed for Portfolio construction.

    Attributes:
        account_snapshot: Exact Data account snapshot.
        market_dataset: Exact Data market dataset.
        analytics_evidence: Exact Analytics allocation evidence.
        fx_evidence: Evidence-ID-keyed Data FX evidence.
        component_volatilities: Analytics-resolved component volatility values.
        component_observations: Analytics-resolved component sample counts.
    """

    account_snapshot: AccountStateSnapshot
    market_dataset: MarketDataset
    analytics_evidence: PortfolioAllocationEvidence
    fx_evidence: Mapping[str, FXConversionEvidence]
    component_volatilities: Mapping[str, Decimal]
    component_observations: Mapping[str, int]

    def __post_init__(self) -> None:
        """Log creation of the immutable owner evidence input bundle."""
        logger.debug("Created Portfolio construction evidence inputs")


@dataclass(frozen=True, slots=True)
class PortfolioReviewResult:
    """Current Simulation and Risk review results for one candidate.

    Attributes:
        simulation: Complete Simulation-owned portfolio result.
        risk_decision: Current Risk-owned allocation decision.
    """

    simulation: PortfolioSimulationResult
    risk_decision: AllocationRiskDecision

    def __post_init__(self) -> None:
        """Log creation of the immutable review bundle."""
        logger.debug("Created Portfolio Simulation and Risk review result")


type StrategyReferenceSource = Callable[
    [PortfolioConstructionRequest], Mapping[str, ValidatedStrategyRef]
]
type EligibilityDecisionSource = Callable[
    [PortfolioConstructionRequest],
    Mapping[str, StrategyOperationalEligibilityDecision],
]
type ConstructionEvidenceSource = Callable[
    [PortfolioConstructionRequest], ConstructionEvidenceInputs
]
type SimulationRunner = Callable[
    [PortfolioBacktestRequestV1], PortfolioSimulationResult
]
type RiskReviewer = Callable[[AllocationReviewRequest], AllocationRiskDecision]
type KillSwitchSource = Callable[[Mapping[str, str]], Sequence[KillSwitchState]]
type TradingExecutor = Callable[
    [PortfolioRebalanceExecutionRequest], Awaitable[StandardTradingEnvelope]
]
type TradingExecutionSource = Callable[[str], StandardTradingEnvelope]
type AnalyticsMeasurer = Callable[
    [PortfolioRebalanceMeasurementRequest],
    PortfolioRebalanceMeasurementEvidence,
]
type AuditPersister = Callable[[AuditEvent], str]


@dataclass(frozen=True, slots=True)
class PortfolioWorkflowDependencies:
    """Only cross-domain composition bundle used by Portfolio workflows.

    Attributes:
        strategy_reference_source: Strategy public-reference resolver.
        eligibility_decision_source: Risk eligibility resolver.
        construction_evidence_source: Data and Analytics evidence resolver.
        simulation_runner: Simulation receiver operation.
        risk_reviewer: Risk allocation-review operation.
        risk_budget_activator: Risk budget-activation operation.
        kill_switch_source: Current Risk kill-switch resolver.
        trading_executor: Trading rebalance receiver operation.
        trading_execution_source: Read-only immutable Trading evidence resolver.
        analytics_measurer: Analytics measurement receiver operation.
        audit_persister: Utils audit persistence operation.
        clock: Injected aware UTC clock.
    """

    strategy_reference_source: StrategyReferenceSource
    eligibility_decision_source: EligibilityDecisionSource
    construction_evidence_source: ConstructionEvidenceSource
    simulation_runner: SimulationRunner
    risk_reviewer: RiskReviewer
    risk_budget_activator: RiskBudgetActivator
    kill_switch_source: KillSwitchSource
    trading_executor: TradingExecutor
    trading_execution_source: TradingExecutionSource
    analytics_measurer: AnalyticsMeasurer
    audit_persister: AuditPersister
    clock: Callable[[], datetime]

    def __post_init__(self) -> None:
        """Require every workflow dependency to be an explicit callable.

        Raises:
            PortfolioError: If any dependency is absent or not callable.
        """
        logger.info("Validating complete Portfolio workflow dependencies")
        if any(
            not callable(value)
            for value in (
                self.strategy_reference_source,
                self.eligibility_decision_source,
                self.construction_evidence_source,
                self.simulation_runner,
                self.risk_reviewer,
                self.risk_budget_activator,
                self.kill_switch_source,
                self.trading_executor,
                self.trading_execution_source,
                self.analytics_measurer,
                self.audit_persister,
                self.clock,
            )
        ):
            raise PortfolioError("PORT_UNSAFE_OBJECT", "WORKFLOW_DEPENDENCY")


def _digest(value: object) -> str:
    """Hash canonical Portfolio workflow material.

    Args:
        value: Supported canonical material.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing canonical Portfolio workflow material")
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _audit_record(event_id: str, action: str) -> AuditOutboxRecord:
    """Build a bounded redacted atomic audit outbox record.

    Args:
        event_id: Persisted Utils audit event identity.
        action: Portfolio action identity.

    Returns:
        Redacted string-only outbox record.
    """
    logger.debug("Building Portfolio atomic audit outbox record")
    return {
        "action": action,
        "audit_event_id": event_id,
        "redaction_applied": "true",
    }


class PortfolioWorkflowService:
    """Coordinate all seven Portfolio workflows without stealing ownership."""

    def __init__(
        self,
        settings: PortfolioSettings,
        repository: PortfolioRepository,
        dependencies: PortfolioWorkflowDependencies,
    ) -> None:
        """Initialize workflow services from explicit validated dependencies.

        Args:
            settings: Complete Portfolio settings.
            repository: Portfolio-owned state repository.
            dependencies: Only cross-domain composition bundle.
        """
        logger.info("Initializing Portfolio workflow service")
        self._settings = settings
        self._repository = repository
        self._deps = dependencies
        self._construction = ConstructionService(settings)
        self._allocation = AllocationService(
            settings,
            repository,
            dependencies.risk_budget_activator,
        )
        self._rebalancing = RebalancingService(settings, repository)

    def _now(self) -> datetime:
        """Return the injected aware UTC workflow time.

        Returns:
            Current injected aware UTC time.

        Raises:
            PortfolioError: If the clock does not return aware UTC.
        """
        logger.debug("Reading injected Portfolio workflow clock")
        now = self._deps.clock()
        if now.tzinfo is None or now.utcoffset() != timedelta(0):
            raise PortfolioError("PORT_INVALID_INPUT", "CLOCK_NOT_UTC")
        return now

    def _audit(
        self,
        action: str,
        *,
        request_id: str,
        correlation_id: str,
        causation_id: str | None,
        payload: Mapping[str, str | bool | None],
    ) -> str:
        """Persist one deterministic redacted Utils audit event.

        Args:
            action: Portfolio action identity.
            request_id: Request trace identity.
            correlation_id: Correlation trace identity.
            causation_id: Optional direct-cause trace identity.
            payload: Bounded secret-free event facts.

        Returns:
            Persisted audit event identity.

        Raises:
            PortfolioError: If audit persistence fails.
        """
        logger.info("Persisting redacted Portfolio workflow audit event")
        event_id = generate_id("evt")
        event = AuditEvent(
            contract_version="v1",
            schema_id="utils.audit_event.v1",
            event_id=event_id,
            timestamp=self._now(),
            domain="Portfolio",
            action=action,
            principal_id=None,
            request_id=request_id,
            correlation_id=correlation_id,
            causation_id=(
                causation_id
                if causation_id is not None and causation_id.startswith("cau-")
                else None
            ),
            payload={**payload, "redaction_applied": True},
        )
        try:
            persisted = self._deps.audit_persister(event)
        except Exception as error:
            raise PortfolioError("PORT_AUDIT_PENDING", "PERSISTENCE") from error
        if persisted != event_id:
            raise PortfolioError("PORT_AUDIT_PENDING", "IDENTITY")
        return persisted

    def validate_construction(
        self,
        request: PortfolioConstructionRequest,
    ) -> ValidatedConstructionEvidence:
        """Run WF-PORT-001 and return a complete validated evidence bundle.

        Args:
            request: Validated Portfolio construction command.

        Returns:
            Complete immutable construction evidence.
        """
        logger.info("Running Portfolio construction evidence workflow")
        owner_evidence = self._deps.construction_evidence_source(request)
        return validate_construction_evidence(
            request,
            strategy_refs=self._deps.strategy_reference_source(request),
            eligibility_decisions=self._deps.eligibility_decision_source(request),
            account_snapshot=owner_evidence.account_snapshot,
            market_dataset=owner_evidence.market_dataset,
            analytics_evidence=owner_evidence.analytics_evidence,
            fx_evidence=owner_evidence.fx_evidence,
            component_volatilities=owner_evidence.component_volatilities,
            component_observations=owner_evidence.component_observations,
            now=self._now(),
            settings=self._settings,
        )

    def construct(
        self,
        request: PortfolioConstructionRequest,
    ) -> tuple[PortfolioConstructionResult, ValidatedConstructionEvidence]:
        """Run WF-PORT-001 and WF-PORT-002 and persist the candidate.

        Args:
            request: Validated Portfolio construction command.

        Returns:
            Persisted construction result and validated evidence bundle.
        """
        logger.info("Running complete Portfolio construction workflow")
        evidence = self.validate_construction(request)
        result = self._construction.construct(evidence, created_at=self._now())
        audit_id = self._audit(
            "portfolio.constructed",
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            payload={
                "portfolio_id": result.portfolio_id,
                "result_id": result.result_id,
                "result_hash": result.canonical_hash,
            },
        )
        persisted = self._repository.save_construction(
            result,
            _audit_record(audit_id, "portfolio.constructed"),
        )
        return persisted, evidence

    def coordinate_review(
        self,
        candidate: PortfolioConstructionResult,
        simulation_request: PortfolioBacktestRequestV1,
        evidence: ValidatedConstructionEvidence,
        *,
        approval_refs: tuple[str, ...] = (),
    ) -> PortfolioReviewResult:
        """Run WF-PORT-003 using caller-supplied Simulation-owned input.

        Args:
            candidate: Complete Portfolio construction result.
            simulation_request: Fully formed receiver-owned Simulation request.
            evidence: Validated construction evidence for Risk projection.
            approval_refs: Ordered owner-provided approval references.

        Returns:
            Current Simulation and Risk review results.

        Raises:
            PortfolioError: If the receiver request or returned results conflict.
        """
        logger.info("Coordinating Portfolio Simulation and Risk review")
        self._validate_simulation_request(candidate, simulation_request)
        try:
            simulation = self._deps.simulation_runner(simulation_request)
        except Exception as error:
            raise PortfolioError("PORT_DEPENDENCY_FAILED", "SIMULATION") from error
        risk_request = self._construction_review_request(
            candidate,
            evidence,
            approval_refs=approval_refs,
        )
        self._audit(
            "portfolio.risk_review_requested",
            request_id=candidate.request_id,
            correlation_id=candidate.correlation_id,
            causation_id=candidate.causation_id,
            payload={
                "portfolio_id": candidate.portfolio_id,
                "result_id": candidate.result_id,
            },
        )
        try:
            decision = self._deps.risk_reviewer(risk_request)
        except Exception as error:
            raise PortfolioError("PORT_DEPENDENCY_FAILED", "RISK_REVIEW") from error
        now = self._now()
        if (
            simulation.status != "completed"
            or simulation.portfolio_id != candidate.portfolio_id
            or simulation.construction_result_id != candidate.result_id
            or decision.portfolio_id != candidate.portfolio_id
            or decision.reviewed_version != candidate.portfolio_version
            or decision.state is not DecisionState.APPROVE
            or decision.issued_at > now
            or decision.expires_at <= now
        ):
            raise PortfolioError("PORT_RISK_AUTHORIZATION_INVALID", "REVIEW")
        self._audit(
            "portfolio.risk_review_decided",
            request_id=candidate.request_id,
            correlation_id=candidate.correlation_id,
            causation_id=candidate.causation_id,
            payload={
                "decision_id": decision.decision_id,
                "state": decision.state.value,
            },
        )
        return PortfolioReviewResult(simulation=simulation, risk_decision=decision)

    def _validate_simulation_request(
        self,
        candidate: PortfolioConstructionResult,
        request: PortfolioBacktestRequestV1,
    ) -> None:
        """Validate a caller-supplied Simulation-owned request binding.

        Args:
            candidate: Complete Portfolio candidate.
            request: Fully formed Simulation-owned request.

        Raises:
            PortfolioError: If trace, construction, component, or route differs.
        """
        logger.debug("Validating supplied Simulation receiver request bindings")
        expected_weights = {
            row.component_id: (row.capital_weight, row.proposed_risk_budget_weight)
            for row in candidate.component_weights
        }
        observed_weights = {
            row.component_id: (row.capital_weight, row.risk_budget)
            for row in request.components
        }
        if (
            request.request_id != candidate.request_id
            or request.workflow_id != candidate.workflow_id
            or request.correlation_id != candidate.correlation_id
            or request.portfolio_id != candidate.portfolio_id
            or request.construction_result_id != candidate.result_id
            or request.construction_version != candidate.portfolio_version
            or request.runtime_profile != "simulation"
            or request.execution_route != "sim"
            or observed_weights != expected_weights
        ):
            raise PortfolioError("PORT_SIMULATION_INVALID", "REQUEST_BINDING")

    def _construction_review_request(
        self,
        candidate: PortfolioConstructionResult,
        evidence: ValidatedConstructionEvidence,
        *,
        approval_refs: tuple[str, ...],
    ) -> AllocationReviewRequest:
        """Build the exact Risk-owned construction review request.

        Args:
            candidate: Complete construction candidate.
            evidence: Validated owner evidence.
            approval_refs: Ordered owner-provided approval references.

        Returns:
            Receiver-owned self-contained Risk request.
        """
        logger.debug("Building Risk-owned Portfolio construction review request")
        request = evidence.request
        return AllocationReviewRequest(
            projection_kind="construction",
            portfolio_id=candidate.portfolio_id,
            portfolio_version=candidate.portfolio_version,
            result_id=candidate.result_id,
            plan_id=None,
            ordered_components=tuple(
                {
                    "capital_weight": str(row.capital_weight),
                    "component_id": row.component_id,
                    "proposed_risk_budget_weight": str(row.proposed_risk_budget_weight),
                    "strategy_id": row.strategy_id,
                    "strategy_version": row.strategy_version,
                }
                for row in candidate.component_weights
            ),
            eligibility_decision_refs=tuple(
                row.decision_id for row in evidence.eligibility_decisions
            ),
            account_evidence_ref=request.evidence.account_snapshot_id,
            market_evidence_ref=request.evidence.market_dataset_id,
            fx_evidence_refs=request.evidence.fx_evidence_ids,
            evidence_hashes={
                "candidate": candidate.canonical_hash,
                "evidence": evidence.evidence_hash,
                "strategy_lineage": evidence.strategy_lineage_hash,
            },
            runtime_profile=request.runtime_profile,
            execution_route=request.execution_route,
            approval_refs=approval_refs,
            requested_at=self._now(),
            request_id=candidate.request_id,
            workflow_id=candidate.workflow_id,
            correlation_id=candidate.correlation_id,
        )

    def activate(
        self,
        candidate: PortfolioConstructionResult,
        evidence: ValidatedConstructionEvidence,
        review: PortfolioReviewResult,
        *,
        approval_attestation: ApprovalAttestation | None,
        approval_validation: ApprovalValidationResult | None,
        expires_at: datetime,
        idempotency_key: str,
        expected_predecessor: str | None,
        expected_revision: int,
        rollback_of_version: str | None = None,
    ) -> ActivePortfolioAllocation:
        """Run WF-PORT-004 after immediate mutable-gate revalidation.

        Args:
            candidate: Complete construction candidate.
            evidence: Previously validated construction evidence.
            review: Current Simulation and Risk review results.
            approval_attestation: Conditional human approval evidence.
            approval_validation: Conditional Risk validation result.
            expires_at: Explicit UTC allocation expiry.
            idempotency_key: Deterministic activation identity.
            expected_predecessor: Caller-observed predecessor version.
            expected_revision: Caller-observed scope revision.
            rollback_of_version: Optional historical allocation version.

        Returns:
            Atomically activated immutable allocation.
        """
        logger.info("Running governed Portfolio activation workflow")
        now = self._now()
        revalidate_activation_evidence(
            evidence,
            strategy_refs=self._deps.strategy_reference_source(evidence.request),
            eligibility_decisions=self._deps.eligibility_decision_source(
                evidence.request
            ),
            now=now,
        )
        kill_switches = self._deps.kill_switch_source(candidate.scope)
        audit_id = self._audit(
            "portfolio.activation_submitted",
            request_id=candidate.request_id,
            correlation_id=candidate.correlation_id,
            causation_id=candidate.causation_id,
            payload={
                "decision_id": review.risk_decision.decision_id,
                "portfolio_id": candidate.portfolio_id,
                "rollback_of_version": rollback_of_version,
            },
        )
        return self._allocation.activate(
            candidate,
            simulation=review.simulation,
            risk_decision=review.risk_decision,
            kill_switches=kill_switches,
            approval_attestation=approval_attestation,
            approval_validation=approval_validation,
            runtime_profile=evidence.request.runtime_profile,
            activated_at=now,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            expected_predecessor=expected_predecessor,
            expected_revision=expected_revision,
            audit_ref=audit_id,
            audit_record=_audit_record(audit_id, "portfolio.activation_submitted"),
            rollback_of_version=rollback_of_version,
        )

    def assess_drift(
        self,
        allocation: ActivePortfolioAllocation,
        *,
        actual_exposures: Mapping[str, Decimal],
        evidence_as_of: datetime,
        risk_decision: AllocationRiskDecision,
        eligibility_decisions: Mapping[str, StrategyOperationalEligibilityDecision],
        request_id: str,
        workflow_id: str,
        correlation_id: str,
    ) -> PortfolioRebalancePlan:
        """Run WF-PORT-005 and persist one immutable drift plan.

        Args:
            allocation: Current active allocation.
            actual_exposures: Exact component Risk-budget exposures.
            evidence_as_of: UTC account/FX evidence time.
            risk_decision: Current authoritative Risk allocation decision.
            eligibility_decisions: Component-keyed current Risk eligibility.
            request_id: Request trace identity.
            workflow_id: Workflow trace identity.
            correlation_id: Correlation trace identity.

        Returns:
            Persisted immutable rebalance plan.
        """
        logger.info("Running Portfolio drift assessment workflow")
        audit_id = self._audit(
            "portfolio.drift_assessed",
            request_id=request_id,
            correlation_id=correlation_id,
            causation_id=allocation.request_id,
            payload={
                "allocation_version": allocation.allocation_version,
                "portfolio_id": allocation.portfolio_id,
            },
        )
        return self._rebalancing.assess(
            allocation,
            actual_exposures=actual_exposures,
            evidence_as_of=evidence_as_of,
            risk_decision=risk_decision,
            eligibility_decisions=eligibility_decisions,
            kill_switches=self._deps.kill_switch_source(allocation.scope),
            now=self._now(),
            request_id=request_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
            audit_record=_audit_record(audit_id, "portfolio.drift_assessed"),
        )

    def _rebalance_review_request(
        self,
        plan: PortfolioRebalancePlan,
        *,
        account_evidence_ref: str,
        market_evidence_ref: str,
        fx_evidence_refs: tuple[str, ...],
        runtime_profile: Literal["simulation", "paper", "live"],
        execution_route: Literal["sim", "paper", "live"],
        approval_refs: tuple[str, ...],
    ) -> AllocationReviewRequest:
        """Build the exact Risk-owned rebalance review request.

        Args:
            plan: Immutable reduce-only Portfolio plan.
            account_evidence_ref: Current Data account evidence reference.
            market_evidence_ref: Current Data market evidence reference.
            fx_evidence_refs: Ordered Data FX evidence references.
            runtime_profile: Explicit execution profile.
            execution_route: Compatible Trading route.
            approval_refs: Ordered owner-provided approval references.

        Returns:
            Receiver-owned self-contained Risk request.
        """
        logger.debug("Building Risk-owned Portfolio rebalance review request")
        return AllocationReviewRequest(
            projection_kind="rebalance",
            portfolio_id=plan.portfolio_id,
            portfolio_version=plan.allocation_version,
            result_id=None,
            plan_id=plan.plan_id,
            ordered_components=tuple(
                {
                    "action": action.action,
                    "component_id": action.component_id,
                    "current_exposure": str(action.current_exposure),
                    "reduction_amount": str(action.reduction_amount),
                    "target_exposure": str(action.target_exposure),
                }
                for action in plan.actions
            ),
            eligibility_decision_refs=tuple(
                action.eligibility_decision_id for action in plan.actions
            ),
            account_evidence_ref=account_evidence_ref,
            market_evidence_ref=market_evidence_ref,
            fx_evidence_refs=fx_evidence_refs,
            evidence_hashes={
                "config": plan.config_hash,
                "evidence": plan.evidence_hash,
                "plan": plan.canonical_hash,
            },
            runtime_profile=runtime_profile,
            execution_route=execution_route,
            approval_refs=approval_refs,
            requested_at=self._now(),
            request_id=plan.request_id,
            workflow_id=plan.workflow_id,
            correlation_id=plan.correlation_id,
        )

    def _execution_request(
        self,
        plan: PortfolioRebalancePlan,
        decision: AllocationRiskDecision,
        *,
        trading_request_id: str,
        execution_route: Literal["sim", "paper", "live"],
        approval_token_ref: str,
        valid_until: datetime,
    ) -> PortfolioRebalanceExecutionRequest:
        """Build the exact Trading-owned high-level execution request.

        Args:
            plan: Immutable approved Portfolio plan.
            decision: Current Risk plan authorization.
            trading_request_id: Unique Trading request identity.
            execution_route: Explicit Trading route.
            approval_token_ref: Opaque Risk approval token reference.
            valid_until: Explicit execution authorization expiry.

        Returns:
            Canonically hash-bound Trading receiver request.
        """
        logger.debug("Building Trading-owned Portfolio rebalance request")
        now = self._now()
        data: dict[str, object] = {
            "contract_version": "v1",
            "schema_id": "trading.portfolio_rebalance_execution_request.v1",
            "request_id": trading_request_id,
            "workflow_id": plan.workflow_id,
            "correlation_id": plan.correlation_id,
            "plan_id": plan.plan_id,
            "plan_version": plan.plan_version,
            "portfolio_id": plan.portfolio_id,
            "allocation_version": plan.allocation_version,
            "allocation_decision_id": decision.decision_id,
            "eligibility_decision_ids": tuple(
                action.eligibility_decision_id for action in plan.actions
            ),
            "actions": tuple(
                {
                    "action_id": action.action_id,
                    "component_id": action.component_id,
                    "eligibility_decision_id": action.eligibility_decision_id,
                    "action": action.action,
                    "reduce_only": action.reduce_only,
                    "current_exposure": str(action.current_exposure),
                    "target_exposure": str(action.target_exposure),
                    "reduction_amount": str(action.reduction_amount),
                }
                for action in plan.actions
            ),
            "route": TradingRoute(execution_route),
            "approval_token_ref": approval_token_ref,
            "canonical_material_version": "v1",
            "valid_from": now,
            "valid_until": valid_until,
        }
        data["canonical_hash"] = _digest(data)
        return PortfolioRebalanceExecutionRequest.model_validate(data)

    def _transition_plan(
        self,
        plan: PortfolioRebalancePlan,
        *,
        status: str,
        risk_decision_id: str,
        trading_execution_ref: str,
        analytics_measurement_ref: str | None,
        transitioned_at: datetime,
    ) -> PortfolioRebalancePlan:
        """Create one new immutable plan lifecycle version.

        Args:
            plan: Prior immutable plan version.
            status: Next lifecycle status.
            risk_decision_id: Current Risk decision identity.
            trading_execution_ref: Immutable Trading evidence reference.
            analytics_measurement_ref: Optional Analytics evidence reference.
            transitioned_at: Injected UTC transition time.

        Returns:
            New immutable plan lifecycle version.
        """
        logger.debug("Creating a new immutable Portfolio plan lifecycle version")
        material = {
            "analytics_measurement_ref": analytics_measurement_ref,
            "prior_hash": plan.canonical_hash,
            "risk_decision_id": risk_decision_id,
            "status": status,
            "trading_execution_ref": trading_execution_ref,
            "transitioned_at": transitioned_at,
        }
        digest = _digest(material)
        data = plan.model_dump(mode="python")
        data.update(
            {
                "analytics_measurement_ref": analytics_measurement_ref,
                "canonical_hash": digest,
                "created_at": transitioned_at,
                "plan_version": f"{plan.plan_version}:{status}:{digest[:12]}",
                "risk_decision_id": risk_decision_id,
                "status": status,
                "trading_execution_ref": trading_execution_ref,
            }
        )
        return PortfolioRebalancePlan.model_validate(data)

    @staticmethod
    def _execution_facts(envelope: StandardTradingEnvelope) -> Mapping[str, object]:
        """Project immutable redacted Trading facts for Analytics.

        Args:
            envelope: Trading-owned execution result envelope.

        Returns:
            Bounded receiver request fact projection.
        """
        logger.debug("Projecting immutable redacted Trading execution facts")
        dumped = envelope.model_dump(mode="json")
        return {
            "status": dumped["status"],
            "data": dumped["data"],
            "errors": dumped["errors"],
            "warnings": dumped["warnings"],
            "audit_metadata": dumped["audit_metadata"],
        }

    def _measurement_request(
        self,
        plan: PortfolioRebalancePlan,
        envelope: StandardTradingEnvelope,
        *,
        trading_request_id: str,
    ) -> PortfolioRebalanceMeasurementRequest:
        """Build the Analytics-owned deterministic measurement request.

        Args:
            plan: Executed-but-unmeasured immutable plan version.
            envelope: Immutable redacted Trading execution facts.
            trading_request_id: Trading execution request identity.

        Returns:
            Hash-bound Analytics receiver request.

        Raises:
            PortfolioError: If the plan lacks immutable Trading evidence.
        """
        logger.debug("Building Analytics-owned rebalance measurement request")
        if plan.trading_execution_ref is None:
            raise PortfolioError("PORT_MEASUREMENT_FAILED", "EXECUTION_REFERENCE")
        facts = self._execution_facts(envelope)
        return PortfolioRebalanceMeasurementRequest(
            contract_version="v1",
            schema_id="analytics.portfolio_rebalance_measurement_request.v1",
            request_id=f"{trading_request_id}:measurement",
            workflow_id=plan.workflow_id,
            correlation_id=plan.correlation_id,
            portfolio_id=plan.portfolio_id,
            allocation_version=plan.allocation_version,
            plan_id=plan.plan_id,
            plan_version=plan.plan_version,
            plan_hash=plan.canonical_hash,
            trading_request_id=trading_request_id,
            trading_execution_ref=plan.trading_execution_ref,
            trading_execution_hash=_digest(facts),
            trading_facts=facts,
            requested_at=plan.created_at,
        )

    async def submit_rebalance(
        self,
        plan: PortfolioRebalancePlan,
        *,
        account_evidence_ref: str,
        market_evidence_ref: str,
        fx_evidence_refs: tuple[str, ...],
        runtime_profile: Literal["simulation", "paper", "live"],
        execution_route: Literal["sim", "paper", "live"],
        approval_refs: tuple[str, ...],
        approval_token_ref: str,
        trading_request_id: str,
        valid_until: datetime,
    ) -> PortfolioRebalancePlan:
        """Run WF-PORT-006 once and preserve execution before measurement.

        Args:
            plan: Current immutable reduce-only plan.
            account_evidence_ref: Current Data account evidence reference.
            market_evidence_ref: Current Data market evidence reference.
            fx_evidence_refs: Ordered Data FX evidence references.
            runtime_profile: Explicit execution profile.
            execution_route: Compatible Trading route.
            approval_refs: Ordered owner-provided approval references.
            approval_token_ref: Opaque Risk approval token reference.
            trading_request_id: Unique Trading request identity.
            valid_until: Explicit execution authorization expiry.

        Returns:
            Measured plan or explicit executed-but-unmeasured plan.

        Raises:
            PortfolioError: If a pre-execution gate or receiver call fails.
        """
        logger.info("Submitting and measuring authorized Portfolio rebalance")
        if plan.status != "review_required" or not plan.actions:
            raise PortfolioError("PORT_REBALANCE_BLOCKED", "PLAN_STATUS")
        active = self._repository.active(plan.portfolio_id, plan.scope)
        if active is None or active[0].allocation_version != plan.allocation_version:
            raise PortfolioError("PORT_REFERENCE_CHANGED", "ACTIVE_ALLOCATION")
        if any(
            switch.state != "inactive"
            for switch in self._deps.kill_switch_source(plan.scope)
        ):
            raise PortfolioError("PORT_KILL_SWITCH_ACTIVE", "REBALANCE")
        review_request = self._rebalance_review_request(
            plan,
            account_evidence_ref=account_evidence_ref,
            market_evidence_ref=market_evidence_ref,
            fx_evidence_refs=fx_evidence_refs,
            runtime_profile=runtime_profile,
            execution_route=execution_route,
            approval_refs=approval_refs,
        )
        try:
            decision = self._deps.risk_reviewer(review_request)
        except Exception as error:
            raise PortfolioError("PORT_DEPENDENCY_FAILED", "RISK_REVIEW") from error
        now = self._now()
        if (
            decision.state is not DecisionState.APPROVE
            or decision.portfolio_id != plan.portfolio_id
            or decision.reviewed_version != plan.allocation_version
            or decision.expires_at <= now
        ):
            raise PortfolioError("PORT_RISK_AUTHORIZATION_INVALID", "REBALANCE")
        trading_request = self._execution_request(
            plan,
            decision,
            trading_request_id=trading_request_id,
            execution_route=execution_route,
            approval_token_ref=approval_token_ref,
            valid_until=valid_until,
        )
        audit_id = self._audit(
            "portfolio.rebalance_submitted",
            request_id=plan.request_id,
            correlation_id=plan.correlation_id,
            causation_id=None,
            payload={"plan_id": plan.plan_id, "trading_request_id": trading_request_id},
        )
        try:
            envelope = await self._deps.trading_executor(trading_request)
        except Exception as error:
            raise PortfolioError("PORT_UNCERTAIN_OUTCOME", "TRADING") from error
        execution_ref = f"trading-execution:{trading_request_id}"
        executed = self._transition_plan(
            plan,
            status="executed_unmeasured",
            risk_decision_id=decision.decision_id,
            trading_execution_ref=execution_ref,
            analytics_measurement_ref=None,
            transitioned_at=now,
        )
        executed = self._repository.save_plan(
            executed,
            _audit_record(audit_id, "portfolio.rebalance_submitted"),
        )
        if envelope.status != "success":
            return executed
        return self._measure(executed, envelope, trading_request_id=trading_request_id)

    def _measure(
        self,
        executed: PortfolioRebalancePlan,
        envelope: StandardTradingEnvelope,
        *,
        trading_request_id: str,
    ) -> PortfolioRebalancePlan:
        """Measure execution once while preserving failure truth.

        Args:
            executed: Persisted executed-but-unmeasured plan.
            envelope: Immutable redacted Trading execution facts.
            trading_request_id: Trading request identity.

        Returns:
            Measured plan or unchanged executed-but-unmeasured plan.
        """
        logger.info("Measuring immutable Portfolio Trading execution facts")
        request = self._measurement_request(
            executed,
            envelope,
            trading_request_id=trading_request_id,
        )
        try:
            evidence = self._deps.analytics_measurer(request)
        except Exception:  # noqa: BLE001 - receiver failure preserves execution truth.
            logger.warning(
                "Analytics measurement failed; preserving executed Portfolio truth"
            )
            return executed
        if (
            evidence.plan_id != executed.plan_id
            or evidence.trading_execution_ref != executed.trading_execution_ref
            or evidence.trading_execution_hash != request.trading_execution_hash
        ):
            logger.warning(
                "Analytics measurement conflicted; preserving executed Portfolio truth"
            )
            return executed
        audit_id = self._audit(
            "portfolio.rebalance_measured",
            request_id=executed.request_id,
            correlation_id=executed.correlation_id,
            causation_id=None,
            payload={"evidence_id": evidence.evidence_id, "plan_id": executed.plan_id},
        )
        measured = self._transition_plan(
            executed,
            status="measured",
            risk_decision_id=executed.risk_decision_id or "",
            trading_execution_ref=executed.trading_execution_ref or "",
            analytics_measurement_ref=evidence.evidence_id,
            transitioned_at=self._now(),
        )
        return self._repository.save_plan(
            measured,
            _audit_record(audit_id, "portfolio.rebalance_measured"),
        )

    def recompute_measurement(
        self,
        plan_id: str,
        *,
        trading_request_id: str,
    ) -> PortfolioRebalancePlan:
        """Recompute Analytics evidence without invoking Trading again.

        Args:
            plan_id: Executed-but-unmeasured plan identity.
            trading_request_id: Original Trading request identity.

        Returns:
            Measured plan or unchanged executed-but-unmeasured plan.

        Raises:
            PortfolioError: If the plan is not eligible for recomputation.
        """
        logger.info("Recomputing Portfolio measurement from immutable Trading facts")
        plan = self._repository.plan(plan_id)
        if plan.status != "executed_unmeasured" or plan.trading_execution_ref is None:
            raise PortfolioError("PORT_MEASUREMENT_FAILED", "PLAN_STATUS")
        try:
            envelope = self._deps.trading_execution_source(plan.trading_execution_ref)
        except Exception as error:
            raise PortfolioError(
                "PORT_DEPENDENCY_FAILED", "TRADING_EVIDENCE"
            ) from error
        return self._measure(plan, envelope, trading_request_id=trading_request_id)

    def rollback(
        self,
        candidate: PortfolioConstructionResult,
        evidence: ValidatedConstructionEvidence,
        review: PortfolioReviewResult,
        *,
        rollback_of_version: str,
        approval_attestation: ApprovalAttestation | None,
        approval_validation: ApprovalValidationResult | None,
        expires_at: datetime,
        idempotency_key: str,
        expected_predecessor: str | None,
        expected_revision: int,
    ) -> ActivePortfolioAllocation:
        """Run WF-PORT-007 as a new fully governed allocation version.

        Args:
            candidate: New construction candidate reproducing historical weights.
            evidence: Validated evidence for the new candidate.
            review: Current Simulation and Risk review.
            rollback_of_version: Historical allocation version selected.
            approval_attestation: Conditional human approval evidence.
            approval_validation: Conditional Risk validation result.
            expires_at: Explicit UTC allocation expiry.
            idempotency_key: Deterministic activation identity.
            expected_predecessor: Caller-observed active version.
            expected_revision: Caller-observed scope revision.

        Returns:
            New governed active allocation version.

        Raises:
            PortfolioError: If the historical version or new governance fails.
        """
        logger.info("Running governed Portfolio rollback workflow")
        historical = self._repository.allocation(
            candidate.portfolio_id,
            rollback_of_version,
        )
        if candidate.component_weights != historical.component_weights:
            raise PortfolioError("PORT_REFERENCE_CHANGED", "ROLLBACK_WEIGHTS")
        return self.activate(
            candidate,
            evidence,
            review,
            approval_attestation=approval_attestation,
            approval_validation=approval_validation,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            expected_predecessor=expected_predecessor,
            expected_revision=expected_revision,
            rollback_of_version=rollback_of_version,
        )


__all__: tuple[str, ...] = (
    "ConstructionEvidenceInputs",
    "PortfolioReviewResult",
    "PortfolioWorkflowDependencies",
    "PortfolioWorkflowService",
)
