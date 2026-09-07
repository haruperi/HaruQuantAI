"""Generate deterministic, offline Phase 0 market and catalogue fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO / "docs/dev/evidence"
FIXTURE_PATHS = {
    "FIX-BARS-M1-EURUSD": Path("tests/fixtures/bars/eurusd_m1_202501.parquet"),
    "FIX-TICKS-EURUSD": Path("tests/fixtures/ticks/eurusd_ticks_20250102.parquet"),
    "FIX-CATALOGUE-SQLITE": Path("tests/fixtures/catalogue/baseline_catalogue.db"),
}


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest for one generated fixture."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_bars(path: Path) -> int:
    """Write one deterministic UTC day of scaled EURUSD minute bars.

    Returns:
        Number of written bar records.
    """
    records = 1_440
    base_ms = 1_735_689_600_000
    opens = [110_000 + ((index * 7) % 121) - 60 for index in range(records)]
    closes = [value + ((index % 7) - 3) for index, value in enumerate(opens)]
    table = pa.table(
        {
            "timestamp": pa.array(
                [base_ms + index * 60_000 for index in range(records)],
                type=pa.timestamp("ms", tz="UTC"),
            ),
            "symbol": pa.array(["EURUSD"] * records),
            "open_scaled_1e5": pa.array(opens, type=pa.int64()),
            "high_scaled_1e5": pa.array(
                [
                    max(open_, close) + 4
                    for open_, close in zip(opens, closes, strict=True)
                ],
                type=pa.int64(),
            ),
            "low_scaled_1e5": pa.array(
                [
                    min(open_, close) - 4
                    for open_, close in zip(opens, closes, strict=True)
                ],
                type=pa.int64(),
            ),
            "close_scaled_1e5": pa.array(closes, type=pa.int64()),
            "volume_units": pa.array(
                [100 + (index % 23) for index in range(records)], type=pa.int64()
            ),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(  # type: ignore[no-untyped-call]
        table,
        path,
        compression="zstd",
        compression_level=3,
        use_dictionary=False,
        row_group_size=records,
        write_statistics=True,
    )
    return records


def _write_ticks(path: Path) -> int:
    """Write deterministic millisecond EURUSD bid/ask observations.

    Returns:
        Number of written tick records.
    """
    records = 3_600
    base_ms = 1_735_776_000_000
    bids = [110_000 + ((index * 11) % 97) - 48 for index in range(records)]
    table = pa.table(
        {
            "timestamp": pa.array(
                [base_ms + index * 1_000 for index in range(records)],
                type=pa.timestamp("ms", tz="UTC"),
            ),
            "sequence": pa.array(range(records), type=pa.int64()),
            "symbol": pa.array(["EURUSD"] * records),
            "bid_scaled_1e5": pa.array(bids, type=pa.int64()),
            "ask_scaled_1e5": pa.array(
                [bid + 2 + (index % 2) for index, bid in enumerate(bids)],
                type=pa.int64(),
            ),
            "volume_units": pa.array(
                [1 + (index % 5) for index in range(records)], type=pa.int64()
            ),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(  # type: ignore[no-untyped-call]
        table,
        path,
        compression="zstd",
        compression_level=3,
        use_dictionary=False,
        row_group_size=records,
        write_statistics=True,
    )
    return records


def _write_catalogue(path: Path) -> int:
    """Write a deterministic instrument/provider compatibility fixture.

    Returns:
        Number of written instrument records.
    """
    rows = [
        ("EURUSD", "FX", "EUR", "USD", 5, 100_000),
        ("GBPUSD", "FX", "GBP", "USD", 5, 100_000),
        ("USDJPY", "FX", "USD", "JPY", 3, 1_000),
        ("AUDUSD", "FX", "AUD", "USD", 5, 100_000),
        ("USDCAD", "FX", "USD", "CAD", 5, 100_000),
        ("USDCHF", "FX", "USD", "CHF", 5, 100_000),
        ("NZDUSD", "FX", "NZD", "USD", 5, 100_000),
        ("EURGBP", "FX", "EUR", "GBP", 5, 100_000),
        ("XAUUSD", "METAL", "XAU", "USD", 2, 100),
        ("BTCUSD", "CRYPTO", "BTC", "USD", 2, 100),
        ("SPY", "EQUITY", "SPY", "USD", 2, 100),
        ("QQQ", "EQUITY", "QQQ", "USD", 2, 100),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA page_size = 4096")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = OFF")
        connection.execute(
            "CREATE TABLE instruments ("
            "symbol TEXT PRIMARY KEY, asset_class TEXT NOT NULL, "
            "base_asset TEXT NOT NULL, quote_asset TEXT NOT NULL, "
            "price_scale INTEGER NOT NULL, scaled_unit INTEGER NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO instruments VALUES (?, ?, ?, ?, ?, ?)", rows
        )
        connection.execute(
            "CREATE TABLE provider_support ("
            "provider TEXT NOT NULL, symbol TEXT NOT NULL, mode TEXT NOT NULL, "
            "PRIMARY KEY (provider, symbol), "
            "FOREIGN KEY (symbol) REFERENCES instruments(symbol))"
        )
        connection.executemany(
            "INSERT INTO provider_support VALUES (?, ?, ?)",
            [("synthetic", symbol, "OFFLINE_FIXTURE") for symbol, *_ in rows],
        )
        connection.execute("PRAGMA user_version = 1")
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()
    return len(rows)


def generate(root: Path) -> dict[str, dict[str, Any]]:
    """Generate all fixtures below ``root``.

    Returns:
        Fixture metadata keyed by stable fixture identifier.
    """
    writers = {
        "FIX-BARS-M1-EURUSD": (_write_bars, "Parquet scaled OHLCV"),
        "FIX-TICKS-EURUSD": (_write_ticks, "Parquet scaled bid/ask ticks"),
        "FIX-CATALOGUE-SQLITE": (_write_catalogue, "SQLite catalogue v1"),
    }
    metadata: dict[str, dict[str, Any]] = {}
    for fixture_id, relative_path in FIXTURE_PATHS.items():
        writer, schema = writers[fixture_id]
        target = root / relative_path
        records = writer(target)
        metadata[fixture_id] = {
            "fixture_id": fixture_id,
            "path": relative_path.as_posix(),
            "records": records,
            "sha256": _sha256(target),
            "bytes": target.stat().st_size,
            "schema": schema,
            "generator": "scripts/generate_phase0_fixtures.py",
            "offline_only": True,
        }
    return metadata


def _payloads(metadata: dict[str, dict[str, Any]]) -> dict[Path, dict[str, Any]]:
    """Build fixture manifest and workload hierarchy payloads.

    Returns:
        Mapping of evidence paths to canonical JSON payloads.
    """
    return {
        EVIDENCE_DIR / "fixture-manifest.json": {
            "manifest_version": "2.0",
            "determinism": (
                "Pinned pyarrow/sqlite runtime; exact bytes checked by SHA-256."
            ),
            "fixtures": list(metadata.values()),
        },
        EVIDENCE_DIR / "schema-fixture-plan.json": {
            "manifest_version": "2.0",
            "numeric_representation": (
                "Signed int64 values scaled by the declared column unit."
            ),
            "hierarchy": {
                "small": {
                    "purpose": "unit and contract checks",
                    "maximum_records": 200,
                    "budget_ms": 100,
                },
                "medium": {
                    "purpose": "domain integration and Phase 1 browser readiness",
                    "maximum_records": 5_000,
                    "budget_ms": 1_000,
                },
                "large": {
                    "purpose": (
                        "explicit scale qualification generated in temporary storage"
                    ),
                    "maximum_records": 1_000_000,
                    "budget_ms": 10_000,
                    "checked_in": False,
                },
            },
            "checked_in_fixtures": list(metadata.values()),
        },
    }


def _render(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    """Write fixtures and manifests or verify exact reproducibility.

    Returns:
        Process exit status: zero on success and one on drift or failure.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        metadata = generate(REPO)
        for path, payload in _payloads(metadata).items():
            path.write_text(_render(payload), encoding="utf-8")
            print(f"[WRITE] {path.relative_to(REPO)}")
        print(f"[OK] generated {len(metadata)} deterministic fixtures")
        return 0
    with tempfile.TemporaryDirectory(prefix="hq-phase0-fixtures-") as temporary:
        generated = generate(Path(temporary))
    expected_payloads = _payloads(generated)
    drift: list[str] = []
    for fixture_id, fixture_metadata in generated.items():
        actual_path = REPO / FIXTURE_PATHS[fixture_id]
        if (
            not actual_path.is_file()
            or _sha256(actual_path) != fixture_metadata["sha256"]
        ):
            drift.append(FIXTURE_PATHS[fixture_id].as_posix())
    for path, payload in expected_payloads.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != _render(payload):
            drift.append(path.relative_to(REPO).as_posix())
    if drift:
        print("[FAIL] deterministic fixture drift:")
        for drift_path in drift:
            print(f"  - {drift_path}")
        return 1
    print("[OK] 3 fixture files and 2 manifests reproduce exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
