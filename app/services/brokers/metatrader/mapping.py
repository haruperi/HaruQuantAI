"""MetaTrader provider payload to canonical DTO mapping."""

# ruff: noqa: ANN401, PLR2004 - SDK records and native retcodes are provider-defined.
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.brokers.canonical_contracts import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerBalance,
    BrokerBar,
    BrokerDeal,
    BrokerEnvironment,
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

type Clock = Callable[[], datetime]


def _live_clock() -> datetime:
    """Return the current aware UTC observation time.

    Returns:
        Current aware UTC datetime.
    """
    return datetime.now(UTC)


def _observation_time(clock: Clock) -> datetime:
    """Capture and validate one observation-owned timestamp.

    Args:
        clock: Injected clock called exactly once for one provider payload.

    Returns:
        Aware zero-offset UTC observation time.

    Raises:
        ValueError: If the clock returns a naive or non-UTC datetime.
        TypeError: If the clock does not return a datetime.
    """
    moment = clock()
    if not isinstance(moment, datetime):
        raise TypeError("mapping clock must return datetime")
    if moment.tzinfo is None or moment.utcoffset() != timedelta(0):
        raise ValueError("mapping clock must return aware UTC")
    return moment


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

    Raises:
        ValueError: If required provider facts are missing or invalid.
    """
    symbol = str(_field(value, "name"))
    digits = int(_field(value, "digits"))

    raw_dict: dict[str, object] = {}
    asdict_fn = getattr(value, "_asdict", None)
    if asdict_fn is not None:
        raw_dict = dict(asdict_fn())
    elif isinstance(value, dict):
        raw_dict = dict(value)

    trade_mode_raw = _field(value, "trade_mode")
    trade_mode_str = (
        {
            0: "DISABLED",
            1: "LONGONLY",
            2: "SHORTONLY",
            3: "CLOSEONLY",
            4: "FULL",
        }.get(cast("int", trade_mode_raw), str(trade_mode_raw))
        if trade_mode_raw is not None
        else str(trade_mode_raw)
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
        else "Unknown"
    )

    swap_mode_raw = _field(value, "swap_mode")
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
        else str(swap_mode_raw)
    )

    point = float(_field(value, "point"))
    tick_size = float(_field(value, "trade_tick_size"))
    contract_size = float(_field(value, "trade_contract_size"))
    if point <= 0 or tick_size <= 0 or contract_size <= 0:
        raise ValueError("MT5 symbol point, tick size, and contract size are required")

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
            "swap_long": float(_field(value, "swap_long")),
            "swap_short": float(_field(value, "swap_short")),
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


def _map_quote(
    value: object, symbol: str, *, clock: Clock = _live_clock
) -> BrokerQuote:
    """Map only genuine MT5 quote fields.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        retrieved_at=_observation_time(clock),
        bid=bid or None,
        ask=ask or None,
        last_price=last or None,
        provider_timestamp=_time(value),
    )


