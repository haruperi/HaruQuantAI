"""A deliberately simple, deterministic, no-lookahead bar backtest engine.

Execution model
---------------
1. A strategy sees only bars that have fully completed at a bar close.
2. Its intents are submitted for execution at the following bar open.
3. Market orders fill at next-bar bid/ask plus configured adverse slippage.
4. Stop/limit orders are evaluated against bid/ask OHLC after they become active.
5. SL/TP conflicts in a single OHLC bar use a declared deterministic policy.
6. Trailing stops update after that bar's protection checks and apply from the
   next bar, preventing a favorable intrabar high/low from being reused as a
   known stop fill on the same bar.

This is suitable for initial strategy research and regression tests.  It is not
a replacement for the HaruQuant Simulation module's future tick-level fill,
liquidity, latency, margin, swap, corporate-action, and asset-class realism.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from math import floor
from typing import TYPE_CHECKING

from app.services.data import validate_bars
from app.services.simulator.models import (
    BacktestConfig,
    BacktestEvent,
    BacktestMetrics,
    BacktestResult,
    ClosedTrade,
    EquityPoint,
    FillReason,
    IntrabarConflictPolicy,
    SimPendingOrder,
    SimPosition,
)
from app.services.strategy import (
    AccountSnapshot,
    Bar,
    Direction,
    EntryType,
    IntentAction,
    MarketContext,
    PendingOrderSnapshot,
    PositionSnapshot,
    ProtectionRequest,
    QuoteSnapshot,
    RuntimeMode,
    TradeIntent,
)
from app.services.strategy.state import StrategyState

if TYPE_CHECKING:
    from app.services.strategy.base import BaseStrategy

type FeatureProvider = Callable[[int, Sequence[Bar], datetime], Mapping[str, object]]
type QueuedIntent = tuple[TradeIntent, bool]


class SimpleBacktestEngine:
    """Execute one broker-neutral strategy against one primary OHLCV bar stream.

    ``run`` deliberately resets strategy-local state by default.  A caller who
    wants a resumable segmented run can set ``BacktestConfig.reset_strategy_state``
    to ``False`` and persist/restore ``StrategyState`` independently.
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self._position_counter = 0
        self._order_counter = 0
        self._trade_counter = 0

    def run(
        self,
        strategy: BaseStrategy,
        bars: Sequence[Bar],
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
        additional_chart_bars: Mapping[str, Sequence[Bar]] | None = None,
        chart_timeframes: Mapping[str, str] | None = None,
        feature_provider: FeatureProvider | None = None,
    ) -> BacktestResult:
        """Run a bar-by-bar simulation and return a fully auditable result.

        ``additional_chart_bars`` supports strategies such as Harriet Hedging.
        Keys must match the keys the strategy requests in ``context.bars_for_chart``.
        ``feature_provider`` supplies per-close normalized data, for example the
        newest-first ``zigzag_extremes`` sequence needed by Market Structure EA.
        """
        main_bars = validate_bars(bars)
        if self.config.reset_strategy_state:  # pragma: no cover
            strategy.state = StrategyState()
        self._reset_ids()

        resolved_symbol = symbol or str(
            strategy.config.section("trading_profile").get("symbols", {}).get("main", {}).get("symbol", "")
        )
        resolved_timeframe = timeframe or str(
            strategy.config.section("trading_profile").get("symbols", {}).get("main", {}).get("timeframe", "")
        )
        if not resolved_symbol or not resolved_timeframe:
            raise ValueError("symbol and timeframe must be supplied or configured in strategy.json.")
        main_duration = _timeframe_duration(resolved_timeframe)
        auxiliary = {
            key: validate_bars(value)
            for key, value in (additional_chart_bars or {}).items()
        }
        auxiliary_durations = {
            key: _timeframe_duration((chart_timeframes or {}).get(key, key))
            for key in auxiliary
        }

        balance = self.config.initial_balance
        positions: list[SimPosition] = []
        pending_orders: list[SimPendingOrder] = []
        queued_intents: dict[int, list[QueuedIntent]] = defaultdict(list)
        deferred_time_exits: dict[int, list[str]] = defaultdict(list)
        closed_trades: list[ClosedTrade] = []
        equity_curve: list[EquityPoint] = []
        events: list[BacktestEvent] = []
        diagnostics: list[str] = []

        if main_bars:  # pragma: no cover
            import pandas as pd
            df_all = pd.DataFrame(
                {
                    "open": [b.open for b in main_bars],
                    "high": [b.high for b in main_bars],
                    "low": [b.low for b in main_bars],
                    "close": [b.close for b in main_bars],
                    "volume": [b.volume for b in main_bars],
                },
                index=[b.open_time for b in main_bars],
            )
            full_context = MarketContext(
                runtime_mode=RuntimeMode.SIMULATOR,
                symbol=resolved_symbol,
                timeframe=resolved_timeframe,
                as_of=main_bars[-1].open_time + main_duration,
                bars=main_bars,
                chart_bars=auxiliary,
            )
            strategy.df_signals = strategy.calculate_signals(df_all, full_context)

        for index, bar in enumerate(main_bars):
            open_quote = self._quote(bar.open)
            fill_event_ids: list[str] = []

            time_exit_ids = deferred_time_exits.pop(index, [])
            for position_id in time_exit_ids:
                position = _find_position(positions, position_id)
                if position is None:
                    continue  # pragma: no cover
                close_price = self._market_exit_price(open_quote, position.direction)
                balance = self._close_position(
                    position,
                    position.quantity,
                    close_price,
                    bar.open_time,
                    FillReason.TIME_EXIT,
                    positions,
                    closed_trades,
                    balance,
                )

            open_queue = queued_intents.pop(index, [])
            normal_intents = [item for item in open_queue if not item[1]]
            event_intents = [item for item in open_queue if item[1]]
            normal_fill_ids, balance = self._apply_intents(
                normal_intents,
                bar_index=index,
                now=bar.open_time,
                quote=open_quote,
                positions=positions,
                pending_orders=pending_orders,
                closed_trades=closed_trades,
                events=events,
                balance=balance,
                pending_activation_index=index,
            )
            fill_event_ids.extend(normal_fill_ids)
            event_fill_ids, balance = self._apply_intents(
                event_intents,
                bar_index=index,
                now=bar.open_time,
                quote=open_quote,
                positions=positions,
                pending_orders=pending_orders,
                closed_trades=closed_trades,
                events=events,
                balance=balance,
                pending_activation_index=index + 1,
            )
            fill_event_ids.extend(event_fill_ids)

            pending_fill_ids, balance = self._fill_triggered_pending_orders(
                bar,
                index,
                positions,
                pending_orders,
                closed_trades,
                events,
                balance,
            )
            fill_event_ids.extend(pending_fill_ids)

            if self.config.emit_execution_events and index > 0:
                self._queue_execution_reactions(
                    strategy=strategy,
                    event_ids=fill_event_ids,
                    next_index=index + 1,
                    as_of=bar.open_time,
                    history=main_bars[:index],
                    auxiliary=auxiliary,
                    auxiliary_durations=auxiliary_durations,
                    feature_provider=feature_provider,
                    symbol=resolved_symbol,
                    timeframe=resolved_timeframe,
                    quote=open_quote,
                    positions=positions,
                    pending_orders=pending_orders,
                    balance=balance,
                    queued_intents=queued_intents,
                    events=events,
                    diagnostics=diagnostics,
                )

            balance = self._process_protective_exits(
                bar,
                index,
                positions,
                closed_trades,
                events,
                balance,
            )
            self._update_trailing_stops(bar, positions)
            for position in positions:
                if (
                    position.time_exit_bars is not None
                    and index - position.opened_bar_index + 1 >= position.time_exit_bars
                ):
                    deferred_time_exits[index + 1].append(position.position_id)

            close_time = bar.open_time + main_duration
            close_context = self._make_context(
                history=main_bars[: index + 1],
                as_of=close_time,
                symbol=resolved_symbol,
                timeframe=resolved_timeframe,
                quote=self._quote(bar.close),
                positions=positions,
                pending_orders=pending_orders,
                balance=balance,
                auxiliary=auxiliary,
                auxiliary_durations=auxiliary_durations,
                feature_provider=feature_provider,
                feature_index=index,
            )
            decision = strategy.evaluate(close_context)
            for message in decision.diagnostics:
                events.append(  # pragma: no cover
                    BacktestEvent(close_time, "STRATEGY_DIAGNOSTIC", message)
                )
            if decision.intents:
                if index + 1 < len(main_bars):
                    queued_intents[index + 1].extend((intent, False) for intent in decision.intents)
                else:
                    diagnostics.append(
                        f"Discarded {len(decision.intents)} final-bar intent(s): no next bar exists for no-lookahead execution."
                    )

            unrealized = self._unrealized_pnl(positions, self._quote(bar.close))
            equity_curve.append(
                EquityPoint(
                    time=close_time,
                    balance=balance,
                    equity=balance + unrealized,
                    unrealized_pnl=unrealized,
                    open_position_count=len(positions),
                    pending_order_count=len(pending_orders),
                )
            )

        final_bar = main_bars[-1]
        final_time = final_bar.open_time + main_duration
        if self.config.close_open_positions_at_end:
            close_quote = self._quote(final_bar.close)
            for position in tuple(positions):
                balance = self._close_position(  # pragma: no cover
                    position,
                    position.quantity,
                    self._market_exit_price(close_quote, position.direction),
                    final_time,
                    FillReason.END_OF_TEST,
                    positions,
                    closed_trades,
                    balance,
                )
            pending_orders.clear()
            if equity_curve:  # pragma: no cover
                equity_curve[-1] = replace(
                    equity_curve[-1],
                    balance=balance,
                    equity=balance,
                    unrealized_pnl=0.0,
                    open_position_count=0,
                    pending_order_count=0,
                )

        metrics = _build_metrics(self.config.initial_balance, balance, closed_trades, equity_curve)
        return BacktestResult(
            strategy_id=strategy.config.strategy_id,
            symbol=resolved_symbol,
            timeframe=resolved_timeframe,
            started_at=main_bars[0].open_time,
            ended_at=final_time,
            config=self.config,
            closed_trades=tuple(closed_trades),
            equity_curve=tuple(equity_curve),
            events=tuple(events),
            open_positions=tuple(positions),
            pending_orders=tuple(pending_orders),
            metrics=metrics,
            diagnostics=tuple(diagnostics),
        )

    def _apply_intents(
        self,
        queued: Sequence[QueuedIntent],
        *,
        bar_index: int,
        now: datetime,
        quote: QuoteSnapshot,
        positions: list[SimPosition],
        pending_orders: list[SimPendingOrder],
        closed_trades: list[ClosedTrade],
        events: list[BacktestEvent],
        balance: float,
        pending_activation_index: int,
    ) -> tuple[list[str], float]:
        """Apply queued intents in deterministic cancellation/close/modify/open order."""
        fill_event_ids: list[str] = []
        priority = {
            IntentAction.CANCEL_PENDING: 0,
            IntentAction.CLOSE: 1,
            IntentAction.PARTIAL_CLOSE: 2,
            IntentAction.MODIFY: 3,
            IntentAction.OPEN: 4,
        }
        ordered = sorted((item[0] for item in queued), key=lambda intent: priority[intent.action])
        for intent in ordered:
            if not intent.symbol:
                events.append(BacktestEvent(now, "IGNORED_INTENT", "Intent has an invalid symbol.", intent.intent_id))  # pragma: no cover
                continue  # pragma: no cover
            if intent.action is IntentAction.CANCEL_PENDING:
                removed = self._cancel_pending(intent, pending_orders)  # pragma: no cover
                events.append(BacktestEvent(now, "CANCEL_PENDING", f"Cancelled {removed} pending order(s).", intent.intent_id))  # pragma: no cover
            elif intent.action is IntentAction.CLOSE:
                targets = self._target_positions(intent, positions)  # pragma: no cover
                for position in tuple(targets):  # pragma: no cover
                    exit_price = self._market_exit_price(quote, position.direction)  # pragma: no cover
                    balance = self._close_position(position, position.quantity, exit_price, now, FillReason.SIGNAL_CLOSE, positions, closed_trades, balance)  # pragma: no cover
                events.append(BacktestEvent(now, "CLOSE", f"Closed {len(targets)} position(s).", intent.intent_id))  # pragma: no cover
            elif intent.action is IntentAction.PARTIAL_CLOSE:
                quantity_left = self._quantity(intent.requested_quantity)  # pragma: no cover
                if quantity_left is not None and quantity_left > 0:  # pragma: no cover
                    targets = self._target_positions(intent, positions)  # pragma: no cover
                    closed_count = 0  # pragma: no cover
                    for position in tuple(targets):  # pragma: no cover
                        if quantity_left <= 0:  # pragma: no cover
                            break  # pragma: no cover
                        quantity = min(position.quantity, quantity_left)  # pragma: no cover
                        exit_price = self._market_exit_price(quote, position.direction)  # pragma: no cover
                        balance = self._close_position(position, quantity, exit_price, now, FillReason.PARTIAL_CLOSE, positions, closed_trades, balance)  # pragma: no cover
                        quantity_left -= quantity  # pragma: no cover
                        closed_count += 1  # pragma: no cover
                    events.append(BacktestEvent(now, "PARTIAL_CLOSE", f"Partially closed {closed_count} position(s).", intent.intent_id))  # pragma: no cover
            elif intent.action is IntentAction.MODIFY:
                targets = self._target_positions(intent, positions)  # pragma: no cover
                for position in targets:  # pragma: no cover
                    _apply_protection_to_position(position, intent.protection)  # pragma: no cover
                events.append(BacktestEvent(now, "MODIFY", f"Modified {len(targets)} position(s).", intent.intent_id))  # pragma: no cover
            elif intent.action is IntentAction.OPEN:  # pragma: no cover
                if intent.entry_type in (EntryType.MARKET, EntryType.REVERSE):
                    new_pos = self._open_market_position(intent, bar_index, now, quote, balance)
                    if new_pos is None:
                        events.append(BacktestEvent(now, "IGNORED_INTENT", "Invalid market quantity.", intent.intent_id))  # pragma: no cover
                    else:
                        positions.append(new_pos)
                        balance -= new_pos.entry_commission
                        fill_event_ids.append(f"fill:{new_pos.position_id}")
                        events.append(BacktestEvent(now, "MARKET_FILL", "Opened market position.", intent.intent_id, new_pos.position_id))
                elif intent.entry_type in (EntryType.LIMIT, EntryType.STOP):
                    order = self._place_pending_order(intent, now, pending_activation_index)
                    if order is None:
                        events.append(BacktestEvent(now, "IGNORED_INTENT", "Pending order requires a valid price and quantity.", intent.intent_id))  # pragma: no cover
                    else:
                        pending_orders.append(order)
                        events.append(BacktestEvent(now, "PENDING_PLACED", "Placed pending order.", intent.intent_id, order.order_id))
                else:
                    events.append(BacktestEvent(now, "IGNORED_INTENT", "Unsupported entry type.", intent.intent_id))  # pragma: no cover
        return fill_event_ids, balance

    def _open_market_position(
        self,
        intent: TradeIntent,
        bar_index: int,
        now: datetime,
        quote: QuoteSnapshot,
        balance: float,
    ) -> SimPosition | None:
        quantity = self._quantity(intent.requested_quantity)
        if quantity is None:
            return None  # pragma: no cover
        entry = quote.entry_price(intent.direction)
        if intent.direction is Direction.LONG:
            entry += self.config.slippage_price
        else:
            entry -= self.config.slippage_price  # pragma: no cover
        return self._new_position(
            intent,
            quantity,
            entry,
            now,
            bar_index,
            entry_commission=quantity * self.config.commission_per_unit,
        )

    def _place_pending_order(
        self,
        intent: TradeIntent,
        now: datetime,
        activation_bar_index: int,
    ) -> SimPendingOrder | None:
        quantity = self._quantity(intent.requested_quantity)
        requested_price = intent.limit_price if intent.entry_type is EntryType.LIMIT else intent.stop_price
        if quantity is None or requested_price is None or requested_price <= 0 or intent.entry_type is None:
            return None  # pragma: no cover
        self._order_counter += 1
        protection = intent.protection
        return SimPendingOrder(
            order_id=f"ord-{self._order_counter:07d}",
            strategy_id=intent.strategy_id,
            symbol=intent.symbol,
            direction=intent.direction,
            entry_type=intent.entry_type,
            quantity=quantity,
            requested_price=requested_price,
            placed_at=now,
            activation_bar_index=activation_bar_index,
            magic_number=intent.magic_number,
            comment=intent.order_comment,
            stop_loss_price=protection.stop_loss_price,
            profit_target_price=protection.profit_target_price,
            stop_loss_distance=protection.stop_loss_distance,
            profit_target_distance=protection.profit_target_distance,
            trailing_distance=protection.trailing_distance,
            trailing_activation_distance=protection.trailing_activation_distance,
            time_exit_bars=protection.time_exit_bars,
            metadata=dict(intent.metadata),
        )

    def _fill_triggered_pending_orders(
        self,
        bar: Bar,
        bar_index: int,
        positions: list[SimPosition],
        pending_orders: list[SimPendingOrder],
        closed_trades: list[ClosedTrade],
        events: list[BacktestEvent],
        balance: float,
    ) -> tuple[list[str], float]:
        fill_ids: list[str] = []
        for order in tuple(pending_orders):
            if order.activation_bar_index > bar_index:
                continue  # pragma: no cover
            entry_price = self._pending_fill_price(order, bar)
            if entry_price is None:
                continue  # pragma: no cover
            pending_orders.remove(order)
            intent = TradeIntent(
                intent_id=f"pending-fill:{order.order_id}",
                strategy_id=order.strategy_id,
                signal_time=bar.open_time,
                action=IntentAction.OPEN,
                symbol=order.symbol,
                direction=order.direction,
                entry_type=order.entry_type,
                order_comment=order.comment,
                magic_number=order.magic_number,
                protection=ProtectionRequest(
                    stop_loss_price=order.stop_loss_price,
                    profit_target_price=order.profit_target_price,
                    stop_loss_distance=order.stop_loss_distance,
                    profit_target_distance=order.profit_target_distance,
                    trailing_distance=order.trailing_distance,
                    trailing_activation_distance=order.trailing_activation_distance,
                    time_exit_bars=order.time_exit_bars,
                ),
                requested_quantity=order.quantity,
                metadata=order.metadata,
            )
            position = self._new_position(
                intent,
                order.quantity,
                entry_price,
                bar.open_time,
                bar_index,
                entry_commission=order.quantity * self.config.commission_per_unit,
            )
            positions.append(position)
            balance -= position.entry_commission
            reason = FillReason.LIMIT if order.entry_type is EntryType.LIMIT else FillReason.STOP
            fill_ids.append(f"fill:{position.position_id}")
            events.append(BacktestEvent(bar.open_time, f"{reason}_FILL", "Filled pending order.", entity_id=position.position_id))
        return fill_ids, balance

    def _pending_fill_price(self, order: SimPendingOrder, bar: Bar) -> float | None:
        open_price, high, low, _ = self._side_ohlc(bar, order.direction, for_entry=True)
        price = order.requested_price
        if order.entry_type is EntryType.LIMIT:
            if order.direction is Direction.LONG:
                if open_price <= price:
                    return min(open_price, price)  # pragma: no cover
                return price if low <= price else None
            if open_price >= price:  # pragma: no cover
                return max(open_price, price)  # pragma: no cover
            return price if high >= price else None  # pragma: no cover
        if order.entry_type is EntryType.STOP:
            if order.direction is Direction.LONG:
                if open_price >= price:
                    return open_price + self.config.slippage_price  # pragma: no cover
                return price + self.config.slippage_price if high >= price else None
            if open_price <= price:  # pragma: no cover
                return open_price - self.config.slippage_price  # pragma: no cover
            return price - self.config.slippage_price if low <= price else None  # pragma: no cover
        return None

    def _process_protective_exits(
        self,
        bar: Bar,
        bar_index: int,
        positions: list[SimPosition],
        closed_trades: list[ClosedTrade],
        events: list[BacktestEvent],
        balance: float,
    ) -> float:
        del bar_index
        for position in tuple(positions):
            _, high, low, _ = self._side_ohlc(bar, position.direction, for_entry=False)
            stop_hit = position.stop_loss_price is not None and (
                low <= position.stop_loss_price if position.direction is Direction.LONG else high >= position.stop_loss_price
            )
            target_hit = position.profit_target_price is not None and (
                high >= position.profit_target_price if position.direction is Direction.LONG else low <= position.profit_target_price
            )
            if not stop_hit and not target_hit:
                continue
            if stop_hit and (not target_hit or self.config.intrabar_conflict_policy is IntrabarConflictPolicy.STOP_FIRST):  # pragma: no cover
                assert position.stop_loss_price is not None  # pragma: no cover
                price = self._protection_exit_price(bar, position.direction, position.stop_loss_price, is_stop=True)  # pragma: no cover
                balance = self._close_position(position, position.quantity, price, bar.open_time, FillReason.STOP_LOSS, positions, closed_trades, balance)  # pragma: no cover
                events.append(BacktestEvent(bar.open_time, "STOP_LOSS", "Closed position at stop loss.", entity_id=position.position_id))  # pragma: no cover
            else:  # pragma: no cover
                assert position.profit_target_price is not None  # pragma: no cover
                price = self._protection_exit_price(bar, position.direction, position.profit_target_price, is_stop=False)  # pragma: no cover
                balance = self._close_position(position, position.quantity, price, bar.open_time, FillReason.PROFIT_TARGET, positions, closed_trades, balance)  # pragma: no cover
                events.append(BacktestEvent(bar.open_time, "PROFIT_TARGET", "Closed position at profit target.", entity_id=position.position_id))  # pragma: no cover
        return balance

    def _update_trailing_stops(self, bar: Bar, positions: Sequence[SimPosition]) -> None:
        for position in positions:
            if position.trailing_distance is None:
                continue
            _, high, low, _ = self._side_ohlc(bar, position.direction, for_entry=False)  # pragma: no cover
            activation = position.trailing_activation_distance or 0.0  # pragma: no cover
            activated = (  # pragma: no cover
                high >= position.entry_price + activation  # pragma: no cover
                if position.direction is Direction.LONG  # pragma: no cover
                else low <= position.entry_price - activation  # pragma: no cover
            )  # pragma: no cover
            if not activated:  # pragma: no cover
                continue  # pragma: no cover
            candidate = high - position.trailing_distance if position.direction is Direction.LONG else low + position.trailing_distance  # pragma: no cover
            improves = position.stop_loss_price is None or (  # pragma: no cover
                candidate > position.stop_loss_price if position.direction is Direction.LONG else candidate < position.stop_loss_price  # pragma: no cover
            )  # pragma: no cover
            if improves:  # pragma: no cover
                position.stop_loss_price = candidate  # pragma: no cover

    def _queue_execution_reactions(
        self,
        *,
        strategy: BaseStrategy,
        event_ids: Sequence[str],
        next_index: int,
        as_of: datetime,
        history: Sequence[Bar],
        auxiliary: Mapping[str, Sequence[Bar]],
        auxiliary_durations: Mapping[str, timedelta],
        feature_provider: FeatureProvider | None,
        symbol: str,
        timeframe: str,
        quote: QuoteSnapshot,
        positions: Sequence[SimPosition],
        pending_orders: Sequence[SimPendingOrder],
        balance: float,
        queued_intents: dict[int, list[QueuedIntent]],
        events: list[BacktestEvent],
        diagnostics: list[str],
    ) -> None:
        if not history:
            return  # pragma: no cover
        for event_id in event_ids:
            context = self._make_context(
                history=history,
                as_of=as_of,
                symbol=symbol,
                timeframe=timeframe,
                quote=quote,
                positions=positions,
                pending_orders=pending_orders,
                balance=balance,
                auxiliary=auxiliary,
                auxiliary_durations=auxiliary_durations,
                feature_provider=feature_provider,
                feature_index=len(history) - 1,
            )
            decision = strategy.evaluate_execution_event(context, event_id)
            if decision.intents:
                queued_intents[next_index].extend((intent, True) for intent in decision.intents)  # pragma: no cover
                events.append(BacktestEvent(as_of, "EXECUTION_REACTION", f"Queued {len(decision.intents)} event-reaction intent(s).", entity_id=event_id))  # pragma: no cover
            diagnostics.extend(decision.diagnostics)

    def _make_context(
        self,
        *,
        history: Sequence[Bar],
        as_of: datetime,
        symbol: str,
        timeframe: str,
        quote: QuoteSnapshot,
        positions: Sequence[SimPosition],
        pending_orders: Sequence[SimPendingOrder],
        balance: float,
        auxiliary: Mapping[str, Sequence[Bar]],
        auxiliary_durations: Mapping[str, timedelta],
        feature_provider: FeatureProvider | None,
        feature_index: int,
    ) -> MarketContext:
        features = dict(feature_provider(feature_index, history, as_of)) if feature_provider else {}
        chart_bars = {}
        for key, values in auxiliary.items():
            duration = auxiliary_durations[key]
            cutoff = as_of - duration
            low = 0
            high = len(values)
            while low < high:
                mid = (low + high) // 2
                if values[mid].open_time <= cutoff:
                    low = mid + 1
                else:
                    high = mid
            chart_bars[key] = tuple(values[:low])
        return MarketContext(
            runtime_mode=RuntimeMode.SIMULATOR,
            symbol=symbol,
            timeframe=timeframe,
            as_of=as_of,
            bars=tuple(history),
            chart_bars=chart_bars,
            quote=quote,
            account=AccountSnapshot(
                balance=balance,
                volume_min=self.config.volume_min,
                volume_max=self.config.volume_max,
                volume_step=self.config.volume_step,
            ),
            positions=tuple(_position_snapshot(item) for item in positions),
            pending_orders=tuple(_pending_snapshot(item) for item in pending_orders),
            features=features,
        )

    def _target_positions(self, intent: TradeIntent, positions: Sequence[SimPosition]) -> list[SimPosition]:
        if intent.target_position_ids:
            identifiers = set(intent.target_position_ids)
            return [position for position in positions if position.position_id in identifiers]
        return [  # pragma: no cover
            position
            for position in positions
            if position.symbol == intent.symbol
            and position.direction is intent.direction
            and (position.strategy_id == intent.strategy_id or position.magic_number == intent.magic_number)
        ]

    def _cancel_pending(self, intent: TradeIntent, pending_orders: list[SimPendingOrder]) -> int:
        if intent.target_pending_order_ids:
            identifiers = set(intent.target_pending_order_ids)
            before = len(pending_orders)
            pending_orders[:] = [order for order in pending_orders if order.order_id not in identifiers]
            return before - len(pending_orders)
        before = len(pending_orders)  # pragma: no cover
        pending_orders[:] = [  # pragma: no cover
            order  # pragma: no cover
            for order in pending_orders  # pragma: no cover
            if not (  # pragma: no cover
                order.symbol == intent.symbol  # pragma: no cover
                and order.direction is intent.direction  # pragma: no cover
                and (order.strategy_id == intent.strategy_id or order.magic_number == intent.magic_number)  # pragma: no cover
            )  # pragma: no cover
        ]  # pragma: no cover
        return before - len(pending_orders)  # pragma: no cover

    def _new_position(
        self,
        intent: TradeIntent,
        quantity: float,
        entry_price: float,
        now: datetime,
        bar_index: int,
        *,
        entry_commission: float,
    ) -> SimPosition:
        self._position_counter += 1
        protection = intent.protection
        stop, target = _initial_protection_prices(intent.direction, entry_price, protection)
        return SimPosition(
            position_id=f"pos-{self._position_counter:07d}",
            strategy_id=intent.strategy_id,
            symbol=intent.symbol,
            direction=intent.direction,
            quantity=quantity,
            entry_price=entry_price,
            opened_at=now,
            opened_bar_index=bar_index,
            magic_number=intent.magic_number,
            comment=intent.order_comment,
            stop_loss_price=stop,
            profit_target_price=target,
            trailing_distance=protection.trailing_distance,
            trailing_activation_distance=protection.trailing_activation_distance,
            time_exit_bars=protection.time_exit_bars,
            entry_commission=entry_commission,
        )

    def _close_position(
        self,
        position: SimPosition,
        quantity: float,
        exit_price: float,
        now: datetime,
        reason: FillReason,
        positions: list[SimPosition],
        closed_trades: list[ClosedTrade],
        balance: float,
    ) -> float:
        if quantity <= 0:
            return balance  # pragma: no cover
        quantity = min(quantity, position.quantity)
        original_quantity = position.quantity
        entry_commission = position.entry_commission * quantity / original_quantity
        exit_commission = quantity * self.config.commission_per_unit
        gross = _gross_pnl(position.direction, position.entry_price, exit_price, quantity, self.config.contract_size)
        net = gross - entry_commission - exit_commission
        self._trade_counter += 1
        closed_trades.append(
            ClosedTrade(
                trade_id=f"trade-{self._trade_counter:07d}",
                position_id=position.position_id,
                strategy_id=position.strategy_id,
                symbol=position.symbol,
                direction=position.direction,
                quantity=quantity,
                entry_time=position.opened_at,
                exit_time=now,
                entry_price=position.entry_price,
                exit_price=exit_price,
                gross_pnl=gross,
                net_pnl=net,
                entry_commission=entry_commission,
                exit_commission=exit_commission,
                reason=reason,
                magic_number=position.magic_number,
                comment=position.comment,
            )
        )
        balance += gross - exit_commission
        position.quantity -= quantity
        position.entry_commission -= entry_commission
        if position.quantity <= 1e-12:  # pragma: no cover
            positions.remove(position)
        return balance

    def _unrealized_pnl(self, positions: Sequence[SimPosition], quote: QuoteSnapshot) -> float:
        return sum(
            _gross_pnl(
                position.direction,
                position.entry_price,
                quote.exit_price(position.direction),
                position.quantity,
                self.config.contract_size,
            )
            for position in positions
        )

    def _quote(self, mid_price: float) -> QuoteSnapshot:
        half_spread = self.config.spread_price / 2.0
        return QuoteSnapshot(
            bid=mid_price - half_spread,
            ask=mid_price + half_spread,
            point_size=self.config.point_size,
        )

    def _side_ohlc(self, bar: Bar, direction: Direction, *, for_entry: bool) -> tuple[float, float, float, float]:
        half_spread = self.config.spread_price / 2.0
        # Long entry and short exit use ask.  Short entry and long exit use bid.
        use_ask = (direction is Direction.LONG and for_entry) or (direction is Direction.SHORT and not for_entry)
        adjustment = half_spread if use_ask else -half_spread
        return (
            bar.open + adjustment,
            bar.high + adjustment,
            bar.low + adjustment,
            bar.close + adjustment,
        )

    def _market_exit_price(self, quote: QuoteSnapshot, direction: Direction) -> float:
        price = quote.exit_price(direction)
        return price - self.config.slippage_price if direction is Direction.LONG else price + self.config.slippage_price

    def _protection_exit_price(self, bar: Bar, direction: Direction, trigger: float, *, is_stop: bool) -> float:
        open_price, _, _, _ = self._side_ohlc(bar, direction, for_entry=False)  # pragma: no cover
        if is_stop:  # pragma: no cover
            if direction is Direction.LONG:  # pragma: no cover
                return min(open_price, trigger) - self.config.slippage_price  # pragma: no cover
            return max(open_price, trigger) + self.config.slippage_price  # pragma: no cover
        if direction is Direction.LONG:  # pragma: no cover
            return max(open_price, trigger)  # pragma: no cover
        return min(open_price, trigger)  # pragma: no cover

    def _quantity(self, requested: float | None) -> float | None:
        value = self.config.default_quantity if requested is None else requested
        if value <= 0:
            return None  # pragma: no cover
        if value < self.config.volume_min - 1e-12:
            return None  # pragma: no cover
        bounded = min(value, self.config.volume_max)
        steps = floor((bounded - self.config.volume_min) / self.config.volume_step + 1e-9)
        return round(self.config.volume_min + steps * self.config.volume_step, 10)

    def _reset_ids(self) -> None:
        self._position_counter = 0
        self._order_counter = 0
        self._trade_counter = 0


