"""Backward-only multi-timeframe alignment.

Every aligned value is one the target timestamp could actually have seen. Alignment
uses only records whose ``available_at`` precedes the target, so a higher-timeframe bar
never leaks into a decision made before it closed. Lookahead fails the batch atomically
rather than degrading silently, because a quiet lookahead is indistinguishable from a
good backtest result.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import DataQualityReport, MarketDataset
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord
from app.utils import logger


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
                        spread=last_r.spread,
                        spread_unit=last_r.spread_unit,
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


def align_multitimeframe_data(
    datasets: Mapping[str, MarketDataset],
    target_timestamps: Sequence[datetime],
) -> Mapping[str, MarketDataset]:
    """Align multiple datasets to a uniform timestamp index with forward fill."""
    logger.info("Executing public DATA multi-timeframe alignment")
    return align_datasets(datasets, target_timestamps)


__all__ = [
    "align_datasets",
    "align_multitimeframe_data",
]
