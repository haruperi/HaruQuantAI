"""Provider-private legacy compatibility types and stubs."""

# ruff: noqa: ANN401, ARG002
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class BrokerId(StrEnum):
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
    SANDBOX = "SANDBOX"
    DEMO = "DEMO"
    TESTNET = "TESTNET"
    LIVE = "LIVE"


class BrokerConnectionState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    READY = "READY"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"


class BrokerCapabilityId(StrEnum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    IS_CONNECTED = "is_connected"
    GET_PLATFORM_INFO = "get_platform_info"
    GET_ACCOUNT_INFO = "get_account_info"
    GET_QUOTE = "get_quote"
    GET_SPREAD = "get_spread"
    GET_TICKS = "get_ticks"
    GET_BARS = "get_bars"
    GET_HISTORICAL_BARS = "get_historical_bars"
    GET_SYMBOLS = "get_symbols"
    GET_SYMBOL_INFO = "get_symbol_info"
    GET_TRADING_SESSION = "get_trading_session"
    GET_TRADING_SESSIONS = "get_trading_sessions"
    GET_MARKET_STATUS = "get_market_status"
    GET_ORDER_BOOK = "get_order_book"
    GET_SERVER_TIME = "get_server_time"
    GET_BALANCES = "get_balances"
    GET_LAST_ERROR = "get_last_error"
    GET_PERMISSIONS = "get_permissions"
    GET_PROVIDER_SPECIFICATION = "get_provider_specification"
    SELECT_SYMBOL = "select_symbol"
    GET_ORDERS = "get_orders"
    GET_ORDER = "get_order"
    GET_POSITIONS = "get_positions"
    GET_POSITION = "get_position"
    GET_DEALS = "get_deals"
    GET_DEAL = "get_deal"
    LIST_ACCOUNT_TRANSACTIONS = "list_account_transactions"
    CHECK_ORDER = "check_order"
    PLACE_ORDER = "place_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    CLOSE_POSITION = "close_position"
    MODIFY_POSITION = "modify_position"
    REPLACE_ORDER = "replace_order"
    ATTACH_PROTECTION = "attach_protection"
    REDUCE_POSITION = "reduce_position"
    CALCULATE_MARGIN = "calculate_margin"
    CALCULATE_PROFIT = "calculate_profit"
    SUBSCRIBE_QUOTES = "subscribe_quotes"
    SUBSCRIBE_TICKS = "subscribe_ticks"
    SUBSCRIBE_BARS = "subscribe_bars"
    SUBSCRIBE_ORDER_BOOK = "subscribe_order_book"


class BrokerErrorCode(StrEnum):
    BROKER_OK = "BROKER_OK"
    BROKER_PROVIDER_ERROR = "BROKER_PROVIDER_ERROR"
    BROKER_REQUEST_INVALID = "BROKER_REQUEST_INVALID"
    BROKER_REQUEST_REJECTED = "BROKER_REQUEST_REJECTED"
    BROKER_AUTHENTICATION_FAILED = "BROKER_AUTHENTICATION_FAILED"
    BROKER_RESPONSE_INVALID = "BROKER_RESPONSE_INVALID"
    BROKER_CAPABILITY_UNAVAILABLE = "BROKER_CAPABILITY_UNAVAILABLE"
    BROKER_CAPABILITY_NOT_IMPLEMENTED = "BROKER_CAPABILITY_NOT_IMPLEMENTED"
    BROKER_ENVIRONMENT_MISMATCH = "BROKER_ENVIRONMENT_MISMATCH"
    BROKER_CONFIGURATION_INVALID = "BROKER_CONFIGURATION_INVALID"
    BROKER_UNKNOWN_OUTCOME = "BROKER_UNKNOWN_OUTCOME"
    BROKER_CONNECTION_FAILED = "BROKER_CONNECTION_FAILED"
    BROKER_NOT_CONNECTED = "BROKER_NOT_CONNECTED"
    BROKER_TIMEOUT = "BROKER_TIMEOUT"
    BROKER_RATE_LIMITED = "BROKER_RATE_LIMITED"
    BROKER_CIRCUIT_OPEN = "BROKER_CIRCUIT_OPEN"
    BROKER_ACCOUNT_NOT_FOUND = "BROKER_ACCOUNT_NOT_FOUND"
    BROKER_ORDER_NOT_FOUND = "BROKER_ORDER_NOT_FOUND"
    BROKER_POSITION_NOT_FOUND = "BROKER_POSITION_NOT_FOUND"
    BROKER_DEAL_NOT_FOUND = "BROKER_DEAL_NOT_FOUND"
    BROKER_SYMBOL_NOT_FOUND = "BROKER_SYMBOL_NOT_FOUND"


class _CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class _CircuitOpenError(Exception):
    pass


class _RateLimitedError(Exception):
    pass


class _ProviderResponseError(Exception):
    pass


class _RequestValidationError(Exception):
    pass


@dataclass(frozen=True)
class BrokerError:
    code: Any
    message: str = ""
    transient: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    provider_code: Any = None
    provider_message: Any = None
    capability: Any = None


@dataclass(frozen=True)
class BrokerCapability:
    capability: Any
    implementation_status: str = "IMPLEMENTED"
    availability: str = "AVAILABLE"
    access_mode: str = "READ"
    requirement: str = "NONE"
    verification_status: str = "TESTED_SANDBOX"
    execution_model: str = "LOCAL"


@dataclass(frozen=True)
class BrokerConnectionConfig:
    broker_id: Any = BrokerId.MT5
    environment: Any = BrokerEnvironment.DEMO
    provider_enabled: bool = True
    connect_timeout_sec: float = 10.0
    request_timeout_sec: float = 10.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 30.0
    circuit_half_open_max_calls: int = 2
    stream_buffer_size: int = 1000
    transport_reconnect_max_attempts: int = 3
    account_reference: Any = None
    endpoint: Any = None
    credentials: dict[str, Any] | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StandardResponse[T]:
    status: str
    data: T | None = None
    error: BrokerError | None = None
    message: str = ""


@dataclass
class BrokerPlatformInfo:
    broker_id: Any = BrokerId.MT5
    provider_name: Any = "mt5"
    product_profile: Any = "spot"
    environment: Any = BrokerEnvironment.DEMO
    connected: bool = True
    server_time: str = ""
    build: str = ""
    version: str = ""
    terminal_name: str = ""
    terminal_company: str = ""
    platform_name: str = ""
    platform_version: str = ""
    account_mode: str = ""
    observed_at: Any = None
    endpoint_metadata: Any = None
    api_or_terminal_version: str | None = None


@dataclass
class BrokerAccountInfo:
    account_id: str = "test-account"
    broker_id: Any = BrokerId.MT5
    environment: Any = BrokerEnvironment.DEMO
    currency: str = "USD"
    balance: Any = "10000.00"
    equity: Any = "10000.00"
    margin: Any = "0.00"
    free_margin: Any = "10000.00"
    margin_level: Any = "0.00"
    leverage: int = 100
    observed_at: Any = None


@dataclass
class BrokerBalance:
    currency: str = "USD"
    balance: Any = "10000.00"
    equity: Any = "10000.00"
    free_margin: Any = "10000.00"


@dataclass
class BrokerPermissions:
    trade_allowed: bool = True
    expert_allowed: bool = True
    account_mode: str = "DEMO"


@dataclass
class BrokerSymbolInfo:
    symbol: str = "EURUSD"
    provider_symbol: str = "EURUSD"
    product_profile: Any = "forex"
    price_unit: Any = "0.00001"
    quantity_unit: Any = "1000"
    base_asset: str = "EUR"
    quote_asset: str = "USD"
    min_quantity: Any = "0.01"
    max_quantity: Any = "100.0"
    lot_size: Any = "100000"
    digits: int = 5
    price_precision: int = 5
    quantity_precision: int = 5
    trading_flags: Any = None


@dataclass
class BrokerQuote:
    symbol: str = "EURUSD"
    bid: Any = "1.08000"
    ask: Any = "1.08010"
    spread: Any = "0.00010"
    timestamp: Any = None
    price_unit: Any = "0.00001"
    quantity_unit: Any = "1000"
    retrieved_at: Any = None
    provider_timestamp: Any = None
    bid_quantity: Any = None
    ask_quantity: Any = None
    provider_sequence_id: Any = None


@dataclass
class BrokerTick:
    symbol: str = "EURUSD"
    time: Any = None
    event_timestamp: Any = None
    provider_receipt_timestamp: Any = None
    bid: Any = "1.08000"
    ask: Any = "1.08010"
    last: Any = "1.08005"
    last_price: Any = "1.08005"
    volume: Any = "1.0"
    bid_quantity: Any = None
    ask_quantity: Any = None
    price_unit: Any = "0.00001"
    quantity_unit: Any = "1000"
    tick_type: Any = None
    provider_sequence_id: Any = None


@dataclass
class BrokerBar:
    symbol: str = "EURUSD"
    timeframe: str = "1m"
    start_time: Any = None
    open: Any = "1.08000"
    high: Any = "1.08020"
    low: Any = "1.07990"
    close: Any = "1.08010"
    volume: Any = "10.0"
    trade_volume: Any = "10.0"
    opening_timestamp: Any = None
    closing_timestamp: Any = None
    is_closed: bool = True
    provider_timeframe: str = "1m"
    requested_timeframe: str = "1m"
    price_unit: Any = "0.00001"
    quantity_unit: Any = "1000"
    tick_volume: Any = "10"
    spread: Any = None
    spread_unit: Any = None


@dataclass
class BrokerOrder:
    order_id: str = "order-1"
    symbol: str = "EURUSD"
    side: str = "BUY"
    order_type: str = "LIMIT"
    quantity: Any = "1.0"
    price: Any = "1.08000"
    status: str = "FILLED"
    time: Any = None


@dataclass
class BrokerPosition:
    position_id: str = "pos-1"
    symbol: str = "EURUSD"
    side: str = "BUY"
    volume: Any = "1.0"
    open_price: Any = "1.08000"
    current_price: Any = "1.08010"
    profit: Any = "10.0"
    open_time: Any = None


@dataclass
class BrokerPositionFilter:
    symbol: str | None = None
    position_id: str | None = None
    side: str | None = None


@dataclass
class BrokerDeal:
    deal_id: str = "deal-1"
    order_id: str = "order-1"
    position_id: str = "pos-1"
    symbol: str = "EURUSD"
    side: str = "BUY"
    volume: Any = "1.0"
    price: Any = "1.08000"
    time: Any = None


@dataclass
class BrokerAccountTransaction:
    transaction_id: str = "tx-1"
    account_id: str = "test-account"
    transaction_type: str = "DEAL"
    amount: Any = "10.0"
    time: Any = None


@dataclass
class BrokerOrderFilter:
    symbol: str | None = None
    status: str | None = None


@dataclass
class BrokerOrderCheckRequest:
    symbol: str = "EURUSD"
    side: str = "BUY"
    order_type: str = "LIMIT"
    quantity: Any = "1.0"
    price: Any = "1.08000"


@dataclass
class BrokerOrderPlacementRequest:
    symbol: str = "EURUSD"
    side: str = "BUY"
    order_type: str = "LIMIT"
    quantity: Any = "1.0"
    price: Any = "1.08000"


@dataclass
class BrokerOrderModificationRequest:
    order_id: str = "order-1"
    price: Any = "1.08000"
    quantity: Any = "1.0"


@dataclass
class BrokerOrderCancellationRequest:
    order_id: str = "order-1"
    symbol: str = "EURUSD"


@dataclass
class BrokerOrderReplacementRequest:
    order_id: str = "order-1"
    new_price: Any = "1.08000"
    new_quantity: Any = "1.0"


@dataclass
class BrokerPositionCloseRequest:
    position_id: str = "pos-1"
    symbol: str = "EURUSD"
    volume: Any = "1.0"


@dataclass
class BrokerPositionModificationRequest:
    position_id: str = "pos-1"
    stop_loss: Any = None
    take_profit: Any = None


@dataclass
class BrokerPositionProtectionRequest:
    position_id: str = "pos-1"
    stop_loss: Any = None
    take_profit: Any = None


@dataclass
class BrokerPositionReductionRequest:
    position_id: str = "pos-1"
    volume: Any = "0.5"


@dataclass
class BrokerMarginCalculationRequest:
    symbol: str = "EURUSD"
    side: str = "BUY"
    volume: Any = "1.0"


@dataclass
class BrokerProfitCalculationRequest:
    symbol: str = "EURUSD"
    side: str = "BUY"
    volume: Any = "1.0"
    open_price: Any = "1.08000"
    close_price: Any = "1.08010"


@dataclass
class BrokerTradingSession:
    symbol: str = "EURUSD"
    opens_at: Any = None
    closes_at: Any = None
    is_open: bool = True
    session_name: str = "REGULAR"
    provider_timezone: str = "UTC"
    provider_metadata: Any = None


@dataclass
class BrokerMarketStatus:
    symbol: str = "EURUSD"
    status: str = "OPEN"
    is_open: bool = True
    retrieved_at: Any = None
    reason: str = ""


@dataclass
class BrokerOrderBook:
    symbol: str = "EURUSD"
    bids: Any = ()
    asks: Any = ()
    is_snapshot: bool = True
    resnapshot_required: bool = False
    event_timestamp: Any = None
    price_unit: Any = "0.00001"
    quantity_unit: Any = "1000"
    first_sequence_id: Any = None
    last_sequence_id: Any = None
    depth_truncation: Any = None


@dataclass
class BrokerServerTime:
    server_time: Any = None
    provider_time: Any = None
    local_send_time: Any = None
    local_receive_time: Any = None
    estimated_clock_offset_ms: Any = None
    round_trip_latency_ms: Any = None


@dataclass
class BrokerPage[T]:
    items: tuple[T, ...] | list[T] = field(default_factory=list)
    total: int = 0
    limit: int = 100
    cursor: str | None = None
    next_cursor: str | None = None
    truncated: bool = False
    provider_metadata: Any = None


class _BrokerSubscription[TEvent]:
    """Legacy bounded subscription handle."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def events(self) -> AsyncIterator[TEvent]:
        items: tuple[TEvent, ...] = ()
        for item in items:
            yield item

    async def unsubscribe(self) -> StandardResponse[bool]:
        return StandardResponse(status="success", data=True)


class _TransportCircuitBreaker:
    """Legacy adapter circuit breaker."""

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

    async def before_call(self) -> Any:
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


class _UnsupportedAdapterBase:
    """Legacy base adapter implementation."""

    _config: Any
    _session_generation: int
    _state: BrokerConnectionState

    def __init__(self, config: Any = None, *args: Any, **kwargs: Any) -> None:
        self._config = config
        self._session_generation = 0
        self._state = BrokerConnectionState.DISCONNECTED

    @property
    def is_connected_sync(self) -> bool:
        return self._state == BrokerConnectionState.READY

    async def connect(self) -> StandardResponse[None]:
        self._state = BrokerConnectionState.READY
        return StandardResponse(status="success", data=None)

    async def disconnect(self) -> StandardResponse[Any]:
        self._state = BrokerConnectionState.DISCONNECTED
        return StandardResponse(status="success", data=None)

    async def get_last_error(self) -> StandardResponse[BrokerError | None]:
        return StandardResponse(status="success", data=None)

    def _record_provider_latency(self, latency_ms: float) -> None:
        pass

    async def _transition(self, state: BrokerConnectionState, reason: str = "") -> None:
        del reason
        self._state = state

    def _result[T](
        self,
        capability: Any = None,
        data: T | None = None,
        error: BrokerError | None = None,
    ) -> StandardResponse[T]:
        del capability
        return StandardResponse(
            status="success" if error is None else "error",
            data=data,
            error=error,
        )

    def _unsupported[T](self, capability: Any = None) -> StandardResponse[T]:
        del capability
        return StandardResponse(
            status="error",
            error=BrokerError(
                code=BrokerErrorCode.BROKER_CAPABILITY_NOT_IMPLEMENTED,
                message="Operation not supported",
            ),
        )

    def _propagated_error[T](self, *args: Any, **kwargs: Any) -> StandardResponse[T]:
        return StandardResponse(
            status="error",
            error=BrokerError(
                code=BrokerErrorCode.BROKER_PROVIDER_ERROR,
                message="Propagated error",
            ),
        )

    def _error[T](
        self,
        capability: Any = None,
        code: Any = None,
        message: str = "",
        *args: Any,
        **kwargs: Any,
    ) -> StandardResponse[T]:
        del capability, args, kwargs
        return StandardResponse(
            status="error",
            error=BrokerError(code=code, message=message),
        )

    async def is_connected(self) -> StandardResponse[bool]:
        return StandardResponse(
            status="success", data=(self._state == BrokerConnectionState.READY)
        )


# Legacy Aliases
BrokerMarginRequest = BrokerMarginCalculationRequest
BrokerProfitRequest = BrokerProfitCalculationRequest
BrokerOrderResult = BrokerOrder
BrokerOrderCheck = BrokerOrderCheckRequest
BrokerOrderRequest = BrokerOrderPlacementRequest
BrokerOrderRequestV2 = BrokerOrderPlacementRequest

BrokerSubscription = _BrokerSubscription
BrokerSubscriptionHandle = _BrokerSubscription


@dataclass(frozen=True)
class BrokerSubscriptionInfo:
    subscription_id: str
    capability: Any
    symbols: tuple[str, ...]
    created_at: str
    buffer_size: int = 1000
