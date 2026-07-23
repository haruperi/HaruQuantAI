"""Concrete recovered Market Structure signal evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.strategy.signals._mechanics import (
    _bar_records,
    _feature_values,
    _make_signal,
    _SignalDataError,
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

_FEATURE_NAME = "zigzag_extremes"
_MIN_BARS = 2
_REQUIRED_EXTREMES = 8


@dataclass(frozen=True, slots=True)
class MarketStructureEvaluator(_SignalEvaluatorBase):
    """Preserve recovered structure breaks over supplied ZigZag evidence."""

    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate recovered bullish and bearish structure-break rules.

        Args:
            evidence: Bars and provenance-complete ZigZag feature evidence.
            indicators: Unused; ZigZag is not an official Strategy-calculated
                indicator.
            config: Validated immutable configuration.
            context: Fixed deterministic evaluation context.

        Returns:
            Bullish and bearish structure signal states.

        Raises:
            _SignalDataError: If bar or ZigZag evidence is incomplete.
        """
        logger.info("Evaluating recovered Market Structure signals")
        del indicators
        bars = _bar_records(evidence.primary_market)
        if len(bars) < _MIN_BARS:
            raise _SignalDataError("Market Structure requires two completed bars")
        values = _feature_values(evidence, _FEATURE_NAME, _REQUIRED_EXTREMES)[
            :_REQUIRED_EXTREMES
        ]
        if values[0] > values[1]:
            high0, low0, high1, low1, high2, low2, high3, low3 = values
        else:
            low0, high0, low1, high1, low2, high2, low3, high3 = values
        previous_close = bars[-2].close
        current_close = bars[-1].close
        bullish = (
            current_close > high1
            and previous_close < high1
            and high1 > high2
            and high2 < high3
            and low0 > low1
            and low1 < low2
        )
        bearish = (
            current_close < low1
            and previous_close > low1
            and low1 < low2
            and low2 > low3
            and high0 < high1
            and high1 > high2
        )
        facts = {
            "feature_ref": evidence.feature_refs[_FEATURE_NAME],
            "high0": str(high0),
            "low0": str(low0),
            "high1": str(high1),
            "low1": str(low1),
        }
        lineage = {"zigzag_ref": evidence.feature_refs[_FEATURE_NAME]}
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="BULLISH_STRUCTURE_BREAK",
                side="BUY",
                active=bullish,
                facts=facts,
                lineage=lineage,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="BEARISH_STRUCTURE_BREAK",
                side="SELL",
                active=bearish,
                facts=facts,
                lineage=lineage,
            ),
        )


__all__ = ["MarketStructureEvaluator"]