def _map_tick(value: object, symbol: str, *, clock: Clock = _live_clock) -> BrokerTick:
    """Map map tick.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        provider_receipt_timestamp=_observation_time(clock),
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


def _map_account(value: object, *, clock: Clock = _live_clock) -> BrokerAccountInfo:
    """Map direct MT5 account state.

    Args:
        value: Value supplied to the operation.
        clock: Observation clock called once for this payload.

    Returns:
        Canonical account information.

    Raises:
        ValueError: If required provider facts are missing or invalid.
    """
    currency = str(_field(value, "currency"))
    balance = Decimal(str(_field(value, "balance")))
    equity = Decimal(str(_field(value, "equity")))
    margin = Decimal(str(_field(value, "margin")))
    free_margin = Decimal(str(_field(value, "margin_free")))

    trade_mode_raw = _field(value, "trade_mode")
    trade_mode_str = (
        {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(
            cast("int", trade_mode_raw), str(trade_mode_raw)
        )
        if trade_mode_raw is not None
        else str(trade_mode_raw)
    )
    trade_mode_desc = (
        {0: "Demo account", 1: "Contest account", 2: "Real account"}.get(
            cast("int", trade_mode_raw), "Unknown"
        )
        if trade_mode_raw is not None
        else "Unknown"
    )

    margin_mode_raw = _field(value, "margin_mode")
    margin_mode_str = (
        {0: "NETTING", 1: "HEDGING", 2: "EXCHANGE"}.get(
            cast("int", margin_mode_raw), str(margin_mode_raw)
        )
        if margin_mode_raw is not None
        else str(margin_mode_raw)
    )
    margin_mode_desc = (
        {
            0: "Netting position accounting",
            1: "Hedging position accounting",
            2: "Exchange position accounting",
        }.get(cast("int", margin_mode_raw), "Unknown")
        if margin_mode_raw is not None
        else "Unknown"
    )

    credit = Decimal(str(_optional(value, "credit") or 0))
    profit = Decimal(str(_optional(value, "profit") or 0))
    leverage = _field(value, "leverage")
    if Decimal(str(leverage)) <= 0:
        raise ValueError("MT5 account leverage is required and must be positive")
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
        retrieved_at=_observation_time(clock),
        account_reference_redacted="***",
        currency=currency,
        balance=balance,
        equity=equity,
        margin=margin,
        free_margin=free_margin,
        details=details,
    )


def _map_position(value: object, *, clock: Clock = _live_clock) -> BrokerPosition:
    """Map direct MT5 position state.

    Args:
        value: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        retrieved_at=_observation_time(clock),
        state="OPEN",
        ownership_ref=f"mt5-magic:{int(magic)}" if magic is not None else None,
        open_price=Decimal(str(_field(value, "price_open"))),
        current_price=Decimal(str(_field(value, "price_current"))),
        profit=Decimal(str(_field(value, "profit"))),
        stop_loss=stop_loss,
        take_profit=take_profit,
        provider_timestamp=_time(value, "time_update"),
    )


def _map_permissions(
    account: object, terminal: object, *, clock: Clock = _live_clock
) -> BrokerPermissions:
    """Map only permission fields reported by the terminal and account.

    Args:
        account: Value supplied to the operation.
        terminal: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        observed_at=_observation_time(clock),
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


def _map_balance(value: object, *, clock: Clock = _live_clock) -> BrokerBalance:
    """Map the MT5 account-currency balance without inventing availability.

    Args:
        value: Value supplied to the operation.
        clock: Observation clock called once for this payload.

    Returns:
        Canonical account-currency balance.
    """
    currency = str(_field(value, "currency"))
    return BrokerBalance(
        asset=currency,
        unit=currency,
        retrieved_at=_observation_time(clock),
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


def _map_order(value: object, *, clock: Clock = _live_clock) -> BrokerOrder:
    """Map one MT5 active or historical order.

    Args:
        value: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        retrieved_at=_observation_time(clock),
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


def _map_deal(value: object, *, clock: Clock = _live_clock) -> BrokerDeal:
    """Map one MT5 execution deal.

    Args:
        value: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        retrieved_at=_observation_time(clock),
        fee=fee or None,
        provider_timestamp=_time(value),
    )


def _map_transaction(
    value: object, currency: str, *, clock: Clock = _live_clock
) -> BrokerAccountTransaction:
    """Map one non-trade MT5 deal as an account transaction.

    Args:
        value: Provider deal payload.
        currency: Verified account currency.
        clock: Observation clock called once for this payload.

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
        retrieved_at=_observation_time(clock),
        provider_metadata={
            "reason": _optional(value, "reason"),
            "native_transaction_type": type_code,
        },
    )


