# Phase 9 Simulation StandardResponse Migration

> **Plan ID:** `SIM-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target package:** `app/services/simulator`
> **Domain name:** Simulation
> **Migration program:** HaruQuantAI standard public-operation responses

## 1. Purpose and Gate

Migrate every qualifying Simulation public operation to Utils
`StandardResponse[T]` while preserving deterministic execution, accounting,
journaling, replay, state, reports, and raw results.

The implementation agent must read all repository authorities, the Simulation
README, source, tests, usage programs, current upstream domain contracts, and Utils
responses/errors. It must refresh this inventory, issue a dry run, and wait for a
new standalone `APPROVED: EXECUTE`.

Simulation must never be represented as a live trade. All operations use
`places_trade=False`, including simulated order submission.

## 2. Contract Invariants

The exact response fields are `status`, `message`, `data`, `error`, and `metadata`.

- Raw `SimulationResult`, `PortfolioSimulationResult`, `FastResearchResult`,
  receipts, matches, ledger snapshots, journal hashes, artifacts, report strings,
  mappings, tuples, and successful `None` remain directly in `data`.
- Simulation/business run states stay in their raw DTOs.
- Technical/domain failures use the error branch.
- Do not nest a Simulation result in a result/payload dictionary.
- Preserve non-payload run/audit/persistence evidence in extensions.
- Use monotonic duration timing rounded to three decimals.
- Preserve deterministic seeds, hashes, ordering, and replay equivalence.

## 3. Feature Order

1. Validation.
2. State.
3. Timeline.
4. Accounting.
5. Execution.
6. Journal.
7. Run orchestration.
8. Errors.
9. Reporting.

## 4. Public Operation Inventory

The baseline contains 52 operations.

### 4.1 Public functions

Validation and timing:

- `validate_phase_one_scope`
- `validate_run_inputs`
- `validate_market_data`
- `validate_intent_timing`
- `validate_fx_evidence`
- `build_tick_timeline`

Accounting/execution:

- `calculate_execution_costs`
- `calculate_margin`
- `convert_fx_amount`
- `normalize_volume`
- `evaluate_protective_exit`
- `match_order`
- `price_order`

Journal/state/error:

- `replay_journal`
- `resolve_idempotent_run`
- `to_simulation_error_payload`

Run:

- `run_backtest`
- `run_fast_research`
- `run_portfolio_backtest`

Reporting:

- `build_artifact_manifest`
- `build_json_report`
- `build_markdown_report`

`to_simulation_error_payload` remains a public conversion operation and returns its
existing payload mapping directly in `data`; migrated public boundaries should use
Utils error factories directly.

### 4.2 Accounting ledger

- `AccountLedger.apply_fill`
- `AccountLedger.mark_to_market`
- `AccountLedger.snapshot`

Preserve Decimal precision, balances, margin, realized/unrealized PnL, and invariant
checks. `mark_to_market` may successfully return `data=None`.

### 4.3 Execution engine and trader

- `EventDrivenExecutionEngine.submit_order`
- `EventDrivenExecutionEngine.execute_tick`
- `EventDrivenExecutionEngine.close_position`
- `EventDrivenExecutionEngine.snapshot`
- `SimTrader.submit_order`
- `SimTrader.close_position`
- `SimTrader.snapshot`

These operations mutate only in-memory/simulated state. They use
`places_trade=False`.

### 4.4 Journal writer

- `JournalWriter.append`
- `JournalWriter.finalize`

Preserve hash chaining, flush/fsync policy, atomicity, and final hash. Set
`writes_file=True`.

### 4.5 Request hash operations

- `SimulationBacktestRequestV1.calculate_config_hash`
- `PortfolioBacktestRequestV1.calculate_config_hash`

The exact hash string is raw `data`; response metadata must not influence hash
material.

### 4.6 Run dependency protocol

- `SimulationRunDependencies.persist_audit_event`
- `SimulationRunDependencies.load_market_data`
- `SimulationRunDependencies.generate_tick_series`
- `SimulationRunDependencies.calculate_indicators`
- `SimulationRunDependencies.evaluate_strategy`
- `SimulationRunDependencies.review_risk`
- `SimulationRunDependencies.build_order_intents`
- `SimulationRunDependencies.resolve_execution_profile`
- `SimulationRunDependencies.resolve_symbol_specification`
- `SimulationRunDependencies.resolve_cost_model`
- `SimulationRunDependencies.resolve_fx_evidence`

These protocol methods are public seams and must be migrated with every concrete
adapter and mock. Orchestration must unwrap their responses exactly once.

### 4.7 State-store protocol

- `SimulationStateStore.append_journal`
- `SimulationStateStore.flush_journal`
- `SimulationStateStore.finalize_journal`
- `SimulationStateStore.load_run`
- `SimulationStateStore.record_idempotency`

Preserve transaction, schema migration, idempotency, and resource-lifecycle rules.

### 4.8 Exclusions

Properties such as execution-engine observation accessors, constructors, Pydantic
validators, private hash/event helpers, migration constants, and feature-internal
functions not re-exported by the package root are excluded.

## 5. Error Catalogue Migration

`SIM_ERROR_CATALOG` already centralizes 43 domain codes, but its values are generic
mappings. Convert it to an immutable Simulation-owned
`Mapping[str, ErrorDefinition]`, preserving the export name and every code:

Request/scope:

- `SIM_INVALID_CONFIG`
- `SIM_INVALID_DATE_RANGE`
- `SIM_MISSING_SYMBOL`
- `SIM_ARBITRARY_CODE_REJECTED`
- `SIM_UNSUPPORTED_OPERATION`
- `SIM_UNSUPPORTED_ASSET_CLASS`
- `SIM_UNSUPPORTED_FEATURE`

Data/timing:

- `SIM_DATA_CHECKSUM_MISMATCH`
- `SIM_DATA_SCHEMA_INVALID`
- `SIM_DATA_NON_MONOTONIC`
- `SIM_DATA_DUPLICATE_TIMESTAMP`
- `SIM_DATA_OHLC_INVALID`
- `SIM_DATA_SPREAD_NEGATIVE`
- `SIM_DATA_STALE`
- `SIM_DATA_COVERAGE_INSUFFICIENT`
- `SIM_LOOKAHEAD_DETECTED`
- `SIM_FEATURE_LOOKAHEAD_DETECTED`
- `SIM_UNSUPPORTED_TICK_MODEL`
- `SIM_SPREAD_MISSING`

Execution/accounting:

- `SIM_INVALID_PRICE`
- `SIM_INVALID_VOLUME`
- `SIM_VOLUME_BELOW_MIN`
- `SIM_VOLUME_ABOVE_MAX`
- `SIM_VOLUME_STEP_MISMATCH`
- `SIM_SLIPPAGE_EXCEEDED`
- `SIM_LIQUIDITY_UNAVAILABLE`
- `SIM_GAP_UNCROSSABLE`
- `SIM_MARKET_CLOSED`
- `SIM_UNSUPPORTED_FILL_POLICY`
- `SIM_INSUFFICIENT_MARGIN`
- `SIM_COMMISSION_CALCULATION_FAILED`
- `SIM_SWAP_CALCULATION_FAILED`
- `SIM_FX_EVIDENCE_UNAVAILABLE`
- `SIM_POSITION_NOT_FOUND`
- `SIM_ORDER_NOT_FOUND`
- `SIM_EVENT_PRIORITY_AMBIGUOUS`
- `SIM_ACCOUNT_INVARIANT_BROKEN`

Persistence/replay/portfolio:

- `SIM_PERSISTENCE_FAILED`
- `SIM_CHECKPOINT_INCOMPATIBLE`
- `SIM_RUN_ID_CONFLICT`
- `SIM_COMPONENT_INCOMPLETE`
- `SIM_AGGREGATE_UNRECONCILED`
- `SIM_INTERNAL_ERROR`

Preserve group semantics as stable catalogue metadata where the Utils shape permits.
Map `SimulationError` code/message/details and trace IDs to the standard error and
metadata. Unexpected exceptions become `SIM_INTERNAL_ERROR` with no raw message.

## 6. Metadata Matrix

Common:

- `domain="simulation"`.
- `places_trade=False`.
- `requires_network` is true only for a concrete operation capable of invoking an
  external data or cross-process provider.

| Family | Risk | Read only | Side effects |
|---|---|---:|---|
| Validation/hash/calculation/report rendering | `low` | Yes | None |
| Timeline/matching/pricing | `medium` | Yes | None |
| Ledger/engine/trader mutation | `medium` | No | In-memory simulated state only |
| Journal writer/state store | `medium` | No | File/database flags as implemented |
| Dependency protocol reads | `medium` | Depends | Network flag where applicable |
| Backtest orchestration | `medium` | No | State/audit/artifact flags as configured |
| Portfolio backtest | `high` | No | Simulated multi-component state only |

Extensions may contain run IDs, audit IDs, journal hashes, artifact references,
component counts, or non-canonical fast-research disclosure when those are not
already fields of the raw result.

## 7. Cross-Domain Coordination

Prerequisites:

- Data for market datasets.
- Indicators for calculation.
- Strategy for evaluation and intents.
- Risk for review/governor decisions.
- Trading contracts for `OrderIntent`/`ExecutionReceipt`.

Every `SimulationRunDependencies` call returns a standard response after migration.
The orchestrator must fail closed on error, unwrap data once, and translate safe
upstream failure evidence to a Simulation code.

Analytics consumes Simulation outputs. During this phase, update its direct adapters
and fixtures to consume raw `response.data` without changing analytic results.
Optimization and Portfolio are later downstream phases.

## 8. Implementation Work Packages

### SIM-WP1 — Characterization

Freeze all 52 signatures, raw results, hashes, ordering, numerical values, journal
bytes, replay behavior, idempotency, and side effects.

### SIM-WP2 — Catalogue and base boundary

Convert the catalogue to `ErrorDefinition`, add response construction/mapping, and
test all codes, redaction, timing, and successful `None`.

### SIM-WP3 — Validation, timeline, accounting

Migrate pure operations and ledger methods without changing formulas or invariants.

### SIM-WP4 — Execution and journal

Migrate engine/trader and journal methods. Preserve async signatures, simulated-only
semantics, event priority, atomicity, and final hashes.

### SIM-WP5 — Protocols and state

Migrate dependency/state-store protocols, all adapters, fakes, fixtures, and mocks
as one compatibility unit.

### SIM-WP6 — Run orchestrators

Migrate backtest, fast-research, and portfolio orchestration. Unwrap upstream
responses explicitly, preserve audit ordering, and emit success only after required
finalization.

### SIM-WP7 — Reporting and consumers

Migrate reports/artifacts and Analytics/Optimization/Portfolio consumers needed for
compatibility.

### SIM-WP8 — Documentation

Update all nine feature registry sections, exact `FR-*`, public contracts, usage
paths/lines, architecture relationships, and `[Unreleased]`.

## 9. Tests and Usage

Required:

- Exact response shape and raw data for all 52 operations.
- All 43 catalogue codes.
- Deterministic hashes, journals, replay, results, and golden report.
- No lookahead or arbitrary-code regression.
- Accurate simulated-only `places_trade=False`.
- Upstream response failure translation.
- Protocol/implementation/mock parity.
- Closed resources and genuine async mocks.

Primary suites:

- All `tests/simulator/unit/`
- `tests/simulator/integration/test_official_backtest.py`
- `test_portfolio_backtest.py`
- `test_replay.py`
- `test_sim_trader.py`
- `test_optimization_boundary.py`
- `test_contract_compatibility.py`
- `test_usage_scripts.py`
- All nine numbered usage programs

Final gate:

```powershell
uv run ruff check app/services/simulator tests/simulator
uv run ruff format --check app/services/simulator tests/simulator
uv run mypy app/services/simulator tests/simulator
uv run pytest tests/simulator
Get-ChildItem tests/simulator/usage/[0-9][0-9]_*.py | ForEach-Object {
    uv run python $_.FullName
}
```

## 10. Risks, Exclusions, and Rollback

Risks:

- Response metadata leaking into deterministic hash material.
- Nested dependency responses.
- Misclassifying simulated submissions as live trades.
- Success emitted before journal/audit finalization.
- Altered Decimal or event-priority behavior.

Excluded:

- Execution-model or accounting redesign.
- New asset classes/fill policies/tick models.
- Live broker calls.
- Golden-output rebaselining without approved behavior change.
- AI-tool registration.

Rollback affected Simulator source, tests, fixtures only if intentionally changed,
usage programs, consumer edits, and active docs. Restore the old catalogue shape only
with all consumers. Rerun determinism, replay, and official backtest gates.

## 11. Completion Checklist

- [ ] All 52 refreshed operations return `StandardResponse[T]`.
- [ ] All raw outputs remain directly in `data`.
- [ ] All 43 codes use Utils-shaped Simulation-owned definitions.
- [ ] Determinism, hashes, replay, accounting, and journaling are unchanged.
- [ ] All operations accurately declare `places_trade=False`.
- [ ] Protocols, consumers, mocks, examples, and docs agree.
- [ ] Exact `FR-*` evidence is current.
- [ ] Full validation passes.
