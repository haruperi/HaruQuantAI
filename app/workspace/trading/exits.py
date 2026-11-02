"""Shared, explicitly driven exit policies for live and simulated positions.

Description:
    Dynamic exit manager evaluating protective StopLoss, ProfitTarget, TrailingStop,
    MoveSL2BE, and ExitAfterBars against open positions.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and dynamic exits.
Key Capabilities:
    - FR-trading-exit-manager: Attach, detach, and evaluate exit rules.
    - FR-trading-exit-brackets: Stop-loss and profit-target bracket maintenance.
    - FR-trading-exit-trailing: Trailing stop and breakeven adjustment.
    - FR-trading-exit-time: Time-based bar count exit trigger.
Python API Usage:
    from app.workspace.trading.exits import (
        ExitManager, ExitPlan, ProfitTarget, StopLoss
    )
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.data.contracts import PositionInfo, SymbolInfo, TradeResult
from app.core.enums import TradeRetcode
from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.order.close.close_position import close_position
from app.extend.blocks.order.modify.set_profit_target import set_profit_target
from app.extend.blocks.order.modify.set_stop_loss import set_stop_loss
from app.extend.functions.order_functions import (
    TradeFilter,
    aware_timestamp,
    bars_since,
)

logger = get_logger(__name__)


def _nonnegative(value: float, label: str, *, positive: bool = False) -> None:
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(
            f"{label} must be finite and {'positive' if positive else 'nonnegative'}"
        )


@dataclass(frozen=True, slots=True)
class StopLoss:
    """An evaluated absolute stop price; existing tighter stops are preserved."""

    price: float

    def __post_init__(self) -> None:
        """Validate the protective price."""
        _nonnegative(self.price, "stop loss", positive=True)


@dataclass(frozen=True, slots=True)
class ProfitTarget:
    """An evaluated absolute profit-target price."""

    price: float

    def __post_init__(self) -> None:
        """Validate the target price."""
        _nonnegative(self.price, "profit target", positive=True)


@dataclass(frozen=True, slots=True)
class MoveSL2BE:
    """Activate after a favorable price move, then protect entry plus an offset.

    Activation and offset are price distances, not pip counts. Offset is added
    for a long and subtracted for a short; it does not estimate trading costs.
    """

    activation: float
    offset: float = 0.0

    def __post_init__(self) -> None:
        """Validate trigger and offset distances."""
        _nonnegative(self.activation, "break-even activation")
        _nonnegative(self.offset, "break-even offset")


@dataclass(frozen=True, slots=True)
class TrailingStop:
    """Track favorable decision prices after activation, without loosening stops."""

    distance: float
    activation: float = 0.0

    def __post_init__(self) -> None:
        """Validate trailing and activation distances in price units."""
        _nonnegative(self.distance, "trailing distance", positive=True)
        _nonnegative(self.activation, "trailing activation")


@dataclass(frozen=True, slots=True)
class ExitAfterBars:
    """Close after this many later chart bar starts; zero disables the policy."""

    bars: int

    def __post_init__(self) -> None:
        """Validate the explicit bar count."""
        if type(self.bars) is not int or self.bars < 0:
            raise ValueError("exit bars must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class ExitPlan:
    """Independent exit configuration attached to one or more filled positions."""

    stop_loss: StopLoss | None = None
    profit_target: ProfitTarget | None = None
    move_sl_to_be: MoveSL2BE | None = None
    trailing_stop: TrailingStop | None = None
    exit_after_bars: ExitAfterBars | None = None


@dataclass(frozen=True, slots=True)
class ExitOutcome:
    """One requested action and its broker result; None means the position vanished."""

    ticket: int
    action: Literal["close", "stop_loss", "profit_target"]
    price: float | None
    result: TradeResult | None


@dataclass
class _Binding:
    identity: tuple[int, int, str, int, int, int]
    plan: ExitPlan
    favorable_price: float | None = None
    break_even_active: bool = False
    trailing_active: bool = False
    last_evaluation: float | None = None
    blocked: bool = False


def _identity(position: PositionInfo) -> tuple[int, int, str, int, int, int]:
    return (
        position.ticket,
        position.identifier,
        position.symbol,
        position.magic,
        position.position_type,
        position.time_msc or position.time * 1000,
    )


class ExitManager:
    """Evaluate attached exits from caller-provided events and delegate to Trade.

    No timers or implicit wall clock are used. State belongs to this manager and
    each position lifecycle; pending orders must first fill before attachment.
    """

    def __init__(self, context: TradingRuntime) -> None:
        self._context = context
        self._position = context.position
        self._symbol = context.symbol
        self._bindings: dict[int, _Binding] = {}
        self._lock = asyncio.Lock()

    @property
    def blocked_tickets(self) -> tuple[int, ...]:
        """Return positions needing caller reconciliation after an execution failure."""
        return tuple(
            ticket for ticket, binding in self._bindings.items() if binding.blocked
        )

    async def attach(self, scope: TradeFilter, plan: ExitPlan) -> list[int]:
        """Attach to filled matches, preserving state when reconfiguring a lifecycle."""
        logger.debug("FR-trading-exit-manager: attaching exit plan")
        async with self._lock:
            tickets = []
            for position in await self._position.PositionsGet():
                if not scope.matches(position):
                    continue
                identity = _identity(position)
                existing = self._bindings.get(position.ticket)
                if existing is not None and existing.identity == identity:
                    existing.plan = plan
                else:
                    self._bindings[position.ticket] = _Binding(identity, plan)
                tickets.append(position.ticket)
            return tickets

    def detach(self, ticket: int) -> None:
        """Remove policy state; already dispatched requests are not cancelled."""
        logger.debug(
            "FR-trading-exit-manager: detaching exit plan",
            extra={"ticket": ticket},
        )
        self._bindings.pop(ticket, None)

    def resume(self, ticket: int) -> None:
        """Allow a later evaluation after the caller has reconciled the position."""
        logger.debug(
            "FR-trading-exit-manager: resuming exit plan",
            extra={"ticket": ticket},
        )
        self._bindings[ticket].blocked = False

    async def evaluate(
        self,
        *,
        as_of: datetime,
        prices: Mapping[str, float] | None = None,
        bar_times: Mapping[str, Sequence[datetime]] | None = None,
        market_open: bool = True,
    ) -> list[ExitOutcome]:
        """Evaluate one explicit event, coalescing actions for each position.

        Supply complete decision-price mappings when using bar-close valuation.
        Bar-count exits require actual chart starts, oldest first and covering entry.
        Repeated timestamps do not repeat requests; backward timestamps are rejected.
        """
        logger.debug("FR-trading-exit-manager: evaluating exits")
        stamp = aware_timestamp(as_of)
        async with self._lock:
            positions = {
                p.ticket: replace(p) for p in await self._position.PositionsGet()
            }
            self._prune(positions)
            if any(
                binding.last_evaluation is not None and stamp < binding.last_evaluation
                for binding in self._bindings.values()
            ):
                raise ValueError("exit evaluation time must not move backward")
            if not market_open:
                return []
            outcomes = []
            for ticket, binding in list(self._bindings.items()):
                if binding.blocked or binding.last_evaluation == stamp:
                    continue
                position = positions[ticket]
                if position.time_msc / 1000 > stamp or (
                    not position.time_msc and position.time > stamp
                ):
                    continue
                outcomes.extend(
                    await self._evaluate_position(
                        position, binding, as_of, prices, bar_times
                    )
                )
            return outcomes

    def _prune(self, positions: dict[int, PositionInfo]) -> None:
        for ticket, binding in list(self._bindings.items()):
            if (
                ticket not in positions
                or _identity(positions[ticket]) != binding.identity
            ):
                del self._bindings[ticket]

    async def _evaluate_position(
        self,
        position: PositionInfo,
        binding: _Binding,
        as_of: datetime,
        prices: Mapping[str, float] | None,
        bar_times: Mapping[str, Sequence[datetime]] | None,
    ) -> list[ExitOutcome]:
        scope = TradeFilter(
            position.symbol,
            magic=position.magic,
            ticket=position.ticket,
            direction=1 if position.position_type == 0 else -1,
        )
        bars = binding.plan.exit_after_bars
        if bars is not None and bars.bars > 0:
            if bar_times is None or position.symbol not in bar_times:
                raise ValueError(
                    "bar-count exits require chart bar times for the position"
                )
            opened = (position.time_msc or position.time * 1000) / 1000
            if bars_since(opened, bar_times[position.symbol], as_of) >= bars.bars:
                logger.debug(
                    "FR-trading-exit-time: triggered exit after bars",
                    extra={"ticket": position.ticket},
                )
                return [await self._close(position, binding, scope, as_of)]
        decision = position.price_current if prices is None else prices[position.symbol]
        _nonnegative(decision, "decision price", positive=True)
        spec = await self._symbol.SymbolInfo(position.symbol)
        staged = replace(binding)
        stop = self._stop_price(position, staged, decision, spec)
        target = binding.plan.profit_target
        target_price = self._rounded(target.price, spec) if target is not None else None
        change_target = (
            target_price is not None
            and not math.isclose(target_price, position.tp, rel_tol=0.0, abs_tol=1e-10)
            and self._valid_level(target_price, position, spec, stop=False)
        )
        binding.favorable_price = staged.favorable_price
        binding.break_even_active = staged.break_even_active
        binding.trailing_active = staged.trailing_active
        binding.last_evaluation = aware_timestamp(as_of)
        outcomes = []
        if stop is not None:
            outcome = await self._protect(position, binding, scope, stop, stop=True)
            outcomes.append(outcome)
            if binding.blocked or outcome.result is None:
                return outcomes
        if change_target and target_price is not None:
            outcomes.append(
                await self._protect(position, binding, scope, target_price, stop=False)
            )
        return outcomes

    async def _close(
        self,
        position: PositionInfo,
        binding: _Binding,
        scope: TradeFilter,
        as_of: datetime,
    ) -> ExitOutcome:
        binding.last_evaluation = aware_timestamp(as_of)
        try:
            result = await close_position(self._context, scope)
            if result is None:
                self._bindings.pop(position.ticket, None)
            elif result.retcode == int(TradeRetcode.DONE):
                remaining = await self._position.PositionsGet()
                if any(_identity(item) == binding.identity for item in remaining):
                    binding.blocked = True
                else:
                    self._bindings.pop(position.ticket, None)
            else:
                binding.blocked = True
        except Exception:
            binding.blocked = True
            raise
        return ExitOutcome(position.ticket, "close", None, result)

    @staticmethod
    def _rounded(price: float, spec: SymbolInfo) -> float:
        _nonnegative(price, "exit price", positive=True)
        _nonnegative(spec.price.tick_step, "tick step", positive=True)
        step = Decimal(str(spec.price.tick_step))
        rounded = float(round(Decimal(str(price)) / step) * step)
        _nonnegative(rounded, "rounded exit price", positive=True)
        return rounded

    def _stop_price(
        self, position: PositionInfo, binding: _Binding, price: float, spec: SymbolInfo
    ) -> float | None:
        direction = 1 if position.position_type == 0 else -1
        favorable = direction * (price - position.price_open)
        prior = binding.favorable_price
        binding.favorable_price = (
            price
            if prior is None
            else (max(prior, price) if direction == 1 else min(prior, price))
        )
        candidates = []
        plan = binding.plan
        if plan.stop_loss is not None:
            candidates.append(plan.stop_loss.price)
        if plan.move_sl_to_be is not None:
            be = plan.move_sl_to_be
            binding.break_even_active |= favorable >= be.activation or math.isclose(
                favorable, be.activation, rel_tol=0.0, abs_tol=1e-12
            )
            if binding.break_even_active:
                logger.debug(
                    "FR-trading-exit-trailing: MoveSL2BE activated",
                    extra={"ticket": position.ticket},
                )
                candidates.append(position.price_open + direction * be.offset)
        if plan.trailing_stop is not None:
            trailing = plan.trailing_stop
            binding.trailing_active |= favorable >= trailing.activation or math.isclose(
                favorable, trailing.activation, rel_tol=0.0, abs_tol=1e-12
            )
            if binding.trailing_active:
                logger.debug(
                    "FR-trading-exit-trailing: TrailingStop activated",
                    extra={"ticket": position.ticket},
                )
                candidates.append(
                    binding.favorable_price - direction * trailing.distance
                )
        candidates = [self._rounded(candidate, spec) for candidate in candidates]
        candidates = [
            candidate
            for candidate in candidates
            if self._valid_level(candidate, position, spec, stop=True)
        ]
        if not candidates:
            return None
        candidate = max(candidates) if direction == 1 else min(candidates)
        if position.sl > 0 and direction * (candidate - position.sl) <= 0:
            return None
        return candidate

    @staticmethod
    def _valid_level(
        price: float, position: PositionInfo, spec: SymbolInfo, *, stop: bool
    ) -> bool:
        quote = spec.price.bid if position.position_type == 0 else spec.price.ask
        _nonnegative(quote, "execution quote", positive=True)
        _nonnegative(spec.price.tick_size, "tick size", positive=True)
        distance = (
            max(spec.trade.stops_level, spec.trade.freeze_level) * spec.price.tick_size
        )
        direction = 1 if position.position_type == 0 else -1
        gap = direction * (quote - price) if stop else direction * (price - quote)
        return gap > 0 and (
            gap >= distance or math.isclose(gap, distance, abs_tol=1e-10)
        )

    async def _protect(
        self,
        position: PositionInfo,
        binding: _Binding,
        scope: TradeFilter,
        price: float,
        *,
        stop: bool,
    ) -> ExitOutcome:
        try:
            results = await (
                set_stop_loss(
                    self._context,
                    scope,
                    price,
                    include_pending=False,
                    tighten_only=True,
                )
                if stop
                else set_profit_target(
                    self._context, scope, price, include_pending=False
                )
            )
            result = results[0] if results else None
            if result is None:
                self._bindings.pop(position.ticket, None)
            elif result.retcode not in (
                int(TradeRetcode.DONE),
                int(TradeRetcode.NO_CHANGES),
            ):
                binding.blocked = True
            else:
                current = next(
                    (
                        item
                        for item in await self._position.PositionsGet()
                        if _identity(item) == binding.identity
                    ),
                    None,
                )
                if current is None:
                    self._bindings.pop(position.ticket, None)
                    binding.blocked = True
                elif stop:
                    direction = 1 if current.position_type == 0 else -1
                    if direction * (current.sl - price) < 0 and not math.isclose(
                        current.sl, price, rel_tol=0.0, abs_tol=1e-10
                    ):
                        binding.blocked = True
                elif not math.isclose(current.tp, price, rel_tol=0.0, abs_tol=1e-10):
                    binding.blocked = True
        except Exception:
            binding.blocked = True
            raise
        return ExitOutcome(
            position.ticket, "stop_loss" if stop else "profit_target", price, result
        )
