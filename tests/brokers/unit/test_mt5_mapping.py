"""MT5 payload/native-error mapping tests."""

from datetime import UTC, datetime

from app.services.brokers import BrokerErrorCode
from app.services.brokers.mt5.mapping import (
    _map_account,
    _map_error_code,
    _map_position,
    _map_quote,
    _map_symbol,
    _map_tick,
)


def _record(**fields: object) -> dict[str, object]:
    return dict(fields)


def test_map_symbol_preserves_exact_provider_values() -> None:
    """Documented MT5 symbol fields map without alias substitution."""
    symbol = _map_symbol(
        _record(
            name="EURUSD",
            digits=5,
            volume_step=0.01,
            volume_min=0.01,
            volume_max=100,
        )
    )
    assert symbol.provider_symbol == "EURUSD"
    assert symbol.price_precision == 5
    assert str(symbol.quantity_step) == "0.01"


def test_map_quote_preserves_bid_ask_last() -> None:
    """Genuine MT5 tick fields map to a canonical quote."""
    quote = _map_quote(
        _record(
            bid=1.1000,
            ask=1.1002,
            last=1.1001,
            time=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        ),
        "EURUSD",
    )
    assert str(quote.bid) == "1.1"
    assert str(quote.ask) == "1.1002"


def test_map_tick_handles_missing_optional_prices() -> None:
    """Ticks without a last-trade price never fabricate one."""
    tick = _map_tick(
        _record(
            time=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
            bid=1.1,
            ask=None,
            last=None,
        ),
        "EURUSD",
    )
    assert tick.ask is None
    assert tick.last_price is None


def test_map_account_redacts_account_reference() -> None:
    """Account mapping never exposes a raw account reference."""
    account = _map_account(
        _record(
            login=12345,
            currency="USD",
            balance=100,
            equity=100,
            margin=0,
            margin_free=100,
        )
    )
    assert account.account_id == "12345"
    assert account.account_reference_redacted == "***"


def test_map_position_derives_side_from_type_code() -> None:
    """MT5 numeric position-type codes map to explicit canonical sides."""
    long_position = _map_position(
        _record(
            ticket=1,
            symbol="EURUSD",
            type=0,
            volume=1,
            price_open=1.1,
            price_current=1.2,
            profit=100,
            time_update=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        )
    )
    assert long_position.side == "LONG"
    short_position = _map_position(
        _record(
            ticket=2,
            symbol="EURUSD",
            type=1,
            volume=1,
            price_open=1.1,
            price_current=1.2,
            profit=-50,
            time_update=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        )
    )
    assert short_position.side == "SHORT"


def test_map_error_code_floor_is_exhaustive_for_documented_retcodes() -> None:
    """Documented MT5 retcode groups map to their exact canonical codes."""
    assert _map_error_code(10019) == BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN
    assert _map_error_code(10018) == BrokerErrorCode.BROKER_MARKET_CLOSED
    assert _map_error_code(10013) == BrokerErrorCode.BROKER_REQUEST_INVALID
    assert _map_error_code(10006) == BrokerErrorCode.BROKER_REQUEST_REJECTED
    assert _map_error_code(999999) == BrokerErrorCode.BROKER_PROVIDER_ERROR
