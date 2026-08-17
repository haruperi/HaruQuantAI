"""Canonical fixed-precedence Risk decision orchestration."""

from __future__ import annotations

import hashlib
from abc import abstractmethod
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from time import monotonic
from typing import TYPE_CHECKING, Any, Literal, Protocol

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    DecisionState,
    KillSwitchState,
    LimitStatus,
    PortfolioRiskSnapshot,
    ProposedTrade,
    RegimeAssessment,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
)
from app.services.risk.contracts.responses import (
    guard_risk_boundary,
    unwrap_risk_response,
)
from app.services.risk.kill_switch import permits_risk_action
from app.services.risk.limits import evaluate_market_context, evaluate_portfolio_limits
from app.services.risk.scenarios import evaluate_stress_loss_gate
from app.services.risk.stop_validation import validate_stop_loss
from app.utils import canonical_json, get_logger

type AuthContext = Any

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.risk.approvals import ApprovalTokenService
    from app.services.risk.audit import RiskAuditChain
    from app.services.risk.contracts.evidence import _MarketContextEvidenceView


class _CapacityGuard(Protocol):  # pragma: no cover
    """Private receiver-owned atomic in-flight capacity boundary."""

    @abstractmethod
    def reserve_capacity(
        self,
        *,
        reservation_key: str,
        account_id: str,
        strategy_id: str,
        symbol: str,
        requested_notional: Decimal,
        expires_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal["reserved", "already_reserved", "conflict", "unavailable"]:
        """Atomically reserve capacity for one exact proposed action.

        Args:
            reservation_key: Stable proposal and config identity.
            account_id: Bound account identity.
            strategy_id: Bound Strategy identity.
            symbol: Bound instrument identity.
            requested_notional: Regime-capped requested notional.
            expires_at: Reservation expiry.
            timeout_seconds: Configured dependency timeout.

        Returns:
            Atomic receiver-owned capacity outcome.
        """
        logger.debug("Reserving exact in-flight Risk capacity")
        raise NotImplementedError


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If timestamp is not aware UTC.
    """
    logger.debug("Validating Risk governor UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("governor time must be aware UTC")
    return value


def _identity(prefix: str, material: Mapping[str, object]) -> str:
    """Derive one stable SHA-256 decision or audit identity.

    Args:
        prefix: Identity namespace.
        material: Canonically serializable exact material.

    Returns:
        Lowercase hexadecimal identity.
    """
    logger.debug("Deriving canonical Risk governor identity")
    serialized = canonical_json({"prefix": prefix, "material": dict(material)})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _validate_governor_dependencies(
    config: RiskConfig,
    clock: Callable[[], datetime],
    capacity_guard: _CapacityGuard | None,
) -> None:
    """Validate clock and configured concurrency dependencies.

    Args:
        config: Active immutable Risk policy.
        clock: Injected UTC clock.
        capacity_guard: Optional receiver-owned capacity guard.

    Raises:
        ValueError: If a configured dependency is unavailable.
    """
    logger.debug("Validating canonical Risk governor dependencies")
    _utc(clock())
    requires_guard = (
        config.profile == "live" and config.double_spend_owner == "capacity_guard"
    ) or config.in_flight_tolerance is not None
    if requires_guard and capacity_guard is None:
        raise ValueError("configured capacity guard is unavailable")


def _require_attestation(
    attestation: ApprovalAttestation | None,
) -> ApprovalAttestation:
    """Require approval evidence on an approving risk-increase path.

    Args:
        attestation: Optional submitted approval evidence.

    Returns:
        Required approval evidence.

    Raises:
        ValueError: If approval evidence is absent.
    """
    logger.debug("Requiring approval evidence for approved Risk increase")
    if attestation is None:
        raise ValueError("approval state is inconsistent")
    return attestation


def _limit(
    limit_id: str,
    status: LimitStatus,
    precedence: int,
    evidence_refs: tuple[str, ...],
    *,
    observed: Decimal | None = None,
    threshold: Decimal | None = None,
    reason: RiskErrorCode | None = None,
) -> RiskLimitResult:
    """Build one ordered governor-level limit result.

    Args:
        limit_id: Stable check identity.
        status: Deterministic result status.
        precedence: Fixed order index.
        evidence_refs: Exact evidence identities.
        observed: Optional observed value.
        threshold: Optional configured threshold.
        reason: Required stable reason for failing states.

    Returns:
        Immutable ordered check.
    """
    logger.debug("Building one ordered Risk governor check")
    return RiskLimitResult(
        limit_id=limit_id,
        status=status,
        observed_value=observed,
        threshold_value=threshold,
        reason_code=reason,
        evidence_refs=evidence_refs,
        precedence=precedence,
    )


def _reindex(
    results: Sequence[RiskLimitResult], start: int
) -> tuple[RiskLimitResult, ...]:
    """Assign contiguous fixed precedence to supplied policy results.

    Args:
        results: Ordered policy results.
        start: First assigned precedence.

    Returns:
        Reindexed immutable results.
    """
    logger.debug("Reindexing policy results in canonical governor precedence")
    return tuple(
        item.model_copy(update={"precedence": start + offset})
        for offset, item in enumerate(results)
    )


def _kill_switch_result(
    states: Sequence[KillSwitchState], *, live: bool, precedence: int
) -> RiskLimitResult:
    """Evaluate the caller-supplied complete applicable kill-switch hierarchy.

    Args:
        states: Complete applicable typed state hierarchy.
        live: Whether fail-closed live evidence is required.
        precedence: Fixed order index.

    Returns:
        Ordered kill-switch check.
    """
    logger.debug("Evaluating applicable Risk kill-switch hierarchy")
    refs = tuple(state.state_id for state in states) or ("kill-switch:none",)
    if any(state.state == "active" for state in states):
        return _limit(
            "kill_switch",
            LimitStatus.BLOCKED,
            precedence,
            refs,
            reason=RiskErrorCode.KILL_SWITCH_ACTIVE,
        )
    if any(state.state == "unknown" for state in states) or (live and not states):
        return _limit(
            "kill_switch",
            LimitStatus.BLOCKED,
            precedence,
            refs,
            reason=RiskErrorCode.KILL_SWITCH_UNKNOWN,
        )
    return _limit("kill_switch", LimitStatus.PASS, precedence, refs)


def _regime_result(
    regime: RegimeAssessment, *, live: bool, precedence: int
) -> RiskLimitResult:
    """Evaluate supplied regime completeness without loosening limits.

    Args:
        regime: Supplied deterministic regime assessment.
        live: Whether unknown regime state blocks.
        precedence: Fixed order index.

    Returns:
        Ordered regime evidence check.
    """
    logger.debug("Evaluating supplied Risk regime completeness")
    unknown = any(state == "unknown" for state in regime.states.values())
    status = LimitStatus.BLOCKED if live and unknown else LimitStatus.PASS
    return _limit(
        "regime_evidence",
        status,
        precedence,
        (regime.assessment_id, *regime.evidence_refs),
        reason=RiskErrorCode.MISSING_EVIDENCE
        if status is LimitStatus.BLOCKED
        else None,
    )


def _state_for_results(results: Sequence[RiskLimitResult]) -> DecisionState:
    """Map ordered checks to one canonical decision state.

    Args:
        results: Complete ordered checks.

    Returns:
        Canonical decision state before approval eligibility.
    """
    logger.debug("Mapping ordered Risk checks to canonical decision state")
    statuses = {item.status for item in results}
    if statuses & {LimitStatus.FAIL, LimitStatus.BLOCKED}:
        return DecisionState.BLOCK
    if LimitStatus.NEEDS_MORE_EVIDENCE in statuses:
        return DecisionState.NEEDS_MORE_EVIDENCE
    if LimitStatus.WARN in statuses:
        return DecisionState.WARN
    return DecisionState.APPROVE


def _failures(
    results: Sequence[RiskLimitResult],
) -> tuple[str | None, tuple[str, ...]]:
    """Return the primary and composite non-pass check identities.

    Args:
        results: Complete ordered checks.

    Returns:
        First non-pass identity and every non-pass identity.
    """
    logger.debug("Selecting primary and composite Risk check outcomes")
    flags = tuple(
        item.limit_id for item in results if item.status is not LimitStatus.PASS
    )
    return (flags[0] if flags else None), flags


def _audit_input(decision: RiskDecisionPackage, now: datetime) -> RiskAuditRecord:
    """Build one unsealed canonical governor decision audit record.

    Args:
        decision: Completed Risk decision.
        now: Checked UTC decision time.

    Returns:
        Unsealed secret-safe audit input.
    """
    logger.debug("Building canonical Risk governor audit input")
    return RiskAuditRecord(
        record_id=_identity("governor.audit", {"decision_id": decision.decision_id}),
        event_type="risk.governor.decision",
        payload={
            "state": decision.state.value,
            "primary_failure": decision.primary_failure_limit,
            "composite_flags": decision.composite_breach_flags,
            "concurrency": decision.concurrency_disclosure,
        },
        evidence_refs=decision.evidence_refs,
        config_hash=decision.config_hash,
        decision_id=decision.decision_id,
        occurred_at=now,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=decision.request_id,
        correlation_id=decision.correlation_id,
    )


class RiskGovernor:
    """Own fixed-precedence trade and current-state Risk coordination."""

    def __init__(
        self,
        config: RiskConfig,
        approvals: ApprovalTokenService,
        audit: RiskAuditChain,
        clock: Callable[[], datetime],
        capacity_guard: _CapacityGuard | None = None,
    ) -> None:
        """Initialize canonical Risk governor dependencies.

        Args:
            config: Immutable active Risk policy.
            approvals: Durable approval-token service.
            audit: Tamper-evident Risk audit chain.
            clock: Injected aware UTC clock.
            capacity_guard: Optional configured atomic capacity owner.

        Raises:
            RiskDomainError: If live or time dependencies are incomplete.
        """
        logger.info("Initializing canonical fixed-precedence Risk governor")
        try:
            _validate_governor_dependencies(config, clock, capacity_guard)
        except (TypeError, ValueError) as error:
            raise RiskDomainError(
                RiskErrorCode.INVALID_RISK_CONFIG,
                "Risk governor dependencies are incomplete",
            ) from error
        self._config = config
        self._approvals = approvals
        self._audit = audit
        self._clock = clock
        self._capacity_guard = capacity_guard

    def _config_hash(self) -> str:
        """Return the current configuration hash after response validation.

        Returns:
            The exact current Risk configuration hash.

        Raises:
            RiskDomainError: If configuration hashing fails.
        """
        return unwrap_risk_response(
            compute_config_hash(self._config), operation="compute_config_hash"
        )

    def _append_audit(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Append one governor audit record and fail closed on persistence errors.

        Args:
            record: Unsealed governor audit record.

        Returns:
            Durable sealed audit record.

        Raises:
            RiskDomainError: If audit persistence fails.
        """
        return unwrap_risk_response(
            self._audit.append(record), operation="risk_audit.append"
        )

    def _validate_common(
        self,
        snapshot: PortfolioRiskSnapshot,
        auth: AuthContext,
        now: datetime,
    ) -> None:
        """Validate current config, snapshot, clock, and auth trace bindings.

        Args:
            snapshot: Supplied immutable portfolio evidence.
            auth: Authenticated caller context.
            now: Caller-supplied UTC decision time.

        Raises:
            ValueError: If any exact common binding conflicts.
        """
        logger.debug("Validating common Risk governor bindings")
        checked_clock = _utc(self._clock())
        tolerance = timedelta(
            seconds=float(self._config.clock_skew_tolerance_seconds or 0)
        )
        if abs(now - checked_clock) > tolerance:
            raise ValueError("governor clock skew exceeded")
        if snapshot.config_hash != self._config_hash():
            raise ValueError("snapshot configuration binding conflicts")
        if auth.runtime_profile != self._config.profile:
            raise ValueError("authenticated environment conflicts with Risk profile")

    def _capacity_result(
        self,
        proposal: ProposedTrade,
        capped_size: Decimal,
        precedence: int,
    ) -> tuple[RiskLimitResult, str]:
        """Apply configured receiver-owned concurrency protection.

        Args:
            proposal: Exact risk-increasing proposal.
            capped_size: Regime-capped requested size.
            precedence: Fixed order index.

        Returns:
            Ordered capacity result and concurrency disclosure.

        Raises:
            RiskDomainError: If a configured capacity dependency is unavailable.
        """
        logger.debug("Applying configured Risk concurrent-capacity protection")
        if self._capacity_guard is None:
            return (
                _limit(
                    "concurrent_capacity",
                    LimitStatus.PASS,
                    precedence,
                    ("risk_store:approval_token",),
                ),
                "risk_store:atomic_token_consumption",
            )
        reservation_key = _identity(
            "capacity",
            {
                "intent_id": proposal.intent.intent_id,
                "config_hash": self._config_hash(),
                "size": capped_size,
            },
        )
        try:
            outcome = self._capacity_guard.reserve_capacity(
                reservation_key=reservation_key,
                account_id=proposal.account_id,
                strategy_id=proposal.intent.strategy_id,
                symbol=proposal.intent.symbol,
                requested_notional=capped_size * proposal.current_price,
                expires_at=min(
                    proposal.expires_at,
                    _utc(self._clock())
                    + timedelta(seconds=float(self._config.decision_ttl_seconds)),
                ),
                timeout_seconds=self._config.dependency_timeouts_seconds.get(
                    "capacity_guard"
                ),
            )
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "capacity guard unavailable"
            ) from error
        passed = outcome in {"reserved", "already_reserved"}
        return (
            _limit(
                "concurrent_capacity",
                LimitStatus.PASS if passed else LimitStatus.BLOCKED,
                precedence,
                (reservation_key,),
                reason=None
                if passed
                else RiskErrorCode.PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED,
            ),
            f"capacity_guard:{outcome}",
        )

    def _validate_trade_bindings(
        self,
        proposal: ProposedTrade,
        snapshot: PortfolioRiskSnapshot,
        market: _MarketContextEvidenceView,
        auth: AuthContext,
        now: datetime,
    ) -> None:
        """Validate exact proposal, evidence, and authenticated trace bindings.

        Args:
            proposal: Submitted Risk-owned proposal.
            snapshot: Current immutable portfolio evidence.
            market: Current normalized market evidence.
            auth: Authenticated caller context.
            now: Checked UTC decision time.

        Raises:
            ValueError: If any material binding conflicts.
        """
        logger.debug("Validating exact trade Risk governor bindings")
        if (
            proposal.risk_profile != self._config.profile
            or proposal.account_id != snapshot.account_id
            or proposal.intent.symbol != market.symbol
            or proposal.expires_at <= now
            or proposal.market_as_of != market.as_of
            or auth.request_id != proposal.request_id
            or auth.workflow_id != proposal.workflow_id
            or auth.correlation_id != proposal.correlation_id
        ):
            raise ValueError("proposal, evidence, or auth binding conflicts")

    @staticmethod
    def _validate_portfolio_trace(
        snapshot: PortfolioRiskSnapshot, auth: AuthContext
    ) -> None:
        """Validate exact current-state review trace bindings.

        Args:
            snapshot: Current immutable portfolio evidence.
            auth: Authenticated caller context.

        Raises:
            ValueError: If request or workflow identity conflicts.
        """
        logger.debug("Validating current-state Risk governor trace bindings")
        if (
            auth.request_id != snapshot.request_id
            or auth.workflow_id != snapshot.workflow_id
        ):
            raise ValueError("portfolio governor auth trace conflicts")

    def _base_checks(
        self,
        snapshot: PortfolioRiskSnapshot,
        market: _MarketContextEvidenceView,
        regime: RegimeAssessment,
        kill_switch_states: Sequence[KillSwitchState],
        now: datetime,
    ) -> list[RiskLimitResult]:
        """Evaluate fixed kill, evidence, regime, and policy precedence.

        Args:
            snapshot: Current immutable portfolio evidence.
            market: Current normalized market context.
            regime: Current deterministic regime assessment.
            kill_switch_states: Complete applicable typed state hierarchy.
            now: Checked UTC decision time.

        Returns:
            Mutable ordered checks for final capacity/projection extension.
        """
        logger.debug("Evaluating fixed Risk governor safety precedence")
        checks = [
            _kill_switch_result(
                kill_switch_states,
                live=self._config.profile == "live",
                precedence=0,
            ),
            _regime_result(regime, live=self._config.profile == "live", precedence=1),
        ]
        portfolio = unwrap_risk_response(
            evaluate_portfolio_limits(snapshot, self._config, now=now),
            operation="evaluate_portfolio_limits",
        )
        market_results = unwrap_risk_response(
            evaluate_market_context(market, self._config, now=now),
            operation="evaluate_market_context",
        )
        checks.extend(_reindex(portfolio, len(checks)))
        checks.extend(_reindex(market_results, len(checks)))
        return checks

    @guard_risk_boundary(
        risk_level="critical",
        read_only=False,
        modifies_database=True,
    )
    def review_trade_risk(
        self,
        proposal: ProposedTrade,
        snapshot: PortfolioRiskSnapshot,
        market: _MarketContextEvidenceView,
        regime: RegimeAssessment,
        kill_switch_states: Sequence[KillSwitchState],
        auth: AuthContext,
        *,
        attestation: ApprovalAttestation | None = None,
        now: datetime,
        evidence_now: datetime | None = None,
    ) -> RiskDecisionPackage:
        """Review one proposed trade through fixed fail-closed precedence.

        Args:
            proposal: Risk-owned non-executable proposal.
            snapshot: Current immutable portfolio evidence.
            market: Current normalized market evidence.
            regime: Current deterministic regime assessment.
            kill_switch_states: Complete applicable typed state hierarchy.
            auth: Authenticated caller and trace context.
            attestation: Optional UI/API-produced human approval evidence.
            now: Caller-supplied UTC decision time.
            evidence_now: Optional historical evidence time. Decision tokens,
                audit records, and expiry remain bound to ``now``.

        Returns:
            Audited canonical Risk decision package.

        Raises:
            RiskDomainError: If validation, calculation, approval, concurrency,
                or mandatory persistence fails.
        """
        logger.info("Reviewing one proposed trade through canonical Risk precedence")
        started_at = monotonic()
        try:
            checked_now = _utc(now)
            checked_evidence_now = _utc(evidence_now or now)
            self._validate_common(snapshot, auth, checked_evidence_now)
            self._validate_trade_bindings(
                proposal, snapshot, market, auth, checked_evidence_now
            )
            checks = self._base_checks(
                snapshot, market, regime, kill_switch_states, checked_evidence_now
            )
            modifier = min(regime.modifiers.values(), default=Decimal(1))
            capped_size = proposal.requested_size * modifier
            projected_gross = snapshot.gross_exposure + abs(
                capped_size * proposal.current_price
            )
            checks.append(
                _limit(
                    "projected_gross_exposure",
                    LimitStatus.PASS,
                    len(checks),
                    (snapshot.snapshot_id, proposal.intent.intent_id),
                    observed=projected_gross,
                )
            )
            risk_increasing = proposal.intent.intent_type in {"OPEN", "INCREASE"}
            concurrency = "not_required:risk_reducing_action"
            if risk_increasing and _state_for_results(checks) is DecisionState.APPROVE:
                capacity, concurrency = self._capacity_result(
                    proposal, capped_size, len(checks)
                )
                checks.append(capacity)
            state = _state_for_results(checks)
            if (
                state is DecisionState.APPROVE
                and risk_increasing
                and attestation is None
            ):
                state = DecisionState.NEEDS_APPROVAL
            primary, flags = _failures(checks)
            if state is DecisionState.NEEDS_APPROVAL:
                primary = "approval_required"
                flags = (*flags, "approval_required")
            config_hash = self._config_hash()
            decision_id = _identity(
                "trade.decision",
                {
                    "intent_id": proposal.intent.intent_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "regime_id": regime.assessment_id,
                    "config_hash": config_hash,
                    "state": state.value,
                },
            )
            expires_at = min(
                proposal.expires_at,
                checked_now
                + timedelta(seconds=float(self._config.decision_ttl_seconds)),
            )
            approved_size = capped_size if state is DecisionState.APPROVE else None
            decision = RiskDecisionPackage(
                decision_id=decision_id,
                intent_id=proposal.intent.intent_id,
                state=state,
                requested_size=proposal.requested_size,
                approved_size=approved_size,
                ordered_checks=tuple(checks),
                primary_failure_limit=primary,
                composite_breach_flags=flags,
                evidence_refs={
                    "proposal": proposal.request_id,
                    "portfolio": snapshot.snapshot_id,
                    "market": market.request_id,
                    "regime": regime.assessment_id,
                    "config": config_hash,
                },
                config_hash=config_hash,
                concurrency_disclosure=concurrency,
                recommendations=("obtain_authenticated_approval",)
                if state is DecisionState.NEEDS_APPROVAL
                else ("do_not_increase_risk",)
                if state in {DecisionState.BLOCK, DecisionState.REJECT}
                else (),
                issued_at=checked_now,
                expires_at=expires_at,
                token=None,
                request_id=proposal.request_id,
                workflow_id=proposal.workflow_id,
                correlation_id=proposal.correlation_id,
            )
            if state is DecisionState.APPROVE and risk_increasing:
                required_attestation = _require_attestation(attestation)
                token = unwrap_risk_response(
                    self._approvals.issue(
                        decision, required_attestation, now=checked_now
                    ),
                    operation="approval_tokens.issue",
                )
                decision = decision.model_copy(update={"token": token})
            self._append_audit(_audit_input(decision, checked_now))
            logger.bind(
                request_id=decision.request_id,
                workflow_id=decision.workflow_id,
                correlation_id=decision.correlation_id,
                verdict=decision.state.value,
                reason_codes=tuple(
                    check.reason_code.value
                    for check in decision.ordered_checks
                    if check.reason_code is not None
                ),
                latency_ms=round((monotonic() - started_at) * 1000, 3),
                evidence_refs=dict(decision.evidence_refs),
                config_hash=decision.config_hash,
            ).info("Completed canonical trade Risk decision")
            return decision
        except RiskDomainError as error:
            if error.risk_code is RiskErrorCode.STORAGE_ERROR:
                raise
            raise RiskDomainError(
                RiskErrorCode.GOVERNOR_DECISION_FAILED,
                "trade Risk governor failed closed",
            ) from error
        except (ArithmeticError, KeyError, TypeError, ValueError) as error:
            raise RiskDomainError(
                RiskErrorCode.GOVERNOR_DECISION_FAILED,
                "trade Risk governor failed closed",
            ) from error

    @guard_risk_boundary(
        risk_level="critical",
        read_only=False,
        modifies_database=True,
    )
    def run_portfolio_risk_governor(
        self,
        snapshot: PortfolioRiskSnapshot,
        market: _MarketContextEvidenceView,
        regime: RegimeAssessment,
        kill_switch_states: Sequence[KillSwitchState],
        auth: AuthContext,
        *,
        now: datetime,
    ) -> RiskDecisionPackage:
        """Evaluate current compliance without mutating execution state.

        Args:
            snapshot: Current immutable portfolio evidence.
            market: Current normalized market evidence.
            regime: Current deterministic regime assessment.
            kill_switch_states: Complete applicable typed state hierarchy.
            auth: Authenticated caller and trace context.
            now: Caller-supplied UTC decision time.

        Returns:
            Audited current-state compliance and remediation recommendation.

        Raises:
            RiskDomainError: If validation, calculation, or audit persistence fails.
        """
        logger.info("Running current-state portfolio Risk governor")
        started_at = monotonic()
        try:
            checked_now = _utc(now)
            self._validate_common(snapshot, auth, checked_now)
            self._validate_portfolio_trace(snapshot, auth)
            checks = self._base_checks(
                snapshot, market, regime, kill_switch_states, checked_now
            )
            state = _state_for_results(checks)
            primary, flags = _failures(checks)
            config_hash = self._config_hash()
            decision = RiskDecisionPackage(
                decision_id=_identity(
                    "portfolio.decision",
                    {
                        "snapshot_id": snapshot.snapshot_id,
                        "regime_id": regime.assessment_id,
                        "config_hash": config_hash,
                        "state": state.value,
                    },
                ),
                intent_id=None,
                state=state,
                requested_size=None,
                approved_size=None,
                ordered_checks=tuple(checks),
                primary_failure_limit=primary,
                composite_breach_flags=flags,
                evidence_refs={
                    "portfolio": snapshot.snapshot_id,
                    "market": market.request_id,
                    "regime": regime.assessment_id,
                    "config": config_hash,
                },
                config_hash=config_hash,
                concurrency_disclosure="not_applicable:current_state_review",
                recommendations=("reduce_or_reconcile_risk",)
                if state is not DecisionState.APPROVE
                else ("no_remediation_required",),
                issued_at=checked_now,
                expires_at=checked_now
                + timedelta(seconds=float(self._config.decision_ttl_seconds)),
                token=None,
                request_id=auth.request_id,
                workflow_id=auth.workflow_id,
                correlation_id=auth.correlation_id,
            )
            self._append_audit(_audit_input(decision, checked_now))
            logger.bind(
                request_id=decision.request_id,
                workflow_id=decision.workflow_id,
                correlation_id=decision.correlation_id,
                verdict=decision.state.value,
                reason_codes=tuple(
                    check.reason_code.value
                    for check in decision.ordered_checks
                    if check.reason_code is not None
                ),
                latency_ms=round((monotonic() - started_at) * 1000, 3),
                evidence_refs=dict(decision.evidence_refs),
                config_hash=decision.config_hash,
            ).info("Completed canonical portfolio Risk decision")
            return decision
        except RiskDomainError as error:
            if error.risk_code is RiskErrorCode.STORAGE_ERROR:
                raise
            raise RiskDomainError(
                RiskErrorCode.GOVERNOR_DECISION_FAILED,
                "portfolio Risk governor failed closed",
            ) from error
        except (KeyError, TypeError, ValueError) as error:
            raise RiskDomainError(
                RiskErrorCode.GOVERNOR_DECISION_FAILED,
                "portfolio Risk governor failed closed",
            ) from error