def _map_order_check(
    value: object,
    *,
    environment: BrokerEnvironment | None = None,
    account_digest: str | None = None,
    provider_specification_checksum: str | None = None,
    terminal_build: str | None = None,
    observed_at: datetime | None = None,
) -> BrokerOrderCheck:
    """Map an MT5 pre-submission order check.

    Args:
        value: Value supplied to the operation.
        environment: Bound canonical Broker environment.
        account_digest: Redacted account identity digest.
        provider_specification_checksum: Bound specification checksum.
        terminal_build: Bound provider terminal build.
        observed_at: Aware-UTC specification observation time.

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
        projected_balance=(
            Decimal(str(_optional(value, "balance")))
            if _optional(value, "balance") is not None
            else None
        ),
        projected_equity=(
            Decimal(str(_optional(value, "equity")))
            if _optional(value, "equity") is not None
            else None
        ),
        projected_profit=(
            Decimal(str(_optional(value, "profit")))
            if _optional(value, "profit") is not None
            else None
        ),
        projected_margin=(
            Decimal(str(_optional(value, "margin")))
            if _optional(value, "margin") is not None
            else None
        ),
        projected_free_margin=(
            Decimal(str(_optional(value, "margin_free")))
            if _optional(value, "margin_free") is not None
            else None
        ),
        projected_margin_level=(
            Decimal(str(_optional(value, "margin_level")))
            if _optional(value, "margin_level") is not None
            else None
        ),
        environment=environment,
        account_digest=account_digest,
        provider_specification_checksum=provider_specification_checksum,
        terminal_build=terminal_build,
        observed_at=observed_at,
    )


def _map_order_result(
    value: object, *, clock: Clock = _live_clock
) -> BrokerOrderResult:
    """Map one acknowledged MT5 order-send response.

    Args:
        value: Value supplied to the operation.
        clock: Observation clock called once for this payload.

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
        retrieved_at=_observation_time(clock),
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


def _normalize_decimal_str(val: object) -> str | None:
    """Normalize decimal/float/int/str value to canonical trimmed string.

    Args:
        val: Input value to normalize.

    Returns:
        Normalized decimal string or None.
    """
    if val is None:
        return None
    d = Decimal(str(val))
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    return s


def _format_utc_timestamp(dt: datetime | None) -> str | None:
    """Format aware UTC datetime to ISO8601 string.

    Args:
        dt: Input datetime to format.

    Returns:
        ISO8601 formatted UTC timestamp string or None.
    """
    if dt is None:
        return None
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def map_market_state(
    session_id: str,
    generation: int,
    instrument: Any,
    provider_symbol: str,
    quote: BrokerQuote,
) -> Any:
    """Map canonical quote to BrokerMarketState wire record.

    Args:
        session_id: Active broker session ID.
        generation: Active session generation.
        instrument: Associated instrument reference.
        provider_symbol: Exact provider symbol.
        quote: Resolved canonical quote.

    Returns:
        BrokerMarketState model.
    """
    import uuid

    from app.contracts.broker.models import BrokerMarketState
    from app.contracts.catalogue.models import InstrumentRef

    inst = (
        instrument
        if isinstance(instrument, InstrumentRef)
        else InstrumentRef(instrument_id=str(uuid.uuid7()))
    )
    bid_str = _normalize_decimal_str(quote.bid)
    ask_str = _normalize_decimal_str(quote.ask)
    last_str = bid_str or ask_str
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    event_time_str = (
        _format_utc_timestamp(quote.provider_timestamp)
        if quote.provider_timestamp
        else now_str
    )
    return BrokerMarketState(
        session_id=session_id,
        generation=generation,
        instrument=inst,
        provider_symbol=provider_symbol,
        market_status="OPEN",
        receipt_time=now_str,
        bid=bid_str,
        ask=ask_str,
        last=last_str,
        event_time=event_time_str,
    )


