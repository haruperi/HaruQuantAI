"""Run bounded backfill, recovery, status, and recurrent-worker lifecycle examples."""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import app.services.data as data_api
from app.services.data import (
    create_data_update_job,
    get_data_update_job_status,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.config import DataSettings, data_settings_context
from app.services.data.contracts import (
    BackfillChunkRequest,
    JobDefinition,
    JobStatusRequest,
    RawSourceBatch,
    SourceDescriptor,
    SourceIdentity,
    SourceLicensePolicy,
    SourceReadRequest,
    SymbolListRequest,
    SymbolMetadata,
    SymbolMetadataRequest,
    SymbolPage,
)
from app.services.data.jobs.backfill import (
    derive_backfill_key,
    execute_backfill_chunk,
    recover_update_jobs,
)
from app.services.data.sources import MarketDataSource, register_source
from app.services.data.sources.policy import SourcePolicyConfig, register_source_policy
from app.services.data.storage.migrations import run_data_migrations
from app.utils import generate_id, logger

_SOURCE_ID = "usage-job-source"
_JOB_ID = "usage-aapl-m1-update"
_START = datetime(2026, 7, 1, 13, 30, tzinfo=UTC)
_END = _START + timedelta(minutes=1)


class JobMarketDataSource(MarketDataSource):
    """Concrete bounded source used by the backfill example."""

    def fetch(self, request: SourceReadRequest) -> RawSourceBatch:
        """Return two exact bars for the requested backfill range."""
        logger.info(
            "Reading the bounded update-job source for %s", request.provider_symbol
        )
        records = tuple(
            {
                "timestamp": _START + timedelta(minutes=index),
                "open": Decimal(210) + index,
                "high": Decimal(211) + index,
                "low": Decimal(209) + index,
                "close": Decimal("210.5") + index,
                "volume": Decimal(1000) + (index * 100),
                "price_unit": "USD",
                "volume_unit": "shares",
                "source": request.source_id,
                "source_symbol": request.provider_symbol,
                "source_revision": "job-source-v1",
                "available_at": _END + timedelta(seconds=1),
            }
            for index in range(2)
        )
        return RawSourceBatch(
            source_id=request.source_id,
            provider_symbol=request.provider_symbol,
            data_kind=request.data_kind,
            records=records,
            retrieved_at=_END + timedelta(seconds=1),
            revision="job-source-v1",
            request_id=request.request_id,
        )

    def list_symbols(self, request: SymbolListRequest) -> SymbolPage:
        """Return the source's single configured symbol."""
        logger.info("Listing symbols from the update-job source")
        return SymbolPage(
            source_id=request.source_id,
            items=("AAPL",),
            limit=request.limit,
            revision="job-source-v1",
            request_id=request.request_id,
        )

    def get_symbol_metadata(self, request: SymbolMetadataRequest) -> SymbolMetadata:
        """Return exact metadata for the configured symbol."""
        logger.info("Reading update-job source metadata for %s", request.symbol)
        return SymbolMetadata(
            canonical_symbol="AAPL",
            provider_symbol="AAPL",
            asset_class="equity",
            base_currency="USD",
            digits=2,
            price_step=Decimal("0.01"),
            quantity_step=Decimal(1),
            timezone="America/New_York",
            source_id=request.source_id,
            revision="job-source-v1",
            retrieved_at=_END,
            missing_fields=("quote_currency",),
            request_id=request.request_id,
        )


def _configure_environment(root: Path) -> None:
    """Configure isolated persistence and the bounded update source."""
    logger.info("Configuring isolated update-job state under %s", root)
    for relative in ("data/raw", "data/processed", "data/cache", "artifacts/data"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    run_data_migrations(generate_id("req"))
    descriptor = SourceDescriptor(
        source_id=_SOURCE_ID,
        readiness="production",
        capabilities=("bars",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="America/New_York",
        revision="job-source-v1",
        license_policy=SourceLicensePolicy(
            source_id=_SOURCE_ID,
            status="approved",
            permitted_workflows=("validation",),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("bounded-backfill",),
    )
    identity = SourceIdentity(
        source_id=_SOURCE_ID,
        canonical_symbol="AAPL",
        friendly_name="Apple Inc.",
        provider_symbol="AAPL",
        mapping_revision="mapping-v1",
        provenance={"catalog": "usage-v1"},
        request_id=generate_id("req"),
    )
    register_source(descriptor, JobMarketDataSource, identities=(identity,))
    register_source_policy(
        SourcePolicyConfig(
            source_id=_SOURCE_ID,
            rate_limit=100,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=30,
        )
    )


def _chunk_request() -> BackfillChunkRequest:
    """Build the bounded chunk shared by key and execution examples."""
    logger.info("Building a bounded update-job chunk request")
    return BackfillChunkRequest(
        job_id=_JOB_ID,
        source_id=_SOURCE_ID,
        symbol="AAPL",
        data_kind="ohlcv",
        timeframe="M1",
        start=_START,
        end=_END,
        schema_version="v1",
        normalization_version="v1",
        max_records=10,
        request_id=generate_id("req"),
    )


def example_fr_data_041_backfill_key() -> str:
    """Derive a stable idempotency key from the complete chunk identity."""
    logger.info("FR-DATA-041: deriving a canonical backfill idempotency key")
    key = derive_backfill_key(_chunk_request())
    logger.info("Backfill key=%s", key)
    return key


def example_fr_data_044_create_recurrent_job() -> None:
    """Persist a disabled recurrent job definition before starting it."""
    logger.info("FR-DATA-044: creating a recurrent update-job definition")
    status = create_data_update_job(
        JobDefinition(
            job_id=_JOB_ID,
            source_id=_SOURCE_ID,
            symbols=("AAPL",),
            timeframes=("M1",),
            data_kinds=("ohlcv",),
            start=_START,
            end=_END,
            interval_seconds=300,
            enabled=False,
            created_at=_START,
            request_id=generate_id("req"),
        ),
        generate_id("req"),
    )
    logger.info("Created job=%s enabled=%s", status.job_id, status.enabled)


def example_fr_data_042_execute_chunk() -> None:
    """Retrieve, normalize, publish, and checkpoint one bounded chunk."""
    logger.info("FR-DATA-042: executing one bounded backfill chunk")
    result = execute_backfill_chunk(_chunk_request())
    if not result.committed:
        raise AssertionError("backfill chunk did not commit")
    logger.info(
        "Committed chunk key=%s records=%d checkpoint=%s",
        result.idempotency_key,
        result.record_count,
        result.checkpoint,
    )


def example_fr_data_084_private_chunking_boundary() -> None:
    """Show that generic sequence chunking is absent from the public DATA API."""
    logger.info("FR-DATA-084: verifying the private bounded chunking boundary")
    forbidden_exports = (
        "chunk_data",
        "chunk_sequence",
        "execute_backfill_chunk",
    )
    leaked_exports = tuple(
        name for name in forbidden_exports if hasattr(data_api, name)
    )
    if leaked_exports:
        raise AssertionError(f"private chunking exports leaked: {leaked_exports}")
    request = _chunk_request()
    logger.info(
        "Backfill workflow owns chunk bound=%d over span=%s",
        request.max_records,
        request.end - request.start,
    )


def example_fr_data_043_recovery() -> None:
    """Verify persisted job/checkpoint state is clean after commit."""
    logger.info("FR-DATA-043: verifying restart-safe recovery state")
    report = recover_update_jobs(generate_id("req"))
    logger.info(
        "Recovered jobs=%s blocked jobs=%s",
        report.recovered_job_ids,
        report.blocked_job_ids,
    )


def example_fr_data_045_status_query() -> None:
    """Read persisted definition, state, and checkpoint evidence without mutation."""
    logger.info("FR-DATA-045: querying persisted update-job status")
    status = get_data_update_job_status(
        JobStatusRequest(job_id=_JOB_ID, request_id=generate_id("req"))
    )
    logger.info(
        "Job=%s state=%s enabled=%s checkpoint=%s",
        status.job_id,
        status.state,
        status.enabled,
        status.last_checkpoint,
    )


def example_fr_data_044_start_stop_worker() -> None:
    """Start and stop the single-node in-process recurrent worker task."""
    logger.info("FR-DATA-044: starting and stopping the recurrent worker task")

    async def exercise() -> None:
        """Keep one running event loop alive while the worker is registered."""
        logger.info("Starting recurrent worker inside a running event loop")
        started = start_data_update_job(_JOB_ID, generate_id("req"))
        if not started.enabled:
            raise AssertionError("update job did not enter enabled state")
        await asyncio.sleep(0)
        stopped = stop_data_update_job(_JOB_ID, generate_id("req"))
        if stopped.enabled:
            raise AssertionError("update job did not stop")
        await asyncio.sleep(0)
        logger.info("Worker lifecycle completed with state=%s", stopped.state)

    asyncio.run(exercise())


if __name__ == "__main__":
    with TemporaryDirectory(prefix="haru-data-jobs-") as directory:
        demo_root = Path(directory)
        settings = DataSettings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=demo_root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            _configure_environment(demo_root)
            example_fr_data_041_backfill_key()
            example_fr_data_044_create_recurrent_job()
            example_fr_data_045_status_query()
            example_fr_data_042_execute_chunk()
            example_fr_data_084_private_chunking_boundary()
            example_fr_data_043_recovery()
            example_fr_data_044_start_stop_worker()
