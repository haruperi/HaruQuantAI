"""Strict Pydantic v2 wire records for the ratified Runtime Risk v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from app.contracts.common.models import (
    ContentHash,
    CurrencyCode,
    DecimalValue,
    JsonObject,
    Money,
    RuntimeRiskDecision,
    Side,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# This reference type is annotation-only for readers but Pydantic resolves it
# at class-creation time, so it must remain a runtime import.
from app.contracts.workspace.models import (  # noqa: TC001
    PrincipalRef,
)

# Constrained local string alias reused across risk records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Closed enum literals local to the Risk records. Decision verdicts reuse the
# shared ``RuntimeRiskDecision`` set; limit states are Risk-local per the
# ratified v1 public-records table.
type RiskLimitState = Literal["PASS", "WARN", "MISSING", "FAIL", "BLOCKED"]
type RiskEvidenceSourceOwner = Literal[
    "ACCOUNT",
    "FX",
    "MARKET",
    "NEWS",
    "SESSION",
    "STRATEGY",
    "BROKER",
    "PORTFOLIO",
]
type RiskEvidenceFreshness = Literal["FRESH", "STALE", "MISSING"]
type RiskTokenState = Literal["ISSUED", "CONSUMED", "REVOKED", "EXPIRED"]
type RiskReservationState = Literal["RESERVED", "COMMITTED", "RELEASED", "EXPIRED"]
type KillSwitchScopeKind = Literal[
    "GLOBAL",
    "ENVIRONMENT",
    "BROKER_ACCOUNT",
    "PORTFOLIO",
    "STRATEGY",
    "SYMBOL",
]
type KillSwitchSignalState = Literal["ACTIVE", "CLEARED", "UNKNOWN"]
type StrategyEligibilityOutcome = Literal["ELIGIBLE", "CONDITIONAL", "INELIGIBLE"]
type RiskAuditEventKind = Literal[
    "PROFILE",
    "EVIDENCE_VALIDATION",
    "DECISION",
    "TOKEN",
    "RESERVATION",
    "KILL_SWITCH",
    "ELIGIBILITY",
    "ALLOCATION",
    "REUSE",
    "SCENARIO",
]


def _require_present(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that omits a required field.

    Args:
        fields: ``(field name, value)`` pairs that must not be None.

    Raises:
        ValueError: Any listed field is None.
    """
    for name, value in fields:
        if value is None:
            raise ValueError("required field is missing: " + name)


def _require_absent(fields: tuple[tuple[str, object], ...]) -> None:
    """Reject an operation request that sets a forbidden field.

    Args:
        fields: ``(field name, value)`` pairs that must be None.

    Raises:
        ValueError: Any listed field is not None.
    """
    for name, value in fields:
        if value is not None:
            raise ValueError("forbidden field is set: " + name)


class RiskDecisionState(WireModel):
    """Named runtime decision-state entry for one decision identity."""

    decision_id: Uuid7
    verdict: RuntimeRiskDecision
    entered_at: UtcTimestamp
    schema_version: Literal[1] = 1


class RiskProfileRef(WireModel):
    """Reference to one risk profile identity."""

    profile_id: Uuid7
    schema_version: Literal[1] = 1


class RiskProfileVersion(WireModel):
    """One immutable, effective-dated risk profile version.

    Thresholds, units, modes, and every policy object are strictly validated
    by the owning feature; the wire record pins their canonical hash and
    half-open effective interval without implicit defaults.
    """

    profile_id: Uuid7
    version: int = Field(ge=1)
    effective_from: UtcTimestamp
    thresholds: JsonObject
    units: JsonObject
    modes: JsonObject
    freshness_policy: JsonObject
    rounding_policy: JsonObject
    concurrency_policy: JsonObject
    approval_policy: JsonObject
    audit_policy: JsonObject
    failure_precedence: NonEmptyStr
    content_hash: ContentHash
    effective_to: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_effective_interval(self) -> RiskProfileVersion:
        """Reject a non-half-open effective interval.

        Returns:
            The validated profile version.

        Raises:
            ValueError: ``effective_to`` is not strictly after
                ``effective_from``.
        """
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class FirmMandateVersion(WireModel):
    """One immutable, effective-dated firm mandate version."""

    mandate_id: Uuid7
    version: int = Field(ge=1)
    rules: JsonObject
    effective_from: UtcTimestamp
    content_hash: ContentHash
    effective_to: UtcTimestamp | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_effective_interval(self) -> FirmMandateVersion:
        """Reject a non-half-open effective interval.

        Returns:
            The validated mandate version.

        Raises:
            ValueError: ``effective_to`` is not strictly after
                ``effective_from``.
        """
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class RiskEvidenceRef(WireModel):
    """Reference to one consumed cross-owner source-evidence record.

    Owner schema, identity, UTC time, freshness, coverage, provenance,
    explicit missingness, and exact units are validated without redefining
    the source record itself.
    """

    evidence_id: Uuid7
    source_owner: RiskEvidenceSourceOwner
    source_record_id: Uuid7
    source_hash: ContentHash
    observed_at: UtcTimestamp
    freshness: RiskEvidenceFreshness
    missingness: str = ""
    units: NonEmptyStr
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_explicit_missingness(self) -> RiskEvidenceRef:
        """Reject a MISSING freshness grade without explicit missingness.

        Domain assumption: an evidence reference graded ``MISSING`` must say
        what is missing; present evidence states the empty string instead.

        Returns:
            The validated evidence reference.

        Raises:
            ValueError: Freshness is ``MISSING`` and ``missingness`` is empty.
        """
        if self.freshness == "MISSING" and not self.missingness:
            raise ValueError("MISSING freshness requires explicit missingness")
        return self


