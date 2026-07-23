"""Concrete recovered Decomposing Trade signal evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.strategy.signals._mechanics import (
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
class DecomposingTradeEvaluator(_SignalEvaluatorBase):
    """Preserve four recovered Decomposing Trade RSI crossing signals."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered Decomposing Trade RSI crossings.

        Args:
            evidence: Point-in-time market evidence.
            indicators: Official RSI result for the configured period.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            Four stable active/inactive RSI signal states.

        Raises:
            _SignalConfigError: If an RSI period or threshold is invalid.
        """
        logger.info("Evaluating recovered Decomposing Trade signals")
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
        definitions = (
            ("LONG_ENTRY", "BUY", current >= oversold and previous < oversold),
            ("SHORT_ENTRY", "SELL", current <= overbought and previous > overbought),
            ("OPPOSE_BUY", "BUY", current <= oversold and previous > oversold),
            ("OPPOSE_SELL", "SELL", current >= overbought and previous < overbought),
        )
        return tuple(
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name=name,
                side=side,
                active=active,
                facts=facts,
            )
            for name, side, active in definitions
        )


__all__ = ["DecomposingTradeEvaluator"]
