"""Base broker client architecture, HTTP transport, and provider registry.

Description:
    Provides the foundational BrokerClient base class for all market data providers,
    TradingClient for execution-capable brokers, bounded HTTP session pooling with
    retry backoff, rate limiting, and credential redaction, plus lazy provider
    registry resolution.

Purpose:
    FEAT-BROKER-BASE: Foundational broker client abstractions, HTTP transport, and registry.

Key Capabilities:
    - FR-BROKER-BASE-CLIENT: Uniform market data retrieval and symbol metadata queries.
      Associated: `BrokerClient.get_bars()`, `BrokerClient.get_ticks()`,
        `BrokerClient.get_symbol_info()`, `BrokerClient.get_terminal_info()`.
      Logging: DEBUG execution lifecycle and queries through provider logger.
    - FR-BROKER-BASE-TRADING: Execution, order placement, and margin calculations.
      Associated: `TradingClient.order_send()`, `TradingClient.order_check()`,
        `TradingClient.calc_margin()`, `TradingClient.calc_profit()`.
      Logging: DEBUG order and account execution operations.
    - FR-BROKER-BASE-LIFECYCLE: Connection session management, arming, and receipts.
      Associated: `BrokerClient.connect()`, `BrokerClient.disconnect()`,
        `TradingClient.arm()`, `TradingClient.disarm()`, `TradingClient.receipt()`.
      Logging: DEBUG connection and arming status changes.
    - FR-BROKER-HTTP-SESSION: Connection pooling and exponential retry backoff.
      Associated: `create_http_session()`.
      Logging: DEBUG session creation with retry policy metadata.
    - FR-BROKER-HTTP-EXECUTE: Bounded GET execution with timeout, size, and redaction.
      Associated: `execute_bounded_get()`, `RateLimiter.acquire()`, `redact_url_or_message()`.
      Logging: DEBUG request latency and response code metrics.

Python API Usage:
    ```python
    from app.services.brokers.base import (
        BrokerClient,
        TradingClient,
        create_http_session,
        execute_bounded_get,
    )
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/ --no-cov
    ```
"""

from __future__ import annotations

import contextlib
import contextvars
import fnmatch
import importlib
import inspect
import re
import threading
import time
import uuid
from collections.abc import Awaitable
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, ClassVar, Self

import app.services.include.contracts as _contracts
import app.services.include.enums as _enums
import requests
from app.host.logging import get_logger
from app.services.include.contracts import (
    AccountInfo,
    BookInfo,
    BridgeError,
    BridgeEvent,
    DealInfo,
    MarketBar,
    MarketTick,
    OrderInfo,
    PositionInfo,
    Receipt,
    SymbolInfo,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.services.include.enums import (
    OrderFilling,
    OrderTime,
    OrderType,
    ReceiptStatus,
    Timeframe,
    TradeAction,
)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger(__name__)

SESSION_FR = "FR-BROKER-HTTP-SESSION"
EXECUTE_FR = "FR-BROKER-HTTP-EXECUTE"
REDACTION_FR = "FR-BROKER-HTTP-REDACTION"

MAX_RESPONSE_BYTES = 50 * 1024 * 1024  # 50 MB

__all__ = [
    "BridgeError",
    "BrokerClient",
    "MAX_RESPONSE_BYTES",
    "RateLimiter",
    "TradingClient",
    "create_http_session",
    "epoch_millis",
    "epoch_seconds",
    "execute_bounded_get",
    "get_broker",
    "normalize_broker_name",
    "normalize_provider_id",
    "redact_url_or_message",
    "utc_now",
]

_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|auth)=([^& \t\r\n]+)"
)
_USERINFO_PATTERN = re.compile(r"://([^:/@]+):([^@]+)@")


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(tz=UTC)


