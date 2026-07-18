"""MetaTrader 5 provider payload to canonical DTO mapping."""

# ruff: noqa: ANN401, PLR2004 - SDK records and native retcodes are provider-defined.

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.brokers.contracts import (
    BrokerAccountInfo,
    BrokerBar,
    BrokerErrorCode,
    BrokerPosition,
    BrokerQuote,
    BrokerSymbolInfo,
    BrokerTick,
)


def _field(value: object, name: str) -> Any:
    if isinstance(value, dict):
        return value[name]
    try:
        return getattr(value, name)
    except AttributeError:
        return cast("Any", value)[name]


def _optional(value: object, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    try:
        return getattr(value, name)
    except AttributeError:
        try:
            return cast("Any", value)[name]
        except (IndexError, KeyError, TypeError, ValueError):
            return None


def _time(value: object, name: str = "time") -> datetime:
    raw = _field(value, name)
    return datetime.fromtimestamp(float(raw), UTC)


def _map_symbol(value: object) -> BrokerSymbolInfo:
    """Map mandatory MT5 symbol evidence without aliases.

    Returns:
        Canonical symbol information.
    """
    symbol = str(_field(value, "name"))
    digits = int(_field(value, "digits"))

    # Extract provider_metadata dynamically from value
    raw_dict = {}
    asdict_fn = getattr(value, "_asdict", None)
    if asdict_fn is not None:
        raw_dict = asdict_fn()
    elif isinstance(value, dict):
        raw_dict = dict(value)
    else:
        for name in dir(value):
            if not name.startswith("_"):
                try:
                    raw_dict[name] = getattr(value, name)
                except Exception:
                    pass

    return BrokerSymbolInfo(
        provider_symbol=symbol,
        product_profile="mt5",
        price_unit="quote_currency",
        quantity_unit="lots",
        price_precision=digits,
        quantity_step=Decimal(str(_field(value, "volume_step"))),
        min_quantity=Decimal(str(_field(value, "volume_min"))),
        max_quantity=Decimal(str(_field(value, "volume_max"))),
        provider_metadata=raw_dict,
    )


def _map_quote(value: object, symbol: str) -> BrokerQuote:
    """Map only genuine MT5 quote fields.

    Returns:
        Canonical quote evidence.
    """
    bid = Decimal(str(_field(value, "bid")))
    ask = Decimal(str(_field(value, "ask")))
    last = Decimal(str(_field(value, "last")))
    return BrokerQuote(
        symbol=symbol,
        price_unit="quote_currency",
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        bid=bid or None,
        ask=ask or None,
        last_price=last or None,
        provider_timestamp=_time(value),
    )


def _map_tick(value: object, symbol: str) -> BrokerTick:
    timestamp = _time(value)
    return BrokerTick(
        symbol=symbol,
        event_timestamp=timestamp,
        provider_receipt_timestamp=datetime.now(UTC),
        price_unit="quote_currency",
        quantity_unit="lots",
        tick_type="UNKNOWN",
        bid=Decimal(str(_optional(value, "bid"))) if _optional(value, "bid") else None,
        ask=Decimal(str(_optional(value, "ask"))) if _optional(value, "ask") else None,
        last_price=(
            Decimal(str(_optional(value, "last"))) if _optional(value, "last") else None
        ),
    )


def _map_bar(value: object, symbol: str, timeframe: str) -> BrokerBar:
    opening = _time(value)
    durations = {
        "M1": timedelta(minutes=1),
        "M2": timedelta(minutes=2),
        "M3": timedelta(minutes=3),
        "M4": timedelta(minutes=4),
        "M5": timedelta(minutes=5),
        "M6": timedelta(minutes=6),
        "M10": timedelta(minutes=10),
        "M12": timedelta(minutes=12),
        "M15": timedelta(minutes=15),
        "M20": timedelta(minutes=20),
        "M30": timedelta(minutes=30),
        "H1": timedelta(hours=1),
        "H2": timedelta(hours=2),
        "H3": timedelta(hours=3),
        "H4": timedelta(hours=4),
        "H6": timedelta(hours=6),
        "H8": timedelta(hours=8),
        "H12": timedelta(hours=12),
        "D1": timedelta(days=1),
        "W1": timedelta(days=7),
    }
    if timeframe == "MN1":
        closing = opening.replace(
            year=opening.year + (1 if opening.month == 12 else 0),
            month=1 if opening.month == 12 else opening.month + 1,
        )
    else:
        closing = opening + durations[timeframe]
    tick_volume = _optional(value, "tick_volume")
    real_volume = _optional(value, "real_volume")
    spread = _optional(value, "spread")
    return BrokerBar(
        symbol=symbol,
        opening_timestamp=opening,
        closing_timestamp=closing,
        is_closed=True,
        open=Decimal(str(_field(value, "open"))),
        high=Decimal(str(_field(value, "high"))),
        low=Decimal(str(_field(value, "low"))),
        close=Decimal(str(_field(value, "close"))),
        provider_timeframe=timeframe,
        requested_timeframe=timeframe,
        price_unit="quote_currency",
        quantity_unit="lots",
        trade_volume=(
            Decimal(str(real_volume)) if real_volume not in (None, 0) else None
        ),
        tick_volume=(Decimal(str(tick_volume)) if tick_volume is not None else None),
        spread=Decimal(str(spread)) if spread is not None else None,
        spread_unit="points" if spread is not None else None,
    )


def _map_account(value: object) -> BrokerAccountInfo:
    """Map direct MT5 account state.

    Returns:
        Canonical account information.
    """
    return BrokerAccountInfo(
        account_id=str(_field(value, "login")),
        retrieved_at=datetime.now(UTC),
        account_reference_redacted="***",
        currency=str(_field(value, "currency")),
        balance=Decimal(str(_field(value, "balance"))),
        equity=Decimal(str(_field(value, "equity"))),
        margin=Decimal(str(_field(value, "margin"))),
        free_margin=Decimal(str(_field(value, "margin_free"))),
    )


def _map_position(value: object) -> BrokerPosition:
    """Map direct MT5 position state.

    Returns:
        Canonical open-position information.
    """
    return BrokerPosition(
        position_id=str(_field(value, "ticket")),
        symbol=str(_field(value, "symbol")),
        side="LONG" if int(_field(value, "type")) == 0 else "SHORT",
        quantity=Decimal(str(_field(value, "volume"))),
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        state="OPEN",
        open_price=Decimal(str(_field(value, "price_open"))),
        current_price=Decimal(str(_field(value, "price_current"))),
        profit=Decimal(str(_field(value, "profit"))),
        provider_timestamp=_time(value, "time_update"),
    )


def _map_error_code(retcode: int) -> BrokerErrorCode:
    """Map the normative MT5 order-retcode floor.

    Returns:
        Canonical broker error code.
    """
    if retcode == 10019:
        return BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN
    if retcode in {10018, 10021}:
        return BrokerErrorCode.BROKER_MARKET_CLOSED
    if retcode in {10013, 10014, 10015, 10016, 10022, 10030, 10035, 10038}:
        return BrokerErrorCode.BROKER_REQUEST_INVALID
    if retcode in {10006, 10007, 10010, 10017, 10031, 10032, 10033, 10034}:
        return BrokerErrorCode.BROKER_REQUEST_REJECTED
    return BrokerErrorCode.BROKER_PROVIDER_ERROR
