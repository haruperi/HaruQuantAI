#!/usr/bin/env python3
"""Benchmark explicit parallel-safe pytest selections with 1, 2, and 4 workers."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
MAX_REPEATS = 5


def benchmark(
    selections: list[str],
    *,
    workers: tuple[int, ...] = (1, 2, 4),
    repeat: int = 1,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Run bounded worker-count comparisons for explicitly selected tests.

    Returns:
        Canonical diagnostic report without an automatic adoption decision.

    Raises:
        ValueError: If selection, worker counts, or repeat bounds are invalid.
    """
    if not selections:
        raise ValueError("At least one explicit test selection is required.")
    if (
        repeat < 1
        or repeat > MAX_REPEATS
        or not workers
        or any(value not in {1, 2, 4} for value in workers)
    ):
        raise ValueError("Use workers 1/2/4 and repeat between one and five.")
    results: list[dict[str, Any]] = []
    for worker in workers:
        for iteration in range(1, repeat + 1):
            command = ["uv", "run", "--locked", "pytest", "--no-cov", "-q", *selections]
            if worker > 1:
                command.extend(["-n", str(worker), "--dist=worksteal"])
            started = time.perf_counter()
            completed = runner(
                command, cwd=REPO, capture_output=True, text=True, check=False
            )
            results.append(
                {
                    "workers": worker,
                    "iteration": iteration,
                    "command": command,
                    "elapsed_seconds": round(time.perf_counter() - started, 6),
                    "exit_code": completed.returncode,
                    "passed": completed.returncode == 0,
                }
            )
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(timespec="seconds"),
        "selections": selections,
        "parallel_safe_asserted_by_operator": True,
        "results": results,
        "automatic_lane_adoption": False,
    }


def main() -> int:
    """Run the explicit benchmark and persist its canonical JSON report.

    Returns:
        Zero when every benchmark command passes; otherwise one.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selections", nargs="+")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = benchmark(args.selections, repeat=args.repeat)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if all(item["passed"] for item in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
