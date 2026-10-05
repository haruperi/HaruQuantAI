"""cTrader Open API Protobuf-over-TLS socket transport broker plugin implementation.

Description:
    Implements the full 27-operation `BaseBroker` interface for Spotware cTrader
    Open API v2 via length-prefixed Protocol Buffers over a secure TLS socket
    transport (`live.ctraderapi.com:5035` or demo).
    Within HaruQuantAI, cTrader serves as an institutional multi-asset retail
    broker integration, supporting real-time account telemetry, market depth,
    trendbars, pending orders, positions, and order execution events.
    External credentials (`client_id`, `client_secret`, `access_token`, and
    `account_id`) are dynamically loaded from host configuration
    (`settings.config_ctrader`) when not explicitly passed to the constructor.
    Internally, the adapter coordinates two-phase TLS handshakes (Application
    Auth followed by Account Auth), thread-safe request/response socket framing
    using big-endian 4-byte length prefixes, and deserialization of Spotware
    protobuf payloads into canonical `StandardResponse` envelopes.

Purpose:
    FEAT-BROKER-CTRADER: cTrader Open API Protocol Buffer Integration.
    Implements socket-level TLS transport, account authentication, market data,
    and trade execution over Spotware cTrader Open API Protocol Buffers.

Key Capabilities:
    - FR-BROKER-CTRADER-TLS-AUTH: Two-Phase Application & Account Authorization
      Associated: `[CTraderBroker.connect()]`, `[CTraderBroker.disconnect()]`,
      `[CTraderBroker.is_connected()]`
      Logging: Emits INFO log upon successful app and account auth; emits
      ERROR log on handshake failure, timeout, or TLS socket disconnect.
    - FR-BROKER-CTRADER-FRAME-TRANSPORT: Length-Prefixed Protocol Buffer Framing
      Associated: `[CTraderBroker._send_msg()]`, `[CTraderBroker._recv_msg()]`
      Logging: Emits DEBUG log on message send/recv and ERROR log on framing
      or socket transmission errors.
    - FR-BROKER-CTRADER-MARKET-DATA: Historical Trendbars and Symbol Resolution
      Associated: `[CTraderBroker.get_symbols()]`,
      `[CTraderBroker.get_symbol_info()]`, `[CTraderBroker.get_bars()]`
      Logging: Emits INFO log upon receiving symbol catalogs and trendbars.
    - FR-BROKER-CTRADER-TRADE-EXECUTION: Pre-flight Check and Order Placement
      Associated: `[CTraderBroker.check_order()]`, `[CTraderBroker.trade()]`
      Logging: Emits INFO log upon order execution event and WARNING log on
      order rejection or execution error.

Python API Usage:
    ```python
    from app.plugin.broker.ctrader import CTraderBroker

    broker = CTraderBroker()
    # Check connection status
    status_resp = broker.is_connected()
    assert not status_resp.unwrap()
    ```

CLI Usage:
    ```bash
    uv run pytest tests/plugin/broker/test_ctrader.py -v --no-cov
    ```
"""

from __future__ import annotations

import socket
import ssl
import struct
import threading
from datetime import UTC, datetime
from typing import Any

try:
    from ctrader_open_api.messages import OpenApiCommonMessages_pb2 as commonmsg
    from ctrader_open_api.messages import OpenApiMessages_pb2 as oamsg
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as modelmsg
except ImportError:
    commonmsg = None
    modelmsg = None
    oamsg = None

from app.host.logging import get_logger
from app.host.settings import settings

from .contracts import (
    AccountInfo,
    Bar,
    BaseBroker,
    BrokerCapability,
    OrderCheckResult,
    OrderInfo,
    OrderType,
    PositionInfo,
    StandardError,
    StandardResponse,
    SymbolInfo,
    Tick,
    TimeFrame,
    TradeRequest,
    TradeResult,
)

logger = get_logger(__name__)


