"""Strict Pydantic v2 wire records for the ratified Broker v1 contracts."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from app.contracts.broker.errors import *

# These reference types are annotation-only for readers but Pydantic resolves
# them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import (
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
from app.contracts.common.response import StandardResponse

# Constrained local string alias reused across broker records.
type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


class BrokerId(StrEnum):
    """Standard broker identifiers."""

    BINANCE_SPOT = "binance_spot"
    BINANCE_MARGIN = "binance_margin"
    BINANCE_FUTURES_USDM = "binance_futures_usdm"
    BINANCE_FUTURES_COINM = "binance_futures_coinm"
    BINANCE_USD_M_FUTURES = "binance_futures_usdm"
    BINANCE_COIN_M_FUTURES = "binance_futures_coinm"
    CTRADER = "ctrader"
    MT5 = "mt5"
    DUKASCOPY = "dukascopy"
    YAHOO = "yahoo"


class BrokerEnvironment(StrEnum):
    """Execution environment boundaries."""

    SANDBOX = "SANDBOX"
    DEMO = "DEMO"
    TESTNET = "TESTNET"
    LIVE = "LIVE"
    SIMULATION = "SIMULATION"


class BrokerConnectionState(StrEnum):
    """Provider connection lifecycle states."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    READY = "READY"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"
    CLOSING = "CLOSING"


class BrokerCapabilityId(StrEnum):
    """Standard operation capability identifiers."""

    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    IS_CONNECTED = "is_connected"
    GET_CONNECTION_STATUS = "get_connection_status"
    GET_PLATFORM_INFO = "get_platform_info"
    GET_TERMINAL_INFO = "get_terminal_info"
    GET_ACCOUNT_INFO = "get_account_info"
    GET_BALANCES = "get_balances"
    GET_PERMISSIONS = "get_permissions"
    GET_ACCOUNT_SNAPSHOT = "get_account_snapshot"
    GET_SYMBOLS = "get_symbols"
    GET_SYMBOL_INFO = "get_symbol_info"
    SELECT_SYMBOL = "select_symbol"
    GET_QUOTE = "get_quote"
    GET_SPREAD = "get_spread"
    GET_TICKS = "get_ticks"
    GET_HISTORICAL_BARS = "get_historical_bars"
    SUBSCRIBE_QUOTES = "subscribe_quotes"
    SUBSCRIBE_TICKS = "subscribe_ticks"
    SUBSCRIBE_BARS = "subscribe_bars"
    SUBSCRIBE_ORDER_BOOK = "subscribe_order_book"
    UNSUBSCRIBE = "unsubscribe"
    LIST_SUBSCRIPTIONS = "list_subscriptions"
    GET_ORDERS = "get_orders"
    GET_ORDER = "get_order"
    CHECK_ORDER = "check_order"
    LIST_ORDER_HISTORY = "list_order_history"
    GET_HISTORY_ORDER = "get_history_order"
    GET_DEALS = "get_deals"
    LIST_DEAL_HISTORY = "list_deal_history"
    LIST_ACCOUNT_TRANSACTIONS = "list_account_transactions"
    GET_POSITIONS = "get_positions"
    GET_POSITION = "get_position"
    PLACE_ORDER = "place_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    MODIFY_POSITION = "modify_position"
    CLOSE_POSITION = "close_position"
    CALCULATE_MARGIN = "calculate_margin"
    CALCULATE_PROFIT = "calculate_profit"
    GET_TRADING_SESSIONS = "get_trading_sessions"


@dataclass(frozen=True)
class BrokerCapability:
    """Broker capability descriptor."""

    capability: BrokerCapabilityId | str
    implementation_status: str = "IMPLEMENTED"
    availability: str = "AVAILABLE"
    access_mode: str = "READ"
    requirement: str = "NONE"
    verification_status: str = "NOT_TESTED"
    execution_model: str = "TEST_DOUBLE"
    description: str = ""


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

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Generic, Self, TypeVar, cast

