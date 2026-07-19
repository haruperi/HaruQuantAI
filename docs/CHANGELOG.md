# Changelog

This document is only for adding high-level changes, decisions, or status updates that affect the entire project. It does not contain the detailed changes for each module or service. Please refer to the README.md files in each module or service for more information. Each item should be written in a very brief way that it is easy to understand and can be used to track the progress of the project. Not more than 3 sentences per item.

### Status

- Risk is a completed implementation baseline across contracts, configuration,
  snapshots, sizing, audit, Policy, regimes, approvals, decisions, scenarios,
  reporting, all 54 functional and 12 non-functional requirements, and all
  thirteen workflows.
- Utils, Brokers, and Data are recorded as completed implementation baselines after
  independent deterministic domain verification. The complete system remains
  `Missing`, and repository-wide documentation-quality cleanup remains tracked.
- Indicators is now a completed implementation baseline after independent
  deterministic domain verification (Core plus trend, volatility, momentum,
  volume, candles, the public package port, and all five `WF-INDI-*` workflows).
- Strategy is implemented across contracts, diagnostics, registry, intents,
  replay/checkpoints, vectorized evaluation, event hooks, concrete signal
  evaluators, and all ten workflows. All prescribed Strategy validation gates pass.
- Trading is a completed implementation baseline across all 66 active functional and
  eight non-functional requirements, nine capability modules, and all fourteen
  documented workflows; production live mutation remains disabled by default.
- Simulation is a completed implementation baseline across all 43 functional and
  12 non-functional requirements, its nine registered workflows, and the clean
  Section 7 domain gate. The post-build review of 2026-07-19 closed six blocking
  correctness defects. The Section 7 gate is green on both Linux (`169 passed`,
  `83.21%` coverage) and the Windows toolchain; the domain is verified.
- Data remains a completed implementation baseline, now including real-evidence
  tick-series generation (`FR-DATA-087`–`FR-DATA-090`, `WF-DATA-016`). Its quality
  gates must be run on the Windows toolchain; the feature has not yet been executed.
- Analytics is a completed implementation baseline across contracts, ledger
  adaptation, 60 cataloged metrics, reporting/allocation evidence, bounded dashboards,
  package exports, all active requirements, and all non-excluded workflows. The
  post-build review of 2026-07-19 closed one blocking and three high findings in the
  evidence layer; its Section 7 gate must be re-run on the Windows toolchain before
  the domain is re-declared verified.
- Optimization is a completed advisory-domain baseline across all 64 functional and
  12 non-functional requirements, six domain workflows, and ten official public
  operations. Its deterministic Optimization core passes 160 tests at 82.70% branch
  coverage; `SYS-WF-003` remains `Partial` only because UI/API approval and Strategy
  adoption are outside this domain build.

### Added

- **2026-07-19 — Optimization domain completed.** Added bounded grid and seeded-random
  search, Simulation/Analytics execution adaptation, scoring and overfit evidence,
  walk-forward validation, robustness analysis, durable Optimization-owned state,
  advisory handoff evidence, and the ten-operation public API. Added targeted unit,
  usage, workflow-integration, non-functional, and `SYS-WF-003` core tests.
- **2026-07-19 — Simulation domain gate unblocked.** Re-running the Section 7 gate
  after the post-build review corrections surfaced six failures, all traced to two
  defects in the shared `tests/simulator/unit/test_orchestrator.py` fixtures rather
  than to Simulation production code. `FakeDependencies.resolve_fx_evidence` built a
  `USD → USD` identity rate leg, which Data's `FXRateLeg` correctly rejects
  (`app/services/data/contracts/fx.py:197`) because a leg converting a currency to
  itself carries no conversion evidence and cannot satisfy the contract's
  continuous-path and composite-rate invariants; the fixture now emits a genuine
  `EUR → USD` leg at `1.10`, matching the `EURUSD` instrument and `USD` account
  currency already used by the request fixture. This unblocked
  `test_portfolio_run_fails_closed_on_incomplete_component`,
  `test_portfolio_run_fails_closed_on_unreconciled_aggregate`,
  `test_portfolio_return_series_is_measured_not_supplied`,
  `test_portfolio_candidate_publishes_reconciled_aggregate`, and
  `test_usage_run_portfolio_backtest`. Separately,
  `test_repeat_request_with_different_hash_conflicts` arranged its conflict by
  writing a mismatched record straight into the state store, so the store's own
  `SIM_RUN_ID_CONFLICT` guard fired during setup and the production path was never
  reached; the test now submits a second request carrying the same `request_id` with
  different hashed material (`seed=11`) and asserts `run_backtest` raises
  `SIM_RUN_ID_CONFLICT` through `resolve_idempotent_run` (`FR-SIM-017`), and further
  asserts the stored run identity is unchanged. `_request` gained a `seed` parameter
  for that purpose. No Simulation production file was modified. Gate: ruff and
  `ruff format --check` clean, `mypy` clean over 32 source files, 110 unit + 16
  integration + 43 usage tests passing, `169 passed` at `83.21%` coverage.

- **2026-07-19 — Simulation domain verified and closed.** The Section 7 command
  block was executed on the Windows toolchain and passes in full: `ruff check`,
  `ruff format --check`, `mypy app/services/simulator`, the unit, integration, and
  usage suites, and `--cov-fail-under=80`. This was the sole remaining checklist
  item. `app/services/simulator/README.md` moves from `Partial` to `Completed`
  with every checklist item satisfied, and no post-build review finding remains
  open at any severity.

