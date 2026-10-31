"""Three-pass HSL 1.0 AST structural, BlockRegistry, and static type validator.

Description:
    Implements the three-pass validation pipeline for HaruQuant Strategy
    Language (HSL 1.0) documents:
    - Pass 1: Structural & schema integrity (unique rule IDs, parameter bounds,
      raw code prohibition).
    - Pass 2: BlockRegistry & reference integrity (indicator/function lookup,
      parameter range validation, parameter/variable reference existence).
    - Pass 3: Bottom-up static type inference and temporal lookahead safety
      (shift >= 0, higher-timeframe on_bar_open shift >= 1, declared symbols
      and timeframes).

Purpose:
    FEAT-WIZARD-VALIDATION: Fail-closed static verification of HSL 1.0 strategy
    ASTs before compilation, backtesting, or live execution.

Key Capabilities:
    - FR-wizard-pass1-structural: Verifies schema, unique rule IDs, and
      parameter min/default/max invariants.
    - FR-wizard-pass2-registry-refs: Verifies indicator/function block IDs and
      parameter bounds against WizardBlockLibrary and checks parameter/variable
      references.
    - FR-wizard-pass3-type-and-lookahead: Infers operand types bottom-up and
      rejects negative shifts or undeclared symbol/timeframe contexts.

Python API Usage:
    from app.workspace.algo_wizard.validation import StrategyValidator

    validator = StrategyValidator()
    report = validator.validate(hsl_document)

CLI Usage:
    python -c "from app.workspace.algo_wizard import validation; print(1)"
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.workspace.algo_wizard.catalogue_models import (
    CatalogueParameterBounds,
    HSLBlockCatalogueEntry,
    StaticReturnType,
)
from app.workspace.algo_wizard.documents import parse_hsl_document
from app.workspace.algo_wizard.library import WizardBlockLibrary
from app.workspace.algo_wizard.models import (
    ActionNode,
    ComparisonConditionNode,
    ConditionNode,
    HSLStrategyDocument,
    HSLStrategyPayload,
    LogicalConditionNode,
    NotConditionNode,
    OrderMarketActionNode,
    OrderModifyActionNode,
    OrderPendingActionNode,
    ParameterSpec,
    RuleNode,
    TemporalConditionNode,
    VariableSetActionNode,
)
from app.workspace.algo_wizard.value_models import (
    EvaluationContext,
    FunctionExpressionNode,
    IndicatorExpressionNode,
    MarketPriceNode,
    MathExpressionNode,
    MoneyManagementSpec,
    OperandNode,
    ParameterRefNode,
    PositionAttrNode,
    ScalarLiteral,
    StopLossSpec,
    TakeProfitSpec,
    ValueLiteralNode,
    VariableRefNode,
)

logger = get_logger(__name__)

_NUMERIC_TYPES: frozenset[str] = frozenset({"int", "float", "price", "series"})


class ValidationIssue(BaseModel):
    """Single diagnostic error detected during HSL 1.0 AST validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(..., min_length=1, description="Machine-readable error code")
    message: str = Field(..., min_length=1, description="Diagnostic explanation")
    path: str = Field(..., min_length=1, description="JSONPath location in AST")
    node_id: str | None = Field(
        default=None,
        description="Optional enclosing rule or block identifier",
    )


