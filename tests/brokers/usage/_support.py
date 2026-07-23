"""Secret-safe support for standalone Brokers usage programs."""

import asyncio
import struct
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
)
from app.services.brokers.dukascopy_ticks.candle_transport import _CandleBatch
from pydantic import SecretStr


def unavailable_capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Return a complete fail-closed capability map for offline examples."""
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="OFFLINE_USAGE",
            reason="offline usage prevents provider side effects",
        )
        for operation in BrokerCapabilityId
    }


def available_capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Return a complete available capability map for offline examples.

    Programs pair this with an offline transport so the adapter's real request
    construction, provider decoding, and canonical mapping execute without any
    network traffic or provider side effect.
    """
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="OFFLINE_USAGE",
        )
        for operation in BrokerCapabilityId
    }


def config(broker_id: BrokerId) -> BrokerConnectionConfig:
    """Build one bounded, secret-safe provider configuration."""
    environment = {
        BrokerId.MT5: BrokerEnvironment.DEMO,
        BrokerId.CTRADER: BrokerEnvironment.DEMO,
        BrokerId.BINANCE_SPOT: BrokerEnvironment.TESTNET,
        BrokerId.DUKASCOPY: BrokerEnvironment.SANDBOX,
        BrokerId.YAHOO: BrokerEnvironment.SANDBOX,
    }[broker_id]
    credentials: dict[str, SecretStr] | None = None
    account_reference: str | None = None
    probe_symbol: str | None = None
    if broker_id == BrokerId.MT5:
        from tests.brokers.provider_settings import ProviderTestSettings

        settings = ProviderTestSettings()
        if (
            settings.mt5_login is not None
            and settings.mt5_password is not None
            and settings.mt5_server is not None
        ):
            account_reference = settings.mt5_login.get_secret_value()
            credentials = {
                "login": settings.mt5_login,
                "password": settings.mt5_password,
                "server": settings.mt5_server,
            }
            if settings.mt5_terminal_path is not None:
                credentials["terminal_path"] = settings.mt5_terminal_path
        else:
            account_reference = "100001"
            credentials = {
                "login": SecretStr(account_reference),
                "password": SecretStr("offline-placeholder"),
                "server": SecretStr("Offline-Demo"),
            }
    elif broker_id == BrokerId.CTRADER:
        account_reference = "100001"
        credentials = {
            "client_id": SecretStr("offline-client"),
            "client_secret": SecretStr("offline-secret"),
            "access_token": SecretStr("offline-token"),
            "account_id": SecretStr(account_reference),
        }
    elif broker_id == BrokerId.BINANCE_SPOT:
        credentials = {
            "api_key": SecretStr("offline-key"),
            "api_secret": SecretStr("offline-secret"),
        }
    elif broker_id == BrokerId.YAHOO:
        probe_symbol = "EURUSD=X"
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=environment,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference=account_reference,
        credentials=credentials,
        probe_symbol=probe_symbol,
    )


def show(label: str, result: BrokerResult[object]) -> None:
    """Print bounded result metadata without provider payloads or secrets."""
    detail = ""
    if result.error is not None:
        detail = f" {result.error.code.value}"
    print(label, result.status, result.operation.value + detail)


def show_value(label: str, result: BrokerResult[object], value: object) -> None:
    """Print one bounded mapped provider value alongside its result status."""
    print(label, result.status, result.operation.value, "->", value)


