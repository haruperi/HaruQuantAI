"""Deterministic market-data transformations for the Data domain."""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal

from app.services.data.contracts.errors import DataError
from app.services.data.contracts.market import DataQualityReport, MarketDataset
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord
from app.services.data.processing.timeframes import (
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


def _validate_alignment_target(target: Sequence[datetime]) -> None:
    """Validate target sequence formatting and ordering."""
    logger.debug("Running DATA function: _validate_alignment_target")
    if not target:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "Target sequence cannot be empty."},
        )

    for i, t in enumerate(target):
        if t.tzinfo is None or t.utcoffset() is None:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"message": f"Target timestamp {t} must be UTC-aware."},
            )
        if i > 0 and t < target[i - 1]:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={
                    "message": "Target sequence must be chronologically ordered."
                },
            )


def align_datasets(
    datasets: Mapping[str, MarketDataset], target: Sequence[datetime]
) -> Mapping[str, MarketDataset]:
    """Backward-align multiple datasets using only values available by target.

    Preserves source availability metadata and fails atomically on lookahead.

    Args:
        datasets: Map of dataset keys to MarketDataset.
        target: Ordered sequence of aware UTC target datetimes.

    Returns:
        Map of dataset keys to backward-aligned MarketDatasets.

    Raises:
        DataError: If validation fails or lookahead/empty values are found.
    """
    logger.info("Aligning %d datasets to target sequence", len(datasets))
    if not datasets:
        return {}

    _validate_alignment_target(target)

    aligned_datasets = {}
    for name, ds in datasets.items():
        aligned_records: list[OHLCVRecord | TickRecord | SpreadRecord] = []
        for t in target:
            # Find last record available at/before t
            valid = [r for r in ds.records if r.timestamp <= t and r.available_at <= t]
            if not valid:
                raise DataError(
                    "VALIDATION_FAILED",
                    safe_details={
                        "message": (
                            f"No record available for dataset '{name}' "
                            f"at target time {t}."
                        )
                    },
                )

            last_r = valid[-1]

            # Construct aligned record at timestamp t preserving original properties
            if isinstance(last_r, OHLCVRecord):
                aligned_records.append(
                    OHLCVRecord(
                        timestamp=t,
                        source=last_r.source,
                        source_symbol=last_r.source_symbol,
                        source_revision=last_r.source_revision,
                        available_at=t,
                        open=last_r.open,
                        high=last_r.high,
                        low=last_r.low,
                        close=last_r.close,
                        volume=last_r.volume,
                        price_unit=last_r.price_unit,
                        volume_unit=last_r.volume_unit,
                    )
                )
            elif isinstance(last_r, TickRecord):
                aligned_records.append(
                    TickRecord(
                        timestamp=t,
                        source=last_r.source,
                        source_symbol=last_r.source_symbol,
                        source_revision=last_r.source_revision,
                        available_at=t,
                        bid=last_r.bid,
                        ask=last_r.ask,
                        last=last_r.last,
                        volume=last_r.volume,
                        price_unit=last_r.price_unit,
                        volume_unit=last_r.volume_unit,
                    )
                )
            elif isinstance(last_r, SpreadRecord):
                aligned_records.append(
                    SpreadRecord(
                        timestamp=t,
                        source=last_r.source,
                        source_symbol=last_r.source_symbol,
                        source_revision=last_r.source_revision,
                        available_at=t,
                        spread=last_r.spread,
                        unit=last_r.unit,
                        scale=last_r.scale,
                    )
                )
            else:
                raise DataError(
                    "VALIDATION_FAILED",
                    safe_details={
                        "message": ("Expected known record type for aligned record.")
                    },
                )

        quality_report = DataQualityReport(
            quality_status="passed",
            quality_score=Decimal(1),
            issues=(),
            warnings=(),
            record_count=len(aligned_records),
            checked_count=len(aligned_records),
            truncated=False,
            sample_limit=1000,
            schema_version="v1",
            generated_at=max(record.available_at for record in aligned_records),
        )

        max_avail = max(r.available_at for r in aligned_records)
        dataset_avail = max(max_avail, target[-1])

        aligned_datasets[name] = MarketDataset(
            normalization_version=ds.normalization_version,
            data_kind=ds.data_kind,
            symbol=ds.symbol,
            timeframe=ds.timeframe,
            records=tuple(aligned_records),
            start=target[0],
            end=target[-1],
            available_at=dataset_avail,
            record_count=len(aligned_records),
            quality_report=quality_report,
            source_metadata=ds.source_metadata,
            license_metadata=ds.license_metadata,
            cache_status="not_used",
            workflow_context=ds.workflow_context,
            precision_policy=ds.precision_policy,
            request_id=ds.request_id,
        )

    return aligned_datasets


