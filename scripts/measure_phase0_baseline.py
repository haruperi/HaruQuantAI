"""Measure bounded Phase 0 fixture and evidence operations on reference hardware."""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq

from scripts import generate_phase0_evidence

REPO = Path(__file__).resolve().parent.parent
OUTPUT = REPO / "docs/dev/evidence/performance-baseline.json"
HARDWARE = REPO / "docs/dev/evidence/reference-hardware.json"
BARS = REPO / "tests/fixtures/bars/eurusd_m1_202501.parquet"
CATALOGUE = REPO / "tests/fixtures/catalogue/baseline_catalogue.db"
SAMPLES = 7
WARMUPS = 2


def _measure(operation: Callable[[], object]) -> list[float]:
    """Return elapsed milliseconds for warmed repeated calls."""
    for _ in range(WARMUPS):
        operation()
    samples: list[float] = []
    for _ in range(SAMPLES):
        started = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return samples


def summarize(samples: list[float], budget_ms: float) -> dict[str, Any]:
    """Summarize measured samples without hiding raw observations.

    Returns:
        Statistics, budget, raw samples, and deterministic pass/fail result.
    """
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))
    median = statistics.median(ordered)
    return {
        "unit": "ms",
        "samples": [round(value, 6) for value in samples],
        "minimum": round(min(samples), 6),
        "median": round(median, 6),
        "p95": round(ordered[p95_index], 6),
        "budget": budget_ms,
        "budget_result": "PASS" if median <= budget_ms else "FAIL",
    }


def _parquet_scan() -> int:
    """Read the pinned bars fixture.

    Returns:
        Number of rows in the fixture.
    """
    table = pq.read_table(  # type: ignore[no-untyped-call]
        BARS, columns=["timestamp", "close_scaled_1e5"]
    )
    return cast("int", table.num_rows)


def _catalogue_query() -> str:
    """Resolve one instrument through a fresh read-only SQLite connection.

    Returns:
        The matched instrument symbol.

    Raises:
        RuntimeError: If the pinned EURUSD fixture record cannot be resolved.
    """
    uri = f"file:{CATALOGUE.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        row = connection.execute(
            "SELECT asset_class FROM instruments WHERE symbol = ?", ("EURUSD",)
        ).fetchone()
    if row is None:
        raise RuntimeError("pinned catalogue fixture is missing EURUSD")
    return str(row[0])


def _evidence_projection() -> int:
    """Rebuild the in-memory Phase 0 evidence projection.

    Returns:
        Number of generated evidence documents.
    """
    return len(generate_phase0_evidence.build_payloads())


def measure() -> dict[str, Any]:
    """Measure the named workloads.

    Returns:
        Provenance-rich performance baseline payload.
    """
    reference = json.loads(HARDWARE.read_text(encoding="utf-8"))
    return {
        "manifest_version": "2.0",
        "reference_hardware_id": reference["hardware_id"],
        "runtime": reference["runtime"],
        "method": {
            "clock": "time.perf_counter_ns",
            "warmups": WARMUPS,
            "samples_per_workload": SAMPLES,
            "aggregation": (
                "median; raw samples retained; p95 nearest-rank over 7 samples"
            ),
            "command": (
                "uv run --frozen python scripts/measure_phase0_baseline.py --write"
            ),
        },
        "workloads": {
            "parquet_scan_1440_bars": {
                "fixture": BARS.relative_to(REPO).as_posix(),
                **summarize(_measure(_parquet_scan), 100.0),
            },
            "sqlite_catalogue_point_lookup": {
                "fixture": CATALOGUE.relative_to(REPO).as_posix(),
                **summarize(_measure(_catalogue_query), 20.0),
            },
            "phase0_evidence_projection": {
                "sources": [
                    "docs/dev/Phased_Feature_Implementation_Plan.md",
                    "docs/dev/Feature_Requirement_Traceability_Register.md",
                ],
                **summarize(_measure(_evidence_projection), 1_000.0),
            },
        },
    }


def main() -> int:
    """Write a measured baseline or enforce its declared budgets.

    Returns:
        Process exit status: zero when all workloads satisfy their budgets.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = measure()
    except (OSError, RuntimeError, sqlite3.Error) as error:
        print(f"[FAIL] performance measurement failed: {error}")
        return 1
    failed = [
        name
        for name, result in payload["workloads"].items()
        if result["budget_result"] != "PASS"
    ]
    if failed:
        print(f"[FAIL] performance budgets exceeded: {', '.join(failed)}")
        return 1
    if args.write:
        OUTPUT.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"[WRITE] {OUTPUT.relative_to(REPO)}")
    else:
        recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if recorded.get("reference_hardware_id") != payload["reference_hardware_id"]:
            print("[FAIL] recorded performance baseline targets different hardware")
            return 1
    print("[OK] all measured Phase 0 workloads are within their recorded budgets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