- **2026-07-19 — Analytics post-build review corrections (blocking class).** A
  read-only completion review returned `NOT READY`. The blocking finding and the
  three high findings that shared the evidence/safety layer are now closed.
  `build_performance_report()` no longer hardcodes `quality_flags=()`
  (`FR-ANLT-043`): it emits `required_section_failed` per failed required section,
  `diagnostic_partial_report` when a required section failed under
  `diagnostic_partial_mode`, `sample_below_threshold` below
  `MIN_METRIC_SAMPLES["statistical"]`, and `intratrade_exposure_unobserved` on every
  closed-trade report. A diagnostic partial report is therefore no longer
  byte-indistinguishable from a complete one, closing a false-success path into the
  registered `PerformanceReport v1` consumed by Optimization, Portfolio, and UI/API.
  `AnalyticsWarning` and `QualityFlag` now implement their documented `Raises`
  (`FR-ANLT-007`, `FR-ANLT-008`): both validate `code` against `EVIDENCE_CATALOG`
  and reject a severity — and, for flags, a blocker value — that conflicts with the
  catalog. All fifteen direct `AnalyticsWarning(...)` constructions in
  `metrics/` are routed through `build_warning()` (`FR-ANLT-022`), restoring the
  `MAX_WARNING_DETAIL_BYTES` bound, Utils redaction, catalog-code validation, and
  catalog-derived severity on the dominant emission path. Producer
  `source_metadata` and `quality_metadata` are redacted through Utils
  `redact_mapping_value` before they reach `TradingResult` and before their bound is
  measured (`FR-ANLT-027`, `NFR-ANLT-006`). Two latent catalog defects surfaced by
  the routing are fixed: `insufficient_samples` in `returns.py` and
  `undefined_zero_variance` in `distributions.py` carried detail keys that did not
  match their cataloged `required_detail_keys`, and `r_multiple_basis_mixed` carried
  `severity="warning"` against a cataloged `major`. Eleven tests were added, each
  revert-checked to confirm it fails when its fix is removed. Domain gate: 135
  passed, 84.63% coverage.

- **2026-07-19 — Simulation post-build review corrections.** A read-only completion
  review returned `NOT READY` with six blocking findings; all six are now closed.
  Protective exits execute: `evaluate_protective_exit()` (`FR-SIM-043`) resolves
  stop-loss and take-profit against each tick and `EventDrivenExecutionEngine`
  closes triggered positions before matching pending orders, with same-tick
  conflicts resolved by `SAME_TICK_PRIORITY` so stop-loss always wins.
  `SimulationResult.closed_trades` is populated from engine-observed terminal
  closes carrying the `mae`/`mfe` observed during execution, replacing a
  permanently empty tuple. `AccountingSummary` is derived from the completed
  ledger, replacing hardcoded `commission=0`, `swap=0`, and
  `gross_profit=net_profit`; `AccountLedger.apply_fill()` now returns itemized
  costs so they can be attributed per position, and the orchestrator asserts
  `net_profit == gross_profit + commission + swap`. `SimulationStateStore` is a
  `Protocol` again: the SQLite implementation moved to
  `tests/simulator/_fixtures/sqlite_store.py`, and Simulation imports no `sqlite3`
  and executes no schema statement. The portfolio path measures instead of echoes:
  `component_return_series` is derived from each component's own simulated equity
  on a shared cadence (`FR-SIM-033`), reconciliation is an exact `Decimal`
  comparison of aggregate against component totals, FX lineage is resolved through
  the new `SimulationRunDependencies.resolve_fx_evidence()` seam and freshness
  validated, and `aggregate_metrics_ref` now points at a written artifact.
  `docs/PROJECT.md` rows for the four Simulation-owned contracts and the
  Simulation persisted-state row move from `Missing` to `Completed`. Supporting
  fixes: the engine no longer fabricates an acceptance tick when none exists
  (`average_price=None`, no invented price in the journal), equity now includes
  unrealized profit and loss via `AccountLedger.mark_to_market()` (`FR-SIM-042`)
  so margin admission accounts for open exposure, and `SimTrader.submit_order()`
  verifies route and Risk-approved volume before the engine is reached.
  Ruff lint and format pass; `mypy`, `pytest`, and coverage must be executed on
  the Windows toolchain.

- **2026-07-19 — Simulation domain completed.** Implemented the deterministic
  validation, timeline, accounting, state, journal, execution, reporting, and run
  boundaries, including isolated fast research and all-or-nothing portfolio runs.
  The final domain gate passes 112 tests at 82.37% coverage.

- **2026-07-19 — Analytics domain completed.** Implemented all active Analytics
  features and workflows, exact Simulation fixture parity, value-bearing metric
  goldens, and the Section 7 gate at 124 passing tests with 84.44% domain coverage.

- **2026-07-19 — Simulator build blockers resolved (owner-approved).** Simulator
  request, validation, accounting, matching, lifecycle, dependency, artifact,
  fast-research, export, workflow-test, and observational-performance contracts
  are exact; official execution has no implicit model, calendar, clock,
  liquidity, cost, or global-engine default.

- **2026-07-19 — Analytics implementation reached the allocation seam.** Built
  contracts, producer-neutral ledger adaptation, all metric kernels and golden
  fixture paths, hashing, serialization, comparison, portfolio aggregation, and a
  partial report builder; stopped before allocation rather than inventing missing
  dependence/concentration inputs or metric definitions.

- **2026-07-19 — Trading kill-switch freshness and root-port conformance fixed.**
  Added a required `kill_switch` bound to `MAX_STALENESS_SECONDS` so inactive but
  stale governance evidence fails readiness with `KILL_SWITCH_STALE` and blocks the
  live gate. Restored the repository-wide `__all__: tuple[str, ...]` package-root
  convention that the Trading build had regressed to a list.

- **2026-07-19 — Trading post-build review corrections completed.** Enforced truthful boundary redaction, required runtime safety bounds, deterministic timeout evidence, per-child paper/live emergency Risk authority, and exact report/state contracts. Added the missing rebalance, paper dispatch, bulk emergency, and standalone usage workflow evidence and reconciled the project contract registry.

- **2026-07-19 — Trading domain completed.** Built the complete route-aware
  execution domain across contracts, state, validation, routing, reconciliation,
  monitoring, live lifecycle, actions, reporting, public exports, and all fourteen
  workflow integrations, including authorized rebalance and live evaluation-cycle
  orchestration.