class OfflineMT5Transport:
    """Serve recorded MT5 terminal payloads without a terminal or network."""

    _NOW = datetime(2026, 1, 1, tzinfo=UTC).timestamp()

    def __init__(self) -> None:
        """Record every provider call name for bounded display."""
        self.calls: list[str] = []

    async def connect(self) -> bool:
        """Report a verified offline terminal session.

        Returns:
            Always ``True`` for the recorded offline session.
        """
        self.calls.append("initialize")
        return True

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        """Return one recorded MT5 payload for the requested SDK call.

        Args:
            name: Exact documented MT5 SDK function name.
            args: Ignored positional provider arguments.
            kwargs: Ignored keyword provider arguments.

        Returns:
            The recorded provider payload, or ``None`` when unrecorded.
        """
        del args, kwargs
        self.calls.append(name)
        return {
            "terminal_info": {"connected": True, "trade_allowed": True},
            "account_info": {
                "login": 100001,
                "server": "Offline-Demo",
                "currency": "USD",
                "balance": "10500.75",
                "equity": "10620.30",
                "margin": "250.00",
                "margin_free": "10370.30",
                "trade_allowed": True,
            },
            "version": "5.0.0",
            "symbol_info_tick": {
                "time": self._NOW,
                "bid": "1.10500",
                "ask": "1.10520",
                "last": "1.10510",
            },
            "positions_get": (
                {
                    "ticket": 555001,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": "0.50",
                    "price_open": "1.10000",
                    "price_current": "1.10500",
                    "profit": "25.00",
                    "time_update": self._NOW,
                },
            ),
            "orders_get": (
                {
                    "ticket": 555002,
                    "symbol": "EURUSD",
                    "type": 2,
                    "state": 1,
                    "volume_initial": "1.00",
                    "volume_current": "0.40",
                    "price_open": "1.09500",
                    "time_setup": self._NOW,
                },
            ),
            "history_deals_get": (
                {
                    "ticket": 555003,
                    "order": 555002,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": "0.60",
                    "price": "1.09800",
                    "commission": "-0.50",
                    "time": self._NOW,
                },
            ),
            "order_calc_margin": "35.25",
            "order_calc_profit": "12.40",
            # Recorded provider acknowledgements. `10009` is MT5's documented
            # "request completed" retcode; no live order is ever transmitted.
            "order_check": {
                "retcode": 0,
                "margin": "35.25",
                "comment": "Done",
            },
            "order_send": {
                "retcode": 10009,
                "order": 555002,
                "deal": 555003,
                "volume": "0.01",
                "price": "1.10510",
                "comment": "Done",
            },
        }.get(name)

    async def constant(self, name: str) -> object:
        """Return one documented MT5 constant from the offline session.

        Args:
            name: Documented MT5 constant name.

        Returns:
            A stable offline constant value.
        """
        self.calls.append(f"constant:{name}")
        return 0

    async def close(self) -> None:
        """Release the recorded offline session deterministically."""
        self.calls.append("shutdown")


