"""MT5 adapter tests using an injected fake transport."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pytest
from app.services.brokers.canonical_contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerMarginRequest,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
)
from app.services.brokers.metatrader.adapter import MT5BrokerAdapter
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Mark every operation available for adapter-body unit testing.

    The real registry catalogue keeps every non-connection capability
    ``UNAVAILABLE`` until credential-gated release evidence is recorded
    (see ``capabilities/matrix.py``). Unit tests exercise the adapter's own
    method bodies directly, so they assert availability locally instead of
    depending on that release gate.
    """
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


class _FakeTransport:
    def __init__(self, *, verified: bool = True) -> None:
        self._verified = verified
        self.closed = False

    async def connect(self) -> bool:
        return self._verified

    def _responses(self) -> dict[str, object]:
        now = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
        return {
            "account_info": {
                "login": 12345,
                "server": "Demo-Server",
                "currency": "USD",
                "balance": 1000,
                "equity": 1100,
                "margin": 100,
                "margin_free": 1000,
                "trade_allowed": True,
            },
            "terminal_info": (
                {
                    "name": "MetaTrader 5",
                    "company": "MetaQuotes Ltd.",
                    "build": 4570,
                    "language": "English",
                    "connected": True,
                    "trade_allowed": True,
                    "dlls_allowed": True,
                    "ping_last": 1500,
                    "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                    "data_path": "C:\\Users\\Mock\\AppData\\Roaming\\MetaQuotes\\Terminal\\Instance",
                    "common_data_path": "C:\\ProgramData\\MetaQuotes\\Terminal\\Common",
                }
                if self._verified
                else None
            ),
            "version": "5.0.0",
            # Deliberately not in alphabetical order: the adapter is what
            # imposes the deterministic ordering a cursor depends on.
            "symbols_get": (
                {
                    "name": "GBPUSD",
                    "digits": 5,
                    "volume_step": 0.01,
                    "volume_min": 0.01,
                    "volume_max": 100,
                },
                {
                    "name": "EURUSD",
                    "digits": 5,
                    "volume_step": 0.01,
                    "volume_min": 0.01,
                    "volume_max": 100,
                },
                {
                    "name": "XAUUSD",
                    "digits": 2,
                    "volume_step": 0.01,
                    "volume_min": 0.01,
                    "volume_max": 100,
                },
            ),
            "symbols_total": 3,
            "symbol_select": True,
            "symbol_info": {
                "name": "EURUSD",
                "digits": 5,
                "point": 0.00001,
                "filling_mode": 1,
                "order_mode": 127,
                "expiration_mode": 7,
                "order_gtc_mode": 0,
                "trade_exemode": 2,
                "trade_mode": 4,
                "trade_calc_mode": 0,
                "swap_mode": 1,
                "swap_rollover3days": 3,
                "trade_stops_level": 0,
                "trade_freeze_level": 0,
                "volume_min": 0.01,
                "volume_max": 500.0,
                "volume_step": 0.01,
                "volume_limit": 0.0,
                "trade_tick_size": 0.00001,
                "trade_tick_value": 1.0,
                "trade_tick_value_profit": 1.0,
                "trade_tick_value_loss": 1.0,
                "trade_contract_size": 100000.0,
                "currency_base": "EUR",
                "currency_profit": "USD",
                "currency_margin": "USD",
                "margin_initial": 0.0,
                "margin_maintenance": 0.0,
                "margin_hedged": 100000.0,
                "margin_hedged_use_leg": False,
                "swap_long": -0.2,
                "swap_short": -1.2,
            },
            "symbol_info_tick": {
                "time": now,
                "bid": 1.1,
                "ask": 1.1002,
                "last": 1.1001,
            },
            "copy_ticks_from": ({"time": now, "bid": 1.1, "ask": 1.1002},),
            "copy_rates_from_pos": (
                {
                    "time": now,
                    "open": 1.1,
                    "high": 1.2,
                    "low": 1.0,
                    "close": 1.15,
                    "tick_volume": 25,
                    "real_volume": 0,
                },
            ),
            "copy_rates_range": (
                {
                    "time": now,
                    "open": 1.1,
                    "high": 1.2,
                    "low": 1.0,
                    "close": 1.15,
                    "tick_volume": 25,
                    "real_volume": 0,
                },
            ),
            "positions_get": (
                {
                    "ticket": 1,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": 1,
                    "price_open": 1.1,
                    "price_current": 1.2,
                    "profit": 100,
                    "time_update": now,
                },
            ),
            "orders_get": (
                {
                    "ticket": 11,
                    "symbol": "EURUSD",
                    "type": 2,
                    "state": 1,
                    "volume_initial": 1,
                    "volume_current": 0.5,
                    "price_open": 1.1,
                    "time_setup": now,
                },
            ),
            "history_orders_get": (
                {
                    "ticket": 12,
                    "symbol": "EURUSD",
                    "type": 0,
                    "state": 4,
                    "volume_initial": 1,
                    "volume_current": 0,
                    "price_open": 1.1,
                    "time_setup": now,
                    "time_done": now,
                },
            ),
            "history_deals_get": (
                {
                    "ticket": 21,
                    "order": 12,
                    "position_id": 1,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": 1,
                    "price": 1.2,
                    "entry": 0,
                    "time": now,
                    "commission": -1,
                },
                {
                    "ticket": 22,
                    "symbol": "",
                    "type": 2,
                    "profit": 100,
                    "time": now,
                },
            ),
            "last_error": (1, "Success"),
            "order_check": {
                "retcode": 0,
                "comment": "Done",
                "balance": 1000,
                "equity": 1010,
                "profit": 10,
                "margin": 10,
                "margin_free": 1000,
                "margin_level": 10100,
            },
            "order_send": {
                "retcode": 10009,
                "comment": "Done",
                "order": 77,
                "deal": 88,
                "volume": 1,
                "price": 1.2,
            },
            "order_calc_margin": 10,
            "order_calc_profit": 25,
        }

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        del args, kwargs
        return self._responses().get(name)

    async def constant(self, name: str) -> object:
        del name
        return 1

    async def close(self) -> None:
        self.closed = True


