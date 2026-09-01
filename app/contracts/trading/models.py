"""Strict Pydantic v2 wire records for the ratified Trading v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# Cross-namespace reference records and the Data-owned interval are
# annotation-only for readers, but Pydantic resolves them at class-creation
# time, so they must remain runtime imports. The TradingMode,
# TradingOperationState, and TradingSessionState literal unions from
# common Shared Contracts §4.3 are imported under ``*Value`` aliases because
# the record classes R1, R7, and R4 own the primary names below.
from app.contracts.analytics.models import FilterSpec  # noqa: TC001
from app.contracts.catalogue.models import InstrumentRef  # noqa: TC001
from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    CurrencyCode,
    DecimalValue,
    JsonObject,
    Money,
    OrderState,
    OrderType,
    Rounding,
    Side,
    TimeInForce,
    TradingModeValue,
    TradingOperationStateValue,
    TradingSessionStateValue,
    UtcTimestamp,
    Uuid7,
    WireModel,
)
from app.contracts.data.models import SeriesInterval  # noqa: TC001

# Constrained local string alias reused across trading records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Closed journal event-kind union shared by TradingJournalRecord.event_kind
# (record R21) and the trading.event payload kind (record R28).
type TradingEventKind = Literal[
    "PLAN",
    "VALIDATION",
    "RISK_CHECK",
    "RESERVATION",
    "DISPATCH",
    "RECEIPT",
    "ORDER_CHANGE",
    "DEAL",
    "POSITION_CHANGE",
    "RECONCILIATION",
    "PROTECTION",
    "RETRY",
    "CLOSURE",
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


class TradingMode(WireModel):
    """Explicit per-session trading-mode declaration (record R1).

    There is no live default and no implicit promotion; a missing or
    mismatched mode blocks session start and dispatch.
    """

    mode: TradingModeValue
    schema_version: Literal[1] = 1


class TradingSessionRef(WireModel):
    """Reference to one durable trading session and its explicit mode."""

    session_id: Uuid7
    mode: TradingModeValue
    schema_version: Literal[1] = 1


class TradingSession(WireModel):
    """One durable trading session binding (record R3).

    Bindings are immutable while active; changes create a new session
    version. Uniqueness ``(session_id, generation)`` is enforced by the
    owning store because it spans multiple session records.
    """

    session_id: Uuid7
    mode: TradingModeValue
    account_authority_ref: NonEmptyStr
    route_profile_version: int = Field(ge=1)
    capability_snapshot_id: Uuid7
    risk_profile_id: Uuid7
    # Paper sessions may bind an opening state and data binding; broker
    # sessions leave this null.
    opening_state: JsonObject | None = None
    created_at: UtcTimestamp
    started_at: UtcTimestamp | None = None
    stopped_at: UtcTimestamp | None = None
    archived_at: UtcTimestamp | None = None
    generation: int = Field(ge=1)
    schema_version: Literal[1] = 1


class TradingSessionState(WireModel):
    """One recorded lifecycle-state transition of a session generation.

    Illegal transitions have no side effect; recovery fences old
    generations and reconciles before ``ACTIVE``; unresolved drift stays
    ``DEGRADED``.
    """

    session_id: Uuid7
    state: TradingSessionStateValue
    generation: int = Field(ge=1)
    changed_at: UtcTimestamp
    causal_event_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


class TradingOperationRef(WireModel):
    """Reference to one logical idempotent trading mutation.

    Dispatch occurs at most once per logical identity
    ``(idempotency_scope, idempotency_key)``.
    """

    operation_id: Uuid7
    session_id: Uuid7
    idempotency_scope: NonEmptyStr
    idempotency_key: NonEmptyStr
    schema_version: Literal[1] = 1


class TradingOperationState(WireModel):
    """One recorded state snapshot of a logical operation (record R7).

    Unknown transport outcomes enter ``UNKNOWN`` then ``RECONCILING``; only
    reconciled authority evidence establishes fills or a final state.
    """

    operation_id: Uuid7
    state: TradingOperationStateValue
    changed_at: UtcTimestamp
    schema_version: Literal[1] = 1


class TradingOperation(WireModel):
    """One logical idempotent trading mutation (record R6).

    No operation changes session, action, or plan identity after dispatch,
    so the embedded identity fields are immutable while in flight.
    """

    operation_id: Uuid7
    session_id: Uuid7
    idempotency_scope: NonEmptyStr
    idempotency_key: NonEmptyStr
    action: Literal[
        "CREATE",
        "SUBMIT",
        "CANCEL",
        "MODIFY",
        "CLOSE",
        "FLATTEN",
        "HOLD",
        "PROTECTION",
    ]
    plan_hash: ContentHash
    risk_decision_id: Uuid7 | None
    risk_reservation_id: Uuid7 | None
    authority_route: NonEmptyStr
    state: TradingOperationStateValue
    provider_correlation_id: Uuid7 | None
    paper_correlation_id: Uuid7 | None
    event_ids: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class TradeIntentRef(WireModel):
    """Reference to one exact Strategy intent or manual order (record R8).

    Manual actions carry authenticated principal, reason, source interface,
    request/correlation IDs, and explicit discretionary identity; they
    cannot masquerade as Strategy signals.
    """

    intent_id: Uuid7
    origin: Literal["STRATEGY_INTENT", "MANUAL_ORDER"]
    strategy_version_id: Uuid7 | None
    intent_hash: ContentHash
    schema_version: Literal[1] = 1


class ProtectionSpec(WireModel):
    """One protective-order specification inside a protection set (R19).

    Inline nested record of ``ProtectionSet.protections``; not a numbered
    public record itself.
    """

    kind: Literal["STOP", "TARGET", "TRAILING", "BREAKEVEN", "PARTIAL_EXIT"]
    quantity_scope: DecimalValue
    parameters: JsonObject

    @model_validator(mode="after")
    def validate_quantity_scope(self) -> ProtectionSpec:
        """Reject nonpositive protected quantity scopes.

        Returns:
            The validated specification.

        Raises:
            ValueError: ``quantity_scope`` is zero or negative.
        """
        if Decimal(self.quantity_scope) <= 0:
            raise ValueError("quantity_scope must be positive")
        return self


class ProtectionSet(WireModel):
    """One versioned set of owned protective orders (record R19).

    Protections bind an exact entry/order/position identity and never
    attach to another strategy or manual action; protected quantity never
    exceeds live residual quantity. Uniqueness
    ``(owner_identity, version)`` spans records and is store-enforced.
    """

    owner_identity: NonEmptyStr
    version: int = Field(ge=1)
    owner_kind: Literal["STRATEGY", "MANUAL", "ATM"]
    protections: tuple[ProtectionSpec, ...] = ()
    plan_version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class TradePlan(WireModel):
    """One validated immutable trade plan (record R9).

    Ambiguous or mutable inputs reject before Risk review; the plan hash
    pins the exact normalized content.
    """

    plan_id: Uuid7
    intent: TradeIntentRef
    instrument: InstrumentRef
    side: Side
    order_type: OrderType
    quantity_method: JsonObject
    entry: JsonObject
    protection: ProtectionSet | None
    time_in_force: TimeInForce
    route: NonEmptyStr
    session_id: Uuid7
    evidence_version_ids: tuple[Uuid7, ...] = ()
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ExecutionAuthorityRef(WireModel):
    """Reference to the selected paper or broker authority (record R11).

    Cross-authority and cross-environment dispatch is structurally
    impossible: a paper authority carries only the registered
    paper-execution capability, and a demo/live authority carries only the
    exact Broker session environment.
    """

    authority_id: Uuid7
    kind: TradingModeValue
    paper_capability: CapabilityIdentifier | None
    broker_session_id: Uuid7 | None
    generation: int = Field(ge=1)
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_authority_isolation(self) -> ExecutionAuthorityRef:
        """Reject mixed or missing authority references.

        Returns:
            The validated authority reference.

        Raises:
            ValueError: The declared kind contradicts which authority
                reference is present.
        """
        if self.kind == "PAPER":
            _require_present((("paper_capability", self.paper_capability),))
            _require_absent((("broker_session_id", self.broker_session_id),))
        else:
            _require_present((("broker_session_id", self.broker_session_id),))
            _require_absent((("paper_capability", self.paper_capability),))
        return self


class TradingReadiness(WireModel):
    """Point-in-time preflight readiness assessment (record R10).

    Any mandatory unknown state blocks a new mutation by appearing in
    ``blocking_reasons``.
    """

    session: TradingSessionRef
    is_session_active: bool
    selected_authority: ExecutionAuthorityRef | None
    authority_capability_ready: bool
    instrument_mapping_valid: bool
    market_session_state: Literal["OPEN", "CLOSED", "UNKNOWN"]
    evidence_fresh: bool
    route_profile_compatible: bool
    account_permission_granted: bool
    risk_admissible: bool
    assessed_at: UtcTimestamp
    blocking_reasons: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class DispatchEvidence(WireModel):
    """Staged pre-dispatch evidence with an immutable request hash (R12).

    The staged record and request hash commit before any external or paper
    side effect; staging failure causes no dispatch.
    """

    evidence_id: Uuid7
    operation_id: Uuid7
    request_hash: ContentHash
    staged_at: UtcTimestamp
    authority_generation: int = Field(ge=1)
    recheck_passed: Literal[True]
    schema_version: Literal[1] = 1


class DispatchReceipt(WireModel):
    """Classified dispatch receipt from the authority (record R13).

    Concurrent or repeated requests never create a duplicate logical
    order; blind retry stays disabled on ``UNKNOWN`` until reconciliation
    proves no authority operation or a new separately authorized action
    exists.
    """

    receipt_id: Uuid7
    operation_id: Uuid7
    outcome: Literal["ACCEPTED", "REJECTED", "UNKNOWN"]
    authority_request_id: NonEmptyStr | None
    authority_receipt_id: NonEmptyStr | None
    provider_evidence: JsonObject
    received_at: UtcTimestamp
    schema_version: Literal[1] = 1


class TradingOrder(WireModel):
    """One canonical operational order (record R14).

    Only reconciled authority evidence establishes the state; uniqueness
    ``(session_id, authority_order_id)`` spans records and is
    store-enforced.
    """

    order_id: Uuid7
    session_id: Uuid7
    operation_id: Uuid7
    authority_order_id: NonEmptyStr
    instrument: InstrumentRef
    side: Side
    order_type: OrderType
    requested_quantity: DecimalValue
    filled_quantity: DecimalValue = "0"
    state: OrderState
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_quantities(self) -> TradingOrder:
        """Reject nonpositive requests and negative filled quantities.

        Returns:
            The validated order.

        Raises:
            ValueError: A quantity violates its ratified bound.
        """
        if Decimal(self.requested_quantity) <= 0:
            raise ValueError("requested_quantity must be positive")
        if Decimal(self.filled_quantity) < 0:
            raise ValueError("filled_quantity must be >= 0")
        return self


class TradingDeal(WireModel):
    """One authority execution deal (record R15).

    Deals are the authority for executed quantity and realized state;
    uniqueness ``(session_id, authority_deal_id)`` spans records and is
    store-enforced.
    """

    deal_id: Uuid7
    session_id: Uuid7
    order_id: Uuid7
    authority_deal_id: NonEmptyStr
    timestamp: UtcTimestamp
    side: Side
    quantity: DecimalValue
    price: DecimalValue
    fee: Money | None
    financing: Money | None
    realized_pl: Money | None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_quantity(self) -> TradingDeal:
        """Reject nonpositive executed quantities.

        Returns:
            The validated deal.

        Raises:
            ValueError: ``quantity`` is zero or negative.
        """
        if Decimal(self.quantity) <= 0:
            raise ValueError("quantity must be positive")
        return self


class TradingPositionProjection(WireModel):
    """One canonical operational position projection (record R16).

    Snapshots are current-state evidence, never a replacement for
    transaction history; disagreements remain explicit until reconciled.
    """

    position_id: Uuid7
    session_id: Uuid7
    position_identity: NonEmptyStr
    instrument: InstrumentRef
    direction: Literal["LONG", "SHORT"]
    quantity: DecimalValue
    avg_price: DecimalValue | None
    realized_pl: Money
    unrealized_pl: Money | None
    as_of: UtcTimestamp
    authority_source: Literal["DEAL_DERIVED", "SNAPSHOT"]
    schema_version: Literal[1] = 1


class ReconciliationRequest(WireModel):
    """One bounded reconciliation run request (record R17).

    Compares local operations and projections with bounded authority
    state; missing pages or event gaps block clean completion.
    ``SeriesInterval`` is Data-owned and imported per the cross-namespace
    owner-type rule.
    """

    request_id: Uuid7
    session_id: Uuid7
    time_window: SeriesInterval
    event_cursor: str | None
    scope: Literal[
        "ORDERS",
        "DEALS",
        "POSITIONS",
        "ACCOUNT",
        "EVENTS",
        "ALL",
    ] = "ALL"
    schema_version: Literal[1] = 1


class ReconciliationFinding(WireModel):
    """One typed reconciliation finding (record R18).

    Destructive repair requires explicit authorization; the transition
    history is append-only.
    """

    finding_id: Uuid7
    run_id: Uuid7
    finding_key: NonEmptyStr
    kind: Literal[
        "MISSING_ORDER",
        "MISSING_DEAL",
        "MISSING_POSITION",
        "QUANTITY_MISMATCH",
        "PRICE_MISMATCH",
        "STATE_MISMATCH",
        "EVENT_GAP",
        "PAGE_MISSING",
        "DUPLICATE",
        "CORPORATE_ACTION_UNMATCHED",
        "PROTECTION_MISSING",
        "PROTECTION_ORPHANED",
        "PROTECTION_STALE",
        "PROTECTION_DUPLICATED",
    ]
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    evidence_refs: tuple[Uuid7, ...] = ()
    resolution_policy: Literal["AUTO", "MANUAL"]
    transition_history: tuple[JsonObject, ...] = ()
    schema_version: Literal[1] = 1


class ProtectionChange(WireModel):
    """One risk-validated protection lifecycle change (record R20).

    Risk-worsening changes block unless an explicit exception authorizes
    them.
    """

    change_id: Uuid7
    protection_set: ProtectionSet
    change: Literal["INSTALL", "MODIFY", "CANCEL"]
    risk_validation_id: Uuid7
    authority_rules_applied: JsonObject
    is_risk_worsening: bool
    explicit_exception_id: Uuid7 | None = None
    changed_at: UtcTimestamp
    schema_version: Literal[1] = 1


class TradingJournalRecord(WireModel):
    """One immutable append-only journal record (record R21).

    First-divergence causal reconstruction requires no free-text log
    parsing; secrets never appear in redacted failure details.
    """

    record_id: Uuid7
    session_id: Uuid7
    sequence: int = Field(ge=1)
    record_hash: ContentHash
    event_kind: TradingEventKind
    contract_versions: JsonObject
    request_hash: ContentHash | None
    response_hash: ContentHash | None
    evidence_refs: tuple[Uuid7, ...] = ()
    authority_generation: int = Field(ge=1)
    operator_or_strategy_identity: NonEmptyStr
    occurred_at: UtcTimestamp
    failure_detail_redacted: str = ""
    schema_version: Literal[1] = 1


class ExecutionProvenance(WireModel):
    """Bounded verifiable export provenance pin (record R22).

    The export reproduces record hashes without credentials or
    unrestricted provider payloads.
    """

    provenance_id: Uuid7
    journal_record_id: Uuid7
    profile_versions: JsonObject
    evidence_refs: tuple[Uuid7, ...] = ()
    export_bounds: JsonObject
    schema_version: Literal[1] = 1


class OperationalAccount(WireModel):
    """One operational account projection (record R23).

    Projected from reconciled deals and events only; projection totals
    reconcile to the ledger plus explicit provider differences.
    """

    account_id: Uuid7
    session_id: Uuid7
    account_ref: NonEmptyStr
    currency: CurrencyCode
    cash: Money
    balances: dict[CurrencyCode, DecimalValue] = Field(default_factory=dict)
    open_positions: tuple[Uuid7, ...] = ()
    pending_obligations: JsonObject = Field(default_factory=dict)
    realized_pl: Money
    unrealized_pl: Money | None
    fees: Money
    financing: Money
    equity: Money | None
    margin: Money | None
    free_margin: Money | None
    buying_power: Money | None
    risk_health_at: UtcTimestamp | None
    as_of: UtcTimestamp
    schema_version: Literal[1] = 1


class OperationalLedgerEntry(WireModel):
    """One signed balanced operational ledger entry (record R24).

    Every journalized transaction balances; direct edit or delete of
    history is prohibited, and adjustments append evidence-linked balanced
    entries with reversal lineage.
    """

    entry_id: Uuid7
    account_id: Uuid7
    sequence: int = Field(ge=1)
    record_hash: ContentHash
    entry_kind: Literal[
        "CASH",
        "ASSET_POSITION",
        "FEE",
        "FINANCING_SWAP",
        "REALIZED_PL",
        "ADJUSTMENT",
    ]
    debit: DecimalValue
    credit: DecimalValue
    currency: CurrencyCode
    source_deal_id: Uuid7 | None
    source_event_id: Uuid7 | None
    effective_at: UtcTimestamp
    recorded_at: UtcTimestamp
    posted_at: UtcTimestamp
    reversal_of: Uuid7 | None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_amounts(self) -> OperationalLedgerEntry:
        """Reject negative debit or credit amounts.

        Returns:
            The validated ledger entry.

        Raises:
            ValueError: ``debit`` or ``credit`` is negative.
        """
        if Decimal(self.debit) < 0:
            raise ValueError("debit must be >= 0")
        if Decimal(self.credit) < 0:
            raise ValueError("credit must be >= 0")
        return self


class OperationalValuation(WireModel):
    """One point-in-time operational valuation (record R25).

    No value, P/L, margin, or buying power is derived from a stale or
    missing mandatory mark.
    """

    valuation_id: Uuid7
    account_id: Uuid7
    as_of: UtcTimestamp
    valuation_version: int = Field(ge=1)
    mark_source: NonEmptyStr
    mark_time: UtcTimestamp
    fx_graph_version: NonEmptyStr
    contract_sizes: JsonObject
    currencies: tuple[CurrencyCode, ...] = ()
    rounding: Rounding
    missing_price_policy: NonEmptyStr
    values: JsonObject
    stale_mandatory_marks: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class PublicTradingAction(WireModel):
    """One versioned mode-neutral public action (record R26).

    One delegated contract reaches the exact session owner; no caller
    selects a private adapter, and scope cannot broaden between preview
    and commit.
    """

    schema_id: NonEmptyStr = "trading.public_action.v1"
    action_id: Uuid7
    action: Literal[
        "CREATE",
        "SUBMIT",
        "CANCEL",
        "MODIFY",
        "CLOSE",
        "FLATTEN",
        "HOLD",
        "PROTECTION",
    ]
    contract_version: Literal[1] = 1
    session: TradingSessionRef
    payload: JsonObject
    pinned_selection_token_id: Uuid7 | None = None
    impact_preview_id: Uuid7 | None = None
    conflict_policy: Literal["REJECT", "KEEP_EXISTING", "CREATE_NEW_VERSION"] | None = (
        None
    )
    approval_token_id: Uuid7 | None = None
    idempotency_key: NonEmptyStr
    per_target_outcomes: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_bulk_governance(self) -> PublicTradingAction:
        """Reject bulk actions without full governance evidence.

        A bulk or emergency action is identified by its pinned selection
        token and requires the impact preview, explicit conflict policy,
        and authenticated approval of FR-TRD-GOVERN_BULK_ACTIONS.

        Returns:
            The validated action.

        Raises:
            ValueError: A pinned bulk selection lacks the impact preview,
                conflict policy, or approval token.
        """
        if self.pinned_selection_token_id is not None:
            _require_present(
                (
                    ("impact_preview_id", self.impact_preview_id),
                    ("conflict_policy", self.conflict_policy),
                    ("approval_token_id", self.approval_token_id),
                )
            )
        return self


class TradingStateQuery(WireModel):
    """One bounded trading-state projection query (record R27).

    Bounded projections carry authority and freshness state; stale or
    unresolved projections are visibly marked and never presented as live
    authority.
    """

    query_id: Uuid7
    session_id: Uuid7 | None
    projection: Literal[
        "SESSIONS",
        "OPERATIONS",
        "ORDERS",
        "DEALS",
        "POSITIONS",
        "PROTECTIONS",
        "ACCOUNTS",
        "LEDGER",
        "RECONCILIATION",
    ]
    cursor: str | None
    page_size: int = Field(default=100, ge=1, le=500)
    filters: tuple[FilterSpec, ...] = ()
    schema_version: Literal[1] = 1


class ManageTradingSessionsRequest(WireModel):
    """Operation-discriminated trading session request.

    CREATE requires only ``session``; START, STOP, ARCHIVE, and RECOVER
    require only ``session_ref``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["CREATE", "START", "STOP", "ARCHIVE", "RECOVER"]
    session: TradingSession | None = None
    session_ref: TradingSessionRef | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageTradingSessionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "CREATE":
                _require_present((("session", self.session),))
                _require_absent((("session_ref", self.session_ref),))
            case "START" | "STOP" | "ARCHIVE" | "RECOVER":
                _require_present((("session_ref", self.session_ref),))
                _require_absent((("session", self.session),))
        return self


