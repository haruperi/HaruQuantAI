"""MetaTrader 5 provider payload to canonical DTO mapping."""

# ruff: noqa: ANN401, PLR2004 - SDK records and native retcodes are provider-defined.

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.brokers.contracts import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerBalance,
    BrokerBar,
    BrokerDeal,
    BrokerErrorCode,
    BrokerOrder,
    BrokerOrderCheck,
    BrokerOrderResult,
    BrokerPermissions,
    BrokerPosition,
    BrokerQuote,
    BrokerSymbolInfo,
    BrokerTick,
)


def _field(value: object, name: str) -> Any:
    """Handle field.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Returns:
        The operation result.
    """
    if isinstance(value, dict):
        return value[name]
    try:
        return getattr(value, name)
    except AttributeError:
        return cast("Any", value)[name]


def _optional(value: object, name: str) -> Any:
    """Handle optional.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Returns:
        The operation result.
    """
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
    """Handle time.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Returns:
        The operation result.
    """
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
    """Map map tick.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.

    Returns:
        The operation result.
    """
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
    """Map map bar.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        timeframe: Value supplied to the operation.

    Returns:
        The operation result.
    """
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
    position_type = int(_field(value, "type"))
    side = (
        "LONG" if position_type == 0 else "SHORT" if position_type == 1 else "UNKNOWN"
    )
    return BrokerPosition(
        position_id=str(_field(value, "ticket")),
        symbol=str(_field(value, "symbol")),
        side=cast("Any", side),
        quantity=Decimal(str(_field(value, "volume"))),
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        state="OPEN",
        open_price=Decimal(str(_field(value, "price_open"))),
        current_price=Decimal(str(_field(value, "price_current"))),
        profit=Decimal(str(_field(value, "profit"))),
        provider_timestamp=_time(value, "time_update"),
    )


def _map_permissions(account: object, terminal: object) -> BrokerPermissions:
    """Map only permission fields reported by the terminal and account.

    Returns:
        Canonical provider-reported permissions.
    """
    account_trade = _optional(account, "trade_allowed")
    terminal_trade = _optional(terminal, "trade_allowed")
    connected = _optional(terminal, "connected")
    return BrokerPermissions(
        observed_at=datetime.now(UTC),
        market_data_read=bool(connected) if connected is not None else None,
        account_read=True,
        trade_write=(
            bool(account_trade and terminal_trade)
            if account_trade is not None and terminal_trade is not None
            else None
        ),
        subscription=None,
        provider_permissions={
            "account_trade_allowed": (
                bool(account_trade) if account_trade is not None else None
            ),
            "terminal_trade_allowed": (
                bool(terminal_trade) if terminal_trade is not None else None
            ),
        },
    )


def _map_balance(value: object) -> BrokerBalance:
    """Map the MT5 account-currency balance without inventing availability.

    Returns:
        Canonical account-currency balance.
    """
    currency = str(_field(value, "currency"))
    return BrokerBalance(
        asset=currency,
        unit=currency,
        retrieved_at=datetime.now(UTC),
        total=Decimal(str(_field(value, "balance"))),
    )


def _side(type_code: int) -> str:
    """Map MT5 order/deal direction codes.

    Returns:
        Canonical side value.
    """
    if type_code in {0, 2, 4, 6}:
        return "BUY"
    if type_code in {1, 3, 5, 7}:
        return "SELL"
    return "UNKNOWN"


def _map_order(value: object) -> BrokerOrder:
    """Map one MT5 active or historical order.

    Returns:
        Canonical order state.
    """
    quantity = Decimal(str(_field(value, "volume_initial")))
    remaining = Decimal(str(_field(value, "volume_current")))
    type_code = int(_field(value, "type"))
    order_types = {
        0: "MARKET",
        1: "MARKET",
        2: "LIMIT",
        3: "LIMIT",
        4: "STOP",
        5: "STOP",
        6: "STOP_LIMIT",
        7: "STOP_LIMIT",
        8: "UNKNOWN",
    }
    states = {
        0: "PENDING",
        1: "ACCEPTED",
        2: "CANCELLED",
        3: "PARTIALLY_FILLED",
        4: "FILLED",
        5: "REJECTED",
        6: "EXPIRED",
        7: "PENDING",
        8: "PENDING",
        9: "PENDING",
    }
    timestamp_name = "time_done" if _optional(value, "time_done") else "time_setup"
    return BrokerOrder(
        order_id=str(_field(value, "ticket")),
        symbol=str(_field(value, "symbol")),
        side=cast("Any", _side(type_code)),
        order_type=order_types.get(type_code, "UNKNOWN"),
        state=states.get(int(_field(value, "state")), "UNKNOWN"),
        quantity=quantity,
        filled=quantity - remaining,
        remaining=remaining,
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        price=(
            Decimal(str(_optional(value, "price_open")))
            if _optional(value, "price_open") is not None
            else None
        ),
        stop_price=(
            Decimal(str(_optional(value, "price_stoplimit")))
            if _optional(value, "price_stoplimit") is not None
            else None
        ),
        product_profile="mt5",
        provider_timestamp=_time(value, timestamp_name),
        provider_metadata={
            "reason": _optional(value, "reason"),
            "magic": _optional(value, "magic"),
            "native_order_type": type_code,
            "native_order_state": int(_field(value, "state")),
        },
    )