T = TypeVar("T")


class DictLikeModelMixin:
    """Provides dictionary-like interface to dataclasses for contract interoperability."""

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        details = getattr(self, "details", None)
        if isinstance(details, dict) and key in details:
            return details[key]
        raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        if hasattr(self, key):
            return True
        details = getattr(self, "details", None)
        return isinstance(details, dict) and key in details

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        details = getattr(self, "details", None)
        if isinstance(details, dict):
            return details.get(key, default)
        return default

    def keys(self) -> list[str]:
        k = [f.name for f in fields(cast("Any", self))]
        details = getattr(self, "details", None)
        if isinstance(details, dict):
            k.extend([dk for dk in details if dk not in k])
        return k

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary representation."""
        from dataclasses import asdict

        return asdict(cast("Any", self))

    @classmethod
    def from_dict(cls: type[Self], data: Any) -> Self:
        """Construct instance from raw dictionary or namedtuple."""
        raw = data._asdict() if hasattr(data, "_asdict") else dict(data)
        known = {f.name for f in fields(cast("Any", cls)) if f.name != "details"}
        init_kwargs = {k: raw[k] for k in known if k in raw}
        extra = {k: v for k, v in raw.items() if k not in known}
        if "details" in [f.name for f in fields(cast("Any", cls))]:
            init_kwargs["details"] = extra
        return cls(**init_kwargs)


@dataclass
class BrokerConnectionConfig:
    """Connection settings for a broker session."""

    broker_id: Any = "mt5"
    environment: Any = "demo"
    account_number: Any = None
    account_id: Any = None
    account_reference: Any = None
    login: Any = None
    password: Any = None
    server: Any = None
    terminal_path: Any = None
    path: Any = None
    endpoint: Any = None
    timeout: float = 30.0
    timeout_sec: float = 30.0
    connect_timeout_sec: float = 30.0
    request_timeout_sec: float = 30.0
    transport_reconnect_max_attempts: int = 3
    stream_buffer_size: int = 1000
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 30.0
    circuit_half_open_max_calls: int = 1
    probe_symbol: str | None = None
    provider_enabled: bool = True
    read_only: bool = False
    credentials: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerTerminalInfo(DictLikeModelMixin):
    """Properties of the broker terminal/platform environment (CTerminalInfo)."""

    build: int = 0
    community_account: bool = False
    community_connection: bool = False
    connected: bool = True
    dlls_allowed: bool = True
    trade_allowed: bool = True
    email_enabled: bool = False
    ftp_enabled: bool = False
    notifications_enabled: bool = False
    max_bars: int = 100000
    mqid: bool = False
    codepage: int = 0
    ping_last: int = 0
    memory_total: int = 0
    memory_free: int = 0
    memory_used: int = 0
    name: str = ""
    path: str = ""
    data_path: str = ""
    commondata_path: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerPlatformInfo:
    """Platform identity and features."""

    platform: str = "metatrader5"
    version: str = "5.0"
    build: int = 0
    environment: str = "demo"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerPage(Generic[T]):
    """Generic paged response container."""

    items: tuple[T, ...] = ()
    cursor: str | None = None
    has_more: bool = False
    total: int | None = None
    limit: int | None = None
    truncated: bool = False
    provider_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerOrderFilter:
    """Filter parameters for historical order queries."""

    symbol: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int | None = None


@dataclass
class BrokerTradingSession:
    """Trading session schedule."""

    symbol: str = "EURUSD"
    session_start: str = "00:00"
    session_end: str = "24:00"
    is_open: bool = True


class _ProviderResponseError(Exception):
    """Exception raised on unexpected provider response format."""


class _CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class _CircuitOpenError(RuntimeError):
    """Raised when the circuit breaker rejects an operation."""


class _RateLimitedError(RuntimeError):
    """Raised when a broker API rate limit is exceeded."""


class _TransportCircuitBreaker:
    """Circuit breaker guarding transport operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_max_calls: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_max_calls = half_open_max_calls
        self._state = _CircuitState.CLOSED
        self._consecutive_failures = 0

    @property
    def state(self) -> _CircuitState:
        return self._state

    async def before_call(self) -> _CircuitOpenError | None:
        if self._state == _CircuitState.OPEN:
            return _CircuitOpenError("Circuit is open")
        return None

    async def record_success(self) -> None:
        self._state = _CircuitState.CLOSED
        self._consecutive_failures = 0

    async def record_failure(self, error: Any = None) -> None:
        del error
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._state = _CircuitState.OPEN


