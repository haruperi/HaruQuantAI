"""Pure, event-driven strategy rule evaluation and effects calculation runtime."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.core.host.logging import get_logger
from app.core.trading.blocks.registry import block_registry
from app.core.trading.blocks.series import BarData
from app.core.trading.conditions import ConditionComparator
from app.core.trading.strategy.contracts import (
    ActionKind,
    BarUpdateEvent,
    CloseRequest,
    ConditionDefinition,
    EvaluationEvent,
    OrderModification,
    OrderRequest,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    SignalConflictPolicy,
    StrategyContext,
    StrategyDocument,
    StrategyEffects,
    TickUpdateEvent,
)

logger = get_logger(__name__)


def _resolve_event_field(val: str, event: EvaluationEvent) -> float | None:
    """Resolve field from incoming market event."""
    if isinstance(event, BarUpdateEvent):
        if hasattr(event.bar, val):
            return float(getattr(event.bar, val))
        aliases = {
            "bar_close": event.bar.close,
            "close": event.bar.close,
            "bar_open": event.bar.open,
            "open": event.bar.open,
            "bar_high": event.bar.high,
            "high": event.bar.high,
            "bar_low": event.bar.low,
            "low": event.bar.low,
            "bar_volume": event.bar.tick_volume,
            "volume": event.bar.tick_volume,
        }
        if val in aliases:
            return float(aliases[val])

    elif isinstance(event, TickUpdateEvent):
        if hasattr(event.tick, val):
            return float(getattr(event.tick, val))
        if val == "price":
            return (
                float(event.tick.last)
                if event.tick.last > 0
                else (event.tick.bid + event.tick.ask) / 2.0
            )

    return None


def _resolve_numeric(
    val: str | float,
    event: EvaluationEvent,
    context: StrategyContext,
    params: dict[str, Any],
) -> float:
    """Resolve a condition operand to float from event, context, or params."""
    if isinstance(val, (int, float)):
        return float(val)

    candidate = context.variables.get(val, params.get(val))
    if candidate is not None:
        try:
            return float(candidate)
        except ValueError, TypeError:
            return math.nan

    ev_val = _resolve_event_field(val, event)
    if ev_val is not None:
        return ev_val

    try:
        return float(val)
    except ValueError:
        logger.warning("Unable to resolve operand '%s' to float", val)
        return math.nan


def _create_enter_order(
    action: RuleAction,
    symbol: str,
    current_price: float,
    pip_size: float,
    magic: int,
) -> OrderRequest:
    exec_price = (
        current_price + action.price_offset
        if action.price_offset != 0.0
        else current_price
    )
    sl = 0.0
    if action.sl_price > 0.0:
        sl = action.sl_price
    elif action.sl_pips > 0.0:
        sl = (
            exec_price - action.sl_pips * pip_size
            if action.direction == 1
            else exec_price + action.sl_pips * pip_size
        )

    tp = 0.0
    if action.tp_price > 0.0:
        tp = action.tp_price
    elif action.tp_pips > 0.0:
        tp = (
            exec_price + action.tp_pips * pip_size
            if action.direction == 1
            else exec_price - action.tp_pips * pip_size
        )

    return OrderRequest(
        symbol=symbol,
        direction=action.direction,
        order_type=action.order_type,
        volume=action.volume,
        price=exec_price,
        sl=sl,
        tp=tp,
        magic=magic,
        comment=action.comment,
        atm_rules=action.atm_rules,
    )


def _create_exit_requests(
    action: RuleAction,
    symbol: str,
    context: StrategyContext,
) -> list[CloseRequest]:
    if action.target_ticket is not None:
        return [
            CloseRequest(
                ticket=action.target_ticket,
                volume=action.volume,
                comment=action.comment,
            )
        ]

    requests: list[CloseRequest] = []
    for pos in context.positions:
        if pos.symbol == symbol:
            pos_dir = 1 if pos.position_type == 0 else -1
            if action.direction in (0, pos_dir):
                requests.append(
                    CloseRequest(
                        ticket=pos.ticket,
                        volume=action.volume,
                        comment=action.comment,
                    )
                )
    return requests


def _create_cancel_requests(
    action: RuleAction,
    symbol: str,
    context: StrategyContext,
) -> list[str]:
    if action.target_ticket is not None:
        return [str(action.target_ticket)]
    return [
        str(ord_info.ticket) for ord_info in context.orders if ord_info.symbol == symbol
    ]


def _create_modify_request(action: RuleAction) -> OrderModification | None:
    if action.target_ticket is None:
        return None
    return OrderModification(
        ticket=action.target_ticket,
        price=action.price_offset if action.price_offset != 0 else None,
        sl=action.sl_price if action.sl_price != 0 else None,
        tp=action.tp_price if action.tp_price != 0 else None,
    )


@dataclass
class _EffectAccumulator:
    symbol: str
    price: float
    pip_size: float
    magic: int
    context: StrategyContext
    orders_to_open: list[OrderRequest] = field(default_factory=list)
    orders_to_cancel: list[str] = field(default_factory=list)
    orders_to_modify: list[OrderModification] = field(default_factory=list)
    positions_to_close: list[CloseRequest] = field(default_factory=list)

    def dispatch(self, action: RuleAction) -> None:
        if action.kind == ActionKind.ENTER:
            self.orders_to_open.append(
                _create_enter_order(
                    action, self.symbol, self.price, self.pip_size, self.magic
                )
            )
        elif action.kind == ActionKind.EXIT:
            self.positions_to_close.extend(
                _create_exit_requests(action, self.symbol, self.context)
            )
        elif action.kind == ActionKind.CANCEL:
            self.orders_to_cancel.extend(
                _create_cancel_requests(action, self.symbol, self.context)
            )
        elif action.kind == ActionKind.MODIFY:
            mod = _create_modify_request(action)
            if mod is not None:
                self.orders_to_modify.append(mod)


class StrategyRuntime:
    """Pure, event-driven strategy rule evaluation engine."""

    def evaluate(
        self,
        strategy: StrategyDocument,
        context: StrategyContext,
        event: EvaluationEvent,
    ) -> StrategyEffects:
        """Evaluate strategy rules against context and incoming event.

        Evaluation is pure: no state in strategy, context, or runtime is modified.
        """
        symbol = event.symbol
        current_price = (
            float(event.bar.close)
            if isinstance(event, BarUpdateEvent)
            else (
                float(event.tick.last)
                if event.tick.last > 0
                else (event.tick.bid + event.tick.ask) / 2.0
            )
        )
        pip_size = strategy.trading_setup.pip_size
        magic = strategy.trading_setup.magic_number
        params = {p.name: p.value for p in strategy.params}
        acc = _EffectAccumulator(
            symbol=symbol,
            price=current_price,
            pip_size=pip_size,
            magic=magic,
            context=context,
        )

        logger.debug(
            "Evaluating strategy '%s' on %s (symbol=%s, price=%.5f)",
            strategy.strategy_id,
            type(event).__name__,
            symbol,
            current_price,
        )

        for rule in strategy.rules:
            if not rule.is_enabled or not self._matches_trigger(rule.trigger, event):
                continue

            if not self._evaluate_conditions(rule, event, context, params):
                continue

            for action in rule.actions:
                acc.dispatch(action)

        resolved_orders = self._resolve_conflicts(
            acc.orders_to_open,
            strategy.trading_setup.conflict_policy,
            strategy.trading_setup.max_open_positions,
            context,
            symbol,
        )

        return StrategyEffects(
            orders_to_open=tuple(resolved_orders),
            orders_to_cancel=tuple(acc.orders_to_cancel),
            orders_to_modify=tuple(acc.orders_to_modify),
            positions_to_close=tuple(acc.positions_to_close),
        )

    def _matches_trigger(
        self, trigger: RuleTriggerKind, event: EvaluationEvent
    ) -> bool:
        if trigger == RuleTriggerKind.ALL:
            return True
        if isinstance(event, BarUpdateEvent):
            if trigger == RuleTriggerKind.ON_BAR_CLOSE:
                return event.is_bar_close
            if trigger == RuleTriggerKind.ON_BAR_OPEN:
                return not event.is_bar_close
            return False
        return trigger == RuleTriggerKind.ON_TICK

    def _evaluate_conditions(
        self,
        rule: RuleDefinition,
        event: EvaluationEvent,
        context: StrategyContext,
        params: dict[str, Any],
    ) -> bool:
        """Evaluate all conditions on rule sequentially; all must be satisfied."""
        for cond in rule.conditions:
            if not self._evaluate_single_condition(cond, event, context, params):
                return False
        return True

    def _evaluate_single_condition(
        self,
        cond: ConditionDefinition,
        event: EvaluationEvent,
        context: StrategyContext,
        params: dict[str, Any],
    ) -> bool:
        if cond.composition_block_id:
            return self._evaluate_composition(cond, event, context)

        left_val = _resolve_numeric(cond.left, event, context, params)
        right_val = _resolve_numeric(cond.right, event, context, params)
        delta = left_val - right_val
        try:
            return ConditionComparator.validate(delta, cond.comparator)
        except ValueError as err:
            logger.warning("Condition evaluation error: %s", err)
            return False

    def _evaluate_composition(
        self,
        cond: ConditionDefinition,
        event: EvaluationEvent,
        context: StrategyContext,
    ) -> bool:
        desc = block_registry.get(cond.composition_block_id or "")
        if desc is None:
            logger.warning(
                "Composition block '%s' not registered", cond.composition_block_id
            )
            return False

        bars: BarData | None = None
        if context.bars_by_symbol and event.symbol in context.bars_by_symbol:
            bars = context.bars_by_symbol[event.symbol]
        elif context.bars is not None:
            bars = context.bars

        if bars is None:
            logger.warning("No BarData available for composition evaluation")
            return False

        try:
            callable_target = desc.instantiate(**cond.composition_params)
            res = callable_target(bars)
            return bool(res)
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            logger.warning("Error evaluating composition block: %s", exc)
            return False

    def _resolve_conflicts(
        self,
        orders: list[OrderRequest],
        policy: SignalConflictPolicy,
        max_open_positions: int,
        context: StrategyContext,
        symbol: str,
    ) -> list[OrderRequest]:
        """Apply signal conflict policy and enforce max open position limits."""
        if not orders:
            return []

        has_long = any(o.direction == 1 for o in orders)
        has_short = any(o.direction == -1 for o in orders)

        if has_long and has_short:
            logger.info("Signal conflict: policy=%s", policy)
            if policy == SignalConflictPolicy.CANCEL_BOTH:
                return []
            if policy == SignalConflictPolicy.FIRST_SIGNAL:
                first_dir = orders[0].direction
                orders = [o for o in orders if o.direction == first_dir]
            elif policy == SignalConflictPolicy.REVERSE:
                last_dir = orders[-1].direction
                orders = [o for o in orders if o.direction == last_dir]

        current_open = sum(1 for p in context.positions if p.symbol == symbol)
        remaining_slots = max(0, max_open_positions - current_open)
        if len(orders) > remaining_slots:
            logger.info(
                "Trimming orders to available slots (%d orders -> %d slots)",
                len(orders),
                remaining_slots,
            )
            orders = orders[:remaining_slots]

        return orders


__all__ = ["StrategyRuntime"]