class RiskLimitResult(WireModel):
    """One evaluated limit with its precedence-ordered state.

    ``(decision_id, precedence)`` uniqueness is enforced by the owning
    store because it spans multiple result rows.
    """

    decision_id: Uuid7
    limit_key: NonEmptyStr
    state: RiskLimitState
    precedence: int = Field(ge=0)
    observed: DecimalValue | None
    threshold: DecimalValue | None
    unit: NonEmptyStr
    schema_version: Literal[1] = 1


class RiskSnapshot(WireModel):
    """Immutable portfolio/account risk snapshot for one decision.

    Pending, open, and reserved exposure are always carried explicitly and
    never silently excluded; ``duplicate_treatment`` discloses the
    deterministic duplicate and in-flight treatment used.
    """

    snapshot_id: Uuid7
    decision_id: Uuid7
    as_of: UtcTimestamp
    base_currency: CurrencyCode
    equity: Money
    daily_loss: Money
    total_loss: Money
    drawdown: DecimalValue
    gross_exposure: Money
    net_exposure: Money
    dimensional_exposure: JsonObject
    margin: Money | None
    leverage: DecimalValue | None
    historical_tail_risk: JsonObject
    volatility_contribution: JsonObject
    correlation_contribution: JsonObject
    limit_results: tuple[RiskLimitResult, ...] = ()
    pending_order_exposure: JsonObject
    open_position_exposure: JsonObject
    reserved_exposure: JsonObject
    duplicate_treatment: NonEmptyStr
    schema_version: Literal[1] = 1


class PositionSizeRecommendation(WireModel):
    """Bounded position-sizing recommendation that never implies approval."""

    recommendation_id: Uuid7
    decision_id: Uuid7
    method: NonEmptyStr
    method_version: int = Field(ge=1)
    requested_size: DecimalValue
    normalized_size: DecimalValue | None = None
    constraints_applied: JsonObject
    evidence_gaps: tuple[ValidationIssue, ...] = ()
    fallback_disclosure: str = ""
    calculation_trace: JsonObject
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_positive_sizes(self) -> PositionSizeRecommendation:
        """Reject nonpositive requested or normalized sizes.

        Returns:
            The validated sizing recommendation.

        Raises:
            ValueError: ``requested_size`` or a present
                ``normalized_size`` is zero or negative.
        """
        if Decimal(self.requested_size) <= 0:
            raise ValueError("requested_size must be positive")
        if self.normalized_size is not None and Decimal(self.normalized_size) <= 0:
            raise ValueError("normalized_size must be positive")
        return self


class StopLossAssessment(WireModel):
    """Validity assessment of one proposed protective stop.

    A missing or invalid stop, or missing required volatility evidence,
    rejects sizing and admission downstream.
    """

    assessment_id: Uuid7
    decision_id: Uuid7
    side: Side
    stop_price: DecimalValue
    tick_aligned: bool
    invalidation_distance: DecimalValue
    venue_minimum: DecimalValue | None
    noise_minimum: DecimalValue | None
    projected_loss: Money | None
    widening_permitted: bool
    is_valid: bool
    findings: tuple[ValidationIssue, ...] = ()
    schema_version: Literal[1] = 1