@guard_risk_boundary(risk_level="medium", read_only=True)
def evaluate_emergency_state(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    *,
    now: datetime,
) -> RiskLimitResult:
    """Evaluate configured emergency triggers and derive lock/recovery state.

    Detects margin-call, drawdown-breach, and data/connectivity-failure
    emergencies using the emergency rule group added by ``feature``.
    Flash-crash detection is intentionally not evaluated here: no Data-owned
    evidence contract currently carries a bounded recent price-move
    measurement, so this trigger is not approximated from an unrelated
    field; it remains a documented gap pending that upstream evidence
    contract. Disabled configuration (no emergency group configured) always
    passes. An active or unknown-evidence emergency fails closed to
    ``BLOCKED``.

    Args:
        snapshot: Current immutable portfolio evidence.
        config: Active validated Risk configuration.
        now: Explicit aware-UTC evaluation time.

    Returns:
        Ordered emergency-state check; ``BLOCKED`` marks an active emergency.

    Raises:
        RiskDomainError: If evaluation time is not aware UTC.
    """
    logger.info("Evaluating configured Risk emergency triggers")
    checked_now = _utc(now)
    evidence_refs = (snapshot.snapshot_id,)
    if config.emergency_margin_call_utilization_pct is None:
        return _limit("emergency_state", LimitStatus.PASS, 0, evidence_refs)
    triggers: list[str] = []
    if (
        snapshot.margin_utilization is not None
        and snapshot.margin_utilization >= config.emergency_margin_call_utilization_pct
    ):
        triggers.append("margin_emergency")
    if snapshot.drawdown >= config.max_drawdown:
        triggers.append("drawdown_breach")
    staleness = (checked_now - snapshot.as_of).total_seconds()
    connectivity_bound = config.emergency_connectivity_loss_seconds or 0
    if staleness < 0 or staleness > connectivity_bound:
        triggers.append("connectivity_failure")
    if triggers:
        logger.warning("Risk emergency state active: %s", ", ".join(triggers))
        return _limit(
            "emergency_state",
            LimitStatus.BLOCKED,
            0,
            evidence_refs,
            reason=RiskErrorCode.LIMIT_FAILED,
        )
    return _limit("emergency_state", LimitStatus.PASS, 0, evidence_refs)


