"""Coverage expansion tests for MT5 mutation operations."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import _RequestValidationError
from app.services.brokers.mt5_account.adapter import (
    MT5BrokerAdapter as _MT5MutationsMixin,
)
from app.services.brokers.mt5_mutations.operations import (
    _provider_ticket,
)
from app.utils import generate_id

_REQ_ID = generate_id("req")


def _make_result(
    operation: BrokerCapabilityId, data: object = None, error: object = None
) -> BrokerResult:
    return BrokerResult(
        status="success" if error is None else "error",
        broker=BrokerId.MT5,
        operation=operation,
        request_id=_REQ_ID,
        timestamp=datetime.now(UTC),
        environment=BrokerEnvironment.SANDBOX,
        adapter_version="1.0",
        data=data,
        error=error,
    )


def _make_mt5_send_res(retcode: int = 10009) -> MagicMock:
    res = MagicMock()
    res.retcode = retcode
    res.order = 12345
    res.deal = 67890
    res.volume = 1.0
    res.price = 1.1000
    res.bid = 1.0999
    res.ask = 1.1001
    res.comment = "OK"
    res.request_id = 1
    res.retcode_external = 0
    return res


def _make_mt5_pos(
    ticket: int = 54321, symbol: str = "EURUSD", pos_type: int = 0
) -> MagicMock:
    pos = MagicMock()
    pos.ticket = ticket
    pos.symbol = symbol
    pos.type = pos_type
    pos.volume = 1.0
    pos.price_open = 1.1000
    pos.price_current = 1.1010
    pos.sl = 1.0900
    pos.tp = 1.1100
    pos.profit = 10.0
    pos.time = 1700000000
    pos.time_msc = 1700000000000
    pos.time_update = 1700000000
    pos.time_update_msc = 1700000000000
    pos.identifier = ticket
    pos.magic = 0
    pos.comment = ""
    pos.swap = 0.0
    return pos


class FakeMT5Mutations:
    check_order = _MT5MutationsMixin.check_order
    place_order = _MT5MutationsMixin.place_order
    modify_order = _MT5MutationsMixin.modify_order
    cancel_order = _MT5MutationsMixin.cancel_order
    modify_position = _MT5MutationsMixin.modify_position
    close_position = _MT5MutationsMixin.close_position
    _native_order_request = _MT5MutationsMixin._native_order_request
    _send_mutation = _MT5MutationsMixin._send_mutation
    _native_rejection = _MT5MutationsMixin._native_rejection

    def __init__(self) -> None:
        self._transport = MagicMock()
        self._transport.call = AsyncMock()
        self._transport.constant = AsyncMock(side_effect=lambda name: f"CONST_{name}")
        self._last_error = None

    def _result(
        self, operation: BrokerCapabilityId, data: object = None, error: object = None
    ) -> BrokerResult:
        return _make_result(operation, data=data, error=error)

    def _error(self, operation: BrokerCapabilityId, error: object) -> BrokerResult:
        return _make_result(operation, error=error)

    def _copy_prices(self, native: dict[str, object], request: object) -> None:
        pass


def test_provider_ticket_parsing() -> None:
    """Verify parsing provider ticket integers or raising validation error."""
    assert _provider_ticket("12345") == 12345
    with pytest.raises(_RequestValidationError, match="MT5 ticket must be an integer"):
        _provider_ticket("invalid_ticket")


def test_check_order_coverage() -> None:
    """Verify check_order formats request and handles responses."""

    async def run_test() -> None:
        provider = FakeMT5Mutations()
        mock_response = MagicMock()
        mock_response.retcode = 10009
        mock_response.margin = 150.0
        mock_response.margin_free = 1000.0
        mock_response.comment = "OK"
        provider._transport.call.return_value = mock_response

        req = BrokerOrderRequest(
            environment=BrokerEnvironment.SANDBOX,
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
            account_reference="acc-1",
        )

        res = await provider.check_order(req)
        assert res.error is None
        assert res.data is not None

        # Test None response
        provider._transport.call.return_value = None
        res_none = await provider.check_order(req)
        assert res_none.error is not None

    asyncio.run(run_test())


def test_place_order_coverage() -> None:
    """Verify place_order handles MARKET, LIMIT, STOP, STOP_LIMIT order requests."""

    async def run_test() -> None:
        provider = FakeMT5Mutations()
        provider._transport.call.return_value = _make_mt5_send_res(10009)

        req_market = BrokerOrderRequest(
            environment=BrokerEnvironment.SANDBOX,
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
            account_reference="acc-1",
            stop_loss=Decimal("1.0900"),
            take_profit=Decimal("1.1100"),
            deviation_points=5,
            magic=123,
            comment="mkt",
        )

        res = await provider.place_order(req_market)
        assert res.error is None

        # LIMIT request
        req_limit = BrokerOrderRequest(
            environment=BrokerEnvironment.SANDBOX,
            symbol="EURUSD",
            side="BUY",
            order_type="LIMIT",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
            account_reference="acc-1",
            limit_price=Decimal("1.0950"),
        )
        res_lim = await provider.place_order(req_limit)
        assert res_lim.error is None

        # STOP request
        req_stop = BrokerOrderRequest(
            environment=BrokerEnvironment.SANDBOX,
            symbol="EURUSD",
            side="BUY",
            order_type="STOP",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
            account_reference="acc-1",
            stop_price=Decimal("1.1050"),
        )
        res_st = await provider.place_order(req_stop)
        assert res_st.error is None

        # STOP_LIMIT request
        req_stop_limit = BrokerOrderRequest(
            environment=BrokerEnvironment.SANDBOX,
            symbol="EURUSD",
            side="SELL",
            order_type="STOP_LIMIT",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
            account_reference="acc-1",
            limit_price=Decimal("1.0950"),
            stop_price=Decimal("1.0960"),
            time_in_force="GTD",
            expiration=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
        )

        res_sl = await provider.place_order(req_stop_limit)
        assert res_sl.error is None

    asyncio.run(run_test())


def test_modify_order_and_cancel_order() -> None:
    """Verify modify_order and cancel_order transmit MT5 trade actions."""

    async def run_test() -> None:
        provider = FakeMT5Mutations()
        provider._transport.call.return_value = _make_mt5_send_res(10009)

        mod_req = BrokerOrderModificationRequest(
            order_id="12345",
            quantity=Decimal("2.0"),
            expiration=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
        )

        res_mod = await provider.modify_order(mod_req)
        assert res_mod.error is None

        res_cancel = await provider.cancel_order("12345")
        assert res_cancel.error is None

    asyncio.run(run_test())


def test_modify_position_coverage() -> None:
    """
    Verify modify_position handles success, rejection, missing position, and None transport response.
    """

    async def run_test() -> None:
        provider = FakeMT5Mutations()
        mock_send = _make_mt5_send_res(10009)
        mock_pos = _make_mt5_pos(54321)

        provider._transport.call.side_effect = [mock_send, (mock_pos,)]

        req = BrokerPositionModificationRequest(
            position_id="54321",
            stop_loss=Decimal("1.0950"),
        )

        res = await provider.modify_position(req)
        assert res.error is None

        # Test None response
        provider._transport.call.side_effect = None
        provider._transport.call.return_value = None
        res_none = await provider.modify_position(req)
        assert res_none.error is not None

        # Test rejection response (retcode != 10009)
        mock_rej = _make_mt5_send_res(10013)  # Invalid request
        provider._transport.call.return_value = mock_rej
        res_rej = await provider.modify_position(req)
        assert res_rej.error is not None

        # Test missing position response
        provider._transport.call.side_effect = [mock_send, ()]
        res_empty = await provider.modify_position(req)
        assert res_empty.error is not None

    asyncio.run(run_test())


def test_close_position_coverage() -> None:
    """Verify close_position fetches open position and sends opposite deal action."""

    async def run_test() -> None:
        provider = FakeMT5Mutations()
        mock_pos = _make_mt5_pos(54321, pos_type=0)
        mock_send = _make_mt5_send_res(10009)

        provider._transport.call.side_effect = [(mock_pos,), mock_send]

        req = BrokerPositionCloseRequest(
            position_id="54321",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
        )

        res = await provider.close_position(req)
        assert res.error is None

        # Test missing position
        provider._transport.call.side_effect = None
        provider._transport.call.return_value = ()
        res_missing = await provider.close_position(req)
        assert res_missing.error is not None

    asyncio.run(run_test())