def _initial_protection_prices(
    direction: Direction,
    entry_price: float,
    protection: ProtectionRequest,
) -> tuple[float | None, float | None]:
    stop = protection.stop_loss_price
    target = protection.profit_target_price
    if stop is None and protection.stop_loss_distance is not None:
        stop = entry_price - protection.stop_loss_distance if direction is Direction.LONG else entry_price + protection.stop_loss_distance  # pragma: no cover
    if target is None and protection.profit_target_distance is not None:
        target = entry_price + protection.profit_target_distance if direction is Direction.LONG else entry_price - protection.profit_target_distance  # pragma: no cover
    return stop, target


def _apply_protection_to_position(position: SimPosition, protection: ProtectionRequest) -> None:
    if protection.clear_stop_loss:
        position.stop_loss_price = None
    elif protection.stop_loss_price is not None:  # pragma: no cover
        position.stop_loss_price = protection.stop_loss_price  # pragma: no cover
    if protection.clear_profit_target:
        position.profit_target_price = None
    elif protection.profit_target_price is not None:  # pragma: no cover
        position.profit_target_price = protection.profit_target_price  # pragma: no cover
    if protection.trailing_distance is not None:  # pragma: no cover
        position.trailing_distance = protection.trailing_distance
    if protection.trailing_activation_distance is not None:  # pragma: no cover
        position.trailing_activation_distance = protection.trailing_activation_distance
    if protection.time_exit_bars is not None:  # pragma: no cover
        position.time_exit_bars = protection.time_exit_bars