@guard_risk_boundary(risk_level="high", read_only=True)
def evaluate_trade_readiness(
    stop_validation: Mapping[str, object],
    kill_switch_states: Sequence[KillSwitchState],
    scope: Mapping[str, str],
    snapshot: PortfolioRiskSnapshot,
    market: _MarketContextEvidenceView,
    config: RiskConfig,
    stress_layer_loss_ratios: Mapping[str, Decimal],
    max_stress_loss_ratio: Decimal,
    *,
    now: datetime,
) -> tuple[RiskLimitResult, ...]:
    """Re-evaluate the fixed-precedence submit-time trade readiness gate.

    Composes already-built gates into one explicit re-validation step at
    order submission, in fixed precedence: session/news (market context),
    lock (kill-switch ``new_exposure`` permission), entry/stop validity,
    broker/data freshness plus margin/correlation/drawdown (portfolio
    limits), and the blocking stress-loss gate. Strategy operational
    eligibility (:func:`app.services.risk.admission.review_strategy_admission`)
    is a separate persistence-owning gate the caller composes alongside this
    one; it is not re-implemented here because it requires an eligibility
    store and audit chain this pure gate does not own. The first non-pass
    result is the primary failure; every failing result is preserved.

    Args:
        stop_validation: JSON-safe ``StopValidation v1`` mapping built by
            :func:`app.services.risk.stop_validation.build_stop_validation`.
        kill_switch_states: Complete applicable kill-switch state hierarchy.
        scope: Exact action portfolio/strategy/symbol scope for the lock
            check.
        snapshot: Current immutable portfolio evidence.
        market: Current normalized market-context evidence.
        config: Active validated Risk configuration.
        stress_layer_loss_ratios: Non-negative equity-loss ratio per
            registered stress layer.
        max_stress_loss_ratio: Configured maximum combined stress-loss
            ratio.
        now: Explicit aware-UTC evaluation time.

    Returns:
        Ordered readiness-gate results across every composed check.
    """
    logger.info("Evaluating fixed-precedence Risk trade readiness gate")
    checked_now = _utc(now)
    market_results = unwrap_risk_response(
        evaluate_market_context(market, config, now=checked_now),
        operation="evaluate_market_context",
    )
    lock_permitted = unwrap_risk_response(
        permits_risk_action(kill_switch_states, scope, "new_exposure"),
        operation="permits_risk_action",
    )
    lock_result = _limit(
        "lock",
        LimitStatus.PASS if lock_permitted else LimitStatus.BLOCKED,
        0,
        (snapshot.snapshot_id,),
        reason=None if lock_permitted else RiskErrorCode.KILL_SWITCH_ACTIVE,
    )
    stop_results = unwrap_risk_response(
        validate_stop_loss(stop_validation), operation="validate_stop_loss"
    )
    portfolio_results = unwrap_risk_response(
        evaluate_portfolio_limits(snapshot, config, now=checked_now),
        operation="evaluate_portfolio_limits",
    )
    stress_result = unwrap_risk_response(
        evaluate_stress_loss_gate(
            snapshot,
            stress_layer_loss_ratios,
            max_stress_loss_ratio,
            now=checked_now,
        ),
        operation="evaluate_stress_loss_gate",
    )
    return _reindex(
        (
            *market_results,
            lock_result,
            *stop_results,
            *portfolio_results,
            stress_result,
        ),
        0,
    )


