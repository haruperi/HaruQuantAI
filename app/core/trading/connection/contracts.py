"""Domain value objects and contracts for trading broker connection and IPC.

Description:
    Defines canonical trading domain value objects, broker connection state,
    account and terminal snapshots, open positions, active and historical orders,
    execution deals, and IPC request/receipt lifecycle records for live and
    simulated trading backends.

Purpose:
    FEAT-TRADING-CONNECTION-CONTRACTS: Core trading and broker execution contracts.

Key Capabilities:
    - FR-trading-connection-orders: Strongly typed OrderInfo, PositionInfo, DealInfo contracts.
    - FR-trading-connection-requests: TradeRequest, TradeResult, TradeCheckResult lifecycle contracts.
    - FR-trading-connection-account: AccountInfo and TerminalInfo snapshot contracts.
    - FR-trading-connection-bridge: BridgeError, BridgeEvent, Receipt, and TradingBackend protocol.

Python API Usage:
    ```python
    from app.core.trading.connection.contracts import (
        AccountInfo,
        BridgeError,
        OrderInfo,
        PositionInfo,
        TradeRequest,
        TradeResult,
    )
    ```

CLI Usage:
    ```bash
    uv run pytest tests/core/trading/connection/test_contracts.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from app.core.enums import (
    AccountTradeMode,
    DealEntry,
    DealType,
    MarginMode,
    OrderFilling,
    OrderState,
    OrderTime,
    OrderType,
    PositionType,
    ReceiptStatus,
    StopoutMode,
    TradeAction,
)
from app.core.host.logging import get_logger

logger = get_logger(__name__)

READ_TIMEOUT: float = 60.0


def _enum_titles(enum_cls: Any) -> dict[Any, str]:
    """Build title-cased description mapping for an enum class."""
    return {item: item.name.replace("_", " ").title() for item in enum_cls}


ORDER_TYPE_DESCRIPTIONS: dict[OrderType, str] = _enum_titles(OrderType)
POSITION_TYPE_DESCRIPTIONS: dict[PositionType, str] = _enum_titles(PositionType)
ORDER_STATE_DESCRIPTIONS: dict[OrderState, str] = _enum_titles(OrderState)
DEAL_TYPE_DESCRIPTIONS: dict[DealType, str] = _enum_titles(DealType)
DEAL_ENTRY_DESCRIPTIONS: dict[DealEntry, str] = _enum_titles(DealEntry)
ORDER_FILLING_DESCRIPTIONS: dict[OrderFilling, str] = {
    OrderFilling.FOK: "Fill or Kill",
    OrderFilling.IOC: "Immediate or Cancel",
    OrderFilling.RETURN: "Return",
    OrderFilling.BOC: "Book or Cancel",
}
ORDER_TIME_DESCRIPTIONS: dict[OrderTime, str] = {
    OrderTime.GTC: "Good Till Cancelled",
    OrderTime.DAY: "Day",
    OrderTime.SPECIFIED: "Specified",
    OrderTime.SPECIFIED_DAY: "Specified Day",
}


class BridgeError(RuntimeError):
    """Base runtime exception for broker and market data bridge operations."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "BRIDGE_ERROR",
        command_id: str | None = None,
        uncertain: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.command_id = command_id
        self.uncertain = uncertain


@dataclass(frozen=True, slots=True)
class PropertyValue:
    """Container for a typed scalar property query result or failure."""

    ok: bool
    value: Any = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Receipt:
    """Immutable audit record tracking the lifecycle of an IPC command."""

    command_id: str
    object_id: str
    class_name: str
    method_name: str
    status: ReceiptStatus
    created_at: float
    sent_at: float | None = None
    acknowledged_at: float | None = None
    resolved_at: float | None = None
    native_request_id: int | None = None
    value: Any = None
    meta: Mapping[str, Any] = field(default_factory=dict)
    error: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BridgeEvent:
    """Parsed asynchronous event dispatched from the trading bridge."""

    event_type: str
    payload: Mapping[str, Any]
    command_id: str | None = None
    request_id: int | None = None