def map_event_market_state(
    session_id: str,
    generation: int,
    raw_event: dict[str, Any],
    instrument: Any | None = None,
) -> Any:
    """Normalize raw MetaTrader event payload to BrokerMarketState.

    Args:
        session_id: Active session ID.
        generation: Active session generation.
        raw_event: Raw provider event dictionary.
        instrument: Optional instrument reference.

    Returns:
        BrokerMarketState model.
    """
    import uuid

    from app.contracts.broker.models import BrokerMarketState
    from app.contracts.catalogue.models import InstrumentRef

    symbol = str(raw_event.get("symbol", raw_event.get("provider_symbol", "EURUSD")))
    inst = (
        instrument
        if isinstance(instrument, InstrumentRef)
        else InstrumentRef(instrument_id=str(uuid.uuid7()))
    )
    bid_str = _normalize_decimal_str(raw_event.get("bid"))
    ask_str = _normalize_decimal_str(raw_event.get("ask"))
    last_str = _normalize_decimal_str(raw_event.get("last")) or bid_str or ask_str
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    return BrokerMarketState(
        session_id=session_id,
        generation=generation,
        instrument=inst,
        provider_symbol=symbol,
        market_status="OPEN",
        receipt_time=now_str,
        bid=bid_str,
        ask=ask_str,
        last=last_str,
        event_time=now_str,
    )


def map_account_snapshot(
    session_id: str,
    generation: int,
    account_ref: str,
    currency: str = "USD",
    equity: Decimal | str | float = "10000",
    balances: dict[str, Decimal | str | float] | None = None,
    margin: Decimal | str | float | None = None,
    free_margin: Decimal | str | float | None = None,
    permissions: tuple[str, ...] = ("READ",),
    provider_time: datetime | None = None,
) -> Any:
    """Map account fields to BrokerAccountSnapshot wire record.

    Args:
        session_id: Active broker session ID.
        generation: Active session generation.
        account_ref: Configured account reference.
        currency: Base account currency.
        equity: Account equity value.
        balances: Currency balance mapping.
        margin: Used margin value.
        free_margin: Available free margin value.
        permissions: Account permission tags.
        provider_time: Timestamp from provider.

    Returns:
        BrokerAccountSnapshot model.
    """
    from app.contracts.broker.models import BrokerAccountSnapshot
    from app.contracts.common.models import Money

    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    eq_norm = _normalize_decimal_str(equity) or "10000"
    b_dict = {
        k: _normalize_decimal_str(v) or "0"
        for k, v in (balances or {currency: eq_norm}).items()
    }
    m_money = (
        Money(amount=_normalize_decimal_str(margin) or "0", currency=currency)
        if margin is not None
        else None
    )
    fm_money = (
        Money(amount=_normalize_decimal_str(free_margin) or eq_norm, currency=currency)
        if free_margin is not None
        else None
    )
    return BrokerAccountSnapshot(
        session_id=session_id,
        generation=generation,
        account_ref=account_ref,
        currency=currency,
        equity=Money(amount=eq_norm, currency=currency),
        retrieved_at=now_str,
        balances=b_dict,
        margin=m_money,
        free_margin=fm_money,
        permissions=permissions,
        provider_time=_format_utc_timestamp(provider_time) if provider_time else None,
    )


