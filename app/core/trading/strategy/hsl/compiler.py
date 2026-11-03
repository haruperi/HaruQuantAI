"""Validated HSL compiler and shared historical execution adapter.

Description:
    Preserves complete strategy meaning in a serializable, fingerprinted plan.
Purpose:
    FEAT-WIZARD-COMPILER: Shared HSL compilation and execution.
Key Capabilities:
    - FR-hsl-compile: Validate, bind, and log reproducible compiled plans.
Python API Usage:
    plan = StrategyCompiler().compile_to_runtime(document)
CLI Usage:
    uv run pytest tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    ParameterDefinition,
    RuleDefinition,
    RuleTriggerKind,
    StrategyDocument,
    StrategyEffects,
    TradingSetupConfig,
    VariableDefinition,
)
from app.core.trading.strategy.hsl.capabilities import block_fingerprints
from app.core.trading.strategy.hsl.documents import canonical_hsl_bytes
from app.core.trading.strategy.hsl.library import WizardBlockLibrary
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.core.trading.strategy.hsl.validation import StrategyValidator
from app.core.wizard.transform import NormalizedStrategy

logger = get_logger(__name__)
type BarEvent = BarUpdateEvent | MarketBar


class StrategyCompiler:
    """Compile a full AST instead of generating unbound synthetic references."""

    def __init__(
        self,
        library: WizardBlockLibrary | None = None,
        validator: StrategyValidator | None = None,
    ) -> None:
        self._library = library if library is not None else WizardBlockLibrary()
        self._validator = validator or StrategyValidator(library=self._library)

    @property
    def library(self) -> WizardBlockLibrary:
        """Return the shared block projection."""
        return self._library

    @property
    def validator(self) -> StrategyValidator:
        """Return schema, semantic, and execution capability validation."""
        return self._validator

    def compile_to_runtime(self, document: HSLStrategyDocument) -> StrategyDocument:
        """Validate and bind an independently executable strategy plan."""
        self.validator.validate(document, raise_on_error=True)
        strategy = document.strategy
        # Rules remain visible for legacy inventory clients; HSL execution uses
        # the complete AST below, never these descriptive entries.
        rules = tuple(
            RuleDefinition(
                rule.id,
                rule.name or rule.id,
                RuleTriggerKind(rule.event.type)
                if rule.event.type in ("on_bar_close", "on_bar_open", "on_tick")
                else RuleTriggerKind.ALL,
                is_enabled=rule.enabled,
            )
            for rule in sorted(
                strategy.rules, key=lambda item: (item.priority, item.id)
            )
        )
        plan = StrategyDocument(
            strategy.id,
            rules,
            tuple(
                VariableDefinition(name, spec.type, spec.initial)
                for name, spec in sorted(strategy.variables.items())
            ),
            tuple(
                ParameterDefinition(name, spec.type, spec.default)
                for name, spec in sorted(strategy.parameters.items())
            ),
            TradingSetupConfig(
                max_open_positions=strategy.risk_management.max_open_positions,
                magic_number=int(strategy.metadata.get("magic_number", 1000)),
            ),
            canonical_hsl_bytes(document).decode(),
            block_fingerprints(document, self.library.registry),
        )
        logger.info(
            "FR-hsl-compile: strategy=%s rules=%d blocks=%d",
            strategy.id,
            len(rules),
            len(plan.block_fingerprints),
        )
        return plan

    def evaluate_hsl_on_bars(
        self, document: HSLStrategyDocument, bars: Sequence[BarEvent], **options: Any
    ) -> tuple[StrategyEffects, ...]:
        """Execute through the same backtester used by ordinary strategy plans."""
        from app.core.trading.backtest.contracts import BacktestSettings, RunSpec
        from app.core.trading.backtest.runner import BacktestRunner
        from app.core.trading.strategy.runtime import StrategyRuntime

        plan = self.compile_to_runtime(document)
        events = tuple(bars)
        raw = tuple(
            item.bar if isinstance(item, BarUpdateEvent) else item for item in events
        )
        try:
            timeframe = Timeframe(document.strategy.timeframe.primary)
        except ValueError as error:
            raise DomainError(
                code="HSL_UNSUPPORTED_TIMEFRAME",
                message="Historical execution requires a concrete timeframe",
            ) from error
        for item in events:
            if isinstance(item, BarUpdateEvent) and (
                item.symbol != document.strategy.universe.symbols[0]
                or item.timeframe != timeframe
                or not item.is_bar_close
            ):
                raise DomainError(
                    code="HSL_EVENT_STREAM_UNSUPPORTED",
                    message="Mixed and bar-open streams require the event evaluator",
                )
        settings = options.pop("settings", BacktestSettings())
        result = BacktestRunner(StrategyRuntime(self.library.registry)).run(
            RunSpec(
                plan,
                document.strategy.universe.symbols[0],
                timeframe,
                raw,
                settings,
                **options,
            )
        )
        return result.effects

    def compile_to_normalized(
        self, document: HSLStrategyDocument
    ) -> NormalizedStrategy:
        """Preserve HSL source for native export; target renderers must gate support."""
        self.compile_to_runtime(document)
        import re

        name = re.sub(r"[^a-zA-Z0-9_]", "_", document.strategy.name) or "Strategy"
        if name[0].isdigit():
            name = "var_" + name
        return NormalizedStrategy(
            document.strategy.id,
            name,
            "".join(part[:1].upper() + part[1:] for part in name.split("_") if part),
            1000,
            document.strategy.risk_management.max_open_positions,
            (),
            (),
            (),
            hsl_json=canonical_hsl_bytes(document).decode(),
            block_fingerprints=block_fingerprints(document, self.library.registry),
        )


__all__ = ["BarEvent", "StrategyCompiler"]
