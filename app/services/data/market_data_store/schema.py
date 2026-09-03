"""Strict PyArrow Schemas and Fixed-Point Tick Conversion Engine."""

from __future__ import annotations

from decimal import Decimal

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

# Canonical PyArrow Schemas for on-disk Parquet datasets

TICK_ARROW_SCHEMA = pa.schema(
    [
        pa.field("datetime", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("sequence", pa.uint32(), nullable=False),
        pa.field("bid_ticks", pa.int64(), nullable=False),
        pa.field("ask_ticks", pa.int64(), nullable=False),
        pa.field("last_ticks", pa.int64(), nullable=True),
        pa.field("volume", pa.uint64(), nullable=False),
        pa.field("flags", pa.uint16(), nullable=False),
    ]
)

BAR_ARROW_SCHEMA = pa.schema(
    [
        pa.field("datetime", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("open_ticks", pa.int64(), nullable=False),
        pa.field("high_ticks", pa.int64(), nullable=False),
        pa.field("low_ticks", pa.int64(), nullable=False),
        pa.field("close_ticks", pa.int64(), nullable=False),
        pa.field("tick_volume", pa.uint64(), nullable=False),
        pa.field("real_volume", pa.uint64(), nullable=True),
    ]
)


def price_to_ticks(price: float | Decimal, tick_size: float | Decimal) -> int:
    """Convert a floating or decimal price to fixed-point integer ticks.

    Formula:
        ticks = round(price / tick_size)

    Args:
        price: Raw monetary price value.
        tick_size: Instrument tick size specification (e.g. 0.00001 or 0.001).

    Returns:
        Exact integer tick representation.
    """
    if isinstance(price, Decimal) or isinstance(tick_size, Decimal):
        dec_price = Decimal(str(price))
        dec_tick_size = Decimal(str(tick_size))
        return int((dec_price / dec_tick_size).quantize(Decimal(1)))
    return round(float(price) / float(tick_size))


def ticks_to_price(
    ticks: int | np.ndarray,
    tick_size: float | Decimal,
) -> float | np.ndarray:
    """Restore a floating price value from fixed-point integer ticks.

    Args:
        ticks: Integer tick count or array of ticks.
        tick_size: Instrument tick size specification.

    Returns:
        Floating-point price matching the instrument precision.
    """
    return ticks * float(tick_size)


def _extract_datetime_col(table: pa.Table, name_map: dict[str, str]) -> pa.ChunkedArray:
    """Extract and normalize UTC timestamp column."""
    candidates = ("datetime", "time", "timestamp", "ts")
    dt_col_name = next((name_map[c] for c in candidates if c in name_map), None)
    if dt_col_name is None:
        msg = f"Input table missing datetime column. Available: {table.column_names}"
        raise ValueError(msg)

    dt_col = table[dt_col_name]
    if (
        not pa.types.is_timestamp(dt_col.type)
        or dt_col.type.tz != "UTC"
        or dt_col.type.unit != "us"
    ):
        dt_col = pc.cast(dt_col, pa.timestamp("us", tz="UTC"))
    return dt_col


def _extract_price_ticks(
    table: pa.Table,
    name_map: dict[str, str],
    tick_col: str,
    float_col: str,
    inv_tick_size: float,
) -> pa.ChunkedArray:
    """Extract price ticks directly or convert from floats."""
    if tick_col in name_map:
        return pc.cast(table[name_map[tick_col]], pa.int64())
    if float_col in name_map:
        raw = table[name_map[float_col]].to_numpy()
        ticks = np.round(raw * inv_tick_size).astype(np.int64)
        return pa.array(ticks, type=pa.int64())
    msg = f"Table missing '{float_col}' or '{tick_col}' column"
    raise ValueError(msg)


def convert_ticks_table_to_canonical(
    table: pa.Table,
    tick_size: float | Decimal,
) -> pa.Table:
    """Transform an incoming tick table to canonical integer-tick Arrow schema.

    Args:
        table: Raw PyArrow Table.
        tick_size: Instrument tick size for scaling prices.

    Returns:
        PyArrow Table conforming strictly to TICK_ARROW_SCHEMA.
    """
    name_map = {c.lower(): c for c in table.column_names}
    inv_tick_size = 1.0 / float(tick_size)

    dt_col = _extract_datetime_col(table, name_map)

    # Sequence
    if "sequence" in name_map:
        seq_col = pc.cast(table[name_map["sequence"]], pa.uint32())
    else:
        seq_col = pa.array(np.arange(len(table), dtype=np.uint32), type=pa.uint32())

    # Bids & Asks
    bid_col = _extract_price_ticks(table, name_map, "bid_ticks", "bid", inv_tick_size)
    ask_col = _extract_price_ticks(table, name_map, "ask_ticks", "ask", inv_tick_size)

    # Last ticks (nullable)
    if "last_ticks" in name_map:
        last_col = pc.cast(table[name_map["last_ticks"]], pa.int64())
    elif "last" in name_map or "price" in name_map:
        c_name = name_map.get("last", name_map.get("price"))
        raw_last = table[c_name].to_numpy()
        last_col = pa.array(
            np.round(raw_last * inv_tick_size).astype(np.int64), type=pa.int64()
        )
    else:
        last_col = pa.nulls(len(table), type=pa.int64())

    # Volume & Flags
    vol_c = next(
        (name_map[c] for c in ("volume", "vol", "size") if c in name_map), None
    )
    vol_col = (
        pc.cast(table[vol_c], pa.uint64())
        if vol_c
        else pa.array(np.zeros(len(table), dtype=np.uint64), type=pa.uint64())
    )

    flags_col = (
        pc.cast(table[name_map["flags"]], pa.uint16())
        if "flags" in name_map
        else pa.array(np.zeros(len(table), dtype=np.uint16), type=pa.uint16())
    )

    return pa.Table.from_arrays(
        [dt_col, seq_col, bid_col, ask_col, last_col, vol_col, flags_col],
        schema=TICK_ARROW_SCHEMA,
    )


def convert_bars_table_to_canonical(
    table: pa.Table,
    tick_size: float | Decimal,
) -> pa.Table:
    """Transform an incoming bar table to canonical integer-tick Arrow schema.

    Args:
        table: Raw PyArrow Table.
        tick_size: Instrument tick size for scaling prices.

    Returns:
        PyArrow Table conforming strictly to BAR_ARROW_SCHEMA.
    """
    name_map = {c.lower(): c for c in table.column_names}
    inv_tick_size = 1.0 / float(tick_size)

    dt_col = _extract_datetime_col(table, name_map)

    # OHLC
    o_col = _extract_price_ticks(table, name_map, "open_ticks", "open", inv_tick_size)
    h_col = _extract_price_ticks(table, name_map, "high_ticks", "high", inv_tick_size)
    l_col = _extract_price_ticks(table, name_map, "low_ticks", "low", inv_tick_size)
    c_col = _extract_price_ticks(table, name_map, "close_ticks", "close", inv_tick_size)

    # Volumes
    if "tick_volume" in name_map:
        t_vol = pc.cast(table[name_map["tick_volume"]], pa.uint64())
    elif "volume" in name_map:
        t_vol = pc.cast(table[name_map["volume"]], pa.uint64())
    else:
        t_vol = pa.array(np.zeros(len(table), dtype=np.uint64), type=pa.uint64())

    r_vol = (
        pc.cast(table[name_map["real_volume"]], pa.uint64())
        if "real_volume" in name_map
        else pa.nulls(len(table), type=pa.uint64())
    )

    return pa.Table.from_arrays(
        [dt_col, o_col, h_col, l_col, c_col, t_vol, r_vol],
        schema=BAR_ARROW_SCHEMA,
    )
