"""Deterministic tick-series generation from real market evidence.

Derives a canonical tick ``MarketDataset`` from real bar or real tick evidence
under one of four approved models. Every price originates from an actual OHLC
bound or an actual quote and every tick count from actual tick volume; only the
intra-bar path shape is constructed, and it is fully deterministic.

This is not synthetic generation. ``processing.synthetic.generate_synthetic_dataset``
fabricates prices from a GBM random walk for fixtures and tests only, and its output
must never reach an official simulation run.

Data owns no trading concepts here. The generated stream carries prices, spread, and
intra-bar position only; entry, exit, pending, stop-loss, and take-profit fields are
Strategy-owned and never appear in a Data record.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from random import Random

from app.services.data.contracts.errors import DataError
from app.services.data.contracts.market import (
    DataQualityReport,
    MarketDataset,
    PrecisionPolicy,
    WorkflowContext,
)
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.processing.timeframes import get_timeframe_spec
from app.utils import logger

TICK_MODEL_REAL = "real"
TICK_MODEL_TRADING_BAR = "trading_bar"
TICK_MODEL_OHLC_M1 = "ohlc_m1"
TICK_MODEL_GENERATED = "generated"

TICK_GENERATION_MODELS: tuple[str, ...] = (
    TICK_MODEL_REAL,
    TICK_MODEL_TRADING_BAR,
    TICK_MODEL_OHLC_M1,
    TICK_MODEL_GENERATED,
)

SPREAD_NATIVE = "native_spread"
SPREAD_FIXED = "fixed_spread"
SPREAD_VARIABLE = "variable_spread"

SPREAD_MODELS: tuple[str, ...] = (SPREAD_NATIVE, SPREAD_FIXED, SPREAD_VARIABLE)

GENERATED_TICKS_MIN_PER_BAR = 4

PHASE_OPEN = 1
PHASE_HIGH = 2
PHASE_LOW = 4
PHASE_CLOSE = 8

_WAYPOINTS_PER_BAR = 4


def _error(
    code: str,
    field: str,
    request_id: str | None,
    detail: str | None = None,
) -> DataError:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _error")
    safe_details: dict[str, str] = {"field": field}
    if detail is not None:
        safe_details["reason"] = detail
    return DataError(code, safe_details=safe_details, request_id=request_id)


def _validate_model(model: str, request_id: str | None) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _validate_model")
    if model not in TICK_GENERATION_MODELS:
        raise _error("INVALID_INPUT", "model", request_id, "unsupported tick model")
    return model


def _validate_spread_model(
    spread_model: str,
    fixed_spread_points: Decimal | None,
    min_spread_points: Decimal | None,
    max_spread_points: Decimal | None,
    seed: int | None,
    request_id: str | None,
) -> str:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _validate_spread_model")
    if spread_model not in SPREAD_MODELS:
        raise _error("INVALID_INPUT", "spread_model", request_id, "unsupported model")
    if spread_model == SPREAD_FIXED and (
        fixed_spread_points is None or fixed_spread_points < 0
    ):
        raise _error("INVALID_INPUT", "fixed_spread_points", request_id, "required")
    if spread_model == SPREAD_VARIABLE:
        if min_spread_points is None or max_spread_points is None:
            raise _error("INVALID_INPUT", "min_spread_points", request_id, "required")
        if min_spread_points < 0 or max_spread_points < min_spread_points:
            raise _error("INVALID_INPUT", "max_spread_points", request_id, "invalid")
        if seed is None:
            raise _error("INVALID_INPUT", "seed", request_id, "required for variable")
    return spread_model


def _require_bars(
    dataset: MarketDataset,
    request_id: str | None,
) -> tuple[OHLCVRecord, ...]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _require_bars")
    if dataset.data_kind != "bars":
        raise _error("VALIDATION_FAILED", "data_kind", request_id, "bars required")
    records = tuple(
        record for record in dataset.records if isinstance(record, OHLCVRecord)
    )
    if not records:
        raise _error("VALIDATION_FAILED", "records", request_id, "no bar records")
    ordered = tuple(sorted(records, key=lambda record: record.timestamp))
    return ordered


def _require_ticks(
    dataset: MarketDataset | None,
    request_id: str | None,
) -> tuple[TickRecord, ...]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _require_ticks")
    if dataset is None or dataset.data_kind != "ticks":
        raise _error("VALIDATION_FAILED", "real_tick_dataset", request_id, "required")
    records = tuple(
        record for record in dataset.records if isinstance(record, TickRecord)
    )
    if not records:
        raise _error("VALIDATION_FAILED", "records", request_id, "no tick records")
    return tuple(sorted(records, key=lambda record: record.timestamp))


def _bar_seconds(
    bars: Sequence[OHLCVRecord],
    trading_timeframe: str,
    request_id: str | None,
) -> int:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _bar_seconds")
    if len(bars) > 1:
        deltas = sorted(
            int((bars[index + 1].timestamp - bars[index].timestamp).total_seconds())
            for index in range(len(bars) - 1)
        )
        median = deltas[len(deltas) // 2]
        if median > 0:
            return median
    try:
        spec = get_timeframe_spec(trading_timeframe)
    except DataError as error:
        raise _error(
            "UNSUPPORTED_TIMEFRAME",
            "trading_timeframe",
            request_id,
            "unknown timeframe",
        ) from error
    return int(spec.duration.total_seconds())


def _quantum(price_unit_exponent: int) -> Decimal:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _quantum")
    return Decimal(1).scaleb(-price_unit_exponent)


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _quantize")
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)


def _waypoints(bar: OHLCVRecord) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Execute one private DATA operation.

    A bullish bar visits the low before the high; a bearish bar visits the high
    before the low. The ordering is deterministic and is the evidence a consumer
    needs to resolve same-bar protective-order precedence.
    """
    logger.debug("Running DATA function: _waypoints")
    bullish = bar.close >= bar.open
    first = bar.low if bullish else bar.high
    second = bar.high if bullish else bar.low
    return bar.open, first, second, bar.close


