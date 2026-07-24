# Strategy Performance Baseline

This report records the first reproducible, non-gating Strategy runtime baseline
required by `NFR-STR-012`. It does not establish or imply a latency service-level
objective.

## Environment

| Field | Recorded value |
|---|---|
| Measured at | 2026-07-24 (Africa/Cairo) |
| Hardware | Intel64 Family 6 Model 189 Stepping 1, GenuineIntel |
| Operating system | Windows 11, build 26220, 64-bit |
| Python | CPython 3.14.3 |
| NumPy | 2.4.6 |
| pandas | 3.0.3 |
| Pydantic | 2.13.4 |

## Workload

- Program: `tests/strategy/benchmarks/market_structure_signal.py`
- Strategy type: event-driven deterministic Market Structure evaluation.
- Method: `MarketStructureEvaluator.evaluate_signals`.
- Dataset: eight canonical `EURUSD` `M5` bars and eight official
  `zigzag_value_2` values.
- Output: two immutable `StrategySignal` values per evaluation.
- Repetition: one unmeasured warm-up, then five measured repeats of 1,000
  evaluations.
- Measurement: `time.perf_counter()` wall time with `tracemalloc` active.
- Boundaries: no network, provider, filesystem, or persistence activity is
  included.

## Observation

| Metric | Recorded value |
|---|---:|
| Repeat durations (seconds) | 1.946269, 2.454259, 2.159872, 1.602944, 1.272884 |
| Median time per evaluation | 1,946.269 microseconds |
| Peak traced Python allocation | 151,532 bytes |

The observed values are diagnostic and machine-specific. The variation and
memory-tracing overhead make them unsuitable as an enforced numerical gate.
Any future CI budget requires a separate owner-approved workload, runner class,
sampling policy, and threshold.

## Reproduction

Run from the repository root with the active locked environment:

```powershell
.venv\Scripts\python.exe tests/strategy/benchmarks/market_structure_signal.py
```
