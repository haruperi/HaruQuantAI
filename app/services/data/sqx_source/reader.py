"""Direct SQX/QuantDataManager ``.dat`` binary reader (FEAT-DATA-15).

Decodes StrategyQuant X (version 4.x) M1-bar and tick ``.dat`` files into
pandas DataFrames without intermediate conversion or disk duplication. The
payload is a sequential delta stream: each record carries per-field config
bytes whose 2-bit fields encode the value width (1/2/4/8 bytes) and the
delta opcode (subtract/add/absolute), and every 1000 records a 19-byte sync
chain plus block index realigns the stream. Prices scale by 10^6 and volumes
by 10^5 (M1, version 4.2) or 10^2 (ticks).

The reader is read-only: it never writes into the QuantDataManager workspace.
"""

from __future__ import annotations

import sqlite3
import struct
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Literal

import numba as nb
import numpy as np
import pandas as pd

from app.services.data._settings import get_data_settings
from app.services.data.contracts import DataError
from app.services.data.persistence import read_quantdata_symbol_rows
from app.utils import get_logger

logger = get_logger(__name__)

# SQX scaling constants: prices as 10^6 points and volumes by data kind.
_PRICE_SCALE: float = 1_000_000.0
_M1_VOLUME_SCALE: float = 100_000.0
_TICK_VOLUME_SCALE: float = 100.0
_EPOCH_MS_CUTOFF: int = 10_000_000_000
_MAX_SYNC_RECORDS: int = 1000
_SYNC_BYTES: int = 19

type _Timestamp = str | datetime | int | "np.integer[Any]"


def _resolve_history_root(request_id: str) -> Path:
    """Resolve the configured QuantDataManager history root.

    Args:
        request_id: Caller trace identity.

    Returns:
        Existing ``user/data/History`` directory under the configured root.

    Raises:
        DataError: If the QuantDataManager root is absent or unusable.
    """
    root = get_data_settings().quantdata_manager_root
    if root is None:
        raise DataError("QUANTDATA_ROOT_MISSING", request_id=request_id)
    history = root / "user" / "data" / "History"
    if not history.is_dir():
        raise DataError("QUANTDATA_ROOT_MISSING", request_id=request_id)
    return history


def _resolve_database_path(request_id: str) -> Path:
    """Resolve the QuantDataManager SQLite catalogue path.

    Args:
        request_id: Caller trace identity.

    Returns:
        Existing ``user/data/data.db`` path.

    Raises:
        DataError: If the database is absent.
    """
    root = get_data_settings().quantdata_manager_root
    if root is None:
        raise DataError("QUANTDATA_ROOT_MISSING", request_id=request_id)
    database = root / "user" / "data" / "data.db"
    if not database.is_file():
        raise DataError("QUANTDATA_ROOT_MISSING", request_id=request_id)
    return database