def map_trading_state(
    session_id: str,
    generation: int,
    positions: tuple[BrokerPosition, ...] = (),
    orders: tuple[BrokerOrder, ...] = (),
    deals: tuple[BrokerDeal, ...] = (),
    duplicate_or_contradictory: tuple[str, ...] = (),
) -> Any:
    """Map trading entities to BrokerTradingState wire record.

    Args:
        session_id: Active session ID.
        generation: Active session generation.
        positions: Open positions.
        orders: Active or historical orders.
        deals: Execution deals.
        duplicate_or_contradictory: Anomaly tags.

    Returns:
        BrokerTradingState model.
    """
    from app.contracts.broker.models import BrokerTradingState, ProviderRecord

    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    pos_records = tuple(
        ProviderRecord(
            provider_id=p.position_id,
            record={
                "position_id": p.position_id,
                "symbol": p.symbol,
                "side": p.side,
                "quantity": _normalize_decimal_str(p.quantity) or "0",
                "state": p.state,
                "open_price": _normalize_decimal_str(p.open_price),
            },
        )
        for p in positions
    )
    ord_records = tuple(
        ProviderRecord(
            provider_id=o.order_id,
            record={
                "order_id": o.order_id,
                "symbol": o.symbol,
                "side": o.side,
                "order_type": o.order_type,
                "state": o.state,
                "quantity": _normalize_decimal_str(o.quantity) or "0",
                "filled": _normalize_decimal_str(o.filled) or "0",
            },
        )
        for o in orders
    )
    deal_records = tuple(
        ProviderRecord(
            provider_id=d.deal_id,
            record={
                "deal_id": d.deal_id,
                "order_id": d.order_id,
                "position_id": d.position_id,
                "symbol": d.symbol,
                "side": d.side,
                "quantity": _normalize_decimal_str(d.quantity) or "0",
                "price": _normalize_decimal_str(d.price) or "0",
            },
        )
        for d in deals
    )
    return BrokerTradingState(
        session_id=session_id,
        generation=generation,
        retrieved_at=now_str,
        positions=pos_records,
        orders=ord_records,
        deals=deal_records,
        duplicate_or_contradictory=duplicate_or_contradictory,
    )


def map_history_page(
    values: tuple[BrokerBar, ...] | tuple[BrokerTick, ...],
    symbol: str,
    timeframe: str,
    limit: int,
    page_id: str,
    retrieved_at: str | None = None,
    requested_timeframe: str | None = None,
    is_truncated: bool = False,
    cursor: str | None = None,
) -> Any:
    """Map bar/tick sequence to BrokerHistoryPage wire record.

    Args:
        values: Sequence of BrokerBar or BrokerTick.
        symbol: Provider symbol.
        timeframe: Provider timeframe interval.
        limit: Requested page size limit.
        page_id: Unique page ID.
        retrieved_at: Retrieval timestamp string.
        requested_timeframe: Canonical requested timeframe.
        is_truncated: Whether more records are available.
        cursor: Pagination cursor string.

    Returns:
        BrokerHistoryPage model.
    """
    from app.contracts.broker.models import BrokerHistoryPage, ProviderRecord

    del timeframe, requested_timeframe
    now_str = retrieved_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    records: list[ProviderRecord] = []
    for idx, item in enumerate(values):
        if isinstance(item, BrokerBar):
            rec_dict: dict[str, Any] = {
                "symbol": item.symbol,
                "open": _normalize_decimal_str(item.open) or "0",
                "high": _normalize_decimal_str(item.high) or "0",
                "low": _normalize_decimal_str(item.low) or "0",
                "close": _normalize_decimal_str(item.close) or "0",
                "volume": _normalize_decimal_str(item.tick_volume) or "0",
                "opening_timestamp": _format_utc_timestamp(item.opening_timestamp),
                "closing_timestamp": _format_utc_timestamp(item.closing_timestamp),
                "timeframe": item.provider_timeframe,
            }
        elif isinstance(item, BrokerTick):
            rec_dict = {
                "symbol": item.symbol,
                "bid": _normalize_decimal_str(item.bid),
                "ask": _normalize_decimal_str(item.ask),
                "event_timestamp": _format_utc_timestamp(item.event_timestamp),
            }
        else:
            rec_dict = {"symbol": symbol}
        records.append(ProviderRecord(provider_id=f"{symbol}:{idx}", record=rec_dict))
    selected = records[:limit]
    return BrokerHistoryPage(
        page_id=page_id,
        requested_count=limit,
        returned_count=len(selected),
        is_truncated=is_truncated or (len(records) > limit),
        retrieved_at=now_str,
        provider_cursor=cursor,
        records=tuple(selected),
    )
