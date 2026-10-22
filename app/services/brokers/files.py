"""Local filesystem market data client, partition parsers, and HST/FXT codecs.

Description:
    Implements the local filesystem market data and symbol catalog client
    (`FilesClient`) along with shared delimited (CSV, TSV, semicolon-separated),
    columnar (Parquet), and MetaTrader 4 binary (`HST` v400/v401, `FXT` v405)
    parsers, exporters, and deterministic partition discovery helpers.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local Filesystem Historical Market Data Ingestion and Codecs.

Key Capabilities:
    - FR-BROKER-FILES-PARSING: CSV, Parquet, HST, and FXT Bar and Tick Ingestion
      Associated: `[FilesClient.get_bars()]`, `[FilesClient.get_ticks()]`,
        `parse_delimited_bars()`, `parse_delimited_ticks()`, `read_parquet_bars()`
      Logging: Emits INFO/DEBUG on parsed record counts, and WARNING on absent paths.
    - FR-BROKER-FILES-SYMBOLS: Filesystem Symbol Discovery and Specification Resolution
      Associated: `[FilesClient.get_symbol_info()]`, `[FilesClient.get_symbols()]`,
        `find_matching_partitions()`
      Logging: Emits INFO/DEBUG upon resolving symbol info or partition matches.
    - FR-BROKER-CODECS-HST: Decode and encode MT4 HST files across versions 400 and 401.
      Associated: `decode_hst_bytes()`, `encode_hst_bytes()`
      Logging: Emits DEBUG on detecting HST version, symbol, and record count.
    - FR-BROKER-CODECS-FXT: Decode and encode MT4 FXT tick model files (version 405).
      Associated: `decode_fxt_bytes()`, `encode_fxt_bytes()`
      Logging: Emits DEBUG on parsing FXT header and model records.

Python API Usage:
    ```python
    from app.services.brokers.files import FilesClient, parse_delimited_bars
    from app.services.include.enums import Timeframe

    client = FilesClient(data_dir="data/market")
    bars = client.get_bars("EURUSD", Timeframe.PERIOD_M1, count=5)
    client.disconnect()
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.files
    ```
"""

from __future__ import annotations

import csv
import io
import math
import re
import struct
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa
import pyarrow.parquet as pq
from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    epoch_millis,
    epoch_seconds,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.data import bars_to_dataframe, ticks_to_dataframe
from app.services.include.enums import Timeframe

logger = get_logger(__name__)

PARSING_FR = "FR-BROKER-FILES-PARSING"
SYMBOLS_FR = "FR-BROKER-FILES-SYMBOLS"
DELIMITED_FR = "FR-BROKER-FILES-PARSING-DELIMITED"
PARQUET_FR = "FR-BROKER-FILES-PARSING-PARQUET"
PARTITION_FR = "FR-BROKER-FILES-PARTITION-SELECTION"
HST_FR = "FR-BROKER-CODECS-HST"
FXT_FR = "FR-BROKER-CODECS-FXT"

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

# Compile-time byte-layout verification against canonical MT4 specifications
assert struct.calcsize("<iddddd") == 44, "MT4 HST v400 record must be 44 bytes"
assert struct.calcsize("<qddddqiq") == 60, "MT4 HST v401 record must be 60 bytes"
assert struct.calcsize("<qddddqii") == 56, "MT4 FXT v405 record must be 56 bytes"

__all__ = [
    "FilesClient",
    "decode_fxt_bytes",
    "decode_hst_bytes",
    "encode_fxt_bytes",
    "encode_hst_bytes",
    "export_bars_to_csv",
    "export_bars_to_parquet",
    "find_matching_partitions",
    "load_local_partition_bars",
    "load_local_partition_ticks",
    "main",
    "parse_delimited_bars",
    "parse_delimited_ticks",
    "parse_timestamp_flexible",
    "read_parquet_bars",
]