@runtime_checkable
class TradingBackend(Protocol):
    """Async execution capability consumed by trading and market data APIs."""

    async def start(self) -> None:
        """Backend capability: start."""

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        """Backend capability: wait connected."""

    async def close(self) -> None:
        """Backend capability: close."""

    def arm(self) -> None:
        """Backend capability: arm."""

    def disarm(self) -> None:
        """Backend capability: disarm."""

    def last_command_id(self) -> str | None:
        """Backend capability: last command id."""

    def receipt(self, command_id: str) -> Receipt | None:
        """Backend capability: receipt."""

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        """Backend capability: next event."""

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Backend capability: await request event."""

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> Any:
        """Backend capability: call."""


@dataclass(slots=True)
class AccountInfo:
    """Atomic state of account balance, margin, leverage, and trading permissions."""

    login: int = 0
    trade_mode: AccountTradeMode = AccountTradeMode.DEMO
    leverage: int = 100
    stopout_mode: StopoutMode = StopoutMode.PERCENT
    margin_mode: MarginMode = MarginMode.RETAIL_HEDGING
    trade_allowed: bool = True
    trade_expert: bool = True
    limit_orders: int = 0
    balance: float = 10_000.0
    credit: float = 0.0
    profit: float = 0.0
    equity: float = 10_000.0
    margin: float = 0.0
    free_margin: float = 10_000.0
    margin_level: float = 0.0
    margin_call: float = 50.0
    margin_stop_out: float = 20.0
    name: str = "Simulation"
    server: str = "Simulation"
    currency: str = "USD"
    company: str = "HaruQuantAI"
    currency_digits: int = 2
    fifo_close: bool = False
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    assets: float = 0.0
    liabilities: float = 0.0
    commission_blocked: float = 0.0
    trade_mode_description: str = ""
    stopout_mode_description: str = ""
    margin_mode_description: str = ""


@dataclass(slots=True)
class TerminalInfo:
    """Atomic state of terminal connectivity, paths, and platform metadata."""

    build: int = 0
    connected: bool = True
    dlls_allowed: bool = False
    trade_allowed: bool = True
    email_enabled: bool = False
    ftp_enabled: bool = False
    max_bars: int = 100_000
    code_page: int = 65001
    cpu_cores: int = 1
    memory_physical: int = 0
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    is_x64: bool = True
    opencl_support: int = 0
    disk_space: int = 0
    language: str = "English"
    name: str = "HaruQuantAI Simulator"
    company: str = "HaruQuantAI"
    path: str = ""
    data_path: str = ""
    common_data_path: str = ""
    community_account: bool = False
    community_connection: bool = False
    tradeapi_disabled: bool = False
    notifications_enabled: bool = False
    mqid: bool = False
    ping_last: int = 0
    community_balance: float = 0.0
    retransmission: float = 0.0


@dataclass(slots=True)
class PositionInfo:
    """Atomic state of an open market position."""

    ticket: int = 0
    identifier: int = 0
    symbol: str = ""
    position_type: int = 0
    type_description: str = ""
    volume: float = 0.0
    price_open: float = 0.0
    price_current: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    magic: int = 0
    comment: str = ""
    time: int = 0
    time_msc: int = 0
    time_update: int = 0
    time_update_msc: int = 0


@dataclass(slots=True)
class OrderInfo:
    """Atomic state of an active or historical trade order."""

    ticket: int = 0
    symbol: str = ""
    order_type: int = 0
    type_description: str = ""
    state: int = 0
    state_description: str = ""
    volume_initial: float = 0.0
    volume_current: float = 0.0
    price_open: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    price_current: float = 0.0
    price_stop_limit: float = 0.0
    time_setup: int = 0
    time_setup_msc: int = 0
    time_done: int = 0
    time_done_msc: int = 0
    time_expiration: int = 0
    type_filling: int = 0
    type_filling_description: str = ""
    type_time: int = 0
    type_time_description: str = ""
    magic: int = 0
    position_id: int = 0
    position_by_id: int = 0
    comment: str = ""
    reason: int = 0


@dataclass(slots=True)
class DealInfo:
    """Atomic state of an executed trade deal."""

    ticket: int = 0
    order: int = 0
    position_id: int = 0
    symbol: str = ""
    deal_type: int = 0
    type_description: str = ""
    entry: int = 0
    entry_description: str = ""
    volume: float = 0.0
    price: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    fee: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    magic: int = 0
    reason: int = 0
    comment: str = ""
    time: int = 0
    time_msc: int = 0


@dataclass(slots=True)
class TradeRequest:
    """Strongly typed trading operation parameters."""

    action: TradeAction = TradeAction.DEAL
    magic: int = 0
    order: int = 0
    symbol: str = ""
    volume: float = 0.0
    price: float = 0.0
    stoplimit: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    deviation: int = 0
    order_type: OrderType = OrderType.BUY
    type_filling: OrderFilling = OrderFilling.FOK
    type_time: OrderTime = OrderTime.GTC
    expiration: datetime | None = None
    comment: str = ""
    position: int = 0
    position_by: int = 0


@dataclass(slots=True)
class TradeResult:
    """Strongly typed result of a sent trade operation."""

    retcode: int = 0
    deal: int = 0
    order: int = 0
    volume: float = 0.0
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    comment: str = ""
    request_id: int = 0
    retcode_external: int = 0
    retcode_description: str = ""
    raw: Any = None


@dataclass(slots=True)
class TradeCheckResult:
    """Strongly typed result of pre-trade checks."""

    retcode: int = 0
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    comment: str = ""
    raw: Any = None


def normalize_request(data: TradeRequest | dict[str, Any]) -> TradeRequest:
    """Normalize request mappings, native aliases, and UTC expiration times."""
    if isinstance(data, TradeRequest):
        if data.expiration is not None and data.expiration.tzinfo is None:
            raise ValueError("trading datetimes must include a timezone")
        return data
    action_val = data.get("action", TradeAction.DEAL)
    action = (
        action_val
        if isinstance(action_val, TradeAction)
        else TradeAction(int(action_val))
    )
    order_type_val = data.get("type", data.get("order_type", OrderType.BUY))
    order_type = (
        order_type_val
        if isinstance(order_type_val, OrderType)
        else OrderType(int(order_type_val))
    )
    filling_val = data.get("type_filling", OrderFilling.FOK)
    filling = (
        filling_val
        if isinstance(filling_val, OrderFilling)
        else OrderFilling(int(filling_val))
    )
    time_val = data.get("type_time", OrderTime.GTC)
    type_time = (
        time_val if isinstance(time_val, OrderTime) else OrderTime(int(time_val))
    )

    exp_val = data.get("expiration")
    expiration: datetime | None = None
    if isinstance(exp_val, datetime):
        if exp_val.tzinfo is None:
            raise ValueError("trading datetimes must include a timezone")
        expiration = exp_val
    elif isinstance(exp_val, (int, float)) and exp_val > 0:
        expiration = datetime.fromtimestamp(float(exp_val), tz=UTC)

    return TradeRequest(
        action=action,
        magic=int(data.get("magic", 0)),
        order=int(data.get("order", 0)),
        symbol=str(data.get("symbol", "")),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        stoplimit=float(data.get("stoplimit", 0.0)),
        sl=float(data.get("sl", 0.0)),
        tp=float(data.get("tp", 0.0)),
        deviation=int(data.get("deviation", 0)),
        order_type=order_type,
        type_filling=filling,
        type_time=type_time,
        expiration=expiration,
        comment=str(data.get("comment", "")),
        position=int(data.get("position", 0)),
        position_by=int(data.get("position_by", 0)),
    )


__all__ = [
    "DEAL_ENTRY_DESCRIPTIONS",
    "DEAL_TYPE_DESCRIPTIONS",
    "ORDER_FILLING_DESCRIPTIONS",
    "ORDER_STATE_DESCRIPTIONS",
    "ORDER_TIME_DESCRIPTIONS",
    "ORDER_TYPE_DESCRIPTIONS",
    "POSITION_TYPE_DESCRIPTIONS",
    "READ_TIMEOUT",
    "AccountInfo",
    "BridgeError",
    "BridgeEvent",
    "DealInfo",
    "OrderInfo",
    "PositionInfo",
    "PropertyValue",
    "Receipt",
    "TerminalInfo",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "TradingBackend",
    "normalize_request",
]