class _EmptyCalculationTransport(_FakeTransport):
    """Return no provider value for MT5 calculation calls."""

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        """Return no calculation evidence and delegate every other call."""
        if name in {"order_calc_margin", "order_calc_profit"}:
            return None
        return await super().call(name, *args, **kwargs)


def test_adapter_rejects_mismatched_account_reference() -> None:
    """The declared account reference must match the resolved login."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="99999",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    with pytest.raises(ValueError, match="account_reference must match login"):
        MT5BrokerAdapter(bad)


def test_adapter_connect_verifies_account_and_server() -> None:
    """A successful transport verification transitions to a ready session."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status == "success"
        status = await adapter.is_connected()
        assert status.data is True

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_on_account_mismatch() -> None:
    """A transport that cannot verify identity fails the connection closed."""

    class _MismatchedTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            del args, kwargs
            if name == "account_info":
                return {"login": 1, "server": "Other-Server"}
            if name == "terminal_info":
                return {}
            return None

    adapter = MT5BrokerAdapter(_config(), transport=_MismatchedTransport())

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONNECTION_FAILED.value

    asyncio.run(exercise())


def test_adapter_get_symbol_info_not_found_is_structured() -> None:
    """A missing symbol returns the exact canonical not-found error."""

    class _EmptyTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_info":
                return None
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), transport=_EmptyTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbol_info("UNKNOWN")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND.value

    asyncio.run(exercise())


