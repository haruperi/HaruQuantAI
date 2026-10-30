"""Base broker client architecture and HTTP transport abstractions.

Provides the foundational BrokerClient base class for all market data providers,
TradingClient for execution-capable brokers, bounded HTTP session pooling with
retry backoff, rate limiting, and credential redaction.
"""

from __future__ import annotations

import contextlib
import contextvars
import inspect
import re
import threading
import time
import uuid
from collections.abc import Awaitable
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-untyped]

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.data.contracts import (
    AccountInfo,
    BookInfo,
    BridgeError,
    BridgeEvent,
    DealInfo,
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
from app.core.enums import (
    OrderType,
    ReceiptStatus,
    Timeframe,
)
from app.core.host.logging import get_logger
from app.core.trading.connection.trading_dispatch import TradingDispatcher

logger = get_logger(__name__)

SESSION_FR = "FR-BROKER-HTTP-SESSION"
EXECUTE_FR = "FR-BROKER-HTTP-EXECUTE"
REDACTION_FR = "FR-BROKER-HTTP-REDACTION"

MAX_RESPONSE_BYTES = 50 * 1024 * 1024  # 50 MB

__all__ = [
    "MAX_RESPONSE_BYTES",
    "BridgeError",
    "BrokerClient",
    "RateLimiter",
    "TradingClient",
    "create_http_session",
    "epoch_millis",
    "epoch_seconds",
    "execute_bounded_get",
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


def epoch_seconds(value: datetime | float | str | None) -> int:
    """Convert an optional datetime or numeric timestamp to integer epoch seconds."""
    if value is None:
        return 0
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return 0
        try:
            if v.replace(".", "", 1).isdigit():
                num = float(v)
                return int(num) if num < 100_000_000_000 else int(num // 1000)
            parsed = datetime.fromisoformat(v)
            return int(
                (
                    parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
                ).timestamp()
            )
        except ValueError, TypeError:
            return 0
    if isinstance(value, (int, float)):
        return int(value) if value < 100_000_000_000 else int(value // 1000)
    dt = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return int(dt.timestamp())


def epoch_millis(value: datetime | float | str | None) -> int:
    """Convert an optional datetime or numeric timestamp to integer epoch milliseconds."""
    if isinstance(value, (int, float)):
        return int(value * 1000) if value < 100_000_000_000 else int(value)
    return epoch_seconds(value) * 1000


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
        self.logger = get_logger(f"app.core.trading.connection.{name.lower()}")
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
    ) -> pd.DataFrame | Awaitable[pd.DataFrame]:
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
    ) -> pd.DataFrame | Awaitable[pd.DataFrame]:
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


class TradingClient(BrokerClient):
    """Trading-capable broker client supporting account, order, and position operations."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._armed: bool = False
        self._last_cmd: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            f"{name}_last_cmd", default=None
        )
        self._last_cmd_id: str | None = None
        self._receipts: dict[str, Receipt] = {}
        self._trading_dispatchers: dict[str, TradingDispatcher] = {}

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

    def _finalize_receipt(
        self, cmd_id: str, rec: Receipt, status: ReceiptStatus, **kwargs: Any
    ) -> None:
        t = time.time()
        self._receipts[cmd_id] = replace(
            rec, status=status, sent_at=t, acknowledged_at=t, resolved_at=t, **kwargs
        )

    def _resolve_receipt(self, cmd_id: str, rec: Receipt, val: Any) -> None:
        v = asdict(val) if is_dataclass(val) and not isinstance(val, type) else val
        self._finalize_receipt(cmd_id, rec, ReceiptStatus.RESOLVED, value=v)

    def _reject_receipt(self, cmd_id: str, rec: Receipt, exc: Exception) -> None:
        err = {"code": str(getattr(exc, "code", "BROKER_ERROR")), "message": str(exc)}
        self._finalize_receipt(cmd_id, rec, ReceiptStatus.REJECTED, error=err)

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
        """Retrieve historical execution deals, or reject unavailable history."""
        raise BridgeError(
            f"{self.name} does not support execution history",
            code="UNSUPPORTED_OPERATION",
        )

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
        raise BridgeError(
            f"{self.name} does not support profit calculation",
            code="UNSUPPORTED_OPERATION",
        )

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
        del timeout
        cmd_id, rec = self._record_receipt(object_id, class_name, method_name)
        try:
            if (
                requires_arm or (class_name == "Trade" and method_name == "OrderSend")
            ) and not self.is_armed:
                raise BridgeError("Trading client is not armed", code="NOT_ARMED")
            dispatcher = self._trading_dispatchers.get(object_id)
            if dispatcher is None:
                dispatcher = TradingDispatcher(self)
                self._trading_dispatchers[object_id] = dispatcher
            val = dispatcher.dispatch(class_name, method_name, args)
            if inspect.isawaitable(val):
                val = await val
            self._resolve_receipt(cmd_id, rec, val)
            return val
        except Exception as exc:
            self._reject_receipt(cmd_id, rec, exc)
            raise
