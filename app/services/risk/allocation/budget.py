"""Allocation constraint review and authoritative Risk-budget activation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from time import monotonic
from typing import TYPE_CHECKING

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    AllocationBudgetActivationRequest,
    AllocationReviewRequest,
    AllocationRiskDecision,
    DecisionState,
    KillSwitchState,
    LimitStatus,
    PortfolioRiskSnapshot,
    RiskAuditRecord,
    RiskDomainError,
    RiskErrorCode,
)
from app.services.risk.limits import evaluate_market_context
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.data.evidence.market_context_contracts import (
        MarketContextEvidence,
    )
    from app.services.risk.audit import RiskAuditChain
    from app.services.risk.audit.storage import _AllocationDecisionStore

_ALLOCATION_KINDS = frozenset({"portfolio", "strategy", "symbol", "cluster"})


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating allocation Policy UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("allocation time must be aware UTC")
    return value


def _parse_component(component: Mapping[str, str]) -> tuple[str, str, Decimal]:
    """Parse one exact documented allocation component.

    Args:
        component: One component mapping.

    Returns:
        Component ID, dimension, and exact weight.

    Raises:
        RiskDomainError: If the component is incomplete or malformed.
    """
    logger.debug("Parsing one exact allocation review component")
    required = {"component_id", "dimension", "weight"}
    if set(component) != required:
        raise RiskDomainError(
            RiskErrorCode.INVALID_INPUT,
            "allocation component fields invalid",
        )
    component_id = component["component_id"]
    dimension = component["dimension"]
    kind, separator, identity = dimension.partition(":")
    try:
        weight = Decimal(component["weight"])
    except InvalidOperation as error:
        raise RiskDomainError(
            RiskErrorCode.INVALID_INPUT,
            "allocation component weight invalid",
        ) from error
    if (
        not component_id
        or component_id != component_id.strip()
        or separator != ":"
        or kind not in _ALLOCATION_KINDS
        or not identity
        or not weight.is_finite()
        or weight < 0
    ):
        raise RiskDomainError(
            RiskErrorCode.INVALID_INPUT,
            "allocation component value invalid",
        )
    return component_id, dimension, weight


def _parse_components(
    components: tuple[Mapping[str, str], ...],
) -> tuple[tuple[str, str, Decimal], ...]:
    """Parse the complete ordered allocation component sequence.

    Args:
        components: Ordered component mappings.

    Returns:
        Ordered component ID, dimension, and exact weight tuples.

    Raises:
        RiskDomainError: If a component is incomplete or malformed.
    """
    logger.debug("Parsing exact allocation review components")
    parsed = tuple(_parse_component(component) for component in components)
    identifiers = [item[0] for item in parsed]
    dimensions = [item[1] for item in parsed]
    if len(set(identifiers)) != len(identifiers) or len(set(dimensions)) != len(
        dimensions
    ):
        raise RiskDomainError(
            RiskErrorCode.INVALID_INPUT,
            "allocation components must be unique",
        )
    return parsed


def _cap_for(dimension: str, config: RiskConfig) -> Decimal:
    """Return the exact or documented baseline allocation cap.

    Args:
        dimension: Canonical allocation dimension.
        config: Active Risk policy.

    Returns:
        Applicable cap ratio.
    """
    logger.debug("Resolving allocation cap for %s", dimension)
    configured = config.allocation_caps.get(dimension)
    if configured is not None:
        return configured
    kind = dimension.partition(":")[0]
    if kind == "portfolio":
        return Decimal(1)
    if kind == "symbol":
        return config.max_symbol_concentration
    return config.max_dimension_concentration


def _review_state(
    market_statuses: tuple[LimitStatus, ...], *, cap_breached: bool, total_invalid: bool
) -> tuple[DecisionState, tuple[str, ...]]:
    """Map market and cap outcomes to the allocation review state.

    Args:
        market_statuses: Ordered market limit statuses.
        cap_breached: Whether an exact component cap was exceeded.
        total_invalid: Whether total requested allocation exceeded one.

    Returns:
        Decision state and explicit conditions.
    """
    logger.debug("Mapping allocation checks to review state")
    if any(
        status in {LimitStatus.FAIL, LimitStatus.BLOCKED} for status in market_statuses
    ):
        return DecisionState.BLOCK, ("market_policy_blocked",)
    if LimitStatus.NEEDS_MORE_EVIDENCE in market_statuses:
        return DecisionState.NEEDS_MORE_EVIDENCE, ("market_evidence_required",)
    if total_invalid:
        return DecisionState.REJECT, ("allocation_total_exceeds_one",)
    if cap_breached:
        return DecisionState.REJECT, ("allocation_cap_exceeded",)
    if LimitStatus.WARN in market_statuses:
        return DecisionState.WARN, ("market_policy_warning",)
    return DecisionState.APPROVE, ()


def _identity(material: Mapping[str, object]) -> str:
    """Derive one stable allocation decision identity.

    Args:
        material: Canonical identity material.

    Returns:
        Lowercase SHA-256 identity.
    """
    logger.debug("Deriving allocation decision identity")
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def _audit_record(
    *,
    record_id: str,
    event_type: str,
    decision: AllocationRiskDecision,
    config_hash: str,
    request_id: str,
    correlation_id: str,
    now: datetime,
) -> RiskAuditRecord:
    """Build one unsealed material allocation audit event.

    Args:
        record_id: Stable event identity.
        event_type: Stable event type.
        decision: Reviewed or activated allocation decision.
        config_hash: Active configuration hash.
        request_id: Source request identity.
        correlation_id: Source correlation identity.
        now: Event time.

    Returns:
        Unsealed Risk audit record.
    """
    logger.debug("Building allocation Policy audit event")
    return RiskAuditRecord(
        record_id=record_id,
        event_type=event_type,
        payload={
            "portfolio_id": decision.portfolio_id,
            "reviewed_version": decision.reviewed_version,
            "state": decision.state.value,
            "active": decision.active,
        },
        evidence_refs=decision.evidence_refs,
        config_hash=config_hash,
        decision_id=decision.decision_id,
        occurred_at=now,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=request_id,
        correlation_id=correlation_id,
    )


def review_allocation_proposal(
    request: AllocationReviewRequest,
    snapshot: PortfolioRiskSnapshot,
    market: MarketContextEvidence,
    config: RiskConfig,
    store: _AllocationDecisionStore,
    audit: RiskAuditChain,
    *,
    now: datetime,
) -> AllocationRiskDecision:
    """Review, persist, and audit one self-contained allocation projection.

    Args:
        request: Self-contained allocation review request.
        snapshot: Exact immutable portfolio Risk snapshot.
        market: Supplied Data-owned market context.
        config: Active Risk policy.
        store: Receiver-owned atomic allocation store.
        audit: Tamper-evident Risk audit coordinator.
        now: Injected current UTC time.

    Returns:
        Persisted immutable allocation Risk decision.

    Raises:
        RiskDomainError: If bindings, evidence, policy, storage, or audit fails.
    """
    logger.info("Reviewing self-contained allocation Risk proposal")
    started_at = monotonic()
    checked_now = _utc(now)
    config_hash = compute_config_hash(config)
    bound = (
        request.requested_at <= checked_now
        and request.runtime_profile == config.profile
        and request.execution_route == config.execution_route
        and request.account_evidence_ref in snapshot.evidence_refs.values()
        and request.market_evidence_ref == market.request_id
        and request.evidence_hashes.get("snapshot_config") == snapshot.config_hash
        and snapshot.config_hash == config_hash
    )
    if not bound:
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE,
            "allocation evidence or runtime binding is incompatible",
        )
    components = _parse_components(request.ordered_components)
    market_results = evaluate_market_context(market, config, now=checked_now)
    requested = {dimension: weight for _, dimension, weight in components}
    capped = {
        dimension: min(weight, _cap_for(dimension, config))
        for dimension, weight in requested.items()
    }
    total_invalid = sum(requested.values(), Decimal(0)) > Decimal(1)
    cap_breached = any(capped[key] != value for key, value in requested.items())
    state, conditions = _review_state(
        tuple(result.status for result in market_results),
        cap_breached=cap_breached,
        total_invalid=total_invalid,
    )
    decision_id = _identity(
        {
            "request_id": request.request_id,
            "portfolio_id": request.portfolio_id,
            "portfolio_version": request.portfolio_version,
            "components": request.ordered_components,
            "config_hash": config_hash,
        }
    )
    audit_ref = f"risk-allocation-review-{decision_id}"
    decision = AllocationRiskDecision(
        decision_id=decision_id,
        portfolio_id=request.portfolio_id,
        reviewed_version=request.portfolio_version,
        state=state,
        capped_weights=capped,
        risk_budget_projection={
            key: value * snapshot.equity for key, value in capped.items()
        },
        conditions=conditions,
        policy_version=config.policy_version,
        evidence_refs={
            "account": request.account_evidence_ref,
            "market": market.request_id,
            "snapshot": snapshot.snapshot_id,
            "config": config_hash,
            **dict(request.evidence_hashes),
        },
        issued_at=checked_now,
        expires_at=checked_now + timedelta(seconds=float(config.decision_ttl_seconds)),
        active=False,
        predecessor_version=request.plan_id
        if request.projection_kind == "rebalance"
        else None,
        audit_ref=audit_ref,
    )
    timeout = config.dependency_timeouts_seconds.get("allocation_store")
    try:
        saved = store.save_review_if_absent(decision, timeout_seconds=timeout)
    except Exception as error:
        logger.error("Allocation review persistence failed")
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "allocation review persistence unavailable",
        ) from error
    if not saved:
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "allocation review identity conflict",
        )
    audit.append(
        _audit_record(
            record_id=audit_ref,
            event_type="risk.allocation_review",
            decision=decision,
            config_hash=config_hash,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            now=checked_now,
        )
    )
    logger.bind(
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        verdict=decision.state.value,
        reason_codes=decision.conditions,
        latency_ms=round((monotonic() - started_at) * 1000, 3),
        evidence_refs=dict(decision.evidence_refs),
        config_hash=config_hash,
    ).info("Completed allocation Risk review decision")
    return decision


def _kill_switch_blocks(
    states: Sequence[KillSwitchState], scope: Mapping[str, str]
) -> bool:
    """Return whether an applicable active or unknown kill switch blocks.

    Args:
        states: Canonical scoped kill-switch states.
        scope: Requested allocation activation scope.

    Returns:
        Whether activation must block.
    """
    logger.debug("Checking kill-switch states for allocation activation")
    for state in states:
        applicable = state.scope_level == "global" or all(
            scope.get(key) == value for key, value in state.scope.items()
        )
        if applicable and state.state in {"active", "unknown"}:
            return True
    return False


def _validate_activation(
    request: AllocationBudgetActivationRequest,
    decision: AllocationRiskDecision,
    states: Sequence[KillSwitchState],
    config: RiskConfig,
    current: AllocationRiskDecision | None,
    now: datetime,
) -> None:
    """Validate exact decision, predecessor, time, config, and switch bindings.

    Args:
        request: Exact activation request.
        decision: Reviewed allocation decision.
        states: Canonical kill-switch evidence.
        config: Active Risk policy.
        current: Current active durable budget, if any.
        now: Checked evaluation time.

    Raises:
        RiskDomainError: If any activation condition blocks.
    """
    logger.debug("Validating exact allocation budget activation bindings")
    current_version = None if current is None else current.reviewed_version
    valid = (
        request.effective_at <= now < decision.expires_at
        and request.decision_id == decision.decision_id
        and request.portfolio_id == decision.portfolio_id
        and request.allocation_version == decision.reviewed_version
        and request.predecessor_version == decision.predecessor_version
        and current_version == request.predecessor_version
        and request.scope.get("portfolio_id") == request.portfolio_id
        and decision.state is DecisionState.APPROVE
        and not decision.active
        and decision.policy_version == config.policy_version
        and decision.evidence_refs.get("config") == compute_config_hash(config)
        and not _kill_switch_blocks(states, request.scope)
    )
    if not valid:
        raise RiskDomainError(
            RiskErrorCode.POLICY_BLOCKED,
            "allocation budget activation binding blocked",
        )


def activate_allocation_budget(
    request: AllocationBudgetActivationRequest,
    decision: AllocationRiskDecision,
    kill_switch_states: Sequence[KillSwitchState],
    config: RiskConfig,
    store: _AllocationDecisionStore,
    audit: RiskAuditChain,
    *,
    now: datetime,
) -> AllocationRiskDecision:
    """Atomically activate one exact approved allocation Risk budget.

    Args:
        request: Exact version-bound activation request.
        decision: Approved reviewed allocation decision.
        kill_switch_states: Applicable canonical kill-switch evidence.
        config: Active Risk policy.
        store: Receiver-owned atomic allocation store.
        audit: Tamper-evident Risk audit coordinator.
        now: Injected current UTC time.

    Returns:
        Activated authoritative Risk-budget projection.

    Raises:
        RiskDomainError: If policy, concurrency, storage, or audit fails.
    """
    logger.info("Activating exact allocation Risk budget projection")
    started_at = monotonic()
    checked_now = _utc(now)
    timeout = config.dependency_timeouts_seconds.get("allocation_store")
    try:
        current = store.get_active(
            request.portfolio_id,
            timeout_seconds=timeout,
        )
    except Exception as error:
        logger.error("Reading active allocation Risk budget failed")
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "active allocation budget unavailable",
        ) from error
    _validate_activation(
        request,
        decision,
        kill_switch_states,
        config,
        current,
        checked_now,
    )
    values = decision.model_dump(mode="python")
    values["active"] = True
    active = AllocationRiskDecision.model_validate(values)
    try:
        activated = store.activate_compare_and_swap(
            active,
            expected_predecessor_version=request.predecessor_version,
            timeout_seconds=timeout,
        )
    except Exception as error:
        logger.error("Allocation Risk budget compare-and-swap failed")
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "allocation budget activation unavailable",
        ) from error
    if not activated:
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR,
            "allocation budget activation conflict",
        )
    config_hash = compute_config_hash(config)
    audit.append(
        _audit_record(
            record_id=f"risk-allocation-activate-{request.request_id}",
            event_type="risk.allocation_activation",
            decision=active,
            config_hash=config_hash,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            now=checked_now,
        )
    )
    logger.bind(
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        verdict=active.state.value,
        reason_codes=active.conditions,
        latency_ms=round((monotonic() - started_at) * 1000, 3),
        evidence_refs=dict(active.evidence_refs),
        config_hash=config_hash,
    ).info("Completed allocation Risk budget activation decision")
    return active


__all__ = ["activate_allocation_budget", "review_allocation_proposal"]