@nb.njit(fastmath=True, cache=True)  # type: ignore[untyped-decorator]
def _decode_m1_records(
    buf: np.ndarray,
    max_records: int,
    start_ts_ms: np.int64,
    end_ts_ms: np.int64,
    price_scale: np.float64,
    volume_scale: np.float64,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Decode M1 OHLCV records into contiguous arrays.

    Args:
        buf: Raw payload bytes.
        max_records: Header-declared record bound.
        start_ts_ms: Inclusive start filter in epoch milliseconds.
        end_ts_ms: Inclusive end filter in epoch milliseconds.
        price_scale: Price divisor (10^6).
        volume_scale: Volume divisor by data kind.

    Returns:
        Truncated arrays of time, open, high, low, close, and volume.
    """
    times = np.empty(max_records, dtype=np.int64)
    opens = np.empty(max_records, dtype=np.float64)
    highs = np.empty(max_records, dtype=np.float64)
    lows = np.empty(max_records, dtype=np.float64)
    closes = np.empty(max_records, dtype=np.float64)
    volumes = np.empty(max_records, dtype=np.float64)

    pos = 0
    prev_time = np.int64(0)
    prev_open = np.int64(0)
    prev_high = np.int64(0)
    prev_low = np.int64(0)
    prev_close = np.int64(0)
    prev_volume = np.int64(0)

    buf_len = len(buf)
    idx = 0
    raw_idx = 0

    while raw_idx < max_records and pos < buf_len:
        # Every 1000 records a 19-byte sync chain plus block index realigns
        # the stream; it carries no bar values.
        if raw_idx % _MAX_SYNC_RECORDS == 0:
            pos += _SYNC_BYTES
            if pos >= buf_len:
                break

        cfg0 = buf[pos]
        cfg1 = buf[pos + 1]
        cfg2 = buf[pos + 2]
        pos += 3

        vol_dt = cfg2 & 3
        vol_op = (cfg2 >> 2) & 3
        close_dt = (cfg2 >> 4) & 3
        close_op = (cfg2 >> 6) & 3
        low_dt = cfg1 & 3
        low_op = (cfg1 >> 2) & 3
        high_dt = (cfg1 >> 4) & 3
        high_op = (cfg1 >> 6) & 3
        open_dt = cfg0 & 3
        open_op = (cfg0 >> 2) & 3
        time_dt = (cfg0 >> 4) & 3
        time_op = (cfg0 >> 6) & 3

        time_val = np.int64(buf[pos])  # widened below per width field
        if time_dt == 0:
            time_val = np.int64(buf[pos])
            pos += 1
        elif time_dt == 1:
            time_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif time_dt == 2:
            time_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            time_val = np.int64(0)
            for k in range(8):
                time_val = (time_val << 8) | buf[pos + k]
            pos += 8
        if time_op == 0:
            prev_time -= time_val
        elif time_op == 1:
            prev_time += time_val
        else:
            prev_time = time_val

        open_val = np.int64(0)
        if open_dt == 0:
            open_val = np.int64(buf[pos])
            pos += 1
        elif open_dt == 1:
            open_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif open_dt == 2:
            open_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            open_val = np.int64(0)
            for k in range(8):
                open_val = (open_val << 8) | buf[pos + k]
            pos += 8
        if open_op == 0:
            prev_open -= open_val
        elif open_op == 1:
            prev_open += open_val
        else:
            prev_open = open_val

        high_val = np.int64(0)
        if high_dt == 0:
            high_val = np.int64(buf[pos])
            pos += 1
        elif high_dt == 1:
            high_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif high_dt == 2:
            high_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            high_val = np.int64(0)
            for k in range(8):
                high_val = (high_val << 8) | buf[pos + k]
            pos += 8
        if high_op == 0:
            prev_high -= high_val
        elif high_op == 1:
            prev_high += high_val
        else:
            prev_high = high_val

        low_val = np.int64(0)
        if low_dt == 0:
            low_val = np.int64(buf[pos])
            pos += 1
        elif low_dt == 1:
            low_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif low_dt == 2:
            low_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            low_val = np.int64(0)
            for k in range(8):
                low_val = (low_val << 8) | buf[pos + k]
            pos += 8
        if low_op == 0:
            prev_low -= low_val
        elif low_op == 1:
            prev_low += low_val
        else:
            prev_low = low_val

        close_val = np.int64(0)
        if close_dt == 0:
            close_val = np.int64(buf[pos])
            pos += 1
        elif close_dt == 1:
            close_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif close_dt == 2:
            close_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            close_val = np.int64(0)
            for k in range(8):
                close_val = (close_val << 8) | buf[pos + k]
            pos += 8
        if close_op == 0:
            prev_close -= close_val
        elif close_op == 1:
            prev_close += close_val
        else:
            prev_close = close_val

        volume_val = np.int64(0)
        if vol_dt == 0:
            volume_val = np.int64(buf[pos])
            pos += 1
        elif vol_dt == 1:
            volume_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif vol_dt == 2:
            volume_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            volume_val = np.int64(0)
            for k in range(8):
                volume_val = (volume_val << 8) | buf[pos + k]
            pos += 8
        if vol_op == 0:
            prev_volume -= volume_val
        elif vol_op == 1:
            prev_volume += volume_val
        else:
            prev_volume = volume_val

        raw_idx += 1

        if prev_time > end_ts_ms:
            break
        if prev_time >= start_ts_ms:
            times[idx] = prev_time
            opens[idx] = prev_open / price_scale
            highs[idx] = prev_high / price_scale
            lows[idx] = prev_low / price_scale
            closes[idx] = prev_close / price_scale
            volumes[idx] = prev_volume / volume_scale
            idx += 1

    return (
        times[:idx],
        opens[:idx],
        highs[:idx],
        lows[:idx],
        closes[:idx],
        volumes[:idx],
    )


@nb.njit(fastmath=True, cache=True)  # type: ignore[untyped-decorator]
def _decode_tick_records(
    buf: np.ndarray,
    max_records: int,
    start_ts_ms: np.int64,
    end_ts_ms: np.int64,
    price_scale: np.float64,
    volume_scale: np.float64,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Decode tick bid/ask/volume records into contiguous arrays.

    Args:
        buf: Raw payload bytes.
        max_records: Header-declared record bound.
        start_ts_ms: Inclusive start filter in epoch milliseconds.
        end_ts_ms: Inclusive end filter in epoch milliseconds.
        price_scale: Price divisor (10^6).
        volume_scale: Tick volume divisor (10^2).

    Returns:
        Truncated arrays of time, bid, ask, and volume.
    """
    times = np.empty(max_records, dtype=np.int64)
    bids = np.empty(max_records, dtype=np.float64)
    asks = np.empty(max_records, dtype=np.float64)
    volumes = np.empty(max_records, dtype=np.float64)

    pos = 0
    prev_time = np.int64(0)
    prev_bid = np.int64(0)
    prev_ask = np.int64(0)
    prev_volume = np.int64(0)

    buf_len = len(buf)
    idx = 0
    raw_idx = 0

    while raw_idx < max_records and pos < buf_len:
        if raw_idx % _MAX_SYNC_RECORDS == 0:
            pos += _SYNC_BYTES
            if pos >= buf_len:
                break

        cfg0 = buf[pos]
        cfg1 = buf[pos + 1]
        pos += 2

        vol_dt = cfg1 & 3
        vol_op = (cfg1 >> 2) & 3
        bid_dt = (cfg1 >> 4) & 3
        bid_op = (cfg1 >> 6) & 3
        ask_dt = cfg0 & 3
        ask_op = (cfg0 >> 2) & 3
        time_dt = (cfg0 >> 4) & 3
        time_op = (cfg0 >> 6) & 3

        time_val = np.int64(0)
        if time_dt == 0:
            time_val = np.int64(buf[pos])
            pos += 1
        elif time_dt == 1:
            time_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif time_dt == 2:
            time_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            time_val = np.int64(0)
            for k in range(8):
                time_val = (time_val << 8) | buf[pos + k]
            pos += 8
        if time_op == 0:
            prev_time -= time_val
        elif time_op == 1:
            prev_time += time_val
        else:
            prev_time = time_val

        ask_val = np.int64(0)
        if ask_dt == 0:
            ask_val = np.int64(buf[pos])
            pos += 1
        elif ask_dt == 1:
            ask_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif ask_dt == 2:
            ask_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            ask_val = np.int64(0)
            for k in range(8):
                ask_val = (ask_val << 8) | buf[pos + k]
            pos += 8
        if ask_op == 0:
            prev_ask -= ask_val
        elif ask_op == 1:
            prev_ask += ask_val
        else:
            prev_ask = ask_val

        bid_val = np.int64(0)
        if bid_dt == 0:
            bid_val = np.int64(buf[pos])
            pos += 1
        elif bid_dt == 1:
            bid_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif bid_dt == 2:
            bid_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            bid_val = np.int64(0)
            for k in range(8):
                bid_val = (bid_val << 8) | buf[pos + k]
            pos += 8
        if bid_op == 0:
            prev_bid -= bid_val
        elif bid_op == 1:
            prev_bid += bid_val
        else:
            prev_bid = bid_val

        volume_val = np.int64(0)
        if vol_dt == 0:
            volume_val = np.int64(buf[pos])
            pos += 1
        elif vol_dt == 1:
            volume_val = np.int64((np.int64(buf[pos]) << 8) | buf[pos + 1])
            pos += 2
        elif vol_dt == 2:
            volume_val = np.int64(
                (np.int64(buf[pos]) << 24)
                | (np.int64(buf[pos + 1]) << 16)
                | (np.int64(buf[pos + 2]) << 8)
                | buf[pos + 3]
            )
            pos += 4
        else:
            volume_val = np.int64(0)
            for k in range(8):
                volume_val = (volume_val << 8) | buf[pos + k]
            pos += 8
        if vol_op == 0:
            prev_volume -= volume_val
        elif vol_op == 1:
            prev_volume += volume_val
        else:
            prev_volume = volume_val

        raw_idx += 1

        if prev_time > end_ts_ms:
            break
        if prev_time >= start_ts_ms:
            times[idx] = prev_time
            bids[idx] = prev_bid / price_scale
            asks[idx] = prev_ask / price_scale
            volumes[idx] = prev_volume / volume_scale
            idx += 1

    return times[:idx], bids[:idx], asks[:idx], volumes[:idx]


def _parse_header(handle: IO[bytes]) -> dict[str, Any]:
    """Parse one SQX ``.dat`` binary header.

    Args:
        handle: Binary file handle positioned at the header start.

    Returns:
        Parsed version, data type, record count, and header length.

    Raises:
        EOFError: If the header is truncated.
    """

    def read_utf() -> str:
        """Read one length-prefixed big-endian UTF-8 header string.

        Returns:
            Decoded header string.

        Raises:
            EOFError: If the header is truncated.
        """
        raw = handle.read(2)
        if len(raw) < 2:
            raise EOFError("truncated SQX header")
        (length,) = struct.unpack(">H", raw)
        return str(handle.read(length).decode("utf-8", errors="replace"))

    version = read_utf()
    data_type = read_utf()
    identifier = read_utf()
    (total_records,) = struct.unpack(">q", handle.read(8))
    (custom_count,) = struct.unpack(">i", handle.read(4))
    for _ in range(custom_count):
        read_utf()
        handle.read(4)
    read_utf()
    if data_type == "C":
        (mod_len,) = struct.unpack(">i", handle.read(4))
        handle.read(mod_len)
    return {
        "version": version,
        "data_type": data_type,
        "identifier": identifier,
        "total_records": total_records,
        "header_length": handle.tell(),
    }


def _to_epoch_ms(value: _Timestamp | None, default: int) -> int:
    """Convert one timestamp parameter to epoch milliseconds.

    Args:
        value: Datetime-like value, epoch seconds/milliseconds, or None.
        default: Value returned when ``value`` is None.

    Returns:
        Epoch milliseconds.
    """
    if value is None:
        return default
    if isinstance(value, (int, np.integer)):
        number = int(value)
        return number if number >= _EPOCH_MS_CUTOFF else number * 1000
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    return int(stamp.timestamp() * 1000)


def _locate_dat_file(
    symbol_or_path: str | Path, timeframe: Literal["M1", "TICK"], *, request_id: str
) -> Path:
    """Locate one ``.dat`` file by symbol name or explicit path.

    Args:
        symbol_or_path: Symbol name (e.g. ``EURUSD``) or direct file path.
        timeframe: Requested data kind.
        request_id: Caller trace identity.

    Returns:
        Resolved existing ``.dat`` path.

    Raises:
        DataError: If no file matches.
    """
    direct = Path(symbol_or_path)
    if direct.is_file():
        return Path(direct)
    root = _resolve_history_root(request_id)
    symbol = direct.stem.upper()
    if timeframe == "TICK":
        candidate = root / symbol / f"{symbol}_TICK.dat"
    else:
        candidate = root / f"{symbol}_M1" / f"{symbol}_M1_M1.dat"
    if candidate.is_file():
        return candidate
    raise DataError("SQX_FILE_NOT_FOUND", request_id=request_id)


def _read_payload(
    path: Path,
    timeframe: Literal["M1", "TICK"],
    start: _Timestamp | None,
    end: _Timestamp | None,
    max_records: int | None,
    request_id: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Read and bound one ``.dat`` payload for decoding.

    Args:
        path: Resolved ``.dat`` file.
        timeframe: Requested data kind.
        start: Optional inclusive start filter.
        end: Optional inclusive end filter.
        max_records: Optional record bound.
        request_id: Caller trace identity.

    Returns:
        Raw payload buffer and parsed header.

    Raises:
        DataError: If the header declares zero records.
    """
    _ = end  # the end bound is applied by the JIT date filter
    _ = request_id  # trace identity reserved for the public wrappers
    with path.open("rb") as handle:
        header = _parse_header(handle)
        payload_bytes = path.stat().st_size - header["header_length"]
        # Some exports omit the record count; estimate from the mean record
        # size instead of failing, mirroring the reference reader.
        declared = header["total_records"]
        if declared <= 0:
            declared = max(100_000, payload_bytes // 12)
        record_bound = (
            min(declared, max_records) if max_records is not None else declared
        )
        # Bounded I/O: without a start filter only the head slice is needed.
        if max_records is not None and start is None:
            bytes_per_record = 30 if timeframe == "M1" else 24
            buffer = np.frombuffer(
                handle.read(min(payload_bytes, max_records * bytes_per_record)),
                dtype=np.uint8,
            )
        else:
            buffer = np.frombuffer(handle.read(), dtype=np.uint8)
    return buffer, {**header, "record_bound": record_bound}


def read_sqx_m1(
    symbol_or_path: str | Path,
    *,
    start: _Timestamp | None = None,
    end: _Timestamp | None = None,
    max_bars: int | None = None,
    request_id: str,
) -> pd.DataFrame:
    """Read SQX M1 bars directly into one UTC-indexed DataFrame.

    Args:
        symbol_or_path: Symbol name (e.g. ``EURUSD``) or ``.dat`` file path.
        start: Optional inclusive start filter.
        end: Optional inclusive end filter.
        max_bars: Optional bar bound.
        request_id: Caller trace identity.

    Returns:
        DataFrame with ``open``/``high``/``low``/``close``/``volume`` columns
        and a UTC ``DatetimeIndex``.

    Raises:
        DataError: If the file cannot be located or is empty.
    """
    logger.info("Reading SQX M1 history for %s", symbol_or_path)
    path = _locate_dat_file(symbol_or_path, "M1", request_id=request_id)
    buffer, header = _read_payload(path, "M1", start, end, max_bars, request_id)
    volume_scale = _M1_VOLUME_SCALE if header["version"] == "4.2" else 100.0
    times, opens, highs, lows, closes, volumes = _decode_m1_records(
        buffer,
        header["record_bound"],
        np.int64(_to_epoch_ms(start, 0)),
        np.int64(_to_epoch_ms(end, 2**62)),
        np.float64(_PRICE_SCALE),
        np.float64(volume_scale),
    )
    if max_bars is not None:
        times, opens, highs, lows, closes, volumes = (
            part[:max_bars] for part in (times, opens, highs, lows, closes, volumes)
        )
    frame = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        },
        index=pd.to_datetime(times, unit="ms", utc=True),
    )
    frame.index.name = "time"
    return frame


def read_sqx_ticks(
    symbol_or_path: str | Path,
    *,
    start: _Timestamp | None = None,
    end: _Timestamp | None = None,
    max_ticks: int | None = None,
    request_id: str,
) -> pd.DataFrame:
    """Read SQX ticks directly into one UTC-indexed DataFrame.

    Args:
        symbol_or_path: Symbol name (e.g. ``EURUSD``) or ``_TICK.dat`` path.
        start: Optional inclusive start filter.
        end: Optional inclusive end filter.
        max_ticks: Optional tick bound.
        request_id: Caller trace identity.

    Returns:
        DataFrame with ``bid``/``ask``/``spread``/``volume`` columns and a
        UTC ``DatetimeIndex``. Spread is the floating ``ask - bid``.

    Raises:
        DataError: If the file cannot be located or is empty.
    """
    logger.info("Reading SQX tick history for %s", symbol_or_path)
    path = _locate_dat_file(symbol_or_path, "TICK", request_id=request_id)
    buffer, header = _read_payload(path, "TICK", start, end, max_ticks, request_id)
    times, bids, asks, volumes = _decode_tick_records(
        buffer,
        header["record_bound"],
        np.int64(_to_epoch_ms(start, 0)),
        np.int64(_to_epoch_ms(end, 2**62)),
        np.float64(_PRICE_SCALE),
        np.float64(_TICK_VOLUME_SCALE),
    )
    if max_ticks is not None:
        times, bids, asks, volumes = (
            part[:max_ticks] for part in (times, bids, asks, volumes)
        )
    frame = pd.DataFrame(
        {
            "bid": bids,
            "ask": asks,
            "spread": np.round(asks - bids, 6),
            "volume": volumes,
        },
        index=pd.to_datetime(times, unit="ms", utc=True),
    )
    frame.index.name = "time"
    return frame


def list_sqx_symbols(*, request_id: str) -> pd.DataFrame:
    """List symbols, timeframes, ranges, and counts from the QDM catalogue.

    Args:
        request_id: Caller trace identity.

    Returns:
        DataFrame with ``symbol``/``instrument``/``timeframe``/``timezone``/
        ``start_date``/``end_date``/``total_records`` columns.

    Raises:
        DataError: If the catalogue query fails.
    """
    logger.info("Listing QuantDataManager symbols")
    database = _resolve_database_path(request_id)
    try:
        rows = read_quantdata_symbol_rows(database, request_id=request_id)
    except sqlite3.Error as error:
        raise DataError("QUANTDATA_ROOT_MISSING", request_id=request_id) from error

    def _as_date(value: object) -> str | None:
        """Convert epoch milliseconds to a UTC ISO date string.

        Args:
            value: Epoch milliseconds or None.

        Returns:
            UTC date string, or None for absent values.
        """
        if value is None or not value:
            return None
        stamp = pd.to_datetime(value, unit="ms", utc=True)
        return str(stamp.strftime("%Y-%m-%d"))

    return pd.DataFrame(
        {
            "symbol": [row["SYMBOL"] for row in rows],
            "instrument": [row["INSTRUMENT"] for row in rows],
            "timeframe": [row["TIMEFRAME"] for row in rows],
            "timezone": [row["TIMEZONE"] for row in rows],
            "start_date": [_as_date(row["DATEFROM"]) for row in rows],
            "end_date": [_as_date(row["DATETO"]) for row in rows],
            "total_records": [int(row["ROWS"] or 0) for row in rows],
        }
    )


__all__ = (
    "list_sqx_symbols",
    "read_sqx_m1",
    "read_sqx_ticks",
)