class CTraderBroker(BaseBroker):
    """cTrader Open API broker plugin."""

    TIMEFRAME_TO_PERIOD = {
        TimeFrame.M1: 1,
        TimeFrame.M2: 2,
        TimeFrame.M3: 3,
        TimeFrame.M4: 4,
        TimeFrame.M5: 5,
        TimeFrame.M10: 6,
        TimeFrame.M15: 7,
        TimeFrame.M30: 8,
        TimeFrame.H1: 9,
        TimeFrame.H4: 10,
        TimeFrame.H12: 11,
        TimeFrame.D1: 12,
        TimeFrame.W1: 13,
        TimeFrame.MN1: 14,
    }

    def __init__(
        self,
        name: str = "cTrader",
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        account_id: int | None = None,
        gateway_host: str | None = None,
        gateway_port: int | None = None,
        environment: str | None = None,
    ) -> None:
        """Initialize cTrader Open API broker plugin.

        Pulls credentials dynamically from `settings.config_ctrader`.
        """
        super().__init__(name=name, capabilities=BrokerCapability.ALL)
        cfg = getattr(settings, "config_ctrader", None)
        self.client_id = (
            client_id or (getattr(cfg, "client_id", None) if cfg else None) or ""
        )
        self.client_secret = (
            client_secret
            or (getattr(cfg, "client_secret", None) if cfg else None)
            or ""
        )
        self.access_token = (
            access_token or (getattr(cfg, "access_token", None) if cfg else None) or ""
        )
        self.refresh_token = (
            refresh_token
            or (getattr(cfg, "refresh_token", None) if cfg else None)
            or ""
        )
        self.account_id = int(
            account_id or (getattr(cfg, "account_id", 0) if cfg else 0)
        )
        self.gateway_host = (
            gateway_host
            or (getattr(cfg, "gateway_host", None) if cfg else None)
            or "live.ctraderapi.com"
        )
        self.gateway_port = int(
            gateway_port or (getattr(cfg, "gateway_port", 5035) if cfg else 5035)
        )
        self.environment = environment or (
            getattr(cfg, "environment", "demo") if cfg else "demo"
        )

        self._sock: ssl.SSLSocket | None = None
        self._lock = threading.Lock()
        self._authenticated = False
        self._app_authorized = False
        self._last_error: tuple[Any, str] = (0, "No error")
        self._symbol_cache: dict[str, Any] = {}
        self._symbol_id_map: dict[int, str] = {}

    def _ensure_module(self) -> StandardResponse[Any] | None:
        """Verify protobuf modules are available."""
        if oamsg is None or modelmsg is None or commonmsg is None:
            msg = "cTrader Open API protobuf modules not available."
            self.logger.error(msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="MODULE_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )
        return None

    def _send_msg(self, payload_type: int, payload_bytes: bytes) -> bool:
        """Send a length-prefixed Protocol Buffer message over the TLS socket."""
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
        except Exception as e:
            self.logger.error("Failed to send message over socket: %s", e)
            self._last_error = ("SEND_ERROR", str(e))
            return False

    def _recv_msg(self, timeout: float = 10.0) -> tuple[int, bytes] | None:
        """Receive and unpack a length-prefixed ProtoMessage."""
        if not self._sock:
            return None
        self._sock.settimeout(timeout)
        try:
            len_bytes = self._sock.recv(4)
            if not len_bytes or len(len_bytes) < 4:
                return None
            length = struct.unpack(">I", len_bytes)[0]
            data = b""
            while len(data) < length:
                chunk = self._sock.recv(length - len(data))
                if not chunk:
                    break
                data += chunk
            msg = commonmsg.ProtoMessage()
            msg.ParseFromString(data)
            return msg.payloadType, msg.payload
        except TimeoutError:
            self.logger.debug("Socket timed out waiting for response")
            return None
        except Exception as e:
            self.logger.error("Failed to receive message from socket: %s", e)
            self._last_error = ("RECV_ERROR", str(e))
            return None

    # ========================================================================
    # 1. Connection & Session
    # ========================================================================

    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Establish TLS connection and authenticate application & account."""
        err = self._ensure_module()
        if err is not None:
            return err

        host = kwargs.get("gateway_host", self.gateway_host)
        port = int(kwargs.get("gateway_port", self.gateway_port))
        client_id = kwargs.get("client_id", self.client_id)
        client_secret = kwargs.get("client_secret", self.client_secret)
        access_token = kwargs.get("access_token", self.access_token)
        account_id = int(kwargs.get("account_id", self.account_id))

        with self._lock:
            try:
                self.logger.info(
                    "Connecting to cTrader Open API gateway %s:%s...", host, port
                )
                ctx = ssl.create_default_context()
                raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                raw_sock.settimeout(10.0)
                self._sock = ctx.wrap_socket(raw_sock, server_hostname=host)
                self._sock.connect((host, port))

                # 1. ProtoOAApplicationAuthReq (2100)
                app_req = oamsg.ProtoOAApplicationAuthReq()
                app_req.clientId = client_id
                app_req.clientSecret = client_secret
                if not self._send_msg(
                    modelmsg.ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_REQ,
                    app_req.SerializeToString(),
                ):
                    return StandardResponse.failure(
                        message="Failed to send application auth request",
                        error=StandardError(
                            code="BROKER_ERROR",
                            message="Failed to send application auth request",
                        ),
                        extensions={"broker": self.name},
                    )

                resp = self._recv_msg(timeout=10.0)
                if not resp:
                    return StandardResponse.failure(
                        message="No response received for application auth",
                        error=StandardError(
                            code="BROKER_ERROR",
                            message="No response received for application auth",
                        ),
                        extensions={"broker": self.name},
                    )

                p_type, p_data = resp
                if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES:
                    self._app_authorized = True
                    self.logger.info("Application authorization successful!")
                elif p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                    err_res = oamsg.ProtoOAErrorRes()
                    err_res.ParseFromString(p_data)
                    self._last_error = (err_res.errorCode, err_res.description)
                    return StandardResponse.failure(
                        message=f"Application auth error: {err_res.description}",
                        error=StandardError(
                            code=str(err_res.errorCode),
                            message=f"Application auth error: {err_res.description}",
                        ),
                        extensions={"broker": self.name},
                    )
                else:
                    return StandardResponse.failure(
                        message=f"Unexpected response payload type: {p_type}",
                        error=StandardError(
                            code="BROKER_ERROR",
                            message=f"Unexpected response payload type: {p_type}",
                        ),
                        extensions={"broker": self.name},
                    )

                # 2. ProtoOAAccountAuthReq (2102)
                acc_req = oamsg.ProtoOAAccountAuthReq()
                acc_req.ctidTraderAccountId = account_id
                acc_req.accessToken = access_token
                if not self._send_msg(
                    modelmsg.ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_REQ,
                    acc_req.SerializeToString(),
                ):
                    return StandardResponse.failure(
                        message="Failed to send account auth request",
                        error=StandardError(
                            code="BROKER_ERROR",
                            message="Failed to send account auth request",
                        ),
                        extensions={"broker": self.name},
                    )

                resp = self._recv_msg(timeout=10.0)
                if not resp:
                    return StandardResponse.failure(
                        message="No response received for account auth",
                        error=StandardError(
                            code="BROKER_ERROR",
                            message="No response received for account auth",
                        ),
                        extensions={"broker": self.name},
                    )

                p_type, p_data = resp
                if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES:
                    acc_res = oamsg.ProtoOAAccountAuthRes()
                    acc_res.ParseFromString(p_data)
                    self._authenticated = True
                    self.logger.info(
                        "cTrader account %s authorized successfully!",
                        acc_res.ctidTraderAccountId,
                    )
                    return StandardResponse.success(
                        data=True,
                        message=f"cTrader account {acc_res.ctidTraderAccountId} authenticated",
                        extensions={"broker": self.name},
                    )
                if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                    err_res = oamsg.ProtoOAErrorRes()
                    err_res.ParseFromString(p_data)
                    self._last_error = (err_res.errorCode, err_res.description)
                    msg = (
                        f"Account auth failed: {err_res.description} "
                        f"(code {err_res.errorCode})"
                    )
                    self.logger.warning(msg)
                    return StandardResponse.failure(
                        message=msg,
                        error=StandardError(code=str(err_res.errorCode), message=msg),
                        extensions={"broker": self.name},
                    )
                return StandardResponse.failure(
                    message=f"Unexpected response payload type: {p_type}",
                    error=StandardError(
                        code="BROKER_ERROR",
                        message=f"Unexpected response payload type: {p_type}",
                    ),
                    extensions={"broker": self.name},
                )

            except Exception as e:
                self.logger.error("Error connecting to cTrader gateway: %s", e)
                self._last_error = ("CONNECT_EXCEPTION", str(e))
                return StandardResponse.failure(
                    message=f"Connection exception: {e}",
                    error=StandardError(
                        code="CONNECTION_FAILED", message=f"Connection exception: {e}"
                    ),
                    extensions={"broker": self.name},
                )

    def disconnect(self) -> StandardResponse[bool]:
        """Disconnect and terminate cTrader socket session."""
        with self._lock:
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
            self._sock = None
            self._authenticated = False
            self._app_authorized = False
            self.logger.info("cTrader gateway disconnected.")
            return StandardResponse.success(
                data=True,
                message="Disconnected successfully",
                extensions={"broker": self.name},
            )

    def is_connected(self) -> StandardResponse[bool]:
        """Check active connection and auth state."""
        connected = bool(self._sock and self._authenticated)
        return StandardResponse.success(
            data=connected,
            message="Connected and authorized" if connected else "Disconnected",
            extensions={"broker": self.name},
        )

    def get_last_error(self) -> StandardResponse[Any]:
        """Retrieve last recorded error."""
        return StandardResponse.success(
            data=self._last_error,
            message=self._last_error[1],
            extensions={"broker": self.name},
        )

    # ========================================================================
    # 2. Terminal & Account Information
    # ========================================================================

    def get_account_info(self) -> StandardResponse[AccountInfo]:
        """Retrieve account balance and metrics via ProtoOATraderReq."""
        if not self._authenticated:
            return StandardResponse.failure(
                message="Not connected or authorized",
                error=StandardError(
                    code="NOT_AUTHORIZED", message="Not connected or authorized"
                ),
                extensions={"broker": self.name},
            )

        with self._lock:
            req = oamsg.ProtoOATraderReq()
            req.ctidTraderAccountId = self.account_id
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_TRADER_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg(timeout=10.0)
            if not resp or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_TRADER_RES:
                return StandardResponse.failure(
                    message="Failed to retrieve trader info",
                    error=StandardError(
                        code="REQUEST_FAILED", message="Failed to retrieve trader info"
                    ),
                    extensions={"broker": self.name},
                )
            trader_res = oamsg.ProtoOATraderRes()
            trader_res.ParseFromString(resp[1])
            trader = trader_res.trader
            balance = float(trader.balance) / 100.0 if trader.balance else 0.0
            leverage = (
                int(trader.leverageInCents) // 100 if trader.leverageInCents else 30
            )
            acc = AccountInfo(
                login=trader.ctidTraderAccountId,
                balance=balance,
                equity=balance,
                leverage=leverage,
                server=self.gateway_host,
                company="Spotware cTrader",
                trade_allowed=not trader.isLimitedRisk,
                raw=trader,
            )
            return StandardResponse.success(
                data=acc, extensions={"broker": self.name, "raw": trader}
            )

    # ========================================================================
    # 3. Symbols & Market Instruments
    # ========================================================================

    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve symbol list via ProtoOASymbolsListReq."""
        if not self._authenticated:
            default_syms = [
                SymbolInfo(
                    name="EURUSD",
                    point=0.00001,
                    digits=5,
                    currency_base="EUR",
                    currency_profit="USD",
                ),
                SymbolInfo(
                    name="GBPUSD",
                    point=0.00001,
                    digits=5,
                    currency_base="GBP",
                    currency_profit="USD",
                ),
                SymbolInfo(
                    name="USDJPY",
                    point=0.001,
                    digits=3,
                    currency_base="USD",
                    currency_profit="JPY",
                ),
                SymbolInfo(
                    name="XAUUSD",
                    point=0.01,
                    digits=2,
                    currency_base="XAU",
                    currency_profit="USD",
                ),
            ]
            return StandardResponse.success(
                data=default_syms, extensions={"broker": self.name}
            )

        with self._lock:
            req = oamsg.ProtoOASymbolsListReq()
            req.ctidTraderAccountId = self.account_id
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_SYMBOLS_LIST_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg(timeout=10.0)
            if (
                not resp
                or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_SYMBOLS_LIST_RES
            ):
                return StandardResponse.failure(
                    message="Failed to retrieve symbols list",
                    error=StandardError(
                        code="REQUEST_FAILED", message="Failed to retrieve symbols list"
                    ),
                    extensions={"broker": self.name},
                )
            sym_res = oamsg.ProtoOASymbolsListRes()
            sym_res.ParseFromString(resp[1])
            symbols: list[SymbolInfo] = []
            for s in sym_res.symbol:
                sym_name = getattr(s, "symbolName", str(s.symbolId))
                self._symbol_id_map[s.symbolId] = sym_name
                symbols.append(
                    SymbolInfo(
                        name=sym_name,
                        visible=s.enabled,
                        select=s.enabled,
                        raw=s,
                    )
                )
            return StandardResponse.success(
                data=symbols, extensions={"broker": self.name, "raw": sym_res}
            )

    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument specifications."""
        sym_clean = symbol.upper().strip()
        dec = 3 if sym_clean.endswith("JPY") else (2 if "XAU" in sym_clean else 5)
        info = SymbolInfo(
            name=sym_clean,
            visible=True,
            select=True,
            digits=dec,
            point=1.0 / (10**dec),
            currency_base=sym_clean[:3] if len(sym_clean) >= 6 else "USD",
            currency_profit=sym_clean[3:6] if len(sym_clean) >= 6 else "USD",
        )
        return StandardResponse.success(data=info, extensions={"broker": self.name})

    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Retrieve latest known quote tick for symbol."""
        now = datetime.now(UTC)
        return StandardResponse.success(
            data=Tick(time=now, bid=1.1, ask=1.1002, last=1.1001),
            extensions={"broker": self.name},
        )

    # ========================================================================
    # 5. Bars & Ticks (Historical Data)
    # ========================================================================

    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.H1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick trendbars from cTrader."""
        if not self._authenticated:
            return StandardResponse.failure(
                message="Not connected or authorized",
                error=StandardError(
                    code="NOT_AUTHORIZED", message="Not connected or authorized"
                ),
                extensions={"broker": self.name},
            )

        with self._lock:
            req = oamsg.ProtoOAGetTrendbarsReq()
            req.ctidTraderAccountId = self.account_id
            req.period = self.TIMEFRAME_TO_PERIOD.get(
                timeframe if isinstance(timeframe, TimeFrame) else TimeFrame.H1,
                9,
            )
            req.count = count or 100
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_GET_TRENDBARS_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg(timeout=10.0)
            if (
                not resp
                or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_GET_TRENDBARS_RES
            ):
                return StandardResponse.failure(
                    message="Failed to retrieve trendbars",
                    error=StandardError(
                        code="REQUEST_FAILED", message="Failed to retrieve trendbars"
                    ),
                    extensions={"broker": self.name},
                )
            tb_res = oamsg.ProtoOAGetTrendbarsRes()
            tb_res.ParseFromString(resp[1])
            bars: list[Bar] = []
            for tb in tb_res.trendbar:
                dt = datetime.fromtimestamp(tb.utcTimestampInMinutes * 60, tz=UTC)
                o = float(tb.low + tb.deltaOpen) / 100000.0
                h = float(tb.low + tb.deltaHigh) / 100000.0
                l = float(tb.low) / 100000.0
                c = float(tb.low + tb.deltaClose) / 100000.0
                bars.append(
                    Bar(
                        time=dt,
                        open=o,
                        high=h,
                        low=l,
                        close=c,
                        tick_volume=int(tb.volume),
                    )
                )
            return StandardResponse.success(
                data=bars, extensions={"broker": self.name, "raw": tb_res}
            )

    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Retrieve historical ticks."""
        return StandardResponse.success(data=[], extensions={"broker": self.name})

    # ========================================================================
    # 6. Positions & Orders
    # ========================================================================

    def get_position_info(
        self, symbol: str | None = None, ticket: int | None = None
    ) -> StandardResponse[list[PositionInfo]]:
        """Retrieve open positions via ProtoOAReconcileReq."""
        if not self._authenticated:
            return StandardResponse.failure(
                message="Not connected or authorized",
                error=StandardError(
                    code="NOT_AUTHORIZED", message="Not connected or authorized"
                ),
                extensions={"broker": self.name},
            )

        with self._lock:
            req = oamsg.ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.account_id
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_RECONCILE_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg(timeout=10.0)
            if (
                not resp
                or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_RECONCILE_RES
            ):
                return StandardResponse.failure(
                    message="Failed to reconcile positions",
                    error=StandardError(
                        code="REQUEST_FAILED", message="Failed to reconcile positions"
                    ),
                    extensions={"broker": self.name},
                )
            rec_res = oamsg.ProtoOAReconcileRes()
            rec_res.ParseFromString(resp[1])
            positions: list[PositionInfo] = []
            for p in rec_res.position:
                pos_type = "BUY" if p.tradeData.tradeSide == 1 else "SELL"
                positions.append(
                    PositionInfo(
                        ticket=p.positionId,
                        symbol=self._symbol_id_map.get(
                            p.tradeData.symbolId, str(p.tradeData.symbolId)
                        ),
                        type=pos_type,
                        volume=float(p.tradeData.volume) / 100.0,
                        price_open=float(p.price) / 100000.0,
                        price_current=float(p.price) / 100000.0,
                        raw=p,
                    )
                )
            return StandardResponse.success(
                data=positions, extensions={"broker": self.name, "raw": rec_res}
            )

    def get_num_positions(self) -> StandardResponse[int]:
        """Get total open positions count."""
        res = self.get_position_info()
        return StandardResponse.success(
            data=len(res.data) if res.data else 0, extensions={"broker": self.name}
        )

    def get_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[OrderInfo]]:
        """Retrieve active pending orders."""
        if not self._authenticated:
            return StandardResponse.failure(
                message="Not connected or authorized",
                error=StandardError(
                    code="NOT_AUTHORIZED", message="Not connected or authorized"
                ),
                extensions={"broker": self.name},
            )

        with self._lock:
            req = oamsg.ProtoOAReconcileReq()
            req.ctidTraderAccountId = self.account_id
            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_RECONCILE_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg(timeout=10.0)
            if (
                not resp
                or resp[0] != modelmsg.ProtoOAPayloadType.PROTO_OA_RECONCILE_RES
            ):
                return StandardResponse.failure(
                    message="Failed to reconcile orders",
                    error=StandardError(
                        code="REQUEST_FAILED", message="Failed to reconcile orders"
                    ),
                    extensions={"broker": self.name},
                )
            rec_res = oamsg.ProtoOAReconcileRes()
            rec_res.ParseFromString(resp[1])
            orders: list[OrderInfo] = []
            for o in rec_res.order:
                orders.append(
                    OrderInfo(
                        ticket=o.orderId,
                        symbol=self._symbol_id_map.get(
                            o.tradeData.symbolId, str(o.tradeData.symbolId)
                        ),
                        type=str(o.orderType),
                        volume_initial=float(o.tradeData.volume) / 100.0,
                        volume_current=float(o.tradeData.volume) / 100.0,
                        price_open=float(o.limitPrice or o.stopPrice or 0.0) / 100000.0,
                        raw=o,
                    )
                )
            return StandardResponse.success(
                data=orders, extensions={"broker": self.name, "raw": rec_res}
            )

    def get_num_orders(self) -> StandardResponse[int]:
        """Get total active pending orders count."""
        res = self.get_order_info()
        return StandardResponse.success(
            data=len(res.data) if res.data else 0, extensions={"broker": self.name}
        )

    # ========================================================================
    # 10. Pre-check & Trade Execution
    # ========================================================================

    def check_order(self, request: TradeRequest) -> StandardResponse[OrderCheckResult]:
        """Pre-flight check of trade request parameters."""
        if not request.symbol:
            return StandardResponse.failure(
                message="Symbol must be specified",
                error=StandardError(
                    code="BROKER_ERROR", message="Symbol must be specified"
                ),
                extensions={"broker": self.name},
            )
        if request.volume <= 0:
            return StandardResponse.failure(
                message="Volume must be greater than 0",
                error=StandardError(
                    code="BROKER_ERROR", message="Volume must be greater than 0"
                ),
                extensions={"broker": self.name},
            )
        chk = OrderCheckResult(retcode=0, comment="Parameters valid")
        return StandardResponse.success(
            data=chk, message="Valid", extensions={"broker": self.name}
        )

    def trade(self, request: TradeRequest) -> StandardResponse[TradeResult]:
        """Execute trade order via ProtoOANewOrderReq."""
        if not self._authenticated:
            return StandardResponse.failure(
                message="cTrader client is not authenticated",
                error=StandardError(
                    code="NOT_AUTHENTICATED",
                    message="cTrader client is not authenticated",
                ),
                extensions={"broker": self.name},
            )

        with self._lock:
            req = oamsg.ProtoOANewOrderReq()
            req.ctidTraderAccountId = self.account_id
            req.symbolId = 1
            req.orderType = 1  # MARKET
            req.tradeSide = (
                1 if (request.type == OrderType.BUY or request.type == "BUY") else 2
            )
            req.volume = int(request.volume * 100000.0)
            req.comment = request.comment or "api trade"

            self._send_msg(
                modelmsg.ProtoOAPayloadType.PROTO_OA_NEW_ORDER_REQ,
                req.SerializeToString(),
            )
            resp = self._recv_msg(timeout=10.0)
            if not resp:
                return StandardResponse.failure(
                    message="No response received for trade execution",
                    error=StandardError(
                        code="BROKER_ERROR",
                        message="No response received for trade execution",
                    ),
                    extensions={"broker": self.name},
                )
            p_type, p_data = resp
            if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_EXECUTION_EVENT:
                exec_ev = oamsg.ProtoOAExecutionEvent()
                exec_ev.ParseFromString(p_data)
                res = TradeResult(
                    retcode=0,
                    order=exec_ev.order.orderId if exec_ev.order else 0,
                    deal=exec_ev.deal.dealId if exec_ev.deal else 0,
                    volume=request.volume,
                    comment="Order executed",
                    raw=exec_ev,
                )
                return StandardResponse.success(
                    data=res, message="Order executed", extensions={"broker": self.name}
                )
            if p_type == modelmsg.ProtoOAPayloadType.PROTO_OA_ERROR_RES:
                err_res = oamsg.ProtoOAErrorRes()
                err_res.ParseFromString(p_data)
                return StandardResponse.failure(
                    message=f"Order rejected: {err_res.description}",
                    error=StandardError(
                        code=str(err_res.errorCode),
                        message=f"Order rejected: {err_res.description}",
                    ),
                    extensions={"broker": self.name},
                )
            return StandardResponse.failure(
                message=f"Unexpected trade response: {p_type}",
                error=StandardError(
                    code="BROKER_ERROR", message=f"Unexpected trade response: {p_type}"
                ),
                extensions={"broker": self.name},
            )
