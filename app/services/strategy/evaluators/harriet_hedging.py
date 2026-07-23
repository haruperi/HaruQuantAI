"""Concrete recovered Harriet Hedging signal evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.strategy.signals._mechanics import (
    _bar_records,
    _decimal_parameter,
    _make_signal,
    _related_market,
    _SignalConfigError,
    _SignalDataError,
    _SignalEvaluatorBase,
    _text_parameter,
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

_MIN_BARS = 2


@dataclass(frozen=True, slots=True)
class HarrietHedgingEvaluator(_SignalEvaluatorBase):
    """Preserve recovered point-in-time multi-timeframe structure signals."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered Harriet higher-low and lower-high confirmations.

        Args:
            evidence: Primary lower and named higher-timeframe market evidence.
            indicators: Unused; Harriet's recovered signal uses bar structure.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            Long and short confirmation signal states.

        Raises:
            _SignalConfigError: If a distance threshold is invalid.
            _SignalDataError: If timeframe or bar evidence is invalid.
        """
        logger.info("Evaluating recovered Harriet Hedging signals")
        del indicators
        higher_name = _text_parameter(config, "higher_timeframe")
        lower_name = _text_parameter(config, "lower_timeframe")
        if evidence.primary_market.timeframe != lower_name:
            raise _SignalDataError("primary market must match lower_timeframe")
        higher_market = _related_market(evidence, higher_name)
        if (
            higher_market.timeframe != higher_name
            or higher_market.symbol != evidence.primary_market.symbol
        ):
            raise _SignalDataError("higher timeframe market identity does not match")
        lower_bars = _bar_records(evidence.primary_market)
        if len(lower_bars) < _MIN_BARS:
            raise _SignalDataError("Harriet requires two lower-timeframe bars")
        current_lower = lower_bars[-1]
        previous_lower = lower_bars[-2]
        available_higher = tuple(
            record
            for record in _bar_records(higher_market)
            if record.available_at <= current_lower.timestamp
        )
        if len(available_higher) < _MIN_BARS:
            raise _SignalDataError(
                "Harriet requires two available higher-timeframe bars"
            )
        current_higher = available_higher[-1]
        previous_higher = available_higher[-2]
        multiplier = _decimal_parameter(config, "pip_multiplier")
        higher_distance = (
            _decimal_parameter(config, "higher_min_distance_pips")
            * evidence.point_size
            * multiplier
        )
        lower_distance = (
            _decimal_parameter(config, "lower_min_distance_pips")
            * evidence.point_size
            * multiplier
        )
        if higher_distance < 0 or lower_distance < 0:
            raise _SignalConfigError("Harriet distance thresholds must be non-negative")
        higher_low = (
            current_higher.low > previous_higher.low
            and current_higher.close > current_higher.open
            and current_higher.low - previous_higher.low > higher_distance
        )
        higher_lower_high = (
            current_higher.high < previous_higher.high
            and current_higher.close < current_higher.open
            and previous_higher.high - current_higher.high > higher_distance
        )
        lower_low = (
            current_lower.low > previous_lower.low
            and current_lower.close > current_lower.open
            and current_lower.low - previous_lower.low > lower_distance
        )
        lower_high = (
            current_lower.high < previous_lower.high
            and current_lower.close < current_lower.open
            and previous_lower.high - current_lower.high > lower_distance
        )
        facts = {
            "higher_timeframe": higher_name,
            "lower_timeframe": lower_name,
            "higher_available_at": current_higher.available_at.isoformat(),
        }
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_ENTRY",
                side="BUY",
                active=lower_low and higher_low,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_ENTRY",
                side="SELL",
                active=lower_high and higher_lower_high,
                facts=facts,
            ),
        )


__all__ = ["HarrietHedgingEvaluator"]