def create_risk_governor(
    config: RiskConfig,
    approvals: ApprovalTokenService,
    audit: RiskAuditChain,
    clock: Callable[[], datetime],
    capacity_guard: _CapacityGuard | None = None,
) -> RiskGovernor:
    """Create an opaque fixed-precedence Risk governor.

    Args:
        config: Validated Risk configuration.
        approvals: Opaque approval-token coordinator.
        audit: Opaque Risk audit coordinator.
        clock: Injected aware-UTC clock.
        capacity_guard: Optional atomic in-flight capacity owner.

    Returns:
        Opaque internal Risk governor.
    """
    return RiskGovernor(config, approvals, audit, clock, capacity_guard)


def review_trade_risk(
    governor: RiskGovernor,
    proposal: ProposedTrade,
    snapshot: PortfolioRiskSnapshot,
    market: _MarketContextEvidenceView,
    regime: RegimeAssessment,
    kill_switch_states: Sequence[KillSwitchState],
    auth: object,
    *,
    attestation: ApprovalAttestation | None = None,
    now: datetime,
    evidence_now: datetime | None = None,
) -> object:
    """Review one proposed trade through an opaque Risk governor.

    Args:
        governor: Opaque governor returned by :func:`create_risk_governor`.
        proposal: Risk-owned non-executable proposal.
        snapshot: Current immutable portfolio evidence.
        market: Current normalized market-context evidence.
        regime: Current deterministic regime assessment.
        kill_switch_states: Complete applicable kill-switch hierarchy.
        auth: Authenticated caller and trace context.
        attestation: Optional current human approval evidence.
        now: Explicit aware-UTC decision time.
        evidence_now: Optional historical evidence time used only for evidence
            freshness and market-time validation.

    Returns:
        Standard response carrying the canonical Risk decision.

    Raises:
        TypeError: If ``governor`` is not a Risk governor.
    """
    if not isinstance(governor, RiskGovernor):
        raise TypeError("governor must be created by create_risk_governor")
    return governor.review_trade_risk(
        proposal,
        snapshot,
        market,
        regime,
        kill_switch_states,
        auth,
        attestation=attestation,
        now=now,
        evidence_now=evidence_now,
    )


