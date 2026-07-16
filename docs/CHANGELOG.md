# Changelog

This document is only for adding high-level changes, decisions, or status updates that affect the entire project. It does not contain the detailed changes for each module or service. Please refer to the README.md files in each module or service for more information. Each item should be written in a very brief way that it is easy to understand and can be used to track the progress of the project. Not more than 3 sentences per item.

### Status

- Documentation alignment review updated to implementation-ready after consistency
  validation; domain implementation statuses remain unchanged unless independently
  verified against their target specifications.

### Added


### Decisions

- **2026-07-16 — Phase 1 Utils seams clarified (owner-resolved).** Logging sink configuration failure emits only the fixed safe fallback and then raises `ConfigurationError`; the stable error-metadata and settings-model field shapes are fixed in the Utils specification. Phase 1 may use private redaction mechanics for logging while public redaction functions and diagnostics remain assigned to Phase 2.

- **2026-07-16 — Four phantom requirement IDs reserved/struck (owner-resolved).** `FR-UTL-025`, `FR-ANLT-015`, `FR-ANLT-019`, and `FR-API-052` are unused numbering gaps that appear only inside inclusive `X through Y` ranges and define no behavior (their numeric neighbors are defined and each owning module is complete without them). They are declared reserved (Appendix R in the owning READMEs), the spanning ranges now exclude them, and the `FR-UTL-025` build step is a reserved no-op. No scope was lost.

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

- **2026-07-16 — Settings usage output aligned to `.env`.** The executable
  settings example now displays only explicitly allowlisted non-secret
  application values from the repository `.env`; integration tests reject
  sensitive setting names in its output.

### Fixed
