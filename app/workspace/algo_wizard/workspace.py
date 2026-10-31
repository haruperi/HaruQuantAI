"""AppWizard workspace coordinator service (WizardService).

Description:
    Implements WizardService (AppWizard equivalent), coordinating the built-in
    canonical HSL 1.0 strategy examples catalog (/AlgoWizard/examples/examples.json
    and /algowizard/loadExample), strategy file import and persistence with
    automatic legacy upgrade and 3-pass validation (/algowizard/loadFile and
    /algowizard/saveFile), and compilation handoff to the Retester workspace
    (/algowizard/saveToRetester).

Purpose:
    FEAT-WIZARD-WORKSPACE: Gate G7 (Phase 5.7, WO-WZ-WORKSPACE-COORDINATOR /
    I-AppWizard) workspace coordinator for HSL 1.0 strategy authoring, file
    exchange, and Retester handoff.

Key Capabilities:
    - FR-wizard-examples-catalog: Serves and loads validated built-in HSL 1.0
      strategy templates (EMA Crossover, RSI Mean Reversion, ATR Breakout,
      Multi-Timeframe Trend Filter) with deterministic cloning.
    - FR-wizard-file-exchange: Loads and persists HSL 1.0 strategy JSON files
      with legacy document auto-upgrade, filename sanitization, SHA-256 content
      hashing, and MRU recent-file tracking.
    - FR-wizard-retester-handoff: Validates and compiles HSL 1.0 documents into
      Retester-ready bundles containing both HSLStrategyDocument and runtime
      StrategyDocument.

Python API Usage:
    from app.workspace.algo_wizard.workspace import WizardService
    from app.workspace.algo_wizard.workspace_models import LoadWizardExampleRequest

    service = WizardService()
    resp = service.load_example(LoadWizardExampleRequest(example_id="ema_crossover"))

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_workspace.py --no-cov -q
"""

from __future__ import annotations

import json
import re
from pathlib import PurePath
from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.core.lib.responses import StandardResponse
from app.workspace.algo_wizard.catalogue import WizardCatalogueService
from app.workspace.algo_wizard.compiler import StrategyCompiler
from app.workspace.algo_wizard.documents import (
    canonical_hsl_bytes,
    compute_document_hash,
    parse_hsl_document,
    upgrade_legacy_wizard_document,
)
from app.workspace.algo_wizard.library import WizardBlockLibrary
from app.workspace.algo_wizard.models import (
    ComparisonConditionNode,
    HSLStrategyDocument,
    HSLStrategyPayload,
    LifecycleEventSpec,
    LogicalConditionNode,
    NotConditionNode,
    OrderMarketActionNode,
    ParameterSpec,
    PositionCloseActionNode,
    RuleNode,
    StateConditionNode,
    TimeframeSpec,
    UniverseSpec,
)
from app.workspace.algo_wizard.strategies import StrategyDocumentService
from app.workspace.algo_wizard.validation import StrategyValidator, ValidationReport
from app.workspace.algo_wizard.value_models import (
    EvaluationContext,
    IndicatorExpressionNode,
    MarketPriceNode,
    MathExpressionNode,
    ParameterRefNode,
    StopLossSpec,
    TakeProfitSpec,
    ValueLiteralNode,
)
from app.workspace.algo_wizard.visual_blocks import VisualBlockService
from app.workspace.algo_wizard.workspace_models import (
    ListWizardExamplesRequest,
    LoadStrategyFileRequest,
    LoadWizardExampleRequest,
    RetesterHandoffResult,
    SavedStrategyFileResult,
    SaveStrategyFileRequest,
    SaveToRetesterRequest,
    WizardExamplePayload,
    WizardExampleSummary,
)