def epoch_seconds(value: datetime | float | None) -> int:
    """Convert an optional datetime or numeric timestamp to integer epoch seconds."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value) if value < 100_000_000_000 else int(value // 1000)
    dt = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return int(dt.timestamp())


def epoch_millis(value: datetime | float | None) -> int:
    """Convert an optional datetime or numeric timestamp to integer epoch milliseconds."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value * 1000) if value < 100_000_000_000 else int(value)
    dt = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return int(dt.timestamp() * 1000)


def redact_url_or_message(text: str) -> str:
    """Redact sensitive query parameters, credentials, and tokens from URLs and errors."""
    if not text:
        return ""
    return _USERINFO_PATTERN.sub(
        r"://***:***@", _SECRET_PATTERN.sub(r"\1=REDACTED", text)
    )


class RateLimiter:
    """Thread-safe rate limiter pacing outbound HTTP requests."""

    def __init__(self, rps: float = 5.0) -> None:
        self.rps = max(0.1, rps)
        self.interval = 1.0 / self.rps
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until pacing interval is met."""
        with self._lock:
            elapsed = time.monotonic() - self._last_call
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self._last_call = time.monotonic()


def create_http_session(
    user_agent: str,
    *,
    retries: int = 3,
    backoff: float = 0.3,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
    pool_size: int = 10,
) -> requests.Session:
    """Create a hardened requests.Session configured with standard retries and timeouts."""
    session = requests.Session()
    session.headers.update(
        {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate", "Accept": "*/*"}
    )
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy, pool_connections=pool_size, pool_maxsize=pool_size
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    logger.debug(
        "%s: Created requests.Session (retries=%d, backoff=%.2f, pool=%d)",
        SESSION_FR,
        retries,
        backoff,
        pool_size,
        extra={"fr_id": SESSION_FR, "retries": retries},
    )
    return session


def execute_bounded_get(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | tuple[float, float] = (5.0, 20.0),
    deadline_seconds: float | None = None,
    provider: str = "",
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> requests.Response:
    """Execute an HTTP GET request with deadline, size limit, and redacted errors."""
    del provider
    safe_url = redact_url_or_message(url)
    t0 = time.perf_counter()
    deadline_start = time.monotonic()

    try:
        if deadline_seconds is not None:
            time_left = deadline_seconds - (time.monotonic() - deadline_start)
            if time_left <= 0:
                msg = f"Overall deadline of {deadline_seconds:.1f}s exceeded before dispatch for {safe_url}"
                raise BridgeError(msg, code="TIMEOUT")
            timeout = (
                (min(timeout[0], time_left), min(timeout[1], time_left))
                if isinstance(timeout, tuple)
                else min(timeout, time_left)
            )

        resp = session.get(url, params=params, headers=headers, timeout=timeout)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        if (
            deadline_seconds is not None
            and (time.monotonic() - deadline_start) > deadline_seconds
        ):
            msg = f"Overall deadline of {deadline_seconds:.1f}s exceeded after request to {safe_url}"
            raise BridgeError(msg, code="TIMEOUT")

        cl_header = resp.headers.get("Content-Length")
        if cl_header and cl_header.isdigit() and int(cl_header) > max_bytes:
            msg = f"HTTP response Content-Length exceeds budget: {cl_header} > {max_bytes} for {safe_url}"
            raise BridgeError(msg, code="DATA_LIMIT_EXCEEDED")
        if len(resp.content) > max_bytes:
            msg = f"HTTP response body size exceeds budget: {len(resp.content)} > {max_bytes} for {safe_url}"
            raise BridgeError(msg, code="DATA_LIMIT_EXCEEDED")
        if resp.status_code == 429:
            raise BridgeError(f"Rate limit exceeded on {safe_url}", code="RATE_LIMIT")
        if resp.status_code in (401, 403):
            msg = f"Upstream authentication rejected by {safe_url} (HTTP {resp.status_code})"
            raise BridgeError(msg, code="AUTHENTICATION")

        logger.debug(
            "%s: GET %s -> %d in %.1f ms",
            EXECUTE_FR,
            safe_url,
            resp.status_code,
            elapsed_ms,
            extra={
                "fr_id": EXECUTE_FR,
                "url": safe_url,
                "status_code": resp.status_code,
                "latency_ms": elapsed_ms,
            },
        )
        return resp
    except requests.exceptions.Timeout as exc:
        safe_exc = redact_url_or_message(str(exc))
        raise BridgeError(
            f"HTTP request timed out for {safe_url}: {safe_exc}", code="TIMEOUT"
        ) from exc
    except requests.exceptions.RequestException as exc:
        safe_msg = redact_url_or_message(str(exc))
        raise BridgeError(
            f"HTTP network error for {safe_url}: {safe_msg}", code="TIMEOUT"
        ) from exc
    except BridgeError:
        raise
    except Exception as exc:
        safe_msg = redact_url_or_message(str(exc))
        raise BridgeError(
            f"HTTP error for {safe_url}: {safe_msg}", code="BRIDGE_ERROR"
        ) from exc


class BrokerClient:
    """Uniform base client for all market data and broker providers."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = get_logger(f"app.services.brokers.{name.lower()}")
        self._connected: bool = False

    def connect(self) -> bool:
        """Establish connection to the broker provider."""
        self.logger.debug("Connecting client: %s", self.name)
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Terminate connection and release resources."""
        self.logger.debug("Disconnecting client: %s", self.name)
        self._connected = False
        sess = getattr(self, "session", None) or getattr(self, "_session", None)
        if sess is not None and hasattr(sess, "close") and callable(sess.close):
            with contextlib.suppress(Exception):
                sess.close()

    @property
    def is_connected(self) -> bool:
        """Return connectivity status."""
        return self._connected

    @property
    def connected(self) -> bool:
        """Return connectivity status."""
        return self._connected

    @property
    def _is_connected(self) -> bool:
        """Return connectivity status for legacy test access."""
        return self._connected

    def close_sync(self) -> None:
        """Synchronously close connection."""
        self.disconnect()

    async def close(self) -> None:
        """Asynchronously close connection."""
        self.disconnect()

    async def start(self) -> None:
        """Start or initialize provider connection session."""
        self.connect()

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        """Confirm provider readiness."""
        del timeout
        if not self._connected:
            self.connect()

    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar] | Awaitable[list[MarketBar]]:
        """Fetch historical candlestick bars. Subclasses implement directly."""
        del symbol, timeframe, date_from, date_to, start_pos, count, limit
        raise BridgeError(
            f"{self.name} does not support historical bars",
            code="UNSUPPORTED_OPERATION",
        )

    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick] | Awaitable[list[MarketTick]]:
        """Fetch historical market ticks. Subclasses implement directly."""
        del symbol, date_from, date_to, count, limit
        raise BridgeError(
            f"{self.name} does not support tick history", code="UNSUPPORTED_OPERATION"
        )

    async def stream(
        self,
        symbol: str,
        *,
        kind: str = "ticks",
        timeframe: Timeframe | str | None = None,
    ) -> Any:
        """Establish async streaming feed."""
        del symbol, kind, timeframe
        raise BridgeError(
            f"{self.name} does not support streaming", code="UNSUPPORTED_OPERATION"
        )

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Retrieve symbol metadata specifications."""
        return SymbolInfo(name=symbol)

    def symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Alias for get_symbol_info."""
        return self.get_symbol_info(symbol)

    def get_symbols(self) -> list[str]:
        """List available instruments."""
        return []

    def symbols_get(self) -> list[str]:
        """Alias for get_symbols."""
        return self.get_symbols()

    def get_terminal_info(self) -> TerminalInfo:
        """Retrieve the current terminal state info."""
        return TerminalInfo(
            name=self.name, company=self.name, connected=True, trade_allowed=False
        )

    async def __aenter__(self) -> Self:
        """Enter asynchronous context manager."""
        self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit asynchronous context manager."""
        del exc_type, exc, tb
        self.disconnect()


