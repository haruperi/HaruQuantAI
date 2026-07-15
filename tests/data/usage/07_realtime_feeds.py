"""Run internal real-time feed lifecycle, ingestion, and status examples."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_feed_status
from app.services.data.config import DataSettings, data_settings_context
from app.services.data.contracts import (
    FeedConfig,
    FeedStatusRequest,
    RawFeedEvent,
    RawSourceBatch,
    ReconnectPolicy,
    SourceDescriptor,
    SourceLicensePolicy,
    SourceReadRequest,
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.feeds.runtime import ingest_feed_event, start_internal_feed
from app.services.data.sources import MarketDataSource, register_source
from app.services.data.storage.migrations import run_data_migrations
from app.utils import generate_id, logger

_SOURCE_ID = "usage-live-source"
_FEED_ID = "usage-btcusd-ticks"
_OBSERVED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


class DeclaredLiveSource(MarketDataSource):
    """Placeholder source object behind a separately injected feed transport."""

    def fetch(self, request: SourceReadRequest) -> RawSourceBatch:
        """Reject historical reads because this declaration is live-only."""
        logger.info("Rejecting unsupported historical read for %s", request.source_id)
        raise NotImplementedError("the usage source declares only live capability")

    def list_symbols(self, request: SymbolListRequest) -> SymbolPage:
        """Return the one symbol configured for the internal feed."""
        logger.info("Listing the configured live-feed symbol")
        return SymbolPage(
            source_id=request.source_id,
            items=("BTCUSDT",),
            limit=request.limit,
            revision="usage-live-v1",
            request_id=request.request_id,
        )

    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SymbolMetadata:
        """Reject metadata reads not demonstrated by this live-only source."""
        logger.info("Rejecting unsupported metadata read for %s", request.symbol)
        raise NotImplementedError("metadata is outside this live-feed example")


def _configure_environment(root: Path) -> None:
    """Configure isolated feed state and register live capability."""
    logger.info("Configuring isolated feed state under %s", root)
    run_data_migrations(generate_id("req"))
    descriptor = SourceDescriptor(
        source_id=_SOURCE_ID,
        readiness="staging",
        capabilities=("live",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="usage-live-v1",
        license_policy=SourceLicensePolicy(
            source_id=_SOURCE_ID,
            status="approved",
            permitted_workflows=("research", "validation"),
            export_allowed=False,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("bounded-feed-probe",),
    )
    register_source(descriptor, DeclaredLiveSource)


def _feed_config() -> FeedConfig:
    """Build one bounded internal feed configuration."""
    logger.info("Building a bounded internal feed configuration")
    return FeedConfig(
        feed_id=_FEED_ID,
        source_id=_SOURCE_ID,
        symbol="BTCUSDT",
        data_kind="tick",
        source_capability="live",
        buffer_capacity=100,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=5,
        reconnect_policy=ReconnectPolicy(
            max_retries=3,
            initial_backoff_seconds=1,
            max_backoff_seconds=10,
            jitter_seconds=0,
            circuit_cooldown_seconds=30,
        ),
        request_id=generate_id("req"),
    )


def example_fr_data_046_start_internal_feed() -> None:
    """Start one bounded internal feed without exposing a subscription handle."""
    logger.info("FR-DATA-046: starting an internal live-capable feed")
    status = start_internal_feed(_feed_config())
    logger.info(
        "Feed=%s state=%s capacity=%d",
        status.feed_id,
        status.state,
        status.buffer_capacity,
    )


def example_fr_data_047_ingest_event() -> None:
    """Ingest a sequenced event and update durable heartbeat evidence."""
    logger.info("FR-DATA-047: ingesting one sequenced feed event")
    event = RawFeedEvent(
        feed_id=_FEED_ID,
        sequence=1,
        event_timestamp=_OBSERVED_AT,
        received_at=_OBSERVED_AT + timedelta(milliseconds=25),
        payload={"bid": "60000.00", "ask": "60000.50", "size": "0.10"},
        request_id=generate_id("req"),
    )
    result = ingest_feed_event(_FEED_ID, event)
    if not result.accepted:
        raise AssertionError("valid feed event was not accepted")
    logger.info("Accepted sequence=%d depth=%d", event.sequence, result.buffer_depth)


def example_fr_data_048_read_status() -> None:
    """Read feed depth, drift, gaps, drops, and heartbeat state."""
    logger.info("FR-DATA-048: reading status backed by real feed runtime state")
    status = get_feed_status(
        FeedStatusRequest(feed_id=_FEED_ID, request_id=generate_id("req"))
    )
    logger.info(
        "Feed state=%s depth=%d drift_ms=%s dropped=%d gaps=%d",
        status.state,
        status.buffer_depth,
        status.drift_ms,
        status.dropped_count,
        status.gap_count,
    )


if __name__ == "__main__":
    with TemporaryDirectory(prefix="haru-data-feeds-") as directory:
        demo_root = Path(directory)
        settings = DataSettings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=demo_root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            _configure_environment(demo_root)
            example_fr_data_046_start_internal_feed()
            example_fr_data_047_ingest_event()
            example_fr_data_048_read_status()