- **2026-07-19 — Risk domain completed.** Completed all Risk features and public
  exports, added dedicated policy-version and optional decision/snapshot migration
  records, and added structured trace/verdict/reason/latency/evidence logging for
  every material decision path.

- **2026-07-19 — Risk public/final integration gates added.** Added exact root
  exports, import-boundary enforcement, token/kill-switch security checks,
  supported-bound workload evidence, and fail-closed audit/token persistence;
  all thirteen documented Risk workflows now have passing integration evidence.

- **2026-07-19 — Risk focused reporting implemented.** Added deterministic
  Markdown/exact-JSON rendering with separated evidence, calculations,
  assumptions, warnings, decisions, and recommendations; five tests pass at
  89% focused coverage with token-bound approval-claim protection.

- **2026-07-19 — Risk advisory scenarios implemented.** Added immutable bounded
  aggregate shock analysis with explicit relative/ratio semantics, deterministic
  seed provenance, no invented distribution, and four focused tests at 86% coverage.

- **2026-07-19 — Risk canonical Decisions implemented.** Added fixed-precedence
  trade/current-state governance, typed kill-switch hierarchy and authorized
  CAS transitions, concurrent-capacity disclosure, durable approval issuance,
  and non-authorizing decision reuse; 19 focused tests pass at 81% coverage.

- **2026-07-19 — Risk durable approvals implemented.** Added HMAC-SHA-256
  decision/attestation binding, injected secret and authorization dependencies,
  atomic single-use consumption, scoped revocation, audit evidence, runnable
  examples, and live-profile workflow evidence at 81% focused coverage.

- **2026-07-19 — Risk regime assessment implemented.** Added deterministic
  volatility, liquidity, correlation, drawdown, crisis, news, and session states,
  explicit transitions, and tightening-only modifiers. Unit, usage, and workflow
  integration evidence passes at 83% focused coverage.

- **2026-07-19 — Risk Policy gates implemented.** Added ordered portfolio and
  normalized market-context limits, immutable Strategy eligibility, allocation
  cap review, and version-exact atomic Risk-budget activation. The 23-case targeted
  gate and real audit-chain integrations pass at 84% focused Policy coverage.

- **2026-07-19 — Risk tamper-evident audit boundary implemented.** Added
  receiver-owned atomic persistence ports, SHA-256 continuity, canonical
  redaction, deterministic verification, Risk-owned migrations, and targeted
  usage/unit evidence at 81% feature coverage.

- **2026-07-19 — Strategy usage converted to real standalone examples.**
  Replaced pytest-style usage cases with 14 numbered scripts using package-root
  exports; market and concrete-strategy examples retrieve real MT5 evidence and
  print evaluated prices, signal states, and entry markers. A subprocess integration
  check distinguishes passing examples from explicit evidence-unavailable exits,
  while stateful registry access remains opt-in.

- **2026-07-19 — Concrete Strategy signal parity implemented.** Replaced the
  removed bundled signal sources with seven immutable, hash-bound evaluators and
  an atomic point-in-time evaluation boundary; all 47 requirements and ten
  workflows pass in the current 79-case suite at 81.11% Strategy coverage, with
  four real-evidence examples explicitly skipped when their prerequisites are
  unavailable.

- **2026-07-18 — Strategy domain implemented.** Built the initial 37
  `FR-STR-*` requirements and nine `WF-STR-*` workflows with immutable
  Data-backed registry, configuration, mutation, and checkpoint state; 92 tests
  pass at over 80% domain coverage, with Ruff, formatting, security, imports,
  and prescribed mypy clean. The 2026-07-19 signal-parity addition
  (`FR-STR-038`–`FR-STR-047`) brought the current total to 47 requirements.

- **2026-07-18 — Indicators post-build review corrections.** Usage examples are
  confirmed as standalone runnable scripts (`usage/NN_*.py`) exercising real data
  and connections — excluded from pytest collection via a usage `conftest.py`,
  verified (executed or explicitly skipped when live data is unavailable) by
  `test_usage_scripts.py`, and repointed in the README. Also: capability-matrix
  dependencies corrected to `("numpy", "pandas")` for every indicator, the Doji
  zero-range edge case aligned to `FR-INDI-031`, per-function logging completed,
  and the input-mutation finalization check wired in.

- **2026-07-16 — Indicators domain implemented with one indicator per file.**
  Built the complete Indicators domain per its README: the Core calculation
  boundary and 20 official built-ins across trend, volatility, momentum, volume,
  and candles, with retired bundled modules removed and SMC explicitly excluded.
  All 34 `FR-INDI-*` requirements pass in 127 tests; the package is Ruff/mypy clean
  and reaches 91% statement-and-branch coverage against the 80% gate.

### Verification

- **2026-07-19 — Trading final Definition of Done.** The complete Trading gate
  passes 188 tests at 84.54% statement-and-branch coverage; Trading formatting,
  Ruff, 42-source-file mypy, public-import, standalone usage, docstring/logger,
  and direct secret scans are clean, with Broker mutation compatibility passing.

- **2026-07-19 — Risk final Definition of Done.** The complete Risk gate passes
  150 tests at 82.03% coverage; Risk formatting, Ruff, 34-source-file mypy,
  import/security/persistence/workload checks, and a direct secret scan are clean.

- **2026-07-19 — Strategy canonical mypy gate.** `Success: no issues found in 87 source files`
  from `uv run mypy app/services/strategy tests/strategy`.

### Decisions

- **2026-07-19 — Optimization V1 blockers resolved.** V1 search is limited to bounded
  grid and seeded random methods; objectives project Analytics-owned metric evidence,
  execution crosses a typed Simulation adapter, walk-forward splits use caller-supplied
  equally spaced UTC observations, and persistence uses an injected Optimization-owned
  store port over Data's public migration contract. Genetic/Bayesian search, live
  authority, Strategy mutation, UI rendering, and automatic adoption remain excluded.
