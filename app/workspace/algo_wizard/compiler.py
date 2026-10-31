"""Deterministic HSL 1.0 strategy compiler and causal bar evaluation bridge.

Description:
    Lowers validated HSL 1.0 strategy AST documents into Core StrategyDocument
    execution plans for StrategyRuntime, evaluates HSL strategies causally
    bar-by-bar over BarEvent sequences, and normalizes HSL ASTs into
    NormalizedStrategy representations for multi-platform code generation.
Purpose:
    FEAT-WIZARD-COMPILER: Gate G4 (Phase 5.4, WO-WZ-HSL-COMPILER) compiler and
    runtime execution bridge for the HaruQuant Strategy Language (HSL 1.0).
Key Capabilities:
    - FR-wizard-hsl-runtime-lowering: Lowers validated HSLStrategyDocument ASTs
      into Core StrategyDocument instances with priority-ordered rules and
      inclusive prior-bar crossing conditions (<= and >=).
    - FR-wizard-hsl-causal-bar-evaluation: Evaluates compiled HSLStrategyDocument
      instances causally bar-by-bar over BarEvent sequences (shift >= 0) and
      returns emitted StrategyEffects per bar.
    - FR-wizard-hsl-normalized-lowering: Lowers validated HSLStrategyDocument
      ASTs into NormalizedStrategy representations for multi-platform export.
Python API Usage:
    from app.workspace.algo_wizard.compiler import StrategyCompiler
    compiler = StrategyCompiler()
    runtime_doc = compiler.compile_to_runtime(hsl_doc)
    normalized = compiler.compile_to_normalized(hsl_doc)
CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_compiler_and_runtime.py
"""

from __future__ import annotations

import hashlib
import json
import math
import operator
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

import numpy as np

from app.core.data.contracts import MarketBar, OrderInfo, PositionInfo
from app.core.enums import OrderType, Timeframe
from app.core.host.logging import get_logger
from app.core.trading.blocks.composition import composition_manifest
from app.core.trading.blocks.indicator import BaseIndicator
from app.core.trading.blocks.series import BarData
from app.core.trading.strategy import contracts as _sc
from app.core.trading.strategy.contracts import (
    ActionKind,
    BarUpdateEvent,
    ConditionDefinition,
    RuleAction,
    RuleTriggerKind,
    StrategyDocument,
    StrategyEffects,
)
from app.core.trading.strategy.runtime import StrategyRuntime
from app.core.wizard import transform as _wt
from app.core.wizard.transform import NormalizedCondition, NormalizedStrategy
from app.workspace.algo_wizard import models as _hm
from app.workspace.algo_wizard import value_models as _vm
from app.workspace.algo_wizard.library import WizardBlockLibrary
from app.workspace.algo_wizard.models import (
    ConditionNode,
    HSLStrategyDocument,
    RuleNode,
)
from app.workspace.algo_wizard.validation import StrategyValidator
from app.workspace.algo_wizard.value_models import OperandNode

logger = get_logger(__name__)
type BarEvent = BarUpdateEvent | MarketBar

_BASE_COMP_OPS: Mapping[str, str] = {
    "greater_than": ">",
    "greater_or_equal": ">=",
    "less_than": "<",
    "less_or_equal": "<=",
}
_RUNTIME_COMP_OPS: Mapping[str, str] = {
    **_BASE_COMP_OPS,
    "equal": "=",
    "not_equal": "<>",
}
_NORM_COMP_OPS: Mapping[str, str] = {**_BASE_COMP_OPS, "equal": "==", "not_equal": "!="}
_EL_COMP_OPS: Mapping[str, str] = {"==": "=", "!=": "<>"}
_TRIGGER_MAP: Mapping[str, RuleTriggerKind] = {
    "on_bar_close": RuleTriggerKind.ON_BAR_CLOSE,
    "on_bar_open": RuleTriggerKind.ON_BAR_OPEN,
    "on_tick": RuleTriggerKind.ON_TICK,
}
_CMP_FNS: Mapping[str, Callable[[Any, Any], bool]] = {
    "greater_than": lambda a, b: float(a) > float(b),
    "greater_or_equal": lambda a, b: float(a) >= float(b),
    "less_than": lambda a, b: float(a) < float(b),
    "less_or_equal": lambda a, b: float(a) <= float(b),
    "equal": operator.eq,
    "not_equal": operator.ne,
}
_MATH_FNS: Mapping[str, Callable[[float, float], float]] = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": lambda a, b: a / b if b != 0.0 else math.nan,
    "min": min,
    "max": max,
}
_P_SPEC: Mapping[str, tuple[str, str, str, str, Callable[[Any], Any]]] = {
    "int": ("int", "int", "int", "int", int),
    "bool": ("bool", "bool", "bool", "bool", bool),
    "str": ("str", "string", "string", "str", repr),
    "enum": ("str", "string", "string", "str", repr),
}


