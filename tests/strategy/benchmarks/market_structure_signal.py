"""Record a non-gating Strategy signal-evaluation performance baseline."""

from __future__ import annotations

import json
import logging
import platform
import statistics
import sys
import time
import tracemalloc
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy.evaluators.market_structure import MarketStructureEvaluator

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_indicator,
    make_market,
    make_signal_config,
    make_signal_evidence,
)

_ITERATIONS = 1_000
_REPEATS = 5
_EXPECTED_SIGNAL_COUNT = 2


def _run_once() -> float:
    """Run the fixed Strategy workload once.

    Returns:
        Elapsed wall-clock seconds.

    Raises:
        RuntimeError: If the evaluator returns an unexpected signal count.
    """
    market = make_market(
        (
            ("100", "111", "90", "100"),
            ("100", "110", "90", "100"),
            ("100", "106", "80", "100"),
            ("100", "105", "80", "100"),
            ("100", "101", "85", "100"),
            ("100", "111", "70", "100"),
            ("100", "105", "95", "104"),
            ("104", "107", "103", "106"),
        )
    )
    indicator = make_indicator(
        market,
        indicator_id="zigzag",
        output_column="zigzag_value_2",
        values=(110, 90, 105, 80, 100, 85, 110, 70),
    )
    evidence = make_signal_evidence(market)
    config = make_signal_config({})
    context = make_context()
    evaluator = MarketStructureEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    started = time.perf_counter()
    for _ in range(_ITERATIONS):
        signals = evaluator.evaluate_signals(
            evidence,
            (indicator,),
            config,
            context,
        )
        if len(signals) != _EXPECTED_SIGNAL_COUNT:
            raise RuntimeError("benchmark workload returned an invalid signal count")
    return time.perf_counter() - started


def main() -> int:
    """Execute the bounded benchmark and print its reproducibility evidence.

    Returns:
        Process exit code ``0`` after a complete measurement.
    """
    logging.disable(logging.CRITICAL)
    _run_once()
    tracemalloc.start()
    durations = tuple(_run_once() for _ in range(_REPEATS))
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    median_seconds = statistics.median(durations)
    result = {
        "benchmark": "strategy.market_structure_signal.v1",
        "cpu": platform.processor() or platform.machine(),
        "dataset": {
            "bars": 8,
            "indicator": "zigzag",
            "indicator_values": 8,
            "symbol": "EURUSD",
            "timeframe": "M5",
        },
        "durations_seconds": [round(item, 6) for item in durations],
        "iterations_per_repeat": _ITERATIONS,
        "median_microseconds_per_evaluation": round(
            median_seconds * 1_000_000 / _ITERATIONS,
            3,
        ),
        "method": "MarketStructureEvaluator.evaluate_signals",
        "operating_system": platform.platform(),
        "peak_traced_bytes": peak_bytes,
        "python": platform.python_version(),
        "repeats": _REPEATS,
        "strategy_type": "event-driven deterministic market structure",
        "versions": {
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "pydantic": version("pydantic"),
        },
        "workload": "two signals per evaluation; no I/O, persistence, or network",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