def parse_timestamp_flexible(val: Any) -> datetime:
    """Parse timestamps across standard ISO-8601, Epoch, and diverse date-time formats."""
    if isinstance(val, datetime):
        return val if val.tzinfo is not None else val.replace(tzinfo=UTC)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(
            val if val < 100_000_000_000 else val / 1000.0, tz=UTC
        )

    s = str(val).strip()
    norm_s = re.sub(r"^(\d{4})\.(\d{2})\.(\d{2})", r"\1-\2-\3", s)
    iso_clean = norm_s.replace("Z", "+00:00").replace("/", "-")
    try:
        dt = datetime.fromisoformat(iso_clean)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    except ValueError:
        pass

    digits = [t for t in re.sub(r"[^\d]", " ", s).split() if t]
    if len(digits) >= 3:
        try:
            yr, mo, dy, hr, mn, sc = (
                int(digits[i]) if len(digits) > i else 0 for i in range(6)
            )
            us = int(digits[6][:6].ljust(6, "0")) if len(digits) > 6 else 0
            return datetime(yr, mo, dy, hr, mn, sc, us, tzinfo=UTC)
        except ValueError, IndexError:
            pass

    raise BridgeError(f"Cannot parse datetime from timestamp value: '{val}'")


def _detect_delimiter(first_line: str) -> str:
    """Detect delimiter among comma, semicolon, and tab."""
    counts = {c: first_line.count(c) for c in (",", ";", "\t")}
    best = max(counts, key=counts.get)  # type: ignore[arg-type]
    return best if counts[best] > 0 else ","


def _find_col(
    headers: list[str], cands: tuple[str, ...], *, required: bool = False
) -> int:
    """Find first matching column index from candidate names."""
    for c in cands:
        clean_c = re.sub(r"[<>]", "", c.lower())
        if clean_c in headers:
            return headers.index(clean_c)
    if required:
        raise BridgeError(
            f"Missing required column among {cands} in headers: {headers}"
        )
    return -1


_BAR_KEYS = (
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
)


def _bar_row(
    t: int, o: float, h: float, l: float, c: float, v: int, sp: int = 0, rv: int = 0
) -> dict[str, Any]:
    """Construct a normalized bar dictionary."""
    return dict(zip(_BAR_KEYS, (t, o, h, l, c, v, sp, rv or v), strict=True))


def parse_delimited_bars(
    content: str, symbol: str = "", timeframe: str = ""
) -> list[dict[str, Any]]:
    """Parse delimited text content into normalized bar records."""
    del timeframe
    if not content or not content.strip():
        return []
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    if not lines:
        return []

    reader = csv.reader(lines, delimiter=_detect_delimiter(lines[0]))
    headers = [re.sub(r"[<>]", "", h.strip().lower()) for h in next(reader)]

    date_idx = _find_col(headers, ("date",))
    time_idx = _find_col(headers, ("time",))
    ts_idx = _find_col(headers, ("timestamp", "datetime", "date_time", "dt"))
    if ts_idx == -1 and not (date_idx != -1 and time_idx != -1):
        if date_idx != -1:
            ts_idx = date_idx
        else:
            raise BridgeError(
                f"Delimited bars file missing timestamp/date column: {headers}"
            )

    o_idx = _find_col(headers, ("open", "o"), required=True)
    h_idx = _find_col(headers, ("high", "h"), required=True)
    l_idx = _find_col(headers, ("low", "l"), required=True)
    c_idx = _find_col(headers, ("close", "c"), required=True)
    v_idx = _find_col(headers, ("volume", "vol", "v", "tick_volume", "tickvol"))
    spread_idx = _find_col(headers, ("spread", "spr"))

    rows: list[dict[str, Any]] = []
    for row in reader:
        if not row or len(row) < 4:
            continue
        try:
            dt_raw = (
                f"{row[date_idx].strip()} {row[time_idx].strip()}"
                if date_idx != -1 and time_idx != -1
                else row[ts_idx].strip()
            )
            dt = parse_timestamp_flexible(dt_raw)
            o_val, h_val, l_val, c_val = (
                float(row[o_idx]),
                float(row[h_idx]),
                float(row[l_idx]),
                float(row[c_idx]),
            )
        except (ValueError, IndexError) as exc:
            raise BridgeError(
                f"Malformed row in delimited bars: {row} ({exc})"
            ) from exc

        if any(math.isnan(x) for x in (o_val, h_val, l_val, c_val)):
            raise BridgeError(f"NaN price detected in bar row: {row}")
        if min(o_val, h_val, l_val, c_val) <= 0:
            raise BridgeError(f"Non-positive price detected in bar row: {row}")
        if h_val < max(o_val, c_val) or l_val > min(o_val, c_val):
            msg = f"Invalid OHLC relationship in row: open={o_val}, high={h_val}, low={l_val}, close={c_val}"
            raise BridgeError(msg)

        vol_val = float(row[v_idx]) if 0 <= v_idx < len(row) else 1.0
        spread_val = float(row[spread_idx]) if 0 <= spread_idx < len(row) else 0.0
        v_clean = int(vol_val) if vol_val >= 1.0 else (1 if vol_val > 0 else 0)
        t_sec = int(dt.timestamp())
        sp_int = int(spread_val)
        rows.append(
            _bar_row(t_sec, o_val, h_val, l_val, c_val, v_clean, sp_int, v_clean)
        )

    logger.debug(
        "%s: Parsed %d bars from delimited content for %s",
        DELIMITED_FR,
        len(rows),
        symbol,
        extra={"fr_id": DELIMITED_FR, "rows": len(rows), "symbol": symbol},
    )
    return rows