def _node_digest(node: Any, shift_delta: int = 0) -> str:
    payload = node.model_dump(mode="json") if hasattr(node, "model_dump") else str(node)
    raw = json.dumps({"node": payload, "s": shift_delta}, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _safe_id(name: str) -> str:
    c = re.sub(r"[^a-zA-Z0-9_]", "_", name) or "unnamed_strategy"
    return f"var_{c}" if c[0].isdigit() else c


def _operand_runtime_ref(node: OperandNode, shift_delta: int = 0) -> str | float:
    """Return a deterministic runtime reference or literal float for an OperandNode."""
    if isinstance(node, _vm.ValueLiteralNode):
        if isinstance(node.value, bool):
            return 1.0 if node.value else 0.0
        dig = _node_digest(node, shift_delta)
        return (
            float(node.value)
            if isinstance(node.value, (int, float))
            else f"__hsl_lit_{dig}"
        )
    if isinstance(node, (_vm.ParameterRefNode, _vm.VariableRefNode)):
        return node.name
    if isinstance(node, _vm.MarketPriceNode):
        s = node.context.shift + shift_delta
        ctx = node.context
        direct = (
            s == 0
            and node.field in ("open", "high", "low", "close", "volume")
            and (ctx.symbol, ctx.timeframe) == ("$current_symbol", "$current_timeframe")
        )
        return (
            node.field
            if direct
            else f"__hsl_price_{node.field}_s{s}_{_node_digest(node, shift_delta)}"
        )
    return f"__hsl_expr_s{shift_delta}_{_node_digest(node, shift_delta)}"


def _lower_condition_tree(node: ConditionNode) -> tuple[ConditionDefinition, ...]:
    if isinstance(node, _hm.ComparisonConditionNode):
        l0, r0 = _operand_runtime_ref(node.left, 0), _operand_runtime_ref(node.right, 0)
        if node.operator in ("crosses_above", "crosses_below"):
            l1 = _operand_runtime_ref(node.left, 1)
            r1 = _operand_runtime_ref(node.right, 1)
            op0, op1 = (">", "<=") if node.operator == "crosses_above" else ("<", ">=")
            return (ConditionDefinition(l0, op0, r0), ConditionDefinition(l1, op1, r1))
        return (ConditionDefinition(l0, _RUNTIME_COMP_OPS.get(node.operator, "="), r0),)
    if isinstance(node, _hm.LogicalConditionNode) and node.operator == "and":
        return tuple(d for c in node.conditions for d in _lower_condition_tree(c))
    return (ConditionDefinition(f"__hsl_cond_{_node_digest(node, 0)}", "=", 1.0),)


def _static_numeric(
    node: OperandNode | None,
    p: Mapping[str, Any],
    v: Mapping[str, Any],
    default: float = 0.0,
) -> float:
    if isinstance(node, _vm.ValueLiteralNode) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, _vm.ParameterRefNode) and isinstance(
        p.get(node.name), (int, float)
    ):
        return float(p[node.name])
    if isinstance(node, _vm.VariableRefNode) and isinstance(
        v.get(node.name), (int, float)
    ):
        return float(v[node.name])
    return default


def _resolve_sl_pips(
    sl: _vm.StopLossSpec | None, p: Mapping[str, Any], v: Mapping[str, Any]
) -> float:
    if sl is None:
        return 0.0
    if sl.type in ("fixed_pips", "fixed_points", "percent"):
        return _static_numeric(sl.value, p, v, 0.0)
    if sl.type in ("atr", "expression"):
        node = sl.multiplier if sl.type == "atr" else sl.expression
        return _static_numeric(node, p, v, 10.0) * (10.0 if sl.type == "atr" else 1.0)
    return 15.0 if sl.type == "indicator" else 0.0


def _resolve_tp_pips(
    tp: _vm.TakeProfitSpec | None,
    p: Mapping[str, Any],
    v: Mapping[str, Any],
    sl_pips: float,
) -> float:
    if tp is None:
        return 0.0
    if tp.type in ("fixed_pips", "fixed_points", "percent"):
        return _static_numeric(tp.value, p, v, 0.0)
    if tp.type == "risk_multiple":
        base = sl_pips if sl_pips > 0 else 10.0
        return base * _static_numeric(tp.multiple, p, v, 2.0)
    if tp.type in ("atr", "expression"):
        node = tp.multiplier if tp.type == "atr" else tp.expression
        return _static_numeric(node, p, v, 20.0) * (10.0 if tp.type == "atr" else 1.0)
    return 0.0


def _resolve_order_volume(
    size_node: _vm.MoneyManagementSpec | OperandNode | None,
    mm: _vm.MoneyManagementSpec,
    p: Mapping[str, Any],
    v: Mapping[str, Any],
) -> float:
    active_mm = size_node if isinstance(size_node, _vm.MoneyManagementSpec) else mm
    if size_node is not None and not isinstance(size_node, _vm.MoneyManagementSpec):
        return max(0.01, _static_numeric(size_node, p, v, 1.0))
    if active_mm.type == "fixed_size":
        return max(0.01, _static_numeric(active_mm.size, p, v, 1.0))
    if active_mm.type == "risk_percent":
        vol = max(0.01, _static_numeric(active_mm.risk_pct, p, v, 1.0) * 0.1)
        return min(vol, active_mm.max_lots) if active_mm.max_lots is not None else vol
    if active_mm.type == "percent_equity":
        return max(0.01, _static_numeric(active_mm.percent, p, v, 1.0) * 0.1)
    return 1.0


