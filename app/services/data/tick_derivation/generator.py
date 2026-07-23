"""Derive deterministic tick series from real market evidence.

Every emitted price originates from a real quote or an observed OHLC bound. Only the
bounded intra-bar traversal is derived; this module never fabricates market evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from random import Random
from typing import NamedTuple, cast

import numpy as np
from numpy.typing import NDArray

from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import (
    DataQualityReport,
    MarketDataset,
    PrecisionPolicy,
    WorkflowContext,
)
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.tick_derivation._kernel import (
    generate_four_tick_arrays,
    generate_volume_tick_arrays,
)
from app.services.data.time_sessions.timeframes import get_timeframe_spec
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
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_INT64_MAX = np.iinfo(np.int64).max
_KERNEL_MIN_RECORDS = 10_000
_MAX_INTERNAL_PRECISION_DIFFERENCE = 18

Int64Array = NDArray[np.int64]
Int8Array = NDArray[np.int8]


class _KernelColumns(NamedTuple):
    """Validated fixed-point output columns from a compiled kernel."""

    timestamps_us: Int64Array
    bids: Int64Array
    asks: Int64Array
    local_indices: Int64Array
    phases: Int8Array
    bar_indices: Int64Array


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
    return Decimal(1).scaleb(-price_unit_exponent)


def _quantize_tick(value: Decimal, quantum: Decimal) -> Decimal:
    """Execute one private DATA operation."""
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)


def _waypoints(bar: OHLCVRecord) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Execute one private DATA operation.

    A bullish bar visits the low before the high; a bearish bar visits the high
    before the low. The ordering is deterministic and is the evidence a consumer
    needs to resolve same-bar protective-order precedence.
    """
    bullish = bar.close >= bar.open
    first = bar.low if bullish else bar.high
    second = bar.high if bullish else bar.low
    return bar.open, first, second, bar.close


def _waypoint_phases(bar: OHLCVRecord) -> tuple[int, int, int, int]:
    """Execute one private DATA operation."""
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
    bar_ms = max(1, bar_seconds * 1000)
    close_offset = max(0, (bar_seconds - 1) * 1000)
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
    if steps <= 0:
        return end_value
    return start_value + ((end_value - start_value) * Decimal(step) / Decimal(steps))


def _segment_lengths(tick_count: int) -> tuple[int, int, int]:
    """Execute one private DATA operation."""
    steps = max(0, tick_count - 1)
    base = steps // 3
    remainder = steps % 3
    first = base + (1 if remainder > 0 else 0)
    second = base + (1 if remainder > 1 else 0)
    return first, second, base


def _interpolated_price_and_phase(
    values: tuple[Decimal, Decimal, Decimal, Decimal],
    phases: tuple[int, int, int, int],
    lengths: tuple[int, int, int],
    local_index: int,
    tick_count: int,
) -> tuple[Decimal, int]:
    """Interpolate one tick from precomputed bar traversal state."""
    open_value, first_value, second_value, close_value = values
    open_phase, first_phase, second_phase, close_phase = phases
    first_len, second_len, third_len = lengths
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


def _epoch_microseconds(value: datetime) -> int:
    """Return exact UTC microseconds since the Unix epoch.

    Args:
        value: A timezone-aware UTC timestamp.

    Returns:
        Exact signed microseconds since the Unix epoch.
    """
    delta = value - _EPOCH
    return ((delta.days * 86_400 + delta.seconds) * 1_000_000) + delta.microseconds


def _scaled_integer(value: Decimal, quantum: Decimal) -> int | None:
    """Convert an exactly aligned Decimal value to a safe fixed-point integer.

    Args:
        value: Decimal value to convert.
        quantum: Smallest emitted price unit.

    Returns:
        A signed 64-bit compatible integer, or None when conversion is lossy or
        outside the compiled kernel's safe range.
    """
    if not value.is_finite():
        return None
    scaled = value / quantum
    integral = scaled.to_integral_value()
    if scaled != integral:
        return None
    converted = int(integral)
    if not -_INT64_MAX <= converted <= _INT64_MAX:
        return None
    return converted