def parse_delimited_ticks(content: str, symbol: str = "") -> list[dict[str, Any]]:
    """Parse delimited text content into normalized tick records."""
    if not content or not content.strip():
        return []
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    if not lines:
        return []

    reader = csv.reader(lines, delimiter=_detect_delimiter(lines[0]))
    headers = [re.sub(r"[<>]", "", h.strip().lower()) for h in next(reader)]

    ts_idx = _find_col(headers, ("timestamp", "time", "datetime", "date", "date_time"))
    if ts_idx == -1:
        raise BridgeError(f"Missing timestamp column in tick headers: {headers}")

    bid_idx = _find_col(headers, ("bid", "bid_price"))
    ask_idx = _find_col(headers, ("ask", "ask_price"))
    price_idx = -1
    if bid_idx == -1 and ask_idx == -1:
        price_idx = _find_col(headers, ("price", "last", "close"))
        if price_idx == -1:
            raise BridgeError(f"Tick file requires bid/ask or price columns: {headers}")
    vol_idx = _find_col(headers, ("volume", "vol", "size", "qty", "quantity"))

    rows: list[dict[str, Any]] = []
    for row in reader:
        if not row:
            continue
        try:
            ts_ms = int(
                parse_timestamp_flexible(row[ts_idx].strip()).timestamp() * 1000.0
            )
            if bid_idx != -1 and ask_idx != -1:
                bid_val, ask_val = float(row[bid_idx]), float(row[ask_idx])
                last_val = (bid_val + ask_val) / 2.0
            else:
                last_val = float(row[price_idx])
                bid_val = ask_val = last_val
            vol_val = float(row[vol_idx]) if 0 <= vol_idx < len(row) else 1.0
        except (ValueError, IndexError) as exc:
            raise BridgeError(
                f"Malformed row in delimited ticks: {row} ({exc})"
            ) from exc

        if any(math.isnan(x) for x in (bid_val, ask_val, last_val)):
            raise BridgeError(f"NaN price in tick row: {row}")
        if min(bid_val, ask_val, last_val) <= 0:
            raise BridgeError(f"Non-positive price in tick row: {row}")
        if bid_val > ask_val:
            raise BridgeError(f"Bid price exceeds ask price in tick row: {row}")

        vol_clean = int(vol_val) if vol_val.is_integer() else float(vol_val)
        rows.append(
            dict(
                zip(
                    (
                        "time_msc",
                        "bid",
                        "ask",
                        "last",
                        "volume",
                        "flags",
                        "volume_real",
                    ),
                    (ts_ms, bid_val, ask_val, last_val, vol_clean, 0, float(vol_val)),
                    strict=True,
                )
            )
        )

    logger.debug(
        "%s: Parsed %d ticks from delimited content for %s",
        DELIMITED_FR,
        len(rows),
        symbol,
        extra={"fr_id": DELIMITED_FR, "rows": len(rows), "symbol": symbol},
    )
    return rows