- **2026-07-19 — Analytics quality-flag emission policy fixed.** `FR-ANLT-043` and
  the `WF-ANLT-001` failure behaviour now state exactly which cataloged flags a
  report carries and when. `quality_flags` is empty of blocker evidence only when
  the report is a complete, clean measurement, so a diagnostic partial report can
  never be mistaken for a complete one. `intratrade_exposure_unobserved` is emitted
  on every report, because a closed-trade curve can never observe open-position
  exposure — it is a permanent property of the basis, not a conditional caveat.

- **2026-07-19 — Analytics metric kernels accept the run configuration.**
  `FR-ANLT-028`, `-029`, `-030`, `-031`, `-035`, and `-037` gained a keyword-only
  `config: AnalyticsRunConfig`, which is the bound `build_warning()` requires. These
  are internal feature APIs (§2), not package-root exports, so no cross-domain
  consumer is affected. `align_benchmark_series` (`FR-ANLT-033`) deliberately did
  **not** gain `config`: it emits no warning today, and carrying a dead parameter
  would be speculative. `benchmark_duplicate_resolved` needs a return-shape change
  and is left to the deferred evidence-code work.

- **2026-07-19 — Portfolio simulation seam frozen.** Simulation `FR-SIM-033` now
  owns exact aligned `component_return_series` evidence in
  `PortfolioSimulationResult v1`, enabling Analytics correlation/concentration
  projection and closing `D-ANLT-004`.

- **2026-07-19 — Trading review decisions ratified.** Bulk paper/live emergency actions use Option A per-child `RiskDecisionPackage` injection; Broker dispatch receives an injected clock and validated operation timeout; Trading usage evidence is exposed through numbered standalone scripts. Runtime retention, concurrency, and per-evidence staleness bounds remain required and fail closed, while the Broker operation timeout keeps the ratified ten-second default.

- **2026-07-19 — Data tick-series generation implemented.** Added
  `processing/ticks.py` with `generate_tick_series` and
  `generate_tick_series_to_parquet`, four models (`real`, `trading_bar`, `ohlc_m1`,
  `generated`), three spread models, `Decimal` quantization at the contract boundary,
  and output-aware Parquet chunking. Wired through `processing/__init__`,
  `public_api/operations`, and the package root. `FR-DATA-087`–`FR-DATA-090` and
  `WF-DATA-016` are `Completed`.

- **2026-07-19 — `TickRecord` extended additively.** Added optional
  `source_bar_time`, `tick_index_in_bar`, and `bar_phase`, all defaulting to `None`.
  Per `docs/PROJECT.md` §5 this is an additive change requiring no version bump;
  provider-sourced ticks and every existing consumer are unaffected. The fields carry
  intra-bar position evidence that bar-derived ticks need and that the canonical
  record previously could not express under `extra="forbid"`.

- **2026-07-19 — Data usage-example paths corrected.** Thirteen `FR-DATA-*` rows cited
  `tests/data/usage/05_processing.py`; the processing examples live in
  `03_processing.py` and `05_feeds.py` is the feeds file. Pre-existing defect fixed in
  the same pass.

- **2026-07-19 — Tick-series generation assigned to Data, superseding a prior
  exclusion.** `app/services/data/README.md` previously stated "Do not retain
  `TicksGenerator` or any trading-bar/M1/real backtest model in Data." The owner
  reversed that: deriving ticks from real evidence is a deterministic
  `MarketDataset → MarketDataset` transform belonging beside resampling, alignment,
  and aggregation. Added `FR-DATA-087`–`FR-DATA-090`, `WF-DATA-016`, `CAP-DATA-022`,
  and `processing/ticks.py` with four models (`real`, `trading_bar`, `ohlc_m1`,
  `generated`) and three spread models (`native`, `fixed`, `variable`). Prices come
  from real OHLC bounds or real quotes and tick counts from real `tick_volume`; only
  the intra-bar path shape is constructed, deterministically. Simulation consumes the
  result and derives no ticks of its own.

- **2026-07-19 — Real-evidence tick generation separated from GBM synthesis.**
  `generate_synthetic_dataset` (`FR-DATA-039`) fabricates prices from a random walk
  and is now explicitly fixtures-and-tests only; it must never reach an official
  Simulation run, and the boundary is enforced by test. The two capabilities shared
  the word "synthetic" while differing on whether the data is real, which was a latent
  path to a legitimate-looking backtest on invented prices.

- **2026-07-19 — Strategy concepts removed from tick generation.** The V1
  `TicksGenerator` merged `entry_signal`, `exit_signal`, `pending_signal`, `sl`, and
  `tp` onto ticks. Data owns no trading decision logic, and the target Simulation is
  event-driven — it calls Strategy per tick through its public boundary — so signal
  pre-joining is obsolete rather than merely misplaced. No Data tick record carries a
  signal, order, position, stop-loss, or take-profit field.

- **2026-07-19 — Simulation specification completed.** Closed all ten blockers from
  the pre-build audit. Added `errors.py` with `SimulationError` and the closed
  `SIM_ERROR_CATALOG` (`FR-SIM-035`–`037`), replacing an unenumerated taxonomy that 24
  requirements already raised. Added the `SimulationStateStore` port and Simulation-owned
  migrations (`FR-SIM-041`), replacing a dependency on Data persistence internals that
  Data does not export. Fixed `FR-SIM-038` as the bound asynchronous
  `SimTrader.submit_order` method matching the
  `Callable[[OrderIntent], Awaitable[ExecutionReceipt]]` port Trading injects, with
  no module-global engine or standalone dispatcher. Added the portfolio backtest
  path (`FR-SIM-032`–`034`) for two registered
  contracts that previously had no requirement, file, or function. Split `FR-SIM-010`
  into `validate_fx_evidence` and `convert_fx_amount` (`FR-SIM-039`). Corrected the
  `WF-SIM-003` diagram, which routed Optimization through the non-canonical research
  path, and the `WF-SIM-001` diagram, which mislabelled two requirements. Removed
  eleven references to a V1 implementation the owner had deliberately deleted,
  including an instruction not to delete files that no longer existed.