def _decimal_places(value: Decimal) -> int:
    """Return the finite Decimal's non-negative fractional digit count."""
    exponent = int(value.as_tuple().exponent)
    return max(0, -exponent)


def _spread_increment(
    bar: OHLCVRecord,
    spread_model: str,
    fixed_spread_points: Decimal | None,
    point_value: Decimal,
) -> Decimal:
    """Return one bar's exact non-variable spread increment in price units."""
    spread_points = (
        max(Decimal(0), bar.spread or Decimal(0))
        if spread_model == SPREAD_NATIVE
        else max(Decimal(0), fixed_spread_points or Decimal(0))
    )
    return spread_points * point_value


def _tick_counts(
    bars: Sequence[OHLCVRecord],
    model: str,
    max_records: int | None,
    request_id: str | None,
) -> tuple[int, ...]:
    """Precompute output counts and reject a configured limit before allocation.

    Args:
        bars: Ordered canonical source bars.
        model: Selected tick derivation model.
        max_records: Optional public output ceiling.
        request_id: Caller trace identifier.

    Returns:
        Per-bar output record counts.

    Raises:
        DataError: If the total exceeds max_records.
    """
    if model == TICK_MODEL_GENERATED:
        counts = tuple(
            max(GENERATED_TICKS_MIN_PER_BAR, int(bar.volume)) for bar in bars
        )
    else:
        counts = (_WAYPOINTS_PER_BAR,) * len(bars)
    total = sum(counts)
    if max_records is not None and total > max_records:
        raise _error("LIMIT_EXCEEDED", "record_count", request_id, "series too long")
    return counts


def _kernel_bar_data(
    bar: OHLCVRecord,
    count: int,
    point_value: Decimal,
    quantum: Decimal,
    spread_model: str,
    fixed_spread_points: Decimal | None,
    output_divisor: int,
) -> tuple[tuple[int, ...], tuple[int, ...], int, int] | None:
    """Convert one source bar into safe, exact fixed-point kernel inputs.

    Args:
        bar: Canonical source bar.
        count: Preflighted output count for the bar.
        point_value: Price value represented by one spread point.
        quantum: Smallest emitted price unit.
        spread_model: Selected non-variable spread model.
        fixed_spread_points: Fixed spread value when configured.
        output_divisor: Internal fixed-point units per output price quantum.

    Returns:
        Waypoints, phases, epoch microseconds, and spread increment, or None when
        exact fixed-point execution is unsafe.
    """
    scaled_values = tuple(_scaled_integer(value, quantum) for value in _waypoints(bar))
    if any(value is None for value in scaled_values):
        return None
    integer_values = tuple(int(value) for value in scaled_values if value is not None)
    spread_ticks = _scaled_integer(
        _spread_increment(bar, spread_model, fixed_spread_points, point_value),
        quantum,
    )
    if spread_ticks is None:
        return None
    maximum_delta = max(integer_values) - min(integer_values)
    start_us = _epoch_microseconds(bar.timestamp)
    maximum_steps = max(1, count - 1)
    unsafe = (
        min(integer_values) < -_INT64_MAX + spread_ticks
        or max(integer_values) > _INT64_MAX - spread_ticks
        or output_divisor * maximum_steps > _INT64_MAX
        or (maximum_delta + output_divisor) * maximum_steps > _INT64_MAX
        or not -_INT64_MAX <= start_us <= _INT64_MAX
    )
    if unsafe:
        return None
    return integer_values, _waypoint_phases(bar), start_us, spread_ticks