def _waypoint_phases(bar: OHLCVRecord) -> tuple[int, int, int, int]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _waypoint_phases")
    bullish = bar.close >= bar.open
    first = PHASE_LOW if bullish else PHASE_HIGH
    second = PHASE_HIGH if bullish else PHASE_LOW
    return PHASE_OPEN, first, second, PHASE_CLOSE


def _spread_points_for(
    native: Decimal | None,
    spread_model: str,
    fixed_spread_points: Decimal | None,
    min_spread_points: Decimal | None,
    max_spread_points: Decimal | None,
    rng: Random | None,
) -> Decimal:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _spread_points_for")
    if spread_model == SPREAD_NATIVE:
        return max(Decimal(0), native if native is not None else Decimal(0))
    if spread_model == SPREAD_FIXED:
        return max(Decimal(0), fixed_spread_points or Decimal(0))
    low = min_spread_points or Decimal(0)
    high = max_spread_points or Decimal(0)
    if rng is None or high <= low:
        return low
    span = high - low
    draw = Decimal(rng.randrange(0, 1_000_001)) / Decimal(1_000_000)
    return low + (span * draw)


def _four_tick_offsets(bar_seconds: int) -> tuple[int, int, int, int]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _four_tick_offsets")
    bar_ms = max(1, bar_seconds * 1000)
    close_offset = max(0, bar_ms - 1)
    first_inner = max(1, bar_ms // 3)
    second_inner = max(first_inner + 1, (2 * bar_ms) // 3)
    second_inner = min(second_inner, max(first_inner + 1, close_offset - 1))
    return 0, first_inner, second_inner, close_offset


def _interpolate(
    start_value: Decimal,
    end_value: Decimal,
    step: int,
    steps: int,
) -> Decimal:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _interpolate")
    if steps <= 0:
        return end_value
    return start_value + ((end_value - start_value) * Decimal(step) / Decimal(steps))


def _segment_lengths(tick_count: int) -> tuple[int, int, int]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _segment_lengths")
    steps = max(0, tick_count - 1)
    base = steps // 3
    remainder = steps % 3
    first = base + (1 if remainder > 0 else 0)
    second = base + (1 if remainder > 1 else 0)
    return first, second, base


def _generated_price_and_phase(
    bar: OHLCVRecord,
    local_index: int,
    tick_count: int,
) -> tuple[Decimal, int]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _generated_price_and_phase")
    open_value, first_value, second_value, close_value = _waypoints(bar)
    open_phase, first_phase, second_phase, close_phase = _waypoint_phases(bar)
    first_len, second_len, third_len = _segment_lengths(tick_count)
    first_turn = first_len
    second_turn = first_len + second_len

    if local_index <= first_turn:
        price = _interpolate(open_value, first_value, local_index, max(first_len, 1))
    elif local_index <= second_turn:
        price = _interpolate(
            first_value, second_value, local_index - first_turn, max(second_len, 1)
        )
    else:
        price = _interpolate(
            second_value, close_value, local_index - second_turn, max(third_len, 1)
        )

    phase = 0
    if local_index == 0:
        phase |= open_phase
    if local_index == first_turn:
        phase |= first_phase
    if local_index == second_turn:
        phase |= second_phase
    if local_index == tick_count - 1:
        phase |= close_phase
    return price, phase


def _build_record(
    bar: OHLCVRecord,
    timestamp: datetime,
    bid: Decimal,
    spread_points: Decimal,
    point_value: Decimal,
    quantum: Decimal,
    local_index: int,
    phase: int,
) -> TickRecord:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _build_record")
    quantized_bid = _quantize(bid, quantum)
    quantized_ask = _quantize(bid + (spread_points * point_value), quantum)
    return TickRecord(
        timestamp=timestamp,
        source=bar.source,
        source_symbol=bar.source_symbol,
        source_revision=bar.source_revision,
        available_at=max(bar.available_at, timestamp),
        bid=quantized_bid,
        ask=quantized_ask,
        last=quantized_bid,
        price_unit=bar.price_unit,
        source_bar_time=bar.timestamp,
        tick_index_in_bar=local_index,
        bar_phase=phase,
    )


def _four_tick_records(
    bars: Sequence[OHLCVRecord],
    bar_seconds: int,
    point_value: Decimal,
    quantum: Decimal,
    spread_model: str,
    fixed_spread_points: Decimal | None,
    min_spread_points: Decimal | None,
    max_spread_points: Decimal | None,
    rng: Random | None,
) -> tuple[TickRecord, ...]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _four_tick_records")
    offsets = _four_tick_offsets(bar_seconds)
    records: list[TickRecord] = []
    for bar in bars:
        values = _waypoints(bar)
        phases = _waypoint_phases(bar)
        for local_index in range(_WAYPOINTS_PER_BAR):
            spread_points = _spread_points_for(
                bar.spread,
                spread_model,
                fixed_spread_points,
                min_spread_points,
                max_spread_points,
                rng,
            )
            records.append(
                _build_record(
                    bar,
                    bar.timestamp + timedelta(milliseconds=offsets[local_index]),
                    values[local_index],
                    spread_points,
                    point_value,
                    quantum,
                    local_index,
                    phases[local_index],
                )
            )
    return tuple(records)


def _generated_records(
    bars: Sequence[OHLCVRecord],
    bar_seconds: int,
    point_value: Decimal,
    quantum: Decimal,
    spread_model: str,
    fixed_spread_points: Decimal | None,
    min_spread_points: Decimal | None,
    max_spread_points: Decimal | None,
    rng: Random | None,
    max_records: int | None,
    request_id: str | None,
) -> tuple[TickRecord, ...]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _generated_records")
    bar_ms = max(1, bar_seconds * 1000)
    records: list[TickRecord] = []
    for bar in bars:
        tick_count = max(GENERATED_TICKS_MIN_PER_BAR, int(bar.volume))
        if max_records is not None and len(records) + tick_count > max_records:
            raise _error("LIMIT_EXCEEDED", "record_count", request_id, "too long")
        for local_index in range(tick_count):
            price, phase = _generated_price_and_phase(bar, local_index, tick_count)
            spread_points = _spread_points_for(
                bar.spread,
                spread_model,
                fixed_spread_points,
                min_spread_points,
                max_spread_points,
                rng,
            )
            offset_ms = (bar_ms * local_index) // max(tick_count, 1)
            records.append(
                _build_record(
                    bar,
                    bar.timestamp + timedelta(milliseconds=offset_ms),
                    price,
                    spread_points,
                    point_value,
                    quantum,
                    local_index,
                    phase,
                )
            )
    return tuple(records)


def _real_records(
    ticks: Sequence[TickRecord],
    bar_seconds: int,
    quantum: Decimal,
) -> tuple[TickRecord, ...]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _real_records")
    bucket_seconds = max(1, bar_seconds)
    grouped: dict[datetime, list[TickRecord]] = {}
    for tick in ticks:
        epoch = int(tick.timestamp.timestamp())
        floored = datetime.fromtimestamp(
            epoch - (epoch % bucket_seconds),
            tz=UTC,
        )
        grouped.setdefault(floored, []).append(tick)

    records: list[TickRecord] = []
    for bucket in sorted(grouped):
        members = grouped[bucket]
        prices = [
            member.bid if member.bid is not None else member.last for member in members
        ]
        usable = [price for price in prices if price is not None]
        high_price = max(usable) if usable else None
        low_price = min(usable) if usable else None
        for local_index, member in enumerate(members):
            phase = 0
            if local_index == 0:
                phase |= PHASE_OPEN
            if local_index == len(members) - 1:
                phase |= PHASE_CLOSE
            price = prices[local_index]
            if price is not None and price == high_price:
                phase |= PHASE_HIGH
            if price is not None and price == low_price:
                phase |= PHASE_LOW
            records.append(
                member.model_copy(
                    update={
                        "bid": None
                        if member.bid is None
                        else _quantize(member.bid, quantum),
                        "ask": None
                        if member.ask is None
                        else _quantize(member.ask, quantum),
                        "last": None
                        if member.last is None
                        else _quantize(member.last, quantum),
                        "source_bar_time": bucket,
                        "tick_index_in_bar": local_index,
                        "bar_phase": phase,
                    }
                )
            )
    return tuple(records)


def _build_dataset(
    source: MarketDataset,
    records: tuple[TickRecord, ...],
    model: str,
    spread_model: str,
    seed: int | None,
    workflow_context: WorkflowContext,
    precision_policy: PrecisionPolicy,
    request_id: str,
) -> MarketDataset:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _build_dataset")
    generated_at = max(record.available_at for record in records)
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=max(1, min(1_000, len(records))),
        schema_version="v1",
        generated_at=generated_at,
    )
    metadata = dict(source.source_metadata)
    metadata.update(
        {
            "tick_generation_model": model,
            "tick_spread_model": spread_model,
            "tick_generation_seed": "none" if seed is None else str(seed),
            "derived_from_schema": source.schema_id,
        }
    )
    return MarketDataset(
        normalization_version=source.normalization_version,
        data_kind="ticks",
        symbol=source.symbol,
        timeframe=source.timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=generated_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata=metadata,
        license_metadata=source.license_metadata,
        cache_status="not_used",
        workflow_context=workflow_context,
        precision_policy=precision_policy,
        request_id=request_id,
    )


def generate_tick_series(
    dataset: MarketDataset,
    *,
    model: str,
    trading_timeframe: str,
    m1_dataset: MarketDataset | None = None,
    real_tick_dataset: MarketDataset | None = None,
    spread_model: str = SPREAD_NATIVE,
    point_value: Decimal = Decimal("0.00001"),
    price_precision: int = 5,
    fixed_spread_points: Decimal | None = None,
    min_spread_points: Decimal | None = None,
    max_spread_points: Decimal | None = None,
    seed: int | None = None,
    max_records: int | None = None,
    request_id: str | None = None,
) -> MarketDataset:
    """Derive a canonical tick dataset from real bar or tick evidence.

    Prices originate from real OHLC bounds or real quotes and tick counts from real
    tick volume; only the intra-bar path shape is constructed. This is not synthetic
    generation and never fabricates a price.

    Args:
        dataset: Source MarketDataset supplying bars, or signal-timeframe context
          for the real model.
        model: One of TICK_GENERATION_MODELS.
        trading_timeframe: Timeframe key used when bar spacing cannot be inferred.
        m1_dataset: Required M1 bar dataset for the ohlc_m1 model.
        real_tick_dataset: Required real tick dataset for the real model.
        spread_model: One of SPREAD_MODELS.
        point_value: Value of one spread point in price units.
        price_precision: Decimal exponent used to quantize emitted prices.
        fixed_spread_points: Required when spread_model is fixed_spread.
        min_spread_points: Required when spread_model is variable_spread.
        max_spread_points: Required when spread_model is variable_spread.
        seed: Required when spread_model is variable_spread.
        max_records: Optional output ceiling; exceeding it raises LIMIT_EXCEEDED.
        request_id: Optional caller trace identifier.

    Returns:
        A canonical tick MarketDataset ordered by timestamp then intra-bar index.

    Raises:
        DataError: If the model, spread configuration, timeframe, source evidence,
          or output size is invalid.
    """
    logger.info(
        "Generating tick series for symbol %s using model %s",
        dataset.symbol,
        model,
    )
    resolved_request_id = request_id or dataset.request_id
    _validate_model(model, resolved_request_id)
    _validate_spread_model(
        spread_model,
        fixed_spread_points,
        min_spread_points,
        max_spread_points,
        seed,
        resolved_request_id,
    )
    if point_value <= 0 or not point_value.is_finite():
        raise _error("INVALID_INPUT", "point_value", resolved_request_id, "must be > 0")

    quantum = _quantum(price_precision)
    rng = Random(seed) if seed is not None else None

    if model == TICK_MODEL_REAL:
        ticks = _require_ticks(real_tick_dataset, resolved_request_id)
        bar_seconds = _bar_seconds((), trading_timeframe, resolved_request_id)
        records = _real_records(ticks, bar_seconds, quantum)
        source = real_tick_dataset if real_tick_dataset is not None else dataset
    else:
        if model == TICK_MODEL_OHLC_M1:
            if m1_dataset is None:
                raise _error(
                    "VALIDATION_FAILED", "m1_dataset", resolved_request_id, "required"
                )
            bars = _require_bars(m1_dataset, resolved_request_id)
            source = m1_dataset
        else:
            bars = _require_bars(dataset, resolved_request_id)
            source = dataset
        bar_seconds = _bar_seconds(bars, trading_timeframe, resolved_request_id)
        if model == TICK_MODEL_GENERATED:
            records = _generated_records(
                bars,
                bar_seconds,
                point_value,
                quantum,
                spread_model,
                fixed_spread_points,
                min_spread_points,
                max_spread_points,
                rng,
                max_records,
                resolved_request_id,
            )
        else:
            records = _four_tick_records(
                bars,
                bar_seconds,
                point_value,
                quantum,
                spread_model,
                fixed_spread_points,
                min_spread_points,
                max_spread_points,
                rng,
            )

    if not records:
        raise _error("VALIDATION_FAILED", "records", resolved_request_id, "empty")
    if max_records is not None and len(records) > max_records:
        raise _error(
            "LIMIT_EXCEEDED", "record_count", resolved_request_id, "series too long"
        )

    ordered = tuple(
        sorted(
            records,
            key=lambda record: (record.timestamp, record.tick_index_in_bar or 0),
        )
    )
    return _build_dataset(
        source,
        ordered,
        model,
        spread_model,
        seed,
        dataset.workflow_context,
        dataset.precision_policy,
        resolved_request_id,
    )


def _serialize_rows(generated: MarketDataset) -> list[dict[str, object]]:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _serialize_rows")
    return [
        {
            "timestamp": record.timestamp,
            "bid": None if record.bid is None else str(record.bid),
            "ask": None if record.ask is None else str(record.ask),
            "last": None if record.last is None else str(record.last),
            "source_bar_time": record.source_bar_time,
            "tick_index_in_bar": record.tick_index_in_bar,
            "bar_phase": record.bar_phase,
        }
        for record in generated.records
        if isinstance(record, TickRecord)
    ]


def _estimated_output_rows(record: OHLCVRecord) -> int:
    """Execute one private DATA operation."""
    logger.debug("Running DATA function: _estimated_output_rows")
    return max(GENERATED_TICKS_MIN_PER_BAR, int(record.volume))


def _source_chunks(
    dataset: MarketDataset,
    max_output_rows_per_chunk: int,
) -> list[MarketDataset]:
    """Execute one private DATA operation.

    Slices the source dataset so each chunk's estimated generated output stays
    within the ceiling. Sizing uses estimated output rows, not input rows.
    """
    logger.debug("Running DATA function: _source_chunks")
    bars = [record for record in dataset.records if isinstance(record, OHLCVRecord)]
    if not bars:
        return [dataset]

    bounds: list[tuple[int, int]] = []
    start = 0
    running = 0
    for index, record in enumerate(bars):
        estimated = _estimated_output_rows(record)
        if index > start and running + estimated > max_output_rows_per_chunk:
            bounds.append((start, index))
            start = index
            running = 0
        running += estimated
    bounds.append((start, len(bars)))

    chunks: list[MarketDataset] = []
    for lower, upper in bounds:
        piece = tuple(bars[lower:upper])
        chunks.append(
            dataset.model_copy(
                update={
                    "records": piece,
                    "record_count": len(piece),
                    "start": piece[0].timestamp,
                    "end": piece[-1].timestamp,
                }
            )
        )
    return chunks


def generate_tick_series_to_parquet(
    dataset: MarketDataset,
    *,
    path: Path,
    max_output_rows_per_chunk: int = 2_000_000,
    **generation_arguments: object,
) -> Mapping[str, object]:
    """Stream a generated tick series to a bounded Parquet artifact.

    Args:
        dataset: Source MarketDataset supplying bar or context evidence.
        path: Destination Parquet path beneath an approved artifact root.
        max_output_rows_per_chunk: Output-aware chunk ceiling.
        **generation_arguments: Keyword arguments forwarded to generate_tick_series.

    Returns:
        Mapping with the written path, row count, and column names.

    Raises:
        DataError: If generation fails or the destination cannot be written.
    """
    logger.info("Streaming generated tick series to %s", path)
    if max_output_rows_per_chunk <= 0:
        raise _error("INVALID_INPUT", "max_output_rows_per_chunk", dataset.request_id)

    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    chunks = _source_chunks(dataset, max_output_rows_per_chunk)
    writer: pq.ParquetWriter | None = None
    rows_written = 0
    columns: list[str] = []
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        for chunk in chunks:
            generated = generate_tick_series(
                chunk,
                **generation_arguments,  # type: ignore[arg-type]
            )
            frame = pd.DataFrame(_serialize_rows(generated))
            if frame.empty:
                continue
            table = pa.Table.from_pandas(frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(path, table.schema)  # type: ignore[no-untyped-call]
                columns = [str(column) for column in frame.columns]
            writer.write_table(table)  # type: ignore[no-untyped-call]
            rows_written += len(frame)
    except OSError as error:
        raise _error(
            "STORAGE_FAILED", "path", dataset.request_id, "write failed"
        ) from error
    finally:
        if writer is not None:
            writer.close()  # type: ignore[no-untyped-call]
    return {"path": str(path), "rows": rows_written, "columns": columns}


__all__ = [
    "GENERATED_TICKS_MIN_PER_BAR",
    "PHASE_CLOSE",
    "PHASE_HIGH",
    "PHASE_LOW",
    "PHASE_OPEN",
    "SPREAD_MODELS",
    "TICK_GENERATION_MODELS",
    "generate_tick_series",
    "generate_tick_series_to_parquet",
]