- **2026-07-19 — `SimulationResult v1` publishes the closed-trade ledger.**
  `FR-SIM-040` defines `ClosedTradeRecord` with the seventeen fields of Analytics
  `FR-ANLT-049`, and `FR-SIM-024` carries both `fills` (execution events) and
  `closed_trades` (paired round-trips), plus `initial_balance` and `account_currency`.
  `FR-SIM-020` now requires per-open-position excursion tracking so `mae` and `mfe`
  are observed during execution rather than reconstructed afterwards. This freezes the
  seam for the parallel Analytics build and closes `D-ANLT-003`.

- **2026-07-19 — Simulation/Analytics seams and activation inputs fixed.** `FR-SIM-024` publishes the exact Analytics-owned 17-field closed-trade projection, `FR-SIM-033` owns the complete `PortfolioSimulationResult v1` schema, `FR-ANLT-051` supplies explicit bounded runtime/statistical/risk-free inputs, Simulation and Analytics may build concurrently with `reports/allocation.py` last, and the former `D-ANLT-007` is resolved by retaining the initial scorecard exclusion.

- **2026-07-19 — Analytics canonical input fixed as the closed-trade ledger.** The
  owner resolved `D-ANLT-001`, `D-ANLT-002`, and `D-ANLT-003`. `FR-ANLT-049`
  (`ClosedTrade`) defines the 17-field ledger row — ticket, symbol, type, volume,
  entry/exit time and price, stop loss, take profit, comment, commission, swap,
  profit, magic, MAE, MFE. `FR-ANLT-050` derives the equity curve from it as
  `initial_balance + cumsum(net_trade_pnl)` ordered on `(exit_time, ticket)`, plus a
  UTC calendar-daily resample for time-based metrics. `initial_balance` and
  `account_currency` are required arguments and fail closed when absent. Drawdown is
  closed-trade basis, labelled `curve_basis="closed_trade"`, with
  `max_intratrade_excursion` reported separately from MAE because open-position
  exposure is not observable in the curve.

- **2026-07-19 — Analytics cost convention corrected to MT5 gross `profit`.**
  Supersedes the cost clause of the ledger decision above, which was first recorded
  with `profit` net of costs. `profit` is **gross** — price movement only — and
  `commission` and `swap` are separate negative amounts. The canonical per-trade
  figure is `net_trade_pnl = profit + commission + swap`, and it is the basis for the
  equity curve and for every classification, aggregation, and ratio metric. Win/loss
  classification is therefore net, so a gross winner with larger costs is correctly
  counted as a loser. `gross_pnl_before_costs` (`sum(profit)`) and `trade_efficiency`
  (`profit / mfe`) are the only two rows that consume raw `profit`; efficiency stays
  gross on both sides because MFE is itself a price-movement figure and mixing bases
  would conflate execution quality with cost structure.

- **2026-07-19 — Analytics R-multiple given a realized-risk fallback.** `r_multiple`
  now has two ordered bases: `declared_stop` (primary), and `realized_mae`
  (`net_trade_pnl / abs(mae)`) when no usable stop price exists. Every trade carries
  its applied basis; a fallback emits `r_multiple_mae_fallback` and a mixed ledger
  emits `r_multiple_basis_mixed`, so declared and realized risk are never averaged
  without disclosure. Added `r_multiple_basis` and `r_multiple_potential`
  (`mfe / abs(mae)`), which separates available edge from exit timing.

- **2026-07-19 — Analytics Metric Definition Catalog approved.** `D-ANLT-005` closed.
  56 metric rows carry complete formula, unit, input, scale, annualization, sample,
  minimum-sample, undefined-behavior, evidence-type, and golden-fixture definitions.
  Industry-standard resolutions adopted: historical VaR returned as a signed return;
  Van Tharp price-based R-multiple; simple returns; bias-corrected G1 skewness and
  excess G2 kurtosis; linear percentile interpolation; Tukey-fence outliers; fixed
  50-bin histogram for determinism; Benjamini-Hochberg FDR; percentile-method
  bootstrap; add-one-corrected permutation p-values; Sortino downside deviation over
  all observations with MAR = 0. `expected_shortfall` was removed as mathematically
  identical to `conditional_var`. `gross_profit` / `gross_loss` were renamed
  `sum_winning_pnl` / `sum_losing_pnl` to avoid collision with
  `gross_pnl_before_costs`. The catalog is 58 rows after the cost-convention
  correction and the R-multiple basis additions recorded below.

- **2026-07-19 — Analytics Evidence Catalog approved.** `D-ANLT-006` closed. Warning
  and quality-flag namespaces fixed with 18 and 11 codes respectively, each traced to
  a written failure behavior. Uncataloged codes are rejected at construction.

- **2026-07-19 — Analytics `PortfolioAllocationEvidence v1` given an owning
  requirement.** The contract was registered in `docs/PROJECT.md` §5 and exported at
  the Analytics package root but had no §4 definition or builder. Minted
  `FR-ANLT-047` (contract in `contracts/models.py`) and `FR-ANLT-048` (projector in
  the new `reports/allocation.py`), and corrected the `WF-ANLT-013` requirement
  sequence, which previously terminated in the Analytics-internal
  `PortfolioPerformanceReport`. Reserved IDs `FR-ANLT-015` and `FR-ANLT-019` were
  not reused.

- **2026-07-19 — Analytics seam phasing separated from dependency order.** Appendix P
  placed `reports/` in phase 1 and `metrics/` in phase 7 while `reports/builder.py`
  imports `metrics.groups`. A `P-ANLT-NNN` phase now explicitly fixes only when a
  public seam appears; the §2 dependency order governs implementation. `FR-ANLT-038`
  and `FR-ANLT-043` are seam-only in phase 1 and complete in phase 7.

