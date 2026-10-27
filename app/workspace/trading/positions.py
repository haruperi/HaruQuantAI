"""Shared position selection and collection queries."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.include import contracts

from .account import AccountProxy
from .base import TradeFilter, TradingClass, aware_timestamp, bars_since, pip_size
from .symbol import SymbolProxy

logger = get_logger(__name__)


class PositionProxy(TradingClass):
    """Canonical asynchronous PositionInfo API proxy."""

    CLASS_NAME = "PositionInfo"

    def __init__(
        self,
        backend: contracts.TradingBackend,
        *,
        object_id: str | None = None,
        symbol: SymbolProxy | None = None,
        account: AccountProxy | None = None,
    ) -> None:
        super().__init__(backend, object_id=object_id)
        self._symbol = symbol if symbol is not None else SymbolProxy(backend)
        self._account = account if account is not None else AccountProxy(backend)

    async def PositionInfo(self, *args: Any) -> contracts.PositionInfo:
        """Await the backend PositionInfo snapshot."""
        logger.debug("FR-TRADING-POSITIONS: querying position snapshot")
        return await self._snapshot(
            "PositionInfo", contracts.PositionInfo, "position info", *args
        )

    async def __call__(self, *args: Any) -> contracts.PositionInfo:
        """Await the backend PositionInfo snapshot directly via call syntax."""
        return await self.PositionInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend position snapshot represented as a dictionary."""
        return await self._snapshot_dict(contracts.PositionInfo, "position", *args)

    async def Select(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def SelectByMagic(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByMagic operation."""
        return await self._call("SelectByMagic", *args)

    async def SelectByTicket(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByTicket operation."""
        return await self._call("SelectByTicket", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def PositionsTotal(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PositionsTotal operation."""
        return await self._call("PositionsTotal", *args)

    async def PositionsGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.PositionInfo]:
        """Await the backend PositionInfo.PositionsGet operation."""
        logger.debug("FR-TRADING-POSITIONS: querying positions collection")
        return await self._collection(
            "PositionsGet", contracts.PositionInfo, *args, **kwargs
        )

    async def _matching(self, scope: TradeFilter) -> list[contracts.PositionInfo]:
        return [
            replace(position)
            for position in await self.PositionsGet()
            if scope.matches(position)
        ]

    async def market_position(self, scope: TradeFilter) -> int:
        """Return first matching direction: 1 long, -1 short, or 0 flat."""
        positions = await self._matching(scope)
        return (1 if positions[0].position_type == 0 else -1) if positions else 0

    async def market_position_is_flat(self, scope: TradeFilter) -> bool:
        """Return whether no matching market position exists."""
        return not await self._matching(scope)

    async def market_position_is_long(self, scope: TradeFilter) -> bool:
        """Return whether any matching position is long, including hedged accounts."""
        return any(
            position.position_type == 0 for position in await self._matching(scope)
        )

    async def market_position_is_short(self, scope: TradeFilter) -> bool:
        """Return whether any matching position is short, including hedged accounts."""
        return any(
            position.position_type == 1 for position in await self._matching(scope)
        )

    async def market_position_is_not_long(self, scope: TradeFilter) -> bool:
        """Return whether no matching long position exists."""
        return not await self.market_position_is_long(scope)

    async def market_position_is_not_short(self, scope: TradeFilter) -> bool:
        """Return whether no matching short position exists."""
        return not await self.market_position_is_short(scope)

    async def market_positions_count(self, scope: TradeFilter) -> int:
        """Count matching market positions, excluding pending orders."""
        return len(await self._matching(scope))

    async def market_position_size(self, scope: TradeFilter) -> float:
        """Sum matching position volumes without netting opposing directions."""
        return sum(position.volume for position in await self._matching(scope))

    async def _position_value(self, scope: TradeFilter, field: str) -> float:
        positions = await self._matching(scope)
        return float(getattr(positions[0], field)) if positions else -1.0

    async def order_open_price(self, scope: TradeFilter) -> float:
        """Return the first matching position entry price, or -1 when absent."""
        return await self._position_value(scope, "price_open")

    async def order_sl(self, scope: TradeFilter) -> float:
        """Return the first matching position stop loss, or -1 when absent."""
        return await self._position_value(scope, "sl")

    async def order_pt(self, scope: TradeFilter) -> float:
        """Return the first matching position target, or -1 when absent."""
        return await self._position_value(scope, "tp")

    @staticmethod
    def _valuation(
        position: contracts.PositionInfo, prices: Mapping[str, float] | None
    ) -> float:
        value = position.price_current if prices is None else prices[position.symbol]
        if not math.isfinite(value) or value <= 0:
            raise ValueError("valuation prices must be finite and positive")
        return value

    async def open_pl_in_money(
        self, scope: TradeFilter, *, prices: Mapping[str, float] | None = None
    ) -> float:
        """Sum net open P/L, optionally valuing at explicit strategy decision prices.

        Supplied prices must cover every matched symbol. No position is mutated.
        """
        total = 0.0
        for position in await self._matching(scope):
            gross = position.profit
            if prices is not None:
                gross = float(
                    await self._account.OrderProfitCheck(
                        position.symbol,
                        position.position_type,
                        position.volume,
                        position.price_open,
                        self._valuation(position, prices),
                    )
                )
            total += gross + position.swap + position.commission
        return total

    async def open_pl_in_pips(
        self, scope: TradeFilter, *, prices: Mapping[str, float] | None = None
    ) -> float:
        """Sum directional pip changes per position, without volume weighting."""
        total = 0.0
        for position in await self._matching(scope):
            spec = await self._symbol.SymbolInfo(position.symbol)
            size = pip_size(spec.price.pip_size, spec.price.tick_size)
            direction = 1 if position.position_type == 0 else -1
            total += (
                direction
                * (self._valuation(position, prices) - position.price_open)
                / size
            )
        return total

    async def bars_since_order_open(
        self, scope: TradeFilter, bar_times: Sequence[datetime], *, as_of: datetime
    ) -> int:
        """Count bar starts since first matching entry; return -1 when absent."""
        end = aware_timestamp(as_of)
        positions = await self._matching(scope)
        if not positions:
            return -1
        position = positions[0]
        timestamp = (
            position.time_msc / 1000 if position.time_msc else float(position.time)
        )
        return bars_since(timestamp, bar_times, as_of) if timestamp <= end else -1
