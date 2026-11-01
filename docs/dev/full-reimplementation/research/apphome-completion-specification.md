# AppHome native execution contract - Iteration 2 candidate

Date: 2026-11-01. HEAD: `6718586dd73352de2ecf65b5048a188d953d9dd8`.
Status: implemented in part, not qualified. See the current completion audit.

## Native project authority

Projects remain Core `.haru` envelopes with `manifest.json`, `project.json` and
`tasks/<task_id>.json`. Home preserves native extension fields when mutating its
owned fields. `manifest.schema_version` is a format version, never an edit counter.
The integer `project.metadata.revision` is the optimistic edit revision.

Every edit supplies `expected_revision`; locking covers load, comparison and
Core atomic envelope replacement. Project settings edits require an existing task.
Notes are complete Unicode plain text stored as `project.metadata.notes`.
Template actions require configured host `project_templates` documents containing
`task_type` and `settings`; no market defaults are invented. Resource resolutions
may update only dependencies already declared in project metadata.

## Task execution settings

Execution is stored in the native task's `settings.execution` object. The task's
native `databank_target` must be one of the project's databank identity values.
No task, destination, strategy or dataset is chosen as a fallback at submission.

```json
{
  "mode": "RETEST",
  "seed": 42,
  "dataset": {
    "source": "sample",
    "symbol": "TEST",
    "timeframe": "M1",
    "revision": null,
    "start": null,
    "end": null
  },
  "model": {
    "initial_capital": 10000,
    "point_value": 1,
    "pip_size": 0.0001,
    "commission_per_order": 0,
    "slippage_points": 0,
    "precision_mode": "OHLC",
    "same_bar_sl_tp_rule": "WORST_CASE"
  },
  "strategy_result_ids": ["an-actual-owned-result-id"],
  "split_time": null
}
```

This is a contract example, not a default market or generated result. The selected
result must contain a real StrategyDocument payload. Supported mappings are:

| Native task type | Mode | Core owners |
| --- | --- | --- |
| build / builder | RANDOM | GenerationEngine, StrategyRuntime, BacktestRunner |
| retest / retester | RETEST | Stored strategy, StrategyRuntime, BacktestRunner |
| optimize / optimizer | GRID | OptimizationEngine indexes, parameter variants, BacktestRunner |

RANDOM additionally accepts `candidates` (1..1000), `max_rule_depth` (1..8) and
`allowed_blocks`. GRID requires one stored strategy and named finite
`parameter_ranges` (`name`, `start`, `end`, positive `step`), bounded at 10000
combinations. Unimplemented genetic/template/robustness/walk-forward algorithms
remain unavailable. Their UI presence is not acceptance evidence.

Preflight captures the saved project revision, pinned catalog revision, detached
market bars, settings, seed and serialized strategy definitions before job
submission. Dataset ranges use epoch seconds. A run admits 1..100000 actual bars.
The optional `split_time` is an explicit epoch-second boundary inside those bars;
no implicit split is inferred. StatisticsService computes trade sample metrics.

Non-finite numerical output causes an explicitly logged rejected evaluation and
no result write for that candidate. Values are not replaced with fabricated zeros.
The receipt records evaluated, stored and rejected counts. A legacy wrapper without
any finite accepted result raises an explicit error rather than reporting a score.

## Lifecycle and result API

Authenticated routes remain under `/api/v1/home`.

- `GET /project/{project_id}` returns native manifest/tasks/databanks/metadata and revision.
- `POST /project/{project_id}/settings` takes task_id, settings, expected_revision.
- `POST /project/{project_id}/notes` takes notes, expected_revision and acknowledges
  successful persistence with status `saved`, exact `notes` and new revision.
- `POST /engine/{project_id}/start` requires task_id and expected_revision.
- pause/resume/stop actions require an explicitly owned job_id.
- `GET /engine/{project_id}/status?job_id=...` reads actual JobManager state.
  Without job_id it recovers the latest known project job. Core progress is 0..100.
- `GET /project/{project_id}/result/{result_id}` returns project-owned stored detail.
- `GET /dashboard/results` ranks all stored pages before applying the display limit.

Every result uses a run-scoped ID and `from_backtest_result` / ResultStore. Stored
results retain strategy payload, parameter provenance, actual trades, equity and
MAE/MFE. ALL metrics are available where finite; IS/OOS metrics exist only with an
explicit saved boundary. Earlier runs and historical records are preserved.

## Candidate limitations and remaining qualification

The approved execution iterations now bind legacy Builder/Retester/Optimizer
services to the shared Home execution authority. Data, Money Management and Options
forms edit the saved execution contract. Notes and custom-analysis names persist
with optimistic revisions; browser acceptance verifies restart and both themes.

Supported execution is bounded to Core OHLC RANDOM generation, stored-strategy
RETEST and numeric GRID optimization. Unsupported algorithms, sizing policies,
analysis providers and unconfigured license/release feeds remain explicitly
unavailable. Analysis names are persisted definitions, not fabricated calculations.

The owner requested retirement of the AppHome implementation work order after
qualification. The completion audit retains the contract and regression evidence.
The earlier 72.99% report omitted execution before pytest-cov startup; coverage
started before plugin imports measured a clean 84.1063% baseline with 2,703 tests
passing. Iteration 5 adds 45 behavior regressions. The final complete suite passes
2,748 tests with 84.1913% combined statement/branch coverage; the audit records
statement and branch counts separately. Coverage thresholds and retained-source exclusions
remain unchanged. This qualification covers the supported contract above, not
complete SQX donor parity or completion of other workspace work orders.
