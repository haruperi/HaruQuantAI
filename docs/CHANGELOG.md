# Changelog

This document is only for adding high-level changes, decisions, or status updates that affect the entire project. It does not contain the detailed changes for each module or service. Please refer to the README.md files in each module or service for more information. Each item should be written in a very brief way that it is easy to understand and can be used to track the progress of the project. Not more than 3 sentences per item.

### Status

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

- **2026-07-19 — Strategy canonical mypy gate.** `Success: no issues found in 87 source files`
  from `uv run mypy app/services/strategy tests/strategy`.

### Decisions

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