- **2026-07-19 — Analytics scorecards excluded from the initial build.**
  `FR-ANLT-014`, `FR-ANLT-044`, `WF-ANLT-004`, and the `scorecards/` files are
  `Excluded` because `STRATEGY_QUALITY_THRESHOLDS` and
  `ALLOWED_RECOMMENDATION_LANGUAGE` have no owner-approved value and Analytics owns no
  promotion-adjacent threshold. `P-ANLT-005` still authorizes the phase-7 seam.

- **2026-07-19 — Analytics undefined limits are required fail-closed settings.** The
  nine limits with a `None` default are supplied explicitly with no fallback; a public
  operation invoked without its required limit raises `AnalyticsValidationError`. No
  numeric value was invented. `RISK_FREE_RATE` is confirmed a caller-supplied argument
  rather than a module constant.

- **2026-07-19 — Analytics `to_json_safe` collision resolved.** `FR-ANLT-025` is
  renamed `to_report_json_safe` and narrowed to normalizing pandas/NumPy values and
  translating Utils `ValidationError` into `AnalyticsValidationError` before delegating
  to the Utils-owned `to_json_safe`. This restores the boundary rule already stated by
  the `Removed` `FR-ANLT-024` and `FR-ANLT-026`.

- **2026-07-19 — Trading contract registry status reconciled.** `OrderIntent v1`,
  `TradeRecord` / `ExecutionReceipt v1`, `OperationalEvent v1`, and the Trading
  execution-state store were still recorded as `Missing` in `docs/PROJECT.md` §5 and
  §5 Data ownership after the Trading domain completed. All four are now `Completed`.

- **2026-07-19 — Analytics V1/V2 reuse instructions withdrawn.** Six "reuse V1" and
  one "V2 historical inventory" reference in the Analytics README pointed at source
  that does not exist in this repository. Each is restated as a direct requirement so
  no implementer infers behavior from an unavailable tree.

- **2026-07-19 — Remaining Trading execution contracts resolved.** Strategy
  `TradeIntent v1` now carries explicit order type and applicable entry/TIF
  material as immutable Risk lineage; Risk publishes a plan-bound
  `PortfolioBudgetExecutionVerdict v1`; Trading consumes normalized symbol
  capability evidence, binds live gates to an injected `LiveSession`, uses complete
  rebalance action rows, canonical control-scope fields and cancellable states, and
  queries official reporting evidence through its state-store port. The owner
  explicitly authorized the necessary additive Strategy, Risk, and Trading-state
  contract/document/test changes.

- **2026-07-19 — Trading executable-intent mapping resolved.** `OrderIntent v1`
  carries approved order type, validated quantity unit, optional order instructions,
  and Trading-state target identities; `BrokerConnectionConfig` remains the sole
  source of broker environment/account material during receiver-owned DTO adaptation.

- **2026-07-19 — Risk registry status reconciled after post-build review.**
  `docs/PROJECT.md` marked all ten Risk-owned `v1` contracts (`RiskDecision`,
  `ScenarioResult`, `StrategyOperationalEligibilityRequest`/`Decision`,
  `AllocationReviewRequest`, `AllocationRiskDecision`,
  `AllocationBudgetActivationRequest`, `ApprovalAttestation`,
  `ActionPolicyVerdict`, `KillSwitchCommand`, `KillSwitchState`) and the Risk
  persisted-state row `Completed`, matching the registry legend (`Completed` =
  implemented, tested, and verified) and the verified Risk build (150 tests,
  82.03% coverage). The `app/services/risk/README.md` package status was
  corrected from `Missing` to `Completed`, and the `admission.py` dependency
  cell now declares all three imported public Strategy symbols
  (`StrategyEnvironment`, `StrategyLifecycleStatus`, `ValidatedStrategyRef`).
  Cross-domain `SYS-WF-*` rows and other unbuilt domains remain `Missing`.

- **2026-07-19 — Evaluation-cycle driver relocated to `actions/` (cycle fix).**
  `run_live_evaluation_cycle` (`FR-TRD-065`) moved from `live/runtime.py` to
  `actions/runtime.py`: a driver that uses `TradingDependencies` and calls the
  validate→gate→dispatch path must sit above the layers it invokes, so hosting it
  in `live/` created a `live ↔ actions` cycle (`actions` already depends on
  `live`). `actions/` is the top capability layer, so the cycle is removed and the
  `LIV → ACT` order preserved. `TradingDependencies` (`FR-TRD-056`) now also carries
  the Data/Indicators/Strategy/Risk read ports for the cycle and the current
  Risk-state sources (`KillSwitchState`, `AllocationRiskDecision`,
  `StrategyOperationalEligibilityDecision`) for rebalance execution. Corrected
  `FR-TRD-065` so a neutral signal is a normal no-mutation `StandardTradingEnvelope`
  outcome, not a `TradingError`.

- **2026-07-19 — Live/paper runtime loop confirmed Trading-owned (Option A).**
  `docs/PROJECT.md` `SYS-WF-002` step 1 assigns the Data→Indicators→Strategy→Risk
  loop to Trading, but §4 had no requirement for it. Added `FR-TRD-065` and
  `live/runtime.py` (`run_live_evaluation_cycle`) plus workflow `WF-TRD-014`
  (`FR-TRD-065 → FR-TRD-012 → FR-TRD-036`); `WF-TRD-012`'s input boundary now
  states the approved `RiskDecision` is produced within that cycle. Trading
  orchestrates only through public domain APIs and never computes indicators,
  generates signals, or sizes/approves. `docs/PROJECT.md` left unchanged.

- **2026-07-19 — Trading execution path made async.** `dispatch_order_intent`,
  every mutation-capable action verb (`FR-TRD-013`–`FR-TRD-023`, `FR-TRD-050`,
  `FR-TRD-064`), `LiveSession.start`/`stop`, `evaluate_live_gate`, and the injected
  simulation callback are `async` so they call the async Brokers `BrokerAdapter`
  mutation operations directly. No synchronous broker bridge (e.g. `asyncio.run`
  inside a live loop) is permitted; `LiveSession.status()` remains synchronous
  (read-only local state). Resolves the sync-Trading-vs-async-Brokers conflict.

