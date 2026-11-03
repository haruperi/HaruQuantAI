"""Shared ordered HSL event execution and isolated state transitions.

Description:
    Evaluates typed rules against a host snapshot and returns effects plus state.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: One strategy evaluator for all execution hosts.
Key Capabilities:
    - FR-hsl-event-execution: Log events, isolate state, and reject missing inputs.
Python API Usage:
    Call evaluate through StrategyRuntime with a compiled HSL document.
CLI Usage:
    uv run pytest tests/core/trading/strategy --no-cov
"""

from __future__ import annotations

import copy
import hashlib
import math
import operator
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, get_args
from zoneinfo import ZoneInfo

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.blocks.composition_runtime import CompositionExecutor
from app.core.trading.blocks.registry import BlockRegistry
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    EvaluationEvent,
    LifecycleEvent,
    StrategyContext,
    StrategyDocument,
    StrategyEffects,
)
from app.core.trading.strategy.hsl import models as hm
from app.core.trading.strategy.hsl.expressions import (
    Expressions,
    event_kind,
    event_time,
    fail,
)
from app.core.trading.strategy.hsl.orders import Orders
from app.core.trading.strategy.hsl.policies import apply_policies

logger = get_logger(__name__)


class EventExecution:
    """Pure event transaction: effects and state are published only on success."""

    def __init__(
        self,
        document: hm.HSLStrategyDocument,
        context: StrategyContext,
        event: EvaluationEvent,
        registry: BlockRegistry,
    ) -> None:
        self.document = document
        self.event = event
        self.state: dict[str, Any] = copy.deepcopy(dict(context.state))
        identity = hashlib.sha256(document.model_dump_json().encode()).hexdigest()
        if self.state.get("document", identity) != identity:
            fail("Execution state belongs to a different strategy revision")
        self.state["document"] = identity
        defaults = {
            name: spec.initial for name, spec in document.strategy.variables.items()
        }
        self.variables = self.state.setdefault("variables", defaults)
        options = document.strategy.trading_options
        day = (
            datetime.fromtimestamp(event_time(event), UTC)
            .astimezone(ZoneInfo(options.timezone))
            .date()
            .isoformat()
        )
        if self.state.get("day") != day or event_kind(event) == "on_session_open":
            for name, spec in document.strategy.variables.items():
                if spec.scope == "session":
                    self.variables[name] = spec.initial
            self.state.update(
                day=day, trades_today=0, day_equity=context.account_equity
            )
        params = {
            name: spec.default for name, spec in document.strategy.parameters.items()
        }
        self.expressions = Expressions(context, event, params, self.variables, registry)
        self.orders = Orders(self.expressions, document.strategy)
        self.expressions.context = replace(
            context, positions=tuple(self.orders.owned_positions())
        )
        self.alerts: list[dict[str, Any]] = []

    def condition(self, node: hm.ConditionNode, *, history: bool = True) -> bool:
        """Evaluate boolean trees and event-time histories without replaying state."""
        if isinstance(node, hm.BlockConditionNode):
            return self._condition_block(node, history)
        if isinstance(node, hm.LogicalConditionNode):
            fn = all if node.operator == "and" else any
            return fn(
                self.condition(child, history=history) for child in node.conditions
            )
        if isinstance(node, hm.NotConditionNode):
            return not self.condition(node.condition, history=history)
        if isinstance(node, hm.StateConditionNode):
            return self._condition_state(node, history)
        if isinstance(node, hm.TemporalConditionNode):
            return self._condition_temporal(node, history)
        return self._condition_comparison(node)

    def run(self) -> StrategyEffects:
        """Apply matching rules in priority/id order and publish a new state."""
        strategy = self.document.strategy
        if not strategy.enabled:
            return StrategyEffects(state_updates=self.state)
        kind = event_kind(self.event)
        if kind in ("on_start", "on_stop"):
            if self.state.get(kind):
                return StrategyEffects(state_updates=self.state)
            self.state[kind] = True
        logger.debug("FR-hsl-event-execution: strategy=%s event=%s", strategy.id, kind)
        for rule in sorted(strategy.rules, key=lambda item: (item.priority, item.id)):
            if not self._matches_rule(rule, kind):
                continue
            try:
                matches = self.condition(rule.when)
            except DomainError as error:
                if error.code != "HSL_WARMUP":
                    raise
                logger.debug("FR-hsl-event-execution: rule=%s warming up", rule.id)
                continue
            for action in rule.then if matches else rule.else_then:
                self._apply_action(action)
        apply_policies(self.orders, self.state)
        return StrategyEffects(
            orders_to_open=tuple(self.orders.entries),
            orders_to_cancel=tuple(self.orders.cancels),
            orders_to_modify=tuple(self.orders.modifications),
            positions_to_close=tuple(self.orders.closes),
            state_updates=self.state,
            alerts=tuple(self.alerts),
        )

    def _apply_action(self, action: hm.ActionNode) -> None:
        """Skip unavailable numeric samples without publishing invalid state."""
        try:
            self._execute_action(action)
        except DomainError as error:
            if error.code != "HSL_WARMUP":
                raise
            logger.debug("FR-hsl-event-execution: action requires warmup")

    def _matches_rule(self, rule: hm.RuleNode, kind: str) -> bool:
        """Match event kind and explicit symbol/timeframe filters."""
        trigger = rule.event
        return (
            rule.enabled
            and trigger.type == kind
            and trigger.symbol in ("$current_symbol", self.event.symbol)
            and trigger.timeframe
            in ("$current_timeframe", str(getattr(self.event, "timeframe", "")))
        )

    def _condition_block(self, node: Any, _history: bool) -> bool:
        """Evaluate the selected condition semantics."""
        from app.core.trading.strategy.hsl.value_models import EvaluationContext

        entry = self.expressions.library.require(node.block_id)
        descriptor = self.expressions.library.registry.require(entry.registry_id)
        target = descriptor.target
        if not isinstance(target, CompositionExecutor):
            fail("Condition requires a validated recipe executor")
        condition = descriptor.instantiate(**node.params)
        bars = self.expressions.feed(EvaluationContext())
        if len(bars) < target.required_history(**node.params):
            return False
        return bool(condition(bars))

    def _condition_state(self, node: Any, _history: bool) -> bool:
        """Evaluate the selected condition semantics."""
        positions = self.orders.owned_positions()
        if node.state == "position.is_flat":
            return not positions and (not self.orders.entries)
        if node.state in ("position.is_long", "position.is_short"):
            direction = 0 if node.state == "position.is_long" else 1
            return any(p.position_type == direction for p in positions)
        if node.state == "session.is_open":
            if self.expressions.context.session_open is None:
                fail("Session state requires an explicit host session snapshot")
            return bool(self.expressions.context.session_open)
        return bool(node.state == "always_true")

    def _condition_temporal(self, node: Any, history: bool) -> bool:
        """Evaluate the selected condition semantics."""
        if not isinstance(self.event, BarUpdateEvent):
            fail("Bar-based temporal conditions require bar events")
        key = hashlib.sha256(
            (
                node.model_dump_json() + self.event.symbol + str(self.event.timeframe)
            ).encode()
        ).hexdigest()
        samples = self.state.setdefault("temporal", {}).setdefault(key, [])
        stamp = event_time(self.event)
        value = self.condition(node.condition, history=history)
        if history:
            if samples and samples[-1][0] == stamp:
                samples[-1] = [stamp, value]
            else:
                samples.append([stamp, value])
            del samples[: -node.bars]
        if node.operator == "remains_true_for":
            return len(samples) >= node.bars and all(sample[1] for sample in samples)
        return any(sample[1] for sample in samples)

    def _condition_comparison(self, node: Any) -> bool:
        """Evaluate the selected condition semantics."""
        left = self.expressions.value(node.left)
        right = self.expressions.value(node.right)
        if any(
            isinstance(value, float) and (not math.isfinite(value))
            for value in (left, right)
        ):
            return False
        if node.operator in ("crosses_above", "crosses_below"):
            previous_left = self.expressions.value(node.left, 1)
            previous_right = self.expressions.value(node.right, 1)
            if any(
                isinstance(value, float) and (not math.isfinite(value))
                for value in (previous_left, previous_right)
            ):
                return False
            return bool(
                left > right and previous_left <= previous_right
                if node.operator == "crosses_above"
                else left < right and previous_left >= previous_right
            )
        return bool(
            {
                "greater_than": operator.gt,
                "greater_or_equal": operator.ge,
                "less_than": operator.lt,
                "less_or_equal": operator.le,
                "equal": operator.eq,
                "not_equal": operator.ne,
            }[node.operator](left, right)
        )

    def _execute_action(self, action: Any) -> None:
        """Validate a concrete executable capability."""
        strategy = self.document.strategy
        if isinstance(action, hm.VariableSetActionNode):
            value = self.expressions.value(action.value)
            expected = strategy.variables[action.name].type
            types: dict[str, Any] = {
                "int": int,
                "float": (int, float),
                "bool": bool,
                "str": str,
            }
            if not isinstance(value, types[expected]) or (
                expected != "bool" and isinstance(value, bool)
            ):
                fail(f"Invalid runtime value for variable {action.name}")
            if isinstance(value, float) and math.isnan(value):
                fail("Variable value is not available for this sample", "HSL_WARMUP")
            if isinstance(value, float) and not math.isfinite(value):
                fail("Variable assignment must be finite", "HSL_NONFINITE_STATE")
            self.variables[action.name] = value
            self.expressions.cache.clear()
        elif isinstance(action, hm.AlertActionNode):
            record = {"level": action.level, "message": action.message}
            self.alerts.append(record)
            getattr(logger, action.level)("FR-hsl-event-execution: %s", action.message)
        else:
            self.orders.execute(action)


def evaluate(
    plan: StrategyDocument,
    context: StrategyContext,
    event: EvaluationEvent,
    registry: BlockRegistry,
) -> StrategyEffects:
    """Evaluate the exact compiled document and reject changed block bindings."""
    from app.core.trading.strategy.hsl.capabilities import block_fingerprints
    from app.core.trading.strategy.hsl.documents import parse_hsl_document

    document = parse_hsl_document(plan.hsl_json or "")
    if isinstance(event, LifecycleEvent) and event.kind not in get_args(
        hm.LifecycleEventType
    ):
        fail("Unknown lifecycle event", "HSL_UNKNOWN_EVENT")
    actual = block_fingerprints(document, registry)
    if dict(plan.block_fingerprints) != actual:
        fail("Registered blocks changed; recompile the strategy", "HSL_STALE_PLAN")
    if isinstance(event, LifecycleEvent) and (not event.timeframe):
        event = replace(event, timeframe=document.strategy.timeframe.primary)
    return EventExecution(document, context, event, registry).run()
