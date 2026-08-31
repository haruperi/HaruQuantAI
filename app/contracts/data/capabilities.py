"""Data domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.data.ports import (
        AggregateBarsCapability,
        AlignSeriesCapability,
        BindRunDataCapability,
        GenerateScenariosCapability,
        ImportIndicatorsCapability,
        ImportQuantdataCapability,
        IngestHistoryCapability,
        ManageRetentionCapability,
        NormalizeTicksCapability,
        PrepareProfilesCapability,
        ResolveQualityCapability,
        StreamMarketEventsCapability,
        SyncConnectorsCapability,
        TrackMarketNewsCapability,
    )

INGEST_HISTORY_CAPABILITY: CapabilityKey[IngestHistoryCapability] = CapabilityKey(
    name="data.ingest-history",
    major=1,
)

SYNC_CONNECTORS_CAPABILITY: CapabilityKey[SyncConnectorsCapability] = CapabilityKey(
    name="data.sync-connectors",
    major=1,
)

IMPORT_QUANTDATA_CAPABILITY: CapabilityKey[ImportQuantdataCapability] = CapabilityKey(
    name="data.import-quantdata",
    major=1,
)

NORMALIZE_TICKS_CAPABILITY: CapabilityKey[NormalizeTicksCapability] = CapabilityKey(
    name="data.normalize-ticks",
    major=1,
)

RESOLVE_QUALITY_CAPABILITY: CapabilityKey[ResolveQualityCapability] = CapabilityKey(
    name="data.resolve-quality",
    major=1,
)

AGGREGATE_BARS_CAPABILITY: CapabilityKey[AggregateBarsCapability] = CapabilityKey(
    name="data.aggregate-bars",
    major=1,
)

MANAGE_RETENTION_CAPABILITY: CapabilityKey[ManageRetentionCapability] = CapabilityKey(
    name="data.manage-retention",
    major=1,
)

ALIGN_SERIES_CAPABILITY: CapabilityKey[AlignSeriesCapability] = CapabilityKey(
    name="data.align-series",
    major=1,
)

PREPARE_PROFILES_CAPABILITY: CapabilityKey[PrepareProfilesCapability] = CapabilityKey(
    name="data.prepare-profiles",
    major=1,
)

IMPORT_INDICATORS_CAPABILITY: CapabilityKey[ImportIndicatorsCapability] = CapabilityKey(
    name="data.import-indicators",
    major=1,
)

BIND_RUN_DATA_CAPABILITY: CapabilityKey[BindRunDataCapability] = CapabilityKey(
    name="data.bind-run-data",
    major=1,
)

GENERATE_SCENARIOS_CAPABILITY: CapabilityKey[GenerateScenariosCapability] = (
    CapabilityKey(
        name="data.generate-scenarios",
        major=1,
    )
)

TRACK_MARKET_NEWS_CAPABILITY: CapabilityKey[TrackMarketNewsCapability] = CapabilityKey(
    name="data.track-market-news",
    major=1,
)

STREAM_MARKET_EVENTS_CAPABILITY: CapabilityKey[StreamMarketEventsCapability] = (
    CapabilityKey(
        name="data.stream-market-events",
        major=1,
    )
)