def _resolve_price(r: TickRecord, policy: str) -> Decimal | None:
    """Resolve price for a tick based on spread policy."""
    logger.debug("Running DATA function: _resolve_price")
    if policy == "bid":
        return r.bid
    if policy == "ask":
        return r.ask
    if policy == "last":
        return r.last
    if policy == "mid" and r.bid is not None and r.ask is not None:
        return (r.bid + r.ask) / Decimal(2)
    return None


def _validate_units(records: Sequence[TickRecord]) -> tuple[str, str]:
    """Validate tick records are homogeneous in units."""
    logger.debug("Running DATA function: _validate_units")
    price_units = {r.price_unit for r in records if r.price_unit}
    if len(price_units) > 1:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": ("Ticks have ambiguous or mismatched price units.")
            },
        )
    if len(price_units) != 1:
        raise DataError("MISSING_ASSET_METADATA", safe_details={"field": "price_unit"})
    price_unit = next(iter(price_units))

    volume_units = {r.volume_unit for r in records if r.volume_unit}
    if len(volume_units) > 1:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": ("Ticks have ambiguous or mismatched volume units.")
            },
        )
    if len(volume_units) != 1 or any(record.volume is None for record in records):
        raise DataError(
            "MISSING_ASSET_METADATA",
            safe_details={"field": "volume_unit"},
        )
    volume_unit = next(iter(volume_units))

    return price_unit, volume_unit


def aggregate_ticks(
    dataset: MarketDataset, timeframe: str, spread_policy: str
) -> MarketDataset:
    """Aggregate sorted canonical ticks into OHLCV bars.

    Rejects disorder or ambiguous spread/price units.

    Args:
        dataset: The Tick MarketDataset.
        timeframe: The target timeframe key (e.g. "M1").
        spread_policy: Price selection policy ("bid", "ask", "mid", "last").

    Returns:
        A new Bar MarketDataset.

    Raises:
        DataError: If validation fails.
    """
    logger.info(
        "Aggregating ticks for %s to timeframe %s with policy %s",
        dataset.symbol,
        timeframe,
        spread_policy,
    )
    if dataset.data_kind != "ticks":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "Only tick datasets can be aggregated."},
        )

    target_spec = get_timeframe_spec(timeframe)
    if spread_policy not in ("bid", "ask", "mid", "last"):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": f"Unsupported spread policy '{spread_policy}'."},
        )

    if not dataset.records:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": "Tick records list cannot be empty for aggregation."
            },
        )

    # Cast to TickRecords and validate
    tick_records = []
    for r in dataset.records:
        if not isinstance(r, TickRecord):
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"message": "Expected TickRecord in tick dataset."},
            )
        tick_records.append(r)

    price_unit, volume_unit = _validate_units(tick_records)

    grouped: dict[datetime, list[tuple[TickRecord, Decimal]]] = {}
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    for tick in tick_records:
        price = _resolve_price(tick, spread_policy)
        if price is None:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "price"},
            )
        bucket = (
            epoch
            + ((tick.timestamp - epoch) // target_spec.duration) * target_spec.duration
        )
        grouped.setdefault(bucket, []).append((tick, price))

    bars: list[OHLCVRecord] = []
    for timestamp, values in sorted(grouped.items()):
        identities = {
            (tick.source, tick.source_symbol, tick.source_revision)
            for tick, _ in values
        }
        if len(identities) != 1:
            raise DataError(
                "DATA_QUALITY_FAILED",
                safe_details={"field": "aggregation_identity"},
                request_id=dataset.request_id,
            )
        prices = tuple(price for _, price in values)
        first_tick = values[0][0]
        bars.append(
            OHLCVRecord(
                timestamp=timestamp,
                source=first_tick.source,
                source_symbol=first_tick.source_symbol,
                source_revision=first_tick.source_revision,
                available_at=max(tick.available_at for tick, _ in values),
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
                volume=sum(
                    (tick.volume for tick, _ in values if tick.volume is not None),
                    start=Decimal(0),
                ),
                price_unit=price_unit,
                volume_unit=volume_unit,
            )
        )

    quality_report = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        issues=(),
        warnings=(),
        record_count=len(bars),
        checked_count=len(bars),
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=max(record.available_at for record in bars),
    )

    start_time = bars[0].timestamp
    end_time = bars[-1].timestamp
    max_avail = max(r.available_at for r in bars)
    dataset_avail = max(max_avail, end_time)

    return MarketDataset(
        normalization_version=dataset.normalization_version,
        data_kind="bars",
        symbol=dataset.symbol,
        timeframe=timeframe,
        records=tuple(bars),
        start=start_time,
        end=end_time,
        available_at=dataset_avail,
        record_count=len(bars),
        quality_report=quality_report,
        source_metadata=dataset.source_metadata,
        license_metadata=dataset.license_metadata,
        cache_status="not_used",
        workflow_context=dataset.workflow_context,
        precision_policy=dataset.precision_policy,
        request_id=dataset.request_id,
    )
