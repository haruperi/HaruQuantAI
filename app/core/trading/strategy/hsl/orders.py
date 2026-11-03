"""Financial HSL actions with explicit valuation inputs.

Description:
    Evaluates entry prices, protection, sizing, and owned position actions.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Consistent financial action semantics.
Key Capabilities:
    - FR-hsl-orders: Reject missing economics and log typed order intentions.
Python API Usage:
    Use Orders from the shared HSL event evaluator.
CLI Usage:
    uv run pytest tests/core/trading/strategy --no-cov
"""

from __future__ import annotations

import math
from decimal import ROUND_FLOOR, Decimal
from typing import Any

from app.core.enums import OrderType
from app.core.host.logging import get_logger
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    CloseRequest,
    InstrumentEconomics,
    OrderModification,
    OrderRequest,
    TickUpdateEvent,
)
from app.core.trading.strategy.hsl import models as hm
from app.core.trading.strategy.hsl import value_models as vm
from app.core.trading.strategy.hsl.expressions import Expressions, event_time, fail

logger = get_logger(__name__)
PERCENT = 100


class Orders:
    """Collect trading intentions; never send orders or mutate broker snapshots."""

    def __init__(
        self, expressions: Expressions, strategy: hm.HSLStrategyPayload
    ) -> None:
        self.expressions = expressions
        self.strategy = strategy
        self.entries: list[OrderRequest] = []
        self.closes: list[CloseRequest] = []
        self.cancels: list[str] = []
        self.modifications: list[OrderModification] = []
        self.magic = int(strategy.metadata.get("magic_number", 1000))
        self.magics = {self.magic} | {
            action.magic_number
            for rule in strategy.rules
            for action in (*rule.then, *rule.else_then)
            if isinstance(action, (hm.OrderMarketActionNode, hm.OrderPendingActionNode))
            and action.magic_number is not None
        }

    def economics(self) -> InstrumentEconomics:
        """Require finite, explicit instrument valuation and quantity constraints."""
        econ = self.expressions.context.economics.get(self.expressions.event.symbol)
        if econ is None:
            fail(
                "Instrument economics are required for financial conversion",
                "HSL_MISSING_ECONOMICS",
            )
        for value in (
            econ.pip_size,
            econ.tick_size,
            econ.pip_value_per_lot,
            econ.contract_size,
            econ.min_volume,
            econ.max_volume,
            econ.volume_step,
        ):
            if not math.isfinite(value) or value <= 0:
                fail("Instrument economics must be finite and positive")
        if econ.min_volume > econ.max_volume:
            fail("Instrument volume bounds are reversed")
        return econ

    def price(self, direction: int = 1) -> float:
        """Use the event's executable side or explicitly available bar price."""
        event = self.expressions.event
        if isinstance(event, TickUpdateEvent):
            value = event.tick.ask if direction == 1 else event.tick.bid
        elif isinstance(event, BarUpdateEvent):
            value = event.bar.close if event.is_bar_close else event.bar.open
        else:
            value = float(self.expressions.feed(vm.EvaluationContext()).close[-1])
        if not math.isfinite(value) or value <= 0:
            fail("Executable price is unavailable")
        return float(value)

    def protection(
        self,
        spec: Any,
        price: float,
        direction: int,
        *,
        target: bool = False,
        stop: float = 0.0,
    ) -> float:
        """Resolve absolute protective prices; expression mode means a price level."""
        if spec.type == "none":
            return 0.0
        ex = self.expressions
        distance, absolute = self._protection_distance(spec, price, stop)
        if not math.isfinite(distance) or distance <= 0:
            fail("Protection must have a finite positive distance or price")
        sign = direction if target else -direction
        level = distance if absolute else price + sign * distance
        if level <= 0 or (level - price) * sign <= 0:
            fail("Protective price is on the wrong side of entry")
        econ = ex.context.economics.get(ex.event.symbol)
        if econ is not None:
            step = self.economics().tick_size
            level = float(
                round(Decimal(str(level)) / Decimal(str(step))) * Decimal(str(step))
            )
            if (level - price) * sign <= 0:
                fail("Tick normalization removes protective distance")
        return float(level)

    def volume(
        self,
        spec: vm.MoneyManagementSpec | vm.OperandNode | None,
        price: float,
        stop: float,
    ) -> float:
        """Calculate quantity without increasing risk to satisfy minimum lot size."""
        ex = self.expressions
        sizing = (
            spec
            if isinstance(spec, vm.MoneyManagementSpec)
            else self.strategy.money_management
        )
        if spec is not None and (not isinstance(spec, vm.MoneyManagementSpec)):
            volume = ex.numeric(spec)
        elif sizing.type == "fixed_size":
            volume = ex.numeric(sizing.size)
        else:
            volume = self._financial_volume(sizing, price, stop)
        if not math.isfinite(volume) or volume <= 0:
            fail("Order quantity must be finite and positive")
        if sizing.max_lots is not None:
            volume = min(volume, sizing.max_lots)
        available_economics = ex.context.economics.get(ex.event.symbol)
        if available_economics is not None:
            econ = self.economics()
            volume = min(volume, econ.max_volume)
            step = Decimal(str(econ.volume_step))
            volume = float(
                (Decimal(str(volume)) / step).to_integral_value(rounding=ROUND_FLOOR)
                * step
            )
            if volume < econ.min_volume:
                fail("Requested risk cannot satisfy the instrument minimum volume")
        return float(volume)

    def owned_positions(self, side: str = "any") -> list[Any]:
        """Select positions by symbol, ownership, and requested direction."""
        return [
            p
            for p in self.expressions.context.positions
            if p.symbol == self.expressions.event.symbol
            and p.magic in self.magics
            and (side == "any" or (p.position_type == 0) == (side == "long"))
        ]

    def execute(self, action: hm.ActionNode) -> None:
        """Evaluate a financial action against the current event snapshot."""
        ex = self.expressions
        if isinstance(action, (hm.OrderMarketActionNode, hm.OrderPendingActionNode)):
            self._entry(action)
        elif isinstance(action, hm.PositionCloseActionNode):
            self.closes.extend(
                CloseRequest(
                    p.ticket, p.volume * action.quantity_pct / 100.0, action.reason
                )
                for p in self.owned_positions(action.target_side)
            )
        elif isinstance(action, hm.OrderModifyActionNode):
            for pos in self.owned_positions():
                direction = 1 if pos.position_type == 0 else -1
                modified_sl = (
                    self.protection(action.stop_loss, self.price(direction), direction)
                    if action.stop_loss
                    else None
                )
                modified_tp = (
                    self.protection(
                        action.take_profit,
                        self.price(direction),
                        direction,
                        target=True,
                        stop=pos.sl,
                    )
                    if action.take_profit
                    else None
                )
                self.modifications.append(
                    OrderModification(pos.ticket, sl=modified_sl, tp=modified_tp)
                )
        elif isinstance(action, hm.OrderCancelActionNode):
            self.cancels.extend(
                str(o.ticket)
                for o in ex.context.orders
                if o.symbol == ex.event.symbol
                and o.magic in self.magics
                and (
                    action.target_side == "any"
                    or (int(o.order_type) % 2 == 0) == (action.target_side == "long")
                )
            )

    def _protection_distance(self, spec: Any, price: Any, stop: Any) -> Any:
        """Resolve one explicit order policy."""
        ex = self.expressions
        absolute = False
        if spec.type == "indicator":
            distance = ex.numeric(spec.indicator)
            absolute = True
        elif spec.type == "expression":
            distance = ex.numeric(spec.expression)
            absolute = True
        elif spec.type == "atr":
            period = ex.numeric(spec.period)
            if not period.is_integer() or period < 1:
                fail("ATR period must be a positive integer")
            atr = vm.IndicatorExpressionNode(
                name="indicator.volatility.atr",
                output="value",
                params={"period": int(period)},
            )
            multiplier = ex.numeric(spec.multiplier)
            distance = ex.numeric(atr) * multiplier
        elif spec.type == "risk_multiple":
            if stop <= 0 or stop == price:
                fail("Risk-multiple target requires a nonzero stop distance")
            distance = abs(price - stop) * ex.numeric(spec.multiple)
        else:
            value = ex.numeric(spec.value)
            unit = (
                self.economics().pip_size
                if spec.type == "fixed_pips"
                else self.economics().tick_size
                if spec.type == "fixed_points"
                else price / 100.0
            )
            distance = value * unit
        return (distance, absolute)

    def _financial_volume(self, sizing: Any, price: Any, stop: Any) -> float:
        """Resolve one explicit order policy."""
        ex = self.expressions
        econ = self.economics()
        equity = ex.context.account_equity
        if sizing.type == "fixed_cash":
            volume = float(
                Decimal(str(ex.numeric(sizing.amount)))
                / (Decimal(str(price)) * Decimal(str(econ.contract_size)))
            )
        else:
            if equity is None or not math.isfinite(equity) or equity <= 0:
                fail("Explicit account equity is required for percentage sizing")
            percentage = ex.numeric(
                sizing.risk_pct if sizing.type == "risk_percent" else sizing.percent
            )
            if not 0 < percentage <= PERCENT:
                fail("Sizing percentage must be within (0, 100]")
            cash = float(Decimal(str(equity)) * Decimal(str(percentage)) / Decimal(100))
            if sizing.type == "risk_percent":
                if stop <= 0:
                    fail("Risk sizing requires a protective stop")
                distance = abs(Decimal(str(price)) - Decimal(str(stop)))
                volume = float(
                    Decimal(str(cash))
                    / (
                        distance
                        / Decimal(str(econ.pip_size))
                        * Decimal(str(econ.pip_value_per_lot))
                    )
                )
            else:
                volume = float(
                    Decimal(str(cash))
                    / (Decimal(str(price)) * Decimal(str(econ.contract_size)))
                )
        return float(volume)

    def _entry(self, action: Any) -> None:
        """Resolve one explicit order policy."""
        ex = self.expressions
        direction = 1 if action.side == "long" else -1
        current = self.price(direction)
        price = (
            ex.numeric(action.entry_price)
            if isinstance(action, hm.OrderPendingActionNode)
            else current
        )
        if price <= 0:
            fail("Entry price must be positive")
        kind = OrderType.BUY if direction == 1 else OrderType.SELL
        atm: dict[str, Any] = {}
        if isinstance(action, hm.OrderPendingActionNode):
            stop_order = action.action == "enter_stop"
            if (price - current) * direction * (1 if stop_order else -1) <= 0:
                fail("Pending entry price is on the wrong side of the market")
            kind = (
                (OrderType.BUY_STOP if direction == 1 else OrderType.SELL_STOP)
                if stop_order
                else OrderType.BUY_LIMIT
                if direction == 1
                else OrderType.SELL_LIMIT
            )
            if action.expiration_bars:
                if not isinstance(ex.event, BarUpdateEvent):
                    fail("Bar expiration requires a bar timeframe")
                atm["expires_at"] = (
                    event_time(ex.event)
                    + action.expiration_bars * ex.event.timeframe.to_seconds()
                )
        sl_spec = action.stop_loss or self.strategy.risk_management.default_stop_loss
        tp_spec = (
            action.take_profit or self.strategy.risk_management.default_take_profit
        )
        sl = self.protection(sl_spec, price, direction)
        tp = self.protection(tp_spec, price, direction, target=True, stop=sl)
        volume = self.volume(action.size, price, sl)
        magic = action.magic_number if action.magic_number is not None else self.magic
        logger.debug(
            "FR-hsl-orders: entry %s direction=%d quantity=%s",
            ex.event.symbol,
            direction,
            volume,
        )
        self.entries.append(
            OrderRequest(
                ex.event.symbol,
                direction,
                kind,
                volume,
                price,
                sl,
                tp,
                magic,
                action.comment,
                atm,
            )
        )
