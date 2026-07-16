# Changelog

This document is only for adding high-level changes, decisions, or status updates that affect the entire project. It does not contain the detailed changes for each module or service. Please refer to the README.md files in each module or service for more information. Each item should be written in a very brief way that it is easy to understand and can be used to track the progress of the project. Not more than 3 sentences per item.

### Status

- Utils, Brokers, and Data are recorded as completed implementation baselines after
  independent deterministic domain verification. The complete system remains
  `Missing`, and repository-wide documentation-quality cleanup remains tracked.

### Added


### Decisions

- **2026-07-16 — Phase 1 Utils seams clarified (owner-resolved).** Logging sink configuration failure emits only the fixed safe fallback and then raises `ConfigurationError`; the stable error-metadata and settings-model field shapes are fixed in the Utils specification. Phase 1 may use private redaction mechanics for logging while public redaction functions and diagnostics remain assigned to Phase 2.

- **2026-07-16 — Existing foundation domains retained (owner-resolved).** Utils, Brokers, and Data are completed implementation baselines and shall not be rebuilt by later agile phases; their allocated steps become compatibility/regression gates unless a genuinely unsatisfied requirement is identified. Current semantic-docstring/format cleanup is tracked separately from functional completion.

- **2026-07-16 — Indicators and Strategy sequencing expanded (owner-resolved).** Indicators is built as one complete domain covering Core, trend, volatility, and momentum, followed by the complete Strategy domain. Later roadmap phase allocations for already completed features become regression gates rather than duplicate implementation.

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

- **2026-07-16 — Foundation and Indicator specifications reconciled.** Corrected
  Data's status legend, restored its authoritative Appendix P, aligned implemented
  contracts/state/configuration in `docs/PROJECT.md`, recorded the actual empty
  Indicator scaffold inventory, fixed its exact file/requirement order, contracts,
  formulas, validation precedence, tests, and workflow gates, removed contradictory
  DataFrame/warmup/timeout/reference-library requirements, and added direct locked
  NumPy 2.4.6 and pandas 3.0.3 dependencies.
