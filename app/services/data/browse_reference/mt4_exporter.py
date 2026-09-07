"""MetaTrader 4 HST and FXT Binary Exporter for Market Data.

Generates standard MetaTrader 4 HST history files (format version 401)
and FXT test files for StrategyQuant and MetaTrader 4 backtesting.
"""

from __future__ import annotations

import struct
import time
from collections.abc import Sequence
from pathlib import Path


def export_hst_file(
    output_path: str | Path,
    symbol: str,
    period: int,
    digits: int,
    bars: Sequence[dict[str, float | int]],
) -> int:
    """Write bars to an MT4 HST file (format 401).

    Args:
        output_path: Target .hst file path.
        symbol: Market symbol name (e.g. 'EURUSD').
        period: Timeframe period in minutes (1, 5, 15, 30, 60, 240, 1440).
        digits: Price decimal precision (e.g. 5).
        bars: Sequence of dicts with keys: 'time' (epoch seconds),
            'open', 'high', 'low', 'close', 'volume'.

    Returns:
        Number of bars written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    version = 401
    copyright_str = "Copyright 2001-2026, MetaQuotes Software Corp.".encode("latin-1")[
        :64
    ].ljust(64, b"\x00")
    symbol_bytes = symbol.encode("latin-1")[:12].ljust(12, b"\x00")
    timesign = int(time.time())
    last_sync = 0
    unused = b"\x00" * (13 * 4)

    # 148 bytes header
    header = struct.pack(
        "<i64s12siii52s",
        version,
        copyright_str,
        symbol_bytes,
        period,
        digits,
        timesign,
        last_sync,
        unused,
    )

    with Path(output_path).open("wb") as f:
        f.write(header)
        for bar in bars:
            t = int(bar["time"])
            o = float(bar["open"])
            h = float(bar["high"])
            low_val = float(bar["low"])
            c = float(bar["close"])
            v = int(bar.get("volume", 1))
            spread = int(bar.get("spread", 0))
            real_vol = int(bar.get("real_volume", v))

            # 60 bytes per bar (version 401)
            # q: int64 time
            # d: double open
            # d: double high
            # d: double low
            # d: double close
            # q: int64 volume
            # i: int32 spread
            record = struct.pack("<qddddqiq", t, o, h, low_val, c, v, spread, real_vol)
            f.write(record)

    return len(bars)


def export_fxt_file(
    output_path: str | Path,
    symbol: str,
    period: int,
    digits: int,
    bars: Sequence[dict[str, float | int]],
    spread: int = 15,
    leverage: int = 100,
    lot_size: float = 100000.0,
) -> int:
    """Write bars to an MT4 FXT backtesting file.

    Args:
        output_path: Target .fxt file path.
        symbol: Symbol name.
        period: Timeframe period.
        digits: Price precision digits.
        bars: Bars or ticks sequence.
        spread: Default spread in points.
        leverage: Account leverage.
        lot_size: Contract size.

    Returns:
        Number of records written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    version = 405
    desc = "HaruQuantAI MT4 FXT Generator".encode("latin-1")[:128].ljust(128, b"\x00")
    server = "DefaultServer".encode("latin-1")[:32].ljust(32, b"\x00")
    symbol_bytes = symbol.encode("latin-1")[:16].ljust(16, b"\x00")
    model_type = 2  # Every tick based on real ticks/bars
    first_time = int(bars[0]["time"]) if bars else 0
    last_time = int(bars[-1]["time"]) if bars else 0

    header = bytearray(728)
    struct.pack_into("<i", header, 0, version)
    header[4:132] = desc
    header[132:164] = server
    header[164:180] = symbol_bytes
    struct.pack_into("<i", header, 180, period)
    struct.pack_into("<i", header, 184, model_type)
    struct.pack_into("<i", header, 188, len(bars))
    struct.pack_into("<i", header, 192, first_time)
    struct.pack_into("<i", header, 196, last_time)
    struct.pack_into("<d", header, 204, 99.9)  # model quality
    # currency
    header[212:224] = b"USD\x00".ljust(12, b"\x00")
    struct.pack_into("<i", header, 224, spread)
    struct.pack_into("<i", header, 228, digits)
    struct.pack_into("<d", header, 236, 10.0 ** (-digits))  # point size
    struct.pack_into("<d", header, 244, lot_size)
    struct.pack_into("<i", header, 252, leverage)

    with Path(output_path).open("wb") as f:
        f.write(header)
        for bar in bars:
            t = int(bar["time"])
            o = float(bar["open"])
            h = float(bar["high"])
            low_val = float(bar["low"])
            c = float(bar["close"])
            v = int(bar.get("volume", 1))

            # 44 bytes per record in FXT
            # i: time
            # d: open
            # d: high
            # d: low
            # d: close
            # q: volume
            rec = struct.pack("<iddddq", t, o, h, low_val, c, v)
            f.write(rec)

    return len(bars)
