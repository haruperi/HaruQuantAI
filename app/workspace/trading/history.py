"""Shared historical order and deal queries."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.include import contracts
from app.include.enums import DealEntry, DealType

from .base import TradeFilter, TradingClass, aware_timestamp, bars_since, pip_size
from .symbol import SymbolProxy

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    """A fully closed position lifecycle reconstructed from its execution deals."""

    position_id: int
    symbol: str
    direction: int
    magic: int
    comment: str
    volume: float
    price_open: float
    price_close: float
    time_open_msc: int
    time_close_msc: int
    closing_deal: int
    profit: float
    commission: float
    swap: float
    fee: float

    @property
    def net_profit(self) -> float:
        """Return reported realized profit including entry/exit fees and carry."""
        return self.profit + self.commission + self.swap + self.fee

    def matches(self, scope: TradeFilter) -> bool:
        """Use opening identity; ticket filters identify the position lifecycle."""
        return scope.matches(
            contracts.PositionInfo(
                ticket=self.position_id,
                symbol=self.symbol,
                position_type=0 if self.direction == 1 else 1,
                magic=self.magic,
                comment=self.comment,
            )
        )


@dataclass
class _Cycle:
    first: contracts.DealInfo
    balance: float = 0.0
    volume_in: float = 0.0
    cost_in: float = 0.0
    volume_out: float = 0.0
    cost_out: float = 0.0
    profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    fee: float = 0.0

    def add(self, deal: contracts.DealInfo) -> None:
        if deal.magic != self.first.magic or deal.deal_type != self.first.deal_type:
            raise contracts.BridgeError(
                "Mixed ownership or direction in netted history",
                code="AMBIGUOUS_HISTORY",
            )
        self.balance += deal.volume
        self.volume_in += deal.volume
        self.cost_in += deal.volume * deal.price
        self.commission += deal.commission
        self.swap += deal.swap
        self.fee += deal.fee

    def close(self, deal: contracts.DealInfo, volume: float, fraction: float) -> None:
        if volume > self.balance and not math.isclose(
            volume, self.balance, abs_tol=1e-9
        ):
            raise contracts.BridgeError(
                "Closing volume exceeds known entries", code="INCOMPLETE_HISTORY"
            )
        if deal.deal_type == self.first.deal_type:
            raise contracts.BridgeError(
                "Closing direction conflicts with entries", code="INCOMPLETE_HISTORY"
            )
        self.balance -= volume
        self.volume_out += volume
        self.cost_out += volume * deal.price
        self.profit += deal.profit
        self.commission += deal.commission * fraction
        self.swap += deal.swap
        self.fee += deal.fee * fraction

    def finish(self, deal: contracts.DealInfo) -> ClosedTrade:
        return ClosedTrade(
            position_id=self.first.position_id,
            symbol=self.first.symbol,
            direction=1 if self.first.deal_type == int(DealType.BUY) else -1,
            magic=self.first.magic,
            comment=self.first.comment,
            volume=self.volume_in,
            price_open=self.cost_in / self.volume_in,
            price_close=self.cost_out / self.volume_out,
            time_open_msc=_deal_time(self.first),
            time_close_msc=_deal_time(deal),
            closing_deal=deal.ticket,
            profit=self.profit,
            commission=self.commission,
            swap=self.swap,
            fee=self.fee,
        )


def _deal_time(deal: contracts.DealInfo) -> int:
    return deal.time_msc or deal.time * 1000


def _validate_deal(deal: contracts.DealInfo) -> None:
    if deal.position_id <= 0 or not math.isfinite(deal.volume) or deal.volume <= 0:
        raise contracts.BridgeError(
            "Invalid execution identity or volume", code="INCOMPLETE_HISTORY"
        )
    if (
        not math.isfinite(deal.price)
        or deal.price <= 0
        or any(
            not math.isfinite(value)
            for value in (deal.profit, deal.commission, deal.swap, deal.fee)
        )
    ):
        raise contracts.BridgeError(
            "Invalid execution price or P/L", code="INCOMPLETE_HISTORY"
        )


def _completed_trades(deals: list[contracts.DealInfo]) -> list[ClosedTrade]:
    cycles: dict[tuple[str, int], _Cycle] = {}
    completed = []
    seen = set()
    for deal in sorted(deals, key=lambda item: (_deal_time(item), item.ticket)):
        if deal.deal_type not in (int(DealType.BUY), int(DealType.SELL)):
            continue
        if deal.ticket in seen:
            raise contracts.BridgeError(
                "Duplicate execution deal", code="INCOMPLETE_HISTORY"
            )
        seen.add(deal.ticket)
        _validate_deal(deal)
        key = (deal.symbol, deal.position_id)
        if deal.entry == int(DealEntry.IN):
            cycles.setdefault(key, _Cycle(deal)).add(deal)
            continue
        cycle = cycles.get(key)
        if cycle is None:
            raise contracts.BridgeError(
                "Closing deal has no known entry", code="INCOMPLETE_HISTORY"
            )
        if deal.entry not in (
            int(DealEntry.OUT),
            int(DealEntry.OUT_BY),
            int(DealEntry.INOUT),
        ):
            raise contracts.BridgeError(
                "Unknown execution entry type", code="INCOMPLETE_HISTORY"
            )
        volume = (
            min(cycle.balance, deal.volume)
            if deal.entry == int(DealEntry.INOUT)
            else deal.volume
        )
        fraction = volume / deal.volume
        cycle.close(deal, volume, fraction)
        if math.isclose(cycle.balance, 0.0, abs_tol=1e-9):
            completed.append(cycle.finish(deal))
            del cycles[key]
        remaining = deal.volume - volume
        if remaining > 0 and deal.entry == int(DealEntry.INOUT):
            opening = replace(
                deal,
                volume=remaining,
                entry=int(DealEntry.IN),
                profit=0.0,
                swap=0.0,
                commission=deal.commission * (1 - fraction),
                fee=deal.fee * (1 - fraction),
            )
            cycles[key] = _Cycle(opening)
            cycles[key].add(opening)
    return sorted(
        completed, key=lambda trade: (trade.time_close_msc, trade.closing_deal)
    )


class HistoryOrderProxy(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API proxy."""

    CLASS_NAME = "HistoryOrderInfo"

    def __init__(
        self,
        backend: contracts.TradingBackend,
        *,
        object_id: str | None = None,
        deal: DealProxy | None = None,
        symbol: SymbolProxy | None = None,
    ) -> None:
        super().__init__(backend, object_id=object_id)
        self._deal = deal if deal is not None else DealProxy(backend)
        self._symbol = symbol if symbol is not None else SymbolProxy(backend)

    async def HistoryOrderInfo(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend HistoryOrderInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying history order snapshot")
        return await self._snapshot(
            "HistoryOrderInfo", contracts.OrderInfo, "history order info", *args
        )

    async def __call__(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend HistoryOrderInfo snapshot directly via call syntax."""
        return await self.HistoryOrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical order snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.OrderInfo, "history order", *args)

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryOrdersTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend HistoryOrderInfo.HistoryOrdersTotal operation."""
        if kwargs:
            return await self._call("HistoryOrdersTotal", kwargs)
        return await self._call("HistoryOrdersTotal", *args)

    async def HistoryOrdersGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.OrderInfo]:
        """Await the backend HistoryOrderInfo.HistoryOrdersGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history orders collection")
        return await self._collection(
            "HistoryOrdersGet", contracts.OrderInfo, *args, **kwargs
        )

    async def closed_trades(
        self, scope: TradeFilter, *, as_of: datetime | None = None
    ) -> list[ClosedTrade]:
        """Return completed lifecycles oldest first, bounded by evaluation time.

        Partial closes accumulate in a lifecycle until the position is flat.
        Reversals end one lifecycle and start another. Missing entries fail explicitly.
        """
        limit = aware_timestamp(as_of) * 1000 if as_of is not None else None
        deals = [
            deal
            for deal in await self._deal.HistoryDealsGet()
            if (scope.symbol is None or deal.symbol == scope.symbol)
            and (scope.ticket is None or deal.position_id == scope.ticket)
            and (limit is None or _deal_time(deal) <= limit)
        ]
        return [trade for trade in _completed_trades(deals) if trade.matches(scope)]

    async def _last_trade(
        self, scope: TradeFilter, trades_ago: int, as_of: datetime | None
    ) -> ClosedTrade | None:
        if type(trades_ago) is not int or trades_ago < 0:
            raise ValueError("trades_ago must be a nonnegative integer")
        trades = await self.closed_trades(scope, as_of=as_of)
        return trades[-1 - trades_ago] if trades_ago < len(trades) else None

    async def closed_pl_in_money(
        self, scope: TradeFilter, *, trades_ago: int = 0, as_of: datetime | None = None
    ) -> float:
        """Return net P/L for the selected completed trade, or zero when absent."""
        trade = await self._last_trade(scope, trades_ago, as_of)
        return trade.net_profit if trade is not None else 0.0

    async def closed_pl_in_pips(
        self, scope: TradeFilter, *, trades_ago: int = 0, as_of: datetime | None = None
    ) -> float:
        """Return directional weighted price change in pips, or zero when absent."""
        trade = await self._last_trade(scope, trades_ago, as_of)
        if trade is None:
            return 0.0
        spec = await self._symbol.SymbolInfo(trade.symbol)
        size = pip_size(spec.price.pip_size, spec.price.tick_size)
        return trade.direction * (trade.price_close - trade.price_open) / size

    async def last_order_was(
        self, scope: TradeFilter, direction: int, *, as_of: datetime | None = None
    ) -> bool:
        """Test last completed entry direction; pending cancellations are excluded."""
        if type(direction) is not int or direction not in (-1, 1):
            raise ValueError("direction must be 1 or -1")
        trade = await self._last_trade(replace(scope, direction=0), 0, as_of)
        return trade is not None and trade.direction == direction

    async def last_order_was_not(
        self, scope: TradeFilter, direction: int, *, as_of: datetime | None = None
    ) -> bool:
        """Test opposite last entry direction; false when no completed trade exists."""
        if type(direction) is not int or direction not in (-1, 1):
            raise ValueError("direction must be 1 or -1")
        trade = await self._last_trade(replace(scope, direction=0), 0, as_of)
        return trade is not None and trade.direction != direction

    async def bars_since_order_closed(
        self, scope: TradeFilter, bar_times: Sequence[datetime], *, as_of: datetime
    ) -> int:
        """Count chart bar starts since latest matching completion, or -1 if absent."""
        trade = await self._last_trade(scope, 0, as_of)
        return (
            bars_since(trade.time_close_msc / 1000, bar_times, as_of) if trade else -1
        )

    async def trade_recently_closed(
        self,
        scope: TradeFilter,
        *,
        as_of: datetime,
        bar_start: datetime | None = None,
        check_this_bar: bool = True,
        check_this_minute: bool = True,
    ) -> bool:
        """Test a recent completion without consuming the matching event."""
        end = aware_timestamp(as_of)
        starts = []
        if check_this_bar:
            if bar_start is None:
                raise ValueError("bar_start is required when checking this bar")
            start = aware_timestamp(bar_start)
            if start > end:
                raise ValueError("bar_start must not exceed evaluation time")
            starts.append(start)
        if check_this_minute:
            starts.append(end - end % 60)
        if not starts:
            return False
        return any(
            min(starts) <= trade.time_close_msc / 1000 <= end
            for trade in await self.closed_trades(scope, as_of=as_of)
        )

    async def no_trade_recently_closed(
        self,
        scope: TradeFilter,
        *,
        as_of: datetime,
        bar_start: datetime | None = None,
        check_this_bar: bool = True,
        check_this_minute: bool = True,
    ) -> bool:
        """Return the complement of the stable recent-completion predicate."""
        return not await self.trade_recently_closed(
            scope,
            as_of=as_of,
            bar_start=bar_start,
            check_this_bar=check_this_bar,
            check_this_minute=check_this_minute,
        )


class DealProxy(TradingClass):
    """Canonical asynchronous DealInfo API proxy."""

    CLASS_NAME = "DealInfo"

    async def DealInfo(self, *args: Any) -> contracts.DealInfo:
        """Await the backend DealInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying deal snapshot")
        return await self._snapshot("DealInfo", contracts.DealInfo, "deal info", *args)

    async def __call__(self, *args: Any) -> contracts.DealInfo:
        """Await the backend DealInfo snapshot directly via call syntax."""
        return await self.DealInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical deal snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.DealInfo, "deal", *args)

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend DealInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend DealInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryDealsTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend DealInfo.HistoryDealsTotal operation."""
        if kwargs:
            return await self._call("HistoryDealsTotal", kwargs)
        return await self._call("HistoryDealsTotal", *args)

    async def HistoryDealsGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.DealInfo]:
        """Await the backend DealInfo.HistoryDealsGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history deals collection")
        return await self._collection(
            "HistoryDealsGet", contracts.DealInfo, *args, **kwargs
        )