class ManageTradingSessionsSuccess(WireModel):
    """Successful trading session operation result."""

    request_id: Uuid7
    session: TradingSession | None = None
    state: TradingSessionState | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ValidateTradePlansRequest(WireModel):
    """Operation-discriminated plan validation request.

    BIND_INTENT requires only ``intent``; BIND_PLAN and NORMALIZE require
    only ``plan``; VALIDATE_READINESS requires only ``session``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["BIND_INTENT", "BIND_PLAN", "VALIDATE_READINESS", "NORMALIZE"]
    intent: TradeIntentRef | None = None
    plan: TradePlan | None = None
    session: TradingSessionRef | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ValidateTradePlansRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "BIND_INTENT":
                _require_present((("intent", self.intent),))
                _require_absent(
                    (
                        ("plan", self.plan),
                        ("session", self.session),
                    )
                )
            case "BIND_PLAN" | "NORMALIZE":
                _require_present((("plan", self.plan),))
                _require_absent(
                    (
                        ("intent", self.intent),
                        ("session", self.session),
                    )
                )
            case "VALIDATE_READINESS":
                _require_present((("session", self.session),))
                _require_absent(
                    (
                        ("intent", self.intent),
                        ("plan", self.plan),
                    )
                )
        return self


class ValidateTradePlansSuccess(WireModel):
    """Successful plan validation operation result."""

    request_id: Uuid7
    intent: TradeIntentRef | None = None
    plan: TradePlan | None = None
    readiness: TradingReadiness | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class AccountOperationsRequest(WireModel):
    """Operation-discriminated operational account request.

    PROJECT_ACCOUNT requires only ``session``; VALUE requires only
    ``account_id``; POST_ADJUSTMENT requires only ``ledger_entry``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["PROJECT_ACCOUNT", "VALUE", "POST_ADJUSTMENT"]
    session: TradingSessionRef | None = None
    account_id: Uuid7 | None = None
    ledger_entry: OperationalLedgerEntry | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> AccountOperationsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "PROJECT_ACCOUNT":
                _require_present((("session", self.session),))
                _require_absent(
                    (
                        ("account_id", self.account_id),
                        ("ledger_entry", self.ledger_entry),
                    )
                )
            case "VALUE":
                _require_present((("account_id", self.account_id),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("ledger_entry", self.ledger_entry),
                    )
                )
            case "POST_ADJUSTMENT":
                _require_present((("ledger_entry", self.ledger_entry),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("account_id", self.account_id),
                    )
                )
        return self