def _lower_action(
    act: _hm.ActionNode,
    mm: _vm.MoneyManagementSpec,
    params: Mapping[str, Any],
    variables: Mapping[str, Any],
) -> RuleAction | None:
    """Lower an HSL ActionNode into a Core RuleAction."""
    if isinstance(act, (_hm.OrderMarketActionNode, _hm.OrderPendingActionNode)):
        d = 1 if act.side == "long" else -1
        sl = _resolve_sl_pips(act.stop_loss, params, variables)
        tp = _resolve_tp_pips(act.take_profit, params, variables, sl)
        vol = _resolve_order_volume(act.size, mm, params, variables)
        if isinstance(act, _hm.OrderMarketActionNode):
            ot = OrderType.BUY if d == 1 else OrderType.SELL
            return RuleAction(
                ActionKind.ENTER, d, ot, vol, 0.0, sl, tp, comment=act.comment
            )
        s = act.action == "enter_stop"
        ot = (
            (OrderType.BUY_STOP if s else OrderType.BUY_LIMIT)
            if d == 1
            else (OrderType.SELL_STOP if s else OrderType.SELL_LIMIT)
        )
        off = _static_numeric(act.entry_price, params, variables, 0.0)
        atm = {"expiration_bars": act.expiration_bars} if act.expiration_bars else {}
        return RuleAction(
            ActionKind.ENTER,
            d,
            ot,
            vol,
            off,
            sl,
            tp,
            comment=act.comment,
            atm_rules=atm,
        )
    if isinstance(act, _hm.PositionCloseActionNode):
        d = {"long": 1, "short": -1, "any": 0}.get(act.target_side, 0)
        return RuleAction(
            ActionKind.EXIT, d, volume=act.quantity_pct / 100.0, comment=act.reason
        )
    if isinstance(act, _hm.OrderModifyActionNode):
        sl = _resolve_sl_pips(act.stop_loss, params, variables)
        tp = _resolve_tp_pips(act.take_profit, params, variables, sl)
        sl_p = sl if sl > 0 else 10.0
        return RuleAction(
            ActionKind.MODIFY, sl_price=sl_p, tp_price=tp, target_ticket="active"
        )
    if isinstance(act, _hm.OrderCancelActionNode):
        return RuleAction(ActionKind.CANCEL, target_ticket=None)
    return None


@dataclass
class _BarSimulationContext:
    """Mutable simulation state across bar-by-bar HSL evaluation."""

    document: HSLStrategyDocument
    events: tuple[BarUpdateEvent, ...]
    bar_data: BarData
    params: dict[str, Any]
    variables: dict[str, Any]
    positions: list[PositionInfo] = field(default_factory=list)
    orders: list[OrderInfo] = field(default_factory=list)
    pos_open_bar: dict[int, int] = field(default_factory=dict)
    indicator_cache: dict[str, dict[str, np.ndarray[Any, Any]]] = field(
        default_factory=dict
    )
    next_ticket: int = 1001


