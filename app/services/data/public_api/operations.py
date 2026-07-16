"""Focused typed public operations for the DATA domain.

This layer exposes approved Data operations through typed Data-owned requests,
results, and errors. It performs no generic wrapping and defines no parallel
business logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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

from app.services.data.contracts.errors import DataError
from app.utils import logger


def get_market_data(request: MarketDataRequest) -> MarketDataset:
    """Retrieve OHLCV bars, ticks, or spreads from cache or source."""
    logger.info("Executing public DATA market retrieval")
    from app.services.data.access.historical import fetch_market_dataset

    return fetch_market_dataset(request)


def get_tick_data(request: MarketDataRequest) -> MarketDataset:
    """Retrieve tick records specifically; raises if data_kind is not tick."""
    logger.info("Executing public DATA tick retrieval")
    if request.data_kind not in ("tick", "ticks"):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"get_tick_data requires tick data_kind, got '{request.data_kind}'"
                )
            },
            request_id=request.request_id,
        )
    from app.services.data.access.historical import fetch_market_dataset

    return fetch_market_dataset(request)


def get_spread_data(request: MarketDataRequest) -> MarketDataset:
    """Retrieve spread records specifically; raises if data_kind is not spread."""
    logger.info("Executing public DATA spread retrieval")
    if request.data_kind not in ("spread", "spreads"):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"get_spread_data requires spread data_kind, "
                    f"got '{request.data_kind}'"
                )
            },
            request_id=request.request_id,
        )
    from app.services.data.access.historical import fetch_market_dataset

    return fetch_market_dataset(request)


def get_symbol_metadata(request: SymbolMetadataRequest) -> SymbolMetadata:
    """Retrieve static catalog details for a single symbol."""
    logger.info("Executing public DATA symbol metadata retrieval")
    from app.services.data.access.reference import fetch_symbol_metadata

    return fetch_symbol_metadata(request)


def list_symbols(request: SymbolListRequest) -> SymbolPage:
    """List and page all discovered symbol descriptors."""
    logger.info("Executing public DATA symbol listing")
    from app.services.data.access.reference import discover_symbols

    return discover_symbols(request)


def get_data_availability(request: AvailabilityRequest) -> DataAvailability:
    """Inspect local storage ranges, density, gaps, and overlaps."""
    logger.info("Executing public DATA availability query")
    from app.services.data.access.reference import inspect_availability

    return inspect_availability(request)


def get_market_hours(
    request: ScheduleRequest,
    calendar: MarketCalendar,
) -> MarketSchedule:
    """Retrieve weekly trading schedule windows; raises if view is not hours."""
    logger.info("Executing public DATA market-hours query")
    if request.view != "hours":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"get_market_hours requires hours view, got '{request.view}'"
                )
            },
            request_id=request.request_id,
        )
    from app.services.data.access.sessions import get_current_schedule

    return get_current_schedule(request, calendar)


def get_trading_sessions(
    request: ScheduleRequest,
    calendar: MarketCalendar,
) -> MarketSchedule:
    """Retrieve specific session intervals; raises if view is not sessions."""
    logger.info("Executing public DATA trading-session query")
    if request.view != "sessions":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"get_trading_sessions requires sessions view, got '{request.view}'"
                )
            },
            request_id=request.request_id,
        )
    from app.services.data.access.sessions import get_current_schedule

    return get_current_schedule(request, calendar)


def get_historical_volume(request: VolumeRequest) -> VolumeResult:
    """Retrieve aggregated or raw historical trading volume metrics."""
    logger.info("Executing public DATA historical-volume query")
    from app.services.data.access.sessions import fetch_historical_volume

    return fetch_historical_volume(request)


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
]
