"""Concrete recovered non-random RandomWalk trigger evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.strategy.evaluators._shared import (
    _integer_parameter,
    _make_signal,
    _position_tag,
    _SignalConfigError,
    _SignalEvaluatorBase,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.indicators import IndicatorResult
    from app.services.strategy.contracts import (
        StrategyExecutionContext,
        StrategySignal,
        StrategySignalEvidence,
        ValidatedStrategyConfig,
    )


@dataclass(frozen=True, slots=True)
class RandomWalkEvaluator(_SignalEvaluatorBase):
    """Preserve deterministic flat-state triggers from the RandomWalk source."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered long and short basket restart triggers.

        Args:
            evidence: Point-in-time market and owned-position tag evidence.
            indicators: Unused; the recovered source has no market indicator.
            config: Validated immutable configuration with source magic numbers.
            context: Fixed deterministic evaluation context.

        Returns:
            Long and short flat-state trigger signals.

        Raises:
            _SignalConfigError: If magic-number parameters are invalid.
        """
        logger.info("Evaluating recovered non-random RandomWalk triggers")
        del indicators
        buy_magic = _integer_parameter(config, "buy_magic_number")
        sell_magic = _integer_parameter(config, "sell_magic_number")
        if buy_magic == sell_magic:
            raise _SignalConfigError("RandomWalk magic numbers must be distinct")
        buy_tag = _position_tag(buy_magic, "BUY")
        sell_tag = _position_tag(sell_magic, "SELL")
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_BASKET_TRIGGER",
                side="BUY",
                active=buy_tag not in evidence.active_position_tags,
                facts={"magic_number": buy_magic, "random_signal": False},
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_BASKET_TRIGGER",
                side="SELL",
                active=sell_tag not in evidence.active_position_tags,
                facts={"magic_number": sell_magic, "random_signal": False},
            ),
        )


__all__ = ["RandomWalkEvaluator"]