class AccountOperationsSuccess(WireModel):
    """Successful operational account operation result."""

    request_id: Uuid7
    account: OperationalAccount | None = None
    valuation: OperationalValuation | None = None
    ledger_entry: OperationalLedgerEntry | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class DispatchOrdersRequest(WireModel):
    """Operation-discriminated authority dispatch request.

    OBTAIN_AUTHORITY requires only ``session``; RECHECK and DISPATCH
    require only ``evidence``; STAGE_EVIDENCE requires only
    ``trading_operation``; CLASSIFY_RECEIPT requires only ``receipt``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "OBTAIN_AUTHORITY",
        "RECHECK",
        "STAGE_EVIDENCE",
        "DISPATCH",
        "CLASSIFY_RECEIPT",
    ]
    session: TradingSessionRef | None = None
    trading_operation: TradingOperation | None = None
    evidence: DispatchEvidence | None = None
    receipt: DispatchReceipt | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> DispatchOrdersRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "OBTAIN_AUTHORITY":
                _require_present((("session", self.session),))
                _require_absent(
                    (
                        ("trading_operation", self.trading_operation),
                        ("evidence", self.evidence),
                        ("receipt", self.receipt),
                    )
                )
            case "RECHECK" | "DISPATCH":
                _require_present((("evidence", self.evidence),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("trading_operation", self.trading_operation),
                        ("receipt", self.receipt),
                    )
                )
            case "STAGE_EVIDENCE":
                _require_present((("trading_operation", self.trading_operation),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("evidence", self.evidence),
                        ("receipt", self.receipt),
                    )
                )
            case "CLASSIFY_RECEIPT":
                _require_present((("receipt", self.receipt),))
                _require_absent(
                    (
                        ("session", self.session),
                        ("trading_operation", self.trading_operation),
                        ("evidence", self.evidence),
                    )
                )
        return self


class DispatchOrdersSuccess(WireModel):
    """Successful authority dispatch operation result."""

    request_id: Uuid7
    authority: ExecutionAuthorityRef | None = None
    evidence: DispatchEvidence | None = None
    receipt: DispatchReceipt | None = None
    operation: TradingOperation | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ReconcileTradingRequest(WireModel):
    """Operation-discriminated reconciliation request.

    REQUEST_RUN and EXECUTE require only ``reconciliation``;
    RESOLVE_FINDING requires only ``finding``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["REQUEST_RUN", "EXECUTE", "RESOLVE_FINDING"]
    reconciliation: ReconciliationRequest | None = None
    finding: ReconciliationFinding | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ReconcileTradingRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "REQUEST_RUN" | "EXECUTE":
                _require_present((("reconciliation", self.reconciliation),))
                _require_absent((("finding", self.finding),))
            case "RESOLVE_FINDING":
                _require_present((("finding", self.finding),))
                _require_absent((("reconciliation", self.reconciliation),))
        return self