class OfflineCTraderTransport:
    """Serve recorded Spotware protobuf-shaped responses without a network."""

    _MUTATIONS = frozenset(
        {
            "ProtoOANewOrderReq",
            "ProtoOAAmendOrderReq",
            "ProtoOACancelOrderReq",
            "ProtoOAAmendPositionSLTPReq",
            "ProtoOAClosePositionReq",
        }
    )

    def __init__(self) -> None:
        """Record every submitted provider request for bounded display."""
        self.requests: list[str] = []
        self.closed = False
        self.handler: object | None = None

    @staticmethod
    def _trade() -> dict[str, object]:
        """Return one recorded provider trade-data block.

        Returns:
            Recorded provider trade metadata.
        """
        return {
            "symbolId": 1,
            "volume": 10_000_000,
            "tradeSide": 1,
            "openTimestamp": 1_700_000_000_000,
        }

    def _responses(self, request: object) -> dict[str, object]:
        """Build the recorded response table for one submitted request.

        Args:
            request: Provider request message being submitted.

        Returns:
            Mapping of provider request type name to recorded payload.
        """
        trade = self._trade()
        order = {
            "orderId": 11,
            "tradeData": trade,
            "orderType": 1,
            "orderStatus": 1,
            "executedVolume": 0,
            "limitPrice": 1.1,
        }
        position = {
            "positionId": 21,
            "tradeData": trade,
            "positionStatus": 1,
            "swap": 0,
            "price": 1.1,
            "moneyDigits": 2,
        }
        tick_price = 110_000 if getattr(request, "type", 1) == 1 else 110_020
        return {
            "ProtoOASymbolsListReq": {
                "symbol": [{"symbolName": "EURUSD", "symbolId": 1, "enabled": True}]
            },
            "ProtoOASymbolByIdReq": {
                "symbol": [
                    {
                        "symbolId": 1,
                        "digits": 5,
                        "pipPosition": 4,
                        "minVolume": 100_000,
                        "maxVolume": 100_000_000,
                        "stepVolume": 100_000,
                        "lotSize": 100_000,
                        "enableShortSelling": True,
                    }
                ]
            },
            "ProtoOAReconcileReq": {"position": [position], "order": [order]},
            "ProtoOAOrderListReq": {"order": [order], "hasMore": False},
            "ProtoOADealListReq": {
                "deal": [
                    {
                        "dealId": 31,
                        "orderId": 11,
                        "positionId": 21,
                        "volume": 10_000_000,
                        "filledVolume": 10_000_000,
                        "symbolId": 1,
                        "createTimestamp": 1_700_000_000_000,
                        "executionTimestamp": 1_700_000_000_100,
                        "executionPrice": 1.1,
                        "tradeSide": 1,
                        "dealStatus": 2,
                        "moneyDigits": 2,
                    }
                ],
                "hasMore": False,
            },
            "ProtoOAExpectedMarginReq": {
                "margin": [
                    {"volume": 10_000_000, "buyMargin": 12345, "sellMargin": 12345}
                ],
                "moneyDigits": 2,
            },
            "ProtoOAGetTickDataReq": {
                "tickData": [
                    {"timestamp": 1_700_000_000_000, "tick": tick_price},
                    {"timestamp": 1_000, "tick": 1},
                ],
                "hasMore": False,
            },
            "ProtoOAGetTrendbarsReq": {
                "trendbar": [
                    {
                        "volume": 5,
                        "low": 109_900,
                        "deltaOpen": 100,
                        "deltaHigh": 300,
                        "deltaClose": 200,
                        "utcTimestampInMinutes": 28_333_333,
                    }
                ]
            },
        }

    async def send(self, request: object, response_type: type[object]) -> object:
        """Return the recorded response for one provider request type.

        Args:
            request: Provider request message being submitted.
            response_type: Expected provider response type.

        Returns:
            The recorded provider payload for the request type.
        """
        del response_type
        name = type(request).__name__
        self.requests.append(name)
        if name in self._MUTATIONS:
            return {"order": {"orderId": 11}}
        if name == "ProtoOASubscribeSpotsReq":
            # The adapter registers its handler after this request returns, so
            # the recorded event is delivered on the next loop iteration.
            asyncio.get_running_loop().call_soon(self._emit_spot_event)
            return {}
        return self._responses(request).get(name, {})

    async def connect(self) -> bool:
        """Report a verified offline application/account session.

        Returns:
            Always ``True`` for the recorded offline session.
        """
        return True

    def _emit_spot_event(self) -> None:
        """Push one recorded provider spot event to the registered handler."""
        if self.handler is None:
            return
        event_type = type("ProtoOASpotEvent", (), {})
        event = event_type()
        event.symbolId = 1
        event.bid = 110_000
        event.ask = 110_020
        event.timestamp = 1_700_000_000_000
        self.handler(event)

    def register_event_handler(self, handler: object) -> None:
        """Capture the adapter-owned provider-event callback.

        Args:
            handler: Adapter callback receiving provider events.
        """
        self.handler = handler

    def unregister_event_handler(self, handler: object) -> None:
        """Release the adapter-owned provider-event callback.

        Args:
            handler: Adapter callback previously registered.
        """
        del handler
        self.handler = None

    async def close(self) -> None:
        """Release the recorded offline session deterministically."""
        self.closed = True


class OfflineBinanceTransport:
    """Serve recorded Binance Spot REST and websocket payloads offline."""

    def __init__(self, message_count: int = 2) -> None:
        """Record calls and bound the number of streamed messages.

        Args:
            message_count: Number of recorded websocket messages to emit.
        """
        self._message_count = message_count
        self.calls: list[str] = []
        self.closed = False

    async def connect(self) -> bool:
        """Report a verified offline Spot client.

        Returns:
            Always ``True`` for the recorded offline session.
        """
        return True

    async def call(self, name: str, **kwargs: object) -> object:
        """Return one recorded Spot REST payload.

        Args:
            name: Documented python-binance client method name.
            kwargs: Ignored provider arguments.

        Returns:
            The recorded provider payload for the call.
        """
        del kwargs
        self.calls.append(name)
        if name in {"ping", "get_server_time"}:
            return {"serverTime": 1_700_000_000_000}
        if name == "get_orderbook_ticker":
            return {
                "bidPrice": "60000.10",
                "askPrice": "60000.50",
                "bidQty": "1.250",
                "askQty": "0.875",
            }
        if name == "get_klines":
            return [
                [
                    1_700_000_000_000,
                    "60000.00",
                    "60500.00",
                    "59900.00",
                    "60250.00",
                    "12.5",
                    1_700_000_060_000,
                    "",
                    0,
                    "",
                    "",
                ]
            ]
        return None

    async def stream(self, name: str, **kwargs: object) -> object:
        """Yield a bounded number of recorded websocket messages.

        Args:
            name: Documented socket-manager factory name.
            kwargs: Ignored provider arguments.

        Yields:
            Recorded provider websocket messages.
        """
        del kwargs
        self.calls.append(f"stream:{name}")
        for index in range(self._message_count):
            yield {
                "b": f"60000.{index}",
                "a": "60000.50",
                "B": "1",
                "A": "2",
                "u": 100 + index,
                "E": 1_700_000_000_000,
            }

    async def close(self) -> None:
        """Release the recorded offline client deterministically."""
        self.closed = True


