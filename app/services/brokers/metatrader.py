r"""MetaTrader MT5Backend facade, TCP bridge and wire-message codec.

Description:
    MT5Backend composes the canonical eight trading classes and delegates
    lifecycle and trade
    authorization to Bridge. Bridge owns the authenticated loopback listener,
    command correlation, receipts, timeouts, journal and events. Module helpers
    encode and decode newline-delimited JSON while preserving integer precision.
    The trading layer imports only the async backend contract, avoiding cycles.

Purpose:
    FEAT-BROKER-MT5-BRIDGE: Call native MQL5 classes through the custom EA without
    DLL bindings. Keep the facade, transport and wire codec in one module.

Key Capabilities:
    - FR-MT5-BRIDGE-FRAME-ENCODING: Encode JSON frames with integer tags.
      Associated: `encode_frame()`, `_pack()`, `Bridge.call()`
      Logging: DEBUG on every encode attempt with operation only; no payloads.
    - FR-MT5-BRIDGE-FRAME-DECODING: Restore values and validate incoming frames.
      Associated: `decode_frame()`, `_unpack()`, `Bridge._accept()`
      Logging: DEBUG on every decode attempt with operation and frame_bytes.
    - FR-MT5-MARKET-DATA: Non-blocking terminal market data retrieval for bars and ticks.
      Associated: `MetaTraderClient.get_bars()`, `MetaTraderClient.get_ticks()`,
        `MetaTraderClient.fetch_bars()`, `MetaTraderClient.fetch_ticks()`.
      Logging: DEBUG on retrieval queries.

Python API Usage:
    ```python
    from app.services.brokers.metatrader import MT5Backend
    from app.services.brokers.metatrader import decode_frame, encode_frame

    frame = encode_frame({"v": 1, "kind": "call", "args": [2**63]})
    message = decode_frame(frame.rstrip(b"\n"))
    ```
    For a configured EA, use MT5Backend's async context manager and
    wait_connected() before proxy calls. Live mutations require separate arming.

CLI Usage:
    Verify the codec without connecting to MT5 or authorizing trading.
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

import asyncio
import contextvars
import json
import secrets
import time
import uuid
from collections.abc import Awaitable, Mapping
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self, override

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger

try:
    from app.host.persistence.mt5bridge_journal import Journal  # type: ignore[import-not-found]
except ImportError:

    class Journal:  # type: ignore[no-redef]
        """Fallback MT5 journal stub."""

        def __init__(self, path: Any = None) -> None:
            pass

        def close(self) -> None:
            pass

        def add_event(self, *args: Any, **kwargs: Any) -> None:
            pass

        def create_command(self, *args: Any, **kwargs: Any) -> None:
            pass

        def mark_sent(self, *args: Any, **kwargs: Any) -> None:
            pass

        def resolve_command(self, *args: Any, **kwargs: Any) -> None:
            pass


from app.services.brokers.base import (
    BridgeError,
    TradingClient,
)
from app.services.include.contracts import (
    READ_TIMEOUT,
    BridgeEvent,
    MarketBar,
    MarketTick,
    Receipt,
    SymbolInfo,
    TerminalInfo,
)
from app.services.include.enums import (
    ReceiptStatus,
    Timeframe,
)
from app.services.include.trading import Trading

__all__ = [
    "Bridge",
    "MetaTraderClient",
    "decode_frame",
    "encode_frame",
]

logger = get_logger(__name__)

PROTOCOL_VERSION = 1
MAX_FRAME_BYTES = 1_048_576


def _pack(value: Any) -> Any:
    """Tag integers and escape reserved string prefixes recursively."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return f"@i64:{value}"
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        return "@" + value if value.startswith("@") else value
    if isinstance(value, (list, tuple)):
        return [_pack(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _pack(v) for k, v in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return _pack(asdict(value))
    if isinstance(value, datetime):
        return f"@i64:{int(value.timestamp())}"
    raise TypeError(f"unsupported wire value: {type(value).__name__}")


def _unpack(value: Any) -> Any:
    """Restore tagged integers and escaped strings recursively."""
    if isinstance(value, str):
        if value.startswith("@@"):
            return value[1:]
        if value.startswith(("@i64:", "@u64:")):
            return int(value[5:])
        return value
    if isinstance(value, list):
        return [_unpack(item) for item in value]
    if isinstance(value, dict):
        return {k: _unpack(v) for k, v in value.items()}
    return value


def encode_frame(message: dict[str, Any]) -> bytes:
    """Encode a message as a newline-delimited UTF-8 JSON frame."""
    logger.debug(
        "FR-MT5-BRIDGE-FRAME-ENCODING: encoding frame",
        extra={"operation": "encode"},
    )
    payload = json.dumps(
        _pack(message),
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(payload) > MAX_FRAME_BYTES:
        raise ValueError(f"frame exceeds {MAX_FRAME_BYTES} bytes")
    return payload + b"\n"


def decode_frame(data: bytes) -> dict[str, Any]:
    """Decode a JSON frame and validate its object shape and protocol version."""
    logger.debug(
        "FR-MT5-BRIDGE-FRAME-DECODING: decoding frame",
        extra={"operation": "decode", "frame_bytes": len(data)},
    )
    if len(data) > MAX_FRAME_BYTES:
        raise ValueError("frame too large")
    value = _unpack(json.loads(data.decode("utf-8")))
    if not isinstance(value, dict):
        # Preserve the established wire-validation exception contract.
        raise ValueError("frame must be a JSON object")
    if value.get("v") != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version: {value.get('v')!r}")
    return value


_UNCERTAIN_RETCODES = {10012, 10031}  # TRADE_RETCODE_TIMEOUT / CONNECTION


class Bridge:
    """Asyncio TCP listener used by the MT5 bridge EA.

    Python is the server; the EA is the only accepted client. Calls are correlated
    by command_id. Per-object serialization is implemented in TradingClass.
    """

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        auth_token: str,
        journal_path: str | Path | None = None,
        command_timeout: float = 10.0,
    ) -> None:
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("Bridge is intentionally loopback-only")
        if len(auth_token) < 16:
            raise ValueError("auth_token must contain at least 16 characters")
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self.command_timeout = command_timeout
        self.journal = Journal(journal_path)

        self._server: asyncio.AbstractServer | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._session_id: str | None = None
        self._connected = asyncio.Event()
        self._authenticated = False
        self._armed = False
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._receipts: dict[str, Receipt] = {}
        self._event_queue: asyncio.Queue[BridgeEvent] = asyncio.Queue()
        self._request_waiters: dict[int, list[asyncio.Future[BridgeEvent]]] = {}
        self._request_events: dict[int, list[BridgeEvent]] = {}
        self._write_lock = asyncio.Lock()
        self._last_command: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            "metatrader_last_command_id", default=None
        )

    @staticmethod
    def generate_auth_token() -> str:
        """Generate a cryptographically secure random token for EA authentication."""
        return secrets.token_urlsafe(32)

    @property
    def connected(self) -> bool:
        """Return True if the bridge TCP socket is connected and authenticated."""
        return self._connected.is_set() and self._authenticated

    @property
    def armed(self) -> bool:
        """Return True if live trading execution is armed."""
        return self._armed

    @property
    def session_id(self) -> str | None:
        """Return the current active session ID or None if disconnected."""
        return self._session_id

    def arm(self) -> None:
        """Arm the bridge to allow executing live trading commands."""
        if not self.connected:
            raise BridgeError(
                "cannot arm while the EA is disconnected", code="NOT_CONNECTED"
            )
        self._armed = True

    def disarm(self) -> None:
        """Disarm the bridge to disallow live trading execution."""
        self._armed = False

    def last_command_id(self) -> str | None:
        """Return the ID of the most recently initiated command in this context."""
        return self._last_command.get()

    def receipt(self, command_id: str) -> Receipt | None:
        """Return the receipt associated with ``command_id`` if known."""
        return self._receipts.get(command_id)

    async def start(self) -> None:
        """Start the loopback TCP server to listen for MetaTrader EA connections."""
        if self._server is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._server = await asyncio.start_server(
            self._accept, self.host, self.port, limit=MAX_FRAME_BYTES
        )

    async def close(self) -> None:
        """Close the loopback TCP connection and server, releasing resources."""
        self.disarm()
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None
        self._authenticated = False
        self._connected.clear()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        for future in list(self._pending.values()):
            if not future.done():
                future.set_exception(
                    BridgeError(
                        "bridge closed", code="CONNECTION_CLOSED", uncertain=True
                    )
                )
        self._pending.clear()
        self.journal.close()

    async def wait_connected(
        self,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> None:
        """Wait until the MetaTrader EA connects and completes authentication."""
        async with asyncio.timeout(timeout):
            await self._connected.wait()
        if not self._authenticated:
            raise BridgeError("EA connection was not authenticated", code="AUTH_FAILED")

    async def _accept(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer = writer.get_extra_info("peername")
        if peer and peer[0] not in {"127.0.0.1", "::1"}:
            writer.close()
            await writer.wait_closed()
            return

        # Enforce one active EA connection.
        if self._writer is not None and not self._writer.is_closing():
            writer.write(
                encode_frame(
                    {
                        "v": PROTOCOL_VERSION,
                        "kind": "error",
                        "code": "BRIDGE_BUSY",
                        "message": "another EA already owns this listener",
                    }
                )
            )
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        self._reader = reader
        self._writer = writer
        self._authenticated = False
        self._connected.clear()
        self._session_id = uuid.uuid4().hex
        try:
            first = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not first:
                return
            hello = decode_frame(first.rstrip(b"\r\n"))
            if hello.get("kind") != "hello" or hello.get("token") != self.auth_token:
                writer.write(
                    encode_frame(
                        {
                            "v": PROTOCOL_VERSION,
                            "kind": "error",
                            "code": "AUTH_FAILED",
                            "message": "invalid bridge token",
                        }
                    )
                )
                await writer.drain()
                return
            self._authenticated = True
            self._connected.set()
            writer.write(
                encode_frame(
                    {
                        "v": PROTOCOL_VERSION,
                        "kind": "hello_ack",
                        "session_id": self._session_id,
                    }
                )
            )
            await writer.drain()

            while True:
                line = await reader.readline()
                if not line:
                    break
                message = decode_frame(line.rstrip(b"\r\n"))
                await self._on_message(message)
        except asyncio.CancelledError, ConnectionError:
            raise
        except Exception:
            pass
        finally:
            self.disarm()
            self._authenticated = False
            self._connected.clear()
            if self._writer is writer:
                self._writer = None
                self._reader = None
            for command_id, future in list(self._pending.items()):
                if not future.done():
                    future.set_exception(
                        BridgeError(
                            "EA connection lost while command outcome may be unknown",
                            code="CONNECTION_LOST",
                            command_id=command_id,
                            uncertain=True,
                        )
                    )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def _on_message(self, message: dict[str, Any]) -> None:
        kind = message.get("kind")
        if kind == "response":
            command_id = str(message.get("command_id", ""))
            future = self._pending.get(command_id)
            if future is not None and not future.done():
                future.set_result(message)
            return

        if kind == "event":
            raw_payload = message.get("payload")
            payload: dict[str, Any] = (
                raw_payload if isinstance(raw_payload, dict) else {}
            )
            request_id_raw = message.get("request_id")
            request_id = (
                int(request_id_raw)
                if isinstance(request_id_raw, (int, str))
                and str(request_id_raw) not in ("", "0")
                else None
            )
            event = BridgeEvent(
                event_type=str(message.get("event_type", "event")),
                payload=payload,
                command_id=message.get("command_id"),
                request_id=request_id,
            )
            self.journal.add_event(
                session_id=self._session_id,
                event_type=event.event_type,
                payload=payload,
                command_id=event.command_id,
                native_request_id=request_id,
            )
            await self._event_queue.put(event)
            if request_id is not None:
                waiters = self._request_waiters.pop(request_id, [])
                if waiters:
                    for waiter in waiters:
                        if not waiter.done():
                            waiter.set_result(event)
                else:
                    self._request_events.setdefault(request_id, []).append(event)
            return

    async def next_event(
        self,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Wait for and retrieve the next asynchronous event from the event queue."""
        async with asyncio.timeout(timeout):
            return await self._event_queue.get()

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Wait for an event associated with a specific request ID."""
        backlog = self._request_events.get(request_id)
        if backlog:
            event = backlog.pop(0)
            if not backlog:
                self._request_events.pop(request_id, None)
            return event
        loop = asyncio.get_running_loop()
        future: asyncio.Future[BridgeEvent] = loop.create_future()
        self._request_waiters.setdefault(request_id, []).append(future)
        try:
            async with asyncio.timeout(timeout):
                return await future
        finally:
            bucket = self._request_waiters.get(request_id)
            if bucket and future in bucket:
                bucket.remove(future)
                if not bucket:
                    self._request_waiters.pop(request_id, None)

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
        """Execute a remote method call on a MetaTrader EA object via the bridge."""
        writer = self._writer
        if not self.connected or writer is None:
            raise BridgeError("EA is not connected", code="NOT_CONNECTED")
        if requires_arm and not self._armed:
            raise BridgeError("live trading bridge is disarmed", code="DISARMED")

        command_id = uuid.uuid4().hex
        self._last_command.set(command_id)
        created = time.time()
        receipt = Receipt(
            command_id=command_id,
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            status=ReceiptStatus.CREATED,
            created_at=created,
        )
        self._receipts[command_id] = receipt
        self.journal.create_command(
            command_id=command_id,
            session_id=self._session_id,
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            args=args,
            requires_arm=requires_arm,
        )

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[command_id] = future
        message = {
            "v": PROTOCOL_VERSION,
            "kind": "call",
            "command_id": command_id,
            "object_id": object_id,
            "class": class_name,
            "method": method_name,
            "args": args,
        }

        try:
            async with self._write_lock:
                writer.write(encode_frame(message))
                await writer.drain()
            sent = time.time()
            self.journal.mark_sent(command_id)
            self._receipts[command_id] = replace(
                receipt, status=ReceiptStatus.SENT, sent_at=sent
            )

            try:
                response = await asyncio.wait_for(
                    future,
                    timeout=self.command_timeout if timeout is None else timeout,
                )
            except TimeoutError as exc:
                if requires_arm:
                    self.disarm()
                uncertain = requires_arm
                status = (
                    ReceiptStatus.UNCERTAIN if uncertain else ReceiptStatus.REJECTED
                )
                timeout_error = {
                    "code": "COMMAND_TIMEOUT",
                    "message": "bridge command timed out",
                }
                self.journal.resolve_command(
                    command_id, status=status.value, error=timeout_error
                )
                self._receipts[command_id] = replace(
                    self._receipts[command_id],
                    status=status,
                    resolved_at=time.time(),
                    error=timeout_error,
                )
                raise BridgeError(
                    "bridge command timed out",
                    code="COMMAND_TIMEOUT",
                    command_id=command_id,
                    uncertain=uncertain,
                ) from exc

            ok = bool(response.get("ok"))
            value = response.get("value")
            raw_meta = response.get("meta")
            meta: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
            error_raw = response.get("error")
            error: Mapping[str, Any] | None = (
                error_raw if isinstance(error_raw, dict) else None
            )
            request_id_raw = meta.get("request_id")
            request_id = (
                int(request_id_raw)
                if isinstance(request_id_raw, (int, str))
                and str(request_id_raw) not in ("", "0")
                else None
            )
            retcode_raw = meta.get("retcode")
            retcode = (
                int(retcode_raw)
                if isinstance(retcode_raw, (int, str)) and str(retcode_raw) != ""
                else None
            )
            uncertain = bool(meta.get("uncertain")) or (
                requires_arm and retcode in _UNCERTAIN_RETCODES
            )
            if uncertain:
                self.disarm()

            if ok and not uncertain:
                status = ReceiptStatus.RESOLVED
            elif uncertain:
                status = ReceiptStatus.UNCERTAIN
            else:
                status = ReceiptStatus.REJECTED

            self.journal.resolve_command(
                command_id,
                status=status.value,
                value=value,
                meta=meta,
                error=error,
                native_request_id=request_id,
            )
            final = replace(
                self._receipts[command_id],
                status=status,
                acknowledged_at=time.time(),
                resolved_at=time.time(),
                native_request_id=request_id,
                value=value,
                meta=meta,
                error=error if isinstance(error, dict) else None,
            )
            self._receipts[command_id] = final

            if not ok:
                err: Mapping[str, Any] = error if isinstance(error, dict) else {}
                raise BridgeError(
                    str(err.get("message", "remote call failed")),
                    code=str(err.get("code", "REMOTE_ERROR")),
                    command_id=command_id,
                    uncertain=uncertain,
                )
            return value
        finally:
            self._pending.pop(command_id, None)


class MetaTraderClient(TradingClient):
    """Unified MetaTrader 4/5 client connecting over the EA TCP bridge."""

    def __init__(
        self,
        *,
        auth_token: str = "",
        host: str = "127.0.0.1",
        port: int = 8765,
        command_timeout: float = 10.0,
        name: str = "MetaTrader",
        backend: MetaTraderClient | None = None,
    ) -> None:
        super().__init__(name=name)
        self.bridge: Bridge
        if backend is not None:
            self.bridge = backend.bridge
        else:
            token = (
                auth_token
                if auth_token and len(auth_token) >= 16
                else Bridge.generate_auth_token()
            )
            self.bridge = Bridge(
                host=host,
                port=port,
                auth_token=token,
                command_timeout=command_timeout,
            )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = False

        # Facade composition for direct proxy access if callers use client.<proxy>
        self.trading = Trading(self)
        self.account = self.trading.account
        self.terminal = self.trading.terminal
        self.symbol = self.trading.symbol
        self.trade = self.trading.trade
        self.position = self.trading.position
        self.order = self.trading.order
        self.history_order = self.trading.history_order
        self.deal = self.trading.deal

    @override
    def connect(self) -> bool:
        """Establish connectivity."""
        self._connected = True
        return True

    @override
    def disconnect(self) -> None:
        """Terminate connectivity."""
        self._connected = False

    @override
    async def start(self) -> None:
        """Start the bridge listener server."""
        self._loop = asyncio.get_running_loop()
        await self.bridge.start()
        self._connected = True

    @override
    async def wait_connected(self, timeout: float | None = None) -> None:
        """Wait until the MetaTrader EA connects and authenticates."""
        await self.bridge.wait_connected(timeout)
        self._connected = True

    @override
    def arm(self) -> None:
        """Arm the bridge to allow live trade mutation commands."""
        self.bridge.arm()
        self._armed = True

    @override
    def disarm(self) -> None:
        """Disarm the bridge to reject mutating trade commands."""
        self.bridge.disarm()
        self._armed = False

    @override
    async def close(self) -> None:
        """Close the bridge server and release client connections."""
        await self.bridge.close()
        self._connected = False

    @override
    def close_sync(self) -> None:
        """Synchronously release local resources."""
        self._connected = False

    @override
    async def __aenter__(self) -> Self:
        """Enter asynchronous runtime context and start listener."""
        await self.start()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit asynchronous runtime context and close listener."""
        await self.close()

    @override
    async def call(
        self,
        *,
        object_id: str = "broker",
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,
    ) -> Any:
        """Delegate a canonical trading call to the native bridge."""
        return await self.bridge.call(
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            args=args,
            requires_arm=requires_arm,
            timeout=timeout,
        )

    @override
    def last_command_id(self) -> str | None:
        """Return the current task's last native command identifier."""
        return self.bridge.last_command_id()

    @override
    def receipt(self, command_id: str) -> Receipt | None:
        """Read one native command receipt."""
        return self.bridge.receipt(command_id)

    @override
    async def next_event(self, timeout: float | None = None) -> BridgeEvent:
        """Wait for the next native transaction event."""
        return await self.bridge.next_event(timeout)

    @override
    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,
    ) -> BridgeEvent:
        """Wait for an event correlated to a native request."""
        return await self.bridge.await_request_event(request_id, timeout)

    @override
    def get_terminal_info(self) -> TerminalInfo:
        """Return terminal information from bridge."""
        return TerminalInfo(
            name=self.name,
            company=self.name,
            connected=self.bridge.connected,
            trade_allowed=self.bridge.armed,
        )

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve symbol metadata as canonical SymbolInfo."""
        return SymbolInfo(name=symbol.upper(), digits=5, point=0.00001)

    @override
    def get_symbols(self) -> list[str]:
        """Return list of symbol names when terminal is not queried asynchronously."""
        return []

    @override
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
    ) -> Awaitable[pd.DataFrame]:
        """Fetch historical candlestick bars directly from the connected MT5 terminal bridge."""
        if not self.bridge.connected:
            raise BridgeError(
                "MetaTrader terminal bridge is not connected",
                code="NOT_CONNECTED",
            )
        return self._get_bars_terminal(
            symbol=symbol,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
            start_pos=start_pos,
            count=count,
            limit=limit,
        )

    async def _get_bars_terminal(
        self,
        symbol: str,
        timeframe: Timeframe | str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Asynchronously retrieve and validate historical bars from MT5 terminal bridge."""
        logger.debug(
            "FR-MT5-MARKET-DATA: requesting bars via terminal bridge",
            extra={"symbol": symbol},
        )
        from app.services.include.data import _route, bars_to_dataframe, validate_rows

        mode, start, end, number = _route(
            date_from, date_to, start_pos, count, limit, scale=1
        )
        clean_sym = symbol.strip().upper()
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
        payload = await self.call(
            object_id="market-data",
            class_name="MarketData",
            method_name="Bars",
            args=[clean_sym, tf_str, mode, start, end, number, limit],
            timeout=READ_TIMEOUT,
        )
        rows = validate_rows(
            payload, "bars", 0 if mode == "position" else start, end, number or limit
        )
        bars = [row for row in rows if isinstance(row, MarketBar)]
        return bars_to_dataframe(bars)

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> Awaitable[pd.DataFrame]:
        """Fetch historical market ticks directly from the connected MT5 terminal bridge."""
        if not self.bridge.connected:
            raise BridgeError(
                "MetaTrader terminal bridge is not connected",
                code="NOT_CONNECTED",
            )
        return self._get_ticks_terminal(
            symbol=symbol,
            date_from=date_from,
            date_to=date_to,
            count=count,
            limit=limit,
        )

    async def _get_ticks_terminal(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Asynchronously retrieve and validate historical ticks from MT5 terminal bridge."""
        logger.debug(
            "FR-MT5-MARKET-DATA: requesting ticks via terminal bridge",
            extra={"symbol": symbol},
        )
        from app.services.include.data import _route, ticks_to_dataframe, validate_rows

        mode, start, end, number = _route(
            date_from, date_to, None, count, limit, scale=1000
        )
        clean_sym = symbol.strip().upper()
        payload = await self.call(
            object_id="market-data",
            class_name="MarketData",
            method_name="Ticks",
            args=[clean_sym, mode, start, end, number, limit],
            timeout=READ_TIMEOUT,
        )
        rows = validate_rows(
            payload, "ticks", 0 if mode == "latest" else start, end, number or limit
        )
        ticks = [row for row in rows if isinstance(row, MarketTick)]
        return ticks_to_dataframe(ticks)


def main() -> None:
    """Demonstrate executable usage of MetaTraderClient."""
    client = MetaTraderClient()
    logger.info("MetaTrader client initialized (connected=%s)", client.is_connected)


if __name__ == "__main__":
    main()
