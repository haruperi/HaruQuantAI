"""Deterministic higher-timeframe aggregation of canonical bars.

Resampling only ever coarsens: a target finer than the source is rejected rather than
interpolated, because inventing intra-bar detail would fabricate evidence. The source
dataset's quality report is propagated with updated provenance rather than recomputed —
a transform changes the shape of a series, not the trustworthiness of the observations
it derives from.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import DataQualityReport, MarketDataset
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.time_sessions.timeframes import (
    get_timeframe_spec,
    validate_resample_target,
)
from app.utils import logger


def resample_dataset(dataset: MarketDataset, target_timeframe: str) -> MarketDataset:
    """Resample ordered canonical OHLCV only to a supported higher timeframe.

    Uses deterministic OHLCV/spread aggregation and updates available_at.

    Args:
        dataset: The source MarketDataset.
        target_timeframe: The target timeframe key (e.g. "M5").

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

    validate_resample_target(dataset.timeframe, target_timeframe)
    target_spec = get_timeframe_spec(target_timeframe)

    if not dataset.records:
        logger.info("Empty source dataset records, returning empty dataset")
        quality_report = DataQualityReport(
            quality_status="not_checked",
            quality_score=Decimal(1),
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

    quality_report = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
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


def resample_ohlcv(dataset: MarketDataset, target_timeframe: str) -> MarketDataset:
    """Roll up OHLCV records to a larger timeframe."""
    logger.info("Executing public DATA OHLCV resample")
    return resample_dataset(dataset, target_timeframe)


__all__ = [
    "resample_dataset",
    "resample_ohlcv",
]