def _try_kernel_columns(
    bars: Sequence[OHLCVRecord],
    model: str,
    counts: tuple[int, ...],
    bar_seconds: int,
    point_value: Decimal,
    quantum: Decimal,
    spread_model: str,
    fixed_spread_points: Decimal | None,
) -> _KernelColumns | None:
    """Generate fixed-point columns when every input is losslessly eligible.

    Args:
        bars: Ordered canonical source bars.
        model: Selected bar-derived generation model.
        counts: Preflighted output counts for each bar.
        bar_seconds: Inferred source-bar duration in seconds.
        point_value: Price value represented by one spread point.
        quantum: Smallest emitted price unit.
        spread_model: Selected spread model.
        fixed_spread_points: Fixed spread value when configured.

    Returns:
        Validated compiled columns, or None when the exact Decimal path is needed.
    """
    total = sum(counts)
    if (
        total < _KERNEL_MIN_RECORDS
        or total > _INT64_MAX
        or spread_model == SPREAD_VARIABLE
    ):
        return None

    quantum_exponent = int(quantum.as_tuple().exponent)
    if quantum_exponent > 0:
        return None
    price_precision = -quantum_exponent
    internal_precision = price_precision
    for bar in bars:
        internal_precision = max(
            internal_precision,
            *(_decimal_places(value) for value in _waypoints(bar)),
            _decimal_places(
                _spread_increment(
                    bar,
                    spread_model,
                    fixed_spread_points,
                    point_value,
                )
            ),
        )
    precision_difference = internal_precision - price_precision
    if precision_difference > _MAX_INTERNAL_PRECISION_DIFFERENCE:
        return None
    output_divisor = 10**precision_difference
    internal_quantum = _quantum(internal_precision)

    waypoints = np.empty((len(bars), _WAYPOINTS_PER_BAR), dtype=np.int64)
    phases = np.empty((len(bars), _WAYPOINTS_PER_BAR), dtype=np.int64)
    starts = np.empty(len(bars), dtype=np.int64)
    spreads = np.empty(len(bars), dtype=np.int64)
    for bar_index, bar in enumerate(bars):
        converted = _kernel_bar_data(
            bar,
            counts[bar_index],
            point_value,
            internal_quantum,
            spread_model,
            fixed_spread_points,
            output_divisor,
        )
        if converted is None:
            return None
        integer_values, phase_values, start_us, spread_ticks = converted
        waypoints[bar_index] = integer_values
        phases[bar_index] = phase_values
        starts[bar_index] = start_us
        spreads[bar_index] = spread_ticks

    if model == TICK_MODEL_GENERATED:
        count_array = np.asarray(counts, dtype=np.int64)
        output_offsets = np.empty(len(bars) + 1, dtype=np.int64)
        output_offsets[0] = 0
        np.cumsum(count_array, out=output_offsets[1:])
        raw_columns = generate_volume_tick_arrays(
            waypoints,
            phases,
            starts,
            count_array,
            output_offsets,
            spreads,
            max(1, bar_seconds * 1_000),
            output_divisor,
        )
    else:
        raw_columns = generate_four_tick_arrays(
            waypoints,
            phases,
            starts,
            np.asarray(_four_tick_offsets(bar_seconds), dtype=np.int64),
            spreads,
            output_divisor,
        )
    columns = _KernelColumns(*raw_columns)
    _validate_kernel_columns(columns, total, len(bars))
    return columns


def _validate_kernel_columns(
    columns: _KernelColumns,
    expected_count: int,
    bar_count: int,
) -> None:
    """Validate compiled output before trusted canonical record construction.

    Args:
        columns: Compiled fixed-point result columns.
        expected_count: Preflighted output row count.
        bar_count: Number of source bars.

    Raises:
        RuntimeError: If a private kernel violates its internal contract.
    """
    if any(column.size != expected_count for column in columns):
        raise RuntimeError("tick kernel returned inconsistent column lengths")
    if expected_count == 0:
        raise RuntimeError("tick kernel returned no records")
    if np.any(columns.asks < columns.bids):
        raise RuntimeError("tick kernel returned ask below bid")
    if np.any(columns.local_indices < 0):
        raise RuntimeError("tick kernel returned a negative local index")
    maximum_phase = PHASE_OPEN | PHASE_HIGH | PHASE_LOW | PHASE_CLOSE
    if np.any(columns.phases < 0) or np.any(columns.phases > maximum_phase):
        raise RuntimeError("tick kernel returned an invalid phase mask")
    if np.any(columns.bar_indices < 0) or np.any(columns.bar_indices >= bar_count):
        raise RuntimeError("tick kernel returned an invalid source-bar index")


