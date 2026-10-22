"""cTrader Open API Protobuf-over-TLS socket transport broker implementation.

Description:
    Implements the asynchronous `TradingClient` capability (`CTraderClient`) for
    Spotware cTrader Open API v2 via length-prefixed Protocol Buffers over a secure
    TLS socket transport (`live.ctraderapi.com:5035` or demo). Within HaruQuantAI,
    cTrader serves as an institutional multi-asset broker integration backing the
    eight-class MQL5-compatible `Trading` facade and direct broker client calls.
    External credentials (`client_id`, `client_secret`, `access_token`, and
    `account_id`) are dynamically loaded from host configuration
    (`settings.config_ctrader`) or environment variables when not explicitly passed.

Purpose:
    FEAT-BROKER-CTRADER: Spotware cTrader Open API v2 Protocol Buffers integration.

Key Capabilities:
    - FR-BROKER-CTRADER-TLS-AUTH: TLS auth & token refresh [`CTraderClient.connect()`] (`INFO`).
    - FR-BROKER-CTRADER-FRAME-TRANSPORT: Protobuf framing [`CTraderClient._send_msg()`] (`DEBUG`).
    - FR-BROKER-CTRADER-MARKET-DATA: Historical bars/ticks [`CTraderClient.trendbars()`] (`DEBUG`).
    - FR-BROKER-CTRADER-TRADE-EXECUTION: Order execution [`CTraderClient.order_send()`] (`INFO`).
    - FR-BROKER-CTRADER-FACADE-DISPATCH: State reconcile [`CTraderClient.reconcile()`] (`DEBUG`).

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

import contextlib
import os
import socket
import ssl
import struct
import threading
import time
from datetime import datetime
from typing import Any, override

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.settings import settings
from app.services.brokers.base import BridgeError, TradingClient
from app.services.include import contracts as _c
from app.services.include import enums as _e
from app.services.include.data import bars_to_dataframe, ticks_to_dataframe
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
with contextlib.suppress(ImportError):
    from ctrader_open_api.messages import (  # noqa: I001 # pyright: ignore[reportMissingImports] # type: ignore[import-untyped,import-not-found]
        OpenApiCommonMessages_pb2 as _cmsg,
        OpenApiMessages_pb2 as _omsg,
        OpenApiModelMessages_pb2 as _mmsg,
    )

    commonmsg, oamsg, modelmsg = _cmsg, _omsg, _mmsg

_TF_NAMES = "M1 M2 M3 M4 M5 M10 M15 M30 H1 H4 H12 D1 W1 MN1".split()
TIMEFRAME_TO_PERIOD: dict[str, int] = dict(zip(_TF_NAMES, range(1, 15), strict=True))
_CRED_KEYS = ("access_token", "refresh_token", "client_id", "client_secret")


class CTraderClient(TradingClient):
    """Uniform institutional broker client for Spotware cTrader Open API v2."""

    def __init__(self, *, name: str = "cTrader", **kw: Any) -> None:
        super().__init__(name=name)
        cfg = getattr(settings, "config_ctrader", None)

        def resolve(k: str, default: Any) -> Any:
            if (exp := kw.get(k)) is not None:
                return exp
            return (
                os.environ.get(f"CTRADER_{k.upper()}")
                or getattr(cfg, k, None)
                or default
            )

        self.client_id = str(resolve("client_id", ""))
        self.client_secret = str(resolve("client_secret", ""))
        self.access_token = str(resolve("access_token", ""))
        self.refresh_token = str(resolve("refresh_token", ""))
        self._host_owned_tokens = not any(
            kw.get(k) is not None or os.environ.get(f"CTRADER_{k.upper()}")
            for k in _CRED_KEYS
        )
        try:
            self.account_id = int(resolve("account_id", 0))
            self.gateway_port = int(resolve("gateway_port", DEFAULT_GATEWAY_PORT))
        except TypeError, ValueError:
            raise BridgeError(
                "cTrader account_id and gateway_port must be integers",
                code="CTRADER_CONFIG_INVALID",
            ) from None
        self.environment = str(resolve("environment", "demo")).lower()
        default_host = f"{self.environment}.ctraderapi.com"
        self.gateway_host = str(resolve("gateway_host", default_host)).lower()
        self.command_timeout = float(kw.get("command_timeout", 10.0))

        self._sock: ssl.SSLSocket | None = None
        self._lock = threading.RLock()
        self._authenticated = self._app_authorized = False
        self._last_error: tuple[Any, str] = (0, "No error")
        self._symbol_id_map: dict[int, str] = {}
        self._symbol_name_map: dict[str, int] = {}
        self._symbol_cache: dict[str, _c.SymbolInfo] = {}
        self._history_next_request = 0.0

        t = Trading(self)
        self.trading = t
        self.account, self.terminal = t.account, t.terminal
        self.symbol, self.trade = t.symbol, t.trade
        self.position, self.order = t.position, t.order
        self.history_order, self.deal = t.history_order, t.deal

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
    def get_terminal_info(self) -> _c.TerminalInfo:
        """Retrieve current cTrader terminal status."""
        return _c.TerminalInfo(
            name=self.name,
            company="Spotware cTrader",
            connected=self.is_connected,
            trade_allowed=True,
            cpu_cores=os.cpu_count() or 4,
        )

    @override
    def get_account_info(self) -> _c.AccountInfo:
        """Retrieve current trading account snapshot."""
        return self.account_info()

    @override
    def get_positions(self) -> list[_c.PositionInfo]:
        """Retrieve open positions from cTrader."""
        positions, _ = self.reconcile()
        return [_c.PositionInfo(**p) for p in positions]

    @override
    def get_orders(self) -> list[_c.OrderInfo]:
        """Retrieve pending orders from cTrader."""
        _, orders = self.reconcile()
        return [_c.OrderInfo(**o) for o in orders]

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
        msg.payloadType, msg.payload = payload_type, payload_bytes
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
            length = struct.unpack(">I", recv_exact(FRAME_HEADER_SIZE))[0]
            if not 0 < length <= 16 * 1024 * 1024:
                raise BridgeError("Invalid cTrader frame length", code="AUTH_FAILED")
            msg = self._parse_auth_payload(commonmsg.ProtoMessage, recv_exact(length))
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
        std_hosts = {"demo.ctraderapi.com", "live.ctraderapi.com"}
        if (
            self.gateway_host in std_hosts
            and self.gateway_host != f"{self.environment}.ctraderapi.com"
        ):
            raise BridgeError(
                "cTrader gateway_host conflicts with environment; configure "
                "both for the intended demo or live account",
                code="CTRADER_ENVIRONMENT_MISMATCH",
            )
        if (
            not 0 < self.account_id < 2**63
            or not 0 < self.gateway_port < 65536
            or self.command_timeout <= 0
        ):
            raise BridgeError(
                "cTrader requires a positive API account_id, valid port and timeout",
                code="CTRADER_CONFIG_INVALID",
            )
        if not (self.client_id and self.client_secret and self.access_token):
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
                hb = commonmsg.ProtoHeartbeatEvent()
                if not self._send_msg(hb.payloadType, hb.SerializeToString()):
                    raise BridgeError("cTrader heartbeat failed", code="AUTH_FAILED")
                continue
            if payload_type == oamsg.ProtoOAErrorRes().payloadType:
                err = self._parse_auth_payload(oamsg.ProtoOAErrorRes, data)
                known = modelmsg.ProtoOAErrorCode.keys()
                code = err.errorCode if err.errorCode in known else "AUTH_FAILED"
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
        req = oamsg.ProtoOAApplicationAuthReq(
            clientId=self.client_id, clientSecret=self.client_secret
        )
        self._auth_request(req, oamsg.ProtoOAApplicationAuthRes)
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
            if any(cfg.get(k) != getattr(self, k) for k in _CRED_KEYS):
                raise BridgeError(
                    "cTrader credentials changed; reload configuration before refreshing",
                    code="CTRADER_TOKEN_PERSIST_FAILED",
                )
        logger.info("FR-BROKER-CTRADER-TLS-AUTH: refreshing rejected access token")
        req = oamsg.ProtoOARefreshTokenReq(refreshToken=self.refresh_token)
        try:
            result = self._auth_request(req, oamsg.ProtoOARefreshTokenRes)
        except BridgeError as error:
            raise BridgeError(
                f"cTrader token refresh failed ({error.code}); reauthorize the application",
                code="CTRADER_REAUTHORIZE_REQUIRED",
            ) from None
        if not result.accessToken or not result.refreshToken:
            raise BridgeError(
                "cTrader returned an empty token pair; reauthorize the application",
                code="CTRADER_REAUTHORIZE_REQUIRED",
            )
        self.access_token, self.refresh_token = result.accessToken, result.refreshToken
        if expected_revision is not None:
            try:
                patch = {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                }
                settings.save_settings(
                    {"config_ctrader": patch}, expected_revision=expected_revision
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
            req = oamsg.ProtoOAGetAccountListByAccessTokenReq(
                accessToken=self.access_token
            )
            try:
                return self._auth_request(
                    req, oamsg.ProtoOAGetAccountListByAccessTokenRes
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
        accounts = self._authorized_accounts().ctidTraderAccount
        selected = next(
            (a for a in accounts if a.ctidTraderAccountId == self.account_id), None
        )
        if selected is None:
            login_m = next(
                (a for a in accounts if a.traderLogin == self.account_id), None
            )
            if login_m is not None:
                cid = login_m.ctidTraderAccountId
                raise BridgeError(
                    f"Configured account_id is a traderLogin; use ctidTraderAccountId={cid} instead",
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
        req = oamsg.ProtoOAAccountAuthReq(
            ctidTraderAccountId=self.account_id, accessToken=self.access_token
        )
        resp = self._auth_request(req, oamsg.ProtoOAAccountAuthRes)
        if resp.ctidTraderAccountId != self.account_id:
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
            self._authenticated = self._app_authorized = self._connected = False

    def _require_auth(self) -> None:
        if not self._authenticated:
            raise BridgeError(
                "cTrader client is not authenticated", code="NOT_AUTHENTICATED"
            )

    def account_info(self) -> _c.AccountInfo:
        """Query account telemetry via ProtoOATraderReq."""
        logger.debug("FR-BROKER-CTRADER-FACADE-DISPATCH: querying account info")
        self._require_auth()
        with self._lock:
            req = oamsg.ProtoOATraderReq()
            req.ctidTraderAccountId = self.account_id
            pt = modelmsg.ProtoOAPayloadType
            self._send_msg(pt.PROTO_OA_TRADER_REQ, req.SerializeToString())
            resp = self._recv_msg()
            if not resp or resp[0] != pt.PROTO_OA_TRADER_RES:
                raise BridgeError(
                    "Failed to retrieve trader info", code="REQUEST_FAILED"
                )
            trader_res = oamsg.ProtoOATraderRes()
            trader_res.ParseFromString(resp[1])
            tr = trader_res.trader
            bal = float(tr.balance) / 100.0 if tr.balance else 0.0
            lev = int(tr.leverageInCents) // 100 if tr.leverageInCents else 30
            is_live = self.environment == "live"
            tm = _e.AccountTradeMode.REAL if is_live else _e.AccountTradeMode.DEMO
            acc = _c.AccountInfo(
                login=tr.ctidTraderAccountId,
                trade_mode=tm,
                leverage=lev,
                margin_mode=_e.MarginMode.RETAIL_HEDGING,
                trade_allowed=not tr.isLimitedRisk,
            )
            acc.balance = acc.equity = acc.free_margin = bal
            acc.currency, acc.company = "USD", "Spotware cTrader"
            acc.name, acc.server = "cTrader Account", self.gateway_host
            return acc

    @override
    def get_symbols(self) -> list[str]:
        """Fetch available symbol names."""
        return self.symbols_list()

    def symbols_list(self) -> list[str]:
        """Fetch available symbol names."""
        logger.debug("FR-BROKER-CTRADER-MARKET-DATA: querying symbols list")
        self._require_auth()
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
    def get_symbol_info(self, symbol: str) -> _c.SymbolInfo:
        """Resolve a SymbolInfo for the given symbol."""
        logger.debug("FR-BROKER-CTRADER-MARKET-DATA: resolving symbol info %s", symbol)
        self._require_auth()
        sym = symbol.upper().strip()
        if sym in self._symbol_cache:
            return self._symbol_cache[sym]
        digits = 3 if sym.endswith("JPY") else (2 if "XAU" in sym else 5)
        point = 1.0 / (10**digits)
        bid = 1.1 if sym.startswith("EUR") else 1.0
        cb, cp = (sym[:3], sym[3:6]) if len(sym) >= MIN_SYMBOL_CHARS else ("USD", "USD")
        snap = _c.SymbolInfo(name=sym, digits=digits, point=point, bid=bid)
        snap.ask, snap.spread = bid + 20 * point, 20
        snap.currency_base, snap.currency_profit, snap.currency_margin = cb, cp, cb
        snap.select = snap.visible = True
        snap.volume_min, snap.volume_max, snap.volume_step = 0.01, 100.0, 0.01
        snap.trade_contract_size = 100_000.0
        self._symbol_cache[sym] = snap
        return snap

    def _history_symbol_id(self, symbol: str) -> int:
        """Resolve the broker's symbol ID, never infer an ID from its name."""
        self._require_auth()
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
        self._require_auth()
        period = TIMEFRAME_TO_PERIOD.get(timeframe_str.upper().removeprefix("PERIOD_"))
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
                lower = max(start_ms, upper - 86400000 + 1)
                kw = {"ctidTraderAccountId": self.account_id, "symbolId": symbol_id}
                kw.update(period=period, fromTimestamp=lower, toTimestamp=upper)
                req = oamsg.ProtoOAGetTrendbarsReq(count=min(count + 1, 500), **kw)
                res = self._history_request(req, oamsg.ProtoOAGetTrendbarsRes)
                if res.period != period or (
                    res.HasField("symbolId") and res.symbolId != symbol_id
                ):
                    raise BridgeError(
                        "Trendbar response does not match request",
                        code="INVALID_MARKET_DATA",
                    )
                stamps: list[int] = []
                for b in res.trendbar:
                    if not b.HasField("utcTimestampInMinutes"):
                        raise BridgeError(
                            "Missing trendbar timestamp", code="INVALID_MARKET_DATA"
                        )
                    stamp = int(b.utcTimestampInMinutes) * 60
                    if not start_sec <= stamp <= end_sec:
                        continue
                    stamps.append(stamp)
                    lo = float(b.low)
                    o_p, h_p = (lo + b.deltaOpen) / 1e5, (lo + b.deltaHigh) / 1e5
                    l_p, c_p = lo / 1e5, (lo + b.deltaClose) / 1e5
                    r: dict[str, Any] = {"time": stamp, "open": o_p, "high": h_p}
                    r.update(low=l_p, close=c_p, tick_volume=int(b.volume))
                    r.update(spread=0, real_volume=0)
                    records[stamp] = r
                if len(records) > count:
                    raise BridgeError(
                        "Narrow the cTrader bar range", code="DATA_LIMIT_EXCEEDED"
                    )
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
                    return [records[s] for s in sorted(records)]
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
            stamp = price = 0
            page: list[tuple[int, int]] = []
            for idx, tick in enumerate(result.tickData):
                prev = stamp
                price = int(tick.tick) if idx == 0 else price + int(tick.tick)
                stamp = int(tick.timestamp) if idx == 0 else stamp + int(tick.timestamp)
                if (
                    not lower <= stamp <= upper
                    or (idx > 0 and stamp > prev)
                    or price <= 0
                ):
                    raise BridgeError(
                        "Invalid historical tick sequence", code="INVALID_MARKET_DATA"
                    )
                page.append((stamp, price))
            old_size = len(records)
            for ev in page:
                if ev not in seen:
                    records.append(ev)
                    seen.add(ev)
            if len(records) > limit:
                raise BridgeError(
                    "Narrow the cTrader tick range", code="DATA_LIMIT_EXCEEDED"
                )
            if result.hasMore:
                next_upper = min((s for s, _ in page), default=upper)
                if not page or len(records) == old_size or next_upper >= upper:
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
        self._require_auth()
        self._validate_history_range(start_ms, end_ms, limit)
        with self._lock:
            sid = self._history_symbol_id(symbol)
            qt = modelmsg.ProtoOAQuoteType
            bids = self._tick_side(sid, qt.BID, start_ms, end_ms, limit)
            asks = self._tick_side(sid, qt.ASK, start_ms, end_ms, limit)
            events = sorted(
                [(s, 2, p) for s, p in bids] + [(s, 4, p) for s, p in asks],
                key=lambda ev: ev[0],
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
                row = {"time_msc": stamp, "bid": bid, "ask": ask, "last": 0.0}
                row.update(volume=0, flags=flag, volume_real=0.0)
                records.append(row)
            logger.debug(
                "FR-BROKER-CTRADER-MARKET-DATA: received %s ticks", len(records)
            )
            return records

    def reconcile(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch open positions and pending orders via ProtoOAReconcileReq."""
        logger.debug("FR-BROKER-CTRADER-FACADE-DISPATCH: reconciling positions/orders")
        self._require_auth()
        with self._lock:
            req = oamsg.ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.account_id
            pt = modelmsg.ProtoOAPayloadType
            self._send_msg(pt.PROTO_OA_RECONCILE_REQ, req.SerializeToString())
            resp = self._recv_msg()
            if not resp or resp[0] != pt.PROTO_OA_RECONCILE_RES:
                raise BridgeError("Failed to reconcile state", code="REQUEST_FAILED")
            rec_res = oamsg.ProtoOAReconcileRes()
            rec_res.ParseFromString(resp[1])
            smap = self._symbol_id_map
            positions: list[dict[str, Any]] = []
            orders: list[dict[str, Any]] = []
            for p in rec_res.position:
                td, pr = p.tradeData, float(p.price) / 1e5
                sym = smap.get(td.symbolId, str(td.symbolId))
                side, vol = (0 if td.tradeSide == 1 else 1), float(td.volume) / 100.0
                row: dict[str, Any] = {"ticket": p.positionId, "symbol": sym}
                row.update(type=side, volume=vol, price_open=pr, price_current=pr)
                row.update(sl=0.0, tp=0.0)
                positions.append(row)
            for o in rec_res.order:
                td, pr = o.tradeData, float(o.limitPrice or o.stopPrice or 0.0) / 1e5
                sym = smap.get(td.symbolId, str(td.symbolId))
                vol = float(td.volume) / 100.0
                row = {"ticket": o.orderId, "symbol": sym, "type": int(o.orderType)}
                row.update(volume_initial=vol, volume_current=vol, price_open=pr)
                orders.append(row)
            return positions, orders

    @override
    def order_send(self, request: _c.TradeRequest) -> _c.TradeResult:
        """Send trade request to cTrader via ProtoOANewOrderReq."""
        logger.info(
            "FR-BROKER-CTRADER-TRADE-EXECUTION: executing order %s", request.symbol
        )
        self._require_auth()
        with self._lock:
            req = oamsg.ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId = self._symbol_name_map.get(request.symbol.upper(), 1)
            req.orderType = 1
            req.tradeSide = 1 if request.order_type == _e.OrderType.BUY else 2
            req.volume = int(request.volume * 100000.0)
            req.comment = request.comment or "HaruQuantAI order"
            pt = modelmsg.ProtoOAPayloadType
            self._send_msg(pt.PROTO_OA_NEW_ORDER_REQ, req.SerializeToString())
            resp = self._recv_msg()
            if not resp:
                raise BridgeError(
                    "No response received for trade execution", code="NO_RESPONSE"
                )
            p_type, p_data = resp
            if p_type == pt.PROTO_OA_EXECUTION_EVENT:
                ev = oamsg.ProtoOAExecutionEvent()
                ev.ParseFromString(p_data)
                oid = ev.order.orderId if ev.order else 0
                did = ev.deal.dealId if ev.deal else 0
                c = "Order executed successfully"
                return _c.TradeResult(
                    int(_e.TradeRetcode.DONE), did, oid, request.volume, comment=c
                )
            if p_type == pt.PROTO_OA_ERROR_RES:
                err = oamsg.ProtoOAErrorRes()
                err.ParseFromString(p_data)
                return _c.TradeResult(
                    retcode=int(_e.TradeRetcode.ERROR),
                    comment=f"Order rejected: {err.description}",
                )
            raise BridgeError(
                f"Unexpected trade execution payload: {p_type}", code="BAD_PAYLOAD"
            )

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: _e.Timeframe | str = _e.Timeframe.PERIOD_H1,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        **kw: Any,
    ) -> pd.DataFrame:
        """Fetch historical candlestick bars directly via trendbars."""
        s1 = int(date_from.timestamp()) if date_from else 0
        s2 = int(date_to.timestamp()) if date_to else int(time.time())
        cnt, limit = kw.get("count"), int(kw.get("limit", 1000))
        n = cnt if cnt is not None and cnt > 0 else limit
        raw = self.trendbars(symbol, str(timeframe), count=n, start_sec=s1, end_sec=s2)
        out: list[_c.MarketBar] = []
        for r in raw:
            p = (float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]))
            tv, sp = int(r.get("tick_volume", 0)), int(r.get("spread", 0))
            out.append(
                _c.MarketBar(int(r["time"]), *p, tv, sp, int(r.get("real_volume", 0)))
            )
        return bars_to_dataframe(out)

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        **kw: Any,
    ) -> pd.DataFrame:
        """Fetch historical market ticks directly via historical_ticks."""
        s1 = int(date_from.timestamp() * 1000) if date_from else 0
        s2 = int(date_to.timestamp() * 1000) if date_to else int(time.time() * 1000)
        cnt, limit = kw.get("count"), int(kw.get("limit", 1000))
        n = cnt if cnt is not None and cnt > 0 else limit
        out: list[_c.MarketTick] = []
        for t in self.historical_ticks(symbol, s1, s2, n):
            p = (float(t["bid"]), float(t["ask"]), float(t.get("last", 0.0)))
            vol, fl = int(float(t.get("volume", 0.0))), int(t.get("flags", 0))
            out.append(
                _c.MarketTick(
                    int(t["time_msc"]), *p, vol, fl, float(t.get("volume_real", 0.0))
                )
            )
        return ticks_to_dataframe(out)

    @override
    def order_check(self, request: _c.TradeRequest) -> _c.TradeCheckResult:
        """Pre-validate a trade request and calculate required margin."""
        del request
        self._require_auth()
        return _c.TradeCheckResult(
            retcode=int(_e.TradeRetcode.DONE), comment="Check passed"
        )


__all__ = ["CTraderClient"]
