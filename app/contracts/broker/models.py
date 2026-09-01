"""Strict Pydantic v2 wire records for the ratified Broker v1 contracts."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

# These reference types are annotation-only for readers but Pydantic resolves
# them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import (  # noqa: TC001
    InstrumentRef,
    ProviderRef,
)
from app.contracts.common.models import (
    ContentHash,
    CurrencyCode,
    DecimalValue,
    JsonObject,
    Money,
    ProblemDetails,
    UtcTimestamp,
    Uuid7,
    WireModel,
)

# Constrained local string alias reused across broker records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# Closed enum literals local to the Broker records.
type BrokerProviderKind = Literal[
    "MT5",
    "CTRADER",
    "BINANCE_SPOT",
    "BINANCE_USD_M",
    "BINANCE_COIN_M",
    "DUKASCOPY",
    "YAHOO",
]
# Domain assumption: a broker environment names the provider-side execution
# boundary, not a trading mode. It deliberately differs from TradingMode
# (PAPER/DEMO/LIVE) because TESTNET, SANDBOX, and SIMULATION identify
# distinct provider boundaries that a trading mode cannot express.
type BrokerEnvironmentKind = Literal[
    "LIVE",
    "DEMO",
    "TESTNET",
    "SANDBOX",
    "SIMULATION",
]
type BrokerConnectionState = Literal[
    "DISCONNECTED",
    "CONNECTING",
    "READY",
    "DEGRADED",
    "CLOSING",
    "FAILED",
]
type ReadinessState = Literal["NOT_READY", "READY"]
type MarketStatus = Literal["OPEN", "CLOSED", "UNKNOWN"]
type BrokerOperationKind = Literal["SUBMIT_ORDER", "CANCEL_ORDER", "MODIFY_ORDER"]
type TransportOutcome = Literal["ACCEPTED", "REJECTED", "UNKNOWN"]

# Wire bound for paged provider history; the package-level
# ``broker_page_limit`` default is 1,000 and profiles may only narrow it.
_PAGE_LIMIT_MAX = 1_000


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


class BrokerProviderProfile(WireModel):
    """One immutable broker provider profile version."""

    profile_id: Uuid7
    version: int = Field(ge=1)
    provider: ProviderRef
    kind: BrokerProviderKind
    account_ref: NonEmptyStr
    # Exactly one environment; no default to live.
    environment: BrokerEnvironmentKind
    api_version_range: NonEmptyStr
    content_hash: ContentHash
    # Workspace SecretRef identifiers; the referenced values never cross.
    credential_ref_ids: tuple[Uuid7, ...] = ()
    schema_version: Literal[1] = 1


class BrokerSessionRef(WireModel):
    """Stable environment/account/session-generation binding."""

    session_id: Uuid7
    profile_id: Uuid7
    profile_version: int = Field(ge=1)
    account_ref: NonEmptyStr
    environment: BrokerEnvironmentKind
    generation: int = Field(ge=1)
    schema_version: Literal[1] = 1


class BrokerSessionState(WireModel):
    """One recorded connection-state transition of a session generation."""

    session_id: Uuid7
    generation: int = Field(ge=1)
    connection_state: BrokerConnectionState
    transitioned_at: UtcTimestamp
    previous_state: BrokerConnectionState | None = None
    reason: str = ""
    schema_version: Literal[1] = 1


class BrokerSessionReadiness(WireModel):
    """Multi-dimensional readiness assessment of a session generation."""

    session_id: Uuid7
    generation: int = Field(ge=1)
    transport: ReadinessState
    authentication: ReadinessState
    account_authorization: ReadinessState
    trading_permission: ReadinessState
    subscriptions: ReadinessState
    environment_verified: bool
    resynchronized: bool
    assessed_at: UtcTimestamp
    schema_version: Literal[1] = 1


class BrokerAccountSnapshot(WireModel):
    """Provider-truth account and balance projection."""

    session_id: Uuid7
    generation: int = Field(ge=1)
    account_ref: NonEmptyStr
    currency: CurrencyCode
    equity: Money
    retrieved_at: UtcTimestamp
    balances: dict[CurrencyCode, DecimalValue] = Field(default_factory=dict)
    margin: Money | None = None
    free_margin: Money | None = None
    permissions: tuple[NonEmptyStr, ...] = ()
    provider_time: UtcTimestamp | None = None
    schema_version: Literal[1] = 1


class ProviderRecord(WireModel):
    """One provider-native record preserved for Trading reconciliation."""

    provider_id: NonEmptyStr
    record: JsonObject


class BrokerTradingState(WireModel):
    """Provider-native positions, orders, and deals of a session generation."""

    session_id: Uuid7
    generation: int = Field(ge=1)
    retrieved_at: UtcTimestamp
    positions: tuple[ProviderRecord, ...] = ()
    orders: tuple[ProviderRecord, ...] = ()
    deals: tuple[ProviderRecord, ...] = ()
    duplicate_or_contradictory: tuple[NonEmptyStr, ...] = ()
    schema_version: Literal[1] = 1


class BrokerMarketState(WireModel):
    """Provider-truth quote, tick, and market-status projection."""

    session_id: Uuid7
    generation: int = Field(ge=1)
    instrument: InstrumentRef
    provider_symbol: NonEmptyStr
    market_status: MarketStatus
    receipt_time: UtcTimestamp
    # Nullable missing values stay explicit; only genuine values appear.
    bid: DecimalValue | None
    ask: DecimalValue | None
    last: DecimalValue | None
    provider_sequence: int | None = Field(default=None, ge=0)
    event_time: UtcTimestamp | None = None
    schema_version: Literal[1] = 1


class BrokerOperationRequest(WireModel):
    """Trading-owned transport request admitted after Risk authorization."""

    operation_id: Uuid7
    trading_operation_id: Uuid7
    session: BrokerSessionRef
    operation: BrokerOperationKind
    provider_symbol: NonEmptyStr
    normalized_quantity: DecimalValue
    # Validated against the active capability declaration before dispatch.
    policy: JsonObject
    risk_authorization_id: Uuid7
    idempotency_key: NonEmptyStr
    attempt_no: int = Field(ge=1)
    request_hash: ContentHash
    normalized_price: DecimalValue | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_quantity(self) -> BrokerOperationRequest:
        """Reject nonpositive normalized quantities.

        Returns:
            The validated transport request.

        Raises:
            ValueError: ``normalized_quantity`` is zero or negative.
        """
        if Decimal(self.normalized_quantity) <= 0:
            raise ValueError("normalized_quantity must be positive")
        return self


class BrokerOperationReceipt(WireModel):
    """Append-only provider transport outcome evidence for one attempt."""

    receipt_id: Uuid7
    operation_id: Uuid7
    attempt_no: int = Field(ge=1)
    profile_version_id: Uuid7
    environment: BrokerEnvironmentKind
    session_generation: int = Field(ge=1)
    request_hash: ContentHash
    outcome: TransportOutcome
    provider_request_id: NonEmptyStr | None = None
    provider_client_id: NonEmptyStr | None = None
    provider_order_id: NonEmptyStr | None = None
    provider_deal_id: NonEmptyStr | None = None
    provider_evidence: JsonObject = Field(default_factory=dict)
    reconciliation_keys: JsonObject = Field(default_factory=dict)
    dispatched_at: UtcTimestamp | None = None
    completed_at: UtcTimestamp | None = None
    # Monotonic wall-clock duration of the transport attempt.
    duration_ms: int = Field(default=0, ge=0)
    error: ProblemDetails | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_branch_exclusivity(self) -> BrokerOperationReceipt:
        """Reject success outcomes that also carry the error branch.

        Returns:
            The validated receipt.

        Raises:
            ValueError: An ``ACCEPTED`` receipt also sets ``error``.
        """
        if self.outcome == "ACCEPTED" and self.error is not None:
            raise ValueError("ACCEPTED outcome and error branch are mutually exclusive")
        return self


class BrokerOperationOutcome(WireModel):
    """Correlated logical result of one transport operation attempt."""

    operation_id: Uuid7
    outcome: TransportOutcome
    receipt: BrokerOperationReceipt
    last_known_transport_state: JsonObject = Field(default_factory=dict)
    is_reconciled: bool = False
    schema_version: Literal[1] = 1


class ProviderCorrelation(WireModel):
    """Stable idempotent correlation identity of a provider operation."""

    correlation_id: Uuid7
    operation_id: Uuid7
    idempotency_key: NonEmptyStr
    provider_request_id: NonEmptyStr | None = None
    provider_client_id: NonEmptyStr | None = None
    provider_order_id: NonEmptyStr | None = None
    provider_deal_id: NonEmptyStr | None = None
    schema_version: Literal[1] = 1


class BrokerHistoryPage(WireModel):
    """One bounded page of provider-native history records."""

    page_id: Uuid7
    requested_count: int = Field(ge=1)
    returned_count: int = Field(ge=0)
    is_truncated: bool
    retrieved_at: UtcTimestamp
    provider_cursor: str | None
    records: tuple[ProviderRecord, ...] = ()
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_pagination_consistency(self) -> BrokerHistoryPage:
        """Reject inconsistent pagination metadata.

        Returns:
            The validated history page.

        Raises:
            ValueError: ``returned_count`` does not equal the record count
                or exceeds ``requested_count``.
        """
        if self.returned_count != len(self.records):
            raise ValueError("returned_count must equal the record count")
        if self.returned_count > self.requested_count:
            raise ValueError("returned_count must not exceed requested_count")
        return self


class ManageSessionsRequest(WireModel):
    """Operation-discriminated session lifecycle request.

    Every operation requires ``session``; TRANSITION additionally
    requires ``state`` and every other operation forbids it.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["OPEN", "TRANSITION", "RECONNECT", "ASSESS_READINESS", "CLOSE"]
    session: BrokerSessionRef | None = None
    state: BrokerSessionState | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ManageSessionsRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: The session reference is missing, a non-TRANSITION
                operation sets ``state``, or TRANSITION omits it.
        """
        _require_present((("session", self.session),))
        match self.operation:
            case "TRANSITION":
                _require_present((("state", self.state),))
            case "OPEN" | "RECONNECT" | "ASSESS_READINESS" | "CLOSE":
                _require_absent((("state", self.state),))
        return self


class ManageSessionsSuccess(WireModel):
    """Successful session lifecycle operation result."""

    request_id: Uuid7
    session: BrokerSessionRef | None = None
    state: BrokerSessionState | None = None
    readiness: BrokerSessionReadiness | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class ReadProviderStateRequest(WireModel):
    """Operation-discriminated provider-truth read request.

    READ_ACCOUNT and READ_TRADING_STATE require only ``session``;
    READ_MARKET additionally requires ``instrument``; PAGE_HISTORY
    permits only paging fields; NORMALIZE_EVENT additionally requires
    ``raw_event``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal[
        "READ_ACCOUNT",
        "READ_TRADING_STATE",
        "READ_MARKET",
        "PAGE_HISTORY",
        "NORMALIZE_EVENT",
    ]
    session: BrokerSessionRef | None = None
    instrument: InstrumentRef | None = None
    page_size: int | None = Field(default=None, ge=1, le=_PAGE_LIMIT_MAX)
    page_cursor: str | None = None
    raw_event: JsonObject | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> ReadProviderStateRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        _require_present((("session", self.session),))
        match self.operation:
            case "READ_ACCOUNT" | "READ_TRADING_STATE":
                _require_absent(
                    (
                        ("instrument", self.instrument),
                        ("page_size", self.page_size),
                        ("page_cursor", self.page_cursor),
                        ("raw_event", self.raw_event),
                    )
                )
            case "READ_MARKET":
                _require_present((("instrument", self.instrument),))
                _require_absent(
                    (
                        ("page_size", self.page_size),
                        ("page_cursor", self.page_cursor),
                        ("raw_event", self.raw_event),
                    )
                )
            case "PAGE_HISTORY":
                _require_absent(
                    (
                        ("instrument", self.instrument),
                        ("raw_event", self.raw_event),
                    )
                )
            case "NORMALIZE_EVENT":
                _require_present((("raw_event", self.raw_event),))
                _require_absent(
                    (
                        ("instrument", self.instrument),
                        ("page_size", self.page_size),
                        ("page_cursor", self.page_cursor),
                    )
                )
        return self