def _decimal_from_ticks(value: int, price_precision: int) -> Decimal:
    """Restore a fixed-point integer as an exactly scaled Decimal.

    Args:
        value: Integer count of price quanta.
        price_precision: Decimal exponent used by the public operation.

    Returns:
        Exact price Decimal with the requested exponent.
    """
    return Decimal(value).scaleb(-price_precision)


def _records_from_kernel(
    bars: Sequence[OHLCVRecord],
    columns: _KernelColumns,
    model: str,
    counts: tuple[int, ...],
    bar_seconds: int,
    price_precision: int,
) -> tuple[TickRecord, ...]:
    """Construct canonical immutable records from validated compiled columns.

    Args:
        bars: Ordered canonical source bars.
        columns: Validated compiled output columns.
        model: Selected tick derivation model.
        counts: Per-bar output record counts.
        bar_seconds: Inferred source-bar duration in seconds.
        price_precision: Decimal exponent used by the public operation.

    Returns:
        Canonical tick records preserving the public contract.
    """
    four_offsets = _four_tick_offsets(bar_seconds)
    bar_milliseconds = max(1, bar_seconds * 1_000)
    timestamp_cache: dict[int, datetime] = {}
    price_cache: dict[int, Decimal] = {}
    templates = tuple(
        TickRecord.model_construct(
            timestamp=bar.timestamp,
            source=bar.source,
            source_symbol=bar.source_symbol,
            source_revision=bar.source_revision,
            available_at=bar.available_at,
            bid=bar.open,
            ask=bar.open,
            last=bar.open,
            price_unit=bar.price_unit,
            source_bar_time=bar.timestamp,
            tick_index_in_bar=0,
            bar_phase=0,
        )
        for bar in bars
    )
    records: list[TickRecord] = []
    for output_index in range(columns.timestamps_us.size):
        bar_index = int(columns.bar_indices[output_index])
        local_index = int(columns.local_indices[output_index])
        bar = bars[bar_index]
        if model == TICK_MODEL_GENERATED:
            offset_ms = (bar_milliseconds * local_index) // counts[bar_index]
        else:
            offset_ms = four_offsets[local_index]
        raw_timestamp = bar.timestamp + timedelta(milliseconds=offset_ms)
        timestamp_value = int(columns.timestamps_us[output_index])
        timestamp = timestamp_cache.get(timestamp_value)
        if timestamp is None:
            timestamp = _EPOCH + timedelta(microseconds=timestamp_value)
            timestamp_cache[timestamp_value] = timestamp
        bid_value = int(columns.bids[output_index])
        ask_value = int(columns.asks[output_index])
        bid = price_cache.get(bid_value)
        if bid is None:
            bid = _decimal_from_ticks(bid_value, price_precision)
            price_cache[bid_value] = bid
        ask = price_cache.get(ask_value)
        if ask is None:
            ask = _decimal_from_ticks(ask_value, price_precision)
            price_cache[ask_value] = ask
        records.append(
            templates[bar_index].model_copy(
                update={
                    "timestamp": timestamp,
                    "available_at": max(bar.available_at, raw_timestamp),
                    "bid": bid,
                    "ask": ask,
                    "last": bid,
                    "tick_index_in_bar": local_index,
                    "bar_phase": int(columns.phases[output_index]),
                }
            )
        )
    return tuple(records)


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
    quantized_bid = _quantize_tick(bid, quantum)
    quantized_ask = _quantize_tick(bid + (spread_points * point_value), quantum)
    normalized_timestamp = (
        timestamp.replace(microsecond=0) if timestamp.microsecond != 0 else timestamp
    )
    return TickRecord(
        timestamp=normalized_timestamp,
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
    counts: tuple[int, ...],
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
    logger.debug("Running DATA function: _generated_records")
    bar_ms = max(1, bar_seconds * 1000)
    records: list[TickRecord] = []
    for bar, tick_count in zip(bars, counts, strict=True):
        values = _waypoints(bar)
        phases = _waypoint_phases(bar)
        lengths = _segment_lengths(tick_count)
        constant_spread = None
        if spread_model != SPREAD_VARIABLE:
            constant_spread = _spread_points_for(
                bar.spread,
                spread_model,
                fixed_spread_points,
                min_spread_points,
                max_spread_points,
                rng,
            )
        for local_index in range(tick_count):
            price, phase = _interpolated_price_and_phase(
                values,
                phases,
                lengths,
                local_index,
                tick_count,
            )
            spread_points = constant_spread
            if spread_points is None:
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
                        else _quantize_tick(member.bid, quantum),
                        "ask": None
                        if member.ask is None
                        else _quantize_tick(member.ask, quantum),
                        "last": None
                        if member.last is None
                        else _quantize_tick(member.last, quantum),
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
        counts = _tick_counts(bars, model, max_records, resolved_request_id)
        kernel_columns = _try_kernel_columns(
            bars,
            model,
            counts,
            bar_seconds,
            point_value,
            quantum,
            spread_model,
            fixed_spread_points,
        )
        if kernel_columns is not None:
            records = _records_from_kernel(
                bars,
                kernel_columns,
                model,
                counts,
                bar_seconds,
                price_precision,
            )
        elif model == TICK_MODEL_GENERATED:
            records = _generated_records(
                bars,
                counts,
                bar_seconds,
                point_value,
                quantum,
                spread_model,
                fixed_spread_points,
                min_spread_points,
                max_spread_points,
                rng,
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

    ordered = records
    if any(
        (records[index].timestamp, records[index].tick_index_in_bar or 0)
        > (records[index + 1].timestamp, records[index + 1].tick_index_in_bar or 0)
        for index in range(len(records) - 1)
    ):
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


def _kernel_parquet_columns(
    dataset: MarketDataset,
    generation_arguments: Mapping[str, object],
) -> Mapping[str, object] | None:
    """Build Parquet-ready columns directly from an eligible compiled batch.

    Args:
        dataset: One bounded source-bar chunk.
        generation_arguments: Public generation arguments supplied by the caller.

    Returns:
        Parquet-ready columns, or None when the canonical public fallback is needed.
    """
    model = generation_arguments.get("model")
    trading_timeframe = generation_arguments.get("trading_timeframe")
    spread_model = generation_arguments.get("spread_model", SPREAD_NATIVE)
    point_value = generation_arguments.get("point_value", Decimal("0.00001"))
    price_precision = generation_arguments.get("price_precision", 5)
    fixed_spread_points = generation_arguments.get("fixed_spread_points")
    max_records = generation_arguments.get("max_records")
    supported = (
        model in {TICK_MODEL_TRADING_BAR, TICK_MODEL_GENERATED}
        and isinstance(trading_timeframe, str)
        and isinstance(spread_model, str)
        and isinstance(point_value, Decimal)
        and isinstance(price_precision, int)
        and (fixed_spread_points is None or isinstance(fixed_spread_points, Decimal))
        and (max_records is None or isinstance(max_records, int))
    )
    if not supported:
        return None
    resolved_timeframe = cast("str", trading_timeframe)
    resolved_point_value = cast("Decimal", point_value)
    resolved_precision = cast("int", price_precision)

    resolved_model = str(model)
    resolved_spread_model = str(spread_model)
    resolved_fixed_spread = (
        fixed_spread_points if isinstance(fixed_spread_points, Decimal) else None
    )
    request_id = dataset.request_id
    minimum_value = generation_arguments.get("min_spread_points")
    maximum_value = generation_arguments.get("max_spread_points")
    seed_value = generation_arguments.get("seed")
    minimum_spread = minimum_value if isinstance(minimum_value, Decimal) else None
    maximum_spread = maximum_value if isinstance(maximum_value, Decimal) else None
    resolved_seed = seed_value if isinstance(seed_value, int) else None
    _validate_spread_model(
        resolved_spread_model,
        resolved_fixed_spread,
        minimum_spread,
        maximum_spread,
        resolved_seed,
        request_id,
    )
    if resolved_point_value <= 0 or not resolved_point_value.is_finite():
        raise _error("INVALID_INPUT", "point_value", request_id, "must be > 0")
    bars = _require_bars(dataset, request_id)
    bar_seconds = _bar_seconds(bars, resolved_timeframe, request_id)
    counts = _tick_counts(
        bars,
        resolved_model,
        max_records if isinstance(max_records, int) else None,
        request_id,
    )
    columns = _try_kernel_columns(
        bars,
        resolved_model,
        counts,
        bar_seconds,
        resolved_point_value,
        _quantum(resolved_precision),
        resolved_spread_model,
        resolved_fixed_spread,
    )
    if columns is None:
        return None
    if np.any(columns.timestamps_us[:-1] > columns.timestamps_us[1:]):
        return None

    timestamps = [
        _EPOCH + timedelta(microseconds=int(value)) for value in columns.timestamps_us
    ]
    bids = [
        str(_decimal_from_ticks(int(value), resolved_precision))
        for value in columns.bids
    ]
    asks = [
        str(_decimal_from_ticks(int(value), resolved_precision))
        for value in columns.asks
    ]
    source_bar_times = [
        bars[int(bar_index)].timestamp for bar_index in columns.bar_indices
    ]
    return {
        "timestamp": timestamps,
        "bid": bids,
        "ask": asks,
        "last": bids,
        "source_bar_time": source_bar_times,
        "tick_index_in_bar": columns.local_indices,
        "bar_phase": columns.phases.astype(np.int64),
    }


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

    requested_model = generation_arguments.get("model")
    requested_maximum = generation_arguments.get("max_records")
    if requested_model in {TICK_MODEL_TRADING_BAR, TICK_MODEL_GENERATED} and isinstance(
        requested_maximum, int
    ):
        source_bars = _require_bars(dataset, dataset.request_id)
        _tick_counts(
            source_bars,
            str(requested_model),
            requested_maximum,
            dataset.request_id,
        )

    chunks = _source_chunks(dataset, max_output_rows_per_chunk)
    writer: pq.ParquetWriter | None = None
    rows_written = 0
    columns: list[str] = []
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        for chunk in chunks:
            direct_columns = _kernel_parquet_columns(chunk, generation_arguments)
            if direct_columns is None:
                generated = generate_tick_series(
                    chunk,
                    **generation_arguments,  # type: ignore[arg-type]
                )
                frame = pd.DataFrame(_serialize_rows(generated))
                if frame.empty:
                    continue
                table = pa.Table.from_pandas(frame, preserve_index=False)
                frame_columns = [str(column) for column in frame.columns]
                row_count = len(frame)
            else:
                table = pa.Table.from_pydict(direct_columns)
                frame_columns = [str(column) for column in direct_columns]
                row_count = table.num_rows
            if writer is None:
                writer = pq.ParquetWriter(path, table.schema)  # type: ignore[no-untyped-call]
                columns = frame_columns
            writer.write_table(table)  # type: ignore[no-untyped-call]
            rows_written += row_count
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
