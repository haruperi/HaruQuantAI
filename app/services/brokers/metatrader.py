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
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self, cast, override

from app.host.logging import get_logger

try:
    from app.host.persistence.engine import DEFAULT_DATABASE_PATH  # type: ignore[import-not-found]
    from app.host.persistence.mt5bridge_journal import Journal  # type: ignore[import-not-found]
except ImportError:
    from app.host.persistence.create import DEFAULT_DB_PATH as DEFAULT_DATABASE_PATH

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


from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderCapabilities,
    ProviderHealth,
)
from app.services.data import BridgeError, DataBrokerBackend
from app.services.trading import (
    BridgeEvent,
    PropertyValue,
    Receipt,
    ReceiptStatus,
    SymbolSnapshot,
    TradeResolution,
    Trading,
)

PLUGIN_MANIFEST = {
    "id": "metatrader",
    "name": "MetaTrader",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "metatrader:create_adapter",
    "description": "MetaTrader 4/5 terminal bridge and archive provider",
    "capabilities": ["data.fetch"],
}

__all__ = [
    "Bridge",
    "BridgeError",
    "MT5Backend",
    "MetaTraderDataBroker",
    "PLUGIN_MANIFEST",
    "PropertyValue",
    "Receipt",
    "ReceiptStatus",
    "TradeResolution",
    "create_adapter",
    "main",
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
        journal_path: str | Path = DEFAULT_DATABASE_PATH,
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


class MT5Backend(Trading):
    """Live MT5 facade backed only by the custom EA bridge."""

    def __init__(
        self,
        *,
        auth_token: str,
        host: str = "127.0.0.1",
        port: int = 8765,
        journal_path: str | Path = DEFAULT_DATABASE_PATH,
        command_timeout: float = 10.0,
    ) -> None:
        self.bridge = Bridge(
            host=host,
            port=port,
            auth_token=auth_token,
            journal_path=journal_path,
            command_timeout=command_timeout,
        )
        super().__init__(self)

    @override
    async def start(self) -> None:
        """Start the bridge listener server."""
        self._loop = asyncio.get_running_loop()
        await self.bridge.start()

    @override
    async def wait_connected(self, timeout: float | None = None) -> None:
        """Wait until the MetaTrader EA connects and authenticates."""
        await self.bridge.wait_connected(timeout)

    @override
    def arm(self) -> None:
        """Arm the bridge to allow live trade mutation commands."""
        self.bridge.arm()

    @override
    def disarm(self) -> None:
        """Disarm the bridge to reject mutating trade commands."""
        self.bridge.disarm()

    @override
    async def close(self) -> None:
        """Close the bridge server and release client connections."""
        await self.bridge.close()

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

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- forwarded deadline
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


def _normalize_terminal_bar(b: Any) -> dict[str, Any]:
    if isinstance(b, dict):
        vol = (
            b.get("tick_volume")
            if b.get("tick_volume") is not None
            else b.get("volume", 0)
        )
        rvol = (
            b.get("real_volume")
            if b.get("real_volume") is not None
            else b.get("volume", 0)
        )
        return {
            "time": int(b.get("time") or 0),
            "open": float(b.get("open") or 0.0),
            "high": float(b.get("high") or 0.0),
            "low": float(b.get("low") or 0.0),
            "close": float(b.get("close") or 0.0),
            "tick_volume": int(vol or 0),
            "spread": int(b.get("spread") or 0),
            "real_volume": int(rvol or 0),
        }
    vol_attr = getattr(b, "tick_volume", None) or getattr(b, "volume", 0)
    rvol_attr = getattr(b, "real_volume", None) or getattr(b, "volume", 0)
    return {
        "time": int(getattr(b, "time", 0) or 0),
        "open": float(getattr(b, "open", 0.0) or 0.0),
        "high": float(getattr(b, "high", 0.0) or 0.0),
        "low": float(getattr(b, "low", 0.0) or 0.0),
        "close": float(getattr(b, "close", 0.0) or 0.0),
        "tick_volume": int(vol_attr or 0),
        "spread": int(getattr(b, "spread", 0) or 0),
        "real_volume": int(rvol_attr or 0),
    }


def _normalize_terminal_tick(t: Any) -> dict[str, Any]:
    if isinstance(t, dict):
        t_ms = (
            int(t["time_msc"])
            if "time_msc" in t
            else int(float(t.get("time") or 0) * 1000)
        )
        last_val = t.get("last") if t.get("last") is not None else t.get("bid", 0.0)
        rvol_val = (
            t.get("volume_real")
            if t.get("volume_real") is not None
            else t.get("volume", 1.0)
        )
        return {
            "time_msc": t_ms,
            "bid": float(t.get("bid") or 0.0),
            "ask": float(t.get("ask") or 0.0),
            "last": float(last_val or 0.0),
            "volume": float(t.get("volume") or 1.0),
            "flags": int(t.get("flags") or 0),
            "volume_real": float(rvol_val or 1.0),
        }
    t_ms = (
        int(t.time_msc)
        if hasattr(t, "time_msc")
        else int(float(getattr(t, "time", 0) or 0) * 1000)
    )
    last_attr = getattr(t, "last", None) or getattr(t, "bid", 0.0)
    rvol_attr = getattr(t, "volume_real", None) or getattr(t, "volume", 1.0)
    return {
        "time_msc": t_ms,
        "bid": float(getattr(t, "bid", 0.0) or 0.0),
        "ask": float(getattr(t, "ask", 0.0) or 0.0),
        "last": float(last_attr or 0.0),
        "volume": float(getattr(t, "volume", 1.0) or 1.0),
        "flags": int(getattr(t, "flags", 0) or 0),
        "volume_real": float(rvol_attr or 1.0),
    }


def _run_coroutine_or_future(coro: Any, backend: Any, timeout: float = 30.0) -> Any:
    loop = getattr(backend, "_loop", None) or getattr(
        getattr(backend, "bridge", None), "_loop", None
    )
    if loop is not None and loop.is_running():
        try:
            curr = asyncio.get_running_loop()
        except RuntimeError:
            curr = None
        if curr is not loop:
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=timeout)
    try:
        return asyncio.run(coro)
    except RuntimeError:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=timeout)


