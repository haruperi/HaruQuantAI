"""Deterministic strategy lifecycle, common SQX handling, and intent helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import datetime, time
from hashlib import sha256
from typing import Any

import pandas as pd

from app.services.strategy.config import StrategyConfig
from app.services.strategy.contracts import (
    Direction,
    EntryType,
    IntentAction,
    MarketContext,
    PendingOrderSnapshot,
    PositionSnapshot,
    ProtectionRequest,
    SignalSet,
    StrategyDecision,
    TradeIntent,
)
from app.services.strategy.state import StrategyState


class StrategyPermissionError(PermissionError):
    """Raised when a strategy is evaluated in an unpermitted environment."""


class BaseStrategy(ABC):
    """Base class for deterministic, config-driven broker-neutral strategies.

    Standard strategies implement ``calculate_signals`` and inherit the SQX-style
    long/short entry/exit resolver.  Complex translations may override
    ``build_custom_decision`` while retaining permissions, warm-up handling,
    idempotency, schedule filters, intent IDs, and persisted state.
    """

    def __init__(
        self, config: StrategyConfig, state: StrategyState | None = None
    ) -> None:
        self.config = config
        self.state = state or StrategyState()
        self.df_signals: pd.DataFrame | None = None

    def evaluate(self, context: MarketContext) -> StrategyDecision:
        """Evaluate the latest completed main-chart bar exactly once."""
        self._assert_runtime_permitted(context)
        if not context.bars:
            return StrategyDecision(
                None, SignalSet(), (), ("No completed bars supplied.",)
            )

        signal_time = context.signal_bar.open_time
        signal_key = signal_time.isoformat()
        if self.state.last_processed_signal_bar == signal_key:
            return StrategyDecision(
                signal_time,
                SignalSet(),
                (),
                ("Signal bar was already processed; no duplicate evaluation.",),
            )

        if len(context.bars) < self.required_warmup_bars:
            decision = StrategyDecision(
                signal_time,
                SignalSet(),
                (),
                (
                    f"Warm-up incomplete: received {len(context.bars)}, requires "
                    f"{self.required_warmup_bars}.",
                ),
            )
        elif self._is_in_cooldown(context):
            decision = StrategyDecision(
                signal_time, SignalSet(), (), ("Strategy cooldown is active.",)
            )
        else:
            scheduled = self._scheduled_exit_scope(context)
            if scheduled is not None:
                decision = StrategyDecision(
                    signal_time,
                    SignalSet(),
                    self._scheduled_exit_intents(context, scheduled),
                    ("Scheduled exit rule is active.",),
                )
            else:
                custom = self.build_custom_decision(context)
                decision = (
                    custom
                    if custom is not None
                    else self._build_standard_decision(context)
                )

        self._record_emitted_intents(context, decision.intents)
        return decision

    def evaluate_execution_event(
        self, context: MarketContext, event_id: str
    ) -> StrategyDecision:
        """Respond once to an execution event, for strategies with order ladders.

        The execution service calls this only after it has reconciled a meaningful
        broker event.  The strategy receives a fresh immutable snapshot and emits
        a new proposal; it does not infer fills from local optimistic state.
        """
        self._assert_runtime_permitted(context)
        if not event_id.strip():
            raise ValueError("event_id cannot be empty.")
        if event_id in self.state.processed_event_ids:
            return StrategyDecision(
                context.signal_bar.open_time if context.bars else None,
                SignalSet(),
                (),
                ("Execution event was already processed; no duplicate evaluation.",),
            )
        intents = self.build_execution_event_intents(context, event_id)
        self.state.processed_event_ids.add(event_id)
        self._record_intents_without_advancing_bar(context, intents)
        return StrategyDecision(
            context.signal_bar.open_time if context.bars else None,
            SignalSet(),
            tuple(intents),
        )

    @property
    def required_warmup_bars(self) -> int:
        """Return the configured number of complete bars needed before evaluation."""
        value = self.config.option("warmup_bars", default=0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(
                "trading_options.warmup_bars must be a non-negative integer."
            )
        return value

    @abstractmethod
    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate the signals in a vectorized way on the input DataFrame."""

    def precalculate_signals(self, context: MarketContext) -> None:
        """Precalculate and cache signals in a vectorized way from context bars."""
        if not context.bars:
            return

        if (
            self.df_signals is not None
            and len(self.df_signals) == len(context.bars) - 1
            and (
                len(self.df_signals) == 0
                or self.df_signals.index[-1] == context.bars[-2].open_time
            )
        ):
            new_bar = context.bars[-1]
            new_row = pd.DataFrame(
                {
                    "open": [new_bar.open],
                    "high": [new_bar.high],
                    "low": [new_bar.low],
                    "close": [new_bar.close],
                    "volume": [new_bar.volume],
                },
                index=[new_bar.open_time],
            )
            ohlcv_df = pd.concat(
                [self.df_signals[["open", "high", "low", "close", "volume"]], new_row]
            )
            self.df_signals = self.calculate_signals(ohlcv_df, context)
        else:
            df = pd.DataFrame(
                {
                    "open": [bar.open for bar in context.bars],
                    "high": [bar.high for bar in context.bars],
                    "low": [bar.low for bar in context.bars],
                    "close": [bar.close for bar in context.bars],
                    "volume": [bar.volume for bar in context.bars],
                },
                index=[bar.open_time for bar in context.bars],
            )
            self.df_signals = self.calculate_signals(df, context)

    def build_custom_decision(self, context: MarketContext) -> StrategyDecision | None:
        """Optionally replace standard signal/action resolution for complex EAs."""
        del context
        return None

    def build_execution_event_intents(
        self, context: MarketContext, event_id: str
    ) -> Sequence[TradeIntent]:
        """Optionally react to a reconciled broker fill/cancel/update event."""
        del context, event_id
        return ()

    def build_protection_request(
        self, context: MarketContext, direction: Direction
    ) -> ProtectionRequest:
        """Return strategy-proposed protection for the standard entry action."""
        del context, direction
        return ProtectionRequest()

    def on_order_update(
        self, intent_id: str, broker_order_id: str, status: str
    ) -> None:
        """Persist non-authoritative execution correlation for observability."""
        if not intent_id or not broker_order_id:
            raise ValueError("intent_id and broker_order_id cannot be empty.")
        self.state.open_signal_order_identifiers[intent_id] = broker_order_id
        if status.upper() in {"CANCELLED", "CANCELED", "REJECTED", "FILLED", "CLOSED"}:
            self.state.open_signal_order_identifiers.pop(intent_id, None)

    def _build_standard_decision(self, context: MarketContext) -> StrategyDecision:
        if self.df_signals is None or len(self.df_signals) < len(context.bars):
            self.precalculate_signals(context)

        current_idx = len(context.bars) - 1
        if self.df_signals is not None and 0 <= current_idx < len(self.df_signals):
            row = self.df_signals.iloc[current_idx]
            long_entry = bool(row["long_entry"])
            short_entry = bool(row["short_entry"])
            long_exit = bool(row["long_exit"])
            short_exit = bool(row["short_exit"])
        else:
            long_entry, short_entry, long_exit, short_exit = False, False, False, False

        raw_signals = SignalSet(
            long_entry=long_entry,
            short_entry=short_entry,
            long_exit=long_exit,
            short_exit=short_exit,
        )
        signals = self._resolve_signal_conflicts(raw_signals)
        intents = list(self._exit_intents(context, signals))
        diagnostics: list[str] = []
        if self._entries_allowed_now(context):
            entry = self._entry_intent(context, signals)
            if entry is not None:
                intents.append(entry)
        elif signals.long_entry or signals.short_entry:
            diagnostics.append(
                "Entry signal blocked by schedule or session restrictions."
            )
        return StrategyDecision(
            context.signal_bar.open_time, signals, tuple(intents), tuple(diagnostics)
        )

    def _assert_runtime_permitted(self, context: MarketContext) -> None:
        if context.runtime_mode.value not in self.config.permitted_environments:
            msg = (
                f"Strategy {self.config.strategy_id!r} is not permitted in "
                f"{context.runtime_mode.value!r}."
            )
            raise StrategyPermissionError(msg)

    def _record_emitted_intents(
        self, context: MarketContext, intents: Sequence[TradeIntent]
    ) -> None:
        self.state.last_processed_signal_bar = context.signal_bar.open_time.isoformat()
        self._record_intents_without_advancing_bar(context, intents)

    def _record_intents_without_advancing_bar(
        self, context: MarketContext, intents: Sequence[TradeIntent]
    ) -> None:
        for intent in intents:
            self.state.emitted_intent_ids.add(intent.intent_id)
            if intent.action is IntentAction.OPEN:
                day = intent.signal_time.date().isoformat()
                self.state.increment_entry_count(day)

    def _is_in_cooldown(self, context: MarketContext) -> bool:
        return (
            self.state.cooldown_until is not None
            and context.as_of < self.state.cooldown_until
        )

    def _entries_allowed_now(self, context: MarketContext) -> bool:
        return (
            not self._is_weekend_blocked(context.as_of)
            and self._is_time_range_allowed(context.as_of)
            and self._is_session_allowed(context.as_of)
        )

    def _can_open(
        self,
        context: MarketContext,
        direction: Direction,
        *,
        enforce_duplicate_policy: bool = True,
        enforce_daily_limit: bool = True,
    ) -> bool:
        """Apply shared entry gates; custom EAs can opt out per source behavior."""
        if not self._entries_allowed_now(context):
            return False
        if enforce_daily_limit:
            max_trades = self.config.option("max_trades_per_day", default=0)
            if isinstance(max_trades, int) and max_trades > 0:
                day = context.signal_bar.open_time.date().isoformat()
                if self.state.entry_count_for(day) >= max_trades:
                    return False
        return not (
            enforce_duplicate_policy
            and not self._duplicate_policy_allows(context, direction)
        )

    def _is_weekend_blocked(self, current: datetime) -> bool:
        weekend = self.config.option("schedule", "weekend", default={})
        if not isinstance(weekend, Mapping) or not weekend.get("enabled", False):
            return False
        start = _parse_weekly_point(weekend.get("start"), "schedule.weekend.start")
        end = _parse_weekly_point(weekend.get("end"), "schedule.weekend.end")
        value = current.weekday() * 1440 + current.hour * 60 + current.minute
        return start <= value < end if start <= end else value >= start or value < end

    def _is_time_range_allowed(self, current: datetime) -> bool:
        rule = self.config.option("signal_time_range", default={})
        if not isinstance(rule, Mapping) or not rule.get("enabled", False):
            return True
        start = _parse_time(rule.get("start"), "signal_time_range.start")
        end = _parse_time(rule.get("end"), "signal_time_range.end")
        now = current.timetz().replace(tzinfo=None)
        return start <= now < end if start <= end else now >= start or now < end

    def _is_session_allowed(self, current: datetime) -> bool:
        sessions = self.config.option("session_restrictions", default=[])
        if not sessions:
            return True
        if not isinstance(sessions, list):
            raise TypeError("trading_options.session_restrictions must be a list.")
        weekday = current.strftime("%A").upper()
        now = current.timetz().replace(tzinfo=None)
        for index, session in enumerate(sessions):
            if not isinstance(session, Mapping) or weekday not in session.get(
                "weekdays", []
            ):
                continue
            start = _parse_time(
                session.get("start"), f"session_restrictions[{index}].start"
            )
            end = _parse_time(session.get("end"), f"session_restrictions[{index}].end")
            if start <= now < end if start <= end else now >= start or now < end:
                return True
        return False

    def _scheduled_exit_scope(self, context: MarketContext) -> str | None:
        options = self.config.section("trading_options")
        eod = options.get("end_of_day_exit", {})
        if (
            isinstance(eod, Mapping)
            and eod.get("enabled", False)
            and context.as_of.timetz().replace(tzinfo=None)
            >= _parse_time(eod.get("time"), "end_of_day_exit.time")
        ):
            return f"eod:{context.as_of.date().isoformat()}"
        friday = options.get("friday_exit", {})
        if (
            isinstance(friday, Mapping)
            and friday.get("enabled", False)
            and context.as_of.weekday() == 4
            and context.as_of.timetz().replace(tzinfo=None)
            >= _parse_time(friday.get("time"), "friday_exit.time")
        ):
            return f"friday:{context.as_of.date().isoformat()}"
        return None

    def _scheduled_exit_intents(
        self, context: MarketContext, scope: str
    ) -> tuple[TradeIntent, ...]:
        positions = self._owned_positions(context)
        if not positions:
            return ()
        intents: list[TradeIntent] = []
        for direction in (Direction.LONG, Direction.SHORT):
            ids = tuple(p.position_id for p in positions if p.direction is direction)
            if ids:
                intents.append(
                    self._make_close_intent(
                        context,
                        direction,
                        ids,
                        operation_key=f"scheduled:{scope}:{direction}",
                    )
                )
        return tuple(intents)

    def _resolve_signal_conflicts(self, signals: SignalSet) -> SignalSet:
        long_entry, short_entry = signals.long_entry, signals.short_entry
        policy = self.config.section("action_rules").get(
            "direction_conflict_policy", "REJECT_BOTH"
        )
        if long_entry and short_entry:
            if policy == "LONG_PRIORITY":
                short_entry = False
            elif policy == "SHORT_PRIORITY":
                long_entry = False
            else:
                long_entry = short_entry = False
        entry_exit = self.config.section("action_rules").get(
            "entry_exit_conflict_policy", "ENTRY_PRIORITY"
        )
        long_exit, short_exit = signals.long_exit, signals.short_exit
        if entry_exit == "ENTRY_PRIORITY":
            if long_entry:
                long_exit = False
            if short_entry:
                short_exit = False
        elif entry_exit == "EXIT_PRIORITY":
            if long_exit:
                long_entry = False
            if short_exit:
                short_entry = False
        return SignalSet(long_entry, short_entry, long_exit, short_exit)

    def _exit_intents(
        self, context: MarketContext, signals: SignalSet
    ) -> tuple[TradeIntent, ...]:
        positions = self._owned_positions(context)
        intents: list[TradeIntent] = []
        if signals.long_exit:
            ids = tuple(
                p.position_id for p in positions if p.direction is Direction.LONG
            )
            if ids:
                intents.append(
                    self._make_close_intent(
                        context, Direction.LONG, ids, operation_key="long_signal_exit"
                    )
                )
        if signals.short_exit:
            ids = tuple(
                p.position_id for p in positions if p.direction is Direction.SHORT
            )
            if ids:
                intents.append(
                    self._make_close_intent(
                        context, Direction.SHORT, ids, operation_key="short_signal_exit"
                    )
                )
        return tuple(intents)

    def _entry_intent(
        self, context: MarketContext, signals: SignalSet
    ) -> TradeIntent | None:
        direction = (
            Direction.LONG
            if signals.long_entry
            else Direction.SHORT
            if signals.short_entry
            else None
        )
        if direction is None or not self._can_open(context, direction):
            return None
        action = self.config.section("action_rules").get(
            "long_entry_action"
            if direction is Direction.LONG
            else "short_entry_action",
            {},
        )
        if not isinstance(action, Mapping) or not action.get("enabled", True):
            return None
        return self._make_open_intent(
            context,
            direction,
            entry_type=EntryType(str(action.get("entry_type", "MARKET"))),
            protection=self.build_protection_request(context, direction),
            operation_key=f"standard:{direction}",
        )

    def _strategy_magic_numbers(self) -> set[int]:
        profile = self.config.section("trading_profile")
        values = profile.get("magic_numbers")
        if isinstance(values, list):
            return {int(item) for item in values}
        return {int(profile.get("magic_number", 0))}

    def _owned_positions(self, context: MarketContext) -> tuple[PositionSnapshot, ...]:
        magic_numbers = self._strategy_magic_numbers()
        return tuple(
            position
            for position in context.positions
            if position.symbol == context.symbol
            and (
                position.strategy_id == self.config.strategy_id
                or position.magic_number in magic_numbers
            )
        )

    def _owned_pending_orders(
        self, context: MarketContext
    ) -> tuple[PendingOrderSnapshot, ...]:
        magic_numbers = self._strategy_magic_numbers()
        return tuple(
            order
            for order in context.pending_orders
            if order.symbol == context.symbol
            and (
                order.strategy_id == self.config.strategy_id
                or order.magic_number in magic_numbers
            )
        )

    def _duplicate_policy_allows(
        self, context: MarketContext, direction: Direction
    ) -> bool:
        policy = self.config.section("action_rules").get(
            "duplicate_trade_policy", "ALLOW"
        )
        positions = self._owned_positions(context)
        if policy == "BLOCK_ANY_OWNED_POSITION":
            return not positions
        if policy == "BLOCK_SAME_DIRECTION":
            return not any(position.direction is direction for position in positions)
        return True

    def _make_open_intent(
        self,
        context: MarketContext,
        direction: Direction,
        *,
        entry_type: EntryType = EntryType.MARKET,
        protection: ProtectionRequest | None = None,
        requested_quantity: float | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
        comment: str | None = None,
        magic_number: int | None = None,
        operation_key: str,
        metadata: Mapping[str, object] | None = None,
    ) -> TradeIntent:
        return self._make_intent(
            context,
            action=IntentAction.OPEN,
            direction=direction,
            entry_type=entry_type,
            protection=protection or ProtectionRequest(),
            requested_quantity=requested_quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            comment=comment,
            magic_number=magic_number,
            operation_key=operation_key,
            metadata=metadata,
        )

    def _make_close_intent(
        self,
        context: MarketContext,
        direction: Direction,
        position_ids: tuple[str, ...],
        *,
        operation_key: str,
        comment: str | None = None,
    ) -> TradeIntent:
        return self._make_intent(
            context,
            action=IntentAction.CLOSE,
            direction=direction,
            entry_type=None,
            target_position_ids=position_ids,
            comment=comment,
            operation_key=operation_key,
        )

    def _make_partial_close_intent(
        self,
        context: MarketContext,
        direction: Direction,
        position_ids: tuple[str, ...],
        quantity: float,
        *,
        operation_key: str,
        comment: str | None = None,
    ) -> TradeIntent:
        return self._make_intent(
            context,
            action=IntentAction.PARTIAL_CLOSE,
            direction=direction,
            entry_type=None,
            target_position_ids=position_ids,
            requested_quantity=quantity,
            comment=comment,
            operation_key=operation_key,
        )

    def _make_modify_intent(
        self,
        context: MarketContext,
        direction: Direction,
        position_ids: tuple[str, ...],
        protection: ProtectionRequest,
        *,
        operation_key: str,
        comment: str | None = None,
    ) -> TradeIntent:
        return self._make_intent(
            context,
            action=IntentAction.MODIFY,
            direction=direction,
            entry_type=None,
            target_position_ids=position_ids,
            protection=protection,
            comment=comment,
            operation_key=operation_key,
        )

    def _make_cancel_pending_intent(
        self,
        context: MarketContext,
        direction: Direction,
        order_ids: tuple[str, ...],
        *,
        operation_key: str,
    ) -> TradeIntent:
        return self._make_intent(
            context,
            action=IntentAction.CANCEL_PENDING,
            direction=direction,
            entry_type=None,
            target_pending_order_ids=order_ids,
            operation_key=operation_key,
        )

    def _make_intent(
        self,
        context: MarketContext,
        *,
        action: IntentAction,
        direction: Direction,
        entry_type: EntryType | None,
        operation_key: str,
        protection: ProtectionRequest | None = None,
        target_position_ids: tuple[str, ...] = (),
        target_pending_order_ids: tuple[str, ...] = (),
        requested_quantity: float | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
        comment: str | None = None,
        magic_number: int | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> TradeIntent:
        signal_time = context.signal_bar.open_time
        magic = int(
            magic_number
            if magic_number is not None
            else self.config.section("trading_profile").get("magic_number", 0)
        )
        intent_id = self._intent_id(
            signal_time,
            action,
            direction,
            operation_key,
            target_position_ids,
            target_pending_order_ids,
        )
        risk = self.config.section("risk_management").get("strategy_sizing_hint", {})
        return TradeIntent(
            intent_id=intent_id,
            strategy_id=self.config.strategy_id,
            signal_time=signal_time,
            action=action,
            symbol=context.symbol,
            direction=direction,
            entry_type=entry_type,
            order_comment=comment
            or str(
                self.config.section("trading_profile").get(
                    "order_comment", self.config.strategy_id
                )
            ),
            magic_number=magic,
            protection=protection or ProtectionRequest(),
            target_position_ids=target_position_ids,
            target_pending_order_ids=target_pending_order_ids,
            requested_quantity=requested_quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            sizing_hint=risk if isinstance(risk, Mapping) else {},
            metadata=dict(metadata or {}),
        )

    def _intent_id(
        self,
        signal_time: datetime,
        action: IntentAction,
        direction: Direction,
        operation_key: str,
        position_ids: tuple[str, ...],
        pending_ids: tuple[str, ...],
    ) -> str:
        material = "|".join(
            (
                self.config.strategy_id,
                signal_time.isoformat(),
                action,
                direction,
                operation_key,
                ",".join(position_ids),
                ",".join(pending_ids),
            )
        )
        return sha256(material.encode("utf-8")).hexdigest()


def _parse_time(value: Any, name: str) -> time:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an HH:MM string.")
    try:
        hour, minute = (int(piece) for piece in value.split(":", maxsplit=1))
        return time(hour, minute)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be an HH:MM string.") from error


def _parse_weekly_point(value: Any, name: str) -> int:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object with weekday and time.")
    weekdays = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4,
        "SATURDAY": 5,
        "SUNDAY": 6,
    }
    day = value.get("weekday")
    if day not in weekdays:
        raise ValueError(f"{name}.weekday must be a weekday name.")
    parsed = _parse_time(value.get("time"), f"{name}.time")
    return weekdays[day] * 1440 + parsed.hour * 60 + parsed.minute