class OfflineYahooTransport:
    """Serve one recorded yfinance public table without a network call."""

    class _Table:
        """Minimal stand-in for the public yfinance table surface."""

        def __init__(self, rows: list[object]) -> None:
            """Hold the recorded rows.

            Args:
                rows: Recorded ``(index, row)`` pairs.
            """
            self._rows = rows

        def iterrows(self) -> object:
            """Iterate the recorded rows.

            Returns:
                An iterator over the recorded rows.
            """
            return iter(self._rows)

    def __init__(self) -> None:
        """Record every requested symbol for bounded display."""
        self.requested: list[str] = []

    async def history(
        self, *, symbol: str, timeframe: str, start: object, end: object
    ) -> object:
        """Return one recorded provider table for the requested symbol.

        Args:
            symbol: Exact provider-native symbol.
            timeframe: Provider interval string.
            start: Optional inclusive start bound.
            end: Optional exclusive end bound.

        Returns:
            A recorded public table object.
        """
        del timeframe, start, end
        self.requested.append(symbol)
        return self._Table(
            [
                (
                    datetime(2026, 1, 1, tzinfo=UTC),
                    {
                        "Open": "150.25",
                        "High": "152.50",
                        "Low": "149.75",
                        "Close": "151.00",
                        "Volume": 1000,
                    },
                )
            ]
        )


class OfflineDukascopyTransport:
    """Serve genuine-shaped decompressed BI5 hour files without a network."""

    def __init__(self, ticks_per_hour: int = 4) -> None:
        """Bound the number of recorded ticks per provider hour file.

        Args:
            ticks_per_hour: Recorded tick records produced per hour file.
        """
        self._ticks_per_hour = ticks_per_hour
        self.requested: list[str] = []

    async def get_hour(self, symbol: str, hour: datetime) -> bytes:
        """Return one recorded decompressed BI5 hour payload.

        Args:
            symbol: Exact provider-native instrument string.
            hour: UTC hour whose provider file is requested.

        Returns:
            Recorded BI5 tick records for the requested hour.
        """
        self.requested.append(f"{symbol}:{hour.isoformat()}")
        records = b""
        for index in range(self._ticks_per_hour):
            # Ascending millisecond offsets with a genuine bid/ask spread.
            records += struct.pack(
                ">3I2f",
                index * 1_000,
                110_020 + index * 10,
                110_000 + index * 10,
                1.5,
                2.5,
            )
        return records


class OfflineDukascopyCandleTransport:
    """Serve genuine-shaped Dukascopy web-chart candle rows offline."""

    def __init__(self) -> None:
        """Record every bounded candle request."""
        self.requested: list[str] = []

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> _CandleBatch:
        """Return deterministic provider-shaped BID candles.

        Args:
            symbol: Exact canonical Dukascopy symbol.
            timeframe: Requested canonical timeframe.
            start: Inclusive UTC range boundary.
            end: Exclusive UTC range boundary.
            limit: Positive output bound.

        Returns:
            Recorded raw candle rows and pagination evidence.
        """
        self.requested.append(f"{symbol}:{timeframe}:{start.isoformat()}")
        intervals = {
            "M1": ("1MIN", timedelta(minutes=1)),
            "M5": ("5MIN", timedelta(minutes=5)),
            "M15": ("15MIN", timedelta(minutes=15)),
            "M30": ("30MIN", timedelta(minutes=30)),
            "H1": ("1HOUR", timedelta(hours=1)),
        }
        provider_interval, duration = intervals[timeframe]
        rows: list[tuple[object, ...]] = []
        current = start
        while current < end and len(rows) < limit:
            index = len(rows)
            rows.append(
                (
                    int(current.timestamp() * 1000),
                    f"1.10{index:02d}",
                    f"1.11{index:02d}",
                    f"1.09{index:02d}",
                    f"1.105{index:01d}",
                    100 + index,
                )
            )
            current += duration
        return _CandleBatch(
            rows=tuple(rows),
            provider_symbol="EUR/USD",
            provider_interval=provider_interval,
            page_count=1,
            truncated=current < end,
        )