class ProposedAction(WireModel):
    """One complete immutable proposed action bound for admission.

    ``intent`` embeds the complete Strategy intent or Trading manual plan
    unchanged; Risk adds scope, valuation, stop, route, evidence, and the
    requested risk profile without altering it.
    """

    action_id: Uuid7
    intent: JsonObject
    account_scope: tuple[Uuid7, ...]
    portfolio_scope: tuple[Uuid7, ...]
    valuation: JsonObject
    stop: JsonObject | None
    route_profile: NonEmptyStr
    evidence: tuple[RiskEvidenceRef, ...] = ()
    requested_profile: RiskProfileRef
    schema_version: Literal[1] = 1


class OrderedCheck(WireModel):
    """One governor check at its fixed precedence position.

    This is the inline ``OrderedCheck`` record of
    ``RiskDecision.ordered_checks``.
    """

    check: NonEmptyStr
    state: RiskLimitState
    precedence: int = Field(ge=0)


class RiskDecision(WireModel):
    """Canonical governor decision package for one proposed action.

    The governor evaluates kill switch, evidence/profile validity,
    eligibility, session/news/regime constraints, stop, size,
    portfolio/market limits, allocation budget, approval policy, and
    capability availability in a fixed documented precedence; earlier
    blocking reasons cannot be masked by later approvals.
    """

    decision_id: Uuid7
    action: ProposedAction
    verdict: RuntimeRiskDecision
    allowed_action: JsonObject | None = None
    maximum_size: DecimalValue | None = None
    ordered_checks: tuple[OrderedCheck, ...] = ()
    primary_reason: str
    composite_reasons: tuple[str, ...] = ()
    expires_at: UtcTimestamp
    profile_version_id: Uuid7
    mandate_version_id: Uuid7 | None
    configuration_hash: ContentHash
    as_of: UtcTimestamp
    request_id: Uuid7
    workflow_id: Uuid7 | None
    correlation_id: Uuid7 | None
    concurrency_disclosure: JsonObject = Field(default_factory=dict)
    authorization_requirement: JsonObject | None = None
    snapshot: RiskSnapshot | None = None
    schema_version: Literal[1] = 1


class NoTradeDecision(WireModel):
    """Successful ``NO_TRADE`` outcome of a mandatory-gate rejection.

    A mandatory-gate rejection with a valid system and evidence state is a
    successful business stand-down, distinct from transport, calculation,
    or storage failure.
    """

    decision_id: Uuid7
    action: ProposedAction
    verdict: Literal["REJECT", "BLOCK"]
    is_valid_system_state: Literal[True]
    business_outcome: Literal["NO_TRADE"] = "NO_TRADE"
    reasons: tuple[str, ...] = ()
    provenance: JsonObject
    schema_version: Literal[1] = 1


