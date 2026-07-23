"""Structural contract implemented by every concrete signal evaluator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.utils import logger

if TYPE_CHECKING:
    from app.services.indicators import IndicatorResult
    from app.services.strategy.contracts import (
        StrategyExecutionContext,
        StrategySignal,
        StrategySignalEvidence,
        ValidatedStrategyConfig,
    )


class SignalEvaluator(Protocol):
    """Structural contract implemented by concrete signal evaluators."""

    strategy_id: str
    strategy_version: str
    module_path: str
    source_hash: str
    artifact_hash: str
    dependency_hash: str

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Declare concrete signal evaluation behavior.

        Args:
            evidence: Concrete signal evidence.
            indicators: Official precomputed indicator results.
            config: Validated immutable strategy configuration.
            context: Fixed deterministic evaluation context.

        Raises:
            NotImplementedError: Protocol declaration has no implementation.
        """
        logger.debug("Invoking concrete Strategy signal evaluator protocol")
        del evidence, indicators, config, context
        raise NotImplementedError


__all__ = ["SignalEvaluator"]
