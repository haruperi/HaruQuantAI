"""Causal bounded-window Naive MA Trend signal evaluator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from typing import TYPE_CHECKING, Any, Protocol

from app.services.strategy.contracts.responses import guard_strategy_boundary
from app.services.strategy.signals._mechanics import (
    _bar_records,
    _integer_parameter,
    _make_signal,
    _SignalConfigError,
    _SignalDataError,
    _SignalEvaluatorBase,
)
from app.utils import get_logger

if TYPE_CHECKING:
    from app.services.strategy.contracts import (
        StrategyExecutionContext,
        StrategySignal,
        StrategySignalEvidence,
        ValidatedStrategyConfig,
    )

logger = get_logger(__name__)

_MIN_PERIOD = 2


class _BarIdentitySource(Protocol):
    """Structural fields consumed from one Data-owned bar record."""

    timestamp: datetime
    available_at: datetime
    close: Decimal


@dataclass(frozen=True, slots=True)
class NaiveMATrendIncrementalEvaluator(_SignalEvaluatorBase):
    """Evaluate the registered MA rules from one causal bounded bar window."""

    _previous_window: tuple[tuple[datetime, datetime, Decimal], ...] | None = field(
        default=None, init=False, repr=False
    )
    _ema_values: dict[int, tuple[Decimal, Decimal]] = field(
        default_factory=dict, init=False, repr=False
    )

    @staticmethod
    def _identity(record: _BarIdentitySource) -> tuple[datetime, datetime, Decimal]:
        """Return immutable evidence identity for one canonical bar.

        Args:
            record: Data-owned OHLCV record.

        Returns:
            Timestamp, availability, and close identity.
        """
        return (record.timestamp, record.available_at, record.close)

    def _validate_progression(self, records: tuple[_BarIdentitySource, ...]) -> None:
        """Require strict order and one-bar causal progression.

        Args:
            records: Current bounded point-in-time market window.

        Raises:
            _SignalDataError: If ordering, uniqueness, or progression differs.
        """
        identities = tuple(self._identity(record) for record in records)
        timestamps = tuple(identity[0] for identity in identities)
        if any(left >= right for left, right in pairwise(timestamps)):
            raise _SignalDataError("naive trend bars must be strictly ordered")
        if self._previous_window is not None:
            overlap = min(len(self._previous_window) - 1, len(identities) - 1)
            if overlap > 0 and self._previous_window[-overlap:] != identities[:overlap]:
                raise _SignalDataError("naive trend bar progression changed")
        object.__setattr__(self, "_previous_window", identities)

    def _ema_pair(
        self, values: tuple[Decimal, ...], period: int, *, new_count: int
    ) -> tuple[Decimal, Decimal]:
        """Return previous/current EMA values with an SMA seed.

        Args:
            values: Ordered close values visible at the decision instant.
            period: Exact configured moving-average period.
            new_count: Number of newly appended records.

        Returns:
            Previous and current causal EMA values.
        """
        alpha = Decimal(2) / Decimal(period + 1)
        cached = self._ema_values.get(period)
        if cached is None:
            current = sum(values[:period], Decimal(0)) / Decimal(period)
            previous = current
            for value in values[period:]:
                previous, current = current, value * alpha + current * (1 - alpha)
        else:
            previous, current = cached
            for value in values[-new_count:]:
                previous, current = current, value * alpha + current * (1 - alpha)
        self._ema_values[period] = (previous, current)
        return previous, current

    def _evaluate_rules(
        self,
        records: tuple[_BarIdentitySource, ...],
        config: ValidatedStrategyConfig,
    ) -> tuple[dict[str, str], bool, bool, bool, bool]:
        """Evaluate EMA crossover rules from validated causal records.

        Args:
            records: Strictly progressing point-in-time bar window.
            config: Canonically validated strategy configuration.

        Returns:
            Signal facts plus upward/downward crossover states.

        Raises:
            _SignalConfigError: If a configured period is invalid.
            _SignalDataError: If evidence is incomplete or changed.
        """
        fast = _integer_parameter(config, "fast_ma_period")
        slow = _integer_parameter(config, "slow_ma_period")
        trend = _integer_parameter(config, "filter_ma_period")
        if min(fast, slow, trend) < _MIN_PERIOD:
            raise _SignalConfigError("moving-average periods must be at least two")
        required = max(fast + 1, slow + 1, trend)
        if len(records) < required:
            raise _SignalDataError("naive trend window is incomplete")
        previous_window = self._previous_window
        self._validate_progression(records)
        new_count = len(records) if previous_window is None else 1
        closes = tuple(record.close for record in records)
        fast_previous, fast_now = self._ema_pair(closes, fast, new_count=new_count)
        slow_previous, slow_now = self._ema_pair(closes, slow, new_count=new_count)
        _, trend_now = self._ema_pair(closes, trend, new_count=new_count)
        up_cross = fast_now > slow_now and fast_previous <= slow_previous
        down_cross = fast_now < slow_now and fast_previous >= slow_previous
        return (
            {
                "fast_ma": str(fast_now),
                "slow_ma": str(slow_now),
                "trend_ma": str(trend_now),
            },
            up_cross and slow_now > trend_now,
            down_cross and slow_now < trend_now,
            down_cross,
            up_cross,
        )

    def _evaluate_compact(
        self,
        records: tuple[_BarIdentitySource, ...],
        config: ValidatedStrategyConfig,
    ) -> frozenset[str]:
        """Return active names after one-time canonical strategy binding.

        Args:
            records: Exact causal bar window.
            config: Canonically validated immutable configuration.

        Returns:
            Active action names for the trusted Simulation runtime.
        """
        _, long_entry, short_entry, long_exit, short_exit = self._evaluate_rules(
            records, config
        )
        active: set[str] = set()
        if long_entry:
            active.add("LONG_ENTRY")
        if short_entry:
            active.add("SHORT_ENTRY")
        if long_exit:
            active.add("LONG_EXIT")
        if short_exit:
            active.add("SHORT_EXIT")
        return frozenset(active)

    @guard_strategy_boundary
    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[Any, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Evaluate the unchanged crossover and trend-filter rules.

        Args:
            evidence: Exact point-in-time market evidence.
            indicators: Must be empty; averages are derived causally from bars.
            config: Validated immutable strategy configuration.
            context: Current deterministic decision context.

        Returns:
            Long/short entry and exit signals in canonical order.

        Raises:
            _SignalConfigError: If periods or supplied indicators are invalid.
            _SignalDataError: If bounded market evidence is incomplete or changed.
        """
        if indicators:
            raise _SignalConfigError("incremental naive trend accepts no indicators")
        records = tuple(_bar_records(evidence.primary_market))
        facts, long_entry, short_entry, long_exit, short_exit = self._evaluate_rules(
            records, config
        )
        return (
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_ENTRY",
                side="BUY",
                active=long_entry,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_ENTRY",
                side="SELL",
                active=short_entry,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="LONG_EXIT",
                side="SELL",
                active=long_exit,
                facts=facts,
            ),
            _make_signal(
                self,
                evidence,
                config,
                context,
                signal_name="SHORT_EXIT",
                side="BUY",
                active=short_exit,
                facts=facts,
            ),
        )


__all__: tuple[str, ...] = ()