def read_parquet_bars(
    path: Path | str, count: int | None = None
) -> list[dict[str, Any]]:
    """Read historical bars from a Parquet file."""
    p = Path(path)
    if not p.is_file():
        return []

    df = pq.read_table(p).to_pandas()
    if df.empty:
        return []
    df.columns = [str(c).lower().strip() for c in df.columns]
    if count is not None and count > 0 and len(df) > count:
        df = df.iloc[-count:]

    ts_col = next((c for c in ("timestamp", "time", "datetime") if c in df.columns), "")
    if not ts_col or "open" not in df.columns:
        return []

    opens, highs, lows, closes = (
        [float(x) for x in df[k]] for k in ("open", "high", "low", "close")
    )
    timestamps = [int(parse_timestamp_flexible(x).timestamp()) for x in df[ts_col]]

    vol_col = next((c for c in ("volume", "tick_volume") if c in df.columns), None)
    vols = (
        [int(x) if x >= 1.0 else (1 if x > 0 else 0) for x in df[vol_col].astype(float)]
        if vol_col
        else [1] * len(df)
    )
    spreads = (
        [int(x or 0) for x in df["spread"].astype(float)]
        if "spread" in df.columns
        else [0] * len(df)
    )
    rvols = (
        [
            int(x) if x >= 1.0 else (1 if x > 0 else 0)
            for x in df["real_volume"].astype(float)
        ]
        if "real_volume" in df.columns
        else vols
    )

    rows: list[dict[str, Any]] = [
        _bar_row(t, o, h, l, c, v, sp, rv)
        for t, o, h, l, c, v, sp, rv in zip(
            timestamps, opens, highs, lows, closes, vols, spreads, rvols, strict=False
        )
    ]
    logger.debug(
        "%s: Read %d Parquet bars from %s",
        PARQUET_FR,
        len(rows),
        p.name,
        extra={"fr_id": PARQUET_FR, "rows": len(rows), "path": str(p)},
    )
    return rows


def decode_hst_bytes(data: bytes, count: int | None = None) -> list[dict[str, Any]]:
    """Decode MetaTrader 4 HST binary files (version 400 or 401)."""
    if len(data) < 148:
        raise BridgeError("HST file too small to contain valid 148-byte header")

    version, _raw_cr, raw_sym, period, digits = struct.unpack_from(
        "<i64s12sii", data, 0
    )
    if version not in (400, 401):
        raise BridgeError(f"Unsupported HST version: {version}")

    rec_size = 44 if version == 400 else 60
    payload_len = len(data) - 148
    if payload_len % rec_size != 0:
        msg = f"HST file contains truncated records: {payload_len} bytes not divisible by record size {rec_size}"
        raise BridgeError(msg)

    symbol = raw_sym.split(b"\x00")[0].decode("ascii", errors="replace").strip()
    logger.debug(
        "%s: Decoding HST for %s (version=%d, period=%d, digits=%d)",
        HST_FR,
        symbol,
        version,
        period,
        digits,
        extra={"fr_id": HST_FR, "symbol": symbol, "version": version},
    )

    offset = 148
    rows: list[dict[str, Any]] = []
    num_records = payload_len // rec_size
    max_recs = (
        min(num_records, count) if count is not None and count > 0 else num_records
    )

    for _ in range(max_recs):
        if version == 400:
            ctm, o, l, h, c, v = struct.unpack_from("<iddddd", data, offset)
            vol, spread, rvol = int(v), 0, int(v)
        else:
            ctm, o, h, l, c, vol_raw, spread, rvol_raw = struct.unpack_from(
                "<qddddqiq", data, offset
            )
            vol, spread, rvol = int(vol_raw), int(spread), int(rvol_raw)
        offset += rec_size
        rows.append(
            _bar_row(
                int(ctm), float(o), float(h), float(l), float(c), vol, spread, rvol
            )
        )
    return rows


