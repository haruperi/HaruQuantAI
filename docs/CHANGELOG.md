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

### Added

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

- **2026-07-19 — Risk final Definition of Done.** The complete Risk gate passes
  150 tests at 82.03% coverage; Risk formatting, Ruff, 34-source-file mypy,
  import/security/persistence/workload checks, and a direct secret scan are clean.

- **2026-07-19 — Strategy canonical mypy gate.** `Success: no issues found in 87 source files`
  from `uv run mypy app/services/strategy tests/strategy`.

### Decisions

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