BrokerResponseError = _ProviderResponseError
_RequestValidationError = _ProviderResponseError


@dataclass
class BrokerPermissions:
    """Trading and account permissions."""

    trade_allowed: bool = True
    trade_expert: bool = True
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerBalance:
    """Asset or currency balance."""

    currency: str = "USD"
    balance: Decimal = Decimal(0)
    equity: Decimal = Decimal(0)
    free: Decimal = Decimal(0)
    locked: Decimal = Decimal(0)
    margin: Decimal = Decimal(0)


@dataclass
class BrokerAccountInfo(DictLikeModelMixin):
    """Account properties and financial state (CAccountInfo)."""

    login: int | str = ""
    trade_mode: str = "DEMO"
    leverage: int = 100
    limit_orders: int = 0
    margin_so_mode: int = 0
    trade_allowed: bool = True
    trade_expert: bool = True
    balance: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)
    profit: Decimal = Decimal(0)
    equity: Decimal = Decimal(0)
    margin: Decimal = Decimal(0)
    margin_free: Decimal = Decimal(0)
    margin_level: Decimal | None = None
    margin_initial: Decimal = Decimal(0)
    margin_maintenance: Decimal = Decimal(0)
    assets: Decimal = Decimal(0)
    liabilities: Decimal = Decimal(0)
    commission_blocked: Decimal = Decimal(0)
    name: str = ""
    server: str = ""
    currency: str = "USD"
    company: str = ""
    retrieved_at: datetime | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerSymbolInfo(DictLikeModelMixin):
    """Symbol specifications and trading parameters (CSymbolInfo)."""

    symbol: str = "EURUSD"
    name: str = "EURUSD"
    provider_symbol: str = "EURUSD"
    product_profile: str = "mt5"
    price_unit: str = "quote_currency"
    quantity_unit: str = "lots"
    price_precision: int = 5
    price_step: Decimal = Decimal("0.00001")
    quantity_step: Decimal = Decimal("0.01")
    min_quantity: Decimal = Decimal("0.01")
    max_quantity: Decimal = Decimal("100.0")
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    select: bool = True
    visible: bool = True
    is_synchronized: bool = True
    digits: int = 5
    point: float = 0.00001
    spread: float = 1.0
    ask: float = 0.0
    bid: float = 0.0
    last: float = 0.0
    volume: float = 0.0
    volume_high: float = 0.0
    volume_low: float = 0.0
    session_deals: int = 0
    session_volume: float = 0.0
    session_turnover: float = 0.0
    contract_size: float = 100000.0
    trade_execution: int = 0
    trade_mode: int | str = 0
    filling_mode: int = 0
    order_mode: int = 0
    expiration_mode: int = 0
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    swap_long: float = 0.0
    swap_short: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerQuote:
    """Bid/ask price quote."""

    symbol: str = "EURUSD"
    bid: Any = 0.0
    ask: Any = 0.0
    timestamp: datetime | None = None
    observation_timestamp: datetime | None = None
    provider_timestamp: datetime | None = None
    retrieved_at: datetime | None = None
    spread: Any = 0.0
    price_unit: str = "quote_currency"
    quantity_unit: str = "lots"
    bid_quantity: Any = None
    ask_quantity: Any = None
    provider_sequence_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerTick:
    """Tick price with volume and flags."""

    symbol: str = "EURUSD"
    time: datetime | None = None
    timestamp: datetime | None = None
    bid: Any = 0.0
    ask: Any = 0.0
    last: Any = 0.0
    volume: Any = 0.0
    flags: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerBar:
    """OHLCV candlestick bar."""

    symbol: str = "EURUSD"
    time: datetime | None = None
    opening_timestamp: datetime | None = None
    closing_timestamp: datetime | None = None
    is_closed: bool = True
    open: Any = 0.0
    high: Any = 0.0
    low: Any = 0.0
    close: Any = 0.0
    provider_timeframe: str = "1m"
    requested_timeframe: str = "1m"
    price_unit: str = "provider_quote_currency"
    quantity_unit: str = "provider_volume"
    trade_volume: Any = None
    tick_volume: int = 0
    spread: int = 0
    real_volume: int = 0
    volume: Any = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerOrderBook:
    """Market depth snapshot."""

    symbol: str = "EURUSD"
    bids: list[tuple[float, float]] = field(default_factory=list)
    asks: list[tuple[float, float]] = field(default_factory=list)
    timestamp: datetime | None = None