class RiskApprovalRequest(WireModel):
    """Human-approval evidence binding one authenticated principal.

    Binds principal, exact action/scope/policy, hashes, times, and trace
    IDs; it carries no secret and grants no authority by itself.
    """

    approval_request_id: Uuid7
    decision_id: Uuid7
    principal: PrincipalRef
    action_hash: ContentHash
    scope: NonEmptyStr
    policy_version: int = Field(ge=1)
    config_hash: ContentHash
    trace_id: Uuid7
    issued_at: UtcTimestamp
    expires_at: UtcTimestamp
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_expiry(self) -> RiskApprovalRequest:
        """Reject an expiry that does not follow issuance.

        Domain assumption: an expiring approval binding must remain valid
        for a nonempty window after issuance.

        Returns:
            The validated approval request.

        Raises:
            ValueError: ``expires_at`` is not strictly after ``issued_at``.
        """
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class RiskApprovalToken(WireModel):
    """Signed, scoped, expiring, single-use approval token.

    Invalid, expired, revoked, consumed, or mismatched tokens grant no
    verdict; validation and consumption are atomic, so concurrent double
    spend yields at most one success.
    """

    token_id: Uuid7
    approval_request_id: Uuid7
    signature: NonEmptyStr
    scope: NonEmptyStr
    nonce: NonEmptyStr
    decision_hash: ContentHash
    config_hash: ContentHash
    action_hash: ContentHash
    approver: PrincipalRef
    issued_at: UtcTimestamp
    expires_at: UtcTimestamp
    state: RiskTokenState
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_expiry(self) -> RiskApprovalToken:
        """Reject an expiry that does not follow issuance.

        Domain assumption: a token cannot expire before or at the instant
        it is issued; the token TTL cannot outlive the underlying decision.

        Returns:
            The validated approval token.

        Raises:
            ValueError: ``expires_at`` is not strictly after ``issued_at``.
        """
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class RiskCapacityReservation(WireModel):
    """Durable risk-capacity reservation with fenced lifecycle transitions.

    Atomically reserved before dispatch against account, strategy,
    portfolio, symbol, and global budgets; Trading cannot substitute
    another action or amount, and concurrent admissions cannot exceed any
    hard budget.
    """

    reservation_id: Uuid7
    decision_id: Uuid7
    action_hash: ContentHash
    plan_hash: ContentHash
    amount: DecimalValue
    unit: NonEmptyStr
    scope: JsonObject
    predecessor_state_hash: ContentHash | None
    idempotency_key: NonEmptyStr
    issued_at: UtcTimestamp
    expires_at: UtcTimestamp
    state: RiskReservationState
    fencing_token: int = Field(ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_expiry(self) -> RiskCapacityReservation:
        """Reject an expiry that does not follow issuance.

        Domain assumption: expiry releases capacity unless already
        committed, so a reservation must hold capacity for a nonempty
        window after issuance.

        Returns:
            The validated reservation.

        Raises:
            ValueError: ``expires_at`` is not strictly after ``issued_at``.
        """
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class KillSwitchScope(WireModel):
    """One hierarchical kill-switch scope identity.

    An active broader scope dominates narrower clear states; the scope
    hash pins the exact scope identity used by state lookups.
    """

    scope_id: Uuid7
    kind: KillSwitchScopeKind
    scope_value: str | None = None
    scope_hash: ContentHash
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_scope_value(self) -> KillSwitchScope:
        """Reject scope values inconsistent with the scope kind.

        Domain assumption: the global scope is the broadest scope and
        carries no value, while every narrowing kind identifies exactly one
        target through a nonempty value.

        Returns:
            The validated scope.

        Raises:
            ValueError: A ``GLOBAL`` scope carries a value or a narrowing
                kind omits one.
        """
        if self.kind == "GLOBAL" and self.scope_value is not None:
            raise ValueError("GLOBAL scope must not carry a scope_value")
        if self.kind != "GLOBAL" and (self.scope_value is None or not self.scope_value):
            raise ValueError("non-global scope requires a nonempty scope_value")
        return self


class KillSwitchState(WireModel):
    """Current kill-switch state for one exact scope.

    Preflight and pre-dispatch checks read a known current version for the
    exact scope; active, unknown, stale, unavailable, or version-mismatched
    state blocks (fail-closed).
    """

    scope: KillSwitchScope
    version: int = Field(ge=1)
    state: KillSwitchSignalState
    reason: str
    last_transition_at: UtcTimestamp
    schema_version: Literal[1] = 1


class KillSwitchTransition(WireModel):
    """One atomic, append-only, audited kill-switch state transition.

    ``(scope_hash, version)`` uniqueness is enforced by the owning store
    because it spans multiple transition records; the critical causal event
    is published to Trading and Interfaces by the owning feature.
    """

    transition_id: Uuid7
    scope: KillSwitchScope
    from_state: KillSwitchSignalState | None
    to_state: KillSwitchSignalState
    version: int = Field(ge=1)
    authorized_principal: PrincipalRef
    reason: NonEmptyStr
    clearance_approval_token_id: Uuid7 | None = None
    remediation_evidence: JsonObject | None = None
    occurred_at: UtcTimestamp
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_clearance_requirements(self) -> KillSwitchTransition:
        """Reject a clear/recover transition without approval evidence.

        Domain assumption: both clear and recover transitions land on
        ``CLEARED`` and additionally require a separate matching current
        approval token and verified remediation evidence; activate and
        block transitions need only the authorized principal and reason,
        which are already required fields.

        Returns:
            The validated transition.

        Raises:
            ValueError: A transition to ``CLEARED`` omits
                ``clearance_approval_token_id`` or
                ``remediation_evidence``.
        """
        if self.to_state == "CLEARED":
            if self.clearance_approval_token_id is None:
                raise ValueError(
                    "clear/recover transitions require clearance_approval_token_id"
                )
            if self.remediation_evidence is None:
                raise ValueError(
                    "clear/recover transitions require remediation_evidence"
                )
        return self


class StrategyEligibilityDecision(WireModel):
    """Operational eligibility decision for one exact strategy version.

    The decision binds strategy/version, runtime profile, route, policy,
    evidence, approval context, conditions, validity interval, and
    decision lineage without altering Strategy registration.
    """

    eligibility_id: Uuid7
    strategy_version_id: Uuid7
    runtime_profile: NonEmptyStr
    route: NonEmptyStr
    policy_version: int = Field(ge=1)
    evidence: tuple[RiskEvidenceRef, ...] = ()
    approval_context: JsonObject
    conditions: JsonObject
    valid_from: UtcTimestamp
    valid_to: UtcTimestamp | None = None
    decision_lineage_id: Uuid7 | None
    outcome: StrategyEligibilityOutcome
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_validity_interval(self) -> StrategyEligibilityDecision:
        """Reject an inverted validity interval.

        Returns:
            The validated eligibility decision.

        Raises:
            ValueError: ``valid_to`` is present and not strictly after
                ``valid_from``.
        """
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be after valid_from")
        return self


class PortfolioAllocationReview(WireModel):
    """Risk review of a self-contained portfolio allocation projection.

    Consumes exact portfolio/allocation version identities, ordered
    weights, eligibility decisions, and account/market/FX evidence without
    importing Portfolio behavior.
    """

    review_id: Uuid7
    portfolio_version_id: Uuid7
    allocation_version_id: Uuid7
    ordered_weights: tuple[JsonObject, ...]
    eligibility: tuple[StrategyEligibilityDecision, ...] = ()
    account_market_fx_evidence: tuple[RiskEvidenceRef, ...] = ()
    runtime_scope: JsonObject
    self_contained_projection: JsonObject
    schema_version: Literal[1] = 1


class AllocationBudget(WireModel):
    """Authoritative capped allocation budget returned to Trading.

    Trading receives the authoritative capped values and validates them;
    it never recalculates budget consumption.
    """

    budget_decision_id: Uuid7
    review_id: Uuid7
    capped_weights: tuple[JsonObject, ...]
    risk_budget_projection: JsonObject
    conditions: JsonObject
    evidence_lineage: JsonObject
    policy_lineage: JsonObject
    expires_at: UtcTimestamp
    predecessor_binding: Uuid7 | None
    effective_at: UtcTimestamp | None
    schema_version: Literal[1] = 1


class ScenarioShock(WireModel):
    """One bounded deterministic shock along a named risk dimension.

    This is the inline ``ScenarioShock`` record of
    ``RiskScenarioRequest.shocks``.
    """

    dimension: NonEmptyStr
    magnitude: DecimalValue


class RiskScenarioRequest(WireModel):
    """Advisory what-if scenario request against one immutable snapshot.

    Advisory only; a scenario result never produces approval.
    """

    request_id: Uuid7
    baseline_snapshot_id: Uuid7
    shocks: tuple[ScenarioShock, ...]
    is_stochastic: bool
    seed: NonEmptyStr | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_stochastic_seed(self) -> RiskScenarioRequest:
        """Reject a stochastic scenario without an explicit seed.

        Returns:
            The validated scenario request.

        Raises:
            ValueError: ``is_stochastic`` is true and ``seed`` is omitted.
        """
        if self.is_stochastic and self.seed is None:
            raise ValueError("stochastic scenarios require an explicit seed")
        return self


class RiskScenarioResult(WireModel):
    """Advisory projected-risk result of one scenario request."""

    result_id: Uuid7
    request_id: Uuid7
    projected_snapshot: RiskSnapshot
    baseline_comparison: JsonObject
    assumptions: tuple[NonEmptyStr, ...]
    limitations: tuple[NonEmptyStr, ...]
    schema_version: Literal[1] = 1


class RiskAuditRecord(WireModel):
    """One redacted, canonical, hash-chained append-only audit record.

    ``record_hash`` covers the canonical redacted record and
    ``previous_hash`` links to the prior record's ``record_hash``; chain
    verification detects insertion, deletion, reordering, or mutation and
    is enforced by the owning feature because it spans records.
    """

    sequence: int = Field(ge=1)
    record_hash: ContentHash
    previous_hash: ContentHash
    event_kind: RiskAuditEventKind
    principal: PrincipalRef | None
    detail: JsonObject
    occurred_at: UtcTimestamp
    schema_version: Literal[1] = 1


class DefineRiskContractsRequest(WireModel):
    """Operation-discriminated profile, mandate, and evidence request.

    DEFINE_PROFILE requires only ``profile``; DEFINE_MANDATE requires only
    ``mandate``; VALIDATE_EVIDENCE requires only ``evidence``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["DEFINE_PROFILE", "DEFINE_MANDATE", "VALIDATE_EVIDENCE"]
    profile: RiskProfileVersion | None = None
    mandate: FirmMandateVersion | None = None
    evidence: RiskEvidenceRef | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DefineRiskContractsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "DEFINE_PROFILE":
                _require_present((("profile", self.profile),))
                _require_absent(
                    (
                        ("mandate", self.mandate),
                        ("evidence", self.evidence),
                    )
                )
            case "DEFINE_MANDATE":
                _require_present((("mandate", self.mandate),))
                _require_absent(
                    (
                        ("profile", self.profile),
                        ("evidence", self.evidence),
                    )
                )
            case "VALIDATE_EVIDENCE":
                _require_present((("evidence", self.evidence),))
                _require_absent(
                    (
                        ("profile", self.profile),
                        ("mandate", self.mandate),
                    )
                )
        return self


class DefineRiskContractsSuccess(WireModel):
    """Successful profile, mandate, and evidence operation result."""

    request_id: Uuid7
    profile: RiskProfileVersion | None = None
    mandate: FirmMandateVersion | None = None
    evidence: RiskEvidenceRef | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class CalculateRiskRequest(WireModel):
    """Operation-discriminated snapshot, sizing, stop, and report request.

    SNAPSHOT, SIZE_POSITION, VALIDATE_STOP, and REPORT require only
    ``decision_id``; RUN_SCENARIO requires only ``scenario``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "SNAPSHOT",
        "SIZE_POSITION",
        "VALIDATE_STOP",
        "RUN_SCENARIO",
        "REPORT",
    ]
    decision_id: Uuid7 | None = None
    scenario: RiskScenarioRequest | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> CalculateRiskRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "RUN_SCENARIO":
                _require_present((("scenario", self.scenario),))
                _require_absent((("decision_id", self.decision_id),))
            case "SNAPSHOT" | "SIZE_POSITION" | "VALIDATE_STOP" | "REPORT":
                _require_present((("decision_id", self.decision_id),))
                _require_absent((("scenario", self.scenario),))
        return self