def run_portfolio_risk_governor(
    governor: RiskGovernor,
    snapshot: PortfolioRiskSnapshot,
    market: _MarketContextEvidenceView,
    regime: RegimeAssessment,
    kill_switch_states: Sequence[KillSwitchState],
    auth: object,
    *,
    now: datetime,
) -> object:
    """Evaluate current portfolio compliance through an opaque governor.

    Args:
        governor: Opaque governor returned by :func:`create_risk_governor`.
        snapshot: Current immutable portfolio evidence.
        market: Current normalized market-context evidence.
        regime: Current deterministic regime assessment.
        kill_switch_states: Complete applicable kill-switch hierarchy.
        auth: Authenticated caller and trace context.
        now: Explicit aware-UTC decision time.

    Returns:
        Standard response carrying the canonical current-state decision.

    Raises:
        TypeError: If ``governor`` is not a Risk governor.
    """
    if not isinstance(governor, RiskGovernor):
        raise TypeError("governor must be created by create_risk_governor")
    return governor.run_portfolio_risk_governor(
        snapshot,
        market,
        regime,
        kill_switch_states,
        auth,
        now=now,
    )


__all__ = [
    "RiskGovernor",
    "create_risk_governor",
    "evaluate_emergency_state",
    "evaluate_trade_readiness",
    "review_trade_risk",
    "run_portfolio_risk_governor",
]
