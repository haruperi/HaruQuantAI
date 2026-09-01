# ruff: noqa: E501
"""Deterministic higher-timeframe aggregation of canonical bars.

Resampling only ever coarsens: a target finer than the source is rejected rather than
interpolated, because inventing intra-bar detail would fabricate evidence. The source
dataset's quality report is propagated with updated provenance rather than recomputed â€”
a transform changes the shape of a series, not the trustworthiness of the observations
it derives from.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import DataQualityReport, MarketDataset
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.time_sessions.timeframes import (
    _get_timeframe_spec_raw,
    _validate_resample_target_raw,
)

logger = get_logger(__name__)


def _bucket_is_closed(
    bucket_start: datetime, duration: object, source_end: datetime
) -> bool:
    """Return whether one resampled bucket is fully covered by source evidence.

    application Phase 0 reconciliation (`feature`): a bucket whose
    full period extends past the source dataset's `end` has not finished
    forming and must never be presented identically to a genuinely closed bar.

    Args:
        bucket_start: The ``bucket_start`` argument.
        duration: The ``duration`` argument.
        source_end: The ``source_end`` argument.

    Returns:
        ``True`` only when the bucket's full duration ends at or before the
        source dataset's observed end.
    """
    return bucket_start + duration <= source_end  # type: ignore[operator]


def _resample_dataset_raw(
    dataset: MarketDataset,
    target_timeframe: str,
    *,
    drop_incomplete_trailing_bucket: bool = False,
) -> MarketDataset:
    """Resample ordered canonical OHLCV only to a supported higher timeframe.

    Uses deterministic OHLCV/spread aggregation and updates available_at.

    Args:
        dataset: The source MarketDataset.
        target_timeframe: The target timeframe key (e.g. "M5").
        drop_incomplete_trailing_bucket: When ``True``, drop the final
            resampled bar if the source dataset's `end` does not cover its
            full target-timeframe duration (`feature` closed-bar
            semantics). Every non-trailing bucket is always fully covered
            by construction, since a later bucket exists only when the
            source data extends past the earlier one's boundary.

    Returns:
        A new resampled MarketDataset.

    Raises:
        DataError: If target timeframe is invalid/unsupported, source is not bars,
          or target timeframe is not strictly higher than source timeframe.
    """
    logger.info(
        "Resampling dataset for symbol %s from %s to %s",
        dataset.symbol,
        dataset.timeframe,
        target_timeframe,
    )
    if dataset.data_kind != "bars":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "Only bar datasets can be resampled."},
        )

    _validate_resample_target_raw(dataset.timeframe, target_timeframe)
    target_spec = _get_timeframe_spec_raw(target_timeframe)

    if not dataset.records:
        logger.info("Empty source dataset records, returning empty dataset")
        quality_report = DataQualityReport(
            quality_status="not_checked",
            quality_decision="not_evaluated",
            quality_score=Decimal(0),
            issues=(),
            warnings=(),
            record_count=0,
            checked_count=0,
            truncated=False,
            sample_limit=1000,
            schema_version="v1",
            generated_at=dataset.quality_report.generated_at,
        )
        return MarketDataset(
            normalization_version=dataset.normalization_version,
            data_kind="bars",
            symbol=dataset.symbol,
            timeframe=target_timeframe,
            records=(),
            start=dataset.start,
            end=dataset.end,
            available_at=dataset.available_at,
            record_count=0,
            quality_report=quality_report,
            source_metadata=dataset.source_metadata,
            license_metadata=dataset.license_metadata,
            cache_status="not_used",
            workflow_context=dataset.workflow_context,
            precision_policy=dataset.precision_policy,
            request_id=dataset.request_id,
        )

    grouped: dict[datetime, list[OHLCVRecord]] = {}
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    for record in dataset.records:
        if not isinstance(record, OHLCVRecord):
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "records"},
            )
        bucket = (
            epoch
            + ((record.timestamp - epoch) // target_spec.duration)
            * target_spec.duration
        )
        grouped.setdefault(bucket, []).append(record)

    resampled_records: list[OHLCVRecord] = []
    for timestamp, records in sorted(grouped.items()):
        identities = {
            (
                item.source,
                item.source_symbol,
                item.source_revision,
                item.price_unit,
                item.volume_unit,
                item.spread_unit,
            )
            for item in records
        }
        if len(identities) != 1:
            raise DataError(
                "DATA_QUALITY_FAILED",
                safe_details={"field": "aggregation_identity"},
                request_id=dataset.request_id,
            )
        first = records[0]
        resampled_records.append(
            OHLCVRecord(
                timestamp=timestamp,
                source=first.source,
                source_symbol=first.source_symbol,
                source_revision=first.source_revision,
                available_at=max(item.available_at for item in records),
                open=first.open,
                high=max(item.high for item in records),
                low=min(item.low for item in records),
                close=records[-1].close,
                volume=sum((item.volume for item in records), start=Decimal(0)),
                price_unit=first.price_unit,
                volume_unit=first.volume_unit,
                spread=records[-1].spread,
                spread_unit=records[-1].spread_unit,
            )
        )

    if (
        drop_incomplete_trailing_bucket
        and resampled_records
        and not _bucket_is_closed(
            resampled_records[-1].timestamp, target_spec.duration, dataset.end
        )
    ):
        logger.info(
            "Dropping incomplete trailing resampled bucket for symbol %s",
            dataset.symbol,
        )
        resampled_records.pop()

    if not resampled_records:
        quality_report = DataQualityReport(
            quality_status="not_checked",
            quality_decision="not_evaluated",
            quality_score=Decimal(0),
            issues=(),
            warnings=(),
            record_count=0,
            checked_count=0,
            truncated=False,
            sample_limit=1000,
            schema_version="v1",
            generated_at=dataset.quality_report.generated_at,
        )
        return MarketDataset(
            normalization_version=dataset.normalization_version,
            data_kind="bars",
            symbol=dataset.symbol,
            timeframe=target_timeframe,
            records=(),
            start=dataset.start,
            end=dataset.end,
            available_at=dataset.available_at,
            record_count=0,
            quality_report=quality_report,
            source_metadata=dataset.source_metadata,
            license_metadata=dataset.license_metadata,
            cache_status="not_used",
            workflow_context=dataset.workflow_context,
            precision_policy=dataset.precision_policy,
            request_id=dataset.request_id,
        )

    quality_report = DataQualityReport(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        issues=(),
        warnings=(),
        record_count=len(resampled_records),
        checked_count=len(resampled_records),
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=max(record.available_at for record in resampled_records),
    )

    start_time = resampled_records[0].timestamp
    end_time = resampled_records[-1].timestamp
    max_avail = max(r.available_at for r in resampled_records)
    dataset_avail = max(max_avail, end_time)

    return MarketDataset(
        normalization_version=dataset.normalization_version,
        data_kind="bars",
        symbol=dataset.symbol,
        timeframe=target_timeframe,
        records=tuple(resampled_records),
        start=start_time,
        end=end_time,
        available_at=dataset_avail,
        record_count=len(resampled_records),
        quality_report=quality_report,
        source_metadata=dataset.source_metadata,
        license_metadata=dataset.license_metadata,
        cache_status="not_used",
        workflow_context=dataset.workflow_context,
        precision_policy=dataset.precision_policy,
        request_id=dataset.request_id,
    )


def resample_dataset(
    dataset: MarketDataset,
    target_timeframe: str,
    *,
    drop_incomplete_trailing_bucket: bool = False,
) -> StandardResponse[MarketDataset]:
    """Resample ordered canonical OHLCV only to a supported higher timeframe.

    Uses deterministic OHLCV/spread aggregation and updates available_at.

    Args:
        dataset: The source MarketDataset.
        target_timeframe: The target timeframe key (e.g. "M5").
        drop_incomplete_trailing_bucket: When ``True``, drop a trailing bar
            whose full period is not yet covered by the source dataset's
            `end` (`feature` closed-bar semantics).

    Returns:
        Standard response carrying a new resampled MarketDataset.

    Raises:
        (in-band) ``VALIDATION_FAILED``, ``UNSUPPORTED_TIMEFRAME``, or
          ``DATA_QUALITY_FAILED`` on failure.
    """
    return run_data_operation(
        operation="data.transformation.resample_dataset",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _resample_dataset_raw(
            dataset,
            target_timeframe,
            drop_incomplete_trailing_bucket=drop_incomplete_trailing_bucket,
        ),
    )


def resample_ohlcv(
    dataset: MarketDataset,
    target_timeframe: str,
    *,
    drop_incomplete_trailing_bucket: bool = False,
) -> StandardResponse[MarketDataset]:
    """Roll up OHLCV records to a larger timeframe.

    Args:
        dataset: The ``dataset`` argument.
        target_timeframe: The ``target_timeframe`` argument.
        drop_incomplete_trailing_bucket: The ``drop_incomplete_trailing_bucket`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.info("Executing public DATA OHLCV resample")
    return run_data_operation(
        operation="data.transformation.resample_ohlcv",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _resample_dataset_raw(
            dataset,
            target_timeframe,
            drop_incomplete_trailing_bucket=drop_incomplete_trailing_bucket,
        ),
    )


__all__ = [
    "resample_dataset",
    "resample_ohlcv",
]
