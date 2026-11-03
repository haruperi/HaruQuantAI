"""Trade request and order parameters validation helpers for simulation."""

from __future__ import annotations

from typing import Any

from app.core.data.contracts import MarketTick, SymbolInfo
from app.core.enums import OrderType, TradeAction, TradeRetcode
from app.core.trading.connection.contracts import TradeRequest, TradeResult

_A = TradeAction
_OT = OrderType
_BUY_TYPES = {_OT.BUY, _OT.BUY_LIMIT, _OT.BUY_STOP, _OT.BUY_STOP_LIMIT}
_SELL_TYPES = {_OT.SELL, _OT.SELL_LIMIT, _OT.SELL_STOP, _OT.SELL_STOP_LIMIT}


def label(member: Any) -> str:
    """Format enum member name to Title Case label."""
    return str(member.name).replace("_", " ").title()


def make_trade_result(
    code: TradeRetcode | int, comment: str = "", **kw: Any
) -> TradeResult:
    """Build TradeResult with coerced retcode."""
    return TradeResult(retcode=int(code), comment=comment, **kw)


def pending_price_valid(
    req: TradeRequest, spec: SymbolInfo, tick: MarketTick | None
) -> bool:
    """Validate pending order trigger price and stop limit bounds."""
    if req.action not in {_A.PENDING, _A.MODIFY}:
        return True
    if tick is None:
        return False
    m, p, ot = (
        spec.trade.stops_level * spec.price.tick_size,
        req.price,
        req.order_type,
    )
    if ot == _OT.BUY_LIMIT:
        return p <= tick.ask - m + 1e-12
    if ot == _OT.SELL_LIMIT:
        return p >= tick.bid + m - 1e-12
    if ot == _OT.BUY_STOP:
        return p >= tick.ask + m - 1e-12
    if ot == _OT.SELL_STOP:
        return p <= tick.bid - m + 1e-12
    if ot == _OT.BUY_STOP_LIMIT:
        return p >= tick.ask + m - 1e-12 and 0 < req.stoplimit <= p + 1e-12
    if ot == _OT.SELL_STOP_LIMIT:
        return p <= tick.bid - m + 1e-12 and req.stoplimit >= max(1e-12, p - 1e-12)
    return False


def volume_valid(spec: SymbolInfo, volume: float) -> bool:
    """Validate requested volume against minimum, maximum, and step constraints."""
    if volume < spec.volume.min - 1e-12 or volume > spec.volume.max + 1e-12:
        return False
    n = (volume - spec.volume.min) / max(spec.volume.step, 1e-12)
    return abs(n - round(n)) <= 1e-7


def stops_valid(req: TradeRequest, spec: SymbolInfo, tick: MarketTick | None) -> bool:
    """Validate stop loss and take profit distances against broker stop levels."""
    m = spec.trade.stops_level * spec.price.tick_size
    if m <= 0 or tick is None:
        return True
    if req.action == _A.DEAL:
        entry = tick.ask if req.order_type == _OT.BUY else tick.bid
    elif req.action in {_A.PENDING, _A.MODIFY}:
        entry = req.price
    else:
        return True
    if req.order_type not in _BUY_TYPES | _SELL_TYPES:
        return True
    is_b = req.order_type in _BUY_TYPES
    d_sl = (entry - req.sl) if is_b else (req.sl - entry)
    d_tp = (req.tp - entry) if is_b else (entry - req.tp)
    return not ((req.sl and d_sl < m - 1e-12) or (req.tp and d_tp < m - 1e-12))
