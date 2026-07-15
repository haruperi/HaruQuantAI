"""cTrader protobuf-fixture mapping tests."""

from datetime import UTC, datetime

from app.services.brokers import BrokerErrorCode
from app.services.brokers.ctrader.mapping import _map_error_code, _map_quote


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
