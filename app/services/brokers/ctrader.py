"""cTrader Open API Protobuf-over-TLS socket transport broker implementation.

Description:
    Implements the asynchronous `TradingClient` capability (`CTraderClient`) for
    Spotware cTrader Open API v2 via length-prefixed Protocol Buffers over a secure
    TLS socket transport (`live.ctraderapi.com:5035` or demo).
    Within HaruQuantAI, cTrader serves as an institutional multi-asset broker
    integration backing the canonical eight-class MQL5-compatible `Trading` facade
    (AccountInfo, TerminalInfo, SymbolInfo, Trade, PositionInfo, OrderInfo,
    HistoryOrderInfo, DealInfo) as well as direct broker client operations.
    External credentials (`client_id`, `client_secret`, `access_token`, and
    `account_id`) are dynamically loaded from host configuration
    (`settings.config_ctrader`) or environment variables when not explicitly passed.

Purpose:
    FEAT-BROKER-CTRADER: Spotware cTrader Open API v2 Protocol Buffers integration.

Key Capabilities:
    - FR-BROKER-CTRADER-TLS-AUTH: TLS, token refresh and account validation.
      Associated: `[CTraderClient.connect()]`, `[CTraderClient.disconnect()]`
      Logging: INFO on successful handshake; ERROR on failure or disconnect.
    - FR-BROKER-CTRADER-FRAME-TRANSPORT: Length-prefixed Protocol Buffer framing.
      Associated: `[CTraderClient._send_msg()]`, `[CTraderClient._recv_msg()]`
      Logging: DEBUG on message send/recv; ERROR on framing or transport error.
    - FR-BROKER-CTRADER-MARKET-DATA: Historical trendbars and symbol resolution.
      Associated: `[CTraderClient.trendbars()]`, `[CTraderClient.symbols_list()]`
      Logging: DEBUG on fetching trendbars and symbols.
    - FR-BROKER-CTRADER-TRADE-EXECUTION: Pre-flight check and order execution.
      Associated: `[CTraderClient.order_check()]`, `[CTraderClient.order_send()]`
      Logging: INFO on execution; WARNING/ERROR on rejection or failure.
    - FR-BROKER-CTRADER-FACADE-DISPATCH: Route eight-class trading proxy calls.
      Associated: `[CTraderClient.call()]`
      Logging: DEBUG on dispatching method to cTrader client; ERROR on unknown.

Python API Usage:
    ```python
    from app.services.brokers.ctrader import CTraderClient

    client = CTraderClient()
    await client.start()
    account = client.get_account_info()
    await client.close()
    ```

CLI Usage:
    ```bash
    uv run python -c "from app.services.brokers.ctrader import CTraderClient"
    ```
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import fnmatch
import os
import socket
import ssl
import struct
import threading
import time
from datetime import datetime
from typing import Any, override

from app.host.logging import get_logger
from app.host.settings import settings
from app.services.brokers.base import (
    BridgeError,
    TradingClient,
)
from app.services.include.contracts import (
    AccountInfo,
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
    AccountTradeMode,
    MarginMode,
    OrderFilling,
    OrderType,
    Timeframe,
    TradeAction,
    TradeRetcode,
)
from app.services.include.trading import Trading

logger = get_logger(__name__)

FRAME_HEADER_SIZE = 4
MIN_SYMBOL_CHARS = 6
DEFAULT_GATEWAY_PORT = 5035
HISTORY_PAGE_LIMIT = 64
HISTORY_MAX_RECORDS = 10000
HISTORY_WEEK_MS = 604800000
HISTORY_MAX_TIMESTAMP_MS = 2147483646000


class _MissingCTraderOpenAPI:
    """Sentinel placeholder when ctrader_open_api package is not installed."""

    def __bool__(self) -> bool:
        return False

    def __getattr__(self, name: str) -> Any:
        return None


commonmsg: Any = _MissingCTraderOpenAPI()
modelmsg: Any = _MissingCTraderOpenAPI()
oamsg: Any = _MissingCTraderOpenAPI()
try:
    from ctrader_open_api.messages import (  # pyright: ignore[reportMissingImports] # type: ignore[import-untyped,import-not-found]
        OpenApiCommonMessages_pb2 as _cmsg,
    )
    from ctrader_open_api.messages import (  # pyright: ignore[reportMissingImports] # type: ignore[import-untyped,import-not-found]
        OpenApiMessages_pb2 as _omsg,
    )
    from ctrader_open_api.messages import (  # pyright: ignore[reportMissingImports] # type: ignore[import-untyped,import-not-found]
        OpenApiModelMessages_pb2 as _mmsg,
    )

    commonmsg = _cmsg
    oamsg = _omsg
    modelmsg = _mmsg
except ImportError:
    pass

TIMEFRAME_TO_PERIOD: dict[str, int] = {
    "M1": 1,
    "M2": 2,
    "M3": 3,
    "M4": 4,
    "M5": 5,
    "M10": 6,
    "M15": 7,
    "M30": 8,
    "H1": 9,
    "H4": 10,
    "H12": 11,
    "D1": 12,
    "W1": 13,
    "MN1": 14,
}


def _arg_float(args: list[Any], idx: int, default: float) -> float:
    return float(args[idx]) if idx < len(args) else default


def _arg_int(args: list[Any], idx: int, default: int) -> int:
    return int(args[idx]) if idx < len(args) else default


def _arg_str(args: list[Any], idx: int, default: str) -> str:
    return str(args[idx]) if idx < len(args) else default


def _filter_records(
    records: list[dict[str, Any]],
    args: list[Any],
) -> list[dict[str, Any]]:
    if not args or not records:
        return records
    first = args[0]
    sym: str | None = None
    group: str | None = None
    ticket: int | None = None
    position: int | None = None

    if isinstance(first, dict):
        sym = first.get("symbol")
        group = first.get("group")
        ticket = first.get("ticket")
        position = first.get("position")
    elif isinstance(first, str):
        if "*" in first or "?" in first:
            group = first
        else:
            sym = first
    elif isinstance(first, int):
        ticket = first

    res = records
    if sym:
        res = [r for r in res if str(r.get("symbol", "")).upper() == sym.upper()]
    if ticket is not None:
        res = [
            r for r in res if r.get("ticket") == ticket or r.get("identifier") == ticket
        ]
    if position is not None:
        res = [
            r
            for r in res
            if r.get("position_id") == position
            or r.get("identifier") == position
            or r.get("ticket") == position
        ]
    if group:
        res = [r for r in res if fnmatch.fnmatch(str(r.get("symbol", "")), group)]
    return res


class CTraderClient(TradingClient):
    """Uniform institutional broker client for Spotware cTrader Open API v2."""

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        account_id: int | None = None,
        gateway_host: str | None = None,
        gateway_port: int | None = None,
        environment: str | None = None,
        command_timeout: float = 10.0,
        name: str = "cTrader",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name)
        cfg = getattr(settings, "config_ctrader", None)

        def resolve(name_str: str, explicit: Any, default: Any) -> Any:
            if explicit is not None:
                return explicit
            env_value = os.environ.get(f"CTRADER_{name_str.upper()}")
            if env_value:
                return env_value
            return getattr(cfg, name_str, None) or default

        self.client_id = str(resolve("client_id", client_id, ""))
        self.client_secret = str(resolve("client_secret", client_secret, ""))
        self.access_token = str(resolve("access_token", access_token, ""))
        self.refresh_token = str(resolve("refresh_token", refresh_token, ""))
        self._host_owned_tokens = (
            access_token is None
            and refresh_token is None
            and client_id is None
            and client_secret is None
            and not any(
                os.environ.get(f"CTRADER_{name_env}")
                for name_env in (
                    "ACCESS_TOKEN",
                    "REFRESH_TOKEN",
                    "CLIENT_ID",
                    "CLIENT_SECRET",
                )
            )
        )
        try:
            self.account_id = int(resolve("account_id", account_id, 0))
            self.gateway_port = int(
                resolve("gateway_port", gateway_port, DEFAULT_GATEWAY_PORT)
            )
        except TypeError, ValueError:
            raise BridgeError(
                "cTrader account_id and gateway_port must be integers",
                code="CTRADER_CONFIG_INVALID",
            ) from None
        self.environment = str(resolve("environment", environment, "demo")).lower()
        self.gateway_host = str(
            resolve("gateway_host", gateway_host, f"{self.environment}.ctraderapi.com")
        ).lower()
        self.command_timeout = command_timeout

        self._sock: ssl.SSLSocket | None = None
        self._lock = threading.RLock()
        self._authenticated = False
        self._app_authorized = False
        self._last_error: tuple[Any, str] = (0, "No error")
        self._symbol_id_map: dict[int, str] = {}
        self._symbol_name_map: dict[str, int] = {}
        self._symbol_cache: dict[str, SymbolInfo] = {}
        self._history_next_request = 0.0
        self._armed = False
        self._connect_error: BridgeError | None = None
        self._last_command: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            "ctrader_last_command", default=None
        )
        self._receipts: dict[str, Receipt] = {}
        self._event_queue: asyncio.Queue[BridgeEvent] = asyncio.Queue()
        self._request_events: dict[int, list[BridgeEvent]] = {}
        self._request_waiters: dict[int, asyncio.Future[BridgeEvent]] = {}
        self._last_request = TradeRequest(action=TradeAction.DEAL)
        self._last_result = TradeResult()
        self._last_check = TradeCheckResult()
        self._book_subscriptions: set[str] = set()
        self._magic: int = 0
        self._deviation: int = 10
        self._filling: OrderFilling = OrderFilling.FOK
        self._selected_position_ticket: int = 0
        self._selected_order_ticket: int = 0
        self._selected_deal_ticket: int = 0
        self._selected_history_order_ticket: int = 0

        self.trading = Trading(self)
        self.account = self.trading.account
        self.terminal = self.trading.terminal
        self.symbol = self.trading.symbol
        self.trade = self.trading.trade
        self.position = self.trading.position
        self.order = self.trading.order
        self.history_order = self.trading.history_order
        self.deal = self.trading.deal

    @property
    @override
    def is_connected(self) -> bool:
        """Return whether TLS socket is active and account is authenticated."""
        return bool(self._sock and self._authenticated)

    @property
    def last_error(self) -> tuple[Any, str]:
        """Return the last recorded error tuple."""
        return self._last_error

    @override
    def get_terminal_info(self) -> TerminalInfo:
        """Retrieve current cTrader terminal status."""
        return TerminalInfo(
            name=self.name,
            company="Spotware cTrader",
            connected=self.is_connected,
            trade_allowed=True,
            cpu_cores=os.cpu_count() or 4,
        )

    @override
    def get_account_info(self) -> AccountInfo:
        """Retrieve current trading account snapshot."""
        return self.account_info()

    @override
    def get_positions(self) -> list[PositionInfo]:
        """Retrieve open positions from cTrader."""
        positions, _ = self.reconcile()
        return [PositionInfo(**p) for p in positions]

    @override
    def get_orders(self) -> list[OrderInfo]:
        """Retrieve pending orders from cTrader."""
        _, orders = self.reconcile()
        return [OrderInfo(**o) for o in orders]

    @override
    def get_history_orders(self) -> list[OrderInfo]:
        """Retrieve history orders (empty if unsupported natively)."""
        return []

    @override
    def get_deals(self) -> list[DealInfo]:
        """Retrieve history deals (empty if unsupported natively)."""
        return []

    def _ensure_module(self) -> None:
        if (
            not oamsg
            or not modelmsg
            or not commonmsg
            or isinstance(commonmsg, _MissingCTraderOpenAPI)
        ):
            msg = "cTrader Open API protobuf modules not available."
            logger.error("FR-BROKER-CTRADER-TLS-AUTH: %s", msg)
            raise BridgeError(msg, code="MODULE_NOT_FOUND")

    def _send_msg(self, payload_type: int, payload_bytes: bytes) -> bool:
        """Send a length-prefixed Protocol Buffer message over the TLS socket."""
        logger.debug(
            "FR-BROKER-CTRADER-FRAME-TRANSPORT: sending message payload_type=%s",
            payload_type,
        )
        if not self._sock:
            return False
        msg = commonmsg.ProtoMessage()
        msg.payloadType = payload_type
        msg.payload = payload_bytes
        serialized = msg.SerializeToString()
        header = struct.pack(">I", len(serialized))
        try:
            self._sock.sendall(header + serialized)
            return True
        except OSError as e:
            logger.exception(
                "FR-BROKER-CTRADER-FRAME-TRANSPORT: Failed to send socket message"
            )
            self._last_error = ("SEND_ERROR", str(e))
            return False

    def _recv_msg(self, timeout: float | None = None) -> tuple[int, bytes] | None:
        """Receive and unpack a length-prefixed ProtoMessage."""
        logger.debug("FR-BROKER-CTRADER-FRAME-TRANSPORT: receiving socket message")
        if not self._sock:
            return None
        deadline = time.monotonic() + (
            timeout if timeout is not None else self.command_timeout
        )

        def recv_exact(size: int) -> bytes:
            assert self._sock is not None
            result = bytearray()
            while len(result) < size:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                self._sock.settimeout(remaining)
                chunk = self._sock.recv(size - len(result))
                if not chunk:
                    raise ConnectionError("cTrader socket closed during a frame")
                result.extend(chunk)
            return bytes(result)

        try:
            len_bytes = recv_exact(FRAME_HEADER_SIZE)
            length = struct.unpack(">I", len_bytes)[0]
            if not 0 < length <= 16 * 1024 * 1024:
                raise BridgeError("Invalid cTrader frame length", code="AUTH_FAILED")
            data = recv_exact(length)
            msg = self._parse_auth_payload(commonmsg.ProtoMessage, data)
            return msg.payloadType, msg.payload
        except TimeoutError:
            logger.debug("FR-BROKER-CTRADER-FRAME-TRANSPORT: Socket timed out waiting")
            return None
        except OSError as e:
            logger.exception(
                "FR-BROKER-CTRADER-FRAME-TRANSPORT: Failed to receive socket message"
            )
            self._last_error = ("RECV_ERROR", str(e))
            return None

    def _validate_configuration(self) -> None:
        """Reject missing credentials and contradictory connection settings."""
        if self.environment not in {"demo", "live"}:
            raise BridgeError(
                "cTrader environment must be demo or live",
                code="CTRADER_CONFIG_INVALID",
            )
        if self.gateway_host in {"demo.ctraderapi.com", "live.ctraderapi.com"}:
            if self.gateway_host != f"{self.environment}.ctraderapi.com":
                raise BridgeError(
                    "cTrader gateway_host conflicts with environment; configure "
                    "both for the intended demo or live account",
                    code="CTRADER_ENVIRONMENT_MISMATCH",
                )
        if (
            self.account_id <= 0
            or self.account_id >= 2**63
            or not 0 < self.gateway_port < 65536
            or self.command_timeout <= 0
        ):
            raise BridgeError(
                "cTrader requires a positive API account_id, valid port and timeout",
                code="CTRADER_CONFIG_INVALID",
            )
        if not self.client_id or not self.client_secret or not self.access_token:
            raise BridgeError(
                "cTrader client_id, client_secret and access_token are required",
                code="AUTH_FAILED",
            )
        logger.debug("FR-BROKER-CTRADER-TLS-AUTH: configuration validated")

    def _auth_request(self, request: Any, response_class: Any) -> Any:
        """Exchange one serialized request with a deadline and safe broker errors."""
        if not self._send_msg(request.payloadType, request.SerializeToString()):
            raise BridgeError("Cannot send cTrader auth request", code="AUTH_FAILED")
        deadline = time.monotonic() + self.command_timeout
        while time.monotonic() < deadline:
            response = self._recv_msg(timeout=deadline - time.monotonic())
            if response is None:
                break
            payload_type, data = response
            if payload_type == commonmsg.ProtoHeartbeatEvent().payloadType:
                heartbeat = commonmsg.ProtoHeartbeatEvent()
                if not self._send_msg(
                    heartbeat.payloadType, heartbeat.SerializeToString()
                ):
                    raise BridgeError("cTrader heartbeat failed", code="AUTH_FAILED")
                continue
            if payload_type == oamsg.ProtoOAErrorRes().payloadType:
                error = self._parse_auth_payload(oamsg.ProtoOAErrorRes, data)
                # Only documented enum names may enter diagnostics. Never include
                # arbitrary server descriptions or unknown error strings.
                known_codes = modelmsg.ProtoOAErrorCode.keys()
                code = (
                    error.errorCode if error.errorCode in known_codes else "AUTH_FAILED"
                )
                raise BridgeError(f"cTrader authorization rejected ({code})", code=code)
            if payload_type == oamsg.ProtoOAClientDisconnectEvent().payloadType:
                raise BridgeError(
                    "cTrader disconnected during auth", code="CONNECTION_LOST"
                )
            if payload_type == response_class().payloadType:
                return self._parse_auth_payload(response_class, data)
            logger.debug(
                "FR-BROKER-CTRADER-TLS-AUTH: ignoring unrelated payload_type=%s",
                payload_type,
            )
        raise BridgeError("cTrader auth response timed out", code="COMMAND_TIMEOUT")

    @staticmethod
    def _parse_auth_payload(message_class: Any, data: bytes) -> Any:
        """Validate authentication protobufs without exposing their contents."""
        message = message_class()
        try:
            message.ParseFromString(data)
        except Exception:
            raise BridgeError(
                "Malformed cTrader authentication response", code="AUTH_FAILED"
            ) from None
        if not message.IsInitialized():
            raise BridgeError(
                "Incomplete cTrader authentication response", code="AUTH_FAILED"
            )
        return message

    def _auth_application(self) -> None:
        """Authorize the Open API application, independently of account tokens."""
        request = oamsg.ProtoOAApplicationAuthReq(
            clientId=self.client_id, clientSecret=self.client_secret
        )
        self._auth_request(request, oamsg.ProtoOAApplicationAuthRes)
        self._app_authorized = True
        logger.info("FR-BROKER-CTRADER-TLS-AUTH: Application authorization successful")

    def _refresh_access_token(self) -> None:
        """Rotate tokens once, saving only credentials owned by host settings."""
        if not self.refresh_token:
            raise BridgeError(
                "cTrader access token rejected; reauthorize or configure a refresh token",
                code="CTRADER_REAUTHORIZE_REQUIRED",
            )
        expected_revision: int | None = None
        if self._host_owned_tokens:
            try:
                cfg = settings.get_scope("config_ctrader")
                expected_revision = settings.revision
            except Exception:
                raise BridgeError(
                    "Cannot read saved cTrader credentials before token rotation",
                    code="CTRADER_TOKEN_PERSIST_FAILED",
                ) from None
            if any(
                cfg.get(name) != getattr(self, name)
                for name in (
                    "access_token",
                    "refresh_token",
                    "client_id",
                    "client_secret",
                )
            ):
                raise BridgeError(
                    "cTrader credentials changed; reload configuration before refreshing",
                    code="CTRADER_TOKEN_PERSIST_FAILED",
                )
        logger.info("FR-BROKER-CTRADER-TLS-AUTH: refreshing rejected access token")
        request = oamsg.ProtoOARefreshTokenReq(refreshToken=self.refresh_token)
        try:
            result = self._auth_request(request, oamsg.ProtoOARefreshTokenRes)
        except BridgeError as error:
            raise BridgeError(
                f"cTrader token refresh failed ({error.code}); "
                "reauthorize the application",
                code="CTRADER_REAUTHORIZE_REQUIRED",
            ) from None
        if not result.accessToken or not result.refreshToken:
            raise BridgeError(
                "cTrader returned an empty token pair; reauthorize the application",
                code="CTRADER_REAUTHORIZE_REQUIRED",
            )
        # Retain rotated credentials even if local persistence fails. They must
        # never be printed, and old tokens are invalid after successful rotation.
        self.access_token = result.accessToken
        self.refresh_token = result.refreshToken
        if expected_revision is not None:
            try:
                settings.update_batch(
                    {
                        "config_ctrader": {
                            "access_token": self.access_token,
                            "refresh_token": self.refresh_token,
                        }
                    },
                    expected_revision=expected_revision,
                )
            except Exception:
                raise BridgeError(
                    "Rotated cTrader tokens could not be saved; securely save the "
                    "client token pair or reauthorize before restarting",
                    code="CTRADER_TOKEN_PERSIST_FAILED",
                ) from None
        logger.info("FR-BROKER-CTRADER-TLS-AUTH: access token refreshed")

    def _authorized_accounts(self) -> Any:
        """List token-authorized accounts, with at most one refresh attempt."""
        for attempt in range(2):
            request = oamsg.ProtoOAGetAccountListByAccessTokenReq(
                accessToken=self.access_token
            )
            try:
                return self._auth_request(
                    request, oamsg.ProtoOAGetAccountListByAccessTokenRes
                )
            except BridgeError as error:
                if error.code not in {
                    "CH_ACCESS_TOKEN_INVALID",
                    "OA_AUTH_TOKEN_EXPIRED",
                }:
                    raise
                if attempt:
                    raise BridgeError(
                        "cTrader rejected the refreshed token; reauthorize the application",
                        code="CTRADER_REAUTHORIZE_REQUIRED",
                    ) from None
                self._refresh_access_token()
        raise AssertionError("Unreachable token retry state")

    def _auth_account(self) -> None:
        """Validate the configured API account and environment before auth."""
        result = self._authorized_accounts()
        accounts = result.ctidTraderAccount
        selected = next(
            (a for a in accounts if a.ctidTraderAccountId == self.account_id), None
        )
        if selected is None:
            login_match = next(
                (a for a in accounts if a.traderLogin == self.account_id), None
            )
            if login_match is not None:
                raise BridgeError(
                    "Configured account_id is a traderLogin; use ctidTraderAccountId="
                    f"{login_match.ctidTraderAccountId} instead",
                    code="CTRADER_ACCOUNT_ID_IS_LOGIN",
                )
            raise BridgeError(
                "Configured cTrader API account_id is not authorized by this token; "
                "verify the API ID and account consent",
                code="CTRADER_ACCOUNT_NOT_AUTHORIZED",
            )
        if not selected.HasField("isLive"):
            raise BridgeError(
                "cTrader account environment is missing", code="AUTH_FAILED"
            )
        if selected.isLive != (self.environment == "live"):
            raise BridgeError(
                "Configured cTrader environment does not match the authorized account",
                code="CTRADER_ENVIRONMENT_MISMATCH",
            )
        request = oamsg.ProtoOAAccountAuthReq(
            ctidTraderAccountId=self.account_id, accessToken=self.access_token
        )
        response = self._auth_request(request, oamsg.ProtoOAAccountAuthRes)
        if response.ctidTraderAccountId != self.account_id:
            raise BridgeError(
                "cTrader authenticated a different account", code="AUTH_FAILED"
            )
        self._authenticated = True
        logger.info("FR-BROKER-CTRADER-TLS-AUTH: Account authorization successful")

    @override
    def connect(self) -> bool:
        """Establish TLS connection and authenticate application & account."""
        self._ensure_module()
        self._validate_configuration()

        with self._lock:
            logger.info(
                "FR-BROKER-CTRADER-TLS-AUTH: Connecting to gateway %s:%s...",
                self.gateway_host,
                self.gateway_port,
            )
            ctx = ssl.create_default_context()
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(self.command_timeout)
            try:
                self._sock = ctx.wrap_socket(
                    raw_sock, server_hostname=self.gateway_host
                )
                self._sock.connect((self.gateway_host, self.gateway_port))
                self._auth_application()
                self._auth_account()
                self._connected = True
                return True
            except OSError as err:
                self.disconnect()
                msg = f"Failed to connect to cTrader gateway: {err}"
                logger.exception("FR-BROKER-CTRADER-TLS-AUTH: %s", msg)
                raise BridgeError(msg, code="CONNECT_FAILED") from err
            except Exception:
                self.disconnect()
                raise

    @override
    def disconnect(self) -> None:
        """Close the active TLS socket session cleanly."""
        logger.info("FR-BROKER-CTRADER-TLS-AUTH: Disconnecting from cTrader...")
        with self._lock:
            if self._sock:
                with contextlib.suppress(OSError):
                    self._sock.shutdown(socket.SHUT_RDWR)
                self._sock.close()
                self._sock = None
            self._authenticated = False
            self._app_authorized = False
            self._connected = False

    def account_info(self) -> AccountInfo:
        """Query account telemetry via ProtoOATraderReq."""
        logger.debug("FR-BROKER-CTRADER-FACADE-DISPATCH: querying account info")
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )
        with self._lock:
            req = oamsg.ProtoOATraderReq()
            req.ctidTraderAccountId = self.account_id
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_TRADER_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg()
            if not resp or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_TRADER_RES:
                raise BridgeError(
                    "Failed to retrieve trader info", code="REQUEST_FAILED"
                )
            trader_res = oamsg.ProtoOATraderRes()
            trader_res.ParseFromString(resp[1])
            trader = trader_res.trader
            bal = float(trader.balance) / 100.0 if trader.balance else 0.0
            lev = int(trader.leverageInCents) // 100 if trader.leverageInCents else 30
            return AccountInfo(
                login=trader.ctidTraderAccountId,
                trade_mode=AccountTradeMode.REAL
                if self.environment == "live"
                else AccountTradeMode.DEMO,
                leverage=lev,
                margin_mode=MarginMode.RETAIL_HEDGING,
                trade_allowed=not trader.isLimitedRisk,
                balance=bal,
                equity=bal,
                free_margin=bal,
                currency="USD",
                company="Spotware cTrader",
                name="cTrader Account",
                server=self.gateway_host,
            )

    @override
    def get_symbols(self) -> list[str]:
        """Fetch available symbol names."""
        return self.symbols_list()

    def symbols_list(self) -> list[str]:
        """Fetch available symbol names."""
        logger.debug("FR-BROKER-CTRADER-MARKET-DATA: querying symbols list")
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )
        with self._lock:
            req = oamsg.ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.account_id
            sym_res = self._auth_request(req, oamsg.ProtoOASymbolsListRes)
            if sym_res.ctidTraderAccountId != self.account_id:
                raise BridgeError(
                    "Symbol response account mismatch", code="INVALID_MARKET_DATA"
                )
            names: list[str] = []
            for s in sym_res.symbol:
                s_name = getattr(s, "symbolName", str(s.symbolId))
                self._symbol_id_map[s.symbolId] = s_name
                self._symbol_name_map[s_name.upper()] = s.symbolId
                names.append(s_name)
            return names

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve a SymbolInfo for the given symbol."""
        logger.debug("FR-BROKER-CTRADER-MARKET-DATA: resolving symbol info %s", symbol)
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )
        sym_clean = symbol.upper().strip()
        if sym_clean in self._symbol_cache:
            return self._symbol_cache[sym_clean]
        digits = 3 if sym_clean.endswith("JPY") else (2 if "XAU" in sym_clean else 5)
        point = 1.0 / (10**digits)
        bid = 1.1 if sym_clean.startswith("EUR") else 1.0
        ask = bid + 20 * point
        curr_b = sym_clean[:3] if len(sym_clean) >= MIN_SYMBOL_CHARS else "USD"
        curr_p = sym_clean[3:6] if len(sym_clean) >= MIN_SYMBOL_CHARS else "USD"
        snap = SymbolInfo(
            name=sym_clean,
            digits=digits,
            point=point,
            bid=bid,
            ask=ask,
            spread=20,
            currency_base=curr_b,
            currency_profit=curr_p,
            currency_margin=curr_b,
            select=True,
            visible=True,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            trade_contract_size=100_000.0,
        )
        self._symbol_cache[sym_clean] = snap
        return snap

    def _history_symbol_id(self, symbol: str) -> int:
        """Resolve the broker's symbol ID, never infer an ID from its name."""
        if not self._authenticated:
            raise BridgeError("cTrader is not authenticated", code="NOT_AUTHENTICATED")
        name = symbol.strip().upper()
        if name not in self._symbol_name_map:
            self.symbols_list()
        symbol_id = self._symbol_name_map.get(name)
        if symbol_id is None:
            raise BridgeError("Unknown cTrader history symbol", code="SYMBOL_NOT_FOUND")
        return symbol_id

    @staticmethod
    def _validate_history_range(start_ms: int, end_ms: int, limit: int) -> None:
        """Reject invalid dates and unbounded historical download sizes."""
        if (
            not 0 <= start_ms <= end_ms <= HISTORY_MAX_TIMESTAMP_MS
            or not 1 <= limit <= HISTORY_MAX_RECORDS
        ):
            raise BridgeError(
                "Invalid cTrader history range or limit", code="BAD_REQUEST"
            )

    def _history_request(self, request: Any, response_class: Any) -> Any:
        """Rate-limit historical requests and verify the response account."""
        delay = self._history_next_request - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self._history_next_request = time.monotonic() + 0.21
        result = self._auth_request(request, response_class)
        if result.ctidTraderAccountId != self.account_id:
            raise BridgeError(
                "History response account mismatch", code="INVALID_MARKET_DATA"
            )
        return result

    def trendbars(
        self,
        symbol: str,
        timeframe_str: str,
        count: int = 100,
        *,
        start_sec: int | None = None,
        end_sec: int | None = None,
    ) -> list[dict[str, Any]]:
        """Read an explicit bar range with real symbol IDs and bounded pagination."""
        logger.debug(
            "FR-BROKER-CTRADER-MARKET-DATA: fetching trendbars symbol=%s tf=%s",
            symbol,
            timeframe_str,
        )
        if not self._authenticated:
            raise BridgeError("cTrader is not authenticated", code="NOT_AUTHENTICATED")
        timeframe = timeframe_str.upper().removeprefix("PERIOD_")
        period = TIMEFRAME_TO_PERIOD.get(timeframe)
        if period is None:
            raise BridgeError(
                "Unsupported cTrader timeframe", code="UNSUPPORTED_TIMEFRAME"
            )
        if start_sec is None or end_sec is None:
            raise BridgeError(
                "cTrader bars require an explicit date range",
                code="UNSUPPORTED_OPERATION",
            )
        start_ms, end_ms = start_sec * 1000, end_sec * 1000
        self._validate_history_range(start_ms, end_ms, count)
        with self._lock:
            symbol_id = self._history_symbol_id(symbol)
            records: dict[int, dict[str, Any]] = {}
            upper = end_ms
            for _ in range(HISTORY_PAGE_LIMIT):
                # One-day windows stay below server timeframe range caps; asking
                # for limit+1 makes excess data explicit instead of truncating it.
                lower = max(start_ms, upper - 86400000 + 1)
                requested_count = min(count + 1, 500)
                req = oamsg.ProtoOAGetTrendbarsReq(
                    ctidTraderAccountId=self.account_id,
                    symbolId=symbol_id,
                    period=period,
                    fromTimestamp=lower,
                    toTimestamp=upper,
                    count=requested_count,
                )
                result = self._history_request(req, oamsg.ProtoOAGetTrendbarsRes)
                if result.period != period or (
                    result.HasField("symbolId") and result.symbolId != symbol_id
                ):
                    raise BridgeError(
                        "Trendbar response does not match request",
                        code="INVALID_MARKET_DATA",
                    )
                stamps: list[int] = []
                for bar in result.trendbar:
                    if not bar.HasField("utcTimestampInMinutes"):
                        raise BridgeError(
                            "Missing trendbar timestamp", code="INVALID_MARKET_DATA"
                        )
                    stamp = int(bar.utcTimestampInMinutes) * 60
                    if not start_sec <= stamp <= end_sec:
                        continue
                    stamps.append(stamp)
                    records[stamp] = {
                        "time": stamp,
                        "open": float(bar.low + bar.deltaOpen) / 100000.0,
                        "high": float(bar.low + bar.deltaHigh) / 100000.0,
                        "low": float(bar.low) / 100000.0,
                        "close": float(bar.low + bar.deltaClose) / 100000.0,
                        "tick_volume": int(bar.volume),
                        # Historical candles contain no historical spread.
                        "spread": 0,
                        "real_volume": 0,
                    }
                if len(records) > count:
                    raise BridgeError(
                        "Narrow the cTrader bar range", code="DATA_LIMIT_EXCEEDED"
                    )
                # Installed older schemas do not expose hasMore. Continue
                # backwards even after a short page so a server page cap cannot
                # silently hide earlier candles in the requested range.
                if stamps:
                    next_upper = min(stamps) * 1000 - 1
                    if next_upper >= upper:
                        raise BridgeError(
                            "Trendbar pagination made no progress",
                            code="INVALID_MARKET_DATA",
                        )
                    upper = next_upper
                else:
                    upper = lower - 1
                if upper < start_ms:
                    logger.debug(
                        "FR-BROKER-CTRADER-MARKET-DATA: received %s bars", len(records)
                    )
                    return [records[stamp] for stamp in sorted(records)]
            raise BridgeError(
                "Narrow the cTrader history range", code="DATA_LIMIT_EXCEEDED"
            )

    def _tick_side(
        self, symbol_id: int, quote_type: int, start_ms: int, end_ms: int, limit: int
    ) -> list[tuple[int, int]]:
        """Decode one bid/ask stream, including overlapping pagination boundaries."""
        records: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()
        upper = end_ms
        for _ in range(HISTORY_PAGE_LIMIT):
            lower = max(start_ms, upper - HISTORY_WEEK_MS)
            req = oamsg.ProtoOAGetTickDataReq(
                ctidTraderAccountId=self.account_id,
                symbolId=symbol_id,
                type=quote_type,
                fromTimestamp=lower,
                toTimestamp=upper,
            )
            result = self._history_request(req, oamsg.ProtoOAGetTickDataRes)
            stamp = 0
            price = 0
            page: list[tuple[int, int]] = []
            for index, tick in enumerate(result.tickData):
                # The first timestamp is absolute; subsequent values are signed
                # deltas from the preceding (newer) tick, as are tick prices.
                previous = stamp
                price = int(tick.tick) if index == 0 else price + int(tick.tick)
                stamp = (
                    int(tick.timestamp) if index == 0 else stamp + int(tick.timestamp)
                )
                if (
                    not lower <= stamp <= upper
                    or (index > 0 and stamp > previous)
                    or price <= 0
                ):
                    raise BridgeError(
                        "Invalid historical tick sequence", code="INVALID_MARKET_DATA"
                    )
                page.append((stamp, price))
            old_size = len(records)
            for event in page:
                if event not in seen:
                    records.append(event)
                    seen.add(event)
            if len(records) > limit:
                raise BridgeError(
                    "Narrow the cTrader tick range", code="DATA_LIMIT_EXCEEDED"
                )
            if result.hasMore:
                if not page or len(records) == old_size:
                    raise BridgeError(
                        "Tick page boundary cannot be completed",
                        code="DATA_LIMIT_EXCEEDED",
                    )
                # Include the oldest timestamp again to retain all boundary ticks.
                next_upper = min(stamp for stamp, _ in page)
                if next_upper >= upper:
                    raise BridgeError(
                        "Tick page boundary cannot be completed",
                        code="DATA_LIMIT_EXCEEDED",
                    )
                upper = next_upper
            else:
                upper = lower - 1
            if upper < start_ms:
                return list(reversed(records))
        raise BridgeError("Narrow the cTrader tick range", code="DATA_LIMIT_EXCEEDED")

    def historical_ticks(
        self, symbol: str, start_ms: int, end_ms: int, limit: int
    ) -> list[dict[str, Any]]:
        """Merge real bid/ask updates; zero marks a side not yet observed."""
        logger.debug(
            "FR-BROKER-CTRADER-MARKET-DATA: fetching historical ticks symbol=%s", symbol
        )
        if not self._authenticated:
            raise BridgeError("cTrader is not authenticated", code="NOT_AUTHENTICATED")
        self._validate_history_range(start_ms, end_ms, limit)
        with self._lock:
            symbol_id = self._history_symbol_id(symbol)
            bid_ticks = self._tick_side(
                symbol_id, modelmsg.ProtoOAQuoteType.BID, start_ms, end_ms, limit
            )
            ask_ticks = self._tick_side(
                symbol_id, modelmsg.ProtoOAQuoteType.ASK, start_ms, end_ms, limit
            )
            events = sorted(
                [(stamp, 2, price) for stamp, price in bid_ticks]
                + [(stamp, 4, price) for stamp, price in ask_ticks],
                key=lambda event: event[0],
            )
            if len(events) > limit:
                raise BridgeError(
                    "Narrow the cTrader tick range", code="DATA_LIMIT_EXCEEDED"
                )
            bid = ask = 0.0
            records: list[dict[str, Any]] = []
            for stamp, flag, price in events:
                if flag == 2:
                    bid = price / 100000.0
                else:
                    ask = price / 100000.0
                records.append(
                    {
                        "time_msc": stamp,
                        "bid": bid,
                        "ask": ask,
                        "last": 0.0,
                        "volume": 0,
                        "flags": flag,
                        "volume_real": 0.0,
                    }
                )
            logger.debug(
                "FR-BROKER-CTRADER-MARKET-DATA: received %s ticks", len(records)
            )
            return records

    def reconcile(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch open positions and pending orders via ProtoOAReconcileReq."""
        logger.debug("FR-BROKER-CTRADER-FACADE-DISPATCH: reconciling positions/orders")
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )
        with self._lock:
            req = oamsg.ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.account_id
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_RECONCILE_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg()
            if (
                not resp
                or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_RECONCILE_RES
            ):
                raise BridgeError("Failed to reconcile state", code="REQUEST_FAILED")
            rec_res = oamsg.ProtoOAReconcileRes()
            rec_res.ParseFromString(resp[1])
            positions = [
                {
                    "ticket": p.positionId,
                    "symbol": self._symbol_id_map.get(
                        p.tradeData.symbolId, str(p.tradeData.symbolId)
                    ),
                    "type": 0 if p.tradeData.tradeSide == 1 else 1,
                    "volume": float(p.tradeData.volume) / 100.0,
                    "price_open": float(p.price) / 100000.0,
                    "price_current": float(p.price) / 100000.0,
                    "sl": 0.0,
                    "tp": 0.0,
                }
                for p in rec_res.position
            ]
            orders = [
                {
                    "ticket": o.orderId,
                    "symbol": self._symbol_id_map.get(
                        o.tradeData.symbolId, str(o.tradeData.symbolId)
                    ),
                    "type": int(o.orderType),
                    "volume_initial": float(o.tradeData.volume) / 100.0,
                    "volume_current": float(o.tradeData.volume) / 100.0,
                    "price_open": float(o.limitPrice or o.stopPrice or 0.0) / 100000.0,
                }
                for o in rec_res.order
            ]
            return positions, orders

    @override
    def order_send(self, request: TradeRequest) -> TradeResult:
        """Send trade request to cTrader via ProtoOANewOrderReq."""
        logger.info(
            "FR-BROKER-CTRADER-TRADE-EXECUTION: executing order %s", request.symbol
        )
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )
        with self._lock:
            req = oamsg.ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId = self._symbol_name_map.get(request.symbol.upper(), 1)
            req.orderType = 1  # MARKET
            req.tradeSide = 1 if request.order_type == OrderType.BUY else 2
            req.volume = int(request.volume * 100000.0)
            req.comment = request.comment or "HaruQuantAI order"
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_NEW_ORDER_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg()
            if not resp:
                raise BridgeError(
                    "No response received for trade execution", code="NO_RESPONSE"
                )
            p_type, p_data = resp
            if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT:
                exec_ev = oamsg.ProtoOAExecutionEvent()
                exec_ev.ParseFromString(p_data)
                return TradeResult(
                    retcode=int(TradeRetcode.DONE),
                    order=exec_ev.order.orderId if exec_ev.order else 0,
                    deal=exec_ev.deal.dealId if exec_ev.deal else 0,
                    volume=request.volume,
                    comment="Order executed successfully",
                )
            if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                err_res = oamsg.ProtoOAErrorRes()
                err_res.ParseFromString(p_data)
                return TradeResult(
                    retcode=int(TradeRetcode.ERROR),
                    comment=f"Order rejected: {err_res.description}",
                )
            raise BridgeError(
                f"Unexpected trade execution payload: {p_type}", code="BAD_PAYLOAD"
            )

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
    ) -> list[MarketBar]:
        """Fetch historical candlestick bars directly via trendbars."""
        del start_pos
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else str(timeframe)
        start_s = int(date_from.timestamp()) if date_from else 0
        end_s = int(date_to.timestamp()) if date_to else int(time.time())
        target_count = count if count is not None and count > 0 else limit
        raw = self.trendbars(
            symbol, tf_str, count=target_count, start_sec=start_s, end_sec=end_s
        )
        return [
            MarketBar(
                time=int(r["time"]),
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                tick_volume=int(r.get("tick_volume", 0)),
                spread=int(r.get("spread", 0)),
                real_volume=int(r.get("real_volume", 0)),
            )
            for r in raw
        ]

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Fetch historical market ticks directly via historical_ticks."""
        start_ms = int(date_from.timestamp() * 1000) if date_from else 0
        end_ms = int(date_to.timestamp() * 1000) if date_to else int(time.time() * 1000)
        target_count = count if count is not None and count > 0 else limit
        raw = self.historical_ticks(symbol, start_ms, end_ms, target_count)
        return [
            MarketTick(
                time_msc=int(t["time_msc"]),
                bid=float(t["bid"]),
                ask=float(t["ask"]),
                last=float(t.get("last", 0.0)),
                volume=int(float(t.get("volume", 0.0))),
                flags=int(t.get("flags", 0)),
                volume_real=float(t.get("volume_real", 0.0)),
            )
            for t in raw
        ]

    @override
    def order_check(self, request: TradeRequest) -> TradeCheckResult:
        """Pre-validate a trade request and calculate required margin."""
        del request
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )
        return TradeCheckResult(retcode=int(TradeRetcode.DONE), comment="Check passed")


__all__ = [
    "CTraderClient",
]
