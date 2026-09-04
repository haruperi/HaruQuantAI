"""Convert Dukascopy M1 bar CSV files to partitioned Parquet datasets with ZSTD-6.

Implements the HaruQuantAI Parquet specification:
- Storage format: Apache Parquet (v2.6) with Zstandard (ZSTD) level 6 compression.
- Writer: PyArrow table writer with dictionary encoding, page checksums, and stats.
- Schema: DateTime (UTC timestamp), Open, High, Low, Close (float64), Volume (uint64).
- Tick size resolution: Loaded from database 'instruments' table
  (data/database/haruquantai.db).
- Timeframe: Always M1 (higher timeframes resampled in-memory).
- Readers: Polars LazyFrame or DuckDB analytical queries.
- Organization: Partitioned by symbol directory and split by year (e.g.
  ``data/market_data/bars/dukascopy/eurusd/2007.parquet``).
- Metadata: Stored in Parquet key-value schema metadata and ``metadata.json``.

Usage:
    # Convert all CSVs with recommended ZSTD-6 and database tick size resolution
    uv run python scripts/convert_dukascopy_csv_to_parquet.py

    # Convert a single symbol (e.g. eurusd)
    uv run python scripts/convert_dukascopy_csv_to_parquet.py --symbols eurusd

    # Dry-run to inspect planned actions
    uv run python scripts/convert_dukascopy_csv_to_parquet.py --dry-run
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import sqlite3
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

_MIN_CSV_COLS = 2
_DEFAULT_DB_PATH = Path("data/database/haruquantai.db")

BAR_SCHEMA = pa.schema(
    [
        pa.field("DateTime", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("Open", pa.float64(), nullable=False),
        pa.field("High", pa.float64(), nullable=False),
        pa.field("Low", pa.float64(), nullable=False),
        pa.field("Close", pa.float64(), nullable=False),
        pa.field("Volume", pa.uint64(), nullable=False),
    ]
)


def extract_symbol_from_path(path: Path) -> str:
    """Extract normalized lowercase symbol from Dukascopy CSV filename.

    Args:
        path: Path to the CSV file.

    Returns:
        Lowercase symbol string.
    """
    stem = path.stem
    if "_" in stem:
        symbol = stem.split("_")[0]
    elif "." in stem:
        symbol = stem.split(".")[0]
    else:
        symbol = stem
    return symbol.strip().lower()


def load_db_instruments(db_path: Path) -> dict[str, tuple[float, int]]:
    """Load tick size and digits for all instruments from database.

    Args:
        db_path: Path to haruquantai.db SQLite database file.

    Returns:
        Dictionary mapping uppercase symbol to (tick_size, digits).
    """
    if not db_path.exists():
        return {}

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name, trade_tick_size, point, digits FROM instruments")
        result: dict[str, tuple[float, int]] = {}
        for row in cur.fetchall():
            name = str(row[0]).strip().upper()
            tick_size = (
                float(row[1])
                if row[1] is not None
                else (float(row[2]) if row[2] is not None else 0.00001)
            )
            digits = int(row[3]) if row[3] is not None else 5
            result[name] = (tick_size, digits)
        conn.close()
        return result
    except sqlite3.Error, ValueError:
        return {}


def resolve_instrument_spec(
    symbol: str,
    csv_path: Path,
    db_instruments: dict[str, tuple[float, int]],
) -> tuple[float, int]:
    """Resolve tick size and decimal digits for symbol using database.

    Args:
        symbol: Lowercase symbol name.
        csv_path: Input CSV file for precision inspection fallback.
        db_instruments: Preloaded dictionary from database instruments table.

    Returns:
        Tuple of (tick_size, digits).
    """
    sym_upper = symbol.upper()
    if sym_upper in db_instruments:
        return db_instruments[sym_upper]

    # Fallback: inspect sample prices in CSV
    try:
        with csv_path.open("r", encoding="utf-8") as fp:
            for _ in range(20):
                line = fp.readline()
                if not line:
                    break
                parts = line.strip().split(",")
                if len(parts) >= _MIN_CSV_COLS and "." in parts[1]:
                    decimals = len(parts[1].split(".")[1])
                    tick_size = round(math.pow(10, -decimals), decimals)
                    return tick_size, decimals
    except OSError:
        pass

    # Standard fallback
    digits = 3 if "JPY" in sym_upper else (2 if sym_upper == "XAUUSD" else 5)
    tick_size = (
        0.001 if "JPY" in sym_upper else (0.01 if sym_upper == "XAUUSD" else 0.00001)
    )
    return tick_size, digits


def _build_duckdb_read_sql(
    csv_posix: str,
    digits: int,
) -> str:
    """Build DuckDB SQL query for parsing Dukascopy CSV into M1 OHLCV.

    Args:
        csv_posix: POSIX path to input CSV.
        digits: Decimal digits precision for rounding prices.

    Returns:
        SQL string for DuckDB execution.
    """
    return f"""
    SELECT
        timezone('UTC', strptime(column0, '%Y%m%d %H:%M:%S')) AS "DateTime",
        round(column1, {digits})::DOUBLE AS "Open",
        round(column2, {digits})::DOUBLE AS "High",
        round(column3, {digits})::DOUBLE AS "Low",
        round(column4, {digits})::DOUBLE AS "Close",
        column5::UBIGINT AS "Volume",
        substr(column0, 1, 4) AS year
    FROM read_csv(
        '{csv_posix}',
        header=false,
        columns={{
            'column0': 'VARCHAR',
            'column1': 'DOUBLE',
            'column2': 'DOUBLE',
            'column3': 'DOUBLE',
            'column4': 'DOUBLE',
            'column5': 'BIGINT',
            'column6': 'DOUBLE'
        }}
    )
    ORDER BY "DateTime"
    """  # noqa: S608


def _write_year_parquet_file(
    table: pa.Table,
    target_file: Path,
    compression_level: int,
    metadata_bytes: dict[bytes, bytes],
) -> None:
    """Write an Arrow table to Parquet with ZSTD compression and metadata.

    Args:
        table: Filtered PyArrow Table for a single year.
        target_file: Destination Parquet file path.
        compression_level: ZSTD compression level (recommended: 6).
        metadata_bytes: Custom key-value schema metadata.
    """
    clean_table = table.drop(["year"]).cast(BAR_SCHEMA)
    clean_table = clean_table.replace_schema_metadata(metadata_bytes)
    pq.write_table(
        clean_table,
        target_file,
        compression="zstd",
        compression_level=compression_level,
        version="2.6",
        use_dictionary=True,
        write_statistics=True,
        write_page_checksum=True,
        row_group_size=250_000,
    )


def convert_symbol_csv(
    csv_path: Path,
    output_dir: Path,
    db_instruments: dict[str, tuple[float, int]],
    *,
    extension: str = "parquet",
    compression_level: int = 6,
    overwrite: bool = True,
    dry_run: bool = False,
    quiet: bool = False,
) -> tuple[int, int, float]:
    """Convert a single Dukascopy CSV file to per-year Parquet files.

    Args:
        csv_path: Path to the input CSV file.
        output_dir: Root directory for output symbol folders.
        db_instruments: Preloaded database instruments mapping.
        extension: File extension (e.g. 'parquet' or 'paquet').
        compression_level: ZSTD compression level (default: 6).
        overwrite: Whether to overwrite existing destination files.
        dry_run: If True, only plan and log actions without writing files.
        quiet: If True, suppress per-year logs.

    Returns:
        Tuple of (total_rows_processed, years_written, elapsed_seconds).
    """
    symbol = extract_symbol_from_path(csv_path)
    symbol_dir = output_dir / symbol
    ext = extension.lstrip(".")
    tick_size, digits = resolve_instrument_spec(symbol, csv_path, db_instruments)

    t0 = time.perf_counter()
    size_mb = csv_path.stat().st_size / (1024 * 1024)

    if dry_run:
        print(
            f"[DRY-RUN] Symbol: {symbol.upper()} "
            f"({csv_path.name}, {size_mb:.1f} MB, "
            f"tick_size={tick_size}, digits={digits})"
        )
        print(f"          Target directory: {symbol_dir}")
        return 0, 0, 0.0

    symbol_dir.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect()
    conn.execute("SET TimeZone = 'UTC'")

    read_sql = _build_duckdb_read_sql(csv_path.as_posix(), digits)
    arrow_table = conn.execute(read_sql).to_arrow_table()
    conn.close()

    total_rows = arrow_table.num_rows
    if total_rows == 0:
        return 0, 0, 0.0

    years_col = arrow_table["year"]
    years = sorted(pc.unique(years_col).to_pylist())

    meta_bytes = {
        b"symbol": symbol.upper().encode("utf-8"),
        b"timeframe": b"M1",
        b"source": b"dukascopy",
        b"tick_size": str(tick_size).encode("utf-8"),
        b"digits": str(digits).encode("utf-8"),
    }

    years_written = 0
    for year in years:
        target_file = symbol_dir / f"{year}.{ext}"
        if target_file.exists() and not overwrite:
            if not quiet:
                print(f"  [SKIP] {target_file.name} already exists.")
            continue

        mask = pc.equal(years_col, year)
        year_table = arrow_table.filter(mask)
        _write_year_parquet_file(year_table, target_file, compression_level, meta_bytes)
        years_written += 1

    # Write metadata.json alongside Parquet files
    metadata: dict[str, Any] = {
        "symbol": symbol.upper(),
        "timeframe": "M1",
        "source": "dukascopy",
        "schema": ["DateTime", "Open", "High", "Low", "Close", "Volume"],
        "tick_size": tick_size,
        "digits": digits,
        "compression": "zstd",
        "compression_level": compression_level,
        "total_rows": total_rows,
        "years": years,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    metadata_file = symbol_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    elapsed = time.perf_counter() - t0
    return total_rows, years_written, elapsed


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Optional command line argument strings.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/market_data/bars/dukascopy"),
        help="Input directory with CSVs (default: data/market_data/bars/dukascopy).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Root output directory (default: same as input directory).",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=_DEFAULT_DB_PATH,
        help="Path to SQLite DB file (default: data/database/haruquantai.db).",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated symbols to process (e.g. 'eurusd,gbpusd').",
    )
    parser.add_argument(
        "--extension",
        type=str,
        default="parquet",
        help="Output file extension (default: parquet).",
    )
    parser.add_argument(
        "--compression-level",
        type=int,
        default=6,
        help="Zstandard (ZSTD) compression level 1-22 (default: 6).",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip files that already exist in destination.",
    )
    parser.add_argument(
        "--delete-csv",
        action="store_true",
        help="Delete source CSV file after successful conversion.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned conversions without writing files.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output per file.",
    )
    return parser.parse_args(argv)


def filter_csv_files(
    csv_files: list[Path],
    symbols_arg: str | None,
) -> list[Path]:
    """Filter CSV files matching optional user-provided symbol list.

    Args:
        csv_files: List of all discovered CSV paths.
        symbols_arg: Comma-separated symbol string or None.

    Returns:
        Filtered list of CSV paths.
    """
    if not symbols_arg:
        return csv_files
    selected = {s.strip().lower() for s in symbols_arg.split(",")}
    return [p for p in csv_files if extract_symbol_from_path(p) in selected]


def _process_single_symbol(
    csv_path: Path,
    output_dir: Path,
    db_instruments: dict[str, tuple[float, int]],
    args: argparse.Namespace,
    idx: int,
    total: int,
) -> tuple[int, int]:
    """Convert a single symbol CSV and print status.

    Args:
        csv_path: Input CSV path.
        output_dir: Output root path.
        db_instruments: Preloaded database instruments specs.
        args: Parsed CLI options.
        idx: Index of current file.
        total: Total number of files.

    Returns:
        Tuple of (rows_processed, years_written).
    """
    symbol = extract_symbol_from_path(csv_path)
    size_mb = csv_path.stat().st_size / (1024 * 1024)
    tick_sz, digits = resolve_instrument_spec(symbol, csv_path, db_instruments)
    print(
        f"[{idx}/{total}] Processing {symbol.upper()} "
        f"({csv_path.name}, {size_mb:.1f} MB, "
        f"tick_size={tick_sz}, digits={digits})..."
    )

    rows, years_written, elapsed = convert_symbol_csv(
        csv_path=csv_path,
        output_dir=output_dir,
        db_instruments=db_instruments,
        extension=args.extension,
        compression_level=args.compression_level,
        overwrite=not args.no_overwrite,
        dry_run=args.dry_run,
        quiet=args.quiet,
    )

    if not args.dry_run:
        target_dir = output_dir / symbol
        ext = args.extension.lstrip(".")
        pq_size_mb = sum(f.stat().st_size for f in target_dir.glob(f"*.{ext}")) / (
            1024 * 1024
        )
        print(
            f"  -> Converted {rows:,} rows across {years_written} year file(s) "
            f"in {elapsed:.2f}s (Parquet size: {pq_size_mb:.2f} MB)"
        )

        if args.delete_csv:
            csv_path.unlink()
            print(f"  -> Deleted source CSV: {csv_path.name}")

    return rows, years_written


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the Dukascopy CSV to Parquet conversion pipeline.

    Args:
        argv: Optional CLI arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    if sys.stdout:
        with contextlib.suppress(AttributeError, io.UnsupportedOperation):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir

    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    all_csvs = sorted([p for p in input_dir.glob("*.csv") if p.is_file()])
    csv_files = filter_csv_files(all_csvs, args.symbols)

    if not csv_files:
        print(f"No matching CSV files found in {input_dir}")
        return 0

    # Load instrument specifications from database
    db_instruments = load_db_instruments(args.db_path)
    print(
        f"Loaded {len(db_instruments)} instrument specifications "
        f"from database: {args.db_path}"
    )

    print(f"Found {len(csv_files)} CSV file(s) to process in {input_dir}.")
    print(f"Output destination: {output_dir}")
    ext_label = args.extension.lstrip(".")
    print(
        f"Format: Parquet (v2.6) + ZSTD (level {args.compression_level}) | "
        f"Schema: DateTime, Open, High, Low, Close, Volume | "
        f"Timeframe: M1 | Extension: .{ext_label}"
    )
    mode_str = "DRY-RUN (no files written)" if args.dry_run else "LIVE"
    print(f"Mode: {mode_str}\n")

    total_start = time.perf_counter()
    total_all_rows = 0
    total_all_years = 0

    for idx, csv_path in enumerate(csv_files, 1):
        try:
            rows, years = _process_single_symbol(
                csv_path, output_dir, db_instruments, args, idx, len(csv_files)
            )
            total_all_rows += rows
            total_all_years += years
        except Exception as exc:  # noqa: BLE001
            print(
                f"  [ERROR] Failed to convert {csv_path.name}: {exc}",
                file=sys.stderr,
            )
            return 1

    total_elapsed = time.perf_counter() - total_start
    print("\n------------------------------------------------------------")
    if args.dry_run:
        print(f"Dry run complete for {len(csv_files)} files.")
    else:
        print(
            f"Successfully processed {len(csv_files)} symbol(s), "
            f"{total_all_rows:,} total rows, and {total_all_years} Parquet file(s) "
            f"in {total_elapsed:.2f}s."
        )
    print("------------------------------------------------------------")
    return 0


if __name__ == "__main__":
    sys.exit(main())