def encode_hst_bytes(
    rows: list[dict[str, Any]],
    symbol: str,
    period: int = 1,
    digits: int = 5,
    version: int = 401,
) -> bytes:
    """Encode market bars into MetaTrader 4 HST format."""
    if version not in (400, 401):
        raise BridgeError(f"Unsupported encode HST version: {version}")
    hdr = struct.pack(
        "<i64s12siiii52s",
        version,
        b"HaruQuantAI MT4 Codec",
        symbol.encode("ascii")[:11],
        period,
        digits,
        int(datetime.now(tz=UTC).timestamp()),
        0,
        b"\x00" * 52,
    )
    buf = io.BytesIO()
    buf.write(hdr)
    for r in rows:
        t = int(r["time"])
        o, h, l, c = (
            float(r["open"]),
            float(r["high"]),
            float(r["low"]),
            float(r["close"]),
        )
        v = r.get("tick_volume", 1)
        packed = (
            struct.pack("<iddddd", t, o, l, h, c, float(v))
            if version == 400
            else struct.pack(
                "<qddddqiq",
                t,
                o,
                h,
                l,
                c,
                int(v),
                int(r.get("spread", 0)),
                int(r.get("real_volume", 1)),
            )
        )
        buf.write(packed)
    return buf.getvalue()


def decode_fxt_bytes(data: bytes, count: int | None = None) -> list[dict[str, Any]]:
    """Decode MetaTrader 4 FXT testing files (version 405)."""
    if len(data) < 724:
        raise BridgeError("FXT file too small to contain valid header")

    version, _raw_desc, _raw_srv, raw_sym, period, _model, bars_count = (
        struct.unpack_from("<i64s128s16siii", data, 0)
    )
    if version != 405:
        raise BridgeError(f"Unsupported FXT version: {version}")

    rec_size = 56
    if len(data) >= 728 and (len(data) - 728) % rec_size == 0:
        offset = 728
    elif len(data) >= 724 and (len(data) - 724) % rec_size == 0:
        offset = 724
    else:
        msg = f"FXT file contains truncated records: length {len(data)} does not match 724/728 + N*{rec_size}"
        raise BridgeError(msg)

    symbol = raw_sym.split(b"\x00")[0].decode("ascii", errors="replace").strip()
    logger.debug(
        "%s: Decoding FXT for %s (version=%d, period=%d, bars=%d)",
        FXT_FR,
        symbol,
        version,
        period,
        bars_count,
        extra={"fr_id": FXT_FR, "symbol": symbol, "version": version},
    )

    num_recs = (len(data) - offset) // rec_size
    max_recs = min(num_recs, count) if count is not None and count > 0 else num_recs
    keys = ("time", "open", "high", "low", "close", "volume", "tick_time", "flag")
    types = (int, float, float, float, float, int, int, int)
    rows: list[dict[str, Any]] = []
    for _ in range(max_recs):
        vals = struct.unpack_from("<qddddqii", data, offset)
        offset += rec_size
        rows.append({k: fn(v) for k, fn, v in zip(keys, types, vals, strict=True)})
    return rows


def encode_fxt_bytes(
    rows: list[dict[str, Any]], symbol: str, period: int = 1, version: int = 405
) -> bytes:
    """Encode market bars into MetaTrader 4 FXT format."""
    t0 = int(rows[0]["time"]) if rows else 0
    t1 = int(rows[-1]["time"]) if rows else 0
    sym_b = symbol.encode("ascii")[:15]
    hdr = struct.pack(
        "<i64s128s16siiiii492s",
        version,
        b"HaruQuantAI FXT Codec",
        b"MetaQuotes-Demo",
        sym_b,
        period,
        0,
        len(rows),
        t0,
        t1,
        b"\x00" * 492,
    )
    buf = io.BytesIO()
    buf.write(hdr)
    for r in rows:
        t = int(r["time"])
        o, h, l, c = (
            float(r["open"]),
            float(r["high"]),
            float(r["low"]),
            float(r["close"]),
        )
        v, tt, fl = (
            int(r.get("volume", 1)),
            int(r.get("tick_time", t)),
            int(r.get("flag", 1)),
        )
        buf.write(struct.pack("<qddddqii", t, o, h, l, c, v, tt, fl))
    return buf.getvalue()


_PARTITION_EXTS = (".parquet", ".csv", ".tsv", ".txt", ".dat", ".hst", ".fxt", ".bi5")