- **2026-07-19 — `PortfolioRebalanceExecutionRequest v1` mapped into Section 4.**
  The Trading-owned contract now has `FR-TRD-063` (model in `contracts/models.py`)
  and `FR-TRD-064` (validation/idempotent adaptation in the new
  `actions/rebalance.py`, `execute_portfolio_rebalance`), each with usage and unit
  tests; `WF-TRD-013` sequence begins `FR-TRD-063 → FR-TRD-064`. Trading never
  recalculates target weights and keeps over-budget correction reduce-only unless
  Risk authorizes an increase. Closes the unmapped-required-contract gap.

- **2026-07-19 — Trading monitoring seam scheduled to Phase 1.** The Trading
  `monitoring` package (`P-TRD-006`) was moved from delivery Phase 11 to Phase 1
  because the §2 module dependency diagram routes `monitoring → live` and
  `monitoring → reporting`, and `live/session.py` and `reporting/evidence.py`
  declare `monitoring` as a local dependency; the prior Phase 11 assignment made
  those Phase 1 modules unbuildable. Only the minimal seam (`OperationalEvent`,
  `emit_runtime_event`, `BudgetGate` — `FR-TRD-046/047/048`) is required in
  Phase 1; extended monitoring breadth is deepened behind that seam later.
  Also corrected in the Trading README: `state/migrations.py` /
  `FR-TRD-042` now reference Data's real `MigrationStep` contract (not the
  non-existent `MigrationDefinition`), and §4 implementation notes were reworded
  to greenfield design constraints since no prior Trading implementation exists.

- **2026-07-19 — Risk Decisions contract gaps resolved.** Governor paths now
  receive typed applicable kill-switch state, kill checks receive config/auth
  trace context, current-state compliance never invents a trade size, and reuse
  returns `DecisionReuseValidationResult` rather than a consumed-token result.

- **2026-07-19 — Risk approval state semantics approved.** The private
  receiver-owned store uses exact synchronous issue, consume-if-active, and
  revoke-intersecting operations; only one concurrent reservation succeeds,
  expected scope is exact, and config compatibility remains explicit/default-deny.

- **2026-07-19 — Risk Policy baseline semantics approved.** Functional defaults
  now cover loss, drawdown, margin, leverage, historical tail risk, and concentration
  while remaining profile-overridable; limit precedence and ratio bases are exact.
  V1 market policy uses exact spread units and normalized session/calendar states,
  treats liquidity as availability-only because its contract has no unit, and excludes
  slippage because that evidence is absent and receiver-owned after execution.

- **2026-07-19 — Five initial Risk pre-build blockers resolved (owner-approved).**
  `ProposedTrade` now embeds the complete public `TradeIntent v1`; persistent
  eligibility, allocation-budget, audit, and kill-switch work uses private injected
  Risk ports over Data infrastructure; `RiskConfig v1` has an exact fail-closed
  schema; PyYAML 6.0.3 is direct; and the supporting Risk test-file manifest is
  explicitly in scope. Audit primitives precede persistent policy gates, no
  production profile invents owner thresholds, and paper/live configuration remains
  deployment-supplied and fail-closed when absent.

- **2026-07-19 — Strategy contract registry reconciled.** The delivered
  `TradeIntent`, `StrategyMutationResult`, `StrategyRegistrationRequest`, and
  `StrategyParameterUpdateRequest` contracts are now correctly marked `Completed`.

- **2026-07-19 — Strategy signal-parity specification adopted
  (owner-resolved).** The seven recovered strategies preserve testable signal
  rules only; legacy loading plus basket, order, fill, broker, risk, and execution
  behavior remain excluded.

- **2026-07-18 — Strategy build specification corrections adopted
  (owner-resolved).** Strategy now owns migration definitions, receives explicit
  validation policy, invokes only injected hash-bound evaluators, returns mutation
  truth directly, persists checkpoints through Data, and uses receiver-owned event
  evidence; the obsolete flat modules and bundled `pybots` implementation were
  removed.

- **2026-07-18 — Strategy pre-build spec blockers resolved (owner-resolved).** The duplicate `FR-STR-017` was resolved by renumbering `StrategyDiagnostics` to `FR-STR-034` (leaving `StrategyMutationResult` = `FR-STR-017`), so every Strategy public symbol now maps to exactly one requirement. `StrategyMutationResult` is now exported (contracts `outcomes.py` and the package public API) and documented as the `WF-STR-008` output boundary published via register/update event-publication. Appendix P `First phase` is clarified as seam-establishment authorization only; Section 2 dependency order governs full `FR-STR-*` implementation sequencing.

- **2026-07-16 — Source policy made non-blocking with default fallback (owner-resolved).** Resolving missing source policies no longer raises `POLICY_BLOCKED` or fails closed. The system now automatically falls back to a default permissive `SourcePolicyConfig` (rate limit: 10,000 attempts per 60s, circuit breaker: 5 consecutive failures, recovery: 30s) to allow unassisted base-level execution.

- **2026-07-16 — Phase 1 Utils seams clarified (owner-resolved).** Logging sink configuration failure emits only the fixed safe fallback and then raises `ConfigurationError`; the stable error-metadata and settings-model field shapes are fixed in the Utils specification. Phase 1 may use private redaction mechanics for logging while public redaction functions and diagnostics remain assigned to Phase 2.

- **2026-07-16 — Existing foundation domains retained (owner-resolved).** Utils, Brokers, and Data are completed implementation baselines and shall not be rebuilt by later agile phases; their allocated steps become compatibility/regression gates unless a genuinely unsatisfied requirement is identified. Current semantic-docstring/format cleanup is tracked separately from functional completion.