class ValidationReport(BaseModel):
    """Result of executing the 3-pass StrategyValidator over an HSL document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    valid: bool = Field(..., description="True when zero validation issues exist")
    issues: tuple[ValidationIssue, ...] = Field(
        default_factory=tuple,
        description="Ordered validation issues across Passes 1, 2, and 3",
    )


def _is_numeric_scalar(val: Any) -> bool:
    """Return True if val is an int or float and not a boolean."""
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _types_compatible(expected: str, actual: str) -> bool:
    """Check whether an actual inferred return type satisfies expected type."""
    if expected == actual:
        return True
    return expected in _NUMERIC_TYPES and actual in _NUMERIC_TYPES


def _scalar_static_type(val: ScalarLiteral) -> StaticReturnType:
    """Return the StaticReturnType for a raw Python scalar."""
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, int):
        return "int"
    if isinstance(val, float):
        return "float"
    return "str"


class _ValidationSession:
    """Stateful collector running Passes 1, 2, and 3 over an HSLStrategyPayload."""

    def __init__(
        self,
        strategy: HSLStrategyPayload,
        library: WizardBlockLibrary,
    ) -> None:
        self.strategy = strategy
        self.library = library
        self.issues: list[ValidationIssue] = []
        self._declared_symbols: frozenset[str] = frozenset(
            {"$current_symbol", *strategy.universe.symbols}
        )
        self._declared_timeframes: frozenset[str] = frozenset(
            {
                "$current_timeframe",
                strategy.timeframe.primary,
                *strategy.timeframe.additional,
            }
        )

    def add_issue(
        self,
        code: str,
        message: str,
        path: str,
        node_id: str | None = None,
    ) -> None:
        """Append a ValidationIssue to the session report."""
        self.issues.append(
            ValidationIssue(
                code=code,
                message=message,
                path=path,
                node_id=node_id,
            )
        )

    def _check_parameter_spec(self, name: str, param: ParameterSpec) -> None:
        """Check numeric bounds on a single strategy parameter definition."""
        if param.type not in {"int", "float"}:
            return
        p_path = f"$.strategy.parameters.{name}"
        if not _is_numeric_scalar(param.default):
            self.add_issue(
                "WIZARD_INVALID_PARAMETER_BOUNDS",
                f"Numeric parameter '{name}' has non-numeric default.",
                f"{p_path}.default",
            )
            return
        default_num = float(param.default)
        if (
            param.min is not None
            and param.max is not None
            and float(param.min) > float(param.max)
        ):
            self.add_issue(
                "WIZARD_INVALID_PARAMETER_BOUNDS",
                (f"Parameter '{name}' min ({param.min}) exceeds max ({param.max})."),
                p_path,
            )
        if param.min is not None and default_num < float(param.min):
            self.add_issue(
                "WIZARD_INVALID_PARAMETER_BOUNDS",
                (
                    f"Parameter '{name}' default ({param.default}) is below "
                    f"min ({param.min})."
                ),
                f"{p_path}.default",
            )
        if param.max is not None and default_num > float(param.max):
            self.add_issue(
                "WIZARD_INVALID_PARAMETER_BOUNDS",
                (
                    f"Parameter '{name}' default ({param.default}) exceeds "
                    f"max ({param.max})."
                ),
                f"{p_path}.default",
            )

    def run_pass1_structural(self) -> None:
        """Pass 1: Check unique rule IDs and parameter default/min/max bounds."""
        seen_rules: set[str] = set()
        for idx, rule in enumerate(self.strategy.rules):
            if rule.id in seen_rules:
                self.add_issue(
                    "WIZARD_DUPLICATE_RULE_ID",
                    f"Duplicate rule id '{rule.id}' at index {idx}.",
                    f"$.strategy.rules[{idx}].id",
                    node_id=rule.id,
                )
            seen_rules.add(rule.id)

        for name, param in self.strategy.parameters.items():
            self._check_parameter_spec(name, param)

    def _validate_context(
        self,
        ctx: EvaluationContext,
        path: str,
        node_id: str | None,
        rule_event: str | None,
    ) -> None:
        """Pass 3 helper: Verify lookahead-safe shift and declared symbol/timeframe."""
        if ctx.shift < 0:
            self.add_issue(
                "WIZARD_LOOKAHEAD_SHIFT_INVALID",
                (
                    f"Negative shift ({ctx.shift}) is prohibited to prevent "
                    "future lookahead."
                ),
                f"{path}.context.shift",
                node_id=node_id,
            )
        elif (
            rule_event == "on_bar_open"
            and ctx.timeframe
            not in {"$current_timeframe", self.strategy.timeframe.primary}
            and ctx.shift < 1
        ):
            self.add_issue(
                "WIZARD_LOOKAHEAD_SHIFT_INVALID",
                (
                    f"Higher timeframe '{ctx.timeframe}' referenced inside an "
                    "'on_bar_open' rule requires shift >= 1."
                ),
                f"{path}.context.shift",
                node_id=node_id,
            )

        if ctx.symbol not in self._declared_symbols:
            self.add_issue(
                "WIZARD_UNDECLARED_CONTEXT_REF",
                f"Symbol '{ctx.symbol}' is not declared in strategy.universe.",
                f"{path}.context.symbol",
                node_id=node_id,
            )
        if ctx.timeframe not in self._declared_timeframes:
            self.add_issue(
                "WIZARD_UNDECLARED_CONTEXT_REF",
                f"Timeframe '{ctx.timeframe}' is not declared in strategy.timeframe.",
                f"{path}.context.timeframe",
                node_id=node_id,
            )

    def _check_param_bound_value(
        self,
        *,
        block_name: str,
        param_key: str,
        bound_spec: CatalogueParameterBounds,
        inferred_type: StaticReturnType,
        resolved_scalar: ScalarLiteral | None,
        param_path: str,
        node_id: str | None,
    ) -> None:
        """Verify parameter type compatibility and min/max numeric range."""
        if not _types_compatible(bound_spec.param_type, inferred_type):
            self.add_issue(
                "WIZARD_INVALID_BLOCK_PARAM",
                (
                    f"Parameter '{param_key}' on '{block_name}' expects "
                    f"'{bound_spec.param_type}', got '{inferred_type}'."
                ),
                param_path,
                node_id=node_id,
            )
            return
        if not _is_numeric_scalar(resolved_scalar):
            return
        num_val = float(resolved_scalar)  # type: ignore[arg-type]
        if bound_spec.min_value is not None and num_val < float(bound_spec.min_value):
            self.add_issue(
                "WIZARD_INVALID_BLOCK_PARAM",
                (
                    f"Parameter '{param_key}'={resolved_scalar} on "
                    f"'{block_name}' is below minimum {bound_spec.min_value}."
                ),
                param_path,
                node_id=node_id,
            )
        if bound_spec.max_value is not None and num_val > float(bound_spec.max_value):
            self.add_issue(
                "WIZARD_INVALID_BLOCK_PARAM",
                (
                    f"Parameter '{param_key}'={resolved_scalar} on "
                    f"'{block_name}' exceeds maximum {bound_spec.max_value}."
                ),
                param_path,
                node_id=node_id,
            )

    def _validate_indicator_params(
        self,
        node: IndicatorExpressionNode,
        entry: HSLBlockCatalogueEntry,
        path: str,
        node_id: str | None,
        rule_event: str | None,
    ) -> None:
        """Pass 2 & 3 helper: Validate indicator parameters against registry bounds."""
        bounds_by_name = {b.name: b for b in entry.parameters}
        for bound in entry.parameters:
            if bound.required and bound.name not in node.params:
                self.add_issue(
                    "WIZARD_INVALID_BLOCK_PARAM",
                    f"Missing required parameter '{bound.name}' for '{node.name}'.",
                    f"{path}.params",
                    node_id=node_id,
                )

        for param_key, param_val in node.params.items():
            param_path = f"{path}.params.{param_key}"
            if bounds_by_name and param_key not in bounds_by_name:
                self.add_issue(
                    "WIZARD_INVALID_BLOCK_PARAM",
                    f"Unknown parameter '{param_key}' for block '{node.name}'.",
                    param_path,
                    node_id=node_id,
                )
                continue

            resolved_scalar: ScalarLiteral | None = None
            if isinstance(param_val, (bool, int, float, str)):
                resolved_scalar = param_val
                inferred_type = _scalar_static_type(param_val)
            else:
                inferred_type = self._validate_operand(
                    param_val, param_path, node_id, rule_event
                )
                if isinstance(param_val, ValueLiteralNode):
                    resolved_scalar = param_val.value
                elif (
                    isinstance(param_val, ParameterRefNode)
                    and param_val.name in self.strategy.parameters
                ):
                    resolved_scalar = self.strategy.parameters[param_val.name].default

            bound_spec = bounds_by_name.get(param_key)
            if bound_spec is not None:
                self._check_param_bound_value(
                    block_name=node.name,
                    param_key=param_key,
                    bound_spec=bound_spec,
                    inferred_type=inferred_type,
                    resolved_scalar=resolved_scalar,
                    param_path=param_path,
                    node_id=node_id,
                )

    def _validate_indicator_node(
        self,
        node: IndicatorExpressionNode,
        path: str,
        node_id: str | None,
        rule_event: str | None,
    ) -> StaticReturnType:
        """Validate an IndicatorExpressionNode and return its StaticReturnType."""
        self._validate_context(node.context, path, node_id, rule_event)
        for in_key, in_operand in node.inputs.items():
            in_type = self._validate_operand(
                in_operand, f"{path}.inputs.{in_key}", node_id, rule_event
            )
            if in_type not in _NUMERIC_TYPES:
                self.add_issue(
                    "WIZARD_TYPE_MISMATCH",
                    f"Indicator input '{in_key}' must be numeric, got '{in_type}'.",
                    f"{path}.inputs.{in_key}",
                    node_id=node_id,
                )

        entry = self.library.resolve(node.name)
        if entry is None:
            self.add_issue(
                "WIZARD_UNKNOWN_BLOCK_ID",
                f"Indicator block '{node.name}' is not registered in BlockRegistry.",
                f"{path}.name",
                node_id=node_id,
            )
            for p_key, p_val in node.params.items():
                if not isinstance(p_val, (bool, int, float, str)):
                    self._validate_operand(
                        p_val, f"{path}.params.{p_key}", node_id, rule_event
                    )
            return "float"

        self._validate_indicator_params(node, entry, path, node_id, rule_event)
        return entry.return_type

    def _validate_math_node(
        self,
        node: MathExpressionNode,
        path: str,
        node_id: str | None,
        rule_event: str | None,
    ) -> StaticReturnType:
        """Validate a MathExpressionNode and return its StaticReturnType."""
        left_type = self._validate_operand(
            node.left, f"{path}.left", node_id, rule_event
        )
        if left_type not in _NUMERIC_TYPES:
            self.add_issue(
                "WIZARD_TYPE_MISMATCH",
                (
                    f"Math operator '{node.operator}' requires numeric left "
                    f"operand, got '{left_type}'."
                ),
                f"{path}.left",
                node_id=node_id,
            )
        if node.right is not None:
            right_type = self._validate_operand(
                node.right, f"{path}.right", node_id, rule_event
            )
            if right_type not in _NUMERIC_TYPES:
                self.add_issue(
                    "WIZARD_TYPE_MISMATCH",
                    (
                        f"Math operator '{node.operator}' requires numeric right "
                        f"operand, got '{right_type}'."
                    ),
                    f"{path}.right",
                    node_id=node_id,
                )
        return "float"

    def _validate_leaf_value_node(
        self,
        node: ValueLiteralNode
        | ParameterRefNode
        | VariableRefNode
        | MarketPriceNode
        | PositionAttrNode,
        path: str,
        node_id: str | None,
        rule_event: str | None,
    ) -> StaticReturnType:
        """Validate a leaf VALUE or PositionAttrNode and return its StaticReturnType."""
        if isinstance(node, ValueLiteralNode):
            return node.value_type or "float"
        if isinstance(node, ParameterRefNode):
            param_spec = self.strategy.parameters.get(node.name)
            if param_spec is None:
                self.add_issue(
                    "WIZARD_UNKNOWN_PARAMETER_REF",
                    f"Parameter '{node.name}' is not defined in strategy.parameters.",
                    f"{path}.name",
                    node_id=node_id,
                )
            return param_spec.type if param_spec is not None else "float"
        if isinstance(node, VariableRefNode):
            var_spec = self.strategy.variables.get(node.name)
            if var_spec is None:
                self.add_issue(
                    "WIZARD_UNKNOWN_VARIABLE_REF",
                    f"Variable '{node.name}' is not defined in strategy.variables.",
                    f"{path}.name",
                    node_id=node_id,
                )
            return var_spec.type if var_spec is not None else "float"
        if isinstance(node, MarketPriceNode):
            self._validate_context(node.context, path, node_id, rule_event)
            return "float"
        return (
            "str"
            if node.field == "side"
            else ("int" if node.field == "bars_held" else "float")
        )

    def _validate_operand(
        self,
        node: OperandNode,
        path: str,
        node_id: str | None,
        rule_event: str | None = None,
    ) -> StaticReturnType:
        """Validate an OperandNode (Passes 2 & 3) and return its static return type."""
        if isinstance(node, IndicatorExpressionNode):
            return self._validate_indicator_node(node, path, node_id, rule_event)
        if isinstance(node, MathExpressionNode):
            return self._validate_math_node(node, path, node_id, rule_event)
        if isinstance(node, FunctionExpressionNode):
            entry = self.library.resolve(node.name)
            if entry is None:
                self.add_issue(
                    "WIZARD_UNKNOWN_BLOCK_ID",
                    f"Function block '{node.name}' is not registered in BlockRegistry.",
                    f"{path}.name",
                    node_id=node_id,
                )
            for idx, arg in enumerate(node.args):
                self._validate_operand(arg, f"{path}.args[{idx}]", node_id, rule_event)
            return entry.return_type if entry is not None else "float"
        return self._validate_leaf_value_node(node, path, node_id, rule_event)

    def _require_numeric_operand(
        self,
        node: OperandNode | None,
        path: str,
        node_id: str | None = None,
        rule_event: str | None = None,
    ) -> None:
        """Validate an optional operand and require its return type to be numeric."""
        if node is None:
            return
        inferred = self._validate_operand(node, path, node_id, rule_event)
        if inferred not in _NUMERIC_TYPES:
            self.add_issue(
                "WIZARD_TYPE_MISMATCH",
                f"Expected numeric operand at '{path}', got '{inferred}'.",
                path,
                node_id=node_id,
            )

    def _validate_stop_loss(
        self,
        spec: StopLossSpec | None,
        path: str,
        node_id: str | None = None,
        rule_event: str | None = None,
    ) -> None:
        if spec is None:
            return
        self._require_numeric_operand(spec.value, f"{path}.value", node_id, rule_event)
        self._require_numeric_operand(
            spec.period, f"{path}.period", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.multiplier, f"{path}.multiplier", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.expression, f"{path}.expression", node_id, rule_event
        )
        if spec.indicator is not None:
            self._require_numeric_operand(
                spec.indicator, f"{path}.indicator", node_id, rule_event
            )

    def _validate_take_profit(
        self,
        spec: TakeProfitSpec | None,
        path: str,
        node_id: str | None = None,
        rule_event: str | None = None,
    ) -> None:
        if spec is None:
            return
        self._require_numeric_operand(spec.value, f"{path}.value", node_id, rule_event)
        self._require_numeric_operand(
            spec.period, f"{path}.period", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.multiplier, f"{path}.multiplier", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.multiple, f"{path}.multiple", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.expression, f"{path}.expression", node_id, rule_event
        )

    def _validate_money_management(
        self,
        spec: MoneyManagementSpec,
        path: str,
        node_id: str | None = None,
        rule_event: str | None = None,
    ) -> None:
        self._require_numeric_operand(spec.size, f"{path}.size", node_id, rule_event)
        self._require_numeric_operand(
            spec.amount, f"{path}.amount", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.percent, f"{path}.percent", node_id, rule_event
        )
        self._require_numeric_operand(
            spec.risk_pct, f"{path}.risk_pct", node_id, rule_event
        )

    def _validate_condition(
        self,
        cond: ConditionNode,
        path: str,
        node_id: str,
        rule_event: str,
    ) -> None:
        """Recursively validate a ConditionNode tree."""
        if isinstance(cond, LogicalConditionNode):
            for idx, child in enumerate(cond.conditions):
                self._validate_condition(
                    child, f"{path}.conditions[{idx}]", node_id, rule_event
                )
        elif isinstance(cond, (NotConditionNode, TemporalConditionNode)):
            self._validate_condition(
                cond.condition, f"{path}.condition", node_id, rule_event
            )
        elif isinstance(cond, ComparisonConditionNode):
            left_t = self._validate_operand(
                cond.left, f"{path}.left", node_id, rule_event
            )
            right_t = self._validate_operand(
                cond.right, f"{path}.right", node_id, rule_event
            )
            if cond.operator in {"equal", "not_equal"}:
                if not _types_compatible(left_t, right_t):
                    self.add_issue(
                        "WIZARD_TYPE_MISMATCH",
                        (
                            f"Equality comparison '{cond.operator}' cannot compare "
                            f"incompatible operand types '{left_t}' and '{right_t}'."
                        ),
                        path,
                        node_id=node_id,
                    )
            elif left_t not in _NUMERIC_TYPES or right_t not in _NUMERIC_TYPES:
                self.add_issue(
                    "WIZARD_TYPE_MISMATCH",
                    (
                        f"Comparison operator '{cond.operator}' requires numeric "
                        f"operands, got '{left_t}' and '{right_t}'."
                    ),
                    path,
                    node_id=node_id,
                )

    def _validate_order_action_sizing(
        self,
        *,
        size: MoneyManagementSpec | OperandNode | None,
        stop_loss: StopLossSpec | None,
        take_profit: TakeProfitSpec | None,
        path: str,
        node_id: str,
        rule_event: str,
    ) -> None:
        """Validate optional sizing, SL, and TP overrides on an order action."""
        if isinstance(size, MoneyManagementSpec):
            self._validate_money_management(size, f"{path}.size", node_id, rule_event)
        elif size is not None:
            self._require_numeric_operand(size, f"{path}.size", node_id, rule_event)
        self._validate_stop_loss(stop_loss, f"{path}.stop_loss", node_id, rule_event)
        self._validate_take_profit(
            take_profit, f"{path}.take_profit", node_id, rule_event
        )

    def _validate_action(
        self,
        action: ActionNode,
        path: str,
        node_id: str,
        rule_event: str,
    ) -> None:
        """Validate a single ActionNode inside a rule."""
        if isinstance(action, OrderMarketActionNode):
            self._validate_order_action_sizing(
                size=action.size,
                stop_loss=action.stop_loss,
                take_profit=action.take_profit,
                path=path,
                node_id=node_id,
                rule_event=rule_event,
            )
        elif isinstance(action, OrderPendingActionNode):
            self._require_numeric_operand(
                action.entry_price, f"{path}.entry_price", node_id, rule_event
            )
            self._validate_order_action_sizing(
                size=action.size,
                stop_loss=action.stop_loss,
                take_profit=action.take_profit,
                path=path,
                node_id=node_id,
                rule_event=rule_event,
            )
        elif isinstance(action, OrderModifyActionNode):
            self._validate_stop_loss(
                action.stop_loss, f"{path}.stop_loss", node_id, rule_event
            )
            self._validate_take_profit(
                action.take_profit, f"{path}.take_profit", node_id, rule_event
            )
        elif isinstance(action, VariableSetActionNode):
            val_type = self._validate_operand(
                action.value, f"{path}.value", node_id, rule_event
            )
            if action.name not in self.strategy.variables:
                self.add_issue(
                    "WIZARD_UNKNOWN_VARIABLE_REF",
                    f"Target variable '{action.name}' is not in strategy.variables.",
                    f"{path}.name",
                    node_id=node_id,
                )
            else:
                expected_var_type = self.strategy.variables[action.name].type
                if (
                    expected_var_type == "int" and val_type != "int"
                ) or not _types_compatible(expected_var_type, val_type):
                    self.add_issue(
                        "WIZARD_TYPE_MISMATCH",
                        (
                            f"Cannot assign expression of type '{val_type}' to "
                            f"variable '{action.name}' of type '{expected_var_type}'."
                        ),
                        f"{path}.value",
                        node_id=node_id,
                    )

    def _validate_rule(self, rule: RuleNode, idx: int) -> None:
        r_path = f"$.strategy.rules[{idx}]"
        rule_event = rule.event.type
        if rule.event.symbol not in self._declared_symbols:
            self.add_issue(
                "WIZARD_UNDECLARED_CONTEXT_REF",
                (
                    f"Rule event symbol '{rule.event.symbol}' is not declared in "
                    "strategy.universe."
                ),
                f"{r_path}.event.symbol",
                node_id=rule.id,
            )
        if rule.event.timeframe not in self._declared_timeframes:
            self.add_issue(
                "WIZARD_UNDECLARED_CONTEXT_REF",
                (
                    f"Rule event timeframe '{rule.event.timeframe}' is not declared "
                    "in strategy.timeframe."
                ),
                f"{r_path}.event.timeframe",
                node_id=rule.id,
            )

        self._validate_condition(rule.when, f"{r_path}.when", rule.id, rule_event)
        for act_idx, act in enumerate(rule.then):
            self._validate_action(act, f"{r_path}.then[{act_idx}]", rule.id, rule_event)
        for else_idx, act in enumerate(rule.else_then):
            self._validate_action(
                act, f"{r_path}.else_then[{else_idx}]", rule.id, rule_event
            )

    def run_pass2_and_pass3(self) -> None:
        """Execute Passes 2 and 3 over sub-DSLs and rules."""
        self._validate_money_management(
            self.strategy.money_management, "$.strategy.money_management"
        )
        self._validate_stop_loss(
            self.strategy.risk_management.default_stop_loss,
            "$.strategy.risk_management.default_stop_loss",
        )
        self._validate_take_profit(
            self.strategy.risk_management.default_take_profit,
            "$.strategy.risk_management.default_take_profit",
        )

        tm = self.strategy.trade_management
        if tm.breakeven is not None:
            self._require_numeric_operand(
                tm.breakeven.trigger_pips,
                "$.strategy.trade_management.breakeven.trigger_pips",
            )
            self._require_numeric_operand(
                tm.breakeven.lock_pips,
                "$.strategy.trade_management.breakeven.lock_pips",
            )
        if tm.trailing_stop is not None:
            self._require_numeric_operand(
                tm.trailing_stop.distance,
                "$.strategy.trade_management.trailing_stop.distance",
            )
            self._require_numeric_operand(
                tm.trailing_stop.activation_pips,
                "$.strategy.trade_management.trailing_stop.activation_pips",
            )
        for idx, pe in enumerate(tm.partial_exits):
            self._require_numeric_operand(
                pe.trigger_pips,
                f"$.strategy.trade_management.partial_exits[{idx}].trigger_pips",
            )

        for idx, rule in enumerate(self.strategy.rules):
            self._validate_rule(rule, idx)


class StrategyValidator:
    """Three-pass static validator for HSL 1.0 strategy AST documents."""

    def __init__(self, library: WizardBlockLibrary | None = None) -> None:
        self._library = library if library is not None else WizardBlockLibrary()

    @property
    def library(self) -> WizardBlockLibrary:
        """Return the WizardBlockLibrary used by this validator."""
        return self._library

    def validate(
        self,
        document: HSLStrategyDocument | Mapping[str, Any],
        *,
        raise_on_error: bool = False,
    ) -> ValidationReport:
        """Execute Pass 1 (schema), Pass 2 (registry/refs), and Pass 3 (types/shift)."""
        if isinstance(document, HSLStrategyDocument):
            parsed = document
        else:
            try:
                parsed = parse_hsl_document(document)
            except DomainError as exc:
                if raise_on_error:
                    raise
                issue = ValidationIssue(
                    code=exc.code,
                    message=exc.message,
                    path=str(
                        exc.details.get("path", "$")
                        if isinstance(exc.details, Mapping)
                        else "$"
                    ),
                )
                return ValidationReport(valid=False, issues=(issue,))

        session = _ValidationSession(parsed.strategy, self._library)
        session.run_pass1_structural()
        session.run_pass2_and_pass3()

        issues = tuple(session.issues)
        valid = len(issues) == 0
        logger.info(
            "Validated HSLStrategyDocument id=%s valid=%s issues=%d",
            parsed.strategy.id,
            valid,
            len(issues),
        )

        if raise_on_error and not valid:
            first = issues[0]
            serialized_issues: list[JSONValue] = [
                {
                    "code": item.code,
                    "message": item.message,
                    "path": item.path,
                    "node_id": item.node_id,
                }
                for item in issues
            ]
            raise DomainError(
                code=first.code,
                message=first.message,
                details={
                    "path": first.path,
                    "issue_count": len(issues),
                    "issues": serialized_issues,
                },
            )

        return ValidationReport(valid=valid, issues=issues)
