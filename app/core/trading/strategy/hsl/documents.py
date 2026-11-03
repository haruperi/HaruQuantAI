"""HSL 1.0 document parser, canonical serializer, SHA-256 hasher, and upgrader.

Description:
    Provides fail-closed parsing for HaruQuant Strategy Language (HSL 1.0)
    JSON documents, prohibited raw-code AST screening, deterministic priority-
    sorted canonical UTF-8 JSON serialization, SHA-256 content hashing, and
    lossless upgrading from legacy flat StrategyDocument and UI Draft payloads.

Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Canonical document lifecycle and backward-
    compatible upgrade pipeline for AlgoWizard strategy definitions.

Key Capabilities:
    - FR-hsl-document-parse: Validates HSL 1.0 envelopes, rejects raw Python or
      arbitrary code blocks with WIZARD_RAW_CODE_PROHIBITED, and wraps schema
      violations in WIZARD_SCHEMA_INVALID.
    - FR-hsl-canonical-hash: Deterministically orders rules by (priority, id)
      and produces canonical UTF-8 JSON bytes and SHA-256 digests.
    - FR-hsl-legacy-upgrade: Losslessly upgrades Core StrategyDocument and UI
      AlgoWizard Draft payloads into canonical HSLStrategyDocument ASTs.

Python API Usage:
    from app.core.trading.strategy.hsl.documents import (
        compute_document_hash,
        parse_hsl_document,
    )

    doc = parse_hsl_document(
        {"schema_version": "1.0.0", "strategy": {"id": "s1", "name": "S1"}}
    )
    digest = compute_document_hash(doc)

CLI Usage:
    python -c "from app.core.trading.strategy.hsl import documents; print(1)"
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, cast

from pydantic import ValidationError

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.core.trading.strategy.contracts import (
    ActionKind,
    RuleDefinition,
    StrategyDocument,
)
from app.core.trading.strategy.hsl.models import (
    ActionNode,
    ComparisonConditionNode,
    ComparisonOperator,
    ConditionNode,
    HSLStrategyDocument,
    HSLStrategyPayload,
    LifecycleEventSpec,
    LifecycleEventType,
    LogicalConditionNode,
    OrderCancelActionNode,
    OrderMarketActionNode,
    ParameterSpec,
    PositionCloseActionNode,
    RuleNode,
    StateConditionNode,
    TimeframeSpec,
    UniverseSpec,
    VariableSpec,
)
from app.core.trading.strategy.hsl.value_models import (
    IndicatorExpressionNode,
    MarketPriceNode,
    MoneyManagementSpec,
    OperandNode,
    PriceField,
    RiskManagementSpec,
    ScalarLiteral,
    ScalarValueType,
    StopLossSpec,
    TakeProfitSpec,
    ValueLiteralNode,
)

logger = get_logger(__name__)

_PROHIBITED_CODE_TYPES: frozenset[str] = frozenset(
    {"python", "code", "raw_code", "eval", "exec"}
)
_PROHIBITED_CODE_KEYS: frozenset[str] = frozenset(
    {"python_code", "raw_python", "inline_code"}
)
_PRICE_FIELDS: frozenset[str] = frozenset(
    {"open", "high", "low", "close", "volume", "typical", "median", "weighted"}
)
_OPERATOR_MAP: dict[str, ComparisonOperator] = {
    ">": "greater_than",
    "gt": "greater_than",
    "greater_than": "greater_than",
    ">=": "greater_or_equal",
    "gte": "greater_or_equal",
    "greater_or_equal": "greater_or_equal",
    "<": "less_than",
    "lt": "less_than",
    "less_than": "less_than",
    "<=": "less_or_equal",
    "lte": "less_or_equal",
    "less_or_equal": "less_or_equal",
    "==": "equal",
    "=": "equal",
    "eq": "equal",
    "equal": "equal",
    "!=": "not_equal",
    "neq": "not_equal",
    "not_equal": "not_equal",
    "crosses_above": "crosses_above",
    "cross_above": "crosses_above",
    "crosses_below": "crosses_below",
    "cross_below": "crosses_below",
}


def _scan_for_prohibited_code_nodes(node: Any, path: str = "$") -> None:
    """Recursively reject raw Python or arbitrary code execution blocks."""
    if isinstance(node, Mapping):
        for forbidden_key in _PROHIBITED_CODE_KEYS:
            if forbidden_key in node:
                logger.warning(
                    "Rejected prohibited code key=%s at path=%s",
                    forbidden_key,
                    path,
                )
                raise DomainError(
                    code="WIZARD_RAW_CODE_PROHIBITED",
                    message=(
                        f"Prohibited raw code key '{forbidden_key}' at '{path}'. "
                        "HSL 1.0 requires typed AST nodes."
                    ),
                    details={"path": path, "key": forbidden_key},
                )
        for discriminator_key in ("type", "action"):
            raw_kind = node.get(discriminator_key)
            if isinstance(raw_kind, str) and raw_kind.lower() in _PROHIBITED_CODE_TYPES:
                logger.warning(
                    "Rejected prohibited node %s=%s at path=%s",
                    discriminator_key,
                    raw_kind,
                    path,
                )
                raise DomainError(
                    code="WIZARD_RAW_CODE_PROHIBITED",
                    message=(
                        f"Prohibited raw code node '{raw_kind}' at '{path}'. "
                        "HSL 1.0 forbids arbitrary code execution blocks."
                    ),
                    details={"path": path, discriminator_key: raw_kind},
                )
        for key, value in node.items():
            _scan_for_prohibited_code_nodes(value, f"{path}.{key}")
    elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for idx, item in enumerate(node):
            _scan_for_prohibited_code_nodes(item, f"{path}[{idx}]")


def _decode_raw_mapping(raw: Mapping[str, Any] | bytes | str) -> Mapping[str, Any]:
    """Decode JSON bytes or strings into a top-level mapping."""
    if isinstance(raw, Mapping):
        return raw
    if isinstance(raw, (bytes, str)):
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode HSL JSON payload: %s", exc.msg)
            raise DomainError(
                code="WIZARD_SCHEMA_INVALID",
                message=f"Malformed JSON strategy document: {exc.msg}",
                details={"line": exc.lineno, "column": exc.colno},
            ) from exc
        if not isinstance(parsed, Mapping):
            logger.warning("Decoded HSL JSON root is not an object")
            raise DomainError(
                code="WIZARD_SCHEMA_INVALID",
                message="HSL 1.0 strategy document root must be a JSON object.",
            )
        return parsed
    raise DomainError(
        code="WIZARD_SCHEMA_INVALID",
        message="Unsupported strategy document input type.",
    )


def parse_hsl_document(raw: Mapping[str, Any] | bytes | str) -> HSLStrategyDocument:
    """Parse and validate a canonical HSL 1.0 strategy document."""
    payload = _decode_raw_mapping(raw)
    _scan_for_prohibited_code_nodes(payload)

    schema_version = payload.get("schema_version")
    if schema_version != "1.0.0":
        logger.warning(
            "Invalid or missing HSL schema_version=%r",
            schema_version,
        )
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message=(
                f"Unsupported or missing schema_version '{schema_version}'. "
                "Expected '1.0.0'."
            ),
            details={"schema_version": str(schema_version)},
        )

    try:
        document = HSLStrategyDocument.model_validate(payload)
    except ValidationError as exc:
        error_messages: list[JSONValue] = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        logger.warning(
            "HSL 1.0 schema validation failed with %d error(s)",
            len(error_messages),
        )
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message="HSL 1.0 strategy document failed schema validation.",
            details={"errors": error_messages},
        ) from exc

    logger.info(
        "Parsed HSLStrategyDocument id=%s rules=%d",
        document.strategy.id,
        len(document.strategy.rules),
    )
    return document


def canonical_hsl_bytes(document: HSLStrategyDocument) -> bytes:
    """Serialize an HSLStrategyDocument into deterministic UTF-8 JSON bytes."""
    sorted_rules = tuple(
        sorted(document.strategy.rules, key=lambda rule: (rule.priority, rule.id))
    )
    normalized_doc = document.model_copy(
        update={
            "strategy": document.strategy.model_copy(update={"rules": sorted_rules})
        }
    )
    dumped = normalized_doc.model_dump(mode="json")
    serialized = json.dumps(
        dumped,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    logger.debug(
        "Serialized canonical HSL bytes id=%s bytes=%d",
        document.strategy.id,
        len(serialized),
    )
    return serialized


def compute_document_hash(document: HSLStrategyDocument) -> str:
    """Compute the deterministic SHA-256 hex digest of an HSLStrategyDocument."""
    digest = hashlib.sha256(canonical_hsl_bytes(document)).hexdigest()
    logger.info(
        "Computed HSL document hash id=%s sha256=%s",
        document.strategy.id,
        digest,
    )
    return digest


def _normalize_semantic_indicator_name(raw_name: str) -> str:
    """Ensure indicator names use canonical 'indicator.<name>' semantic format."""
    cleaned = raw_name.strip().lower()
    if cleaned.startswith("indicator."):
        return cleaned
    return f"indicator.{cleaned}"


def _build_legacy_indicator_lookup(
    raw_indicators: Mapping[str, Any],
) -> dict[str, IndicatorExpressionNode]:
    """Convert legacy flat indicator definitions into IndicatorExpressionNode map."""
    lookup: dict[str, IndicatorExpressionNode] = {}
    for key, spec in raw_indicators.items():
        if not isinstance(spec, Mapping):
            continue
        ind_type = str(spec.get("type") or key).strip()
        params: dict[str, OperandNode | ScalarLiteral] = {}
        inputs: dict[str, OperandNode] = {}
        for param_key, param_val in spec.items():
            if param_key == "type":
                continue
            if (
                param_key == "source"
                and isinstance(param_val, str)
                and param_val.lower() in _PRICE_FIELDS
            ):
                inputs["source"] = MarketPriceNode(
                    field=cast("PriceField", param_val.lower())
                )
            elif isinstance(param_val, (bool, int, float, str)):
                params[param_key] = ValueLiteralNode(value=param_val)
        lookup[key] = IndicatorExpressionNode(
            name=_normalize_semantic_indicator_name(ind_type),
            inputs=inputs,
            params=params,
        )
    return lookup


def _resolve_legacy_operand(
    token: Any,
    indicators: Mapping[str, IndicatorExpressionNode],
) -> OperandNode:
    """Convert a legacy condition left/right token into a typed OperandNode."""
    if isinstance(token, (bool, int, float)):
        return ValueLiteralNode(value=token)
    if isinstance(token, str):
        stripped = token.strip()
        if stripped in indicators:
            return indicators[stripped]
        lower = stripped.lower()
        if lower in _PRICE_FIELDS:
            return MarketPriceNode(field=cast("PriceField", lower))
        try:
            if "." in stripped:
                return ValueLiteralNode(value=float(stripped), value_type="float")
            return ValueLiteralNode(value=int(stripped), value_type="int")
        except ValueError:
            return IndicatorExpressionNode(
                name=_normalize_semantic_indicator_name(stripped)
            )
    raise DomainError(
        code="WIZARD_SCHEMA_INVALID",
        message=f"Unsupported legacy condition operand: {token!r}",
    )


def _map_legacy_operator(raw_op: str) -> ComparisonOperator:
    """Map legacy relational/crossing operator strings to ComparisonOperator."""
    normalized = raw_op.strip().lower()
    mapped = _OPERATOR_MAP.get(normalized)
    if mapped is None:
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message=f"Unsupported legacy comparison operator '{raw_op}'.",
            details={"operator": raw_op},
        )
    return mapped


def _combine_condition_nodes(cond_nodes: Sequence[ConditionNode]) -> ConditionNode:
    """Combine zero, one, or multiple ConditionNodes into a single tree node."""
    if len(cond_nodes) == 0:
        return StateConditionNode(state="always_true")
    if len(cond_nodes) == 1:
        return cond_nodes[0]
    return LogicalConditionNode(operator="and", conditions=tuple(cond_nodes))


def _convert_legacy_dict_rule(
    raw_rule: Mapping[str, Any],
    idx: int,
    indicator_map: Mapping[str, IndicatorExpressionNode],
) -> RuleNode:
    """Convert a single legacy dict rule entry into a canonical RuleNode."""
    rule_id = str(raw_rule.get("id") or f"rule-{idx + 1}").strip()
    direction = str(raw_rule.get("direction") or "LONG").strip().upper()
    is_entry = bool(raw_rule.get("entry", True))
    side: str = "short" if direction == "SHORT" else "long"

    raw_conditions = raw_rule.get("conditions")
    cond_nodes: list[ConditionNode] = []
    if isinstance(raw_conditions, Sequence) and not isinstance(
        raw_conditions, (str, bytes)
    ):
        for cond in raw_conditions:
            if not isinstance(cond, Mapping):
                continue
            op = _map_legacy_operator(str(cond.get("op") or ">"))
            left_node = _resolve_legacy_operand(cond.get("left"), indicator_map)
            right_node = _resolve_legacy_operand(cond.get("right"), indicator_map)
            cond_nodes.append(
                ComparisonConditionNode(operator=op, left=left_node, right=right_node)
            )

    action_node: ActionNode
    if is_entry:
        priority = 300 if side == "long" else 310
        action_node = OrderMarketActionNode(
            side="short" if side == "short" else "long",
        )
    else:
        priority = 200 if side == "long" else 210
        action_node = PositionCloseActionNode(
            target_side="short" if side == "short" else "long",
            reason=rule_id,
        )

    return RuleNode(
        id=rule_id,
        name=rule_id,
        priority=priority + idx,
        when=_combine_condition_nodes(cond_nodes),
        then=(action_node,),
    )


def _convert_legacy_risk_dict(
    risk_dict: Mapping[str, Any],
) -> tuple[MoneyManagementSpec, RiskManagementSpec]:
    """Convert a legacy risk dictionary into money and risk management specs."""
    sizing_mode = str(risk_dict.get("sizing_mode") or "fixed").strip().lower()
    base_size = float(risk_dict.get("base_size") or 1.0)
    if sizing_mode == "percent_equity":
        money_mgmt = MoneyManagementSpec(
            type="percent_equity",
            percent=ValueLiteralNode(value=base_size, value_type="float"),
        )
    elif sizing_mode in {"volatility_target", "risk_percent"}:
        money_mgmt = MoneyManagementSpec(
            type="risk_percent",
            risk_pct=ValueLiteralNode(value=base_size, value_type="float"),
        )
    else:
        money_mgmt = MoneyManagementSpec(
            type="fixed_size",
            size=ValueLiteralNode(value=base_size, value_type="float"),
        )

    sl_pct = risk_dict.get("stop_loss_pct")
    tp_pct = risk_dict.get("take_profit_pct")
    max_open = int(risk_dict.get("max_open_positions") or 1)
    stop_loss = (
        StopLossSpec(
            type="percent",
            value=ValueLiteralNode(value=float(sl_pct), value_type="float"),
        )
        if sl_pct is not None and float(sl_pct) > 0
        else StopLossSpec(type="none")
    )
    take_profit = (
        TakeProfitSpec(
            type="percent",
            value=ValueLiteralNode(value=float(tp_pct), value_type="float"),
        )
        if tp_pct is not None and float(tp_pct) > 0
        else TakeProfitSpec(type="none")
    )
    risk_mgmt = RiskManagementSpec(
        max_open_positions=max(1, max_open),
        default_stop_loss=stop_loss,
        default_take_profit=take_profit,
    )
    return money_mgmt, risk_mgmt


def _upgrade_core_strategy_dict(payload: Mapping[str, Any]) -> HSLStrategyDocument:
    """Upgrade a flat Core StrategyDocument mapping into HSLStrategyDocument."""
    strategy_id = str(payload.get("strategy_id") or payload.get("id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not strategy_id or not name:
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message=(
                "Legacy strategy document requires non-empty 'strategy_id' and 'name'."
            ),
        )

    raw_universe = payload.get("universe")
    symbols: tuple[str, ...] = (
        tuple(str(s) for s in raw_universe if str(s).strip())
        if isinstance(raw_universe, Sequence)
        and not isinstance(raw_universe, (str, bytes))
        and len(raw_universe) > 0
        else ("EURUSD",)
    )
    timeframe_str = str(payload.get("timeframe") or "1h").strip() or "1h"

    raw_indicators = payload.get("indicators")
    indicator_map = (
        _build_legacy_indicator_lookup(raw_indicators)
        if isinstance(raw_indicators, Mapping)
        else {}
    )

    rules: list[RuleNode] = []
    raw_rules = payload.get("rules")
    if isinstance(raw_rules, Sequence) and not isinstance(raw_rules, (str, bytes)):
        for idx, raw_rule in enumerate(raw_rules):
            if isinstance(raw_rule, Mapping):
                rules.append(_convert_legacy_dict_rule(raw_rule, idx, indicator_map))

    raw_risk = payload.get("risk")
    money_mgmt, risk_mgmt = _convert_legacy_risk_dict(
        raw_risk if isinstance(raw_risk, Mapping) else {}
    )

    raw_metadata = payload.get("metadata")
    metadata: dict[str, Any] = (
        dict(raw_metadata) if isinstance(raw_metadata, Mapping) else {}
    )
    if "version" in payload:
        metadata["legacy_version"] = payload["version"]

    return HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id=strategy_id,
            name=name,
            description=str(payload.get("description") or ""),
            metadata=metadata,
            universe=UniverseSpec(mode="explicit", symbols=symbols),
            timeframe=TimeframeSpec(primary=timeframe_str),
            money_management=money_mgmt,
            risk_management=risk_mgmt,
            rules=tuple(rules),
        ),
    )


def _upgrade_ui_draft_dict(payload: Mapping[str, Any]) -> HSLStrategyDocument:
    """Upgrade a frontend AlgoWizard UI Draft mapping into HSLStrategyDocument."""
    strategy_id = str(payload.get("strategyId") or payload.get("id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not strategy_id or not name:
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message="Legacy UI draft requires non-empty 'strategyId' and 'name'.",
        )

    quantity = float(payload.get("quantity") or 1.0)
    sl_pct = payload.get("stopLossPct")
    tp_pct = payload.get("takeProfitPct")
    default_direction = str(payload.get("direction") or "long").strip().lower()

    rules: list[RuleNode] = []
    raw_signals = payload.get("signals")
    if isinstance(raw_signals, Sequence) and not isinstance(raw_signals, (str, bytes)):
        for idx, sig in enumerate(raw_signals):
            if not isinstance(sig, Mapping):
                continue
            sig_id = str(sig.get("id") or f"sig-{idx + 1}").strip()
            sig_label = str(sig.get("label") or sig_id).strip()
            indicator_name = _normalize_semantic_indicator_name(
                str(sig.get("indicator") or "rsi")
            )
            period = int(sig.get("period") or 14)
            comparator = _map_legacy_operator(str(sig.get("comparator") or ">"))
            threshold = float(sig.get("threshold") or 50.0)
            raw_action = str(sig.get("action") or f"enter_{default_direction}").lower()

            when_node = ComparisonConditionNode(
                operator=comparator,
                left=IndicatorExpressionNode(
                    name=indicator_name,
                    params={"period": ValueLiteralNode(value=period, value_type="int")},
                ),
                right=ValueLiteralNode(value=threshold, value_type="float"),
            )

            action_node: ActionNode
            if raw_action == "enter_short":
                priority = 310 + idx
                action_node = OrderMarketActionNode(side="short")
            elif raw_action == "exit_long":
                priority = 200 + idx
                action_node = PositionCloseActionNode(
                    target_side="long", reason=sig_label
                )
            elif raw_action == "exit_short":
                priority = 210 + idx
                action_node = PositionCloseActionNode(
                    target_side="short", reason=sig_label
                )
            else:
                priority = 300 + idx
                action_node = OrderMarketActionNode(side="long")

            rules.append(
                RuleNode(
                    id=sig_id,
                    name=sig_label,
                    priority=priority,
                    when=when_node,
                    then=(action_node,),
                )
            )

    _, risk_mgmt = _convert_legacy_risk_dict(
        {"stop_loss_pct": sl_pct, "take_profit_pct": tp_pct}
    )

    metadata: dict[str, Any] = {"upgraded_from": "ui_draft"}
    if "blocks" in payload and isinstance(payload["blocks"], Sequence):
        metadata["legacy_blocks_count"] = len(payload["blocks"])

    return HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id=strategy_id,
            name=name,
            description=str(payload.get("description") or ""),
            metadata=metadata,
            money_management=MoneyManagementSpec(
                type="fixed_size",
                size=ValueLiteralNode(value=quantity, value_type="float"),
            ),
            risk_management=risk_mgmt,
            rules=tuple(rules),
        ),
    )


def _convert_dataclass_rule(
    rule_def: RuleDefinition,
    idx: int,
    magic_number: int,
) -> RuleNode:
    """Convert a Core RuleDefinition dataclass into a canonical RuleNode."""
    cond_nodes = [
        ComparisonConditionNode(
            operator=_map_legacy_operator(cond.comparator),
            left=_resolve_legacy_operand(cond.left, {}),
            right=_resolve_legacy_operand(cond.right, {}),
        )
        for cond in rule_def.conditions
    ]

    action_nodes: list[ActionNode] = []
    for act in rule_def.actions:
        is_short = act.direction < 0
        if act.kind == ActionKind.EXIT:
            action_nodes.append(
                PositionCloseActionNode(
                    target_side="short" if is_short else "long",
                    reason=act.comment,
                )
            )
        elif act.kind == ActionKind.CANCEL:
            action_nodes.append(
                OrderCancelActionNode(
                    target_side="short" if is_short else "long",
                )
            )
        else:
            sl_spec = (
                StopLossSpec(
                    type="fixed_pips",
                    value=ValueLiteralNode(value=act.sl_pips, value_type="float"),
                )
                if act.sl_pips > 0
                else None
            )
            tp_spec = (
                TakeProfitSpec(
                    type="fixed_pips",
                    value=ValueLiteralNode(value=act.tp_pips, value_type="float"),
                )
                if act.tp_pips > 0
                else None
            )
            action_nodes.append(
                OrderMarketActionNode(
                    side="short" if is_short else "long",
                    stop_loss=sl_spec,
                    take_profit=tp_spec,
                    comment=act.comment,
                    magic_number=magic_number,
                )
            )
    if not action_nodes:
        action_nodes.append(OrderMarketActionNode(side="long"))

    trigger_str = str(rule_def.trigger.value)
    event_type: LifecycleEventType = (
        cast("LifecycleEventType", trigger_str)
        if trigger_str in {"on_bar_close", "on_bar_open", "on_tick"}
        else "on_bar_close"
    )
    return RuleNode(
        id=rule_def.rule_id,
        name=rule_def.name or rule_def.rule_id,
        priority=100 + idx * 10,
        enabled=rule_def.is_enabled,
        event=LifecycleEventSpec(type=event_type),
        when=_combine_condition_nodes(cond_nodes),
        then=tuple(action_nodes),
    )


def _upgrade_core_strategy_dataclass(raw: StrategyDocument) -> HSLStrategyDocument:
    """Upgrade a Core StrategyDocument dataclass instance into HSLStrategyDocument."""
    strategy_id = raw.strategy_id.strip()
    if not strategy_id:
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message="StrategyDocument requires non-empty 'strategy_id'.",
        )

    parameters: dict[str, ParameterSpec] = {}
    for param in raw.params:
        param_type_str = param.param_type.lower()
        p_type: ScalarValueType = (
            cast("ScalarValueType", param_type_str)
            if param_type_str in {"int", "float", "bool", "str"}
            else "float"
        )
        parameters[param.name] = ParameterSpec(
            type=p_type,
            default=param.value
            if isinstance(param.value, (bool, int, float, str))
            else 0.0,
        )

    variables: dict[str, VariableSpec] = {}
    for var in raw.variables:
        var_type_str = var.var_type.lower()
        v_type: ScalarValueType = (
            cast("ScalarValueType", var_type_str)
            if var_type_str in {"int", "float", "bool", "str"}
            else "float"
        )
        variables[var.name] = VariableSpec(
            type=v_type,
            initial=var.default_value
            if isinstance(var.default_value, (bool, int, float, str))
            else 0.0,
        )

    rules = tuple(
        _convert_dataclass_rule(rule_def, idx, raw.trading_setup.magic_number)
        for idx, rule_def in enumerate(raw.rules)
    )

    return HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id=strategy_id,
            name=strategy_id,
            parameters=parameters,
            variables=variables,
            risk_management=RiskManagementSpec(
                max_open_positions=max(1, raw.trading_setup.max_open_positions),
            ),
            rules=rules,
        ),
    )


def upgrade_legacy_wizard_document(
    raw: Mapping[str, Any] | StrategyDocument,
) -> HSLStrategyDocument:
    """Losslessly convert a legacy StrategyDocument or UI Draft into HSL 1.0."""
    if isinstance(raw, StrategyDocument):
        doc = _upgrade_core_strategy_dataclass(raw)
        logger.info("Upgraded Core StrategyDocument instance id=%s", doc.strategy.id)
        return doc

    if not isinstance(raw, Mapping):
        raise DomainError(
            code="WIZARD_SCHEMA_INVALID",
            message=(
                "Legacy strategy upgrade input must be a mapping or StrategyDocument."
            ),
        )

    _scan_for_prohibited_code_nodes(raw)

    if raw.get("schema_version") == "1.0.0" and isinstance(
        raw.get("strategy"), Mapping
    ):
        return parse_hsl_document(raw)

    if "signals" in raw or "strategyId" in raw:
        doc = _upgrade_ui_draft_dict(raw)
        logger.info("Upgraded UI Draft document id=%s", doc.strategy.id)
        return doc

    doc = _upgrade_core_strategy_dict(raw)
    logger.info("Upgraded legacy StrategyDocument mapping id=%s", doc.strategy.id)
    return doc
