"""cTrader protobuf-fixture mapping tests."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.brokers import BrokerErrorCode
from app.services.brokers.ctrader_session.mapping import (
    _map_error_code,
    _map_order,
    _map_quote,
    _optional,
)
from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOASpotEvent
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOAPosition


def test_map_quote_divides_by_symbol_digits() -> None:
    """Relative provider prices are divided by the exact symbol digit scale."""
    timestamp_ms = datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000
    quote = _map_quote(
        {"timestamp": timestamp_ms, "bid": 110000, "ask": 110020},
        "EURUSD",
        5,
    )
    assert str(quote.bid) == "1.1"
    assert str(quote.ask) == "1.1002"


def test_map_quote_never_fabricates_missing_sides() -> None:
    """A one-sided quote never invents the missing bid or ask."""
    timestamp_ms = datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000
    quote = _map_quote(
        {"timestamp": timestamp_ms, "bid": None, "ask": 110020},
        "EURUSD",
        5,
    )
    assert quote.bid is None
    assert quote.ask is not None


def test_optional_protobuf_scalar_preserves_presence() -> None:
    """An absent protobuf scalar is not mistaken for provider-reported zero."""
    position = ProtoOAPosition()
    assert _optional(position, "price") is None
    position.price = 0
    assert _optional(position, "price") == 0


def test_map_real_protobuf_quote_never_fabricates_absent_bid() -> None:
    """Actual protobuf presence semantics preserve a one-sided spot event."""
    event = ProtoOASpotEvent(
        ctidTraderAccountId=1,
        symbolId=1,
        ask=110_020,
        timestamp=1_700_000_000_000,
    )
    quote = _map_quote(event, "EURUSD", 5)
    assert quote.bid is None
    assert quote.ask is not None


def test_map_order_uses_canonical_unknown_and_preserves_native_code() -> None:
    """Unrecognized cTrader order types map to UNKNOWN with native evidence."""
    order = _map_order(
        {
            "orderId": 11,
            "tradeData": {"symbolId": 1, "volume": 10_000_000, "tradeSide": 1},
            "orderType": 99,
            "orderStatus": 1,
        },
        {1: "EURUSD"},
        {1: Decimal(100_000)},
    )
    assert order.order_type == "UNKNOWN"
    assert order.provider_metadata["native_order_type"] == 99


def test_map_error_code_scopes_not_found_by_operation() -> None:
    """Native not-found codes only map when the operation matches their scope."""
    assert (
        _map_error_code("ORDER_NOT_FOUND", "cancel_order")
        == BrokerErrorCode.BROKER_ORDER_NOT_FOUND
    )
    assert (
        _map_error_code("POSITION_NOT_FOUND", "close_position")
        == BrokerErrorCode.BROKER_POSITION_NOT_FOUND
    )
    assert (
        _map_error_code("ORDER_NOT_FOUND", "close_position")
        == BrokerErrorCode.BROKER_PROVIDER_ERROR
    )


def test_map_error_code_floor_covers_documented_codes() -> None:
    """Documented native codes map to their exact specialized error."""
    assert (
        _map_error_code("MARKET_CLOSED", "place_order")
        == BrokerErrorCode.BROKER_MARKET_CLOSED
    )
    assert (
        _map_error_code("NOT_ENOUGH_MONEY", "place_order")
        == BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN
    )
    assert (
        _map_error_code("INVALID_VOLUME", "place_order")
        == BrokerErrorCode.BROKER_REQUEST_INVALID
    )
