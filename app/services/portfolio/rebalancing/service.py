"""Deterministic reduce-only Portfolio drift and rebalance planning."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.portfolio.contracts import (
    DriftObservation,
    PortfolioRebalanceAction,
    PortfolioRebalancePlan,
)
from app.services.portfolio.exceptions import PortfolioError
from app.services.risk import (
    AllocationRiskDecision,
    DecisionState,
    KillSwitchState,
    StrategyOperationalEligibilityDecision,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.portfolio.config import PortfolioSettings
    from app.services.portfolio.contracts import ActivePortfolioAllocation, PlanStatus
    from app.services.portfolio.state import AuditOutboxRecord, PortfolioRepository


def _digest(value: object) -> str:
    """Hash supported canonical rebalance material.

    Args:
        value: Supported primitive rebalance material.

    Returns:
        Lowercase SHA-256 digest.
    """
    logger.debug("Hashing deterministic Portfolio rebalance material")
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class RebalancingService:
    """Assess actual Risk-budget drift and publish reduce-only plans."""

    def __init__(
        self,
        settings: PortfolioSettings,
        repository: PortfolioRepository,
    ) -> None:
        """Initialize rebalancing with explicit policy and persistence.

        Args:
            settings: Complete explicit Portfolio settings.
            repository: Portfolio-owned repository.
        """
        logger.info("Initializing Portfolio rebalancing service")
        self._settings = settings
        self._repository = repository

    def _schedule_due(self, now: datetime) -> bool:
        """Return whether the explicit UTC interval is due exactly now.

        Args:
            now: Current injected UTC time.

        Returns:
            Whether the configured interval boundary is due.
        """
        logger.debug("Evaluating explicit Portfolio rebalance schedule")
        schedule = self._settings.portfolio_rebalance_schedule
        if now < schedule.anchor_at:
            return False
        elapsed = int((now - schedule.anchor_at).total_seconds())
        return elapsed % schedule.interval_seconds == 0

    def _block_reasons(
        self,
        allocation: ActivePortfolioAllocation,
        risk_decision: AllocationRiskDecision,
        kill_switches: Sequence[KillSwitchState],
        evidence_as_of: datetime,
        now: datetime,
    ) -> tuple[str, ...]:
        """Return ordered fail-closed plan block reasons.

        Args:
            allocation: Current active allocation.
            risk_decision: Current authoritative Risk budget decision.
            kill_switches: Applicable canonical Risk kill-switch states.
            evidence_as_of: Actual-exposure observation time.
            now: Current injected UTC time.

        Returns:
            Ordered unique symbolic block reasons.
        """
        logger.info("Evaluating Portfolio rebalance fail-closed gates")
        reasons: set[str] = set()
        if allocation.expires_at <= now:
            reasons.add("ALLOCATION_EXPIRED")
        if (
            evidence_as_of > now
            or now - evidence_as_of > self._settings.evidence_max_age()
        ):
            reasons.add("EXPOSURE_EVIDENCE_STALE")
        if not kill_switches or any(item.state != "inactive" for item in kill_switches):
            reasons.add("KILL_SWITCH")
        if (
            not risk_decision.active
            or risk_decision.state is not DecisionState.APPROVE
            or risk_decision.decision_id != allocation.risk_decision_id
            or risk_decision.reviewed_version != allocation.allocation_version
            or risk_decision.expires_at <= now
        ):
            reasons.add("RISK_TARGET_INVALID")
        return tuple(sorted(reasons))

    def assess(  # noqa: C901 - explicit fail-closed gate classification.
        self,
        allocation: ActivePortfolioAllocation,
        *,
        actual_exposures: Mapping[str, Decimal],
        evidence_as_of: datetime,
        risk_decision: AllocationRiskDecision,
        eligibility_decisions: Mapping[
            str,
            StrategyOperationalEligibilityDecision,
        ],
        kill_switches: Sequence[KillSwitchState],
        now: datetime,
        request_id: str,
        workflow_id: str,
        correlation_id: str,
        audit_record: AuditOutboxRecord,
    ) -> PortfolioRebalancePlan:
        """Assess drift and persist one immutable reduce-only plan.

        Args:
            allocation: Current active allocation version.
            actual_exposures: Fresh actual Risk-budget exposure by component.
            evidence_as_of: Actual-exposure observation time.
            risk_decision: Current authoritative Risk budget decision.
            eligibility_decisions: Current component-keyed eligibility decisions.
            kill_switches: Applicable Risk kill-switch states.
            now: Current injected UTC time.
            request_id: Request trace identity.
            workflow_id: Workflow trace identity.
            correlation_id: Correlation trace identity.
            audit_record: Redacted atomic audit outbox record.

        Returns:
            Persisted immutable plan.

        Raises:
            PortfolioError: If evidence sets, numeric values, or time are invalid.
        """
        logger.info("Assessing Portfolio actual-versus-target Risk-budget drift")
        if (
            now.tzinfo is None
            or now.utcoffset() != timedelta(0)
            or evidence_as_of.tzinfo is None
            or evidence_as_of.utcoffset() != timedelta(0)
        ):
            raise PortfolioError("PORT_INVALID_INPUT", "DRIFT_TIME")
        component_ids = {item.component_id for item in allocation.component_weights}
        if (
            set(actual_exposures) != component_ids
            or set(risk_decision.risk_budget_projection) != component_ids
            or set(eligibility_decisions) != component_ids
        ):
            raise PortfolioError("PORT_EVIDENCE_INVALID", "EXPOSURE_SET")
        if any(
            not value.is_finite() or value < 0 for value in actual_exposures.values()
        ):
            raise PortfolioError("PORT_EVIDENCE_INVALID", "EXPOSURE_VALUE")
        reasons = list(
            self._block_reasons(
                allocation,
                risk_decision,
                kill_switches,
                evidence_as_of,
                now,
            )
        )
        threshold = self._settings.portfolio_rebalance_drift_threshold
        observations: list[DriftObservation] = []
        actions: list[PortfolioRebalanceAction] = []
        for component_id in sorted(component_ids):
            target = risk_decision.risk_budget_projection[component_id]
            actual = actual_exposures[component_id]
            drift = actual - target
            breached = abs(drift) >= threshold
            observations.append(
                DriftObservation(
                    component_id=component_id,
                    target_risk_budget=target,
                    actual_risk_budget=actual,
                    drift=drift,
                    threshold_breached=breached,
                )
            )
            eligibility = eligibility_decisions[component_id]
            if (
                eligibility.state is not DecisionState.APPROVE
                or eligibility.suspended
                or eligibility.expires_at <= now
            ):
                reasons.append("ELIGIBILITY_INVALID")
                continue
            if breached and drift > 0:
                action_hash = _digest(
                    {
                        "allocation_version": allocation.allocation_version,
                        "component_id": component_id,
                        "current": actual,
                        "target": target,
                    }
                )
                actions.append(
                    PortfolioRebalanceAction(
                        action_id=f"rebalance-action-{action_hash[:24]}",
                        component_id=component_id,
                        action="reduce_exposure",
                        reduce_only=True,
                        current_exposure=actual,
                        target_exposure=target,
                        reduction_amount=drift,
                        eligibility_decision_id=eligibility.decision_id,
                    )
                )
            elif breached and drift < 0:
                reasons.append("RISK_INCREASE_UNSUPPORTED")
        reasons = sorted(set(reasons))
        schedule_due = self._schedule_due(now)
        if reasons and not actions:
            status: PlanStatus = "blocked"
        elif actions:
            status = "review_required"
        else:
            status = "no_action"
        if not schedule_due and not any(
            item.threshold_breached for item in observations
        ):
            status = "no_action"
        evidence_hash = _digest(
            {
                "actual_exposures": dict(sorted(actual_exposures.items())),
                "allocation_hash": allocation.canonical_hash,
                "evidence_as_of": evidence_as_of,
                "risk_decision_id": risk_decision.decision_id,
            }
        )
        config_hash = _digest(self._settings.model_dump(mode="json"))
        plan_material = {
            "actions": tuple(item.model_dump(mode="json") for item in actions),
            "allocation_version": allocation.allocation_version,
            "block_reasons": reasons,
            "config_hash": config_hash,
            "evidence_hash": evidence_hash,
            "observations": tuple(
                item.model_dump(mode="json") for item in observations
            ),
            "observed_at": evidence_as_of,
            "status": status,
        }
        canonical_hash = _digest(plan_material)
        plan = PortfolioRebalancePlan(
            plan_id=f"portfolio-plan-{canonical_hash[:32]}",
            plan_version=now.isoformat(),
            portfolio_id=allocation.portfolio_id,
            allocation_version=allocation.allocation_version,
            scope=allocation.scope,
            observations=tuple(observations),
            actions=tuple(actions),
            status=status,
            block_reasons=tuple(reasons),
            evidence_hash=evidence_hash,
            config_hash=config_hash,
            canonical_hash=canonical_hash,
            observed_at=evidence_as_of,
            created_at=now,
            risk_decision_id=None,
            trading_execution_ref=None,
            analytics_measurement_ref=None,
            request_id=request_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        )
        return self._repository.save_plan(plan, audit_record)


__all__: tuple[str, ...] = ("RebalancingService",)
