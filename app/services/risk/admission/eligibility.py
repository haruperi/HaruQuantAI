"""Strategy operational-admission Risk gate without Strategy state mutation."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from time import monotonic
from typing import TYPE_CHECKING

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    DecisionState,
    LimitStatus,
    RiskAuditRecord,
    RiskDomainError,
    RiskErrorCode,
    StrategyOperationalEligibilityDecision,
    StrategyOperationalEligibilityRequest,
)
from app.services.risk.limits import evaluate_market_context
from app.services.strategy import (
    StrategyEnvironment,
    StrategyLifecycleStatus,
    ValidatedStrategyRef,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.data.evidence.market_context_contracts import (
        MarketContextEvidence,
    )
    from app.services.risk.audit import RiskAuditChain
    from app.services.risk.audit.storage import _EligibilityDecisionStore


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating strategy-admission UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("admission time must be aware UTC")
    return value


def _validate_registration(
    request: StrategyOperationalEligibilityRequest,
    registration: ValidatedStrategyRef,
    config: RiskConfig,
    now: datetime,
) -> None:
    """Validate exact Strategy, policy, environment, and request bindings.

    Args:
        request: Exact admission request.
        registration: Public immutable Strategy registration.
        config: Active Risk policy.
        now: Checked evaluation time.

    Raises:
        RiskDomainError: If any exact binding is incompatible.
    """
    logger.debug("Validating exact Strategy registration for admission")
    environment = {
        "simulation": StrategyEnvironment.SIMULATION,
        "paper": StrategyEnvironment.PAPER,
        "live": StrategyEnvironment.LIVE,
    }[request.runtime_profile]
    valid = (
        request.requested_at <= now
        and request.strategy_id == registration.manifest.strategy_id
        and request.strategy_version == registration.manifest.strategy_version
        and request.registration_ref == registration.registry_record_hash
        and request.policy_version == config.policy_version
        and registration.lifecycle_status is StrategyLifecycleStatus.APPROVED
        and registration.environment is environment
        and environment in registration.manifest.permitted_environments
        and request.runtime_profile == config.profile
        and request.execution_route == config.execution_route
    )
    if not valid:
        raise RiskDomainError(
            RiskErrorCode.POLICY_BLOCKED,
            "strategy registration or runtime binding is incompatible",
        )


def _decision_state(
    statuses: tuple[LimitStatus, ...],
) -> tuple[DecisionState, bool, tuple[str, ...]]:
    """Map ordered market results to admission state and conditions.

    Args:
        statuses: Ordered market limit statuses.

    Returns:
        Decision state, suspension flag, and explicit conditions.
    """
    logger.debug("Mapping market limits to strategy admission state")
    if any(status in {LimitStatus.FAIL, LimitStatus.BLOCKED} for status in statuses):
        return DecisionState.BLOCK, True, ("market_policy_blocked",)
    if LimitStatus.NEEDS_MORE_EVIDENCE in statuses:
        return (
            DecisionState.NEEDS_MORE_EVIDENCE,
            True,
            ("market_evidence_required",),
        )
    if LimitStatus.WARN in statuses:
        return DecisionState.WARN, False, ("market_policy_warning",)
    return DecisionState.APPROVE, False, ()


def _identity(
    request: StrategyOperationalEligibilityRequest,
    registration: ValidatedStrategyRef,
    config_hash: str,
) -> str:
    """Derive a stable idempotent decision identity.

    Args:
        request: Exact admission request.
        registration: Exact public Strategy reference.
        config_hash: Active Risk configuration hash.

    Returns:
        Lowercase SHA-256 decision identity.
    """
    logger.debug("Deriving strategy admission decision identity")
    material = {
        "request_id": request.request_id,
        "workflow_id": request.workflow_id,
        "strategy_id": request.strategy_id,
        "strategy_version": request.strategy_version,
        "registration_hash": registration.registry_record_hash,
        "config_hash": config_hash,
    }
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def _audit_record(
    decision: StrategyOperationalEligibilityDecision,
    request: StrategyOperationalEligibilityRequest,
    config_hash: str,
) -> RiskAuditRecord:
    """Build the unsealed material admission audit event.

    Args:
        decision: Persisted admission decision.
        request: Source request.
        config_hash: Active Risk configuration hash.

    Returns:
        Unsealed Risk audit record.
    """
    logger.debug("Building strategy admission audit event")
    return RiskAuditRecord(
        record_id=decision.audit_ref,
        event_type="risk.strategy_admission",
        payload={
            "strategy_id": decision.strategy_id,
            "strategy_version": decision.strategy_version,
            "state": decision.state.value,
            "suspended": decision.suspended,
        },
        evidence_refs=decision.evidence_refs,
        config_hash=config_hash,
        decision_id=decision.decision_id,
        occurred_at=decision.issued_at,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
    )


def review_strategy_admission(
    request: StrategyOperationalEligibilityRequest,
    registration: ValidatedStrategyRef,
    market: MarketContextEvidence,
    config: RiskConfig,
    store: _EligibilityDecisionStore,
    audit: RiskAuditChain,
    *,
    now: datetime,
) -> StrategyOperationalEligibilityDecision:
    """Review and durably record Strategy operational eligibility.

    Args:
        request: Exact registered-strategy admission request.
        registration: Public immutable validated Strategy reference.
        market: Supplied Data-owned market evidence.
        config: Active Risk policy.
        store: Receiver-owned atomic eligibility store.
        audit: Tamper-evident Risk audit coordinator.
        now: Injected current UTC time.

    Returns:
        Persisted immutable operational-eligibility decision.

    Raises:
        RiskDomainError: If evidence, policy, persistence, or audit fails.
    """
    logger.info("Reviewing Strategy operational eligibility")
    started_at = monotonic()
    checked_now = _utc(now)
    _validate_registration(request, registration, config, checked_now)
    if market.request_id not in request.evidence_refs.values():
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE,
            "strategy admission market evidence is not request-bound",
        )
    market_results = evaluate_market_context(market, config, now=checked_now)
    state, suspended, conditions = _decision_state(
        tuple(result.status for result in market_results)
    )
    config_hash = compute_config_hash(config)
    decision_id = _identity(request, registration, config_hash)
    audit_ref = f"risk-admission-{decision_id}"
    decision = StrategyOperationalEligibilityDecision(
        decision_id=decision_id,
        strategy_id=request.strategy_id,
        strategy_version=request.strategy_version,
        scope=request.requested_scope,
        state=state,
        conditions=conditions,
        policy_version=config.policy_version,
        evidence_refs={
            **dict(request.evidence_refs),
            "registration": registration.registry_record_hash,
            "market": market.request_id,
            "config": config_hash,
        },
        issued_at=checked_now,
        expires_at=checked_now + timedelta(seconds=float(config.decision_ttl_seconds)),
        suspended=suspended,
        audit_ref=audit_ref,
    )
    timeout = config.dependency_timeouts_seconds.get("eligibility_store")
    try:
        saved = store.save_if_absent(decision, timeout_seconds=timeout)
    except Exception as error:
        logger.error("Strategy eligibility persistence failed")
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "strategy eligibility persistence unavailable",
        ) from error
    if not saved:
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "strategy eligibility identity conflict",
        )
    audit.append(_audit_record(decision, request, config_hash))
    logger.bind(
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        verdict=decision.state.value,
        reason_codes=decision.conditions,
        latency_ms=round((monotonic() - started_at) * 1000, 3),
        evidence_refs=dict(decision.evidence_refs),
        config_hash=config_hash,
    ).info("Completed Strategy operational eligibility decision")
    return decision


__all__ = ["review_strategy_admission"]
