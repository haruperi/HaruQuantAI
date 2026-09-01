"""Deterministic adapter fixture for the conformance feature."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class BrokerCapabilityId(StrEnum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    GET_PLATFORM_INFO = "get_platform_info"
    GET_ACCOUNT_INFO = "get_account_info"
    GET_QUOTE = "get_quote"
    GET_TICKS = "get_ticks"
    GET_BARS = "get_bars"
    GET_SYMBOLS = "get_symbols"
    GET_TRADING_SESSION = "get_trading_session"
    GET_ORDERS = "get_orders"
    GET_POSITIONS = "get_positions"
    GET_DEALS = "get_deals"
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
    IS_CONNECTED = "is_connected"


class BrokerConnectionState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    READY = "ready"
    FAILED = "failed"


class BrokerErrorCode(StrEnum):
    BROKER_OK = "BROKER_OK"
    BROKER_PROVIDER_ERROR = "BROKER_PROVIDER_ERROR"
    BROKER_CAPABILITY_UNAVAILABLE = "BROKER_CAPABILITY_UNAVAILABLE"
    BROKER_CAPABILITY_NOT_IMPLEMENTED = "BROKER_CAPABILITY_NOT_IMPLEMENTED"


@dataclass(frozen=True)
class BrokerCapability:
    capability: BrokerCapabilityId
    implementation_status: str = "IMPLEMENTED"
    availability: str = "AVAILABLE"
    access_mode: str = "READ"
    requirement: str = "NONE"
    verification_status: str = "TESTED_SANDBOX"
    execution_model: str = "LOCAL"


@dataclass(frozen=True)
class BrokerError:
    code: Any
    message: str


@dataclass(frozen=True)
class BrokerConnectionConfig:
    broker_id: Any = "mt5"
    environment: Any = "demo"
    provider_enabled: bool = True


@dataclass(frozen=True)
class BrokerSubscriptionInfo:
    subscription_id: str
    capability: Any
    symbols: tuple[str, ...]
    created_at: str
    buffer_size: int = 1000


@dataclass(frozen=True)
class StandardResponse[T]:
    status: str
    data: T | None = None
    error: BrokerError | None = None
    message: str = ""


class _BrokerSubscription[TEvent]:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def events(self) -> AsyncIterator[Any]:
        if False:
            yield None

    async def unsubscribe(self) -> Any:
        return StandardResponse(status="success")


class FakeBrokerAdapter:
    """Deterministic fake adapter for conformance test suites."""

    CONTRACT_VERSION = "1.0.0"
    SCHEMA_ID = "haruquantai.broker.adapter@1"

    def __init__(
        self,
        config: Any,
        capabilities: dict[Any, Any] | None = None,
        fixtures: dict[Any, Any] | None = None,
    ) -> None:
        self._config = config
        self._capabilities = capabilities or {}
        self._fixtures = fixtures or {}
        self._state = BrokerConnectionState.DISCONNECTED
        self._injected_errors: dict[Any, Any] = {}

    @property
    def contract_version(self) -> str:
        return self.CONTRACT_VERSION

    @property
    def schema_id(self) -> str:
        return self.SCHEMA_ID

    def inject_error(self, capability: Any, error: Any) -> StandardResponse[None]:
        if error is None:
            self._injected_errors.pop(capability, None)
        else:
            self._injected_errors[capability] = error
        return StandardResponse(status="success")

    async def connect(self) -> StandardResponse[bool]:
        self._state = BrokerConnectionState.READY
        return StandardResponse(status="success", data=True)

    async def disconnect(self) -> StandardResponse[bool]:
        self._state = BrokerConnectionState.DISCONNECTED
        return StandardResponse(status="success", data=True)

    async def is_connected(self) -> StandardResponse[bool]:
        return StandardResponse(
            status="success", data=(self._state == BrokerConnectionState.READY)
        )

    async def supports(self, capability: Any) -> StandardResponse[bool]:
        cap = self._capabilities.get(capability)
        is_avail = bool(
            cap and getattr(cap, "availability", "UNAVAILABLE") == "AVAILABLE"
        )
        return StandardResponse(status="success", data=is_avail)

    async def get_quote(self, symbol: str) -> StandardResponse[Any]:
        del symbol
        if BrokerCapabilityId.GET_QUOTE in self._injected_errors:
            return StandardResponse(
                status="error",
                error=self._injected_errors[BrokerCapabilityId.GET_QUOTE],
            )
        cap = self._capabilities.get(BrokerCapabilityId.GET_QUOTE)
        if not cap or getattr(cap, "availability", "UNAVAILABLE") != "AVAILABLE":
            return StandardResponse(
                status="error",
                error=BrokerError(
                    code=BrokerErrorCode.BROKER_CAPABILITY_UNAVAILABLE,
                    message="Capability unavailable",
                ),
            )
        return StandardResponse(
            status="success", data=self._fixtures.get(BrokerCapabilityId.GET_QUOTE)
        )