def find_matching_partitions(
    data_dir: Path,
    symbol: str,
    timeframe: str,
    extensions: tuple[str, ...] = _PARTITION_EXTS,
) -> list[Path]:
    """Find matching data files with exact symbol boundary matching to avoid collisions."""
    if not data_dir.exists():
        return []
    clean_sym, clean_tf = symbol.strip().upper(), timeframe.strip().upper()
    matches: list[Path] = []
    for f in data_dir.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in extensions:
            continue
        parts = re.split(r"[_.\-]", f.stem.upper())
        if not parts:
            continue
        file_sym = parts[0]
        parent_sym = f.parent.name.upper() if f.parent != data_dir else ""
        if file_sym != clean_sym and parent_sym != clean_sym:
            continue
        if (
            file_sym == clean_sym
            and len(parts) > 1
            and clean_tf
            and parts[1] != clean_tf
        ):
            continue
        matches.append(f)

    matches.sort(key=lambda p: p.name)
    logger.debug(
        "%s: Found %d partition files for %s %s in %s",
        PARTITION_FR,
        len(matches),
        clean_sym,
        clean_tf,
        str(data_dir),
        extra={"fr_id": PARTITION_FR, "matches": len(matches), "symbol": clean_sym},
    )
    return matches


def _dedup_and_trim(
    rows: list[dict[str, Any]], key: str, target_count: int
) -> list[dict[str, Any]]:
    """Sort records ascending by timestamp key, deduplicate, and trim to target_count."""
    rows.sort(key=lambda r: r[key])
    deduped: list[dict[str, Any]] = []
    last_t: int | None = None
    for r in rows:
        if last_t is None or r[key] > last_t:
            deduped.append(r)
            last_t = r[key]
    if target_count and len(deduped) > target_count:
        return deduped[-target_count:]
    return deduped


def load_local_partition_bars(
    files: list[Path],
    symbol: str,
    timeframe: str,
    start: int = 0,
    end: int = 0,
    count: int = 0,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Load, decode, aggregate, filter, and sort bar records from local partition files."""
    target = count if count > 0 else limit
    d_from = datetime.fromtimestamp(start, tz=UTC) if 0 < start < 2**40 else None
    d_to = datetime.fromtimestamp(end, tz=UTC) if 0 < end < 2**40 else None
    tail_only = not d_from and not d_to and bool(target)
    rows: list[dict[str, Any]] = []

    for fp in reversed(files) if tail_only else files:
        batch: list[dict[str, Any]] = []
        if fp.suffix == ".parquet":
            batch = read_parquet_bars(fp, count=target if tail_only else None)
        elif fp.suffix == ".hst":
            batch = decode_hst_bytes(fp.read_bytes())
        elif fp.suffix == ".fxt":
            batch = decode_fxt_bytes(fp.read_bytes())
        elif fp.suffix in (".csv", ".txt", ".tsv"):
            txt = fp.read_text(encoding="utf-8", errors="replace")
            batch = parse_delimited_bars(txt, symbol=symbol, timeframe=timeframe)
        else:
            logger.warning(
                "%s: Skipping unsupported bar file format: %s", PARTITION_FR, fp.suffix
            )
        rows = (batch + rows) if tail_only else [*rows, *batch]
        if tail_only and len(rows) >= target:
            break

    filtered = [
        r
        for r in rows
        if (not d_from or datetime.fromtimestamp(r["time"], tz=UTC) >= d_from)
        and (not d_to or datetime.fromtimestamp(r["time"], tz=UTC) <= d_to)
    ]
    return _dedup_and_trim(filtered, "time", target)


def load_local_partition_ticks(
    files: list[Path],
    symbol: str,
    start_ms: int = 0,
    end_ms: int = 0,
    count: int = 0,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Load, decode, aggregate, filter, and sort tick records from local partition files."""
    target = count if count > 0 else limit
    tail_only = start_ms <= 0 and end_ms <= 0 and bool(target)
    rows: list[dict[str, Any]] = []

    for fp in reversed(files) if tail_only else files:
        batch: list[dict[str, Any]] = []
        if fp.suffix == ".parquet":
            batch = pq.read_table(fp).to_pylist()
        elif fp.suffix in (".csv", ".txt", ".tsv"):
            txt = fp.read_text(encoding="utf-8", errors="replace")
            batch = parse_delimited_ticks(txt, symbol=symbol)
        else:
            logger.warning(
                "%s: Skipping unsupported tick file format: %s", PARTITION_FR, fp.suffix
            )
        rows = (batch + rows) if tail_only else [*rows, *batch]
        if tail_only and len(rows) >= target:
            break

    filtered = [
        r
        for r in rows
        if (start_ms <= 0 or r["time_msc"] >= start_ms)
        and (end_ms <= 0 or r["time_msc"] <= end_ms)
    ]
    return _dedup_and_trim(filtered, "time_msc", target)


def export_bars_to_csv(rows: list[dict[str, Any]], target_path: Path | str) -> None:
    """Export normalized bar rows to a standard CSV file."""
    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["timestamp", "open", "high", "low", "close", "volume", "spread"]
        )
        for r in rows:
            ts = parse_timestamp_flexible(r.get("timestamp", r.get("time"))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            prices = [f"{r[k]:.6f}" for k in ("open", "high", "low", "close")]
            writer.writerow(
                [
                    ts,
                    *prices,
                    r.get("tick_volume", r.get("volume", 1)),
                    r.get("spread", 0),
                ]
            )


def export_bars_to_parquet(rows: list[dict[str, Any]], target_path: Path | str) -> None:
    """Export normalized bar rows to a standard Parquet file."""
    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "timestamp": [
            parse_timestamp_flexible(r.get("timestamp", r.get("time"))) for r in rows
        ],
        **{k: [float(r[k]) for r in rows] for k in ("open", "high", "low", "close")},
        "volume": [float(r.get("tick_volume", r.get("volume", 1))) for r in rows],
        "spread": [float(r.get("spread", 0)) for r in rows],
    }
    pq.write_table(pa.Table.from_pandas(pd.DataFrame(data)), p)


