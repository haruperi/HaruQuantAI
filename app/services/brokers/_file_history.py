"""Shared filesystem historical data parsers, partition selectors, and export codecs.

Description:
    Provides robust delimited (CSV, TSV, semicolon-separated) and columnar (Parquet)
    file parsers, multi-partition directory scanners, and canonical record normalizers
    for local historical data. Resolves partitioned files deterministically without
    substring symbol collisions, handles separated Date and Time columns (MetaTrader format),
    conforms to both workspace lowercase and legacy schemas, and exports normalized
    bars and ticks.

Purpose:
    FEAT-BROKER-FILES-SHARED: Shared filesystem historical data parsing and partition resolution.

Key Capabilities:
    - FR-BROKER-FILES-PARSING-DELIMITED: Parse comma/semicolon/tab delimited bars and ticks.
      Associated: `parse_delimited_bars()`, `parse_delimited_ticks()`
      Logging: Emits DEBUG on parsing records and reporting detected delimiter/columns.
    - FR-BROKER-FILES-PARSING-PARQUET: High-speed vectorized Parquet partition ingestion.
      Associated: `read_parquet_bars()`, `export_bars_to_parquet()`
      Logging: Emits DEBUG when reading Arrow/Parquet tables with row counts.
    - FR-BROKER-FILES-PARTITION-SELECTION: Deterministic exact symbol partition discovery.
      Associated: `find_matching_partitions()`
      Logging: Emits DEBUG when listing matching data partitions.

Python API Usage:
    ```python
    from app.services.brokers._file_history import parse_delimited_bars

    rows = parse_delimited_bars(csv_text, "EURUSD", "M1")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_binary_and_file_codecs.py --no-cov
    ```
"""

from __future__ import annotations

import csv
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa
import pyarrow.parquet as pq
from app.host.logging import get_logger
from app.services.brokers.capabilities import ProviderValidationError

logger = get_logger(__name__)

DELIMITED_FR = "FR-BROKER-FILES-PARSING-DELIMITED"
PARQUET_FR = "FR-BROKER-FILES-PARSING-PARQUET"
PARTITION_FR = "FR-BROKER-FILES-PARTITION-SELECTION"

__all__ = [
    "export_bars_to_csv",
    "export_bars_to_parquet",
    "find_matching_partitions",
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
    # Normalize YYYY.MM.DD to YYYY-MM-DD for standard parsing
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
            year = int(digits[0])
            month = int(digits[1])
            day = int(digits[2])
            hour = int(digits[3]) if len(digits) > 3 else 0
            minute = int(digits[4]) if len(digits) > 4 else 0
            second = int(digits[5]) if len(digits) > 5 else 0
            microsecond = int(digits[6][:6].ljust(6, "0")) if len(digits) > 6 else 0
            return datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                microsecond,
                tzinfo=UTC,
            )
        except ValueError, IndexError:
            pass

    raise ProviderValidationError(
        f"Cannot parse datetime from timestamp value: '{val}'"
    )


def _detect_delimiter(first_line: str) -> str:
    """Detect delimiter among comma, semicolon, and tab."""
    counts = {
        ",": first_line.count(","),
        ";": first_line.count(";"),
        "\t": first_line.count("\t"),
    }
    best = max(counts, key=counts.get)  # type: ignore[arg-type]
    return best if counts[best] > 0 else ","