class ReadProviderStateSuccess(WireModel):
    """Successful provider-truth read operation result."""

    request_id: Uuid7
    account: BrokerAccountSnapshot | None = None
    trading_state: BrokerTradingState | None = None
    market: BrokerMarketState | None = None
    page: BrokerHistoryPage | None = None
    outcome: Literal["SUCCESS"] = "SUCCESS"
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


class TransportOrdersRequest(WireModel):
    """Operation-discriminated execution transport request.

    VALIDATE_REQUEST, SUBMIT, CANCEL, and MODIFY require only
    ``operation_request``; JOURNAL requires only ``operation_id``.
    """

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: Literal["VALIDATE_REQUEST", "SUBMIT", "CANCEL", "MODIFY", "JOURNAL"]
    operation_request: BrokerOperationRequest | None = None
    operation_id: Uuid7 | None = None
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_operation_shape(self) -> TransportOrdersRequest:
        """Validate that request fields match the selected operation.

        Returns:
            The validated request.

        Raises:
            ValueError: Required fields are missing or forbidden fields are
                set for the selected operation.
        """
        match self.operation:
            case "VALIDATE_REQUEST" | "SUBMIT" | "CANCEL" | "MODIFY":
                _require_present((("operation_request", self.operation_request),))
                _require_absent((("operation_id", self.operation_id),))
            case "JOURNAL":
                _require_present((("operation_id", self.operation_id),))
                _require_absent((("operation_request", self.operation_request),))
        return self