class FilesClient(BrokerClient):
    """Local filesystem market data and symbol catalog client."""

    def __init__(self, name: str = "Files", data_dir: str | Path | None = None) -> None:
        """Initialize Files broker client."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._connected = True

    def _scan_catalog(self) -> dict[str, list[Path]]:
        """Index symbols dynamically by discovering files."""
        catalog: dict[str, list[Path]] = {}
        if not self.data_dir.exists():
            return catalog
        for ext in ("*.parquet", "*.csv", "*.txt", "*.hst", "*.fxt", "*.tsv"):
            for p in self.data_dir.rglob(ext):
                raw_sym = p.stem.upper()
                for token in ("_M1", "_D1", "_H1", "_TICK", "_TICKS", "_BARS"):
                    raw_sym = raw_sym.replace(token, "")
                clean_sym = raw_sym.split(".")[0]
                if clean_sym:
                    catalog.setdefault(clean_sym, []).append(p)
        return catalog

    def _find_symbol_files(
        self, symbol: str, timeframe: str | None = None
    ) -> list[Path]:
        """Find data files associated with symbol."""
        sym_clean = re.sub(r"[/_\-]", "", symbol.lower())
        matches: list[Path] = []
        if not self.data_dir.exists():
            return matches

        tf_token = timeframe.lower().strip() if timeframe else None
        for ext in ("*.parquet", "*.csv", "*.txt", "*.hst", "*.fxt", "*.tsv"):
            for p in self.data_dir.rglob(ext):
                name_clean = re.sub(r"[/_\-]", "", p.stem.lower())
                parent_clean = re.sub(r"[/_\-]", "", p.parent.name.lower())
                if sym_clean in name_clean or sym_clean == parent_clean:
                    matches.append(p)
        if not matches:
            return []
        if tf_token:
            tf_matches = [
                p
                for p in matches
                if tf_token in p.name.lower()
                or tf_token in [x.lower() for x in p.parts]
            ]
            if tf_matches:
                return sorted(tf_matches)
        return sorted(matches)

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve symbol metadata as canonical SymbolInfo."""
        sym_upper = symbol.upper()
        logger.info(
            "%s: Resolved symbol info for %s",
            SYMBOLS_FR,
            sym_upper,
            extra={"fr_id": SYMBOLS_FR, "symbol": sym_upper},
        )
        return SymbolInfo(
            name=sym_upper, custom=True, digits=2, point=0.01, trade_contract_size=1.0
        )

    @override
    def get_symbols(self) -> list[str]:
        """Return list of distinct symbol names discovered in filesystem."""
        symbols = sorted(self._scan_catalog().keys())
        logger.info(
            "%s: Discovered %d symbols in filesystem catalog",
            SYMBOLS_FR,
            len(symbols),
            extra={"fr_id": SYMBOLS_FR, "count": len(symbols)},
        )
        return symbols

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Retrieve historical candlestick bars from local files."""
        del start_pos
        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else timeframe
        files = find_matching_partitions(
            self.data_dir, symbol, tf_name
        ) or self._find_symbol_files(symbol, timeframe=tf_name)
        if not files:
            logger.warning(
                "%s: No files found for %s %s in %s",
                PARSING_FR,
                symbol,
                tf_name,
                self.data_dir,
                extra={"fr_id": PARSING_FR, "symbol": symbol, "timeframe": tf_name},
            )
            raise BridgeError(
                f"No local files found for symbol '{symbol}' in {self.data_dir}",
                code="FILE_NOT_FOUND",
            )

        start_sec = epoch_seconds(date_from if date_from is not None else start)
        end_sec = epoch_seconds(date_to if date_to is not None else end)
        try:
            deduped = load_local_partition_bars(
                files, symbol, tf_name, start_sec, end_sec, count or 0, limit
            )
            logger.info(
                "%s: Parsed %d bars for %s %s from %d partition file(s)",
                PARSING_FR,
                len(deduped),
                symbol,
                tf_name,
                len(files),
                extra={"fr_id": PARSING_FR, "count": len(deduped), "symbol": symbol},
            )
            return bars_to_dataframe(
                [
                    MarketBar(
                        int(r["time"]),
                        float(r["open"]),
                        float(r["high"]),
                        float(r["low"]),
                        float(r["close"]),
                        int(r.get("tick_volume", 0)),
                        int(r.get("spread", 0)),
                        int(r.get("real_volume", 0)),
                    )
                    for r in deduped
                ]
            )
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse bars for {symbol}: {exc}", code="READ_ERROR"
            ) from exc

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Retrieve historical ticks from local files."""
        files = (
            find_matching_partitions(self.data_dir, symbol, "tick")
            or self._find_symbol_files(symbol, timeframe="tick")
            or self._find_symbol_files(symbol)
        )
        if not files:
            raise BridgeError(
                f"No local files found for symbol '{symbol}'", code="FILE_NOT_FOUND"
            )

        start_ms = epoch_millis(date_from if date_from is not None else start)
        end_ms = epoch_millis(date_to if date_to is not None else end)
        try:
            deduped = load_local_partition_ticks(
                files, symbol, start_ms, end_ms, count or 0, limit
            )
            logger.info(
                "%s: Parsed %d ticks for %s from %d partition file(s)",
                PARSING_FR,
                len(deduped),
                symbol,
                len(files),
                extra={"fr_id": PARSING_FR, "count": len(deduped), "symbol": symbol},
            )
            return ticks_to_dataframe(
                [
                    MarketTick(
                        int(t["time_msc"]),
                        float(t["bid"]),
                        float(t["ask"]),
                        float(t.get("last", t["bid"])),
                        int(t.get("volume", 1)),
                        int(t.get("flags", 0)),
                        float(t.get("volume_real", 1.0)),
                    )
                    for t in deduped
                ]
            )
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Failed to parse ticks for {symbol}: {exc}", code="READ_ERROR"
            ) from exc


def main() -> None:
    """Demonstrate executable usage of FilesClient."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "EURUSD_M1.csv"
        csv_file.write_text(
            "timestamp,open,high,low,close,volume\n"
            "2026-01-01 00:00:00,1.1000,1.1010,1.0990,1.1005,100\n",
            encoding="utf-8",
        )
        client = FilesClient(data_dir=tmp_path)
        bars = client.get_bars("EURUSD", "M1", count=10)
        assert isinstance(bars, pd.DataFrame)
        logger.info("Read %d bars from %s", len(bars), csv_file.name)
        client.disconnect()


if __name__ == "__main__":
    main()