@dataclass
class BrokerOrder:
    """Active or historical order (COrderInfo / CHistoryOrderInfo)."""

    ticket: int | str = ""
    order_id: str = ""
    time_setup: datetime | None = None
    time_setup_msc: int = 0
    time_done: datetime | None = None
    time_done_msc: int = 0
    time_expiration: datetime | None = None
    type: int | str = 0
    order_type: str = "BUY"
    side: str = "BUY"
    type_filling: int = 0
    type_time: int = 0
    state: int | str = "PLACED"
    status: str = "PLACED"
    magic: int = 0
    position_id: int | str = 0
    volume_initial: float = 1.0
    volume_current: float = 1.0
    quantity: Any = "1.0"
    volume: Any = "1.0"
    price_open: float = 0.0
    price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    price_current: float = 0.0
    price_stoplimit: float = 0.0
    symbol: str = "EURUSD"
    comment: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerOrderRequest:
    """New order submission parameters."""

    symbol: str = "EURUSD"
    side: str = "BUY"
    order_type: str = "MARKET"
    quantity: Any = "1.0"
    volume: Any = "1.0"
    quantity_unit: str = "lots"
    price: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    deviation_points: int | None = None
    magic: int | None = None
    comment: str | None = None
    expiration: datetime | None = None
    fill_policy: str | None = None
    time_policy: str | None = None
    client_order_id: str | None = None
    account_reference: str | None = None
    time_in_force: str | None = None
    environment: str | None = None
    product_profile: str = "mt5"


@dataclass
class BrokerOrderModificationRequest:
    """Parameters for modifying an active order."""

    order_id: str = "order-1"
    price: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    quantity: Any = None
    volume: Any = None
    expiration: datetime | None = None


@dataclass
class BrokerOrderCheck:
    """Pre-trade validation outcome."""

    retcode: int = 0
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    comment: str = "Done"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerOrderResult:
    """Trade placement/execution result."""

    retcode: int = 0
    deal: int = 0
    order: int = 0
    order_id: str = ""
    volume: float = 0.0
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    comment: str = ""
    request_id: int = 0
    status: str = "FILLED"
    outcome: str = "ACCEPTED"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerPosition:
    """Open trading position (CPositionInfo)."""

    ticket: int | str = ""
    position_id: str = "pos-1"
    time: datetime | None = None
    time_msc: int = 0
    time_update: datetime | None = None
    type: int | str = 0
    side: str = "BUY"
    magic: int = 0
    identifier: int | str = 0
    volume: Any = 1.0
    quantity: Any = 1.0
    price_open: Any = 0.0
    open_price: Any = 0.0
    sl: float = 0.0
    tp: float = 0.0
    price_current: Any = 0.0
    current_price: Any = 0.0
    swap: Any = 0.0
    profit: Any = 0.0
    unrealized_profit: Any = 0.0
    symbol: str = "EURUSD"
    comment: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerPositionModificationRequest:
    """Parameters for modifying position stops."""

    position_id: str = "pos-1"
    stop_loss: float | None = None
    take_profit: float | None = None