def parse_delimited_bars(
    content: str,
    symbol: str = "",
    timeframe: str = "",
) -> list[dict[str, Any]]:
    """Parse delimited text content into normalized bar records."""
    _ = (symbol, timeframe)
    if not content or not content.strip():
        return []

    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    if not lines:
        return []

    delim = _detect_delimiter(lines[0])
    reader = csv.reader(lines, delimiter=delim)
    raw_headers = next(reader)
    # Strip angle brackets (e.g. <DATE>, <TIME>, <OPEN>) for MT5 exports and normalize
    headers = [re.sub(r"[<>]", "", h.strip().lower()) for h in raw_headers]

    has_date = "date" in headers
    has_time = "time" in headers
    has_ts = any(h in headers for h in ("timestamp", "datetime", "date_time", "dt"))

    if not has_ts and not (has_date and has_time):
        if has_date:
            has_ts = True
            ts_idx = headers.index("date")
        else:
            raise ProviderValidationError(
                f"Delimited bars file missing timestamp/date column: {headers}"
            )
    else:
        ts_idx = headers.index("timestamp") if "timestamp" in headers else -1
        if ts_idx == -1:
            for cand in ("datetime", "date_time", "dt"):
                if cand in headers:
                    ts_idx = headers.index(cand)
                    break

    date_idx = headers.index("date") if has_date else -1
    time_idx = headers.index("time") if has_time else -1

    def find_col(cands: tuple[str, ...]) -> int:
        for c in cands:
            clean_c = re.sub(r"[<>]", "", c.lower())
            if clean_c in headers:
                return headers.index(clean_c)
        raise ProviderValidationError(
            f"Missing required price column among {cands} in headers: {headers}"
        )

    o_idx = find_col(("open", "o"))
    h_idx = find_col(("high", "h"))
    l_idx = find_col(("low", "l"))
    c_idx = find_col(("close", "c"))

    v_idx = -1
    for c in ("volume", "vol", "v", "tick_volume", "tickvol"):
        if c in headers:
            v_idx = headers.index(c)
            break

    spread_idx = -1
    for c in ("spread", "spr"):
        if c in headers:
            spread_idx = headers.index(c)
            break

    rows: list[dict[str, Any]] = []
    for row in reader:
        if not row or len(row) < 4:
            continue
        try:
            if has_date and has_time and date_idx != -1 and time_idx != -1:
                dt_str = f"{row[date_idx].strip()} {row[time_idx].strip()}"
                dt = parse_timestamp_flexible(dt_str)
            else:
                dt = parse_timestamp_flexible(row[ts_idx].strip())

            o_val = float(row[o_idx])
            h_val = float(row[h_idx])
            l_val = float(row[l_idx])
            c_val = float(row[c_idx])
        except (ValueError, IndexError) as exc:
            raise ProviderValidationError(
                f"Malformed row in delimited bars: {row} ({exc})"
            ) from exc

        if (
            math.isnan(o_val)
            or math.isnan(h_val)
            or math.isnan(l_val)
            or math.isnan(c_val)
        ):
            raise ProviderValidationError(f"NaN price detected in bar row: {row}")
        if o_val <= 0 or h_val <= 0 or l_val <= 0 or c_val <= 0:
            raise ProviderValidationError(
                f"Non-positive price detected in bar row: {row}"
            )
        if h_val < max(o_val, c_val) or l_val > min(o_val, c_val):
            raise ProviderValidationError(
                f"Invalid OHLC relationship in row: open={o_val}, high={h_val}, low={l_val}, close={c_val}"
            )

        vol_val = float(row[v_idx]) if v_idx != -1 and v_idx < len(row) else 1.0
        spread_val = (
            float(row[spread_idx])
            if spread_idx != -1 and spread_idx < len(row)
            else 0.0
        )
        vol_clean: int | float = (
            int(vol_val) if vol_val.is_integer() else float(vol_val)
        )

        rows.append(
            {
                "time": int(dt.timestamp()),
                "open": o_val,
                "high": h_val,
                "low": l_val,
                "close": c_val,
                "tick_volume": vol_clean,
                "spread": int(spread_val),
                "real_volume": float(vol_val),
            }
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

    delim = _detect_delimiter(lines[0])
    reader = csv.reader(lines, delimiter=delim)
    raw_headers = next(reader)
    headers = [re.sub(r"[<>]", "", h.strip().lower()) for h in raw_headers]

    ts_idx = -1
    for c in ("timestamp", "time", "datetime", "date", "date_time"):
        if c in headers:
            ts_idx = headers.index(c)
            break
    if ts_idx == -1:
        raise ProviderValidationError(
            f"Missing timestamp column in tick headers: {headers}"
        )

    bid_idx = -1
    ask_idx = -1
    for c in ("bid", "bid_price"):
        if c in headers:
            bid_idx = headers.index(c)
            break
    for c in ("ask", "ask_price"):
        if c in headers:
            ask_idx = headers.index(c)
            break

    price_idx = -1
    if bid_idx == -1 and ask_idx == -1:
        for c in ("price", "last", "close"):
            if c in headers:
                price_idx = headers.index(c)
                break
        if price_idx == -1:
            raise ProviderValidationError(
                f"Tick file requires bid/ask or price columns: {headers}"
            )

    vol_idx = -1
    for c in ("volume", "vol", "size", "qty", "quantity"):
        if c in headers:
            vol_idx = headers.index(c)
            break

    rows: list[dict[str, Any]] = []
    for row in reader:
        if not row:
            continue
        try:
            dt = parse_timestamp_flexible(row[ts_idx].strip())
            ts_ms = int(dt.timestamp() * 1000.0)

            if bid_idx != -1 and ask_idx != -1:
                bid_val = float(row[bid_idx])
                ask_val = float(row[ask_idx])
                last_val = (bid_val + ask_val) / 2.0
            else:
                last_val = float(row[price_idx])
                bid_val = last_val
                ask_val = last_val

            vol_val = (
                float(row[vol_idx]) if vol_idx != -1 and vol_idx < len(row) else 1.0
            )
        except (ValueError, IndexError) as exc:
            raise ProviderValidationError(
                f"Malformed row in delimited ticks: {row} ({exc})"
            ) from exc

        if math.isnan(bid_val) or math.isnan(ask_val) or math.isnan(last_val):
            raise ProviderValidationError(f"NaN price in tick row: {row}")
        if bid_val <= 0 or ask_val <= 0 or last_val <= 0:
            raise ProviderValidationError(f"Non-positive price in tick row: {row}")
        if bid_val > ask_val:
            raise ProviderValidationError(
                f"Bid price exceeds ask price in tick row: {row}"
            )

        vol_clean = int(vol_val) if vol_val.is_integer() else float(vol_val)
        rows.append(
            {
                "time_msc": ts_ms,
                "bid": bid_val,
                "ask": ask_val,
                "last": last_val,
                "volume": vol_clean,
                "flags": 0,
                "volume_real": float(vol_val),
            }
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

    table = pq.read_table(p)
    df = table.to_pandas()
    if df.empty:
        return []

    rows: list[dict[str, Any]] = []
    target_count = min(len(df), count) if count is not None and count > 0 else len(df)

    for i in range(target_count):
        row_s = df.iloc[i]
        ts_val = row_s["timestamp"] if "timestamp" in row_s else row_s.get("time")
        dt = parse_timestamp_flexible(ts_val)
        rows.append(
            {
                "time": int(dt.timestamp()),
                "open": float(row_s["open"]),
                "high": float(row_s["high"]),
                "low": float(row_s["low"]),
                "close": float(row_s["close"]),
                "tick_volume": int(row_s.get("volume", row_s.get("tick_volume", 1))),
                "spread": int(row_s.get("spread", 0)),
                "real_volume": int(row_s.get("real_volume", row_s.get("volume", 1))),
            }
        )

    logger.debug(
        "%s: Read %d Parquet bars from %s",
        PARQUET_FR,
        len(rows),
        p.name,
        extra={"fr_id": PARQUET_FR, "rows": len(rows), "path": str(p)},
    )
    return rows


def find_matching_partitions(
    data_dir: Path,
    symbol: str,
    timeframe: str,
    extensions: tuple[str, ...] = (
        ".parquet",
        ".csv",
        ".tsv",
        ".txt",
        ".dat",
        ".hst",
        ".fxt",
        ".bi5",
    ),
) -> list[Path]:
    """Find matching data files with exact symbol boundary matching to avoid collisions."""
    if not data_dir.exists():
        return []

    clean_sym = symbol.strip().upper()
    clean_tf = timeframe.strip().upper()

    matches: list[Path] = []
    # Direct file match or letter partition match
    for f in data_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in extensions:
            continue

        stem = f.stem.upper()
        # Ensure exact symbol prefix or boundary
        # Valid stems: "EURUSD", "EURUSD_M1", "EURUSD_D1", "EURUSD-M1", "EURUSD.M1"
        # Invalid stems: "EURUSD_EXTRA", "XEURUSD"
        parts = re.split(r"[_.\-]", stem)
        if not parts:
            continue
        file_sym = parts[0]
        parent_sym = f.parent.name.upper() if f.parent != data_dir else ""
        if file_sym != clean_sym and parent_sym != clean_sym:
            continue

        if file_sym == clean_sym and len(parts) > 1:
            file_tf = parts[1]
            if clean_tf and file_tf != clean_tf:
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
            ts_val = r.get("timestamp", r.get("time"))
            dt = parse_timestamp_flexible(ts_val)
            ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(
                [
                    ts_str,
                    f"{r['open']:.6f}",
                    f"{r['high']:.6f}",
                    f"{r['low']:.6f}",
                    f"{r['close']:.6f}",
                    r.get("tick_volume", r.get("volume", 1)),
                    r.get("spread", 0),
                ]
            )


def export_bars_to_parquet(rows: list[dict[str, Any]], target_path: Path | str) -> None:
    """Export normalized bar rows to a standard Parquet file."""
    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    timestamps = [
        parse_timestamp_flexible(r.get("timestamp", r.get("time"))) for r in rows
    ]
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [float(r["open"]) for r in rows],
            "high": [float(r["high"]) for r in rows],
            "low": [float(r["low"]) for r in rows],
            "close": [float(r["close"]) for r in rows],
            "volume": [float(r.get("tick_volume", r.get("volume", 1))) for r in rows],
            "spread": [float(r.get("spread", 0)) for r in rows],
        }
    )
    table = pa.Table.from_pandas(df)
    pq.write_table(table, p)


def main() -> None:
    """CLI demonstration of file history parsing on sample delimited data."""
    print("=== HaruQuantAI File History Parser Demonstration ===")
    sample_csv = (
        "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
        "2023.01.02\t00:00:00\t1.0500\t1.0550\t1.0490\t1.0530\t100\t100\t2\n"
    )
    bars = parse_delimited_bars(sample_csv, "EURUSD", "M1")
    print(
        f"Parsed {len(bars)} MT5 tab-delimited bar(s): close={bars[0]['close']}, time={bars[0]['time']}"
    )
    print("File parser validation passed.")


if __name__ == "__main__":
    main()