class CalculateRiskSuccess(WireModel):
    """Successful snapshot, sizing, stop, and report operation result."""

    request_id: Uuid7
    snapshot: RiskSnapshot | None = None
    sizing: PositionSizeRecommendation | None = None
    stop: StopLossAssessment | None = None
    scenario: RiskScenarioResult | None = None
    report_artifact_id: Uuid7 | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ControlKillSwitchRequest(WireModel):
    """Operation-discriminated kill-switch command and check request.

    CHECK requires only ``scope``; ACTIVATE additionally requires
    ``principal`` and ``reason``; CLEAR and RECOVER additionally require
    ``clearance_approval_token_id`` and ``remediation_evidence``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CHECK", "ACTIVATE", "CLEAR", "RECOVER"]
    scope: KillSwitchScope | None = None
    principal: PrincipalRef | None = None
    reason: NonEmptyStr | None = None
    clearance_approval_token_id: Uuid7 | None = None
    remediation_evidence: JsonObject | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ControlKillSwitchRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        _require_present((("scope", self.scope),))
        match self.operation:
            case "CHECK":
                _require_absent(
                    (
                        ("principal", self.principal),
                        ("reason", self.reason),
                        (
                            "clearance_approval_token_id",
                            self.clearance_approval_token_id,
                        ),
                        ("remediation_evidence", self.remediation_evidence),
                    )
                )
            case "ACTIVATE":
                _require_present(
                    (
                        ("principal", self.principal),
                        ("reason", self.reason),
                    )
                )
                _require_absent(
                    (
                        (
                            "clearance_approval_token_id",
                            self.clearance_approval_token_id,
                        ),
                        ("remediation_evidence", self.remediation_evidence),
                    )
                )
            case "CLEAR" | "RECOVER":
                _require_present(
                    (
                        ("principal", self.principal),
                        ("reason", self.reason),
                        (
                            "clearance_approval_token_id",
                            self.clearance_approval_token_id,
                        ),
                        ("remediation_evidence", self.remediation_evidence),
                    )
                )
        return self


class ControlKillSwitchSuccess(WireModel):
    """Successful kill-switch command and check operation result."""

    request_id: Uuid7
    state: KillSwitchState | None = None
    transition: KillSwitchTransition | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GovernAdmissionRequest(WireModel):
    """Operation-discriminated admission and governor request.

    BIND_ACTION and EVALUATE require only ``action``; NO_TRADE and
    REVALIDATE require only ``decision_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["BIND_ACTION", "EVALUATE", "NO_TRADE", "REVALIDATE"]
    action: ProposedAction | None = None
    decision_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> GovernAdmissionRequest:
        """Validate that request fields match the selected operation.

        Domain assumption: NO_TRADE derives the typed ``NO_TRADE`` outcome
        from an existing REJECT/BLOCK decision, and REVALIDATE revalidates
        a prior decision, so both reference ``decision_id``.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "BIND_ACTION" | "EVALUATE":
                _require_present((("action", self.action),))
                _require_absent((("decision_id", self.decision_id),))
            case "NO_TRADE" | "REVALIDATE":
                _require_present((("decision_id", self.decision_id),))
                _require_absent((("action", self.action),))
        return self


class GovernAdmissionSuccess(WireModel):
    """Successful admission and governor operation result."""

    request_id: Uuid7
    action: ProposedAction | None = None
    decision: RiskDecision | None = None
    no_trade: NoTradeDecision | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ManageApprovalsRequest(WireModel):
    """Operation-discriminated approval and token lifecycle request.

    REQUEST_APPROVAL requires only ``approval_request``; ISSUE_TOKEN
    requires only ``approval_request_id``; CONSUME_TOKEN and REVOKE_TOKEN
    require only ``token_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "REQUEST_APPROVAL",
        "ISSUE_TOKEN",
        "CONSUME_TOKEN",
        "REVOKE_TOKEN",
    ]
    approval_request: RiskApprovalRequest | None = None
    approval_request_id: Uuid7 | None = None
    token_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageApprovalsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "REQUEST_APPROVAL":
                _require_present((("approval_request", self.approval_request),))
                _require_absent(
                    (
                        ("approval_request_id", self.approval_request_id),
                        ("token_id", self.token_id),
                    )
                )
            case "ISSUE_TOKEN":
                _require_present((("approval_request_id", self.approval_request_id),))
                _require_absent(
                    (
                        ("approval_request", self.approval_request),
                        ("token_id", self.token_id),
                    )
                )
            case "CONSUME_TOKEN" | "REVOKE_TOKEN":
                _require_present((("token_id", self.token_id),))
                _require_absent(
                    (
                        ("approval_request", self.approval_request),
                        ("approval_request_id", self.approval_request_id),
                    )
                )
        return self


