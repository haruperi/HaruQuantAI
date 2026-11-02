"""Shared execution-history reconstruction for strategy state blocks.

Description:
    Provides deterministic reconstruction of closed trade lifecycles from raw
    broker execution deals (IN, OUT, OUT_BY, INOUT), computing realized
    profit/loss, volume, open/close prices, and elapsed bar timing.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-HISTORY: Execution history cycle matching and trade
      reconstruction.
Python API Usage:
    from app.extend.blocks.strategy_control.history import (
        ClosedTrade,
        closed_trades,
        last_trade,
    )
    trades = await closed_trades(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime

from app.core.data import contracts
from app.core.enums import DealEntry, DealType
from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.functions.order_functions import TradeFilter, aware_timestamp

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
    completed: list[ClosedTrade] = []
    seen: set[int] = set()
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


async def closed_trades(
    context: TradingRuntime, scope: TradeFilter, *, as_of: datetime | None = None
) -> list[ClosedTrade]:
    """Return completed lifecycles oldest first, bounded by evaluation time.

    Partial closes accumulate in a lifecycle until the position is flat.
    Reversals end one lifecycle and start another. Missing entries fail explicitly.
    """
    logger.debug("FR-STRATEGY-CONTROL-HISTORY: Reconstructing closed trades")
    limit = aware_timestamp(as_of) * 1000 if as_of is not None else None
    deals = [
        deal
        for deal in await context.deal.HistoryDealsGet()
        if (scope.symbol is None or deal.symbol == scope.symbol)
        and (scope.ticket is None or deal.position_id == scope.ticket)
        and (limit is None or _deal_time(deal) <= limit)
    ]
    return [trade for trade in _completed_trades(deals) if trade.matches(scope)]


async def last_trade(
    context: TradingRuntime, scope: TradeFilter, trades_ago: int, as_of: datetime | None
) -> ClosedTrade | None:
    """Select one completed lifecycle by reverse chronological offset."""
    logger.debug(
        "FR-STRATEGY-CONTROL-HISTORY: Fetching last trade offset=%d",
        trades_ago,
    )
    if type(trades_ago) is not int or trades_ago < 0:
        raise ValueError("trades_ago must be a nonnegative integer")
    trades = await closed_trades(context, scope, as_of=as_of)
    return trades[-1 - trades_ago] if trades_ago < len(trades) else None


__all__ = ["ClosedTrade", "closed_trades", "last_trade"]