class MetaTraderDataBroker(DataBrokerBackend):
    """Historical data provider for MetaTrader terminals and archives."""

    def __init__(
        self,
        name: str = "MetaTrader",
        data_dir: str | Path | None = None,
        backend: MT5Backend | None = None,
        mode: str = "archive",
    ) -> None:
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else None
        self.backend = backend
        self._borrowed_backend = backend is not None
        self.mode = mode.lower().strip()

        self.capabilities = ProviderCapabilities(
            provider_id="metatrader",
            display_name="MetaTrader",
            category="Multi-Asset",
            supported_timeframes=("M1", "M5", "M15", "M30", "H1", "H4", "D1"),
            supported_modes=("bars", "ticks"),
            requires_auth=False,
            rate_limit_rps=10.0,
            default_timeout_seconds=30.0,
            supports_pagination=True,
            has_local_archive=self.data_dir is not None and self.data_dir.exists(),
            description="MetaTrader 4/5 terminal bridge and archive provider",
        )

    @override
    def close_sync(self) -> None:
        """Close provider resources; preserves borrowed backend."""
        self._is_connected = False

    @override
    async def close(self) -> None:
        self.close_sync()

    def check_health(self) -> Any:
        """Inspect health status of MetaTrader terminal connection or archive files."""
        if self.mode == "terminal" and self.backend is not None:
            conn = bool(getattr(self.backend.bridge, "connected", False))
            return ProviderHealth(
                provider_id="metatrader",
                status="available" if conn else "unconfigured",
                connected=conn,
                message="MT5 terminal connected"
                if conn
                else "MT5 terminal not connected",
                capabilities=self.capabilities,
            )
        has_dir = self.data_dir is not None and self.data_dir.exists()
        return ProviderHealth(
            provider_id="metatrader",
            status="available" if has_dir else "unconfigured",
            connected=has_dir,
            message="MetaTrader archive ready"
            if has_dir
            else "Archive data_dir not found",
            capabilities=self.capabilities,
        )

    @override
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        if self.backend is not None:
            resolver = getattr(self.backend, "symbol_info", None)
            if callable(resolver):
                res = resolver(symbol)
                if isinstance(res, SymbolSnapshot):
                    return res
        return SymbolSnapshot(name=symbol.upper(), digits=5, point=0.00001)

    @override
    def symbols_get(self) -> list[str]:
        if self.backend is not None:
            getter = getattr(self.backend, "symbols_get", None)
            if callable(getter):
                syms = getter()
                if isinstance(syms, list):
                    return [str(s) for s in syms]
        if self.data_dir and self.data_dir.exists():
            from app.services.brokers._file_history import find_matching_partitions

            matched = find_matching_partitions(self.data_dir, "", "")
            return sorted({p.stem.split("_")[0] for p in matched})
        return []

    @override
    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str = "range",
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        target_count = count if count > 0 else limit
        clean_sym = symbol.strip().upper()

        if self.mode == "terminal" and self.backend is not None:
            if hasattr(self.backend, "fetch_bars"):
                bars_fn = getattr(self.backend, "fetch_bars")  # noqa: B009
                return cast(
                    "list[dict[str, Any]]",
                    bars_fn(
                        symbol=clean_sym,
                        timeframe=timeframe,
                        mode=mode,
                        start=start,
                        end=end,
                        count=target_count,
                        limit=limit,
                    ),
                )
            if hasattr(self.backend, "call"):
                caller = getattr(self.backend, "call")  # noqa: B009
                res_or_coro = caller(
                    object_id="market-data",
                    class_name="MarketData",
                    method_name="Bars",
                    args=[clean_sym, timeframe, mode, start, end, target_count, limit],
                )
                if asyncio.iscoroutine(res_or_coro):
                    res = _run_coroutine_or_future(res_or_coro, self.backend)
                else:
                    res = res_or_coro
                if isinstance(res, list):
                    return [_normalize_terminal_bar(b) for b in res]
                raise BridgeError(
                    f"Invalid terminal bars response for {clean_sym}: {res!r}",
                    code="READ_ERROR",
                )

        if self.data_dir and self.data_dir.exists():
            from app.services.brokers._file_history import (
                find_matching_partitions,
                parse_delimited_bars,
                read_parquet_bars,
            )
            from app.services.brokers._native_history import (
                decode_fxt_bytes,
                decode_hst_bytes,
            )

            matched = find_matching_partitions(self.data_dir, clean_sym, timeframe)
            rows: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".hst":
                    rows.extend(decode_hst_bytes(p.read_bytes(), count=target_count))
                elif p.suffix.lower() == ".fxt":
                    rows.extend(decode_fxt_bytes(p.read_bytes(), count=target_count))
                elif p.suffix.lower() == ".parquet":
                    rows.extend(read_parquet_bars(p, count=target_count))
                elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
                    rows.extend(
                        parse_delimited_bars(
                            p.read_text(encoding="utf-8", errors="replace"),
                            clean_sym,
                            timeframe,
                        )
                    )

            if rows:
                rows.sort(key=lambda r: r["time"])
                filtered = [
                    r
                    for r in rows
                    if (start <= 0 or r["time"] >= start)
                    and (end <= 0 or r["time"] <= end)
                ]
                if filtered:
                    return filtered[-target_count:] if target_count else filtered

        raise BridgeError(
            f"No bars available for '{clean_sym}' in MetaTrader archives",
            code="NO_DATA",
        )

    @override
    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str = "range",
        start_ms: int = 0,
        end_ms: int = 0,
        count: int = 100,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        target_count = count if count > 0 else limit
        clean_sym = symbol.strip().upper()

        if self.mode == "terminal" and self.backend is not None:
            if hasattr(self.backend, "fetch_ticks"):
                ticks_fn = getattr(self.backend, "fetch_ticks")  # noqa: B009
                return cast(
                    "list[dict[str, Any]]",
                    ticks_fn(
                        symbol=clean_sym,
                        mode=mode,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        count=target_count,
                        limit=limit,
                    ),
                )
            if hasattr(self.backend, "call"):
                caller = getattr(self.backend, "call")  # noqa: B009
                res_or_coro = caller(
                    object_id="market-data",
                    class_name="MarketData",
                    method_name="Ticks",
                    args=[clean_sym, mode, start_ms, end_ms, target_count, limit],
                )
                if asyncio.iscoroutine(res_or_coro):
                    res = _run_coroutine_or_future(res_or_coro, self.backend)
                else:
                    res = res_or_coro
                if isinstance(res, list):
                    return [_normalize_terminal_tick(t) for t in res]
                raise BridgeError(
                    f"Invalid terminal ticks response for {clean_sym}: {res!r}",
                    code="READ_ERROR",
                )

        if self.data_dir and self.data_dir.exists():
            from app.services.brokers._file_history import (
                find_matching_partitions,
                parse_delimited_ticks,
            )
            from app.services.brokers._native_history import decode_fxt_bytes

            matched = find_matching_partitions(self.data_dir, clean_sym, "TICK")
            rows: list[dict[str, Any]] = []
            for p in matched:
                if p.suffix.lower() == ".fxt":
                    fxt_bars = decode_fxt_bytes(p.read_bytes(), count=target_count)
                    for b in fxt_bars:
                        rows.append(
                            {
                                "time_msc": int(b["tick_time"] * 1000)
                                if b.get("tick_time")
                                else int(b["time"] * 1000),
                                "bid": b["close"],
                                "ask": b["close"],
                                "last": b["close"],
                                "volume": b.get("volume", 1),
                                "flags": b.get("flag", 0),
                                "volume_real": float(b.get("volume", 1)),
                            }
                        )
                elif p.suffix.lower() in (".csv", ".tsv", ".txt"):
                    rows.extend(
                        parse_delimited_ticks(
                            p.read_text(encoding="utf-8", errors="replace"), clean_sym
                        )
                    )

            if rows:
                rows.sort(key=lambda r: r["time_msc"])
                filtered = [
                    r
                    for r in rows
                    if (start_ms <= 0 or r["time_msc"] >= start_ms)
                    and (end_ms <= 0 or r["time_msc"] <= end_ms)
                ]
                if filtered:
                    return filtered[-target_count:] if target_count else filtered

        raise BridgeError(
            f"No ticks available for '{clean_sym}' in MetaTrader archives",
            code="NO_DATA",
        )

    def read_history(
        self,
        request: HistoryRequest,
        token: CancellationToken | None = None,
    ) -> HistoryPage:
        """Acquire historical bars or ticks from MetaTrader terminal or archives."""
        if token is not None:
            token.check_cancelled()
        request.validate()

        if request.kind == "ticks" or request.timeframe.upper() == "TICK":
            start_ms = (request.start_epoch() or 0) * 1000
            end_ms = (request.end_epoch() or 0) * 1000
            rows = self.fetch_ticks(
                symbol=request.symbol,
                mode=request.mode,
                start_ms=start_ms,
                end_ms=end_ms,
                count=request.count,
                limit=request.limit,
            )
        else:
            start_s = request.start_epoch() or 0
            end_s = request.end_epoch() or 0
            rows = self.fetch_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                mode=request.mode,
                start=start_s,
                end=end_s,
                count=request.count,
                limit=request.limit,
            )

        if token is not None:
            token.check_cancelled()

        return HistoryPage(
            provider="metatrader",
            symbol=request.symbol,
            timeframe=request.timeframe,
            kind=request.kind,
            rows=rows,
            cursor=None,
            is_complete=True,
            provenance={
                "source": "metatrader",
                "mode": self.mode,
                "data_dir": str(self.data_dir) if self.data_dir else None,
            },
        )


def create_adapter(context: Any = None) -> MetaTraderDataBroker:
    """Factory creating configured MetaTraderDataBroker adapter."""
    data_dir = getattr(context, "data_dir", None)
    settings = getattr(context, "settings", {}) or {}
    mode = str(settings.get("mode", "archive"))
    backend = getattr(context, "backend", getattr(context, "client", None))
    return MetaTraderDataBroker(data_dir=data_dir, backend=backend, mode=mode)


def main() -> None:
    """Demonstrate executable usage of MetaTraderDataBroker."""
    broker = MetaTraderDataBroker(mode="archive")
    health = broker.check_health()
    logger.info("MetaTrader health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