class StrategyCompiler:
    """Compiler lowering HSL 1.0 AST to StrategyRuntime and NormalizedStrategy."""

    def __init__(
        self,
        library: WizardBlockLibrary | None = None,
        validator: StrategyValidator | None = None,
    ) -> None:
        self._library = library if library is not None else WizardBlockLibrary()
        self._validator = validator or StrategyValidator(library=self._library)
        self._runtime = StrategyRuntime()
        self._calc_classes: dict[str, type[BaseIndicator]] = {}

    @property
    def library(self) -> WizardBlockLibrary:
        """Return the active WizardBlockLibrary."""
        return self._library

    @property
    def validator(self) -> StrategyValidator:
        """Return the active StrategyValidator."""
        return self._validator

    def compile_to_runtime(self, document: HSLStrategyDocument) -> StrategyDocument:
        """Validate and lower an HSLStrategyDocument into a Core StrategyDocument."""
        self._validator.validate(document, raise_on_error=True)
        strat = document.strategy
        p_map = {k: v.default for k, v in strat.parameters.items()}
        v_map = {k: v.initial for k, v in strat.variables.items()}
        mm = strat.money_management
        core_rules: list[_sc.RuleDefinition] = []
        for r in sorted(strat.rules, key=lambda item: (item.priority, item.id)):
            acts = tuple(
                a for act in r.then if (a := _lower_action(act, mm, p_map, v_map))
            )
            trig = _TRIGGER_MAP.get(r.event.type, RuleTriggerKind.ALL)
            conds = _lower_condition_tree(r.when)
            core_rules.append(
                _sc.RuleDefinition(r.id, r.name or r.id, trig, conds, acts, r.enabled)
            )
        p_defs = tuple(
            _sc.ParameterDefinition(k, v.type, v.default)
            for k, v in sorted(strat.parameters.items())
        )
        v_defs = tuple(
            _sc.VariableDefinition(k, v.type, v.initial)
            for k, v in sorted(strat.variables.items())
        )
        rev = strat.risk_management.allow_opposite_signals
        pol = (
            _sc.SignalConflictPolicy.REVERSE
            if rev
            else _sc.SignalConflictPolicy.FIRST_SIGNAL
        )
        setup = _sc.TradingSetupConfig(
            pol, strat.risk_management.max_open_positions, 1000
        )
        compiled = StrategyDocument(strat.id, tuple(core_rules), v_defs, p_defs, setup)
        logger.info(
            "FR-wizard-hsl-runtime-lowering: Compiled '%s' (%d rules)",
            strat.id,
            len(core_rules),
        )
        return compiled

    def evaluate_hsl_on_bars(
        self, document: HSLStrategyDocument, bars: Sequence[BarEvent]
    ) -> tuple[StrategyEffects, ...]:
        """Evaluate an HSLStrategyDocument causally across a BarEvent sequence."""
        runtime_doc = self.compile_to_runtime(document)
        if not bars:
            return ()
        events = self._normalize_bar_events(document, bars)
        bar_data = BarData.from_arrays(
            open=np.array([e.bar.open for e in events], dtype=np.float64),
            high=np.array([e.bar.high for e in events], dtype=np.float64),
            low=np.array([e.bar.low for e in events], dtype=np.float64),
            close=np.array([e.bar.close for e in events], dtype=np.float64),
            volume=np.array([e.bar.volume() for e in events], dtype=np.float64),
            timestamps=np.array([e.bar.time for e in events], dtype=np.int64),
        )
        p_map = {k: v.default for k, v in document.strategy.parameters.items()}
        v_map = {k: v.initial for k, v in document.strategy.variables.items()}
        sim = _BarSimulationContext(document, events, bar_data, p_map, v_map)
        rules = tuple(sorted(document.strategy.rules, key=lambda r: (r.priority, r.id)))
        effects_per_bar: list[StrategyEffects] = []
        for bar_idx, ev in enumerate(events):
            for pos in sim.positions:
                pos.price_current = ev.bar.close
                d = 1.0 if pos.position_type == 0 else -1.0
                pos.profit = (ev.bar.close - pos.price_open) * d * pos.volume * 100.0
            ctx_vars = dict(sim.variables)
            for rule in rules:
                if rule.enabled:
                    self._populate_condition_bindings(sim, rule.when, bar_idx, ctx_vars)
            ctx = _sc.StrategyContext(
                bars=bar_data,
                positions=tuple(sim.positions),
                orders=tuple(sim.orders),
                account_balance=10_000.0,
                variables=ctx_vars,
            )
            effects = self._runtime.evaluate(runtime_doc, ctx, ev)
            self._execute_rule_side_effects(sim, rules, ev, bar_idx)
            self._apply_portfolio_effects(sim, ev, bar_idx, effects)
            effects_per_bar.append(effects)
        logger.info(
            "FR-wizard-hsl-causal-bar-evaluation: Evaluated '%s' on %d bars",
            document.strategy.id,
            len(events),
        )
        return tuple(effects_per_bar)

    @staticmethod
    def _normalize_bar_events(
        document: HSLStrategyDocument, bars: Sequence[BarEvent]
    ) -> tuple[BarUpdateEvent, ...]:
        syms = document.strategy.universe.symbols
        sym = syms[0] if syms else "EURUSD"
        try:
            tf = Timeframe(document.strategy.timeframe.primary.strip().upper())
        except ValueError:
            tf = Timeframe.PERIOD_H1
        return tuple(
            b if isinstance(b, BarUpdateEvent) else BarUpdateEvent(sym, tf, b, True)
            for b in bars
        )

    def _populate_condition_bindings(
        self,
        sim: _BarSimulationContext,
        cond: ConditionNode,
        bar_idx: int,
        ctx_vars: dict[str, Any],
    ) -> None:
        if isinstance(cond, _hm.ComparisonConditionNode):
            shifts = (
                (0, 1) if cond.operator in ("crosses_above", "crosses_below") else (0,)
            )
            for s in shifts:
                for op in (cond.left, cond.right):
                    ref = _operand_runtime_ref(op, s)
                    if isinstance(ref, str) and ref.startswith("__hsl_"):
                        val = self._eval_operand(sim, op, bar_idx, s)
                        ctx_vars[ref] = (
                            float(val) if isinstance(val, (int, float)) else math.nan
                        )
            return
        if isinstance(cond, _hm.LogicalConditionNode) and cond.operator == "and":
            for child in cond.conditions:
                self._populate_condition_bindings(sim, child, bar_idx, ctx_vars)
            return
        ctx_vars[f"__hsl_cond_{_node_digest(cond, 0)}"] = (
            1.0 if self._eval_condition(sim, cond, bar_idx) else 0.0
        )

    def _eval_condition(
        self, sim: _BarSimulationContext, cond: ConditionNode, bar_idx: int
    ) -> bool:
        if isinstance(cond, _hm.LogicalConditionNode):
            fn = all if cond.operator == "and" else any
            return fn(self._eval_condition(sim, c, bar_idx) for c in cond.conditions)
        if isinstance(cond, _hm.NotConditionNode):
            return not self._eval_condition(sim, cond.condition, bar_idx)
        if isinstance(cond, _hm.StateConditionNode):
            return self._eval_state(sim, cond.state)
        if isinstance(cond, _hm.TemporalConditionNode):
            window = range(max(0, bar_idx - cond.bars + 1), bar_idx + 1)
            if cond.operator == "remains_true_for":
                return bar_idx + 1 >= cond.bars and all(
                    self._eval_condition(sim, cond.condition, idx) for idx in window
                )
            return any(self._eval_condition(sim, cond.condition, idx) for idx in window)
        return self._eval_comparison_condition(sim, cond, bar_idx)

    @staticmethod
    def _eval_state(sim: _BarSimulationContext, state: str) -> bool:
        if state == "position.is_flat":
            return len(sim.positions) == 0
        if state in ("position.is_long", "position.is_short"):
            target = 0 if state == "position.is_long" else 1
            return any(p.position_type == target for p in sim.positions)
        return state != "always_false"

    def _eval_comparison_condition(
        self,
        sim: _BarSimulationContext,
        cond: _hm.ComparisonConditionNode,
        bar_idx: int,
    ) -> bool:
        l0 = self._eval_operand(sim, cond.left, bar_idx, 0)
        r0 = self._eval_operand(sim, cond.right, bar_idx, 0)
        if (isinstance(l0, float) and math.isnan(l0)) or (
            isinstance(r0, float) and math.isnan(r0)
        ):
            return False
        if cond.operator in ("crosses_above", "crosses_below"):
            l1 = float(self._eval_operand(sim, cond.left, bar_idx, 1))
            r1 = float(self._eval_operand(sim, cond.right, bar_idx, 1))
            if math.isnan(l1) or math.isnan(r1):
                return False
            if cond.operator == "crosses_above":
                return float(l0) > float(r0) and l1 <= r1
            return float(l0) < float(r0) and l1 >= r1
        return _CMP_FNS[cond.operator](l0, r0)

    def _eval_operand(
        self,
        sim: _BarSimulationContext,
        node: OperandNode,
        bar_idx: int,
        shift_delta: int = 0,
    ) -> Any:
        leaf_cls = (
            _vm.ValueLiteralNode,
            _vm.ParameterRefNode,
            _vm.VariableRefNode,
            _vm.MarketPriceNode,
            _vm.PositionAttrNode,
        )
        if isinstance(node, leaf_cls):
            return self._eval_leaf_operand(sim, node, bar_idx, shift_delta)
        if isinstance(node, _vm.MathExpressionNode):
            l_val = float(self._eval_operand(sim, node.left, bar_idx, shift_delta))
            if math.isnan(l_val) or node.operator == "abs":
                return math.nan if math.isnan(l_val) else abs(l_val)
            r_raw = (
                self._eval_operand(sim, node.right, bar_idx, shift_delta)
                if node.right
                else math.nan
            )
            r_val = float(r_raw)
            return (
                math.nan
                if math.isnan(r_val)
                else _MATH_FNS[node.operator](l_val, r_val)
            )
        if isinstance(node, _vm.IndicatorExpressionNode):
            return self._eval_indicator_expression(sim, node, bar_idx, shift_delta)
        return self._eval_function_expression(sim, node, bar_idx, shift_delta)

    def _eval_leaf_operand(
        self, sim: _BarSimulationContext, node: Any, bar_idx: int, shift_delta: int
    ) -> Any:
        if isinstance(node, _vm.ValueLiteralNode):
            return node.value
        if isinstance(node, _vm.ParameterRefNode):
            return sim.params.get(node.name, math.nan)
        if isinstance(node, _vm.VariableRefNode):
            return sim.variables.get(node.name, math.nan)
        if isinstance(node, _vm.MarketPriceNode):
            idx = bar_idx - (node.context.shift + shift_delta)
            return self._eval_market_price(sim, node.field, idx)
        return self._eval_position_attr(sim, node, bar_idx)

    @staticmethod
    def _eval_market_price(
        sim: _BarSimulationContext, field_name: str, target_idx: int
    ) -> float:
        if target_idx < 0 or target_idx >= len(sim.events):
            return math.nan
        b = sim.events[target_idx].bar
        if field_name in ("open", "high", "low", "close"):
            return float(getattr(b, field_name))
        if field_name == "volume":
            return float(b.volume())
        hl = b.high + b.low
        if field_name == "median":
            return float(hl / 2.0)
        val = (
            (hl + b.close) / 3.0
            if field_name == "typical"
            else (hl + 2.0 * b.close) / 4.0
        )
        return float(val)

    @staticmethod
    def _eval_position_attr(
        sim: _BarSimulationContext, node: _vm.PositionAttrNode, bar_idx: int
    ) -> float:
        if not sim.positions:
            return 0.0
        pos = sim.positions[0]
        held = float(max(0, bar_idx - sim.pos_open_bar.get(pos.ticket, bar_idx)))
        side = 1.0 if pos.position_type == 0 else -1.0
        vals = {
            "size": pos.volume,
            "open_price": pos.price_open,
            "unrealized_pnl": pos.profit,
        }
        return float(vals.get(node.field, held if node.field == "bars_held" else side))

    def _eval_indicator_expression(
        self,
        sim: _BarSimulationContext,
        node: _vm.IndicatorExpressionNode,
        bar_idx: int,
        shift_delta: int,
    ) -> float:
        idx = bar_idx - (node.context.shift + shift_delta)
        if idx < 0 or idx >= len(sim.events):
            return math.nan
        outputs = self._get_or_compute_indicator_series(sim, node)
        if not outputs:
            return math.nan
        out = node.output
        if out not in outputs:
            hi = node.name.endswith("highest") and "highest" in outputs
            lo = node.name.endswith("lowest") and "lowest" in outputs
            out = "highest" if hi else ("lowest" if lo else next(iter(outputs.keys())))
        s = outputs.get(out)
        return float(s[idx]) if s is not None and idx < len(s) else math.nan

    def _get_or_compute_indicator_series(
        self, sim: _BarSimulationContext, node: _vm.IndicatorExpressionNode
    ) -> dict[str, np.ndarray[Any, Any]]:
        key = _node_digest(node, 0)
        if key in sim.indicator_cache:
            return sim.indicator_cache[key]
        entry = self._library.resolve(node.name)
        if entry is None:
            return {}
        params = self._resolve_indicator_params(sim, entry, node)
        bars = self._resolve_indicator_source_bars(sim, entry, node)
        cls = self._resolve_indicator_class(entry.registry_id)
        desc = self._library.registry.get(entry.registry_id)
        inst: Any = (
            cls(**params) if cls else (desc.instantiate(**params) if desc else None)
        )
        if isinstance(inst, BaseIndicator):
            raw = inst.calculate(bars)
            arr = {
                k: np.asarray(getattr(v, "values", v), dtype=np.float64)
                for k, v in raw.items()
            }
            sim.indicator_cache[key] = arr
            return arr
        return {}

    @staticmethod
    def _resolve_indicator_params(
        sim: _BarSimulationContext, entry: Any, node: _vm.IndicatorExpressionNode
    ) -> dict[str, Any]:
        res = {p.name: p.default for p in entry.parameters if p.default is not None}
        for k, v in node.params.items():
            if isinstance(v, _vm.ParameterRefNode):
                res[k] = sim.params.get(v.name, 0)
            elif isinstance(v, _vm.VariableRefNode):
                res[k] = sim.variables.get(v.name, 0)
            else:
                res[k] = v.value if isinstance(v, _vm.ValueLiteralNode) else v
        return res

    def _resolve_indicator_source_bars(
        self, sim: _BarSimulationContext, entry: Any, node: _vm.IndicatorExpressionNode
    ) -> BarData:
        if "source" not in node.inputs:
            return sim.bar_data
        src, n = node.inputs["source"], len(sim.events)
        vals = [float(self._eval_operand(sim, src, i, 0)) for i in range(n)]
        c = np.array(vals, dtype=np.float64)
        hl = entry.semantic_id in ("indicator.highest", "indicator.lowest")
        bd = sim.bar_data
        h, l_arr = (c, c) if hl else (bd.high, bd.low)
        kw: dict[str, Any] = {"open": bd.open, "high": h, "low": l_arr, "close": c}
        kw.update(volume=bd.volume, timestamps=bd.timestamps)
        return BarData.from_arrays(**kw)

    def _resolve_indicator_class(self, block_id: str) -> type[BaseIndicator] | None:
        if block_id in self._calc_classes:
            return self._calc_classes[block_id]
        calcs = composition_manifest().get("calculations", {})
        if isinstance(calcs, Mapping) and block_id in calcs:
            info = calcs[block_id]
            cls = getattr(import_module(str(info["module"])), str(info["class"]))
            if isinstance(cls, type) and issubclass(cls, BaseIndicator):
                self._calc_classes[block_id] = cls
                return cls
        return None

    def _eval_function_expression(
        self,
        sim: _BarSimulationContext,
        node: _vm.FunctionExpressionNode,
        bar_idx: int,
        shift_delta: int,
    ) -> Any:
        entry = self._library.resolve(node.name)
        desc = self._library.registry.get(entry.registry_id) if entry else None
        if desc is None or not callable(desc.target) or desc.is_class:
            return math.nan
        args = [self._eval_operand(sim, a, bar_idx, shift_delta) for a in node.args]
        return desc.target(*args)

    def _execute_rule_side_effects(
        self,
        sim: _BarSimulationContext,
        rules: Sequence[RuleNode],
        ev: BarUpdateEvent,
        bar_idx: int,
    ) -> None:
        for rule in rules:
            trig = _TRIGGER_MAP.get(rule.event.type, RuleTriggerKind.ALL)
            trig_ok = (
                trig == RuleTriggerKind.ALL
                or (trig == RuleTriggerKind.ON_BAR_CLOSE and ev.is_bar_close)
                or (trig == RuleTriggerKind.ON_BAR_OPEN and not ev.is_bar_close)
            )
            if not (rule.enabled and trig_ok):
                continue
            if not self._eval_condition(sim, rule.when, bar_idx):
                continue
            for act in rule.then:
                if isinstance(act, _hm.VariableSetActionNode):
                    val = self._eval_operand(sim, act.value, bar_idx, 0)
                    sim.variables[act.name] = val
                elif isinstance(act, _hm.AlertActionNode):
                    sid = sim.document.strategy.id
                    msg = act.message
                    logger.info("Strategy '%s' alert [%s]: %s", sid, act.level, msg)

    @staticmethod
    def _apply_portfolio_effects(
        sim: _BarSimulationContext,
        ev: BarUpdateEvent,
        bar_idx: int,
        effects: StrategyEffects,
    ) -> None:
        closed_ids = {str(c.ticket) for c in effects.positions_to_close}
        if closed_ids:
            sim.positions = [
                p for p in sim.positions if str(p.ticket) not in closed_ids
            ]
        canceled_ids = {str(cid) for cid in effects.orders_to_cancel}
        if canceled_ids:
            sim.orders = [o for o in sim.orders if str(o.ticket) not in canceled_ids]
        for mod_req in effects.orders_to_modify:
            for p in sim.positions:
                p.sl = mod_req.sl if mod_req.sl is not None else p.sl
                p.tp = mod_req.tp if mod_req.tp is not None else p.tp
        for req in effects.orders_to_open:
            t = sim.next_ticket
            sim.next_ticket += 1
            b: dict[str, Any] = {
                "ticket": t,
                "symbol": req.symbol,
                "price_open": req.price,
            }
            b.update(sl=req.sl, tp=req.tp, magic=req.magic, comment=req.comment)
            if req.order_type in (OrderType.BUY, OrderType.SELL):
                pt = 0 if req.direction == 1 else 1
                b.update(identifier=t, position_type=pt, volume=req.volume)
                b.update(price_current=req.price, time=ev.bar.time)
                sim.positions.append(PositionInfo(**b))
                sim.pos_open_bar[t] = bar_idx
            else:
                ot, v = int(req.order_type), req.volume
                b.update(order_type=ot, volume_initial=v, volume_current=v)
                b["time_setup"] = ev.bar.time
                sim.orders.append(OrderInfo(**b))

    def compile_to_normalized(
        self, document: HSLStrategyDocument
    ) -> NormalizedStrategy:
        """Validate and lower an HSLStrategyDocument into a NormalizedStrategy."""
        self._validator.validate(document, raise_on_error=True)
        strat = document.strategy
        p_map = {k: v.default for k, v in strat.parameters.items()}
        v_map = {k: v.initial for k, v in strat.variables.items()}
        mm = strat.money_management
        p_items = sorted(strat.parameters.items())
        v_items = sorted(strat.variables.items())
        norm_params = tuple(
            self._normalize_param(n, s.type, s.default) for n, s in p_items
        )
        norm_vars = tuple(self._normalize_var(n, s.type, s.initial) for n, s in v_items)
        norm_rules: list[_wt.NormalizedRule] = []
        for rule in sorted(strat.rules, key=lambda r: (r.priority, r.id)):
            conds = self._normalize_condition_node(rule.when)
            acts = tuple(
                self._normalize_rule_action(a)
                for act in rule.then
                if (a := _lower_action(act, mm, p_map, v_map)) is not None
            )
            c_mql = " && ".join(c.expr_mql for c in conds) or "true"
            c_el = " and ".join(c.expr_el for c in conds) or " true "
            c_cs = " && ".join(c.expr_cs for c in conds) or "true"
            c_py = " and ".join(c.expr_py for c in conds) or "True"
            r_id, ev_t, en = (
                _safe_id(rule.name or rule.id),
                rule.event.type,
                rule.enabled,
            )
            norm_rules.append(
                _wt.NormalizedRule(r_id, ev_t, conds, acts, en, c_mql, c_el, c_cs, c_py)
            )
        s_name = _safe_id(strat.name or strat.id)
        parts = [p[:1].upper() + p[1:] for p in s_name.split("_") if p]
        cls_name = "".join(parts) or "GeneratedStrategy"
        max_pos = strat.risk_management.max_open_positions
        r_tup = tuple(norm_rules)
        normalized = NormalizedStrategy(
            strat.id, s_name, cls_name, 1000, max_pos, norm_params, norm_vars, r_tup
        )
        logger.info(
            "FR-wizard-hsl-normalized-lowering: Normalized '%s' (%d rules)",
            strat.id,
            len(norm_rules),
        )
        return normalized

    @staticmethod
    def _normalize_param(name: str, p_type: str, val: Any) -> _wt.NormalizedParam:
        default_spec = ("float", "double", "double", "float", float)
        t0, t1, t2, t3, fn = _P_SPEC.get(p_type, default_spec)
        return _wt.NormalizedParam(_safe_id(name), t0, t1, t2, t3, fn(val))

    @staticmethod
    def _normalize_var(name: str, v_type: str, val: Any) -> _wt.NormalizedVar:
        default_spec = ("float", "double", "double", "float", float)
        t0, t1, _, t3, fn = _P_SPEC.get(v_type, default_spec)
        return _wt.NormalizedVar(_safe_id(name), t0, t1, t3, fn(val))

    def _normalize_condition_node(
        self, cond: ConditionNode
    ) -> tuple[NormalizedCondition, ...]:
        if isinstance(cond, _hm.ComparisonConditionNode):
            if cond.operator in ("crosses_above", "crosses_below"):
                op0, op1 = (
                    (">", "<=") if cond.operator == "crosses_above" else ("<", ">=")
                )
                c0 = self._format_binary_comparison(cond.left, op0, cond.right, 0)
                c1 = self._format_binary_comparison(cond.left, op1, cond.right, 1)
                return (c0, c1)
            sym = _NORM_COMP_OPS.get(cond.operator, "==")
            return (self._format_binary_comparison(cond.left, sym, cond.right, 0),)
        if isinstance(cond, _hm.LogicalConditionNode) and cond.operator == "and":
            return tuple(
                i for c in cond.conditions for i in self._normalize_condition_node(c)
            )
        if isinstance(cond, _hm.LogicalConditionNode) and cond.operator == "or":
            sub = [self._normalize_condition_node(c) for c in cond.conditions]
            return (self._join_cond_groups(sub, is_or=True),)
        if isinstance(cond, _hm.NotConditionNode):
            return (
                self._join_cond_groups(
                    [self._normalize_condition_node(cond.condition)], False
                ),
            )
        return (
            (self._format_state_condition(cond.state),)
            if isinstance(cond, _hm.StateConditionNode)
            else (NormalizedCondition("true", "true", "true", "True"),)
        )

    @staticmethod
    def _format_state_condition(state: str) -> NormalizedCondition:
        if state == "position.is_flat":
            py_flat = "context is None or not getattr(context, 'positions', ())"
            return NormalizedCondition(
                "!has_position", "MarketPosition = 0", "Positions.Count == 0", py_flat
            )
        el = (
            "MarketPosition > 0"
            if state == "position.is_long"
            else "MarketPosition < 0"
        )
        py_pos = "bool(getattr(context, 'positions', ()))"
        return NormalizedCondition("has_position", el, "Positions.Count > 0", py_pos)

    @staticmethod
    def _join_cond_groups(
        sub: Sequence[Sequence[NormalizedCondition]], is_or: bool = True
    ) -> NormalizedCondition:
        def _and(g: Sequence[NormalizedCondition], attr: str, sep: str) -> str:
            return sep.join(getattr(x, attr) for x in g)

        if is_or:
            return NormalizedCondition(
                "(" + " || ".join(_and(g, "expr_mql", " && ") for g in sub) + ")",
                "(" + " or ".join(_and(g, "expr_el", " and ") for g in sub) + ")",
                "(" + " || ".join(_and(g, "expr_cs", " && ") for g in sub) + ")",
                "(" + " or ".join(_and(g, "expr_py", " and ") for g in sub) + ")",
            )
        g0 = sub[0]
        return NormalizedCondition(
            f"!({_and(g0, 'expr_mql', ' && ')})",
            f"not ({_and(g0, 'expr_el', ' and ')})",
            f"!({_and(g0, 'expr_cs', ' && ')})",
            f"not ({_and(g0, 'expr_py', ' and ')})",
        )

    def _format_binary_comparison(
        self, left: OperandNode, sym: str, right: OperandNode, shift_delta: int
    ) -> NormalizedCondition:
        el_sym = _EL_COMP_OPS.get(sym, sym)
        platforms = ("mql", "el", "cs", "python")
        lv = [self._format_operand(left, p, shift_delta) for p in platforms]
        rv = [self._format_operand(right, p, shift_delta) for p in platforms]
        return NormalizedCondition(
            f"{lv[0]} {sym} {rv[0]}",
            f"{lv[1]} {el_sym} {rv[1]}",
            f"{lv[2]} {sym} {rv[2]}",
            f"{lv[3]} {sym} {rv[3]}",
        )

    def _format_operand(
        self, node: OperandNode, plat: str, shift_delta: int = 0
    ) -> str:
        leaf_cls = (
            _vm.MarketPriceNode,
            _vm.ValueLiteralNode,
            _vm.ParameterRefNode,
            _vm.VariableRefNode,
        )
        if isinstance(node, leaf_cls):
            return self._format_leaf_operand(node, plat)
        if isinstance(node, _vm.MathExpressionNode):
            return self._format_math_operand(node, plat, shift_delta)
        if isinstance(node, _vm.IndicatorExpressionNode):
            ind = _safe_id(node.name.split(".")[-1])
            s = node.context.shift + shift_delta
            if plat == "python":
                return f"float(getattr(context, '{ind}_s{s}', close_price))"
            return f"{ind}[{s}]" if plat == "el" else "close"
        if isinstance(node, _vm.FunctionExpressionNode):
            key = f"fn_{_safe_id(node.name.split('.')[-1])}"
        else:
            key = f"pos_{node.field}"
        return f"float(getattr(context, '{key}', 0.0))" if plat == "python" else "0.0"

    def _format_math_operand(
        self, node: _vm.MathExpressionNode, plat: str, shift_delta: int
    ) -> str:
        l_str = self._format_operand(node.left, plat, shift_delta)
        if node.operator == "abs":
            return f"abs({l_str})" if plat == "python" else f"MathAbs({l_str})"
        r_str = (
            self._format_operand(node.right, plat, shift_delta) if node.right else "0"
        )
        op_map = {"add": "+", "subtract": "-", "multiply": "*", "divide": "/"}
        if node.operator in op_map:
            return f"({l_str} {op_map[node.operator]} {r_str})"
        return f"{'min' if node.operator == 'min' else 'max'}({l_str}, {r_str})"

    @staticmethod
    def _format_leaf_operand(node: Any, plat: str) -> str:
        if isinstance(node, _vm.MarketPriceNode):
            f = (
                node.field
                if node.field in ("open", "high", "low", "close", "volume")
                else "close"
            )
            return f"{f}_price" if plat == "python" and f != "volume" else f
        if isinstance(node, _vm.ValueLiteralNode):
            if isinstance(node.value, bool):
                return str(node.value) if plat == "python" else str(node.value).lower()
            return str(node.value)
        ident = _safe_id(node.name)
        return f"self.{ident}" if plat == "python" else ident

    @staticmethod
    def _normalize_rule_action(act: RuleAction) -> _wt.NormalizedAction:
        sl, tp, buy = float(act.sl_pips), float(act.tp_pips), act.direction == 1
        s5, s4 = ("SYMBOL_ASK", "Ask") if buy else ("SYMBOL_BID", "Bid")
        op_sl, op_tp = ("-", "+") if buy else ("+", "-")
        p5 = f"SymbolInfoDouble(_Symbol, {s5})"
        sl5 = f"{p5} {op_sl} {sl} * _Point" if sl > 0 else "0"
        tp5 = f"{p5} {op_tp} {tp} * _Point" if tp > 0 else "0"
        sl4 = f"{s4} {op_sl} {sl} * Point" if sl > 0 else "0"
        tp4 = f"{s4} {op_tp} {tp} * Point" if tp > 0 else "0"
        k, d, v = str(act.kind.value), int(act.direction), float(act.volume)
        return _wt.NormalizedAction(
            k, d, v, sl, tp, sl5, tp5, sl4, tp4, str(act.comment or "HaruStrategy")
        )


__all__ = ["BarEvent", "StrategyCompiler"]
