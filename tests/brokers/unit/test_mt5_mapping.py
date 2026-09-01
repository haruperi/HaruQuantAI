"""MT5 payload/native-error mapping tests."""

from datetime import UTC, datetime
from decimal import Decimal

import numpy as np
import pytest
from app.services.brokers.metatrader._legacy_types import BrokerErrorCode
from app.services.brokers.metatrader.mapping import (
    _map_account,
    _map_bar,
    _map_error_code,
    _map_order,
    _map_order_result,
    _map_position,
    _map_quote,
    _map_symbol,
    _map_tick,
    _map_transaction,
)


def _record(**fields: object) -> dict[str, object]:
    return dict(fields)


def test_map_symbol_preserves_exact_provider_values() -> None:
    """Documented MT5 symbol fields map without alias substitution."""
    symbol = _map_symbol(
        _record(
            name="EURUSD",
            digits=5,
            point=0.00001,
            trade_tick_size=0.00001,
            trade_contract_size=100000,
            trade_mode=4,
            swap_mode=1,
            swap_long=-6.5,
            swap_short=2.1,
            volume_step=0.01,
            volume_min=0.01,
            volume_max=100,
        )
    )
    assert symbol.provider_symbol == "EURUSD"
    assert symbol.price_precision == 5
    assert symbol.price_step == Decimal("0.00001")
    assert str(symbol.quantity_step) == "0.01"
    assert symbol.provider_metadata["digits"] == 5
    assert symbol.provider_metadata["trade_mode"] == "FULL"


def test_map_symbol_preserves_path_attribute() -> None:
    """MT5 native path attribute is preserved in provider_metadata for asset classification."""
    symbol = _map_symbol(
        _record(
            name="EURJPY",
            digits=3,
            point=0.001,
            trade_tick_size=0.001,
            trade_contract_size=100000,
            trade_mode=4,
            swap_mode=1,
            swap_long=-6.5,
            swap_short=2.1,
            volume_step=0.01,
            volume_min=0.01,
            volume_max=100,
            path="Forex\\EURJPY",
        )
    )
    assert symbol.provider_symbol == "EURJPY"
    assert symbol.provider_metadata["path"] == "Forex\\EURJPY"


@pytest.mark.parametrize("field", ["point", "trade_tick_size", "trade_contract_size"])
def test_map_symbol_rejects_missing_provider_contract_fact(field: str) -> None:
    """Fail closed instead of supplying a symbol-contract fallback."""
    payload = {
        "name": "EURUSD",
        "digits": 5,
        "point": 0.00001,
        "trade_tick_size": 0.00001,
        "trade_contract_size": 100000,
        "trade_mode": 4,
        "swap_mode": 1,
        "swap_long": -7.24,
        "swap_short": 2.1,
        "volume_step": 0.01,
        "volume_min": 0.01,
        "volume_max": 100,
    }
    del payload[field]
    with pytest.raises(KeyError):
        _map_symbol(payload)


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


def test_map_bar_derives_a_nonzero_close_time() -> None:
    """MT5 opening timestamps become valid closed canonical bar windows."""
    opening = datetime(2026, 1, 1, tzinfo=UTC)
    bar = _map_bar(
        _record(
            time=opening.timestamp(),
            open=1.1,
            high=1.2,
            low=1.0,
            close=1.15,
            tick_volume=25,
            real_volume=0,
        ),
        "EURUSD",
        "M1",
    )

    assert bar.opening_timestamp == opening
    assert bar.closing_timestamp > opening
    assert str(bar.tick_volume) == "25"
    assert bar.spread is None


def test_map_bar_reads_mt5_numpy_structured_records() -> None:
    """MT5 NumPy rows map through their named fields."""
    opening = datetime(2026, 1, 1, tzinfo=UTC)
    record = np.array(
        [
            (
                int(opening.timestamp()),
                1.1,
                1.2,
                1.0,
                1.15,
                25,
                2,
                0,
            )
        ],
        dtype=[
            ("time", "<i8"),
            ("open", "<f8"),
            ("high", "<f8"),
            ("low", "<f8"),
            ("close", "<f8"),
            ("tick_volume", "<u8"),
            ("spread", "<i4"),
            ("real_volume", "<u8"),
        ],
    )[0]

    bar = _map_bar(record, "EURUSD", "M1")

    assert bar.opening_timestamp == opening
    assert str(bar.close) == "1.15"
    assert str(bar.tick_volume) == "25"
    assert str(bar.spread) == "2"
    assert bar.spread_unit == "points"


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
            trade_mode=0,
            margin_mode=1,
            leverage=100,
        )
    )
    assert account.account_id == "12345"
    assert account.account_reference_redacted == "***"
    assert account.details["login"] == "12345"
    assert account.details["trade_mode"] == "DEMO"