logger = get_logger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _build_typed_response[T](
    *,
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data."""
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=json_payload,
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


def _validation_error_details(
    strategy_id: str,
    report: ValidationReport,
) -> dict[str, JSONValue]:
    """Format ValidationReport issues as finite JSON error details."""
    issues_json: list[JSONValue] = [
        {
            "code": issue.code,
            "message": issue.message,
            "path": issue.path,
            "node_id": issue.node_id,
        }
        for issue in report.issues
    ]
    return {
        "strategy_id": strategy_id,
        "issue_count": len(report.issues),
        "issues": issues_json,
    }


def _build_ema_crossover_example() -> WizardExamplePayload:
    """Construct the canonical EMA Crossover HSL 1.0 example template."""
    summary = WizardExampleSummary(
        example_id="ema_crossover",
        name="EMA Crossover",
        category="trend",
        description=(
            "Trend-following dual EMA crossover strategy entering long when "
            "the fast EMA crosses above the slow EMA and short on the reverse."
        ),
        tags=("ema", "crossover", "trend", "h1"),
    )
    fast_ema = IndicatorExpressionNode(
        name="indicator.ema",
        params={"period": ParameterRefNode(name="fast_period")},
    )
    slow_ema = IndicatorExpressionNode(
        name="indicator.ema",
        params={"period": ParameterRefNode(name="slow_period")},
    )
    doc = HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="example_ema_crossover",
            name="EMA Crossover",
            description=summary.description,
            universe=UniverseSpec(symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1"),
            parameters={
                "fast_period": ParameterSpec(
                    type="int",
                    default=12,
                    min=2,
                    max=100,
                    step=1,
                    description="Fast EMA lookback period",
                ),
                "slow_period": ParameterSpec(
                    type="int",
                    default=26,
                    min=5,
                    max=250,
                    step=1,
                    description="Slow EMA lookback period",
                ),
            },
            rules=(
                RuleNode(
                    id="long_entry_rule",
                    name="Long Entry on Fast EMA Cross Above Slow EMA",
                    priority=10,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            NotConditionNode(
                                condition=StateConditionNode(
                                    state="position.is_long",
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="crosses_above",
                                left=fast_ema,
                                right=slow_ema,
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            comment="EMA Cross Long",
                        ),
                    ),
                ),
                RuleNode(
                    id="short_entry_rule",
                    name="Short Entry on Fast EMA Cross Below Slow EMA",
                    priority=20,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            NotConditionNode(
                                condition=StateConditionNode(
                                    state="position.is_short",
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="crosses_below",
                                left=fast_ema,
                                right=slow_ema,
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="short",
                            comment="EMA Cross Short",
                        ),
                    ),
                ),
            ),
        ),
    )
    return WizardExamplePayload(summary=summary, document=doc)


def _build_rsi_mean_reversion_example() -> WizardExamplePayload:
    """Construct the canonical RSI Mean Reversion HSL 1.0 example template."""
    summary = WizardExampleSummary(
        example_id="rsi_mean_reversion",
        name="RSI Mean Reversion",
        category="mean_reversion",
        description=(
            "Oscillator mean-reversion strategy buying oversold RSI dips "
            "and closing positions when RSI recovers into overbought territory."
        ),
        tags=("rsi", "mean_reversion", "oscillator", "h1"),
    )
    rsi_expr = IndicatorExpressionNode(
        name="indicator.rsi",
        params={"period": ParameterRefNode(name="rsi_period")},
    )
    doc = HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="example_rsi_mean_reversion",
            name="RSI Mean Reversion",
            description=summary.description,
            universe=UniverseSpec(symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1"),
            parameters={
                "rsi_period": ParameterSpec(
                    type="int",
                    default=14,
                    min=2,
                    max=100,
                    step=1,
                    description="RSI lookback period",
                ),
                "oversold_level": ParameterSpec(
                    type="float",
                    default=30.0,
                    min=5.0,
                    max=50.0,
                    step=1.0,
                    description="Oversold RSI entry threshold",
                ),
                "overbought_level": ParameterSpec(
                    type="float",
                    default=70.0,
                    min=50.0,
                    max=95.0,
                    step=1.0,
                    description="Overbought RSI exit threshold",
                ),
            },
            rules=(
                RuleNode(
                    id="rsi_buy_oversold",
                    name="Buy on Oversold RSI",
                    priority=10,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_flat"),
                            ComparisonConditionNode(
                                operator="less_than",
                                left=rsi_expr,
                                right=ParameterRefNode(name="oversold_level"),
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            comment="RSI Oversold Buy",
                        ),
                    ),
                ),
                RuleNode(
                    id="rsi_exit_overbought",
                    name="Close Long on Overbought RSI",
                    priority=20,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_long"),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=rsi_expr,
                                right=ParameterRefNode(name="overbought_level"),
                            ),
                        ),
                    ),
                    then=(
                        PositionCloseActionNode(
                            target_side="long",
                            reason="RSI Overbought Exit",
                        ),
                    ),
                ),
            ),
        ),
    )
    return WizardExamplePayload(summary=summary, document=doc)


def _build_atr_breakout_example() -> WizardExamplePayload:
    """Construct the canonical ATR Volatility Breakout HSL 1.0 example template."""
    summary = WizardExampleSummary(
        example_id="atr_breakout",
        name="ATR Volatility Breakout",
        category="breakout",
        description=(
            "Volatility channel breakout strategy entering long when close "
            "breaks above SMA plus an ATR multiple, with ATR-based protective stops."
        ),
        tags=("atr", "sma", "breakout", "volatility", "h1"),
    )
    upper_band = MathExpressionNode(
        operator="add",
        left=IndicatorExpressionNode(
            name="indicator.sma",
            params={"period": ParameterRefNode(name="sma_period")},
        ),
        right=MathExpressionNode(
            operator="multiply",
            left=IndicatorExpressionNode(
                name="indicator.atr",
                params={"period": ParameterRefNode(name="atr_period")},
            ),
            right=ParameterRefNode(name="atr_multiplier"),
        ),
    )
    doc = HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="example_atr_breakout",
            name="ATR Volatility Breakout",
            description=summary.description,
            universe=UniverseSpec(symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1"),
            parameters={
                "sma_period": ParameterSpec(
                    type="int",
                    default=20,
                    min=5,
                    max=200,
                    step=1,
                    description="Baseline SMA period",
                ),
                "atr_period": ParameterSpec(
                    type="int",
                    default=14,
                    min=2,
                    max=100,
                    step=1,
                    description="ATR volatility lookback period",
                ),
                "atr_multiplier": ParameterSpec(
                    type="float",
                    default=1.5,
                    min=0.5,
                    max=5.0,
                    step=0.1,
                    description="Channel width ATR multiplier",
                ),
            },
            rules=(
                RuleNode(
                    id="atr_breakout_long",
                    name="Breakout Above Upper Volatility Channel",
                    priority=10,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_flat"),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=MarketPriceNode(field="close"),
                                right=upper_band,
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            stop_loss=StopLossSpec(
                                type="atr",
                                period=ValueLiteralNode(value=14, value_type="int"),
                                multiplier=ValueLiteralNode(
                                    value=2.0, value_type="float"
                                ),
                            ),
                            take_profit=TakeProfitSpec(
                                type="atr",
                                period=ValueLiteralNode(value=14, value_type="int"),
                                multiplier=ValueLiteralNode(
                                    value=3.0, value_type="float"
                                ),
                            ),
                            comment="ATR Channel Breakout",
                        ),
                    ),
                ),
            ),
        ),
    )
    return WizardExamplePayload(summary=summary, document=doc)


def _build_mtf_trend_filter_example() -> WizardExamplePayload:
    """Construct the canonical Multi-Timeframe Trend Filter HSL 1.0 example."""
    summary = WizardExampleSummary(
        example_id="mtf_trend_filter",
        name="Multi-Timeframe Trend Filter",
        category="multi_timeframe",
        description=(
            "Multi-timeframe strategy aligning H4 EMA trend direction with "
            "H1 RSI pullback entries."
        ),
        tags=("mtf", "ema", "rsi", "trend", "h1", "h4"),
    )
    h4_ctx = EvaluationContext(timeframe="H4")
    doc = HSLStrategyDocument(
        schema_version="1.0.0",
        strategy=HSLStrategyPayload(
            id="example_mtf_trend_filter",
            name="Multi-Timeframe Trend Filter",
            description=summary.description,
            universe=UniverseSpec(symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1", additional=("H4",)),
            parameters={
                "trend_ema_period": ParameterSpec(
                    type="int",
                    default=50,
                    min=10,
                    max=200,
                    step=5,
                    description="Higher-timeframe EMA period",
                ),
                "entry_rsi_period": ParameterSpec(
                    type="int",
                    default=14,
                    min=2,
                    max=50,
                    step=1,
                    description="Primary-timeframe RSI period",
                ),
            },
            rules=(
                RuleNode(
                    id="mtf_long_pullback",
                    name="H4 Uptrend + H1 RSI Pullback Entry",
                    priority=10,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_flat"),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=MarketPriceNode(
                                    field="close",
                                    context=h4_ctx,
                                ),
                                right=IndicatorExpressionNode(
                                    name="indicator.ema",
                                    params={
                                        "period": ParameterRefNode(
                                            name="trend_ema_period"
                                        ),
                                    },
                                    context=h4_ctx,
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="less_than",
                                left=IndicatorExpressionNode(
                                    name="indicator.rsi",
                                    params={
                                        "period": ParameterRefNode(
                                            name="entry_rsi_period"
                                        ),
                                    },
                                ),
                                right=ValueLiteralNode(
                                    value_type="float",
                                    value=35.0,
                                ),
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            comment="MTF Trend Pullback Buy",
                        ),
                    ),
                ),
            ),
        ),
    )
    return WizardExamplePayload(summary=summary, document=doc)


def _build_default_examples() -> dict[str, WizardExamplePayload]:
    """Build the ordered registry of canonical HSL 1.0 built-in examples."""
    examples = (
        _build_ema_crossover_example(),
        _build_rsi_mean_reversion_example(),
        _build_atr_breakout_example(),
        _build_mtf_trend_filter_example(),
    )
    return {item.summary.example_id: item for item in examples}


class WizardService:
    """AppWizard coordinator for examples, file exchange, and Retester handoff."""

    def __init__(
        self,
        *,
        library: WizardBlockLibrary | None = None,
        validator: StrategyValidator | None = None,
        compiler: StrategyCompiler | None = None,
        catalogue_service: WizardCatalogueService | None = None,
        strategy_service: StrategyDocumentService | None = None,
        visual_block_service: VisualBlockService | None = None,
    ) -> None:
        """Initialize WizardService and its shared HSL 1.0 collaborators."""
        self._library = library if library is not None else WizardBlockLibrary()
        self._validator = validator or StrategyValidator(library=self._library)
        self._compiler = compiler or StrategyCompiler(
            library=self._library,
            validator=self._validator,
        )
        self._catalogue_service = catalogue_service or WizardCatalogueService(
            library=self._library,
        )
        self._strategy_service = strategy_service or StrategyDocumentService(
            validator=self._validator,
            compiler=self._compiler,
        )
        self._visual_block_service = visual_block_service or VisualBlockService(
            library=self._library,
            validator=self._validator,
            compiler=self._compiler,
        )
        self._examples: dict[str, WizardExamplePayload] = _build_default_examples()
        self._files: dict[str, SavedStrategyFileResult] = {}
        self._recent_files: list[str] = []
        self._retester_handoffs: dict[str, RetesterHandoffResult] = {}
        self._revision: int = 1
        logger.info(
            "FR-wizard-examples-catalog: initialized WizardService with %d examples",
            len(self._examples),
        )

    @property
    def validator(self) -> StrategyValidator:
        """Return the StrategyValidator instance."""
        return self._validator

    @property
    def compiler(self) -> StrategyCompiler:
        """Return the StrategyCompiler instance."""
        return self._compiler

    @property
    def catalogue_service(self) -> WizardCatalogueService:
        """Return the shared WizardCatalogueService instance."""
        return self._catalogue_service

    @property
    def strategy_service(self) -> StrategyDocumentService:
        """Return the shared StrategyDocumentService instance."""
        return self._strategy_service

    @property
    def visual_block_service(self) -> VisualBlockService:
        """Return the shared VisualBlockService instance."""
        return self._visual_block_service

    def list_examples(
        self,
        request: ListWizardExamplesRequest | None = None,
    ) -> StandardResponse[tuple[WizardExampleSummary, ...]]:
        """Serve /AlgoWizard/examples/examples.json catalog of HSL 1.0 templates."""
        req = request or ListWizardExamplesRequest()
        category_filter = req.category.strip().lower() if req.category else None
        query_filter = req.query.strip().lower() if req.query else None

        summaries: list[WizardExampleSummary] = []
        for payload in self._examples.values():
            summary = payload.summary
            if category_filter and summary.category.lower() != category_filter:
                continue
            if query_filter:
                haystack = " ".join(
                    (
                        summary.example_id,
                        summary.name,
                        summary.category,
                        summary.description,
                        *summary.tags,
                    )
                ).lower()
                if query_filter not in haystack:
                    continue
            summaries.append(summary)

        result = tuple(summaries)
        logger.info(
            "FR-wizard-examples-catalog: list_examples request_id=%s count=%d",
            req.request_id,
            len(result),
        )
        return _build_typed_response(
            request_id=req.request_id,
            data=result,
            json_payload=[item.model_dump(mode="json") for item in result],
            revision=self._revision,
        )

    def load_example(
        self,
        request: LoadWizardExampleRequest,
    ) -> StandardResponse[WizardExamplePayload]:
        """Serve /algowizard/loadExample by returning a validated example clone."""
        normalized_id = self._normalize_example_id(request.example_id)
        payload = self._examples.get(normalized_id)
        if payload is None:
            logger.warning(
                "FR-wizard-examples-catalog: unknown example_id=%s (normalized=%s)",
                request.example_id,
                normalized_id,
            )
            raise DomainError(
                code="WIZARD_EXAMPLE_NOT_FOUND",
                message=f"Built-in wizard example '{request.example_id}' not found",
                details={"example_id": request.example_id},
            )

        cloned_doc = parse_hsl_document(canonical_hsl_bytes(payload.document))
        report = self._validator.validate(cloned_doc, raise_on_error=False)
        if not report.valid:  # pragma: no cover - defensive invariant check
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=f"Built-in example '{normalized_id}' failed HSL validation",
                details=_validation_error_details(cloned_doc.strategy.id, report),
            )

        result = WizardExamplePayload(
            summary=payload.summary,
            document=cloned_doc,
        )
        logger.info(
            "FR-wizard-examples-catalog: load_example request_id=%s "
            "example_id=%s strategy_id=%s",
            request.request_id,
            normalized_id,
            cloned_doc.strategy.id,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    def load_file(
        self,
        request: LoadStrategyFileRequest,
    ) -> StandardResponse[HSLStrategyDocument]:
        """Serve /algowizard/loadFile from store or inline HSL/legacy payload."""
        doc = self._resolve_file_document(request)
        report = self._validator.validate(doc, raise_on_error=False)
        if request.strict and not report.valid:
            logger.warning(
                "FR-wizard-file-exchange: load_file rejected invalid strategy_id=%s",
                doc.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Strategy '{doc.strategy.id}' failed HSL validation with "
                    f"{len(report.issues)} issue(s)"
                ),
                details=_validation_error_details(doc.strategy.id, report),
            )

        if request.file_id:
            self._record_recent_file(self._sanitize_filename(request.file_id))

        logger.info(
            "FR-wizard-file-exchange: load_file request_id=%s strategy_id=%s valid=%s",
            request.request_id,
            doc.strategy.id,
            report.valid,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=doc,
            json_payload=doc.model_dump(mode="json"),
            revision=self._revision,
        )

    def save_file(
        self,
        request: SaveStrategyFileRequest,
    ) -> StandardResponse[SavedStrategyFileResult]:
        """Serve /algowizard/saveFile by validating and persisting an HSL document."""
        report = self._validator.validate(request.document, raise_on_error=False)
        if request.strict and not report.valid:
            logger.warning(
                "FR-wizard-file-exchange: save_file rejected invalid strategy_id=%s",
                request.document.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Cannot save invalid HSL strategy '{request.document.strategy.id}'"
                ),
                details=_validation_error_details(
                    request.document.strategy.id,
                    report,
                ),
            )

        raw_name = request.filename or request.file_id or request.document.strategy.id
        filename = self._sanitize_filename(raw_name)
        file_id = self._sanitize_file_id(request.file_id or filename)
        existing = self._files.get(file_id)
        revision = existing.revision + 1 if existing is not None else 1
        doc_hash = compute_document_hash(request.document)
        cloned_doc = parse_hsl_document(canonical_hsl_bytes(request.document))

        self._record_recent_file(filename)
        self._revision += 1
        saved = SavedStrategyFileResult(
            file_id=file_id,
            filename=filename,
            strategy_id=cloned_doc.strategy.id,
            revision=revision,
            document_hash=doc_hash,
            recent_files=tuple(self._recent_files),
            document=cloned_doc,
        )
        self._files[file_id] = saved

        logger.info(
            "FR-wizard-file-exchange: save_file request_id=%s file_id=%s "
            "filename=%s rev=%d hash=%s",
            request.request_id,
            file_id,
            filename,
            revision,
            doc_hash,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=saved,
            json_payload=saved.model_dump(mode="json"),
            revision=self._revision,
        )

    def save_to_retester(
        self,
        request: SaveToRetesterRequest,
    ) -> StandardResponse[RetesterHandoffResult]:
        """Serve /algowizard/saveToRetester by validating and compiling for Retester."""
        report = self._validator.validate(request.document, raise_on_error=False)
        if not report.valid:
            logger.warning(
                "FR-wizard-retester-handoff: rejected invalid strategy_id=%s",
                request.document.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Cannot hand off invalid strategy "
                    f"'{request.document.strategy.id}' to Retester"
                ),
                details=_validation_error_details(
                    request.document.strategy.id,
                    report,
                ),
            )

        compiled = self._compiler.compile_to_runtime(request.document)
        doc_hash = compute_document_hash(request.document)
        cloned_doc = parse_hsl_document(canonical_hsl_bytes(request.document))
        handoff_id = (
            f"retester-{cloned_doc.strategy.id}-{len(self._retester_handoffs) + 1}"
        )
        result = RetesterHandoffResult(
            handoff_id=handoff_id,
            retester_project_name=request.retester_project_name,
            strategy_id=cloned_doc.strategy.id,
            document_hash=doc_hash,
            document=cloned_doc,
            compiled_document=compiled,
        )
        self._retester_handoffs[handoff_id] = result
        self._revision += 1

        logger.info(
            "FR-wizard-retester-handoff: save_to_retester request_id=%s "
            "handoff_id=%s strategy_id=%s project=%s",
            request.request_id,
            handoff_id,
            cloned_doc.strategy.id,
            request.retester_project_name,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    def get_saved_file(self, file_id: str) -> SavedStrategyFileResult | None:
        """Look up a previously saved strategy file by file_id or filename."""
        direct = self._files.get(file_id)
        if direct is not None:
            return direct
        normalized = self._sanitize_file_id(file_id)
        return self._files.get(normalized)

    def list_saved_files(self) -> tuple[SavedStrategyFileResult, ...]:
        """Return all saved strategy file records in insertion order."""
        return tuple(self._files.values())

    def list_retester_handoffs(self) -> tuple[RetesterHandoffResult, ...]:
        """Return all recorded Retester handoff bundles."""
        return tuple(self._retester_handoffs.values())

    def _resolve_file_document(
        self,
        request: LoadStrategyFileRequest,
    ) -> HSLStrategyDocument:
        """Resolve an HSLStrategyDocument from saved file_id or inline payload."""
        if request.payload is not None:
            return self._parse_payload(request.payload)

        file_id = request.file_id or ""
        saved = self.get_saved_file(file_id)
        if saved is None:
            logger.warning(
                "FR-wizard-file-exchange: file_id=%s not found in workspace store",
                file_id,
            )
            raise DomainError(
                code="WIZARD_FILE_NOT_FOUND",
                message=f"Saved strategy file '{file_id}' not found",
                details={"file_id": file_id},
            )
        return parse_hsl_document(canonical_hsl_bytes(saved.document))

    def _parse_payload(
        self,
        payload: dict[str, Any] | str,
    ) -> HSLStrategyDocument:
        """Parse an inline JSON string or dictionary as HSL 1.0 or legacy wizard."""
        raw_dict: dict[str, Any]
        if isinstance(payload, str):
            try:
                loaded = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise DomainError(
                    code="WIZARD_INVALID_JSON",
                    message=f"Strategy file payload is not valid JSON: {exc.msg}",
                    details={"pos": exc.pos},
                ) from exc
            if not isinstance(loaded, dict):
                raise DomainError(
                    code="WIZARD_INVALID_JSON",
                    message="Strategy file JSON root must be an object",
                )
            raw_dict = loaded
        else:
            raw_dict = dict(payload)

        if "schema_version" in raw_dict and isinstance(raw_dict.get("strategy"), dict):
            return parse_hsl_document(raw_dict)
        return upgrade_legacy_wizard_document(raw_dict)

    @staticmethod
    def _normalize_example_id(raw_id: str) -> str:
        """Normalize an example identifier or filename into a catalog key."""
        leaf = PurePath(raw_id.strip().replace("\\", "/")).name
        for ext in (".json", ".sqx", ".sqw", ".str", ".sq4"):
            if leaf.lower().endswith(ext):
                leaf = leaf[: -len(ext)]
                break
        return re.sub(r"[\s\-]+", "_", leaf.strip().lower())

    @staticmethod
    def _sanitize_filename(raw_name: str) -> str:
        """Sanitize a user-provided filename into a safe `<stem>.json` name."""
        leaf = PurePath(raw_name.strip().replace("\\", "/")).name
        for ext in (".json", ".sqx", ".sqw", ".str", ".sq4"):
            if leaf.lower().endswith(ext):
                leaf = leaf[: -len(ext)]
                break
        cleaned = _SAFE_FILENAME_RE.sub("_", leaf).strip("._-")
        if not cleaned:
            cleaned = "strategy"
        return f"{cleaned}.json"

    @classmethod
    def _sanitize_file_id(cls, raw_id: str) -> str:
        """Sanitize a file identifier into its canonical stem."""
        filename = cls._sanitize_filename(raw_id)
        return filename[: -len(".json")]

    def _record_recent_file(self, filename: str) -> None:
        """Record a filename at the front of the MRU list."""
        if filename in self._recent_files:
            self._recent_files.remove(filename)
        self._recent_files.insert(0, filename)
        del self._recent_files[20:]


__all__ = [
    "WizardService",
]
