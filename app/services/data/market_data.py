"""Governed request-driven market data retrieval, transparent caching, and sync.

Feature:
    FEAT-DATA-MARKET_DATA

Purpose:
    Provides unified, governed access to market data retrieval, normalization,
    quality verification, in-memory caching, and connector synchronization across
    data providers matching StrategyQuant X DataManager / MarketData architecture.

Invariants:
    * Stream deduplication and timestamp monotonic sorting are applied automatically.
    * Transparent caching avoids redundant connector network calls.
    * Persists Parquet datasets whenever store_data=True in MarketDataRequest.
    * Zero plaintext credentials handled in retrieval layers.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, override

from app.contracts.brokers import (
    BROKER_CRYPTO,
    BROKER_DARWINEX,
    BROKER_DUKASCOPY,
    BROKER_EQUITY,
    BROKER_FUTURES,
    BROKER_YAHOO,
    BrokerFeedConnector,
)
from app.contracts.data import (
    DATA_DATASETS,
    DATA_MARKET_DATA,
    DATA_PERSISTENCE,
    DATA_QUALITY,
    DATA_SYNC,
    BarRecord,
    DataPersistenceService,
    DatasetService,
    MarketDataRequest,
    QualityAnomaly,
    QualityAnomalyType,
    QualityReport,
    QualityService,
    SyncInterval,
    SyncReport,
    TickRecord,
    build_market_data_request,
)
from app.contracts.data import (
    MarketDataClient as IMarketDataClient,
)
from app.contracts.data import (
    SyncConnectorsCapability as ISyncConnectorsCapability,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True, frozen=True)
class MarketDataConfig:
    """Configuration for market data retrieval client."""

    enable_caching: bool = True
    max_cache_items: int = 1000


async def _stream_bars_from_connector(
    connector: Any,
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
) -> list[BarRecord]:
    """Stream raw bars from connector supporting either stream method."""
    raw_bars: list[BarRecord] = []
    if hasattr(connector, "stream_historical_bars"):
        raw_bars.extend(
            [
                bar
                async for bar in connector.stream_historical_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time,
                    end_time=end_time,
                )
            ]
        )
    elif hasattr(connector, "stream_raw_data"):
        async for chunk in connector.stream_raw_data(symbol, start_time, end_time):
            if "bars" in chunk.metadata:
                raw_bars.extend(chunk.metadata["bars"])
    return raw_bars


def _apply_bar_anomalies(
    bars: list[BarRecord], anomalies: list[QualityAnomaly]
) -> list[BarRecord]:
    """Apply anomaly bitmask flags to corresponding bars."""
    if not anomalies:
        return bars
    anomaly_map: dict[datetime, int] = {}
    for anom in anomalies:
        mask = 1 if anom.anomaly_type == QualityAnomalyType.GAP else 2
        anomaly_map[anom.timestamp] = anomaly_map.get(anom.timestamp, 0) | mask
    return [
        BarRecord(
            timestamp=b.timestamp,
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=b.volume,
            source=b.source,
            anomaly_flags=anomaly_map.get(b.timestamp, b.anomaly_flags),
        )
        for b in bars
    ]


class MarketDataServiceImpl(IMarketDataClient, ISyncConnectorsCapability):
    """Concrete implementation of MarketDataClient and SyncConnectorsCapability."""

    def __init__(
        self,
        dataset_service: DatasetService,
        persistence: DataPersistenceService | None = None,
        quality_service: QualityService | None = None,
        connectors: dict[str, Any] | None = None,
        config: MarketDataConfig | None = None,
    ) -> None:
        """Initialize market data service.

        Args:
            dataset_service: Parquet dataset storage service.
            persistence: Optional persistence service for cache tracking.
            quality_service: Optional quality validation service.
            connectors: Optional dictionary of feed connectors keyed by provider.
            config: Optional configuration.
        """
        self._dataset_service = dataset_service
        self._persistence = persistence
        self._quality_service = quality_service
        self._connectors = connectors or {}
        self._config = config or MarketDataConfig()
        self._cache: OrderedDict[str, list[BarRecord] | list[TickRecord]] = (
            OrderedDict()
        )

    def _make_cache_key(self, request: MarketDataRequest) -> str:
        """Build deterministic cache key from request properties."""
        start_str = request.start.isoformat() if request.start else "MIN"
        end_str = request.end.isoformat() if request.end else "MAX"
        return (
            f"{request.source_id.lower()}:{request.symbol.upper()}:"
            f"{request.data_kind}:{request.timeframe}:{start_str}:{end_str}"
        )

    @override
    def clear_cache(self) -> None:
        """Clear the in-memory request cache."""
        self._cache.clear()
        logger.info("market_data_cache_cleared")

    async def _fetch_from_dataset(
        self, request: MarketDataRequest, is_tick: bool
    ) -> list[BarRecord] | list[TickRecord]:
        """Load records directly from a known dataset version."""
        if is_tick:
            return await self._dataset_service.load_ticks(
                request.source_id, start=request.start, end=request.end
            )
        return await self._dataset_service.load_bars(
            request.source_id, start=request.start, end=request.end
        )

    async def _fetch_ticks_from_connector(
        self, request: MarketDataRequest, connector: Any
    ) -> tuple[list[TickRecord], int]:
        """Stream, deduplicate, and optionally persist ticks from feed connector."""
        start_time = request.start or datetime(1970, 1, 1, tzinfo=UTC)
        end_time = request.end or datetime.now(UTC)

        raw_ticks: list[TickRecord] = []
        if hasattr(connector, "stream_historical_ticks"):
            raw_ticks.extend(
                [
                    tick
                    async for tick in connector.stream_historical_ticks(
                        symbol=request.symbol,
                        start_time=start_time,
                        end_time=end_time,
                    )
                ]
            )
        elif hasattr(connector, "stream_raw_data"):
            async for chunk in connector.stream_raw_data(
                request.symbol, start_time, end_time
            ):
                if "ticks" in chunk.metadata:
                    raw_ticks.extend(chunk.metadata["ticks"])

        seen_keys: set[tuple[datetime, int]] = set()
        deduped: list[TickRecord] = []
        for t in sorted(raw_ticks, key=lambda x: (x.timestamp, x.sequence)):
            k = (t.timestamp, t.sequence)
            if k not in seen_keys:
                seen_keys.add(k)
                deduped.append(t)

        quality_score = 1.0
        lineage: dict[str, Any] = {"source": request.source_id}
        report: QualityReport | None = None
        if self._quality_service is not None and deduped:
            report = self._quality_service.evaluate_tick_quality(deduped)
            quality_score = report.quality_score
            lineage["quality_score"] = quality_score
            lineage["anomalies_count"] = len(report.anomalies)

        if request.store_data and deduped:
            manifest = await self._dataset_service.persist_ticks(
                symbol=request.symbol,
                source_id=request.source_id,
                ticks=deduped,
                lineage=lineage,
                quality_score=quality_score,
            )
            if report is not None and self._persistence is not None:
                bound_report = QualityReport(
                    report_id=f"qr_{manifest.dataset_id}",
                    dataset_id=manifest.dataset_id,
                    quality_score=quality_score,
                    total_records=len(deduped),
                    anomalies=report.anomalies,
                    anomaly_counts=report.anomaly_counts,
                )
                await self._persistence.save_quality_report(bound_report)
        dedup_count = len(raw_ticks) - len(deduped)
        return deduped, dedup_count

    async def _fetch_bars_from_connector(
        self, request: MarketDataRequest, connector: Any
    ) -> tuple[list[BarRecord], int]:
        """Stream, deduplicate, and optionally persist bars from feed connector."""
        start_time = request.start or datetime(1970, 1, 1, tzinfo=UTC)
        end_time = request.end or datetime.now(UTC)

        raw_bars = await _stream_bars_from_connector(
            connector, request.symbol, request.timeframe, start_time, end_time
        )

        seen_ts: set[datetime] = set()
        deduped: list[BarRecord] = []
        for b in sorted(raw_bars, key=lambda x: x.timestamp):
            if b.timestamp not in seen_ts:
                seen_ts.add(b.timestamp)
                deduped.append(b)

        quality_score = 1.0
        lineage: dict[str, Any] = {"source": request.source_id}
        bars_report: QualityReport | None = None
        if self._quality_service is not None and deduped:
            bars_report = self._quality_service.evaluate_quality(
                deduped, timeframe=request.timeframe
            )
            quality_score = bars_report.quality_score
            lineage["quality_score"] = quality_score
            lineage["anomalies_count"] = len(bars_report.anomalies)
            deduped = _apply_bar_anomalies(deduped, bars_report.anomalies)

        if request.store_data and deduped:
            manifest = await self._dataset_service.persist_bars(
                symbol=request.symbol,
                timeframe=request.timeframe,
                source_id=request.source_id,
                bars=deduped,
                lineage=lineage,
                quality_score=quality_score,
            )
            if bars_report is not None and self._persistence is not None:
                bound_report = QualityReport(
                    report_id=f"qr_{manifest.dataset_id}",
                    dataset_id=manifest.dataset_id,
                    quality_score=quality_score,
                    total_records=len(deduped),
                    anomalies=bars_report.anomalies,
                    anomaly_counts=bars_report.anomaly_counts,
                )
                await self._persistence.save_quality_report(bound_report)
        dedup_count = len(raw_bars) - len(deduped)
        return deduped, dedup_count

    async def _search_manifests(
        self, request: MarketDataRequest, is_tick: bool
    ) -> list[BarRecord] | list[TickRecord]:
        """Search published dataset manifests for matching symbol and timeframe."""
        manifests = await self._dataset_service.list_manifests(
            symbol=request.symbol, timeframe=request.timeframe
        )
        for m in manifests:
            matches_start = request.start is None or m.start_time <= request.start
            matches_end = request.end is None or m.end_time >= request.end
            if matches_start and matches_end:
                if is_tick and m.data_kind == "ticks":
                    return await self._dataset_service.load_ticks(
                        m.dataset_id, start=request.start, end=request.end
                    )
                if not is_tick and m.data_kind == "bars":
                    return await self._dataset_service.load_bars(
                        m.dataset_id, start=request.start, end=request.end
                    )
        return []

    @override
    async def fetch_market_data(
        self, request: MarketDataRequest
    ) -> list[BarRecord] | list[TickRecord]:
        """Fetch market data per request specification with transparent caching."""
        cache_key = self._make_cache_key(request)
        if self._config.enable_caching and cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        is_tick = request.data_kind.lower() in {"ticks", "tick"}
        provider = request.source_id.lower()

        # 1. Dataset ID lookup
        if provider.startswith("ds_") or provider == "dataset":
            result = await self._fetch_from_dataset(request, is_tick)
        # 2. Feed connector lookup
        elif provider in self._connectors:
            conn = self._connectors[provider]
            if is_tick:
                result, _ = await self._fetch_ticks_from_connector(request, conn)
            else:
                result, _ = await self._fetch_bars_from_connector(request, conn)
        # 3. Search existing manifests
        else:
            result = await self._search_manifests(request, is_tick)

        if self._config.enable_caching and result:
            if len(self._cache) >= self._config.max_cache_items:
                self._cache.popitem(last=False)
            self._cache[cache_key] = result
        return result

    @override
    async def sync_connectors(
        self,
        provider_ids: list[str] | None = None,
        symbols: list[str] | None = None,
    ) -> SyncReport:
        """Coordinate idempotent synchronization with registered external providers."""
        started_at = datetime.now(UTC)
        errors: list[str] = []
        synced: list[str] = []
        intervals: list[SyncInterval] = []
        total_records = 0

        target_connectors = [
            (k, v)
            for k, v in self._connectors.items()
            if not provider_ids or k in provider_ids
        ]

        target_symbols = symbols or ["EURUSD"]

        for name, conn in target_connectors:
            provider_synced = False
            for symbol in target_symbols:
                try:
                    existing = await self._dataset_service.list_manifests(
                        symbol=symbol, timeframe="M1"
                    )
                    latest_end: datetime | None = None
                    for m in existing:
                        if m.source_id == name and (
                            latest_end is None or m.end_time > latest_end
                        ):
                            latest_end = m.end_time

                    now_utc = datetime.now(UTC)
                    sync_start = latest_end or (now_utc - timedelta(days=1))
                    sync_end = now_utc

                    if sync_start >= sync_end:
                        continue

                    req = build_market_data_request(
                        source_id=name,
                        symbol=symbol,
                        data_kind="bars",
                        timeframe="M1",
                        start=sync_start,
                        end=sync_end,
                        store_data=True,
                    )
                    bars, dedup_count = await self._fetch_bars_from_connector(req, conn)
                    fetched_count = len(bars)
                    total_records += fetched_count

                    dataset_id = ""
                    if bars:
                        manifests = await self._dataset_service.list_manifests(
                            symbol=symbol, timeframe="M1"
                        )
                        matching = [m for m in manifests if m.source_id == name]
                        if matching:
                            dataset_id = matching[-1].dataset_id

                    intervals.append(
                        SyncInterval(
                            provider=name,
                            symbol=symbol,
                            start=sync_start,
                            end=sync_end,
                            records_fetched=fetched_count,
                            records_deduplicated=dedup_count,
                            dataset_id=dataset_id,
                        )
                    )
                    provider_synced = True
                except Exception as exc:  # noqa: BLE001
                    msg = f"Connector '{name}' sync failed for {symbol}: {exc}"
                    errors.append(msg)
                    logger.warning(
                        "connector_sync_failed",
                        provider=name,
                        symbol=symbol,
                        error=str(exc),
                    )

            if provider_synced:
                synced.append(name)
                logger.info(
                    "connector_sync_completed",
                    provider=name,
                    intervals_synced=len(intervals),
                )

        return SyncReport(
            started_at=started_at,
            completed_at=datetime.now(UTC),
            providers_synced=tuple(synced),
            total_records=total_records,
            errors=tuple(errors),
            intervals=tuple(intervals),
        )


SPEC: FeatureSpec = FeatureSpec(
    name="data.market_data",
    provides=frozenset({DATA_MARKET_DATA, DATA_SYNC}),
    requires=frozenset({DATA_DATASETS}),
    optional=frozenset(
        {
            DATA_PERSISTENCE,
            DATA_QUALITY,
            BROKER_DUKASCOPY,
            BROKER_EQUITY,
            BROKER_FUTURES,
            BROKER_DARWINEX,
            BROKER_CRYPTO,
            BROKER_YAHOO,
        }
    ),
    description="Governed market data retrieval, caching, and connector sync.",
)


class MarketDataFeature:
    """Wire market data retrieval feature into kernel composition lifecycle."""

    def __init__(self, config: MarketDataConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional market data configuration.
        """
        self._config = config or MarketDataConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve dependencies and provide market data client and sync capability.

        Args:
            context: Lifecycle feature context.
        """
        dataset_svc = context.require(DATA_DATASETS)
        persistence = context.optional(DATA_PERSISTENCE)
        quality_svc = context.optional(DATA_QUALITY)

        # Collect optional registered broker feed connectors
        connectors: dict[str, BrokerFeedConnector] = {}
        for token, name in [
            (BROKER_DUKASCOPY, "dukascopy"),
            (BROKER_EQUITY, "sq_equity"),
            (BROKER_FUTURES, "sq_futures"),
            (BROKER_DARWINEX, "darwinex"),
            (BROKER_CRYPTO, "crypto"),
            (BROKER_YAHOO, "yahoo"),
        ]:
            conn = context.optional(token)
            if conn is not None:
                connectors[name] = conn

        service = MarketDataServiceImpl(
            dataset_service=dataset_svc,
            persistence=persistence,
            quality_service=quality_svc,
            connectors=connectors,
            config=self._config,
        )
        context.provide(DATA_MARKET_DATA, service)
        context.provide(DATA_SYNC, service)
        logger.info("data_market_data_feature_started")


def feature() -> MarketDataFeature:
    """Return an unmounted MarketDataFeature instance.

    Returns:
        New MarketDataFeature instance.
    """
    return MarketDataFeature()


__all__ = [
    "SPEC",
    "MarketDataConfig",
    "MarketDataFeature",
    "MarketDataServiceImpl",
    "feature",
]
