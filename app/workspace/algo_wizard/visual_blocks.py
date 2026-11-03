"""ServletAlgoWizard equivalent service (VisualBlockService) for AlgoWizard.

Description:
    Provides visual HSL 1.0 AST operations, non-mutating 3-pass validation,
    deterministic condition negation (including De Morgan's law), reusable
    custom block and palette group persistence (backed by CompositionSpec),
    timeframe expansion, resource dependency inspection, and causal bar-by-bar
    wizard backtest execution.

Purpose:
    FEAT-WIZARD-VISUAL-BLOCKS: Gate G6 (Phase 5.6, WO-WZ-VISUAL-BLOCKS /
    I-ServletAlgoWizard) backend service for visual strategy authoring and
    simulation runs.

Key Capabilities:
    - FR-wizard-visual-config-and-validation: Serves WizardConfigResult and
      executes non-mutating 3-pass StrategyValidator checks.
    - FR-wizard-visual-condition-negation: Deterministically negates HSL
      ConditionNode trees with operator inversion and optional De Morgan
      distribution.
    - FR-wizard-visual-custom-blocks-and-groups: Validates and persists
      CustomBlockDefinition (CompositionSpec) and BlockGroupDefinition items.
    - FR-wizard-visual-resources-and-timeframes: Adds validated timeframes and
      inspects AST contexts for missing symbol, timeframe, or block resources.
    - FR-wizard-visual-backtest: Compiles and simulates HSL documents on bar
      series via StrategyCompiler, recording trade logs and PnL deltas.

Python API Usage:
    from app.workspace.algo_wizard.visual_blocks import VisualBlockService
    from app.workspace.algo_wizard.visual_blocks_models import GetWizardConfigRequest

    svc = VisualBlockService()
    cfg = svc.get_config(GetWizardConfigRequest(request_id="r1"))

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_visual_blocks.py
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.enums import OrderType, Timeframe
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.core.lib.responses import StandardResponse, build_typed_response
from app.core.trading.backtest.contracts import RunResult, RunSpec
from app.core.trading.backtest.runner import BacktestRunner
from app.core.trading.strategy.hsl import models as _hm
from app.core.trading.strategy.hsl import value_models as _vm
from app.core.trading.strategy.hsl.compiler import StrategyCompiler
from app.core.trading.strategy.hsl.documents import (
    parse_hsl_document,
    upgrade_legacy_wizard_document,
)
from app.core.trading.strategy.hsl.library import WizardBlockLibrary
from app.core.trading.strategy.hsl.models import (
    ComparisonOperator,
    ConditionNode,
    HSLStrategyDocument,
    RuleNode,
)
from app.core.trading.strategy.hsl.validation import StrategyValidator, ValidationReport
from app.core.trading.strategy.runtime import StrategyRuntime
from app.workspace.algo_wizard import visual_blocks_models as _vbm
from app.workspace.algo_wizard.visual_blocks_models import (
    BlockGroupDefinition,
    CustomBlockDefinition,
    MissingResourceItem,
    ResourceCheckResult,
    WizardBacktestResult,
    WizardBacktestStatus,
    WizardBarInput,
    WizardConfigResult,
    WizardTradeLogEntry,
)

logger = get_logger(__name__)

_SUPPORTED_TIMEFRAMES: tuple[str, ...] = (
    "M1",
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
    "W1",
    "MN1",
)

_SUPPORTED_EVENTS: tuple[str, ...] = (
    "on_start",
    "on_stop",
    "on_timer",
    "on_tick",
    "on_bar_open",
    "on_bar_close",
    "on_order_submitted",
    "on_order_filled",
    "on_order_cancelled",
    "on_order_rejected",
    "on_position_opened",
    "on_position_closed",
    "on_session_open",
    "on_session_close",
)

_NEGATED_COMPARISON_OPS: Mapping[ComparisonOperator, ComparisonOperator] = {
    "greater_than": "less_or_equal",
    "less_or_equal": "greater_than",
    "greater_or_equal": "less_than",
    "less_than": "greater_or_equal",
    "equal": "not_equal",
    "not_equal": "equal",
    "crosses_above": "crosses_below",
    "crosses_below": "crosses_above",
}

_DEFAULT_BLOCK_GROUPS: tuple[BlockGroupDefinition, ...] = (
    BlockGroupDefinition(
        group_id="trend_indicators",
        name="Trend Indicators",
        description="Moving averages and directional trend indicators.",
        block_ids=("indicator.ema", "indicator.sma", "indicator.adx"),
        enabled=True,
    ),
    BlockGroupDefinition(
        group_id="oscillators",
        name="Momentum Oscillators",
        description="Bounded oscillators for mean-reversion and momentum.",
        block_ids=("indicator.rsi", "indicator.stochastic", "indicator.cci"),
        enabled=True,
    ),
    BlockGroupDefinition(
        group_id="volatility_and_channels",
        name="Volatility & Channels",
        description="Volatility ranges and channel breakout blocks.",
        block_ids=(
            "indicator.atr",
            "indicator.bollinger_bands",
            "indicator.highest",
            "indicator.lowest",
        ),
        enabled=True,
    ),
)


def _negate_node(node: ConditionNode, *, distribute_logical: bool) -> ConditionNode:
    """Deterministically negate an HSL 1.0 ConditionNode."""
    if isinstance(node, _hm.ComparisonConditionNode):
        inv_op = _NEGATED_COMPARISON_OPS[node.operator]
        return _hm.ComparisonConditionNode(
            operator=inv_op,
            left=node.left,
            right=node.right,
        )
    if isinstance(node, _hm.NotConditionNode):
        return node.condition
    if isinstance(node, _hm.LogicalConditionNode) and distribute_logical:
        inv_log: Any = "or" if node.operator == "and" else "and"
        children = tuple(
            _negate_node(c, distribute_logical=True) for c in node.conditions
        )
        return _hm.LogicalConditionNode(operator=inv_log, conditions=children)
    return _hm.NotConditionNode(condition=node)


@dataclass
class _ResourceScanState:
    """Mutable collector state for VisualBlockService.check_resources."""

    valid_syms: set[str]
    valid_tfs: set[str]
    ref_syms: set[str]
    ref_tfs: set[str]
    ref_blocks: set[str] = field(default_factory=set)
    missing: list[MissingResourceItem] = field(default_factory=list)


class VisualBlockService:
    """ServletAlgoWizard service for AST transforms, custom blocks, and backtests."""

    def __init__(
        self,
        *,
        library: WizardBlockLibrary | None = None,
        validator: StrategyValidator | None = None,
        compiler: StrategyCompiler | None = None,
    ) -> None:
        self._library = library if library is not None else WizardBlockLibrary()
        self._validator = validator or StrategyValidator(library=self._library)
        self._compiler = compiler or StrategyCompiler(
            library=self._library, validator=self._validator
        )
        self._custom_blocks: dict[str, CustomBlockDefinition] = {}
        self._block_groups: dict[str, BlockGroupDefinition] = {
            g.group_id: g for g in _DEFAULT_BLOCK_GROUPS
        }
        self._backtest_results: dict[str, WizardBacktestResult] = {}
        self._revision: int = 1

    @property
    def library(self) -> WizardBlockLibrary:
        """Return the active WizardBlockLibrary."""
        return self._library

    @property
    def validator(self) -> StrategyValidator:
        """Return the active StrategyValidator."""
        return self._validator

    @property
    def compiler(self) -> StrategyCompiler:
        """Return the active StrategyCompiler."""
        return self._compiler

    @staticmethod
    def _coerce_hsl_document(
        raw: HSLStrategyDocument | Mapping[str, Any],
    ) -> HSLStrategyDocument:
        if isinstance(raw, HSLStrategyDocument):
            return raw
        if "schema_version" in raw and "strategy" in raw:
            return parse_hsl_document(raw)
        return upgrade_legacy_wizard_document(raw)

    def get_config(
        self, request: _vbm.GetWizardConfigRequest | None = None
    ) -> StandardResponse[WizardConfigResult]:
        """Return default HSL schema version, events, and active block groups."""
        req = request if request is not None else _vbm.GetWizardConfigRequest()
        groups = tuple(
            g for _, g in sorted(self._block_groups.items(), key=lambda kv: kv[0])
        )
        cfg = WizardConfigResult(
            schema_version="1.0.0",
            supported_lifecycle_events=_SUPPORTED_EVENTS,
            default_symbol="EURUSD",
            default_timeframe="H1",
            supported_timeframes=_SUPPORTED_TIMEFRAMES,
            custom_block_groups=groups,
            custom_blocks_count=len(self._custom_blocks),
        )
        logger.info(
            "FR-wizard-visual-config-and-validation: Served WizardConfigResult "
            "groups=%d custom_blocks=%d",
            len(groups),
            len(self._custom_blocks),
        )
        return build_typed_response(
            request_id=req.request_id,
            data=cfg,
            json_payload=cfg.model_dump(mode="json"),
            revision=self._revision,
        )

    def validate_document(
        self, request: _vbm.ValidateDocumentRequest
    ) -> StandardResponse[ValidationReport]:
        """Execute non-mutating 3-pass StrategyValidator on an HSL document."""
        doc = self._coerce_hsl_document(request.document)
        report = self._validator.validate(doc, raise_on_error=False)
        logger.info(
            "FR-wizard-visual-config-and-validation: Validated document '%s' "
            "valid=%s issues=%d",
            doc.strategy.id,
            report.valid,
            len(report.issues),
        )
        return build_typed_response(
            request_id=request.request_id,
            data=report,
            json_payload=report.model_dump(mode="json"),
            revision=self._revision,
        )

    def negate_condition(
        self, request: _vbm.NegateConditionRequest
    ) -> StandardResponse[ConditionNode]:
        """Deterministically negate an HSL ConditionNode."""
        negated = _negate_node(
            request.condition,
            distribute_logical=request.distribute_logical,
        )
        logger.info(
            "FR-wizard-visual-condition-negation: Negated condition "
            "in_type=%s out_type=%s distribute=%s",
            request.condition.type,
            negated.type,
            request.distribute_logical,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=negated,
            json_payload=negated.model_dump(mode="json"),
            revision=self._revision,
        )

    def save_custom_blocks(
        self, request: _vbm.SaveCustomBlocksRequest
    ) -> StandardResponse[tuple[CustomBlockDefinition, ...]]:
        """Validate and persist reusable parameterized HSL custom blocks."""
        if request.replace_all:
            self._custom_blocks.clear()
        for blk in request.blocks:
            comp_spec = blk.to_composition_spec()
            if not comp_spec.id:
                raise DomainError(
                    code="WIZARD_CUSTOM_BLOCK_INVALID",
                    message="Custom block ID must be non-empty.",
                )
            self._custom_blocks[blk.block_id] = blk
        self._revision += 1
        saved = tuple(
            b for _, b in sorted(self._custom_blocks.items(), key=lambda kv: kv[0])
        )
        logger.info(
            "FR-wizard-visual-custom-blocks-and-groups: Saved %d custom blocks "
            "(total=%d, rev=%d)",
            len(request.blocks),
            len(saved),
            self._revision,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=saved,
            json_payload=[b.model_dump(mode="json") for b in saved],
            revision=self._revision,
        )

    def load_custom_blocks(
        self, request: _vbm.LoadCustomBlocksRequest | None = None
    ) -> StandardResponse[tuple[CustomBlockDefinition, ...]]:
        """Return all registered custom block definitions ordered by block_id."""
        req = request if request is not None else _vbm.LoadCustomBlocksRequest()
        items = [
            b
            for _, b in sorted(self._custom_blocks.items(), key=lambda kv: kv[0])
            if req.category is None or b.category == req.category
        ]
        result = tuple(items)
        logger.info(
            "FR-wizard-visual-custom-blocks-and-groups: Loaded %d custom blocks "
            "(category=%s)",
            len(result),
            req.category,
        )
        return build_typed_response(
            request_id=req.request_id,
            data=result,
            json_payload=[b.model_dump(mode="json") for b in result],
            revision=self._revision,
        )

    def save_block_groups(
        self, request: _vbm.SaveBlockGroupsRequest
    ) -> StandardResponse[tuple[BlockGroupDefinition, ...]]:
        """Persist named block palette groups for the visual builder."""
        if request.replace_all:
            self._block_groups.clear()
        for grp in request.groups:
            self._block_groups[grp.group_id] = grp
        self._revision += 1
        saved = tuple(
            g for _, g in sorted(self._block_groups.items(), key=lambda kv: kv[0])
        )
        logger.info(
            "FR-wizard-visual-custom-blocks-and-groups: Saved %d block groups "
            "(total=%d, rev=%d)",
            len(request.groups),
            len(saved),
            self._revision,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=saved,
            json_payload=[g.model_dump(mode="json") for g in saved],
            revision=self._revision,
        )

    def load_block_groups(
        self, request: _vbm.LoadBlockGroupsRequest | None = None
    ) -> StandardResponse[tuple[BlockGroupDefinition, ...]]:
        """Return registered block palette groups ordered by group_id."""
        req = request if request is not None else _vbm.LoadBlockGroupsRequest()
        items = [
            g
            for _, g in sorted(self._block_groups.items(), key=lambda kv: kv[0])
            if not req.enabled_only or g.enabled
        ]
        result = tuple(items)
        logger.info(
            "FR-wizard-visual-custom-blocks-and-groups: Loaded %d block groups "
            "(enabled_only=%s)",
            len(result),
            req.enabled_only,
        )
        return build_typed_response(
            request_id=req.request_id,
            data=result,
            json_payload=[g.model_dump(mode="json") for g in result],
            revision=self._revision,
        )

    def add_timeframe(
        self, request: _vbm.AddTimeframeRequest
    ) -> StandardResponse[HSLStrategyDocument]:
        """Add a validated timeframe to strategy.timeframe.additional."""
        tf_norm = request.timeframe.strip().upper()
        if tf_norm not in _SUPPORTED_TIMEFRAMES:
            logger.warning(
                "FR-wizard-visual-resources-and-timeframes: Invalid timeframe '%s'",
                request.timeframe,
            )
            raise DomainError(
                code="WIZARD_INVALID_TIMEFRAME",
                message=f"Unsupported timeframe '{request.timeframe}'.",
                details={
                    "timeframe": request.timeframe,
                    "supported": list(_SUPPORTED_TIMEFRAMES),
                },
            )
        doc = self._coerce_hsl_document(request.document)
        tf_spec = doc.strategy.timeframe
        additional = list(tf_spec.additional)
        if tf_norm != tf_spec.primary and tf_norm not in additional:
            additional.append(tf_norm)
        new_tf = tf_spec.model_copy(update={"additional": tuple(additional)})
        new_strat = doc.strategy.model_copy(update={"timeframe": new_tf})
        updated_doc = doc.model_copy(update={"strategy": new_strat})
        self._revision += 1
        logger.info(
            "FR-wizard-visual-resources-and-timeframes: Added timeframe '%s' "
            "to strategy '%s' (additional=%s)",
            tf_norm,
            updated_doc.strategy.id,
            new_tf.additional,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=updated_doc,
            json_payload=updated_doc.model_dump(mode="json"),
            revision=self._revision,
        )

    def check_resources(
        self, request: _vbm.CheckResourcesRequest
    ) -> StandardResponse[ResourceCheckResult]:
        """Inspect AST contexts and blocks against available symbols and timeframes."""
        doc = self._coerce_hsl_document(request.document)
        strat = doc.strategy
        declared_syms = set(strat.universe.symbols)
        avail_syms = (
            set(request.available_symbols)
            if request.available_symbols
            else declared_syms
        )
        declared_tfs = {strat.timeframe.primary, *strat.timeframe.additional}
        avail_tfs = (
            set(request.available_timeframes)
            if request.available_timeframes
            else declared_tfs
        )

        missing = [
            MissingResourceItem(
                resource_type="symbol",
                identifier=sym,
                path="strategy.universe.symbols",
                message=f"Declared symbol '{sym}' is not in available symbols.",
            )
            for sym in sorted(declared_syms)
            if sym not in avail_syms
        ]
        missing.extend(
            MissingResourceItem(
                resource_type="timeframe",
                identifier=tf,
                path="strategy.timeframe",
                message=f"Declared timeframe '{tf}' is not in available timeframes.",
            )
            for tf in sorted(declared_tfs)
            if tf not in avail_tfs
        )
        state = _ResourceScanState(
            valid_syms=declared_syms & avail_syms,
            valid_tfs=declared_tfs & avail_tfs,
            ref_syms=set(declared_syms),
            ref_tfs=set(declared_tfs),
            missing=missing,
        )

        for idx, rule in enumerate(strat.rules):
            r_path = f"strategy.rules[{idx}]"
            self._inspect_condition_resources(rule.when, f"{r_path}.when", state)
            for a_idx, act in enumerate((*rule.then, *rule.else_then)):
                self._inspect_action_resources(act, f"{r_path}.actions[{a_idx}]", state)

        res = ResourceCheckResult(
            ready=len(state.missing) == 0,
            referenced_symbols=tuple(sorted(state.ref_syms)),
            referenced_timeframes=tuple(sorted(state.ref_tfs)),
            referenced_blocks=tuple(sorted(state.ref_blocks)),
            missing_resources=tuple(state.missing),
        )
        logger.info(
            "FR-wizard-visual-resources-and-timeframes: Checked resources for '%s' "
            "ready=%s missing=%d",
            strat.id,
            res.ready,
            len(state.missing),
        )
        return build_typed_response(
            request_id=request.request_id,
            data=res,
            json_payload=res.model_dump(mode="json"),
            revision=self._revision,
        )

    def _inspect_condition_resources(
        self,
        cond: ConditionNode,
        path: str,
        state: _ResourceScanState,
    ) -> None:
        if isinstance(cond, _hm.ComparisonConditionNode):
            self._inspect_operand_resources(cond.left, f"{path}.left", state)
            self._inspect_operand_resources(cond.right, f"{path}.right", state)
        elif isinstance(cond, _hm.LogicalConditionNode):
            for i, child in enumerate(cond.conditions):
                self._inspect_condition_resources(
                    child, f"{path}.conditions[{i}]", state
                )
        elif isinstance(cond, (_hm.NotConditionNode, _hm.TemporalConditionNode)):
            self._inspect_condition_resources(
                cond.condition, f"{path}.condition", state
            )

    def _inspect_action_resources(
        self,
        act: _hm.ActionNode,
        path: str,
        state: _ResourceScanState,
    ) -> None:
        if isinstance(act, _hm.VariableSetActionNode):
            self._inspect_operand_resources(act.value, f"{path}.value", state)
        elif isinstance(act, _hm.OrderPendingActionNode):
            self._inspect_operand_resources(
                act.entry_price, f"{path}.entry_price", state
            )

    @staticmethod
    def _inspect_context_resources(
        ctx: _vm.EvaluationContext,
        path: str,
        state: _ResourceScanState,
    ) -> None:
        if ctx.symbol != "$current_symbol":
            state.ref_syms.add(ctx.symbol)
            if ctx.symbol not in state.valid_syms:
                state.missing.append(
                    MissingResourceItem(
                        resource_type="symbol",
                        identifier=ctx.symbol,
                        path=f"{path}.context.symbol",
                        message=f"Symbol '{ctx.symbol}' is not available.",
                    )
                )
        if ctx.timeframe != "$current_timeframe":
            state.ref_tfs.add(ctx.timeframe)
            if ctx.timeframe not in state.valid_tfs:
                state.missing.append(
                    MissingResourceItem(
                        resource_type="timeframe",
                        identifier=ctx.timeframe,
                        path=f"{path}.context.timeframe",
                        message=f"Timeframe '{ctx.timeframe}' is not available.",
                    )
                )

    def _inspect_operand_resources(
        self,
        op: _vm.OperandNode,
        path: str,
        state: _ResourceScanState,
    ) -> None:
        if isinstance(op, (_vm.MarketPriceNode, _vm.IndicatorExpressionNode)):
            self._inspect_context_resources(op.context, path, state)
        if isinstance(op, (_vm.IndicatorExpressionNode, _vm.FunctionExpressionNode)):
            state.ref_blocks.add(op.name)
            known = (
                self._library.resolve(op.name) is not None
                or op.name in self._custom_blocks
            )
            if not known:
                state.missing.append(
                    MissingResourceItem(
                        resource_type="block",
                        identifier=op.name,
                        path=f"{path}.name",
                        message=f"Block '{op.name}' is not registered.",
                    )
                )
            children: Sequence[_vm.OperandNode] = (
                tuple(op.inputs.values())
                if isinstance(op, _vm.IndicatorExpressionNode)
                else op.args
            )
            for idx, child in enumerate(children):
                self._inspect_operand_resources(child, f"{path}.inputs[{idx}]", state)
        elif isinstance(op, _vm.MathExpressionNode):
            self._inspect_operand_resources(op.left, f"{path}.left", state)
            if op.right is not None:
                self._inspect_operand_resources(op.right, f"{path}.right", state)

    def run_backtest(
        self, request: _vbm.WizardBacktestRequest
    ) -> StandardResponse[WizardBacktestResult]:
        """Compile an HSL document and run deterministic bar-by-bar simulation."""
        doc = self._coerce_hsl_document(request.document)
        if request.negate_signals:
            neg_rules = tuple(
                r.model_copy(
                    update={"when": _negate_node(r.when, distribute_logical=True)}
                )
                for r in doc.strategy.rules
            )
            doc = doc.model_copy(
                update={
                    "strategy": doc.strategy.model_copy(update={"rules": neg_rules})
                }
            )
        report = self._validator.validate(doc, raise_on_error=False)
        if not report.valid:
            msg = report.issues[0].message if report.issues else "Validation failed"
            issues_json: list[JSONValue] = [
                {"code": i.code, "message": i.message, "path": i.path}
                for i in report.issues
            ]
            raise DomainError(
                code="WIZARD_STRATEGY_INVALID",
                message=f"Cannot backtest invalid strategy '{doc.strategy.id}': {msg}",
                details={"strategy_id": doc.strategy.id, "issues": issues_json},
            )

        market_bars = self._build_market_bars(request.bars)
        plan = self._compiler.compile_to_runtime(doc)
        actual = BacktestRunner(StrategyRuntime(self._library.registry)).run(
            RunSpec(
                plan,
                doc.strategy.universe.symbols[0],
                Timeframe(doc.strategy.timeframe.primary),
                market_bars,
                request.settings,
            )
        )
        effects_seq = actual.effects
        result = self._summarize_backtest(
            request.backtest_id,
            doc.strategy.id,
            market_bars,
            effects_seq,
            actual,
        )
        self._backtest_results[request.backtest_id] = result
        self._revision += 1
        logger.info(
            "FR-wizard-visual-backtest: Completed backtest '%s' for '%s' "
            "bars=%d opened=%d closed=%d pnl=%.2f",
            request.backtest_id,
            doc.strategy.id,
            result.bars_evaluated,
            result.total_orders_opened,
            result.total_positions_closed,
            result.equity_delta,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    @staticmethod
    def _build_market_bars(bars: Sequence[WizardBarInput]) -> tuple[MarketBar, ...]:
        if bars:
            return tuple(
                MarketBar(
                    time=b.time,
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    tick_volume=int(b.volume),
                    real_volume=int(b.volume),
                )
                for b in bars
            )
        raise DomainError(
            code="HSL_MISSING_FEED", message="Backtesting requires explicit market bars"
        )

    @staticmethod
    def _summarize_backtest(
        backtest_id: str,
        strategy_id: str,
        bars: Sequence[MarketBar],
        effects_seq: Sequence[Any],
        actual: RunResult,
    ) -> WizardBacktestResult:
        opened = 0
        closed = 0
        modified = 0
        cancelled = 0
        equity_delta = actual.metrics["net_profit"]
        trade_log: list[WizardTradeLogEntry] = []

        for idx, (bar, eff) in enumerate(zip(bars, effects_seq, strict=False)):
            for req in eff.orders_to_open:
                opened += 1
                side = "long" if req.direction == 1 else "short"
                act_kind = (
                    "enter_market"
                    if req.order_type in (OrderType.BUY, OrderType.SELL)
                    else "enter_pending"
                )
                trade_log.append(
                    WizardTradeLogEntry(
                        bar_index=idx,
                        timestamp=bar.time,
                        action=act_kind,
                        symbol=req.symbol,
                        side=side,
                        volume=req.volume,
                        price=req.price,
                        sl=req.sl or 0.0,
                        tp=req.tp or 0.0,
                        comment=req.comment or "",
                    )
                )
            for close_req in eff.positions_to_close:
                closed += 1
                trade_log.append(
                    WizardTradeLogEntry(
                        bar_index=idx,
                        timestamp=bar.time,
                        action="exit_position",
                        symbol=str(getattr(close_req, "symbol", "EURUSD")),
                        side="any",
                        volume=close_req.volume or 0.0,
                        price=bar.close,
                        comment=close_req.comment or "",
                    )
                )
            modified += len(eff.orders_to_modify)
            cancelled += len(eff.orders_to_cancel)

        return WizardBacktestResult(
            backtest_id=backtest_id,
            strategy_id=strategy_id,
            status="COMPLETED",
            bars_evaluated=len(bars),
            total_orders_opened=opened,
            total_positions_closed=len(actual.trades),
            total_orders_modified=modified,
            total_orders_cancelled=cancelled,
            equity_delta=round(equity_delta, 4),
            trade_log=tuple(trade_log),
        )

    def stop_backtest(
        self, request: _vbm.StopWizardBacktestRequest
    ) -> StandardResponse[WizardBacktestStatus]:
        """Stop a tracked wizard backtest run and transition status to STOPPED."""
        existing = self._backtest_results.get(request.backtest_id)
        if existing is None:
            raise DomainError(
                code="WIZARD_BACKTEST_NOT_FOUND",
                message=f"Backtest '{request.backtest_id}' does not exist.",
                details={"backtest_id": request.backtest_id},
            )
        stopped_res = existing.model_copy(update={"status": "STOPPED"})
        self._backtest_results[request.backtest_id] = stopped_res
        self._revision += 1
        status_payload = WizardBacktestStatus(
            backtest_id=request.backtest_id,
            strategy_id=existing.strategy_id,
            status="STOPPED",
            stopped=True,
            message=f"Backtest '{request.backtest_id}' stopped.",
        )
        logger.info(
            "FR-wizard-visual-backtest: Stopped backtest '%s' for '%s'",
            request.backtest_id,
            existing.strategy_id,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=status_payload,
            json_payload=status_payload.model_dump(mode="json"),
            revision=self._revision,
        )

    def get_backtest_results(
        self, request: _vbm.GetWizardBacktestRequest
    ) -> StandardResponse[WizardBacktestResult]:
        """Return stored WizardBacktestResult for a completed or stopped run."""
        existing = self._backtest_results.get(request.backtest_id)
        if existing is None:
            raise DomainError(
                code="WIZARD_BACKTEST_NOT_FOUND",
                message=f"Backtest '{request.backtest_id}' does not exist.",
                details={"backtest_id": request.backtest_id},
            )
        logger.info(
            "FR-wizard-visual-backtest: Retrieved backtest '%s' status=%s",
            request.backtest_id,
            existing.status,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=existing,
            json_payload=existing.model_dump(mode="json"),
            revision=self._revision,
        )


__all__ = ["RuleNode", "VisualBlockService"]
