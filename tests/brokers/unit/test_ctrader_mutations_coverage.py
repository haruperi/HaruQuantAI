"""Coverage expansion tests for cTrader mutation operations."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
)
from app.services.brokers.contracts.protocols import _RequestValidationError
from app.services.brokers.ctrader_session.adapter import (
    CTraderBrokerAdapter as _CTraderMutationsMixin,
)
from app.utils.responses.models import StandardResponse

from tests.brokers.response_factory import broker_response


def _make_result(
    operation: BrokerCapabilityId, data: object = None, error: object = None
) -> StandardResponse:
    return broker_response(
        operation,
        broker=BrokerId.CTRADER,
        environment=BrokerEnvironment.SANDBOX,
        data=data,
        error=error,
    )


class FakeCTraderMutations:
    check_order = _CTraderMutationsMixin.check_order
    place_order = _CTraderMutationsMixin.place_order
    modify_order = _CTraderMutationsMixin.modify_order
    cancel_order = _CTraderMutationsMixin.cancel_order
    modify_position = _CTraderMutationsMixin.modify_position
    close_position = _CTraderMutationsMixin.close_position
    _execution = _CTraderMutationsMixin._execution
    _propagated_error = _CTraderMutationsMixin._propagated_error
    _copy_order_fields = staticmethod(_CTraderMutationsMixin._copy_order_fields)

    def __init__(self) -> None:
        self.calculate_margin = AsyncMock()
        self._symbol_identity = AsyncMock(return_value=(101, 5))
        self._provider_volume = AsyncMock(return_value=100000)
        self.get_positions = AsyncMock()
        self._request = AsyncMock()
        self._ensure_symbols = AsyncMock()
        self._symbol_names = {101: "EURUSD"}

    def _result(
        self, operation: BrokerCapabilityId, data: object = None, error: object = None
    ) -> StandardResponse:
        return _make_result(operation, data=data, error=error)

    def _error(self, operation: BrokerCapabilityId, error: object) -> StandardResponse:
        return _make_result(operation, error=error)


def _make_order_result(order_id: str = "ord-1") -> BrokerOrderResult:
    return BrokerOrderResult(
        acknowledged=True,
        outcome="ACCEPTED",
        retrieved_at=datetime.now(UTC),
        order_id=order_id,
    )


def test_check_order_success() -> None:
    """Verify check_order validates symbol and returns estimated margin."""

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider.calculate_margin.return_value = _make_result(
            BrokerCapabilityId.CALCULATE_MARGIN,
            data=Decimal("150.00"),
        )

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
        assert res.data.accepted_for_submission is True
        assert res.data.estimated_margin == Decimal("150.00")

    asyncio.run(run_test())


def test_check_order_margin_failure() -> None:
    """Verify check_order propagates calculate_margin error."""

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider.calculate_margin.return_value = _make_result(
            BrokerCapabilityId.CALCULATE_MARGIN,
            error="MARGIN_ERROR",
        )

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
        assert res.error is not None
        assert res.error.code == BrokerErrorCode.BROKER_RESPONSE_INVALID.value

    asyncio.run(run_test())


def test_place_order_success() -> None:
    """Verify place_order formats ProtoOANewOrderReq fields and calls _execution."""

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.PLACE_ORDER,
                data=_make_order_result("ord-1"),
            )
        )

        req = BrokerOrderRequest(
            environment=BrokerEnvironment.SANDBOX,
            symbol="EURUSD",
            side="BUY",
            order_type="LIMIT",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
            account_reference="acc-1",
            limit_price=Decimal("1.1050"),
            time_in_force="GTD",
            expiration=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
            comment="test-comment",
        )

        res = await provider.place_order(req)
        assert res.error is None
        provider._execution.assert_called_once()
        _, kwargs = provider._execution.call_args
        assert kwargs["symbolId"] == 101
        assert kwargs["orderType"] == 2
        assert kwargs["tradeSide"] == 1
        assert kwargs["limitPrice"] == 1.1050
        assert kwargs["comment"] == "test-comment"

    asyncio.run(run_test())


def test_modify_order_success() -> None:
    """Verify modify_order formats ProtoOAAmendOrderReq and calls _execution."""

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.MODIFY_ORDER,
                data=_make_order_result("12345"),
            )
        )
        provider._symbol_for_order = AsyncMock(return_value="EURUSD")

        req = BrokerOrderModificationRequest(
            order_id="12345",
            quantity=Decimal("2.0"),
            stop_price=Decimal("1.1000"),
        )

        res = await provider.modify_order(req)
        assert res.error is None
        provider._execution.assert_called_once()
        _, kwargs = provider._execution.call_args
        assert kwargs["orderId"] == 12345
        assert kwargs["stopPrice"] == 1.1000

    asyncio.run(run_test())


def test_cancel_order_success() -> None:
    """Verify cancel_order submits ProtoOACancelOrderReq."""

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.CANCEL_ORDER,
                data=_make_order_result("12345"),
            )
        )

        res = await provider.cancel_order("12345")
        assert res.error is None
        provider._execution.assert_called_once_with(
            BrokerCapabilityId.CANCEL_ORDER,
            "ProtoOACancelOrderReq",
            fallback_id="12345",
            orderId=12345,
        )

    asyncio.run(run_test())


def test_modify_position_success_and_error() -> None:
    """
    Verify modify_position handles execution success, missing position error, and execution error.
    """

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.MODIFY_POSITION,
                data=_make_order_result("54321"),
            )
        )

        mock_pos = MagicMock(spec=BrokerPosition)
        mock_pos.position_id = "54321"
        provider.get_positions.return_value = _make_result(
            BrokerCapabilityId.GET_POSITIONS,
            data=MagicMock(items=(mock_pos,)),
        )

        req = BrokerPositionModificationRequest(
            position_id="54321",
            stop_loss=Decimal("1.0950"),
        )

        res = await provider.modify_position(req)
        assert res.error is None
        assert res.data == mock_pos

        # Test execution error
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.MODIFY_POSITION,
                error="EXEC_ERROR",
            )
        )
        res_err = await provider.modify_position(req)
        assert res_err.error is not None
        assert res_err.error.code == BrokerErrorCode.BROKER_RESPONSE_INVALID.value

        # Test missing position error
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.MODIFY_POSITION,
                data=_make_order_result("54321"),
            )
        )
        provider.get_positions.return_value = _make_result(
            BrokerCapabilityId.GET_POSITIONS,
            data=MagicMock(items=()),
        )
        res_missing = await provider.modify_position(req)
        assert res_missing.error is not None

    asyncio.run(run_test())


def test_close_position_success() -> None:
    """Verify close_position submits ProtoOAClosePositionReq."""

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        provider._symbol_for_position = AsyncMock(return_value="EURUSD")
        provider._execution = AsyncMock(
            return_value=_make_result(
                BrokerCapabilityId.CLOSE_POSITION,
                data=_make_order_result("54321"),
            )
        )

        req = BrokerPositionCloseRequest(
            position_id="54321",
            quantity=Decimal("1.0"),
            quantity_unit="lots",
        )

        res = await provider.close_position(req)
        assert res.error is None
        provider._execution.assert_called_once_with(
            BrokerCapabilityId.CLOSE_POSITION,
            "ProtoOAClosePositionReq",
            fallback_id="54321",
            positionId=54321,
            volume=100000,
        )

    asyncio.run(run_test())


def test_symbol_for_order_found_and_missing() -> None:
    """
    Verify _symbol_for_order resolves order symbol or raises _RequestValidationError.
    """

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        mock_order = {"orderId": 12345, "tradeData": {"symbolId": 101}}
        mock_res = {"order": (mock_order,)}
        provider._request.return_value = mock_res

        symbol = await _CTraderMutationsMixin._symbol_for_order(provider, "12345")
        assert symbol == "EURUSD"

        with pytest.raises(
            _RequestValidationError, match="cTrader active order is absent"
        ):
            await _CTraderMutationsMixin._symbol_for_order(provider, "99999")

    asyncio.run(run_test())


def test_symbol_for_position_found_and_missing() -> None:
    """
    Verify _symbol_for_position resolves position symbol or raises _RequestValidationError.
    """

    async def run_test() -> None:
        provider = FakeCTraderMutations()
        mock_pos = {"positionId": 54321, "tradeData": {"symbolId": 101}}
        mock_res = {"position": (mock_pos,)}
        provider._request.return_value = mock_res

        symbol = await _CTraderMutationsMixin._symbol_for_position(provider, "54321")
        assert symbol == "EURUSD"

        with pytest.raises(
            _RequestValidationError, match="cTrader active position is absent"
        ):
            await _CTraderMutationsMixin._symbol_for_position(provider, "99999")

    asyncio.run(run_test())


def test_copy_order_fields_helper() -> None:
    """Verify _copy_order_fields extracts all optional fields into provider dict."""
    fields: dict[str, object] = {}
    exp = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
    req = MagicMock(
        limit_price=1.1000,
        stop_price=1.0950,
        stop_loss=1.0900,
        take_profit=1.1100,
        expiration=exp,
        comment="c1",
        label="l1",
        client_order_id="id1",
    )

    _CTraderMutationsMixin._copy_order_fields(fields, req)
    assert fields["limitPrice"] == 1.1000
    assert fields["stopPrice"] == 1.0950
    assert fields["stopLoss"] == 1.0900
    assert fields["takeProfit"] == 1.1100
    assert fields["expirationTimestamp"] == int(exp.timestamp() * 1000)
    assert fields["comment"] == "c1"
    assert fields["label"] == "l1"
    assert fields["clientOrderId"] == "id1"
