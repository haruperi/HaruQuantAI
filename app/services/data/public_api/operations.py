"""Focused typed public operations for the DATA domain.

This layer exposes approved Data operations through typed Data-owned requests,
results, and errors. It performs no generic wrapping and defines no parallel
business logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pandas import DataFrame

    from app.services.data.access.sessions import MarketCalendar
    from app.services.data.contracts import (
        AvailabilityRequest,
        CacheClearRequest,
        CacheClearResult,
        DataAvailability,
        DatasetLoadRequest,
        DatasetSaveRequest,
        FeedStatus,
        FeedStatusRequest,
        JobDefinition,
        JobRunResult,
        JobStatus,
        JobStatusRequest,
        MarketDataRequest,
        MarketDataset,
        MarketSchedule,
        ScheduleRequest,
        StorageManifest,
        SymbolListRequest,
        SymbolMetadata,
        SymbolMetadataRequest,
        SymbolPage,
        SyntheticRequest,
        VolumeRequest,
        VolumeResult,
    )
    from app.services.data.contracts.market import PrecisionPolicy
    from app.services.data.contracts.sources import WorkflowContext

from app.services.data.contracts.errors import DataError
from app.services.data.public_api._requests import (
    availability_request,
    market_request,
    schedule_request,
    symbol_list_request,
    symbol_metadata_request,
    volume_request,
)
from app.services.data.public_api._runtime import (
    ensure_identity,
    ensure_source,
    ensure_source_access,
    ensure_storage,
    resolve_calendar,
)
from app.utils import logger


def get_market_data(
    request: MarketDataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    use_cache: bool | None = None,
    cache_ttl_seconds: int | None = None,
    quality_failure_behavior: Literal["fail", "warn"] | None = None,
    workflow_context: WorkflowContext | None = None,
    precision_policy: PrecisionPolicy | None = None,
    fallback_sources: tuple[str, ...] | None = None,
    source_timezone: str | None = None,
    request_id: str | None = None,
) -> MarketDataset:
    """Retrieve bars using a typed request or direct keyword arguments.

    Returns:
        The normalized market dataset.
    """
    logger.info("Executing public DATA market retrieval")
    resolved = market_request(
        request,
        data_kind=None,
        source_id=source_id,
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
        quality_failure_behavior=quality_failure_behavior,
        workflow_context=workflow_context,
        precision_policy=precision_policy,
        fallback_sources=fallback_sources,
        source_timezone=source_timezone,
        request_id=request_id,
    )
    ensure_storage(resolved.request_id)
    ensure_identity(
        resolved.source_id,
        resolved.symbol,
        resolved.request_id,
    )
    from app.services.data.access.historical import fetch_market_dataset

    return fetch_market_dataset(resolved)


def get_tick_data(
    request: MarketDataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    use_cache: bool | None = None,
    cache_ttl_seconds: int | None = None,
    quality_failure_behavior: Literal["fail", "warn"] | None = None,
    workflow_context: WorkflowContext | None = None,
    precision_policy: PrecisionPolicy | None = None,
    fallback_sources: tuple[str, ...] | None = None,
    source_timezone: str | None = None,
    request_id: str | None = None,
) -> MarketDataset:
    """Retrieve ticks using a typed request or direct keyword arguments.

    Returns:
        The normalized tick dataset.
    """
    logger.info("Executing public DATA tick retrieval")
    resolved = market_request(
        request,
        data_kind="ticks",
        source_id=source_id,
        symbol=symbol,
        timeframe=None,
        start=start,
        end=end,
        limit=limit,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
        quality_failure_behavior=quality_failure_behavior,
        workflow_context=workflow_context,
        precision_policy=precision_policy,
        fallback_sources=fallback_sources,
        source_timezone=source_timezone,
        request_id=request_id,
    )
    ensure_storage(resolved.request_id)
    ensure_identity(
        resolved.source_id,
        resolved.symbol,
        resolved.request_id,
    )
    from app.services.data.access.historical import fetch_market_dataset

    return fetch_market_dataset(resolved)


def get_spread_data(
    request: MarketDataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    use_cache: bool | None = None,
    cache_ttl_seconds: int | None = None,
    quality_failure_behavior: Literal["fail", "warn"] | None = None,
    workflow_context: WorkflowContext | None = None,
    precision_policy: PrecisionPolicy | None = None,
    fallback_sources: tuple[str, ...] | None = None,
    source_timezone: str | None = None,
    request_id: str | None = None,
) -> MarketDataset:
    """Retrieve spreads using a typed request or direct keyword arguments.

    Returns:
        The normalized spread dataset.
    """
    logger.info("Executing public DATA spread retrieval")
    resolved = market_request(
        request,
        data_kind="spreads",
        source_id=source_id,
        symbol=symbol,
        timeframe=None,
        start=start,
        end=end,
        limit=limit,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
        quality_failure_behavior=quality_failure_behavior,
        workflow_context=workflow_context,
        precision_policy=precision_policy,
        fallback_sources=fallback_sources,
        source_timezone=source_timezone,
        request_id=request_id,
    )
    ensure_storage(resolved.request_id)
    ensure_identity(
        resolved.source_id,
        resolved.symbol,
        resolved.request_id,
    )
    from app.services.data.access.historical import fetch_market_dataset

    return fetch_market_dataset(resolved)


def get_symbol_metadata(
    request: SymbolMetadataRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    request_id: str | None = None,
) -> SymbolMetadata:
    """Retrieve symbol metadata using a request or direct keywords.

    Returns:
        Normalized provider symbol metadata.
    """
    logger.info("Executing public DATA symbol metadata retrieval")
    resolved = symbol_metadata_request(
        request,
        source_id=source_id,
        symbol=symbol,
        request_id=request_id,
    )
    ensure_source_access(resolved.source_id, resolved.request_id)
    from app.services.data.access.reference import fetch_symbol_metadata

    return fetch_symbol_metadata(resolved)


def list_symbols(
    request: SymbolListRequest | None = None,
    *,
    source_id: str | None = None,
    query: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
    request_id: str | None = None,
) -> SymbolPage:
    """List provider symbols using a request or direct keywords.

    Returns:
        A bounded provider symbol page.
    """
    logger.info("Executing public DATA symbol listing")
    resolved = symbol_list_request(
        request,
        source_id=source_id,
        query=query,
        cursor=cursor,
        limit=limit,
        request_id=request_id,
    )
    ensure_source_access(resolved.source_id, resolved.request_id)
    from app.services.data.access.reference import discover_symbols

    return discover_symbols(resolved)


def get_data_availability(
    request: AvailabilityRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    data_kind: Literal["ohlcv", "tick", "spread"] | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    max_probe_records: int | None = None,
    request_id: str | None = None,
) -> DataAvailability:
    """Inspect local availability using a request or direct keywords.

    Returns:
        Stored-range and completeness evidence.
    """
    logger.info("Executing public DATA availability query")
    resolved = availability_request(
        request,
        source_id=source_id,
        symbol=symbol,
        data_kind=data_kind,
        timeframe=timeframe,
        start=start,
        end=end,
        max_probe_records=max_probe_records,
        request_id=request_id,
    )
    ensure_source(resolved.source_id, resolved.request_id)
    from app.services.data.access.reference import inspect_availability

    return inspect_availability(resolved)


def get_market_hours(
    request: ScheduleRequest | None = None,
    calendar: MarketCalendar | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timezone: str | None = None,
    request_id: str | None = None,
) -> MarketSchedule:
    """Retrieve market hours using a request or direct keywords.

    Returns:
        The current authoritative market schedule.
    """
    logger.info("Executing public DATA market-hours query")
    resolved = schedule_request(
        request,
        view="hours",
        source_id=source_id,
        symbol=symbol,
        timezone=timezone,
        request_id=request_id,
    )
    selected_calendar = calendar or resolve_calendar(
        resolved.source_id,
        resolved.request_id,
    )
    ensure_source(resolved.source_id, resolved.request_id)
    from app.services.data.access.sessions import get_current_schedule

    return get_current_schedule(resolved, selected_calendar)


def get_trading_sessions(
    request: ScheduleRequest | None = None,
    calendar: MarketCalendar | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    timezone: str | None = None,
    request_id: str | None = None,
) -> MarketSchedule:
    """Retrieve trading sessions using a request or direct keywords.

    Returns:
        The current authoritative trading-session schedule.
    """
    logger.info("Executing public DATA trading-session query")
    resolved = schedule_request(
        request,
        view="sessions",
        source_id=source_id,
        symbol=symbol,
        timezone=timezone,
        request_id=request_id,
    )
    selected_calendar = calendar or resolve_calendar(
        resolved.source_id,
        resolved.request_id,
    )
    ensure_source(resolved.source_id, resolved.request_id)
    from app.services.data.access.sessions import get_current_schedule

    return get_current_schedule(resolved, selected_calendar)


def get_historical_volume(
    request: VolumeRequest | None = None,
    *,
    source_id: str | None = None,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    mode: Literal["records", "buckets", "summary"] | None = None,
    bucket_seconds: int | None = None,
    limit: int | None = None,
    request_id: str | None = None,
) -> VolumeResult:
    """Retrieve historical volume using a request or direct keywords.

    Returns:
        Historical volume records, buckets, or summary evidence.
    """
    logger.info("Executing public DATA historical-volume query")
    resolved = volume_request(
        request,
        source_id=source_id,
        symbol=symbol,
        start=start,
        end=end,
        mode=mode,
        bucket_seconds=bucket_seconds,
        limit=limit,
        request_id=request_id,
    )
    ensure_storage(resolved.request_id)
    ensure_identity(
        resolved.source_id,
        resolved.symbol,
        resolved.request_id,
    )
    from app.services.data.access.sessions import fetch_historical_volume

    return fetch_historical_volume(resolved)


def save_market_data(request: DatasetSaveRequest) -> StorageManifest:
    """Atomically commit a normalized dataset to disk with manifest signature."""
    logger.info("Executing public DATA dataset save")
    from app.services.data.storage.datasets import save_dataset

    return save_dataset(request)


def load_local_dataset(request: DatasetLoadRequest) -> MarketDataset:
    """Atomically read a local CSV/Parquet dataset with checksum verification."""
    logger.info("Executing public DATA dataset load")
    from app.services.data.storage.datasets import load_dataset

    return load_dataset(request)


def clear_data_cache(request: CacheClearRequest) -> CacheClearResult:
    """Clear select cached datasets matching source/symbol/kind selectors."""
    logger.info("Executing public DATA cache clear")
    from app.services.data.storage.cache import clear_cache_entry

    return clear_cache_entry(request)


def resample_ohlcv(dataset: MarketDataset, target_timeframe: str) -> MarketDataset:
    """Roll up OHLCV records to a larger timeframe."""
    logger.info("Executing public DATA OHLCV resample")
    from app.services.data.processing.transforms import resample_dataset

    return resample_dataset(dataset, target_timeframe)


def to_ohlcv_dataframe(dataset: MarketDataset) -> DataFrame:
    """Return a six-column float64 analytical copy of one OHLCV dataset.

    Returns:
        A DataFrame indexed by aware UTC timestamps.

    Raises:
        DataError: If the dataset is not canonical OHLCV bars or its numeric
            values cannot be represented as finite float64 values.
    """
    logger.info("Executing public DATA OHLCV dataframe projection")
    from app.services.data.processing.tabular import (
        to_ohlcv_dataframe as project_to_ohlcv_dataframe,
    )

    return project_to_ohlcv_dataframe(dataset)


def to_tick_dataframe(dataset: MarketDataset) -> DataFrame:
    """Return a four-column float64 analytical copy of one tick dataset.

    Returns:
        A DataFrame indexed by aware UTC timestamps, with genuine missing optional
        values represented as ``NaN``.

    Raises:
        DataError: If the dataset is not canonical ticks, units are inconsistent,
            or numeric values cannot be represented safely as float64.
    """
    logger.info("Executing public DATA tick dataframe projection")
    from app.services.data.processing.tabular import (
        to_tick_dataframe as project_to_tick_dataframe,
    )

    return project_to_tick_dataframe(dataset)


def align_multitimeframe_data(
    datasets: Mapping[str, MarketDataset],
    target_timestamps: Sequence[datetime],
) -> Mapping[str, MarketDataset]:
    """Align multiple datasets to a uniform timestamp index with forward fill."""
    logger.info("Executing public DATA multi-timeframe alignment")
    from app.services.data.processing.transforms import align_datasets

    return align_datasets(datasets, target_timestamps)


def generate_synthetic_ticks(request: SyntheticRequest) -> MarketDataset:
    """Generate GBM-based synthetic tick records; raises if kind is not ticks."""
    logger.info("Executing public DATA synthetic-tick generation")
    if request.data_kind != "ticks":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"generate_synthetic_ticks requires ticks data_kind, "
                    f"got '{request.data_kind}'"
                )
            },
            request_id=request.request_id,
        )
    from app.services.data.processing.synthetic import generate_synthetic_dataset

    return generate_synthetic_dataset(request)


def generate_synthetic_bars(request: SyntheticRequest) -> MarketDataset:
    """Generate GBM-based synthetic OHLCV bar records; raises if kind is not bars."""
    logger.info("Executing public DATA synthetic-bar generation")
    if request.data_kind != "bars":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"generate_synthetic_bars requires bars data_kind, "
                    f"got '{request.data_kind}'"
                )
            },
            request_id=request.request_id,
        )
    from app.services.data.processing.synthetic import generate_synthetic_dataset

    return generate_synthetic_dataset(request)


def aggregate_ticks_to_bars(
    dataset: MarketDataset,
    target_timeframe: str,
    price_policy: str = "last",
) -> MarketDataset:
    """Aggregate tick records into custom-timeframe OHLCV bars."""
    logger.info("Executing public DATA tick aggregation")
    from app.services.data.processing.transforms import aggregate_ticks

    return aggregate_ticks(dataset, target_timeframe, price_policy)


def create_data_update_job(definition: JobDefinition, request_id: str) -> JobStatus:
    """Register a new persistent update/backfill job schedule."""
    logger.info("Executing public DATA job creation")
    from app.services.data.contracts.jobs import ScheduleJobRequest
    from app.services.data.jobs.scheduler import schedule_update_job

    req = ScheduleJobRequest(
        action="create",
        job_id=definition.job_id,
        definition=definition,
        request_id=request_id,
    )
    return schedule_update_job(req)


def start_data_update_job(job_id: str, request_id: str) -> JobStatus:
    """Transitions a configured job state to active scheduling."""
    logger.info("Executing public DATA job start")
    from app.services.data.contracts.jobs import ScheduleJobRequest
    from app.services.data.jobs.scheduler import schedule_update_job

    req = ScheduleJobRequest(
        action="start",
        job_id=job_id,
        request_id=request_id,
    )
    return schedule_update_job(req)


def stop_data_update_job(job_id: str, request_id: str) -> JobStatus:
    """Transitions an active job state to stopped."""
    logger.info("Executing public DATA job stop")
    from app.services.data.contracts.jobs import ScheduleJobRequest
    from app.services.data.jobs.scheduler import schedule_update_job

    req = ScheduleJobRequest(
        action="stop",
        job_id=job_id,
        request_id=request_id,
    )
    return schedule_update_job(req)


def run_data_update_job_once(job_id: str, request_id: str) -> JobRunResult:
    """Trigger a single immediate backfill run for the job."""
    logger.info("Executing public DATA one-shot job run")
    from app.services.data.jobs.scheduler import run_data_update_job_once as run_once

    return run_once(job_id, request_id)


def get_data_update_job_status(request: JobStatusRequest) -> JobStatus:
    """Query configuration, schedules, and active run status of a job."""
    logger.info("Executing public DATA job-status query")
    from app.services.data.jobs.scheduler import read_update_job_status

    return read_update_job_status(request)


def get_feed_status(request: FeedStatusRequest) -> FeedStatus:
    """Query live feed buffer metrics, drift, and reconnect status."""
    logger.info("Executing public DATA feed-status query")
    from app.services.data.feeds.status import read_feed_status

    return read_feed_status(request)


__all__ = [
    "aggregate_ticks_to_bars",
    "align_multitimeframe_data",
    "clear_data_cache",
    "create_data_update_job",
    "generate_synthetic_bars",
    "generate_synthetic_ticks",
    "get_data_availability",
    "get_data_update_job_status",
    "get_feed_status",
    "get_historical_volume",
    "get_market_data",
    "get_market_hours",
    "get_spread_data",
    "get_symbol_metadata",
    "get_tick_data",
    "get_trading_sessions",
    "list_symbols",
    "load_local_dataset",
    "resample_ohlcv",
    "run_data_update_job_once",
    "save_market_data",
    "start_data_update_job",
    "stop_data_update_job",
    "to_ohlcv_dataframe",
    "to_tick_dataframe",
]