class ManageApprovalsSuccess(WireModel):
    """Successful approval and token lifecycle operation result."""

    request_id: Uuid7
    request: RiskApprovalRequest | None = None
    token: RiskApprovalToken | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class GovernAllocationsRequest(WireModel):
    """Operation-discriminated capacity and allocation governance request.

    RESERVE requires only ``reservation``; COMMIT and RELEASE require only
    ``reservation_id``; REVIEW_ALLOCATION requires only ``review``;
    AUTHORIZE_BUDGET requires only ``review_id``; VALIDATE_BUDGET requires
    only ``budget_decision_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "RESERVE",
        "COMMIT",
        "RELEASE",
        "REVIEW_ALLOCATION",
        "AUTHORIZE_BUDGET",
        "VALIDATE_BUDGET",
    ]
    reservation: RiskCapacityReservation | None = None
    reservation_id: Uuid7 | None = None
    review: PortfolioAllocationReview | None = None
    review_id: Uuid7 | None = None
    budget_decision_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> GovernAllocationsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "RESERVE":
                _require_present((("reservation", self.reservation),))
                _require_absent(self._other_fields())
            case "COMMIT" | "RELEASE":
                _require_present((("reservation_id", self.reservation_id),))
                _require_absent(self._other_fields())
            case "REVIEW_ALLOCATION":
                _require_present((("review", self.review),))
                _require_absent(self._other_fields())
            case "AUTHORIZE_BUDGET":
                _require_present((("review_id", self.review_id),))
                _require_absent(self._other_fields())
            case "VALIDATE_BUDGET":
                _require_present((("budget_decision_id", self.budget_decision_id),))
                _require_absent(self._other_fields())
        return self

    def _other_fields(self) -> tuple[tuple[str, object], ...]:
        """Return every operation field not selected by ``operation``.

        Returns:
            ``(field name, value)`` pairs for all optional payload fields
            that the current operation must leave unset.
        """
        fields: dict[str, object] = {
            "reservation": self.reservation,
            "reservation_id": self.reservation_id,
            "review": self.review,
            "review_id": self.review_id,
            "budget_decision_id": self.budget_decision_id,
        }
        selected = {
            "RESERVE": "reservation",
            "COMMIT": "reservation_id",
            "RELEASE": "reservation_id",
            "REVIEW_ALLOCATION": "review",
            "AUTHORIZE_BUDGET": "review_id",
            "VALIDATE_BUDGET": "budget_decision_id",
        }[self.operation]
        return tuple(
            (name, value) for name, value in fields.items() if name != selected
        )


class GovernAllocationsSuccess(WireModel):
    """Successful capacity and allocation governance operation result."""

    request_id: Uuid7
    reservation: RiskCapacityReservation | None = None
    review: PortfolioAllocationReview | None = None
    budget: AllocationBudget | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AuditRiskDecisionsRequest(WireModel):
    """Operation-discriminated audit-chain request.

    APPEND requires only ``record``; VERIFY_CHAIN and EXPORT forbid it.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["APPEND", "VERIFY_CHAIN", "EXPORT"]
    record: RiskAuditRecord | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> AuditRiskDecisionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: APPEND omits ``record`` or a read-only operation
                sets it.
        """
        match self.operation:
            case "APPEND":
                _require_present((("record", self.record),))
            case "VERIFY_CHAIN" | "EXPORT":
                _require_absent((("record", self.record),))
        return self


class AuditRiskDecisionsSuccess(WireModel):
    """Successful audit-chain operation result."""

    request_id: Uuid7
    record: RiskAuditRecord | None = None
    chain_valid: bool | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# The PEP 695 ``type`` aliases are not classes and cannot be registered in
# WIRE_MODELS. OrderedCheck and ScenarioShock are the nested records spelled
# inside the ratified public-records table (RiskDecision.ordered_checks and
# RiskScenarioRequest.shocks), so they are registered alongside their owner
# rows exactly like the Broker nested-record precedent.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "RiskDecisionState": RiskDecisionState,
    "RiskProfileRef": RiskProfileRef,
    "RiskProfileVersion": RiskProfileVersion,
    "FirmMandateVersion": FirmMandateVersion,
    "RiskEvidenceRef": RiskEvidenceRef,
    "RiskSnapshot": RiskSnapshot,
    "PositionSizeRecommendation": PositionSizeRecommendation,
    "StopLossAssessment": StopLossAssessment,
    "ProposedAction": ProposedAction,
    "RiskDecision": RiskDecision,
    "OrderedCheck": OrderedCheck,
    "NoTradeDecision": NoTradeDecision,
    "RiskLimitResult": RiskLimitResult,
    "RiskApprovalRequest": RiskApprovalRequest,
    "RiskApprovalToken": RiskApprovalToken,
    "RiskCapacityReservation": RiskCapacityReservation,
    "KillSwitchScope": KillSwitchScope,
    "KillSwitchState": KillSwitchState,
    "KillSwitchTransition": KillSwitchTransition,
    "StrategyEligibilityDecision": StrategyEligibilityDecision,
    "PortfolioAllocationReview": PortfolioAllocationReview,
    "AllocationBudget": AllocationBudget,
    "RiskScenarioRequest": RiskScenarioRequest,
    "ScenarioShock": ScenarioShock,
    "RiskScenarioResult": RiskScenarioResult,
    "RiskAuditRecord": RiskAuditRecord,
    "DefineRiskContractsRequest": DefineRiskContractsRequest,
    "DefineRiskContractsSuccess": DefineRiskContractsSuccess,
    "CalculateRiskRequest": CalculateRiskRequest,
    "CalculateRiskSuccess": CalculateRiskSuccess,
    "ControlKillSwitchRequest": ControlKillSwitchRequest,
    "ControlKillSwitchSuccess": ControlKillSwitchSuccess,
    "GovernAdmissionRequest": GovernAdmissionRequest,
    "GovernAdmissionSuccess": GovernAdmissionSuccess,
    "ManageApprovalsRequest": ManageApprovalsRequest,
    "ManageApprovalsSuccess": ManageApprovalsSuccess,
    "GovernAllocationsRequest": GovernAllocationsRequest,
    "GovernAllocationsSuccess": GovernAllocationsSuccess,
    "AuditRiskDecisionsRequest": AuditRiskDecisionsRequest,
    "AuditRiskDecisionsSuccess": AuditRiskDecisionsSuccess,
}