@dataclass
class BrokerPositionCloseRequest:
    """Parameters for closing an open position."""

    position_id: str = "pos-1"
    volume: float | None = None
    quantity: Any = None
    quantity_unit: str = "lots"


@dataclass
class BrokerDeal:
    """Trade execution deal (CDealInfo)."""

    ticket: int | str = ""
    deal_id: str = "deal-1"
    order: int | str = ""
    time: datetime | None = None
    time_msc: int = 0
    type: int | str = 0
    side: str = "BUY"
    entry: int = 0
    magic: int = 0
    position_id: int | str = 0
    volume: Any = 1.0
    quantity: Any = 1.0
    price: Any = 0.0
    commission: Any = 0.0
    swap: Any = 0.0
    profit: Any = 0.0
    fee: Any = 0.0
    sl: float = 0.0
    tp: float = 0.0
    symbol: str = "EURUSD"
    comment: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerTransaction:
    """Financial account transaction."""

    transaction_id: str = "txn-1"
    time: datetime | None = None
    type: str = "DEPOSIT"
    amount: Decimal = Decimal(0)
    currency: str = "USD"
    comment: str = ""


@dataclass
class BrokerMarginCalculationRequest:
    """Parameters for calculating required margin."""

    symbol: str = "EURUSD"
    side: str = "BUY"
    volume: Any = "1.0"
    quantity: Any = "1.0"
    quantity_unit: str = "lots"
    price: float | None = None
    leverage: int | None = None
    product_profile: str = "mt5"


BrokerMarginRequest = BrokerMarginCalculationRequest


@dataclass
class BrokerPositionFilter:
    """Filter parameters for position queries."""

    symbol: str | None = None
    limit: int | None = None


@dataclass
class BrokerProfitCalculationRequest:
    """Parameters for calculating expected profit."""

    symbol: str = "EURUSD"
    side: str = "BUY"
    volume: Any = "1.0"
    quantity: Any = "1.0"
    quantity_unit: str = "lots"
    open_price: float | None = None
    close_price: float | None = None
    product_profile: str = "mt5"


BrokerProfitRequest = BrokerProfitCalculationRequest


@dataclass
class BrokerCalculationResult:
    """Margin or profit calculation output."""

    value: Decimal = Decimal(0)
    currency: str = "USD"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrokerSubscriptionInfo:
    """Metadata describing an active stream subscription."""

    subscription_id: str = ""
    capability: str = ""
    symbols: tuple[str, ...] = ()
    created_at: datetime | None = None
    active: bool = True


class BrokerSubscription(Generic[T]):
    """Async streaming subscription handle."""

    def __init__(
        self,
        subscription_id: str,
        capability: str,
        symbols: tuple[str, ...],
        queue: asyncio.Queue[T | None] | None = None,
        unsubscribe_callback: Callable[[], Any] | None = None,
    ) -> None:
        self.subscription_id = subscription_id
        self.capability = capability
        self.symbols = symbols
        self._queue = queue or asyncio.Queue()
        self._unsubscribe_callback = unsubscribe_callback
        self._closed = False

    async def __aiter__(self) -> AsyncIterator[T]:
        while not self._closed:
            item = await self._queue.get()
            if item is None:
                break
            yield item

    async def get(self) -> T | None:
        if self._closed:
            return None
        return await self._queue.get()

    async def close(self) -> None:
        self._closed = True
        await self._queue.put(None)

    async def unsubscribe(self) -> StandardResponse[bool]:
        if self._unsubscribe_callback is not None:
            import inspect

            if inspect.iscoroutinefunction(self._unsubscribe_callback):
                await self._unsubscribe_callback()
            else:
                self._unsubscribe_callback()
        await self.close()
        return StandardResponse(status="success", data=True)
