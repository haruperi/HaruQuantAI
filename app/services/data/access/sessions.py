"""Market calendar hours, session schedules, and volume queries."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from app.services.data.access.historical import fetch_market_dataset
from app.services.data.contracts import (
    MarketDataRequest,
    MarketSchedule,
    ScheduleRequest,
    VolumeRecord,
    VolumeRequest,
    VolumeResult,
    VolumeSummary,
)
from app.services.data.contracts.errors import DataError
from app.services.data.sources.registry import get_source_descriptor
from app.utils import Clock, logger, utc_now

VOLUME_RESPONSE_MODES = ("records", "buckets", "summary")


class MarketCalendar(Protocol):
    """Injected authoritative current-session calendar boundary."""

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Return versioned provider/exchange schedule evidence."""
        ...


def get_current_schedule(
    request: ScheduleRequest,
    calendar: MarketCalendar,
    *,
    clock: Clock | None = None,
) -> MarketSchedule:
    """Return current configured hours and normalized UTC sessions.

    Advances cross-midnight windows correctly and rejects historical reconstruction.

    Args:
        request: Schedule details request.
        calendar: Caller-injected authoritative schedule provider.
        clock: Optional injected UTC clock.

    Returns:
        The MarketSchedule details.

    Raises:
        DataError: On missing, invalid, or unavailable schedule evidence.
    """
    logger.info(
        "Getting current schedule for %s on %s (Request: %s)",
        request.symbol,
        request.source_id,
        request.request_id,
    )

    desc = get_source_descriptor(request.source_id)
    if desc.readiness == "disabled":
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"source_id": request.source_id},
            request_id=request.request_id,
        )
    observed_at = utc_now(clock)
    try:
        schedule = calendar.get_schedule(
            source_id=request.source_id,
            symbol=request.symbol,
            timezone=request.timezone,
            observed_at=observed_at,
            request_id=request.request_id,
        )
    except DataError:
        raise
    except Exception as error:
        logger.error("Authoritative market-calendar query failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "market_calendar"},
            request_id=request.request_id,
        ) from error
    if (
        schedule.source_id != request.source_id
        or schedule.symbol != request.symbol
        or schedule.timezone != request.timezone
        or schedule.request_id != request.request_id
        or schedule.observed_at != observed_at
    ):
        raise DataError(
            "STALE_EVIDENCE",
            safe_details={"operation": "market_calendar"},
            request_id=request.request_id,
        )
    return schedule


def _compute_volume_summary(
    request: VolumeRequest,
    records: tuple[VolumeRecord, ...],
    volume_unit: str,
    provenance: dict[str, str],
) -> VolumeResult:
    """Helper to compute VolumeSummary and construct VolumeResult."""
    logger.debug("Running DATA function: _compute_volume_summary")
    total = Decimal(str(sum(rec.volume for rec in records)))
    average = Decimal(str(total / len(records)))
    minimum = Decimal(str(min(rec.volume for rec in records)))
    maximum = Decimal(str(max(rec.volume for rec in records)))

    summary = VolumeSummary(
        total=total,
        average=average,
        minimum=minimum,
        maximum=maximum,
        record_count=len(records),
    )
    return VolumeResult(
        source_id=request.source_id,
        symbol=request.symbol,
        mode="summary",
        volume_kind="trade",
        volume_unit=volume_unit,
        records=(),
        summary=summary,
        provenance=provenance,
        truncated=False,
        request_id=request.request_id,
    )


def _compute_volume_buckets(
    request: VolumeRequest,
    records: tuple[VolumeRecord, ...],
    volume_unit: str,
    provenance: dict[str, str],
) -> VolumeResult:
    """Helper to group volume records into buckets."""
    logger.debug("Running DATA function: _compute_volume_buckets")
    if not request.bucket_seconds:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"message": "Bucket mode requires positive bucket_seconds"},
            request_id=request.request_id,
        )

    bucket_duration = timedelta(seconds=request.bucket_seconds)
    buckets_dict: dict[datetime, Decimal] = {}

    for rec in records:
        offset = (rec.timestamp - request.start).total_seconds()
        bucket_idx = int(offset // request.bucket_seconds)
        bucket_start = request.start + bucket_idx * bucket_duration
        buckets_dict[bucket_start] = (
            buckets_dict.get(bucket_start, Decimal(0)) + rec.volume
        )

    grouped_records = tuple(
        VolumeRecord(timestamp=ts, volume=vol)
        for ts, vol in sorted(buckets_dict.items())
    )
    truncated = len(grouped_records) >= request.limit

    return VolumeResult(
        source_id=request.source_id,
        symbol=request.symbol,
        mode="buckets",
        volume_kind="trade",
        volume_unit=volume_unit,
        records=grouped_records[: request.limit],
        summary=None,
        provenance=provenance,
        truncated=truncated,
        request_id=request.request_id,
    )


def fetch_historical_volume(request: VolumeRequest) -> VolumeResult:
    """Return bounded source-native or derived volume as records, buckets, or summary.

    Args:
        request: Historical volume request.

    Returns:
        The VolumeResult contract.

    Raises:
        DataError: On invalid input, limits exceeded, or quality failures.
    """
    logger.info(
        "Fetching historical volume for %s on %s (Request: %s)",
        request.symbol,
        request.source_id,
        request.request_id,
    )

    if request.mode not in VOLUME_RESPONSE_MODES:
        raise DataError(
            "INVALID_INPUT",
            safe_details={
                "message": f"Response mode {request.mode} not supported",
                "supported": ", ".join(VOLUME_RESPONSE_MODES),
            },
            request_id=request.request_id,
        )

    # Delegate fetch of the raw market bars to construct volume
    data_req = MarketDataRequest(
        source_id=request.source_id,
        symbol=request.symbol,
        data_kind="bars",
        timeframe="M1",
        start=request.start,
        end=request.end,
        limit=request.limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=request.request_id,
    )
    dataset = fetch_market_dataset(data_req)

    # Filter and extract OHLCVRecord elements
    from app.services.data.contracts.records import OHLCVRecord

    ohlcv_records = [r for r in dataset.records if isinstance(r, OHLCVRecord)]

    if not ohlcv_records:
        raise DataError(
            "EMPTY_RESULT",
            safe_details={
                "message": "No historical volume records found in requested range"
            },
            request_id=request.request_id,
        )

    provenance = dict(dataset.source_metadata)
    volume_unit = ohlcv_records[0].volume_unit
    records = tuple(
        VolumeRecord(timestamp=rec.timestamp, volume=rec.volume)
        for rec in ohlcv_records
    )

    if request.mode == "summary":
        return _compute_volume_summary(request, records, volume_unit, provenance)

    if request.mode == "buckets":
        return _compute_volume_buckets(request, records, volume_unit, provenance)

    truncated = len(records) >= request.limit
    return VolumeResult(
        source_id=request.source_id,
        symbol=request.symbol,
        mode="records",
        volume_kind="trade",
        volume_unit=volume_unit,
        records=records[: request.limit],
        summary=None,
        provenance=provenance,
        truncated=truncated,
        request_id=request.request_id,
    )