def test_map_account_rejects_missing_leverage() -> None:
    """Fail closed instead of supplying an account-leverage fallback."""
    with pytest.raises(KeyError):
        _map_account(
            _record(
                login=12345,
                currency="USD",
                balance=100,
                equity=100,
                margin=0,
                margin_free=100,
                trade_mode=0,
                margin_mode=1,
            )
        )


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
            magic=12345,
            time_update=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        )
    )
    assert long_position.side == "LONG"
    assert long_position.ownership_ref == "mt5-magic:12345"
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

    unknown_position = _map_position(
        _record(
            ticket=3,
            symbol="EURUSD",
            type=99,
            volume=1,
            price_open=1.1,
            price_current=1.2,
            profit=0,
            time_update=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        )
    )
    assert unknown_position.side == "UNKNOWN"


def test_map_order_uses_only_canonical_state_vocabulary() -> None:
    """MT5 native state/type codes never leak into canonical enum fields."""
    order = _map_order(
        _record(
            ticket=1,
            symbol="EURUSD",
            type=8,
            state=3,
            volume_initial=1,
            volume_current=0.5,
            time_setup=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        )
    )
    assert order.order_type == "UNKNOWN"
    assert order.state == "PARTIALLY_FILLED"
    assert order.provider_metadata["native_order_type"] == 8


def test_map_pending_order_does_not_invent_a_fill() -> None:
    """An MT5 placed acknowledgement preserves volume as remaining."""
    result = _map_order_result(
        _record(
            retcode=10008,
            order=123,
            deal=0,
            volume=0.01,
            price=0,
            comment="Request accepted",
        )
    )

    assert result.outcome == "ACCEPTED"
    assert result.order_id == "123"
    assert result.deal_ids == ()
    assert result.filled_quantity == 0
    assert str(result.remaining_quantity) == "0.01"


def test_map_done_pending_order_without_deal_does_not_invent_a_fill() -> None:
    """A completed request without a deal remains an unfilled order."""
    result = _map_order_result(
        _record(
            retcode=10009,
            order=123,
            deal=0,
            volume=0.01,
            price=0,
            comment="Request completed",
        )
    )

    assert result.outcome == "ACCEPTED"
    assert result.deal_ids == ()
    assert result.filled_quantity == 0
    assert str(result.remaining_quantity) == "0.01"


def test_map_completed_order_preserves_provider_fill() -> None:
    """An MT5 completed acknowledgement preserves deal-backed fill volume."""
    result = _map_order_result(
        _record(
            retcode=10009,
            order=123,
            deal=456,
            volume=0.01,
            price=1.1,
            comment="Request completed",
        )
    )

    assert result.outcome == "ACCEPTED"
    assert result.deal_ids == ("456",)
    assert str(result.filled_quantity) == "0.01"
    assert result.remaining_quantity == 0


def test_map_transaction_uses_canonical_type_and_preserves_native_code() -> None:
    """MT5 balance records map by sign without leaking provider vocabulary."""
    transaction = _map_transaction(
        _record(
            ticket=1,
            type=2,
            profit=-25,
            commission=0,
            swap=0,
            fee=0,
            time=datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
        ),
        "USD",
    )
    assert transaction.transaction_type == "WITHDRAWAL"
    assert transaction.provider_metadata["native_transaction_type"] == 2


def test_map_error_code_floor_is_exhaustive_for_documented_retcodes() -> None:
    """Documented MT5 retcode groups map to their exact canonical codes."""
    assert _map_error_code(10019) == BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN
    assert _map_error_code(10018) == BrokerErrorCode.BROKER_MARKET_CLOSED
    assert _map_error_code(10013) == BrokerErrorCode.BROKER_REQUEST_INVALID
    assert _map_error_code(10006) == BrokerErrorCode.BROKER_REQUEST_REJECTED
    assert _map_error_code(999999) == BrokerErrorCode.BROKER_PROVIDER_ERROR