def _position_snapshot(position: SimPosition) -> PositionSnapshot:
    return PositionSnapshot(
        position_id=position.position_id,
        symbol=position.symbol,
        direction=position.direction,
        quantity=position.quantity,
        strategy_id=position.strategy_id,
        magic_number=position.magic_number,
        entry_price=position.entry_price,
        stop_loss_price=position.stop_loss_price,
        profit_target_price=position.profit_target_price,
        comment=position.comment,
    )


def _pending_snapshot(order: SimPendingOrder) -> PendingOrderSnapshot:
    return PendingOrderSnapshot(
        order_id=order.order_id,
        symbol=order.symbol,
        direction=order.direction,
        entry_type=order.entry_type,
        price=order.requested_price,
        quantity=order.quantity,
        strategy_id=order.strategy_id,
        magic_number=order.magic_number,
        comment=order.comment,
    )


def _find_position(positions: Sequence[SimPosition], position_id: str) -> SimPosition | None:
    return next((position for position in positions if position.position_id == position_id), None)


def _gross_pnl(direction: Direction, entry_price: float, exit_price: float, quantity: float, contract_size: float) -> float:
    difference = exit_price - entry_price if direction is Direction.LONG else entry_price - exit_price
    return difference * quantity * contract_size


def _build_metrics(initial_balance: float, final_balance: float, closed: Sequence[ClosedTrade], equity_curve: Sequence[EquityPoint]) -> BacktestMetrics:
    wins = [trade for trade in closed if trade.net_pnl > 0]
    losses = [trade for trade in closed if trade.net_pnl < 0]
    gross_profit = sum(trade.net_pnl for trade in wins)
    gross_loss = sum(trade.net_pnl for trade in losses)
    profit_factor = gross_profit / abs(gross_loss) if gross_loss < 0 else None
    peak = initial_balance
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    for point in equity_curve:
        peak = max(peak, point.equity)
        drawdown = peak - point.equity
        max_drawdown = max(max_drawdown, drawdown)
        if peak > 0:  # pragma: no cover
            max_drawdown_pct = max(max_drawdown_pct, drawdown / peak * 100.0)
    total = len(closed)
    return BacktestMetrics(
        initial_balance=initial_balance,
        final_balance=final_balance,
        net_profit=final_balance - initial_balance,
        return_pct=((final_balance / initial_balance - 1.0) * 100.0) if initial_balance else 0.0,
        total_closed_trades=total,
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate_pct=(len(wins) / total * 100.0) if total else 0.0,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
    )


def _timeframe_duration(value: str) -> timedelta:
    normalized = value.strip().upper()
    units = {
        "M1": timedelta(minutes=1),
        "M2": timedelta(minutes=2),
        "M3": timedelta(minutes=3),
        "M4": timedelta(minutes=4),
        "M5": timedelta(minutes=5),
        "M10": timedelta(minutes=10),
        "M15": timedelta(minutes=15),
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
    try:
        return units[normalized]
    except KeyError as error:
        msg = f"Unsupported timeframe {value!r}; pass a supported MT-style timeframe."
        raise ValueError(msg) from error
