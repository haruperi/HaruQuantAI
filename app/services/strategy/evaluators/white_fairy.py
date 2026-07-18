"""Concrete recovered White Fairy signal evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.strategy.evaluators._shared import (
    _current_previous,
    _decimal_parameter,
    _indicator_values,
    _integer_parameter,
    _make_signal,
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

_MIN_PERIOD = 2


@dataclass(frozen=True, slots=True)
class WhiteFairyEvaluator(_SignalEvaluatorBase):
    """Preserve recovered White Fairy RSI long and short entry signals."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered White Fairy RSI entry crossings.

        Args:
            evidence: Point-in-time market evidence.
            indicators: Official RSI result for the configured period.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            Long and short RSI entry signal states.

        Raises:
            _SignalConfigError: If an RSI period or threshold is invalid.
        """
        logger.info("Evaluating recovered White Fairy signals")
        period = _integer_parameter(config, "rsi_period")
        oversold = _decimal_parameter(config, "oversold")
        overbought = _decimal_parameter(config, "overbought")
        if period < _MIN_PERIOD or not oversold < overbought:
            raise _SignalConfigError("RSI period and thresholds are invalid")
        current, previous = _current_previous(
            _indicator_values(
                indicators, indicator_id="rsi", output_column=f"rsi_{period}"
            ),
            f"rsi_{period}",
        )
        facts = {
            "rsi": str(current),
            "oversold": str(oversold),
            "overbought": str(overbought),
        }
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_ENTRY",
                side="BUY",
                active=current >= oversold and previous < oversold,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_ENTRY",
                side="SELL",
                active=current <= overbought and previous > overbought,
                facts=facts,
            ),
        )


__all__ = ["WhiteFairyEvaluator"]