_TRADE_NOOP_METHODS = frozenset(
    "SetExpertMagicNumber SetDeviationInPoints SetTypeFilling SetTypeFillingBySymbol "
    "SetAsyncMode SetMarginMode LogLevel PrintRequest PrintResult".split()
)


class TradingClient(BrokerClient):
    """Trading-capable broker client supporting account, order, and position operations."""

    _COLLECTION_SPECS: ClassVar[
        dict[str, tuple[str, str, type[Any], str, tuple[str, ...], tuple[str, ...]]]
    ] = {
        "PositionInfo": (
            "get_positions",
            "_selected_position",
            PositionInfo,
            "PositionsTotal",
            ("PositionsGet", "positions"),
            ("PositionGetTicket", "PositionSelectByTicket", "SelectByTicket"),
        ),
        "OrderInfo": (
            "get_orders",
            "_selected_order",
            OrderInfo,
            "OrdersTotal",
            ("OrdersGet", "orders"),
            ("OrderGetTicket", "OrderSelect", "Select", "SelectByTicket"),
        ),
        "HistoryOrderInfo": (
            "get_history_orders",
            "_selected_history_order",
            OrderInfo,
            "HistoryOrdersTotal",
            ("HistoryOrdersGet", "orders"),
            tuple(
                "HistoryOrderGetTicket HistoryOrderSelect Select SelectByTicket Ticket".split()
            ),
        ),
        "DealInfo": (
            "get_deals",
            "_selected_deal",
            DealInfo,
            "HistoryDealsTotal",
            ("HistoryDealsGet", "deals"),
            tuple(
                "HistoryDealGetTicket HistoryDealSelect Select SelectByTicket Ticket".split()
            ),
        ),
    }

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._armed: bool = False
        self._last_cmd: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            f"{name}_last_cmd", default=None
        )
        self._last_cmd_id: str | None = None
        self._receipts: dict[str, Receipt] = {}
        self._current_symbol: str = "EURUSD"
        self._selected_position: Any = None
        self._selected_order: Any = None
        self._selected_history_order: Any = None
        self._selected_deal: Any = None

    def arm(self) -> None:
        """Arm client for live trade execution."""
        self._armed = True
        self.logger.debug("Client armed: %s", self.name)

    def disarm(self) -> None:
        """Disarm client to reject trade execution."""
        self._armed = False
        self.logger.debug("Client disarmed: %s", self.name)

    @property
    def is_armed(self) -> bool:
        """Return whether client is armed for execution."""
        return self._armed

    def last_command_id(self) -> str | None:
        """Return the ID of the most recent dispatched command."""
        return self._last_cmd_id or self._last_cmd.get()

    def receipt(self, command_id: str) -> Receipt | None:
        """Return the execution receipt for a command."""
        return self._receipts.get(command_id)

    def _record_receipt(
        self, object_id: str, class_name: str, method_name: str
    ) -> tuple[str, Receipt]:
        """Create and store an initial command receipt."""
        cmd_id = f"cmd-{uuid.uuid4().hex[:12]}"
        self._last_cmd_id = cmd_id
        self._last_cmd.set(cmd_id)
        rec = Receipt(
            cmd_id,
            object_id,
            class_name,
            method_name,
            ReceiptStatus.CREATED,
            time.time(),
        )
        self._receipts[cmd_id] = rec
        return cmd_id, rec

    def _resolve_receipt(self, cmd_id: str, rec: Receipt, val: Any) -> None:
        """Mark receipt as resolved."""
        t = time.time()
        v = asdict(val) if is_dataclass(val) and not isinstance(val, type) else val
        self._receipts[cmd_id] = replace(
            rec,
            status=ReceiptStatus.RESOLVED,
            sent_at=t,
            acknowledged_at=t,
            resolved_at=t,
            value=v,
        )

    def _reject_receipt(self, cmd_id: str, rec: Receipt, exc: Exception) -> None:
        """Mark receipt as rejected."""
        t = time.time()
        err = {"code": str(getattr(exc, "code", "BROKER_ERROR")), "message": str(exc)}
        self._receipts[cmd_id] = replace(
            rec,
            status=ReceiptStatus.REJECTED,
            sent_at=t,
            acknowledged_at=t,
            resolved_at=t,
            error=err,
        )

    def get_account_info(self) -> AccountInfo | Awaitable[AccountInfo]:
        """Retrieve account state info."""
        return AccountInfo()

    def get_tick(self, name: str) -> MarketTick | None:
        """Retrieve the latest market tick for symbol."""
        del name
        return None

    def select_symbol(self, name: str, selected: bool) -> bool:
        """Select or unselect a symbol in Market Watch."""
        del name, selected
        return True

    def subscribe_book(self, name: str) -> bool:
        """Subscribe to order book updates."""
        del name
        return False

    def get_book(self, name: str) -> tuple[BookInfo, ...]:
        """Retrieve the current order book."""
        del name
        return ()

    def release_book(self, name: str) -> bool:
        """Release order book subscription."""
        del name
        return True

    def get_positions(self) -> list[PositionInfo] | Awaitable[list[PositionInfo]]:
        """Retrieve open market positions."""
        return []

    def get_orders(self) -> list[OrderInfo] | Awaitable[list[OrderInfo]]:
        """Retrieve working orders."""
        return []

    def get_history_orders(self) -> list[OrderInfo] | Awaitable[list[OrderInfo]]:
        """Retrieve historical completed/canceled orders."""
        return []

    def get_deals(self) -> list[DealInfo] | Awaitable[list[DealInfo]]:
        """Retrieve historical execution deals."""
        return []

    def order_send(self, request: TradeRequest) -> TradeResult | Awaitable[TradeResult]:
        """Execute or place an order transaction against the backend."""
        del request
        raise BridgeError(
            f"{self.name} does not support order execution",
            code="UNSUPPORTED_OPERATION",
        )

    def order_check(
        self, request: TradeRequest
    ) -> TradeCheckResult | Awaitable[TradeCheckResult]:
        """Pre-validate a trade request and calculate margin requirements."""
        del request
        return TradeCheckResult()

    def calc_margin(
        self, order_type: OrderType, symbol: str, volume: float, price: float
    ) -> float | Awaitable[float]:
        """Calculate required margin for an order."""
        del order_type, symbol, volume, price
        return 0.0

    def calc_profit(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | Awaitable[float]:
        """Calculate hypothetical floating or realized profit for an order."""
        del order_type, symbol, volume, price_open, price_close
        return 0.0

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        """Default event poll stub."""
        del timeout
        raise NotImplementedError(
            f"{self.name} does not emit asynchronous transaction events"
        )

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Default event correlation stub."""
        del request_id, timeout
        raise NotImplementedError(
            f"{self.name} does not emit asynchronous transaction events"
        )

    async def call(
        self,
        *,
        object_id: str = "broker",
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> Any:
        """Execute a broker command over backend transport with receipt auditing."""
        del requires_arm, timeout
        cmd_id, rec = self._record_receipt(object_id, class_name, method_name)
        try:
            val = self._dispatch(class_name, method_name, args)
            if inspect.isawaitable(val):
                val = await val
            self._resolve_receipt(cmd_id, rec, val)
            return val
        except Exception as exc:
            self._reject_receipt(cmd_id, rec, exc)
            raise

    @staticmethod
    def _lookup_case_insensitive_attr(
        obj: Any, method_name: str, default: Any = None
    ) -> Any:
        """Resolve an attribute on `obj` case-insensitively."""
        target = method_name.lower()
        for attr in dir(obj):
            if attr.lower() == target and not attr.startswith("_"):
                return getattr(obj, attr)
        return getattr(obj, method_name, default)

    def _dispatch_collection(
        self, class_name: str, method_name: str, args: list[Any]
    ) -> Any:
        """Dispatch collection queries and cursor selections for positions, orders, and deals."""
        getter_name, sel_attr, default_cls, total_m, list_ms, ticket_ms = (
            self._COLLECTION_SPECS[class_name]
        )
        raw = getattr(self, getter_name)()
        items = raw if isinstance(raw, list) else []

        if method_name == total_m:
            return len(items)
        if method_name in list_ms:
            if (
                class_name == "PositionInfo"
                and args
                and isinstance(args[0], str)
                and args[0]
            ):
                return [p for p in items if getattr(p, "symbol", "") == args[0]]
            return items
        if method_name in (class_name, "info"):
            selected = getattr(self, sel_attr)
            return (
                selected
                if selected is not None
                else (items[0] if items else default_cls())
            )
        if method_name == "SelectByIndex":
            idx = int(args[0]) if args else 0
            if 0 <= idx < len(items):
                setattr(self, sel_attr, items[idx])
                return True
            return False
        if method_name in ticket_ms:
            ticket = int(args[0]) if args else 0
            hit = next((i for i in items if getattr(i, "ticket", 0) == ticket), None)
            if hit is not None:
                setattr(self, sel_attr, hit)
                return True
            return False
        if class_name == "PositionInfo" and method_name in ("Select", "SelectByMagic"):
            sym = str(args[0]) if args else ""
            magic = int(args[1]) if len(args) > 1 else 0
            hit = next(
                (
                    p
                    for p in items
                    if getattr(p, "symbol", "") == sym
                    and (method_name == "Select" or getattr(p, "magic", 0) == magic)
                ),
                None,
            )
            if hit is not None:
                self._selected_position = hit
                return True
            return False
        if class_name in ("PositionInfo", "OrderInfo") and method_name in (
            "StoreState",
            "CheckState",
        ):
            return True
        raise BridgeError(
            f"{self.name} does not support {class_name}.{method_name}",
            code="UNSUPPORTED_OPERATION",
        )

    def _dispatch(self, class_name: str, method_name: str, args: list[Any]) -> Any:
        """Route generic calls directly to TradingClient typed methods."""
        if class_name == "TerminalInfo":
            t = self.get_terminal_info()
            if method_name in ("TerminalInfo", "info"):
                return t
            return self._lookup_case_insensitive_attr(t, method_name, default=t)

        if class_name == "AccountInfo":
            acc = self.get_account_info()
            if method_name in ("AccountInfo", "info"):
                return acc
            if method_name in ("OrderProfitCheck", "MarginCheck"):
                sym = str(args[0]) if len(args) > 0 else "EURUSD"
                otype = OrderType(int(args[1])) if len(args) > 1 else OrderType.BUY
                vol = float(args[2]) if len(args) > 2 else 1.0
                p1 = float(args[3]) if len(args) > 3 else 0.0
                if method_name == "MarginCheck":
                    return self.calc_margin(otype, sym, vol, p1)
                p2 = float(args[4]) if len(args) > 4 else 0.0
                return self.calc_profit(otype, sym, vol, p1, p2)
            if method_name == "FreeMarginCheck":
                if inspect.isawaitable(acc):

                    async def _free(awaitable: Any) -> float:
                        return float(getattr(await awaitable, "margin_free", 0.0))

                    return _free(acc)
                return float(getattr(acc, "margin_free", 0.0))
            if method_name == "MaxLotCheck":
                return 100.0
            return self._lookup_case_insensitive_attr(acc, method_name)

        if class_name == "SymbolInfo":
            sym = (
                args[0]
                if args and isinstance(args[0], str)
                else getattr(self, "_current_symbol", "EURUSD")
            )
            if method_name in ("SymbolInfo", "info"):
                return self.get_symbol_info(sym)
            if method_name == "SymbolsTotal":
                return len(self.get_symbols())
            if method_name in ("SymbolsGet", "symbols"):
                all_syms = self.get_symbols()
                if args and isinstance(args[0], str) and args[0]:
                    tokens = [p.strip() for p in args[0].split(",") if p.strip()]
                    inc = [p for p in tokens if not p.startswith("!")]
                    exc = [p[1:] for p in tokens if p.startswith("!")]
                    return [
                        s
                        for s in all_syms
                        if (not inc or any(fnmatch.fnmatch(s, p) for p in inc))
                        and not any(fnmatch.fnmatch(s, p) for p in exc)
                    ]
                return all_syms
            if method_name == "SymbolInfoTick":
                return self.get_tick(sym)
            if method_name == "SymbolSelect":
                return self.select_symbol(sym, bool(args[1]) if len(args) > 1 else True)
            if method_name in ("MarketBookAdd", "subscribe_book"):
                return self.subscribe_book(sym)
            if method_name in ("MarketBookRelease", "release_book"):
                return self.release_book(sym)
            if method_name in ("MarketBookGet", "get_book"):
                return self.get_book(sym)
            if method_name in ("Refresh", "RefreshRates", "IsSynchronized"):
                return True
            if method_name == "NormalizePrice":
                return round(
                    float(args[0]) if args else 0.0,
                    int(args[1]) if len(args) > 1 else 5,
                )
            if method_name in ("Name", "Select"):
                if args and isinstance(args[0], str):
                    self._current_symbol = args[0]
                    return self.get_symbol_info(args[0]) is not None
                return (
                    getattr(self, "_current_symbol", "EURUSD")
                    if method_name == "Name"
                    else True
                )
            return self._lookup_case_insensitive_attr(
                self.get_symbol_info(sym), method_name
            )

        if class_name in self._COLLECTION_SPECS:
            return self._dispatch_collection(class_name, method_name, args)

        if class_name == "Trade":
            if method_name == "OrderSend":
                return self.order_send(
                    self._coerce_trade_request(args[0] if args else None)
                )
            if method_name == "OrderCheck":
                return self.order_check(
                    self._coerce_trade_request(args[0] if args else None)
                )
            if method_name in _TRADE_NOOP_METHODS:
                return True
            if method_name in ("FormatRequest", "FormatRequestResult"):
                return ""
            defaults = {
                "Request": TradeRequest,
                "Result": TradeResult,
                "CheckResult": TradeCheckResult,
            }
            if method_name in defaults:
                return defaults[method_name]()

        if class_name in ("MarketDepth", "Book"):
            sym = str(args[0]) if args else getattr(self, "_current_symbol", "EURUSD")
            if method_name in ("Subscribe", "MarketBookAdd"):
                return self.subscribe_book(sym)
            if method_name in ("Get", "MarketBookGet"):
                return self.get_book(sym)
            if method_name in ("Release", "MarketBookRelease"):
                return self.release_book(sym)

        raise BridgeError(
            f"{self.name} does not support {class_name}.{method_name}",
            code="UNSUPPORTED_OPERATION",
        )

    def _coerce_trade_request(self, req: Any) -> Any:
        if req is None:
            return TradeRequest()
        if isinstance(req, dict):
            act = req.get("action", TradeAction.DEAL)
            otype = req.get("order_type", OrderType.BUY)
            fill = req.get("type_filling", OrderFilling.FOK)
            ttime = req.get("type_time", OrderTime.GTC)
            return TradeRequest(
                action=TradeAction(act) if isinstance(act, int) else act,
                magic=int(req.get("magic", 0)),
                order=int(req.get("order", 0)),
                symbol=str(req.get("symbol", "")),
                volume=float(req.get("volume", 0.0)),
                price=float(req.get("price", 0.0)),
                stoplimit=float(req.get("stoplimit", 0.0)),
                sl=float(req.get("sl", 0.0)),
                tp=float(req.get("tp", 0.0)),
                deviation=int(req.get("deviation", 0)),
                order_type=OrderType(otype) if isinstance(otype, int) else otype,
                type_filling=OrderFilling(fill) if isinstance(fill, int) else fill,
                type_time=OrderTime(ttime) if isinstance(ttime, int) else ttime,
                expiration=req.get("expiration"),
                comment=str(req.get("comment", "")),
                position=int(req.get("position", 0)),
                position_by=int(req.get("position_by", 0)),
            )
        return req


_SINGLETONS: dict[str, Any] = {}
_SINGLETON_FACTORIES: dict[str, tuple[str, str]] = {
    "yahoo": ("yahoo", "YahooClient"),
    "dukascopy": ("dukascopy", "DukascopyClient"),
    "darwinex": ("darwinex", "DarwinexClient"),
    "sq_equity": ("sq_equity", "SQEquityClient"),
    "sq_futures": ("sq_futures", "SQFuturesClient"),
    "crypto": ("crypto", "CryptoClient"),
    "binance": ("crypto", "BinanceClient"),
    "files": ("files", "FilesClient"),
    "tick_downloader": ("tick_downloader", "TickDownloaderClient"),
    "metatrader": ("metatrader", "MetaTraderClient"),
    "ctrader": ("ctrader", "CTraderClient"),
    "simulator": ("simulator", "SimulatorClient"),
    "live_test": ("registry", "LiveTest"),
}
_CLASS_TO_MODULE: dict[str, str] = {
    cls_name: mod for mod, cls_name in _SINGLETON_FACTORIES.values()
} | {
    "BrokerClient": "base",
    "TradingClient": "base",
    "BridgeError": "base",
    "BitfinexClient": "crypto",
    "CoinbaseClient": "crypto",
    "PoloniexClient": "crypto",
    "LiveTestCLI": "registry",
}
_PROVIDER_ALIASES = {
    "strategyquant_equity": "sq_equity",
    "strategyquant_futures": "sq_futures",
    "csv": "files",
    "parquet": "files",
    "local": "files",
    "yahoo_finance": "yahoo",
    "yfinance": "yahoo",
    "mt5": "metatrader",
}


def normalize_provider_id(name: str) -> str:
    """Normalize broker name or alias to canonical identifier."""
    cleaned = name.lower().strip().replace("-", "_").replace(" ", "_")
    for suffix in ("_broker", "_backend", "_client"):
        cleaned = cleaned.removesuffix(suffix)
    return _PROVIDER_ALIASES.get(cleaned, cleaned)


def normalize_broker_name(name: str) -> str:
    """Backward-compatible alias for normalize_provider_id."""
    return normalize_provider_id(name)


def get_broker(name: str, registry: Any = None) -> Any:
    """Resolve a broker singleton by name or alias."""
    del registry
    target = normalize_provider_id(name)
    if target not in _SINGLETON_FACTORIES:
        raise KeyError(f"Unknown broker: {name}")
    if target not in _SINGLETONS:
        mod_name, cls_name = _SINGLETON_FACTORIES[target]
        mod = importlib.import_module(f"app.services.brokers.{mod_name}")
        _SINGLETONS[target] = getattr(mod, cls_name)()
    return _SINGLETONS[target]


def _resolve_broker_export(name: str) -> Any:
    """Lazily import broker classes, contracts, and singletons on demand."""
    if name in _SINGLETON_FACTORIES:
        return get_broker(name)
    if name in _CLASS_TO_MODULE:
        mod = importlib.import_module(f"app.services.brokers.{_CLASS_TO_MODULE[name]}")
        return getattr(mod, name)
    for source in (_contracts, _enums):
        if hasattr(source, name):
            return getattr(source, name)
    raise AttributeError(f"module 'app.services.brokers' has no attribute {name!r}")
