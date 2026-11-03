"""HSL entry constraints and owned-position management.

Description:
    Applies account risk, session restrictions, and explicit protective management.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Shared strategy policy enforcement.
Key Capabilities:
    - FR-hsl-policies: Log risk decisions and reject missing account evidence.
Python API Usage:
    Called after ordered rule evaluation, before effects are published.
CLI Usage:
    uv run pytest tests/core/trading/strategy --no-cov
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.core.host.logging import get_logger
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    CloseRequest,
    OrderModification,
)
from app.core.trading.strategy.hsl.expressions import event_time, fail
from app.core.trading.strategy.hsl.orders import Orders

logger = get_logger(__name__)
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
FRIDAY = 4
FIRST_PENDING_TYPE = 2


def _minute(value: str | None) -> int:
    """Validate a required HH:MM setting, without assuming a session time."""
    if value is None:
        fail("Enabled time restriction requires an HH:MM boundary")
    try:
        hour, minute = map(int, value.split(":"))
    except ValueError, AttributeError:
        fail("Session times must use HH:MM")
    if not (0 <= hour < HOURS_PER_DAY and 0 <= minute < MINUTES_PER_HOUR):
        fail("Session time is outside the clock range")
    return hour * 60 + minute


def _risk_allowed(orders: Orders, state: dict[str, Any]) -> bool:
    """Check account-backed loss limits."""
    strategy = orders.strategy
    risk = strategy.risk_management
    ex = orders.expressions
    allowed = True
    if risk.max_daily_loss_pct is not None or risk.max_drawdown_pct is not None:
        equity = ex.context.account_equity
        if equity is None or not math.isfinite(equity) or equity < 0:
            fail("Risk limits require an explicit finite equity snapshot")
        initial = state.get("day_equity")
        if initial is None or initial <= 0:
            fail("Daily risk requires a positive session-opening equity snapshot")
        peak = max(float(state.get("peak_equity", equity)), equity)
        state["peak_equity"] = peak
        daily_loss = max(0.0, (initial - equity) / initial * 100.0)
        drawdown = max(0.0, (peak - equity) / peak * 100.0) if peak else 0.0
        allowed = allowed and (
            not (
                (
                    risk.max_daily_loss_pct is not None
                    and daily_loss >= risk.max_daily_loss_pct
                )
                or (
                    risk.max_drawdown_pct is not None
                    and drawdown >= risk.max_drawdown_pct
                )
            )
        )
        logger.debug(
            "FR-hsl-policies: daily_loss=%s drawdown=%s allowed=%s",
            daily_loss,
            drawdown,
            allowed,
        )
    return allowed


def _pending_count(orders: Orders) -> int:
    """Reserve capacity for unexpired owned pending orders, without counting fills."""
    ex = orders.expressions
    return sum(
        order.symbol == ex.event.symbol
        and order.magic in orders.magics
        and str(order.ticket) not in orders.cancels
        and (not order.time_expiration or order.time_expiration > event_time(ex.event))
        for order in ex.context.orders
    )


def _entries(orders: Orders, state: dict[str, Any], *, allowed: bool) -> None:
    """Apply daily, direction, capacity, and pending-entry constraints."""
    strategy = orders.strategy
    risk = strategy.risk_management
    options = strategy.trading_options
    if not allowed:
        orders.entries.clear()
    if options.max_trades_per_day is not None:
        confirmed = orders.expressions.context.entries_today
        if type(confirmed) is not int or confirmed < 0:
            fail(
                "Daily trade limits require a confirmed entry count",
                "HSL_MISSING_TRADE_COUNT",
            )
        state["trades_today"] = confirmed
        remaining = max(
            0, options.max_trades_per_day - confirmed - _pending_count(orders)
        )
        del orders.entries[remaining:]
    fully_closed = {
        str(request.ticket)
        for request in orders.closes
        for position in orders.owned_positions()
        if str(position.ticket) == str(request.ticket)
        and (request.volume is None or request.volume >= position.volume)
    }
    existing = [
        position
        for position in orders.owned_positions()
        if str(position.ticket) not in fully_closed
    ]
    if orders.entries and (not risk.allow_opposite_signals):
        first = orders.entries[0].direction
        existing_directions = {
            1 if position.position_type == 0 else -1 for position in existing
        }
        if existing_directions:
            first = next(iter(existing_directions))
        orders.entries[:] = [
            entry for entry in orders.entries if entry.direction == first
        ]
    pending_count = _pending_count(orders)
    slots = max(0, risk.max_open_positions - len(existing) - pending_count)
    del orders.entries[slots:]
    if orders.entries and options.min_distance_from_market_pips:
        minimum = options.min_distance_from_market_pips * orders.economics().pip_size
        for request in orders.entries:
            if (
                int(request.order_type) >= FIRST_PENDING_TYPE
                and abs(request.price - orders.price(request.direction)) < minimum
            ):
                fail("Pending price violates the minimum distance from market")


def _positions(orders: Orders, state: dict[str, Any], *, close_session: bool) -> None:
    """Manage owned positions and expiring pending orders."""
    strategy = orders.strategy
    management = strategy.trade_management
    ex = orders.expressions
    now = event_time(ex.event)
    for pending in ex.context.orders:
        if (
            pending.magic in orders.magics
            and pending.symbol == ex.event.symbol
            and pending.time_expiration
            and (pending.time_expiration <= now)
        ):
            orders.cancels.append(str(pending.ticket))
    for position in orders.owned_positions():
        direction = 1 if position.position_type == 0 else -1
        price = orders.price(-direction)
        if close_session:
            orders.closes.append(CloseRequest(position.ticket, comment="SESSION"))
            continue
        if management.time_stop_bars is not None:
            if not isinstance(ex.event, BarUpdateEvent):
                fail("Bar-duration exits require a bar event")
            if (
                now - position.time
                >= management.time_stop_bars * ex.event.timeframe.to_seconds()
            ):
                orders.closes.append(CloseRequest(position.ticket, comment="TIME_STOP"))
                continue
        _protect_position(orders, state, position, direction, price)


def _protect_position(
    orders: Orders, state: dict[str, Any], position: Any, direction: int, price: float
) -> None:
    """Apply breakeven, trailing distance, and one-time partial exits."""
    management = orders.strategy.trade_management
    ex = orders.expressions
    if management.breakeven or management.trailing_stop or management.partial_exits:
        econ = orders.economics()
        favorable = (price - position.price_open) * direction / econ.pip_size
        sl = position.sl
        be = management.breakeven
        if be is not None and be.enabled and (favorable >= ex.numeric(be.trigger_pips)):
            candidate = (
                position.price_open
                + direction * ex.numeric(be.lock_pips) * econ.pip_size
            )
            if (candidate - position.price_open) * direction >= 0:
                sl = (
                    candidate
                    if sl == 0
                    else max(sl, candidate)
                    if direction == 1
                    else min(sl, candidate)
                )
        sl = _trailing(orders, direction, price, favorable, sl)
        if sl != position.sl and (price - sl) * direction > 0:
            orders.modifications.append(OrderModification(position.ticket, sl=sl))
        done = state.setdefault("partial_exits", {})
        for index, partial in enumerate(management.partial_exits):
            key = f"{position.ticket}:{index}"
            if key not in done and favorable >= ex.numeric(partial.trigger_pips):
                orders.closes.append(
                    CloseRequest(
                        position.ticket,
                        position.volume * partial.close_pct / 100.0,
                        "PARTIAL",
                    )
                )
                done[key] = True


def apply_policies(orders: Orders, state: dict[str, Any]) -> None:
    """Constrain entries and manage only positions owned by this strategy."""
    strategy = orders.strategy
    options = strategy.trading_options
    ex = orders.expressions
    now = event_time(ex.event)
    local = datetime.fromtimestamp(now, UTC).astimezone(ZoneInfo(options.timezone))
    minute = local.hour * 60 + local.minute
    allowed = True
    if options.limit_time_range:
        start, end = (
            _minute(options.time_range_start),
            _minute(options.time_range_end),
        )
        allowed = (
            start <= minute < end if start < end else minute >= start or minute < end
        )
    close_session = (
        options.exit_at_end_of_day and minute >= _minute(options.end_of_day_time)
    ) or (
        options.exit_on_friday
        and local.weekday() == FRIDAY
        and (minute >= _minute(options.friday_exit_time))
    )
    allowed = allowed and (not close_session)
    allowed = _risk_allowed(orders, state) and allowed
    _entries(orders, state, allowed=allowed)
    _positions(orders, state, close_session=close_session)


def _trailing(
    orders: Orders,
    direction: int,
    price: float,
    favorable: float,
    sl: float,
) -> float:
    """Tighten a trailing stop using a declared pip or absolute-price distance."""
    management = orders.strategy.trade_management
    ex = orders.expressions
    econ = orders.economics()
    trailing = management.trailing_stop
    if trailing is not None and trailing.enabled:
        activation = (
            ex.numeric(trailing.activation_pips) if trailing.activation_pips else 0.0
        )
        if favorable >= activation:
            distance = ex.numeric(trailing.distance)
            if trailing.type == "fixed_pips":
                distance *= econ.pip_size
            if distance <= 0:
                fail("Trailing distance must be positive")
            candidate = price - direction * distance
            sl = (
                candidate
                if sl == 0
                else max(sl, candidate)
                if direction == 1
                else min(sl, candidate)
            )
    return sl