- **2026-07-16 — Indicators and Strategy sequencing expanded (owner-resolved).** Indicators is built as one complete domain covering Core, trend, volatility, momentum, volume, and candles, followed by the complete Strategy domain. Later roadmap phase allocations for already completed features become regression gates rather than duplicate implementation.

- **2026-07-16 — Retrospective SMC excluded from Indicators (owner-resolved).** SMC/FVG/swing/BOS/CHoCH labels are not part of the production registry because their retroactive confirmation can repaint already-published rows; the approved surface remains immutable and causal.

- **2026-07-16 — Indicator v1 calculation boundary fixed (owner-resolved).** Official calculations consume one Data-owned `MarketDataset v1`, privately project it to pandas/NumPy, preserve non-empty short-history rows as unavailable warmup output, and return an Indicator-owned immutable-copy `IndicatorSeries v1`; multi-symbol and multi-timeframe orchestration remain caller/Data responsibilities. Synchronous Indicators owns no timeout/cancellation mechanism, and golden fixtures—not `pandas-ta`—are the formula authority.

- **2026-07-16 — Three phantom requirement IDs reserved/struck; `FR-UTL-025` restored as active.** `FR-ANLT-015`, `FR-ANLT-019`, and `FR-API-052` remain unused numbering gaps. `FR-UTL-025` is implemented by `resolve_secret_reference` and is no longer described as reserved or a no-op.

- **2026-07-16 — Provisional roadmap IDs promoted to authoritative (full pass).** The agile delivery roadmap (`docs/dev/AGILE_ROADMAP.md`, canonical build plan) minted provisional `P-*` requirement IDs; all 115 are now authoritative — `P-SYS-001`–`006` added to `docs/PROJECT.md` §7, and every `P-<domain>-*` added to its owning README as an Appendix P component requirement. No scope was added or changed; each ID gives a citable anchor to already-specified structure so the coding agent can build against it.

- `Open Decisions` sections are reserved exclusively for unresolved owner choices.
  Once resolved, the subject is removed from that section and the outcome becomes an
  ordinary requirement, contract, workflow, configuration rule, boundary, or explicit
  exclusion in the authoritative Project or README specification. Resolution history
  is recorded in this `Decisions` section; ADR, and other standalone
  decision-record documents are not created.

### Changed

- **2026-07-16 — Canonical tick DataFrame projection added.** Data now exports
  `to_tick_dataframe(dataset)`, returning a detached UTC-indexed float64 frame with
  `bid`, `ask`, `last`, and `volume`; genuine optional missing values remain `NaN`,
  and common price/volume units are retained in DataFrame metadata.

- **2026-07-16 — Canonical OHLCV DataFrame projection added.** Data now exports
  `to_ohlcv_dataframe(dataset)`, which returns a detached analytical copy with a
  UTC timestamp index and exactly six finite float64 columns: OHLCV plus genuine
  provider-reported per-bar spread. The common native spread unit is retained in
  DataFrame metadata; incomplete spread evidence fails closed. Raw provider frames
  remain prohibited, and the source `MarketDataset` remains the authoritative
  precision, quality, provenance, and availability evidence.

- **2026-07-16 — Data Retrieval and Reference facade made standalone-usable.**
  All nine package-root retrieval/reference operations now accept direct keyword
  arguments as well as their existing typed requests. MT5 source registration,
  read-only Brokers composition, provider-confirmed identity mapping, Data
  migrations, and calendar resolution occur lazily behind the facade; the usage
  reference no longer assembles registries, adapters, identities, migrations, or
  calendar objects. MT5 now also fulfills its released historical-bar and
  provider-derived spread reads, with valid bar closing timestamps.

- **2026-07-16 — Simplified Utils, Brokers, and Data public API usage scripts.**
  Rewrote all usage examples under `tests/utils/usage/`, `tests/brokers/usage/`,
  and `tests/data/usage/` to target only the package public exports unassisted,
  directly at the base level, removing all unused complex classes and files.

- **2026-07-16 — Phase 1 Utils documentation corrected.** Every Stage 2 Utils
  class and function now has caller-oriented Google-style documentation for its
  inputs, outputs, errors, attributes, invariants, and material side effects.

- **2026-07-16 — Semantic docstring enforcement enabled.** Ruff now enforces
  explicit Google section ordering and return, yield, parameter, and directly
  raised-exception consistency; the Utils AST test enforces required `Args:`
  and `Attributes:` sections that Ruff cannot require.

- **2026-07-16 — Executable usage examples made visible.** Every Stage 2 Utils
  usage program now prints labeled, bounded, secret-safe demonstration output,
  and integration tests reject silent example scripts.

- **2026-07-16 — Bounded prints and headers added to Data Domain usage examples.** Every Data Domain usage script in `tests/data/usage/` now prints clean, descriptive console headers and outputs demonstrating their operations directly.

- **2026-07-16 — Settings usage output aligned to `.env`.** The executable
  settings example now displays only explicitly allowlisted non-secret
  application values from the repository `.env`; integration tests reject
  sensitive setting names in its output.

### Fixed

- **2026-07-16 — Live standalone Data retrieval example repaired.** Completed
  required local SQLite configuration, added the expected database directory,
  mapped native MT5 NumPy records correctly, and preserved valid availability
  evidence when provider timestamps lead the local clock. The executable example
  now distinguishes missing local manifests and unavailable MT5 schedule
  capabilities from retrieval failures.

- **2026-07-16 — Foundation and Indicator specifications reconciled.** Corrected
  Data's status legend, restored its authoritative Appendix P, aligned implemented
  contracts/state/configuration in `docs/PROJECT.md`, recorded the actual empty
  Indicator scaffold inventory, fixed its exact file/requirement order, contracts,
  formulas, validation precedence, tests, and workflow gates, removed contradictory
  DataFrame/warmup/timeout/reference-library requirements, and added direct locked
  NumPy 2.4.6 and pandas 3.0.3 dependencies.
