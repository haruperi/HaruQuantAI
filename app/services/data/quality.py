"""Market data quality evaluation, anomaly detection, and repair ledger.

Feature:
    FEAT-DATA-QUALITY

Purpose:
    Provides deterministic detection of gaps, high/low inversions, price spikes,
    crossed quotes, duplicate timestamps, non-monotonic ordering, and out-of-session
    bars matching StrategyQuant X DataProblemEvaluator. Applies configurable repair
    policies and produces audit ledgers.

Invariants:
    * Quality score is normalized between 0.0 (severely corrupt) and 1.0 (flawless).
    * Detection of anomalies is deterministic and side-effect free.
    * Repair policies generate audit ledgers with counts of modifications applied.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, override

from app.contracts.data import (
    DATA_PERSISTENCE,
    DATA_QUALITY,
    DATA_SESSIONS,
    BarRecord,
    DataPersistenceService,
    QualityAnomaly,
    QualityAnomalyType,
    QualityReport,
    RepairPolicy,
    RepairResult,
    SessionDefinition,
    SessionService,
    TickRecord,
)
from app.contracts.data import (
    QualityService as IQualityService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

# Standard timeframe durations in seconds
TIMEFRAME_SECONDS: dict[str, int] = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}


def _check_bar_inversions(bar: BarRecord) -> list[QualityAnomaly]:
    """Check structural OHLC price integrity."""
    anomalies: list[QualityAnomaly] = []
    if bar.low > bar.high:
        anomalies.append(
            QualityAnomaly(
                anomaly_type=QualityAnomalyType.CROSSED_QUOTE,
                timestamp=bar.timestamp,
                description=f"Low ({bar.low}) exceeds High ({bar.high})",
                severity="error",
                observed_value=bar.low - bar.high,
            )
        )
    if bar.high < max(bar.open, bar.close):
        anomalies.append(
            QualityAnomaly(
                anomaly_type=QualityAnomalyType.HIGH_PROBLEM,
                timestamp=bar.timestamp,
                description=(
                    f"High ({bar.high}) is less than max(Open, Close) "
                    f"({max(bar.open, bar.close)})"
                ),
                severity="error",
                observed_value=bar.high,
            )
        )
    if bar.low > min(bar.open, bar.close):
        anomalies.append(
            QualityAnomaly(
                anomaly_type=QualityAnomalyType.LOW_PROBLEM,
                timestamp=bar.timestamp,
                description=(
                    f"Low ({bar.low}) is greater than min(Open, Close) "
                    f"({min(bar.open, bar.close)})"
                ),
                severity="error",
                observed_value=bar.low,
            )
        )
    return anomalies


def _check_time_sequence(
    bar: BarRecord,
    prev_bar: BarRecord,
    gap_threshold: float,
) -> QualityAnomaly | None:
    """Check monotonic order and gaps between sequential bars."""
    delta = (bar.timestamp - prev_bar.timestamp).total_seconds()
    if delta < 0:
        return QualityAnomaly(
            anomaly_type=QualityAnomalyType.NON_MONOTONIC,
            timestamp=bar.timestamp,
            description=(
                f"Non-monotonic timestamp ({bar.timestamp} < {prev_bar.timestamp})"
            ),
            severity="error",
        )
    if delta == 0:
        return QualityAnomaly(
            anomaly_type=QualityAnomalyType.DUPLICATE,
            timestamp=bar.timestamp,
            description=f"Duplicate timestamp {bar.timestamp}",
            severity="error",
        )
    if delta > gap_threshold:
        return QualityAnomaly(
            anomaly_type=QualityAnomalyType.GAP,
            timestamp=bar.timestamp,
            description=(
                f"Gap of {delta:.0f}s detected between "
                f"{prev_bar.timestamp} and {bar.timestamp}"
            ),
            severity="warning",
            observed_value=delta,
        )
    return None


def _compute_atr(bars: list[BarRecord], period: int = 14) -> float:
    """Compute Wilder's ATR over bars, with fallback to median range if fewer bars."""
    if len(bars) < period + 1:
        ranges = [max(0.0, b.high - b.low) for b in bars]
        ranges.sort()
        return ranges[len(ranges) // 2] if ranges else 0.0

    true_ranges: list[float] = []
    for i in range(1, len(bars)):
        tr = max(
            bars[i].high - bars[i].low,
            abs(bars[i].high - bars[i - 1].close),
            abs(bars[i].low - bars[i - 1].close),
        )
        true_ranges.append(tr)

    atr = sum(true_ranges[:period]) / period
    for tr in true_ranges[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


@dataclass(slots=True, frozen=True)
class QualityConfig:
    """Configuration for data quality evaluation."""

    atr_period: int = 14
    gap_tolerance_multiplier: float = 1.5


class QualityServiceImpl(IQualityService):
    """Concrete implementation of QualityService protocol."""

    def __init__(
        self,
        persistence: DataPersistenceService | None = None,
        session_service: SessionService | None = None,
        config: QualityConfig | None = None,
    ) -> None:
        """Initialize quality service.

        Args:
            persistence: Optional persistence service for saving reports.
            session_service: Optional session service for session-aware checks.
            config: Optional configuration.
        """
        self._persistence = persistence
        self._session_service = session_service
        self._config = config or QualityConfig()

    @override
    def evaluate_quality(
        self,
        bars: list[BarRecord],
        session: SessionDefinition | None = None,
        timeframe: str = "M1",
        spike_multiplier: float = 3.5,
    ) -> QualityReport:
        """Scan bars for gaps, high/low inversions, spikes, and session violations."""
        anomalies: list[QualityAnomaly] = []
        counts: dict[str, int] = {}

        if not bars:
            return QualityReport(
                report_id=f"qr_{uuid.uuid4().hex[:8]}",
                dataset_id="",
                quality_score=1.0,
                total_records=0,
                anomalies=[],
                anomaly_counts={},
                evaluated_at=datetime.now(UTC),
            )

        expected_step = TIMEFRAME_SECONDS.get(timeframe.upper(), 60)
        gap_threshold = expected_step * self._config.gap_tolerance_multiplier

        atr = _compute_atr(bars, self._config.atr_period)
        spike_cutoff = max(atr * spike_multiplier, 0.0001)

        prev_bar: BarRecord | None = None

        for bar in bars:
            # 1. Structural OHLC checks
            for anomaly in _check_bar_inversions(bar):
                anomalies.append(anomaly)
                counts[str(anomaly.anomaly_type)] = (
                    counts.get(str(anomaly.anomaly_type), 0) + 1
                )

            # 2. Spike check
            bar_range = bar.high - bar.low
            if atr > 0 and bar_range > spike_cutoff:
                spike_anom = QualityAnomaly(
                    anomaly_type=QualityAnomalyType.SPIKE,
                    timestamp=bar.timestamp,
                    description=(
                        f"Range ({bar_range:.5f}) exceeds spike threshold "
                        f"({spike_cutoff:.5f})"
                    ),
                    severity="warning",
                    observed_value=bar_range,
                    expected_range=(0.0, spike_cutoff),
                )
                anomalies.append(spike_anom)
                counts[str(QualityAnomalyType.SPIKE)] = (
                    counts.get(str(QualityAnomalyType.SPIKE), 0) + 1
                )

            # 3. Time sequencing & gaps
            if prev_bar is not None:
                seq_anom = _check_time_sequence(bar, prev_bar, gap_threshold)
                if seq_anom is not None:
                    anomalies.append(seq_anom)
                    counts[str(seq_anom.anomaly_type)] = (
                        counts.get(str(seq_anom.anomaly_type), 0) + 1
                    )

            # 4. Out-of-session checks
            if (
                session is not None
                and self._session_service is not None
                and not self._session_service.is_in_session(bar.timestamp, session)
            ):
                out_anom = QualityAnomaly(
                    anomaly_type=QualityAnomalyType.OUT_OF_SESSION,
                    timestamp=bar.timestamp,
                    description=(
                        f"Bar at {bar.timestamp} outside session {session.name}"
                    ),
                    severity="warning",
                )
                anomalies.append(out_anom)
                counts[str(QualityAnomalyType.OUT_OF_SESSION)] = (
                    counts.get(str(QualityAnomalyType.OUT_OF_SESSION), 0) + 1
                )

            prev_bar = bar

        total = len(bars)
        penalty = len(anomalies) / max(total, 1)
        quality_score = max(0.0, min(1.0, 1.0 - penalty))

        return QualityReport(
            report_id=f"qr_{uuid.uuid4().hex[:8]}",
            dataset_id="",
            quality_score=round(quality_score, 4),
            total_records=total,
            anomalies=anomalies,
            anomaly_counts=counts,
            evaluated_at=datetime.now(UTC),
        )

    @override
    def evaluate_tick_quality(self, ticks: list[TickRecord]) -> QualityReport:
        """Scan ticks for crossed quotes, duplicate sequences, and timing errors."""
        anomalies: list[QualityAnomaly] = []
        counts: dict[str, int] = {}
        if not ticks:
            return QualityReport(
                report_id=f"qr_{uuid.uuid4().hex[:8]}",
                dataset_id="",
                quality_score=1.0,
                total_records=0,
                anomalies=[],
                anomaly_counts={},
                evaluated_at=datetime.now(UTC),
            )

        seen_sequences: set[tuple[datetime, int]] = set()
        prev_tick: TickRecord | None = None

        for t in ticks:
            # 1. Crossed quote
            if t.bid > t.ask:
                anom = QualityAnomaly(
                    anomaly_type=QualityAnomalyType.CROSSED_QUOTE,
                    timestamp=t.timestamp,
                    description=f"Crossed quote: Bid ({t.bid:.5f}) > Ask ({t.ask:.5f})",
                    severity="error",
                    observed_value=t.bid - t.ask,
                )
                anomalies.append(anom)
                counts[str(QualityAnomalyType.CROSSED_QUOTE)] = (
                    counts.get(str(QualityAnomalyType.CROSSED_QUOTE), 0) + 1
                )

            # 2. Duplicate timestamp + sequence
            seq_key = (t.timestamp, t.sequence)
            if seq_key in seen_sequences:
                anom = QualityAnomaly(
                    anomaly_type=QualityAnomalyType.DUPLICATE,
                    timestamp=t.timestamp,
                    description=f"Duplicate tick timestamp and sequence {seq_key}",
                    severity="error",
                )
                anomalies.append(anom)
                counts[str(QualityAnomalyType.DUPLICATE)] = (
                    counts.get(str(QualityAnomalyType.DUPLICATE), 0) + 1
                )
            else:
                seen_sequences.add(seq_key)

            # 3. Non-monotonic timing
            if prev_tick is not None and t.timestamp < prev_tick.timestamp:
                anom = QualityAnomaly(
                    anomaly_type=QualityAnomalyType.NON_MONOTONIC,
                    timestamp=t.timestamp,
                    description=(
                        f"Non-monotonic tick timing "
                        f"({t.timestamp} < {prev_tick.timestamp})"
                    ),
                    severity="error",
                )
                anomalies.append(anom)
                counts[str(QualityAnomalyType.NON_MONOTONIC)] = (
                    counts.get(str(QualityAnomalyType.NON_MONOTONIC), 0) + 1
                )

            prev_tick = t

        error_count = sum(
            c
            for k, c in counts.items()
            if k in {"CROSSED_QUOTE", "DUPLICATE", "NON_MONOTONIC"}
        )
        score = max(0.0, 1.0 - (error_count / max(1, len(ticks))))
        return QualityReport(
            report_id=f"qr_{uuid.uuid4().hex[:8]}",
            dataset_id="",
            quality_score=round(score, 4),
            total_records=len(ticks),
            anomalies=anomalies,
            anomaly_counts=counts,
            evaluated_at=datetime.now(UTC),
        )

    @override
    def repair_data(
        self, bars: list[BarRecord], policy: RepairPolicy
    ) -> tuple[list[BarRecord], RepairResult]:
        """Apply deterministic repair policy to defective bars and record audit."""
        repairs: list[str] = []
        repaired: list[BarRecord] = []
        seen_timestamps: set[datetime] = set()
        modifications = 0

        # Compute spike cutoff if clamping enabled
        atr = (
            _compute_atr(bars, self._config.atr_period) if policy.clamp_spikes else 0.0
        )
        spike_cutoff = max(atr * 3.5, 0.0001)

        prev_bar: BarRecord | None = None
        for bar in bars:
            # 1. Deduplicate timestamps
            if bar.timestamp in seen_timestamps:
                modifications += 1
                repairs.append(f"Dropped duplicate timestamp at {bar.timestamp}")
                continue
            seen_timestamps.add(bar.timestamp)

            # 2. Small gap interpolation
            if policy.fill_small_gaps and prev_bar is not None:
                step_s = (bar.timestamp - prev_bar.timestamp).total_seconds()
                unit_step = 60.0
                gap_bars = round(step_s / unit_step) - 1
                if 1 <= gap_bars <= policy.max_fill_gap_bars:
                    for i in range(1, gap_bars + 1):
                        alpha = i / (gap_bars + 1)
                        diff = bar.open - prev_bar.close
                        interp_price = prev_bar.close + alpha * diff
                        interp_dt = prev_bar.timestamp + timedelta(
                            seconds=i * unit_step
                        )
                        interp_bar = BarRecord(
                            timestamp=interp_dt,
                            open=interp_price,
                            high=interp_price,
                            low=interp_price,
                            close=interp_price,
                            volume=0.0,
                            source=bar.source,
                        )
                        repaired.append(interp_bar)
                        modifications += 1
                        repairs.append(f"Interpolated gap bar at {interp_dt}")

            target_bar = bar
            # 3. Structural OHLC validation
            if not bar.is_valid_ohlc():
                if policy.drop_invalid_ohlc:
                    modifications += 1
                    repairs.append(
                        f"Dropped invalid OHLC bar at {bar.timestamp} "
                        f"(O={bar.open}, H={bar.high}, L={bar.low}, C={bar.close})"
                    )
                    continue
                # If not dropping, clamp high/low
                repaired_high = max(bar.open, bar.close, bar.high)
                repaired_low = min(bar.open, bar.close, bar.low)
                modifications += 1
                repairs.append(f"Clamped OHLC bounds at {bar.timestamp}")
                target_bar = BarRecord(
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=repaired_high,
                    low=repaired_low,
                    close=bar.close,
                    volume=bar.volume,
                    source=bar.source,
                    anomaly_flags=bar.anomaly_flags,
                )

            # 4. Spike clamping
            if policy.clamp_spikes and atr > 0:
                bar_range = target_bar.high - target_bar.low
                if bar_range > spike_cutoff:
                    mid = (target_bar.open + target_bar.close) / 2.0
                    half_cutoff = spike_cutoff / 2.0
                    new_high = max(target_bar.open, target_bar.close, mid + half_cutoff)
                    new_low = min(target_bar.open, target_bar.close, mid - half_cutoff)
                    modifications += 1
                    repairs.append(
                        f"Clamped price spike at {target_bar.timestamp} "
                        f"(range {bar_range:.5f} -> {new_high - new_low:.5f})"
                    )
                    target_bar = BarRecord(
                        timestamp=target_bar.timestamp,
                        open=target_bar.open,
                        high=new_high,
                        low=new_low,
                        close=target_bar.close,
                        volume=target_bar.volume,
                        source=target_bar.source,
                        anomaly_flags=target_bar.anomaly_flags,
                    )

            repaired.append(target_bar)
            prev_bar = target_bar

        audit = RepairResult(
            original_count=len(bars),
            repaired_count=len(repaired),
            modifications_count=modifications,
            repairs_applied=tuple(repairs),
        )
        return repaired, audit


SPEC: FeatureSpec = FeatureSpec(
    name="data.quality",
    provides=frozenset({DATA_QUALITY}),
    requires=frozenset({DATA_PERSISTENCE}),
    optional=frozenset({DATA_SESSIONS}),
    description="Data quality evaluation, anomaly detection, and repair ledger.",
)


class QualityFeature:
    """Wire quality feature into kernel composition lifecycle."""

    def __init__(self, config: QualityConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional quality configuration.
        """
        self._config = config or QualityConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve dependencies and provide quality service.

        Args:
            context: Lifecycle feature context.
        """
        persistence = context.require(DATA_PERSISTENCE)
        session_svc = context.optional(DATA_SESSIONS)
        service = QualityServiceImpl(
            persistence=persistence,
            session_service=session_svc,
            config=self._config,
        )
        context.provide(DATA_QUALITY, service)
        logger.info("data_quality_feature_started")


def feature() -> QualityFeature:
    """Return an unmounted QualityFeature instance.

    Returns:
        New QualityFeature instance.
    """
    return QualityFeature()


__all__ = [
    "SPEC",
    "TIMEFRAME_SECONDS",
    "QualityConfig",
    "QualityFeature",
    "QualityServiceImpl",
    "feature",
]
