"""Concrete recovered Naive MA Trend signal evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.strategy.evaluators._shared import (
    _current_previous,
    _current_value,
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
class NaiveMATrendEvaluator(_SignalEvaluatorBase):
    """Preserve recovered MA crossover, trend-filter, and exit signals."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered Naive MA Trend signal rules.

        Args:
            evidence: Point-in-time market evidence.
            indicators: Official SMA results for all configured periods.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            Long/short entry and exit signal states in stable order.

        Raises:
            _SignalConfigError: If a moving-average period is invalid.
        """
        logger.info("Evaluating recovered Naive MA Trend signals")
        fast = _integer_parameter(config, "fast_ma_period")
        slow = _integer_parameter(config, "slow_ma_period")
        trend = _integer_parameter(config, "filter_ma_period")
        if min(fast, slow, trend) < _MIN_PERIOD:
            raise _SignalConfigError("moving-average periods must be at least two")
        fast_now, fast_previous = _current_previous(
            _indicator_values(
                indicators, indicator_id="sma", output_column=f"sma_{fast}"
            ),
            f"sma_{fast}",
        )
        slow_values = _indicator_values(
            indicators, indicator_id="sma", output_column=f"sma_{slow}"
        )
        slow_now, slow_previous = _current_previous(slow_values, f"sma_{slow}")
        trend_now = _current_value(
            _indicator_values(
                indicators, indicator_id="sma", output_column=f"sma_{trend}"
            ),
            f"sma_{trend}",
        )
        up_cross = fast_now > slow_now and fast_previous <= slow_previous
        down_cross = fast_now < slow_now and fast_previous >= slow_previous
        facts = {
            "fast_ma": str(fast_now),
            "slow_ma": str(slow_now),
            "trend_ma": str(trend_now),
        }
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_ENTRY",
                side="BUY",
                active=up_cross and slow_now > trend_now,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_ENTRY",
                side="SELL",
                active=down_cross and slow_now < trend_now,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_EXIT",
                side="SELL",
                active=down_cross,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_EXIT",
                side="BUY",
                active=up_cross,
                facts=facts,
            ),
        )


__all__ = ["NaiveMATrendEvaluator"]
