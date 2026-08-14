"""MetaTrader provider payload to canonical DTO mapping."""

# ruff: noqa: ANN401, PLR2004 - SDK records and native retcodes are provider-defined.
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.brokers.canonical_contracts import (
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
        except IndexError, KeyError, TypeError, ValueError:
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

    Args:
        value: Value supplied to the operation.

    Returns:
        Canonical symbol information.
    """
    symbol = str(_field(value, "name"))
    digits = int(_field(value, "digits"))

    raw_dict: dict[str, object] = {}
    asdict_fn = getattr(value, "_asdict", None)
    if asdict_fn is not None:
        raw_dict = dict(asdict_fn())
    elif isinstance(value, dict):
        raw_dict = dict(value)

    trade_mode_raw = _optional(value, "trade_mode")
    trade_mode_str = (
        {
            0: "DISABLED",
            1: "LONGONLY",
            2: "SHORTONLY",
            3: "CLOSEONLY",
            4: "FULL",
        }.get(cast("int", trade_mode_raw), str(trade_mode_raw))
        if trade_mode_raw is not None
        else "FULL"
    )
    trade_mode_desc = (
        {
            0: "No trading allowed",
            1: "Long positions only",
            2: "Short positions only",
            3: "Close positions only",
            4: "Full trading access",
        }.get(cast("int", trade_mode_raw), "Full access")
        if trade_mode_raw is not None
        else "Full trading access"
    )

    swap_mode_raw = _optional(value, "swap_mode")
    swap_mode_str = (
        {
            0: "DISABLED",
            1: "POINTS",
            2: "CURRENCY_SYMBOL",
            3: "CURRENCY_MARGIN",
            4: "CURRENCY_DEPOSIT",
            5: "INTEREST_CURRENT",
            6: "REOPEN_CURRENT",
            7: "REOPEN_BID",
        }.get(cast("int", swap_mode_raw), str(swap_mode_raw))
        if swap_mode_raw is not None
        else "POINTS"
    )

    point = float(_optional(value, "point") or (10.0**-digits))
    tick_size = float(
        _optional(value, "trade_tick_size") or _optional(value, "tick_size") or point
    )
    contract_size = float(_optional(value, "trade_contract_size") or 100000.0)

    bid = _optional(value, "bid")
    ask = _optional(value, "ask")
    last = _optional(value, "last")
    spread = _optional(value, "spread")

    raw_dict.update(
        {
            "name": symbol,
            "digits": digits,
            "point": point,
            "tick_size": tick_size,
            "trade_mode": trade_mode_str,
            "trade_mode_description": trade_mode_desc,
            "contract_size": contract_size,
            "volume_min": float(_field(value, "volume_min")),
            "volume_max": float(_field(value, "volume_max")),
            "volume_step": float(_field(value, "volume_step")),
            "swap_mode": swap_mode_str,
            "swap_long": float(_optional(value, "swap_long") or 0.0),
            "swap_short": float(_optional(value, "swap_short") or 0.0),
        }
    )
    if bid is not None:
        raw_dict["bid"] = float(bid)
    if ask is not None:
        raw_dict["ask"] = float(ask)
    if last is not None:
        raw_dict["last"] = float(last)
    if spread is not None:
        raw_dict["spread"] = int(spread)

    return BrokerSymbolInfo(
        provider_symbol=symbol,
        product_profile="mt5",
        price_unit="quote_currency",
        quantity_unit="lots",
        price_precision=digits,
        price_step=Decimal(str(point)),
        quantity_step=Decimal(str(_field(value, "volume_step"))),
        min_quantity=Decimal(str(_field(value, "volume_min"))),
        max_quantity=Decimal(str(_field(value, "volume_max"))),
        provider_metadata=raw_dict,
    )


def _map_quote(value: object, symbol: str) -> BrokerQuote:
    """Map only genuine MT5 quote fields.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.

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
    raw_msc = _optional(value, "time_msc")
    if raw_msc is not None and float(raw_msc) > 0:
        timestamp = datetime.fromtimestamp(float(raw_msc) / 1000.0, UTC)
    else:
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

    Args:
        value: Value supplied to the operation.

    Returns:
        Canonical account information.
    """
    currency = str(_field(value, "currency"))
    balance = Decimal(str(_field(value, "balance")))
    equity = Decimal(str(_field(value, "equity")))
    margin = Decimal(str(_field(value, "margin")))
    free_margin = Decimal(str(_field(value, "margin_free")))

    trade_mode_raw = _optional(value, "trade_mode")
    trade_mode_str = (
        {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(
            cast("int", trade_mode_raw), str(trade_mode_raw)
        )
        if trade_mode_raw is not None
        else "DEMO"
    )
    trade_mode_desc = (
        {0: "Demo account", 1: "Contest account", 2: "Real account"}.get(
            cast("int", trade_mode_raw), "Unknown"
        )
        if trade_mode_raw is not None
        else "Demo account"
    )

    margin_mode_raw = _optional(value, "margin_mode")
    margin_mode_str = (
        {0: "NETTING", 1: "HEDGING", 2: "EXCHANGE"}.get(
            cast("int", margin_mode_raw), str(margin_mode_raw)
        )
        if margin_mode_raw is not None
        else "HEDGING"
    )
    margin_mode_desc = (
        {
            0: "Netting position accounting",
            1: "Hedging position accounting",
            2: "Exchange position accounting",
        }.get(cast("int", margin_mode_raw), "Unknown")
        if margin_mode_raw is not None
        else "Hedging position accounting"
    )

    credit = Decimal(str(_optional(value, "credit") or 0))
    profit = Decimal(str(_optional(value, "profit") or 0))
    leverage = _optional(value, "leverage") or 100
    trade_allowed = _optional(value, "trade_allowed")
    trade_expert = _optional(value, "trade_expert")
    limit_orders = _optional(value, "limit_orders") or 0
    margin_so_level = (
        _optional(value, "margin_so_call") or _optional(value, "margin_so_so") or 0.0
    )

    margin_level = float((equity / margin) * Decimal(100)) if margin > 0 else None

    details: dict[str, object] = {
        "login": str(_field(value, "login")),
        "name": str(_optional(value, "name") or "N/A"),
        "server": str(_optional(value, "server") or "N/A"),
        "company": str(_optional(value, "company") or "N/A"),
        "leverage": leverage,
        "trade_mode": trade_mode_str,
        "trade_mode_description": trade_mode_desc,
        "margin_mode": margin_mode_str,
        "margin_mode_description": margin_mode_desc,
        "trade_allowed": trade_allowed if trade_allowed is not None else True,
        "trade_expert": trade_expert if trade_expert is not None else True,
        "limit_orders": limit_orders,
        "credit": float(credit),
        "profit": float(profit),
        "margin_so_level": float(margin_so_level),
        "margin_level": margin_level,
    }

    return BrokerAccountInfo(
        account_id=str(_field(value, "login")),
        retrieved_at=datetime.now(UTC),
        account_reference_redacted="***",
        currency=currency,
        balance=balance,
        equity=equity,
        margin=margin,
        free_margin=free_margin,
        details=details,
    )


def _map_position(value: object) -> BrokerPosition:
    """Map direct MT5 position state.

    Args:
        value: Value supplied to the operation.

    Returns:
        Canonical open-position information.
    """
    position_type = int(_field(value, "type"))
    side = (
        "LONG" if position_type == 0 else "SHORT" if position_type == 1 else "UNKNOWN"
    )
    magic = _optional(value, "magic")
    sl_raw = _optional(value, "sl")
    tp_raw = _optional(value, "tp")
    stop_loss = (
        Decimal(str(sl_raw)) if sl_raw is not None and float(sl_raw) > 0 else None
    )
    take_profit = (
        Decimal(str(tp_raw)) if tp_raw is not None and float(tp_raw) > 0 else None
    )
    return BrokerPosition(
        position_id=str(_field(value, "ticket")),
        symbol=str(_field(value, "symbol")),
        side=cast("Any", side),
        quantity=Decimal(str(_field(value, "volume"))),
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        state="OPEN",
        ownership_ref=f"mt5-magic:{int(magic)}" if magic is not None else None,
        open_price=Decimal(str(_field(value, "price_open"))),
        current_price=Decimal(str(_field(value, "price_current"))),
        profit=Decimal(str(_field(value, "profit"))),
        stop_loss=stop_loss,
        take_profit=take_profit,
        provider_timestamp=_time(value, "time_update"),
    )


def _map_permissions(account: object, terminal: object) -> BrokerPermissions:
    """Map only permission fields reported by the terminal and account.

    Args:
        account: Value supplied to the operation.
        terminal: Value supplied to the operation.

    Returns:
        Canonical provider-reported permissions.
    """
    account_trade = _optional(account, "trade_allowed")
    if account_trade is None and account is not None:
        account_trade = True
    terminal_trade = _optional(terminal, "trade_allowed")
    if terminal_trade is None and account is not None:
        terminal_trade = True
    connected = _optional(terminal, "connected")
    if connected is None and account is not None:
        connected = True
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

    Args:
        value: Value supplied to the operation.

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

    Args:
        type_code: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.

    Returns:
        Canonical explicit mutation outcome.
    """
    retcode = int(_field(value, "retcode"))
    accepted = retcode in {10008, 10009, 10025}
    partial = retcode == 10010
    order = _optional(value, "order")
    deal = _optional(value, "deal")
    pending_acknowledgement = accepted and not deal
    reported_volume = _optional(value, "volume")
    volume = Decimal(str(reported_volume)) if reported_volume is not None else None
    order_id = str(order or deal) if accepted or partial else None
    return BrokerOrderResult(
        acknowledged=True,
        outcome="PARTIAL" if partial else ("ACCEPTED" if accepted else "REJECTED"),
        retrieved_at=datetime.now(UTC),
        order_id=order_id,
        deal_ids=(str(deal),) if deal else (),
        filled_quantity=Decimal(0) if pending_acknowledgement else volume,
        remaining_quantity=volume
        if pending_acknowledgement
        else Decimal(0)
        if retcode == 10009 and volume is not None
        else None,
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

    Args:
        retcode: Value supplied to the operation.

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
