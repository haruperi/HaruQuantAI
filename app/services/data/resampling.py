"""Deterministic session-aware bar aggregation, 4-price ticks, and timezone cloning.

Feature:
    FEAT-DATA-RESAMPLING

Purpose:
    Provides session-aware bar aggregation from base bars or raw ticks into higher
    timeframes, 4-price bar ticks (Open -> Low/High -> High/Low -> Close), and
    timezone transformation matching StrategyQuant X CloneToTimezoneJob and
    aggregation pipelines.

Invariants:
    * Resampling preserves strict OHLC invariants: High >= max(Open, Close) and
      Low <= min(Open, Close).
    * Total volume is strictly conserved across aggregation boundaries.
    * 4-price tick simulation is deterministic based on bar direction
      (bullish vs bearish).
    * Bucket boundaries align to session open time when session is provided.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, override
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.contracts.data import (
    DATA_RESAMPLING,
    DATA_SESSIONS,
    BarRecord,
    ResamplingError,
    SessionDefinition,
    SessionService,
    TickRecord,
    TimezoneError,
)
from app.contracts.data import (
    ResamplingService as IResamplingService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

TIMEFRAME_SECONDS: dict[str, int] = {
    "M1": 60,
    "M2": 120,
    "M3": 180,
    "M5": 300,
    "M10": 600,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H2": 7200,
    "H4": 14400,
    "H8": 28800,
    "D1": 86400,
    "W1": 604800,
}


def _parse_timeframe_seconds(tf: str) -> int:
    """Parse timeframe string (e.g. M1, M5, H1, D1) into total seconds."""
    clean = tf.strip().upper()
    if clean in TIMEFRAME_SECONDS:
        return TIMEFRAME_SECONDS[clean]
    if clean.startswith("M") and clean[1:].isdigit():
        return int(clean[1:]) * 60
    if clean.startswith("H") and clean[1:].isdigit():
        return int(clean[1:]) * 3600
    if clean.startswith("D") and clean[1:].isdigit():
        return int(clean[1:]) * 86400
    if clean.startswith("S") and clean[1:].isdigit():
        return int(clean[1:])
    msg = f"Unsupported or invalid timeframe: {tf}"
    raise ResamplingError(msg)


def _get_bucket_key(
    dt: datetime,
    interval_s: int,
    session_offset_s: int = 0,
) -> datetime:
    """Calculate the bucket start timestamp aligned to interval and session offset."""
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    total_s = int((dt - epoch).total_seconds())
    adjusted = total_s - session_offset_s
    bucket_adjusted = (adjusted // interval_s) * interval_s
    bucket_s = bucket_adjusted + session_offset_s
    return epoch + timedelta(seconds=bucket_s)


@dataclass(slots=True, frozen=True)
class ResamplingConfig:
    """Configuration for resampling service."""

    default_spread: float = 0.0001


class ResamplingServiceImpl(IResamplingService):
    """Concrete implementation of ResamplingService protocol."""

    def __init__(
        self,
        session_service: SessionService | None = None,
        config: ResamplingConfig | None = None,
    ) -> None:
        """Initialize resampling service.

        Args:
            session_service: Optional session service for timezone conversions.
            config: Optional configuration.
        """
        self._session_service = session_service
        self._config = config or ResamplingConfig()

    @override
    def resample_bars(
        self,
        bars: list[BarRecord],
        target_timeframe: str,
        session: SessionDefinition | None = None,
    ) -> list[BarRecord]:
        """Resample base bars into higher timeframe bars with session alignment."""
        if not bars:
            return []

        interval_s = _parse_timeframe_seconds(target_timeframe)
        session_offset = 0
        if session and session.windows:
            open_parts = session.windows[0].open_time.split(":")
            session_offset = int(open_parts[0]) * 3600 + int(open_parts[1]) * 60

        buckets: dict[datetime, list[BarRecord]] = defaultdict(list)
        for bar in sorted(bars, key=lambda b: b.timestamp):
            b_key = _get_bucket_key(bar.timestamp, interval_s, session_offset)
            buckets[b_key].append(bar)

        resampled: list[BarRecord] = []
        for b_time in sorted(buckets.keys()):
            group = buckets[b_time]
            resampled.append(
                BarRecord(
                    timestamp=b_time,
                    open=group[0].open,
                    high=max(b.high for b in group),
                    low=min(b.low for b in group),
                    close=group[-1].close,
                    volume=sum(b.volume for b in group),
                    source=f"resampled:{target_timeframe}",
                )
            )

        return resampled

    @override
    def resample_ticks_to_bars(
        self,
        ticks: list[TickRecord],
        target_timeframe: str,
        session: SessionDefinition | None = None,
    ) -> list[BarRecord]:
        """Aggregate raw ticks into time bars."""
        if not ticks:
            return []

        interval_s = _parse_timeframe_seconds(target_timeframe)
        session_offset = 0
        if session and session.windows:
            open_parts = session.windows[0].open_time.split(":")
            session_offset = int(open_parts[0]) * 3600 + int(open_parts[1]) * 60

        buckets: dict[datetime, list[TickRecord]] = defaultdict(list)
        for tick in sorted(ticks, key=lambda t: (t.timestamp, t.sequence)):
            b_key = _get_bucket_key(tick.timestamp, interval_s, session_offset)
            buckets[b_key].append(tick)

        bars: list[BarRecord] = []
        for b_time in sorted(buckets.keys()):
            group = buckets[b_time]
            bids = [t.bid for t in group]
            vol = sum(t.bid_volume + t.ask_volume for t in group)
            bars.append(
                BarRecord(
                    timestamp=b_time,
                    open=bids[0],
                    high=max(bids),
                    low=min(bids),
                    close=bids[-1],
                    volume=vol,
                    source=f"ticks_to_bars:{target_timeframe}",
                )
            )

        return bars

    @override
    def generate_4price_ticks(self, bar: BarRecord) -> list[TickRecord]:
        """Generate 4-price intrabar ticks (Open -> Low/High -> High/Low -> Close)."""
        spread = self._config.default_spread
        vol_quarter = round(bar.volume / 4.0, 2)
        ts = bar.timestamp

        # Standard 1-minute delta assumed for intrabar spacing if unspecified
        step_ms = 15000  # 15 seconds

        is_bullish = bar.close >= bar.open
        if is_bullish:
            # Bullish path: Open -> Low -> High -> Close
            path = [bar.open, bar.low, bar.high, bar.close]
        else:
            # Bearish path: Open -> High -> Low -> Close
            path = [bar.open, bar.high, bar.low, bar.close]

        ticks: list[TickRecord] = []
        for seq, price in enumerate(path):
            tick_time = ts + timedelta(milliseconds=seq * step_ms)
            ticks.append(
                TickRecord(
                    timestamp=tick_time,
                    bid=price,
                    ask=price + spread,
                    sequence=seq,
                    bid_volume=vol_quarter,
                    ask_volume=vol_quarter,
                )
            )

        return ticks

    @override
    def clone_to_timezone(
        self,
        bars: list[BarRecord],
        target_timezone: str,
        session: SessionDefinition | None = None,
    ) -> list[BarRecord]:
        """Project bar series into target timezone and re-align session boundaries."""
        try:
            target_tz = ZoneInfo(target_timezone)
        except ZoneInfoNotFoundError as exc:
            msg = f"Unknown target timezone: {target_timezone}"
            raise TimezoneError(msg) from exc

        cloned: list[BarRecord] = []
        for bar in bars:
            local_dt = (
                bar.timestamp.astimezone(target_tz)
                if bar.timestamp.tzinfo
                else bar.timestamp.replace(tzinfo=target_tz)
            )
            cloned.append(
                BarRecord(
                    timestamp=local_dt,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    source=f"cloned:{target_timezone}",
                    anomaly_flags=bar.anomaly_flags,
                )
            )

        return cloned


SPEC: FeatureSpec = FeatureSpec(
    name="data.resampling",
    provides=frozenset({DATA_RESAMPLING}),
    requires=frozenset(),
    optional=frozenset({DATA_SESSIONS}),
    description="Session-aware bar resampling, 4-price ticks, and timezone cloning.",
)


class ResamplingFeature:
    """Wire resampling feature into kernel composition lifecycle."""

    def __init__(self, config: ResamplingConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional resampling configuration.
        """
        self._config = config or ResamplingConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve dependencies and provide resampling service.

        Args:
            context: Lifecycle feature context.
        """
        session_svc = context.optional(DATA_SESSIONS)
        service = ResamplingServiceImpl(
            session_service=session_svc,
            config=self._config,
        )
        context.provide(DATA_RESAMPLING, service)
        logger.info("data_resampling_feature_started")


def feature() -> ResamplingFeature:
    """Return an unmounted ResamplingFeature instance.

    Returns:
        New ResamplingFeature instance.
    """
    return ResamplingFeature()


__all__ = [
    "SPEC",
    "TIMEFRAME_SECONDS",
    "ResamplingConfig",
    "ResamplingFeature",
    "ResamplingServiceImpl",
    "feature",
]