def _map_deal(value: object) -> BrokerDeal:
    """Map one MT5 execution deal.

    Returns:
        Canonical provider deal.
    """
    fee = sum(
        Decimal(str(item or 0))
        for item in (
            _optional(value, "commission"),
            _optional(value, "fee"),
        )
    )
    return BrokerDeal(
        deal_id=str(_field(value, "ticket")),
        order_id=(
            str(_optional(value, "order")) if _optional(value, "order") else None
        ),
        position_id=(
            str(_optional(value, "position_id"))
            if _optional(value, "position_id")
            else None
        ),
        symbol=str(_field(value, "symbol")),
        side=cast("Any", _side(int(_field(value, "type")))),
        quantity=Decimal(str(_field(value, "volume"))),
        quantity_unit="lots",
        price=Decimal(str(_field(value, "price"))),
        partial=bool(_optional(value, "entry") == 2),
        retrieved_at=datetime.now(UTC),
        fee=fee or None,
        provider_timestamp=_time(value),
    )


def _map_transaction(value: object, currency: str) -> BrokerAccountTransaction:
    """Map one non-trade MT5 deal as an account transaction.

    Args:
        value: Provider deal payload.
        currency: Verified account currency.

    Returns:
        Canonical account transaction.
    """
    type_code = int(_field(value, "type"))
    amount = sum(
        (
            Decimal(str(item or 0))
            for item in (
                _optional(value, "profit"),
                _optional(value, "commission"),
                _optional(value, "swap"),
                _optional(value, "fee"),
            )
        ),
        start=Decimal(0),
    )
    transaction_type = {
        3: "ADJUSTMENT",
        4: "FEE",
        5: "ADJUSTMENT",
        6: "ADJUSTMENT",
        7: "COMMISSION",
        8: "COMMISSION",
        9: "COMMISSION",
        10: "COMMISSION",
        11: "COMMISSION",
        12: "INTEREST",
        13: "ADJUSTMENT",
        14: "ADJUSTMENT",
        15: "INTEREST",
        16: "INTEREST",
        17: "FEE",
    }.get(type_code, "UNKNOWN")
    if type_code == 2:
        transaction_type = "DEPOSIT" if amount >= 0 else "WITHDRAWAL"
    return BrokerAccountTransaction(
        transaction_id=str(_field(value, "ticket")),
        transaction_type=transaction_type,
        asset=currency,
        currency=currency,
        amount=amount,
        provider_timestamp=_time(value),
        retrieved_at=datetime.now(UTC),
        provider_metadata={
            "reason": _optional(value, "reason"),
            "native_transaction_type": type_code,
        },
    )


def _map_order_check(value: object) -> BrokerOrderCheck:
    """Map an MT5 pre-submission order check.

    Returns:
        Canonical non-final order check.
    """
    retcode = int(_field(value, "retcode"))
    return BrokerOrderCheck(
        accepted_for_submission=retcode == 0,
        provider_code=str(retcode),
        provider_message=(
            str(_optional(value, "comment"))
            if _optional(value, "comment") is not None
            else None
        ),
        estimated_margin=(
            Decimal(str(_optional(value, "margin")))
            if _optional(value, "margin") is not None
            else None
        ),
    )


def _map_order_result(value: object) -> BrokerOrderResult:
    """Map one acknowledged MT5 order-send response.

    Returns:
        Canonical explicit mutation outcome.
    """
    retcode = int(_field(value, "retcode"))
    accepted = retcode in {10008, 10009}
    partial = retcode == 10010
    order = _optional(value, "order")
    deal = _optional(value, "deal")
    order_id = str(order or deal) if accepted or partial else None
    return BrokerOrderResult(
        acknowledged=True,
        outcome="PARTIAL" if partial else ("ACCEPTED" if accepted else "REJECTED"),
        retrieved_at=datetime.now(UTC),
        order_id=order_id,
        deal_ids=(str(deal),) if deal else (),
        filled_quantity=(
            Decimal(str(_optional(value, "volume")))
            if _optional(value, "volume") is not None
            else None
        ),
        average_price=(
            Decimal(str(_optional(value, "price")))
            if _optional(value, "price") is not None
            else None
        ),
        provider_code=str(retcode),
        provider_message=(
            str(_optional(value, "comment"))
            if _optional(value, "comment") is not None
            else None
        ),
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