class ReconcileTradingSuccess(WireModel):
    """Successful reconciliation operation result."""

    request_id: Uuid7
    request: ReconciliationRequest | None = None
    findings: tuple[ReconciliationFinding, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ManageProtectionsRequest(WireModel):
    """Operation-discriminated protection management request.

    INSTALL, MODIFY, CANCEL, and RECOVER all operate on one
    ``protection_set`` bound to its exact owner identity.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["INSTALL", "MODIFY", "CANCEL", "RECOVER"]
    protection_set: ProtectionSet
    schema_version: Literal[1] = 1


class ManageProtectionsSuccess(WireModel):
    """Successful protection management operation result."""

    request_id: Uuid7
    protection_set: ProtectionSet | None = None
    change: ProtectionChange | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class JournalExecutionRequest(WireModel):
    """Operation-discriminated execution journal request.

    APPEND requires only ``record``; EXPORT requires only
    ``journal_record_id``; BALANCE_LEDGER requires only ``ledger_entry``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["APPEND", "EXPORT", "BALANCE_LEDGER"]
    record: TradingJournalRecord | None = None
    journal_record_id: Uuid7 | None = None
    ledger_entry: OperationalLedgerEntry | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> JournalExecutionRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "APPEND":
                _require_present((("record", self.record),))
                _require_absent(
                    (
                        ("journal_record_id", self.journal_record_id),
                        ("ledger_entry", self.ledger_entry),
                    )
                )
            case "EXPORT":
                _require_present((("journal_record_id", self.journal_record_id),))
                _require_absent(
                    (
                        ("record", self.record),
                        ("ledger_entry", self.ledger_entry),
                    )
                )
            case "BALANCE_LEDGER":
                _require_present((("ledger_entry", self.ledger_entry),))
                _require_absent(
                    (
                        ("record", self.record),
                        ("journal_record_id", self.journal_record_id),
                    )
                )
        return self


class JournalExecutionSuccess(WireModel):
    """Successful execution journal operation result."""

    request_id: Uuid7
    record: TradingJournalRecord | None = None
    provenance: ExecutionProvenance | None = None
    ledger_entry: OperationalLedgerEntry | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ExecutePublicActionsRequest(WireModel):
    """Operation-discriminated public action request.

    ROUTE_ACTION and GOVERN_BULK require only ``action``; QUERY_STATE
    requires only ``query``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["ROUTE_ACTION", "GOVERN_BULK", "QUERY_STATE"]
    action: PublicTradingAction | None = None
    query: TradingStateQuery | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ExecutePublicActionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "ROUTE_ACTION" | "GOVERN_BULK":
                _require_present((("action", self.action),))
                _require_absent((("query", self.query),))
            case "QUERY_STATE":
                _require_present((("query", self.query),))
                _require_absent((("action", self.action),))
        return self


class ExecutePublicActionsSuccess(WireModel):
    """Successful public action operation result.

    ``rows`` are bounded ``ResultPage``-style ``JsonObject`` tuples
    referencing owner records; they are not a copy of any owner record.
    """

    request_id: Uuid7
    action: PublicTradingAction | None = None
    query: TradingStateQuery | None = None
    rows: tuple[JsonObject, ...] = ()
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# TradingModeValue, TradingSessionStateValue, and TradingOperationStateValue
# are PEP 695 ``type`` aliases, and the payload record R28 (TradingEvent)
# is registered in WIRE_EVENTS; ProtectionSpec and FilterSpec are inline
# nested records spelled inside table rows rather than numbered public
# records, so none of them is registered in WIRE_MODELS.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "TradingMode": TradingMode,
    "TradingSessionRef": TradingSessionRef,
    "TradingSession": TradingSession,
    "TradingSessionState": TradingSessionState,
    "TradingOperationRef": TradingOperationRef,
    "TradingOperation": TradingOperation,
    "TradingOperationState": TradingOperationState,
    "TradeIntentRef": TradeIntentRef,
    "TradePlan": TradePlan,
    "TradingReadiness": TradingReadiness,
    "ExecutionAuthorityRef": ExecutionAuthorityRef,
    "DispatchEvidence": DispatchEvidence,
    "DispatchReceipt": DispatchReceipt,
    "TradingOrder": TradingOrder,
    "TradingDeal": TradingDeal,
    "TradingPositionProjection": TradingPositionProjection,
    "ReconciliationRequest": ReconciliationRequest,
    "ReconciliationFinding": ReconciliationFinding,
    "ProtectionSet": ProtectionSet,
    "ProtectionChange": ProtectionChange,
    "TradingJournalRecord": TradingJournalRecord,
    "ExecutionProvenance": ExecutionProvenance,
    "OperationalAccount": OperationalAccount,
    "OperationalLedgerEntry": OperationalLedgerEntry,
    "OperationalValuation": OperationalValuation,
    "PublicTradingAction": PublicTradingAction,
    "TradingStateQuery": TradingStateQuery,
    "ManageTradingSessionsRequest": ManageTradingSessionsRequest,
    "ManageTradingSessionsSuccess": ManageTradingSessionsSuccess,
    "ValidateTradePlansRequest": ValidateTradePlansRequest,
    "ValidateTradePlansSuccess": ValidateTradePlansSuccess,
    "AccountOperationsRequest": AccountOperationsRequest,
    "AccountOperationsSuccess": AccountOperationsSuccess,
    "DispatchOrdersRequest": DispatchOrdersRequest,
    "DispatchOrdersSuccess": DispatchOrdersSuccess,
    "ReconcileTradingRequest": ReconcileTradingRequest,
    "ReconcileTradingSuccess": ReconcileTradingSuccess,
    "ManageProtectionsRequest": ManageProtectionsRequest,
    "ManageProtectionsSuccess": ManageProtectionsSuccess,
    "JournalExecutionRequest": JournalExecutionRequest,
    "JournalExecutionSuccess": JournalExecutionSuccess,
    "ExecutePublicActionsRequest": ExecutePublicActionsRequest,
    "ExecutePublicActionsSuccess": ExecutePublicActionsSuccess,
}