def test_adapter_disconnect_releases_transport() -> None:
    """Disconnecting the adapter releases the owned transport handle."""
    transport = _FakeTransport(verified=True)
    adapter = MT5BrokerAdapter(_config(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        await adapter.disconnect()

    asyncio.run(exercise())
    assert transport.closed


def test_adapter_get_symbols_and_ping() -> None:
    """Symbols map genuine values and ping succeeds on a verified terminal."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        symbols = await adapter.get_symbols(limit=5)
        assert symbols.data is not None
        assert symbols.data.items[0].provider_symbol == "EURUSD"
        ping = await adapter.ping()
        assert ping.status == "success"

    asyncio.run(exercise())


def test_adapter_get_symbols_walks_the_complete_universe() -> None:
    """A cursor walk returns every symbol exactly once in a stable order."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        first = await adapter.get_symbols(limit=2)
        assert first.data is not None
        assert [item.provider_symbol for item in first.data.items] == [
            "EURUSD",
            "GBPUSD",
        ]
        assert first.data.truncated is True
        assert first.data.next_cursor == "2"
        assert first.data.provider_metadata["symbols_total"] == 3

        second = await adapter.get_symbols(limit=2, cursor=first.data.next_cursor)
        assert second.data is not None
        assert [item.provider_symbol for item in second.data.items] == ["XAUUSD"]
        assert second.data.truncated is False
        assert second.data.next_cursor is None

    asyncio.run(exercise())


def test_adapter_get_symbols_rejects_a_foreign_cursor() -> None:
    """A cursor this adapter never issued fails instead of silently restarting."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbols(limit=2, cursor="not-an-offset")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


@pytest.mark.parametrize("symbols_total", [None, True, -1, 2])
def test_adapter_get_symbols_rejects_invalid_universe_count(
    symbols_total: object,
) -> None:
    """Unfiltered discovery requires a valid count matching symbols_get."""

    class _InvalidCountTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbols_total":
                return symbols_total
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), transport=_InvalidCountTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbols(limit=2)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_RESPONSE_INVALID.value

    asyncio.run(exercise())


def test_adapter_get_symbols_rejects_missing_symbol_records() -> None:
    """A missing symbols_get payload cannot masquerade as an empty universe."""

    class _MissingSymbolsTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbols_get":
                return None
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), transport=_MissingSymbolsTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbols(limit=2)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_RESPONSE_INVALID.value

    asyncio.run(exercise())


def test_adapter_select_symbol_reports_not_found() -> None:
    """A rejected symbol selection returns the exact not-found error."""

    class _RejectingTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_select":
                return False
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), transport=_RejectingTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.select_symbol("UNKNOWN")
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND.value

    asyncio.run(exercise())


def test_adapter_get_quote_and_ticks() -> None:
    """Quotes and ticks map genuine terminal values."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        quote = await adapter.get_quote("EURUSD")
        assert quote.data is not None
        assert str(quote.data.bid) == "1.1"
        ticks = await adapter.get_ticks(
            "EURUSD",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            limit=10,
        )
        assert ticks.data is not None
        assert len(ticks.data.items) == 1

    asyncio.run(exercise())


def test_adapter_bounds_numpy_tick_pages_without_ambiguous_truth_checks() -> None:
    """NumPy tick arrays use their length for truncation evidence."""

    class _NumpyTickTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "copy_ticks_from":
                timestamp = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
                return np.array(
                    [
                        (timestamp, 1.1, 1.1002, 0.0),
                        (timestamp + 1, 1.1001, 1.1003, 0.0),
                    ],
                    dtype=[
                        ("time", "<i8"),
                        ("bid", "<f8"),
                        ("ask", "<f8"),
                        ("last", "<f8"),
                    ],
                )
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(
        _config(),
        transport=_NumpyTickTransport(),
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_ticks(
            "EURUSD",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            limit=1,
        )
        assert result.data is not None
        assert len(result.data.items) == 1
        assert result.data.truncated

    asyncio.run(exercise())


def test_adapter_get_latest_ticks_bars_and_spread() -> None:
    """Omitted ranges retrieve bounded recent MT5 evidence."""

    class _RecordingTransport(_FakeTransport):
        """Record the native bounded-bar request."""

        def __init__(self) -> None:
            super().__init__(verified=True)
            self.bar_call: tuple[object, ...] | None = None
            self.history_calls: list[tuple[str, tuple[object, ...]]] = []

        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            """Capture bar arguments and delegate the fake response."""
            if name in {"symbol_select", "copy_rates_from_pos"}:
                self.history_calls.append((name, args))
            if name == "copy_rates_from_pos":
                self.bar_call = args
            return await super().call(name, *args, **kwargs)

    transport = _RecordingTransport()
    adapter = MT5BrokerAdapter(_config(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        ticks = await adapter.get_ticks("EURUSD", limit=10)
        assert ticks.data is not None
        assert len(ticks.data.items) == 1
        bars = await adapter.get_historical_bars(
            "EURUSD",
            "M1",
            limit=10,
        )
        assert bars.data is not None
        assert len(bars.data.items) == 1
        assert (
            bars.data.items[0].closing_timestamp > bars.data.items[0].opening_timestamp
        )
        assert transport.bar_call == ("EURUSD", 1, 0, 10)
        assert transport.history_calls == [
            ("symbol_select", ("EURUSD", True)),
            ("copy_rates_from_pos", ("EURUSD", 1, 0, 10)),
        ]
        spread = await adapter.get_spread("EURUSD")
        assert spread.data is not None
        assert str(spread.data) == "0.0002"

    asyncio.run(exercise())


def test_adapter_historical_bars_fail_closed_when_selection_is_rejected() -> None:
    """Rejected Market Watch selection never proceeds to a history read."""

    class _RejectingHistoryTransport(_FakeTransport):
        """Reject symbol selection and record whether rates were requested."""

        def __init__(self) -> None:
            super().__init__(verified=True)
            self.rates_requested = False

        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            """Return the provider rejection and track forbidden continuation."""
            if name == "symbol_select":
                return False
            if name == "copy_rates_from_pos":
                self.rates_requested = True
            return await super().call(name, *args, **kwargs)

    transport = _RejectingHistoryTransport()
    adapter = MT5BrokerAdapter(_config(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_historical_bars("UNKNOWN", "D1", limit=40)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND.value
        assert not transport.rates_requested

    asyncio.run(exercise())


def test_adapter_get_positions_maps_open_state() -> None:
    """Positions map genuine terminal position state."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        positions = await adapter.get_positions(limit=10)
        assert positions.data is not None
        assert positions.data.items[0].side == "LONG"

    asyncio.run(exercise())


def test_adapter_get_platform_info_reports_terminal_version() -> None:
    """Platform info exposes the redacted terminal version and environment."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_platform_info()
        assert result.data is not None
        assert result.data.api_or_terminal_version == "5.0.0"
        assert result.data.observed_at.tzinfo is UTC
        assert result.data.endpoint_metadata["name"] == "MetaTrader 5"

    asyncio.run(exercise())


def test_adapter_account_history_mutation_and_calculation_operations() -> None:
    """Implemented MT5 operation groups preserve provider evidence."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=True))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)

    async def exercise() -> None:
        await adapter.connect()
        permissions = await adapter.get_permissions()
        assert permissions.data is not None
        assert permissions.data.trade_write is True
        balances = await adapter.get_balances()
        assert balances.data is not None
        assert balances.data[0].asset == "USD"
        assert (await adapter.get_last_error()).data is None
        assert (await adapter.get_position("1")).data is not None
        assert (await adapter.get_orders(limit=10)).data is not None
        filtered_orders = await adapter.get_orders(
            BrokerOrderFilter(symbol="EURUSD", side="BUY", status="ACCEPTED"),
            limit=10,
        )
        assert filtered_orders.data is not None
        assert (await adapter.get_position("not-a-ticket")).error is not None
        assert (await adapter.get_order("11")).data is not None
        assert (await adapter.list_order_history(start, end, limit=10)).data is not None
        deals = await adapter.list_deal_history(start, end, limit=10)
        assert deals.data is not None
        assert len(deals.data.items) == 1
        assert (await adapter.get_deal("21")).data is not None
        transactions = await adapter.list_account_transactions(start, end, limit=10)
        assert transactions.data is not None
        assert len(transactions.data.items) == 1

        order = BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal(1),
            quantity_unit="lots",
            environment=BrokerEnvironment.DEMO,
        )
        assert (await adapter.check_order(order)).status == "success"
        assert (await adapter.place_order(order)).status == "success"
        modify_order = await adapter.modify_order(
            BrokerOrderModificationRequest(order_id="11", limit_price=Decimal("1.2"))
        )
        assert modify_order.error is not None
        assert (
            modify_order.error.code
            == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED.value
        )
        assert (await adapter.cancel_order("11")).status == "success"
        modify_position = await adapter.modify_position(
            BrokerPositionModificationRequest(position_id="1", stop_loss=Decimal("1.0"))
        )
        assert modify_position.error is not None
        assert (
            modify_position.error.code
            == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED.value
        )
        assert (
            await adapter.close_position(
                BrokerPositionCloseRequest(
                    position_id="1",
                    quantity=Decimal(1),
                    quantity_unit="lots",
                )
            )
        ).status == "success"
        margin = await adapter.calculate_margin(
            BrokerMarginRequest(
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lots",
                product_profile="mt5",
            )
        )
        assert margin.data == Decimal(10)
        profit = await adapter.calculate_profit(
            BrokerProfitRequest(
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lots",
                open_price=Decimal("1.1"),
                close_price=Decimal("1.2"),
                product_profile="mt5",
            )
        )
        assert profit.data == Decimal(25)

    asyncio.run(exercise())


def test_adapter_calculations_fail_when_provider_returns_no_value() -> None:
    """Absent provider calculation evidence maps to an explicit error."""
    adapter = MT5BrokerAdapter(_config(), transport=_EmptyCalculationTransport())

    async def exercise() -> None:
        await adapter.connect()
        margin = await adapter.calculate_margin(
            BrokerMarginRequest(
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lots",
                product_profile="mt5",
            )
        )
        assert margin.error is not None
        profit = await adapter.calculate_profit(
            BrokerProfitRequest(
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lots",
                open_price=Decimal("1.1"),
                close_price=Decimal("1.2"),
                product_profile="mt5",
            )
        )
        assert profit.error is not None

    asyncio.run(exercise())


def test_adapter_rejects_non_live_or_demo_env() -> None:
    """MT5BrokerAdapter raises ValueError for invalid environment types."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    with pytest.raises(ValueError, match="MT5 requires LIVE or DEMO"):
        MT5BrokerAdapter(bad)


def test_adapter_rejects_endpoint_override() -> None:
    """MT5BrokerAdapter raises ValueError when an endpoint override is specified."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        endpoint="http://localhost:5000",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials={
            "login": SecretStr("12345"),
            "password": SecretStr("hunter2"),
            "server": SecretStr("Demo-Server"),
        },
    )
    with pytest.raises(ValueError, match="MT5 does not accept endpoint override"):
        MT5BrokerAdapter(bad)


def test_adapter_rejects_missing_credentials() -> None:
    """MT5BrokerAdapter raises ValueError when required credentials are missing."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="12345",
        credentials=None,
    )
    msg = "MT5 resolved login, password, and server are required"
    with pytest.raises(ValueError, match=msg):
        MT5BrokerAdapter(bad)


def test_adapter_connect_handles_transport_exception() -> None:
    """A transport connection exception transitions to failed and fails closed."""

    class _FailingTransport(_FakeTransport):
        async def connect(self) -> bool:
            raise ConnectionError("failed to connect")

    adapter = MT5BrokerAdapter(_config(), transport=_FailingTransport())

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONNECTION_FAILED.value

    asyncio.run(exercise())


def test_adapter_connect_fails_if_initialized_is_false() -> None:
    """A transport reporting initialized is False transitions to failed connection."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport(verified=False))

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.status != "success"

    asyncio.run(exercise())


def test_adapter_ping_unsupported_if_terminal_none() -> None:
    """PING returns unsupported when terminal_info response is missing."""

    class _NoTerminalTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "terminal_info":
                return None
            return await super().call(name, *args, **kwargs)

    transport = _NoTerminalTransport()
    adapter = MT5BrokerAdapter(_config(), transport=transport)
    from app.services.brokers.canonical_contracts import BrokerConnectionState

    async def exercise() -> None:
        await adapter.connect()
        adapter._state = BrokerConnectionState.READY
        result = await adapter.ping()
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED.value

    asyncio.run(exercise())


def test_adapter_get_symbols_invalid_limit() -> None:
    """Retrieving symbols with an invalid limit raises ValueError."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbols(limit=0)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


def test_adapter_get_ticks_invalid_parameters() -> None:
    """Retrieving ticks with missing or invalid parameters raises ValueError."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_ticks("EURUSD", start=None, end=None, limit=0)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


def test_adapter_get_account_info_not_found() -> None:
    """A missing account payload returns the exact canonical account-not-found error."""

    class _NoAccountTransport(_FakeTransport):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.allow_account = True

        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "account_info" and not self.allow_account:
                return None
            return await super().call(name, *args, **kwargs)

    transport = _NoAccountTransport()
    adapter = MT5BrokerAdapter(_config(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        transport.allow_account = False
        result = await adapter.get_account_info()
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND.value

    asyncio.run(exercise())


def test_adapter_get_positions_invalid_limit() -> None:
    """Retrieving positions with an invalid limit raises ValueError."""
    adapter = MT5BrokerAdapter(_config(), transport=_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_positions(limit=0)
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID.value

    asyncio.run(exercise())


def test_adapter_get_symbol_info_success() -> None:
    """Successfully retrieving symbol info returns a valid mapped BrokerSymbolInfo."""

    class _SymbolTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_info":
                return {
                    "name": "EURUSD",
                    "digits": 5,
                    "volume_step": 0.01,
                    "volume_min": 0.01,
                    "volume_max": 100,
                }
            return await super().call(name, *args, **kwargs)

    adapter = MT5BrokerAdapter(_config(), transport=_SymbolTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_symbol_info("EURUSD")
        assert result.status == "success"
        assert result.data is not None
        assert result.data.provider_symbol == "EURUSD"

    asyncio.run(exercise())


def test_adapter_get_quote_not_found() -> None:
    """A missing tick returns symbol not found error."""

    class _NoQuoteTransport(_FakeTransport):
        async def call(self, name: str, *args: object, **kwargs: object) -> object:
            if name == "symbol_info_tick":
                return None
            return await super().call(name, *args, **kwargs)

    transport = _NoQuoteTransport()
    adapter = MT5BrokerAdapter(_config(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_quote("EURUSD")
        assert result.status != "success"
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND.value

    asyncio.run(exercise())
