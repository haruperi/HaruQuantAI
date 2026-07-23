"""Aggregation of canonical ticks into OHLCV bars.

Consumes ticks and produces bars, which is the opposite direction from
``tick_derivation.generate_tick_series``. The two are easy to confuse by name;
they share no code and no purpose.

Tick ordering is a precondition, not something this module repairs: disordered input
raises rather than being sorted, because silently reordering ticks would mask a source
defect that the caller needs to see.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import DataQualityReport, MarketDataset
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.time_sessions.timeframes import (
    get_timeframe_spec,
)
from app.utils import logger


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
        closing_tick = values[-1][0]
        closing_spread = (
            closing_tick.ask - closing_tick.bid
            if closing_tick.ask is not None and closing_tick.bid is not None
            else None
        )
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
                spread=closing_spread,
                spread_unit=price_unit if closing_spread is not None else None,
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


def aggregate_ticks_to_bars(
    dataset: MarketDataset,
    target_timeframe: str,
    price_policy: str = "last",
) -> MarketDataset:
    """Aggregate tick records into custom-timeframe OHLCV bars."""
    logger.info("Executing public DATA tick aggregation")
    return aggregate_ticks(dataset, target_timeframe, price_policy)


__all__ = [
    "aggregate_ticks",
    "aggregate_ticks_to_bars",
]
