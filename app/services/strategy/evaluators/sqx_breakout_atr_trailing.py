"""Concrete recovered SQX breakout and ATR fact evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.strategy.signals._mechanics import (
    _bar_records,
    _current_value,
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
    from app.services.strategy.contracts._base import JsonValue

_MIN_ATR_PERIOD = 2


def _atr_distance(
    indicators: tuple[IndicatorResult, ...],
    config: ValidatedStrategyConfig,
    *,
    period_parameter: str,
    multiplier_parameter: str,
) -> Decimal:
    """Return one supplied ATR value multiplied by its recovered parameter.

    Args:
        indicators: Official ATR results.
        config: Validated immutable configuration.
        period_parameter: Name of the ATR-period parameter.
        multiplier_parameter: Name of the ATR-multiplier parameter.

    Returns:
        Exact non-negative ATR distance.

    Raises:
        _SignalConfigError: If the period or multiplier is invalid.
    """
    logger.debug("Calculating recovered SQX ATR distance")
    period = _integer_parameter(config, period_parameter)
    multiplier = _decimal_parameter(config, multiplier_parameter)
    if period < _MIN_ATR_PERIOD or multiplier < 0:
        raise _SignalConfigError("SQX ATR periods and multipliers are invalid")
    value = _current_value(
        _indicator_values(
            indicators, indicator_id="atr", output_column=f"atr_{period}"
        ),
        f"atr_{period}",
    )
    return value * multiplier


@dataclass(frozen=True, slots=True)
class SQXBreakoutAtrTrailingEvaluator(_SignalEvaluatorBase):
    """Preserve recovered SQX channel-breakout signals and ATR facts."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered completed-bar SQX breakout rules.

        Args:
            evidence: Point-in-time canonical bar evidence.
            indicators: Official ATR results for protection facts.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            Long and short breakout signal states with ATR distance facts.

        Raises:
            _SignalConfigError: If breakout or ATR configuration is invalid.
        """
        logger.info("Evaluating recovered SQX breakout signals")
        lookback = _integer_parameter(config, "breakout_lookback")
        if lookback < 1:
            raise _SignalConfigError("breakout_lookback must be positive")
        bars = _bar_records(evidence.primary_market)
        long_signal = False
        short_signal = False
        if len(bars) >= lookback + 2:
            signal_bar = bars[-1]
            prior_bar = bars[-2]
            signal_reference = bars[-lookback - 1 : -1]
            prior_reference = bars[-lookback - 2 : -2]
            highest_for_signal = max(bar.high for bar in signal_reference)
            lowest_for_signal = min(bar.low for bar in signal_reference)
            highest_for_prior = max(bar.high for bar in prior_reference)
            lowest_for_prior = min(bar.low for bar in prior_reference)
            long_signal = (
                signal_bar.open > highest_for_signal
                and prior_bar.open <= highest_for_prior
            )
            short_signal = (
                signal_bar.open < lowest_for_signal
                and prior_bar.open >= lowest_for_prior
            )
        facts: dict[str, JsonValue] = {
            "breakout_lookback": lookback,
            "stop_distance": str(
                _atr_distance(
                    indicators,
                    config,
                    period_parameter="atr_stop_period",
                    multiplier_parameter="stop_loss_atr_multiple",
                )
            ),
            "trailing_distance": str(
                _atr_distance(
                    indicators,
                    config,
                    period_parameter="trailing_stop_atr_period",
                    multiplier_parameter="trailing_stop_atr_multiple",
                )
            ),
            "trailing_activation_distance": str(
                _atr_distance(
                    indicators,
                    config,
                    period_parameter="trailing_activation_atr_period",
                    multiplier_parameter="trailing_activation_atr_multiple",
                )
            ),
        }
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_ENTRY",
                side="BUY",
                active=long_signal,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_ENTRY",
                side="SELL",
                active=short_signal,
                facts=facts,
            ),
        )


__all__ = ["SQXBreakoutAtrTrailingEvaluator"]