class TransportOrdersSuccess(WireModel):
    """Successful execution transport operation result.

    The ratified field ``outcome`` carries the transport operation
    outcome, so the conventional ``Literal["SUCCESS"]`` discriminator of
    other success records is represented here by ``result_version`` and
    the enclosing success type alone.
    """

    request_id: Uuid7
    outcome: BrokerOperationOutcome | None = None
    receipt: BrokerOperationReceipt | None = None
    correlation: ProviderCorrelation | None = None
    result_version: Literal[1] = 1
    schema_version: Literal[1] = 1


# The PEP 695 ``type`` aliases are not classes and cannot be registered in
# WIRE_MODELS. ProviderEvent is a DomainEvent envelope whose typed payload
# is registered in ``app/contracts/broker/events.py`` instead.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "BrokerProviderProfile": BrokerProviderProfile,
    "BrokerSessionRef": BrokerSessionRef,
    "BrokerSessionState": BrokerSessionState,
    "BrokerSessionReadiness": BrokerSessionReadiness,
    "BrokerAccountSnapshot": BrokerAccountSnapshot,
    "BrokerTradingState": BrokerTradingState,
    "BrokerMarketState": BrokerMarketState,
    "BrokerOperationRequest": BrokerOperationRequest,
    "BrokerOperationReceipt": BrokerOperationReceipt,
    "BrokerOperationOutcome": BrokerOperationOutcome,
    "ProviderCorrelation": ProviderCorrelation,
    "BrokerHistoryPage": BrokerHistoryPage,
    "ProviderRecord": ProviderRecord,
    "ManageSessionsRequest": ManageSessionsRequest,
    "ManageSessionsSuccess": ManageSessionsSuccess,
    "ReadProviderStateRequest": ReadProviderStateRequest,
    "ReadProviderStateSuccess": ReadProviderStateSuccess,
    "TransportOrdersRequest": TransportOrdersRequest,
    "TransportOrdersSuccess": TransportOrdersSuccess,
}
