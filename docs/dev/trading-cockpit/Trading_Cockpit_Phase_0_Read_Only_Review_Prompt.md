# HaruQuantAI Trading Cockpit — Phase 0 Independent Read-Only Review Prompt

## Evidence Trustworthiness, Source-of-Truth Approval, and Phase 1 Readiness

**Prompt ID:** `HQA-TC-PHASE0-REVIEW-001`
**Version:** `1.0`
**Execution mode:** Independent repository and documentation review
**Access mode:** Repository read-only; no implementation and no repository writes
**Primary decision:** `GO`, `CONDITIONAL_GO`, or `NO_GO`
**Target next phase:** Phase 1 — `Utils`

---

## 1. Role

Act as an **Independent Principal Software Architect, Trading-Systems Safety Reviewer, Quality-Assurance Lead, and Evidence Auditor**.

You are reviewing a completed Phase 0 audit of the existing **HaruQuantAI** application before any Trading Cockpit implementation begins.

Your job is **not** to repeat the Phase 0 audit, redesign the architecture, create implementation code, or repair the audit artifacts. Your job is to determine whether the Phase 0 evidence is sufficiently accurate, complete, internally consistent, reproducible, and safety-aware to become the **approved implementation source of truth**.

Treat every Phase 0 statement as a claim requiring verification. Do not accept a conclusion merely because it appears in several audit files.

---

## 2. Mission

Independently verify whether the Phase 0 artifact set can safely govern later implementation work.

Answer these questions:

1. Does the recorded repository baseline accurately identify the codebase, dependencies, migration state, existing owner changes, source documents, test state, and safety environment that were audited?
2. Were all fourteen HaruQuantAI domains inspected with concrete repository evidence?
3. Are the traceability matrix, contract registry, gap matrix, database-ownership map, test baseline, and safety baseline complete and mutually consistent?
4. Are current-state classifications supported by code, tests, migrations, exports, workflows, and runtime wiring rather than names or documentation claims alone?
5. Are future-action classifications justified and kept separate from current implementation status?
6. Does every required contract have one intended canonical owner, with duplicate or conflicting authority clearly identified?
7. Are all durable records assigned to an authoritative state-owning domain or explicitly marked ambiguous?
8. Are test and quality results reproducible without mutating the repository or contacting unsafe external systems?
9. Does the safety baseline accurately enumerate all known paths capable of broker or account writes without executing them?
10. Can Phase 1 — `Utils` be scoped from the approved gap matrix without rediscovering current repository state or relying on unresolved assumptions?

The review must conclude with one decision:

```text
GO
CONDITIONAL_GO
NO_GO
```

---

## 3. Authoritative Inputs

Review the following inputs together.

### 3.1 Normative target specification

```text
Trading_Cockpit_Game_Specification_v1.2.md
```

Expected identity:

```text
Document ID: TCS-TRADING-COCKPIT-001
Version: 1.2
Document type: Normative specification; not a phased implementation plan
```

This document defines the required end-state behavior. It does not prove what currently exists.

### 3.2 Domain-ordered implementation plan

```text
HaruQuantAI_Trading_Cockpit_Phased_Implementation_Plan_v1.0.md
```

Expected identity:

```text
Document ID: HQA-TCS-IMP-001
Version: 1.0
Implementation model: Expand the current HaruQuantAI domains; do not create a parallel Trading Cockpit application.
```

This document defines target ownership, work-package IDs, phase order, dependencies, and delivery rules.

### 3.3 Phase 0 audit instructions

```text
Trading_Cockpit_Phase_0_Audit_Prompt_v1.0.md
```

Use this to verify whether the audit agent followed its assigned scope, evidence standard, artifact contract, safety restrictions, and exit gate.

### 3.4 Completed Phase 0 artifact set

```text
docs/dev/trading-cockpit/phase-0/
├── README.md
├── baseline-manifest.json
├── repository-baseline.md
├── current-state-domain-inventory.md
├── trading-cockpit-traceability-matrix.md
├── trading-cockpit-contract-registry.md
├── trading-cockpit-gap-matrix.md
├── trading-cockpit-gap-matrix.csv
├── trading-cockpit-database-ownership.md
├── trading-cockpit-test-baseline.md
├── trading-cockpit-safety-baseline.md
├── trading-cockpit-change-control.md
├── phase-0-findings-and-decisions.md

```

If the repository uses an approved equivalent path or ADR number, identify the actual location and verify that the deviation is documented.

### 3.5 Current HaruQuantAI repository

The current repository provides evidence of implemented reality through:

- Source code.
- Public exports.
- Tests and assertions.
- Database models and migrations.
- API routes and UI consumers.
- Runtime wiring.
- Configuration and environment guards.
- CI and quality commands.
- Existing READMEs and design records.

Repository READMEs describe intent but do not override contradictory code, tests, migrations, or runtime behavior.

---

## 4. Source Precedence

Use this precedence model:

```text
Desired end state:
Trading Cockpit Specification v1.2

Implementation order and target ownership:
Trading Cockpit Phased Implementation Plan v1.0

Phase 0 assignment and evidence contract:
Phase 0 Audit Prompt v1.0

Current implemented reality:
Repository code + tests + migrations + public exports + runtime wiring

Current documented intent:
Repository READMEs and design documents

Claims under review:
Completed Phase 0 artifacts
```

The Phase 0 artifacts are **not authoritative merely because they exist**. They become authoritative only after this review approves them.

When sources disagree:

- Do not silently reconcile them.
- Identify each conflicting source.
- Cite the exact repository path, symbol, test, migration, artifact row, or source-document section.
- Determine whether the Phase 0 artifact accurately recorded the conflict.
- Do not implement or rewrite a resolution.

---

## 5. Strict Read-Only Boundary

### 5.1 Permitted actions

You may:

- Inspect repository files and Git metadata.
- Read all Phase 0 artifacts and source documents.
- Use non-mutating search and parsing commands.
- Recompute hashes and counts.
- Verify that cited files, symbols, routes, migrations, tests, and exports exist.
- Inspect code and tests to determine whether cited evidence actually supports a claim.
- Run an existing validation command only when it is demonstrably non-mutating and isolated from live or shared external systems.
- Redirect unavoidable caches or temporary output to a temporary directory outside the repository.
- Return a review report and a proposed closeout record in your final response.

### 5.2 Prohibited actions

Do not:

- Modify, create, rename, move, delete, format, or regenerate any repository file, including Phase 0 documentation.
- Save `phase-0-closeout.md` yourself.
- Implement Trading Cockpit functionality.
- Modify source code, tests, migrations, configuration, READMEs, schemas, dependencies, lockfiles, or generated files.
- Add or install dependencies.
- Apply migrations.
- Run formatting or lint auto-fixes.
- Create or switch branches.
- Commit, amend, tag, merge, rebase, stash, reset, clean, restore, or push.
- Stage or unstage files.
- submit, cancel, replace, amend, or otherwise transmit an order.
- Authenticate against or write to a production live-money account.
- Modify `.env` files or reveal secret values.
- Change connected data, calendars, email, cloud files, databases, queues, caches, or external services.
- Convert an unsupported claim into a corrected claim inside the artifacts.
- produce implementation patches, migration scripts, or Phase 1 production code.

Commands such as the following are forbidden:

```text
git reset
git clean
git checkout
git switch
git restore
git stash
git commit
git push
git rebase
ruff check --fix
ruff format
pre-commit run   # unless every invoked hook is first proven non-mutating
```

### 5.3 Repository mutation guard

At the beginning and end of the review, capture the repository state using non-mutating Git commands.

If any review command unexpectedly changes a repository path:

1. Stop executing further validation commands.
2. Do not revert the change.
3. Record the exact unexpected mutation.
4. Issue `NO_GO` unless the mutation can be conclusively shown to have pre-existed the review and the apparent change is only a measurement error.

Use environment controls such as `PYTHONDONTWRITEBYTECODE=1` and external temporary cache paths when needed. Do not allow `__pycache__`, `.pytest_cache`, coverage files, Ruff caches, mypy caches, snapshots, generated schemas, or test databases to be written into the repository.

---

## 6. Review Principle: Validate, Do Not Re-Audit

The completed Phase 0 artifacts define the claims and row set under review.

Do not reconstruct the entire audit from a blank page. Instead:

1. Verify artifact completeness and internal consistency across **all rows**.
2. Verify the existence and referential correctness of cited evidence across **all machine-checkable references** where practical.
3. Fully reperform all high-risk and Phase 1-relevant claims.
4. Use a deterministic, stratified evidence sample for ordinary non-critical claims.
5. Search for material omissions only in high-risk areas where omission would invalidate the audit, especially broker writes, canonical state ownership, public contracts, and migration ownership.
6. Report unsupported, overstated, contradictory, stale, or unverifiable claims without silently replacing them.

The review is about the **trustworthiness of the audit**, not whether HaruQuantAI already satisfies the final Trading Cockpit specification.

A trustworthy audit may accurately conclude that a capability is absent, conflicting, or unsafe. The problem is not the gap itself; the problem is an inaccurate or incomplete account of the gap.

---

## 7. Required Review Procedure

Execute every stage below.

---

### `P0-REV-01` — Review Preflight and Input Identity

Record:

- Repository root.
- Current branch or detached-HEAD state.
- Current HEAD SHA.
- Current upstream state where available.
- Review timestamp in UTC.
- Current Git worktree status.
- Exact paths and versions of the three source documents.
- Exact Phase 0 artifact directory.
- Parsed `baseline_id` from `baseline-manifest.json`.

Verify:

- The normative specification is Version `1.2`.
- The phased plan is Version `1.0`.
- The Phase 0 audit prompt is Version `1.0`.
- All required Phase 0 artifacts are present and readable.
- `baseline-manifest.json` is valid JSON.
- `trading-cockpit-gap-matrix.csv` is valid CSV with a stable header and parseable rows.

If a required source document or a core Phase 0 artifact is missing, continue only far enough to document the impact and issue `NO_GO`.

---

### `P0-REV-02` — Artifact Integrity and Completeness

Verify the complete artifact set against the Phase 0 audit prompt.

For each artifact, record:

- Present or missing.
- Parseable or malformed.
- Baseline ID where applicable.
- Version or timestamp where applicable.
- Required sections present or absent.
- Internal links and referenced files valid or broken.
- Secret or sensitive-value exposure detected or not detected.

Verify that `README.md` provides:

- Phase purpose.
- Baseline ID.
- Source documents.
- Artifact index.
- Audit scope.
- Known limitations.
- Exit-gate status.

Verify that no artifact claims Phase 0 implementation work occurred.

Verify that the artifact set contains no uncontrolled raw secret values, credentials, tokens, private keys, production account credentials, or unredacted credential-bearing URLs.

---

### `P0-REV-03` — Protected Baseline and Repository Integrity

Independently verify the baseline claims in:

```text
baseline-manifest.json
repository-baseline.md
trading-cockpit-change-control.md
```

Recompute or re-observe, where safely possible:

- Repository root.
- Remote identity with credentials redacted.
- Branch and HEAD SHA.
- Upstream relation.
- Lockfile existence and SHA-256.
- Relevant configuration hashes.
- Source-document hashes.
- Migration head or heads without applying migrations.
- Python and dependency-manager versions.
- Current application version where defined.

Compare:

```text
Initial Phase 0 baseline
vs.
Recorded Phase 0 final state
vs.
Current review-time state
```

Classify review-time drift as:

```text
NO_DRIFT
EXPLAINED_POST_AUDIT_DRIFT
UNEXPLAINED_DRIFT
UNVERIFIABLE_DRIFT
```

Verify that:

- Every pre-existing staged, tracked-modified, deleted, renamed, untracked, or ignored path was recorded.
- The audit did not claim a clean tree when it was dirty.
- No pre-existing owner path was overwritten, reverted, staged, or silently incorporated into Phase 0 edits.
- Only permitted Phase 0 artifacts were introduced by the audit.
- No production code, tests, migrations, configuration, dependency metadata, or lockfile changed during Phase 0.

If the evidence supplied by the baseline is insufficient to prove preservation of pre-existing owner changes, record this as a material review finding. Do not assume preservation.

---

### `P0-REV-04` — Full Structural and Referential Consistency

Perform structural checks across the entire artifact set.

Verify:

1. All fourteen domains appear exactly once in the required order:

```text
Utils
Brokers
Data
Indicators
Strategy
Risk
Trading
Simulator
Analytics
Optimization
Research
Portfolio
Agentic
UI-API
```

2. Every planned work-package ID from the phased implementation plan appears exactly once in the canonical gap-matrix row set.
3. The Markdown and CSV gap matrices contain the same work-package IDs and the same canonical values for status, future action, owner, dependencies, and blockers.
4. Every required cross-domain contract appears in the contract registry.
5. Every requirement row references valid owner domains and known work-package IDs.
6. Every contract row references valid work-package IDs or explicitly states why no work package applies.
7. Every database object or durable record has an owner or an explicit ownership ambiguity.
8. Every `REUSE`, `EXTEND`, `CREATE`, `REFACTOR`, `DEFERRED_INTEGRATION`, and `NOT_APPLICABLE` value uses the approved vocabulary.
9. Every current status uses only:

```text
FULL
PARTIAL
ABSENT
CONFLICTING
UNKNOWN
NOT_APPLICABLE
```

10. Current status and future action are never collapsed into one field.
11. Every `UNKNOWN` row identifies missing evidence.
12. Every `CONFLICTING` or `REFACTOR` row identifies the conflict or duplicate authority.
13. Every `DEFERRED_INTEGRATION` row names the later authoritative provider.
14. Every `NOT_APPLICABLE` row contains an explicit rationale.
15. Counts in `phase-0-findings-and-decisions.md` reconcile to the canonical row set.
16. Requirement, contract, persistence, test, UI/API, telemetry, safety, and acceptance references are not dangling.
17. No duplicate work-package row silently assigns two canonical owners.
18. No source requirement is weakened when summarized.

Report exact duplicate IDs, missing IDs, invalid enumerations, mismatched rows, dangling references, and count discrepancies.

---

### `P0-REV-05` — Evidence Verification Policy

Use two verification levels.

#### A. Full verification

Verify the following at `100%` coverage:

- Baseline and repository-protection claims.
- Every critical or blocking finding.
- Every current `CONFLICTING` or `UNKNOWN` row.
- Every future `REFACTOR` or `DEFERRED_INTEGRATION` row.
- Every low-confidence row.
- Every safety claim and every listed broker/account write path.
- Every claimed canonical owner of order, fill, position, protection, ledger, account, risk-lock, scenario, checklist, replay, score, and research-approval state.
- Every public contract and work package required by Phase 1 — `Utils`.
- Every row that would remove future work through a `REUSE` classification at least to the level of path, symbol, workflow, and test-evidence sufficiency.
- Every claim that a database or persistence concern is `NOT_APPLICABLE`.
- Every claimed pre-existing quality failure that is used to excuse a failing current command.

#### B. Deterministic stratified semantic sample

For remaining ordinary claims in each domain:

```text
sample_size = max(3, ceiling(20% of eligible rows in that domain))
```

If a domain contains fewer than three eligible rows, review all of them.

Select the sample deterministically from work-package or requirement IDs after sorting them. Include early, middle, and late IDs and distribute the remaining selections evenly. Do not cherry-pick convenient rows.

The sample should cover, where present:

- `FULL`, `PARTIAL`, and `ABSENT` current states.
- `EXTEND` and `CREATE` future actions.
- Code, tests, persistence, workflows, and UI/API evidence.
- High-, medium-, and low-complexity capabilities.

Record the exact sample-selection method and all sampled IDs.

#### Evidence sufficiency rule

For each verified claim, check this chain:

```text
Claim
  -> exact path and symbol
  -> implemented semantics
  -> public or intended authority
  -> tests and assertions
  -> actual workflow or consumer
  -> failure behavior
  -> persistence or telemetry where required
```

A folder, filename, class name, or README statement alone is not sufficient.

---

### `P0-REV-06` — Fourteen-Domain Inventory Quality

Review `current-state-domain-inventory.md` against repository evidence.

For every domain, verify that the artifact distinguishes:

- Stated responsibility from actual responsibility.
- Public export from internal implementation.
- Active workflow from unused helper.
- Durable authoritative state from a read model or cache.
- Existing implementation from planned implementation.
- Code evidence from README intent.
- Unit tests from real integration or usage evidence.
- Simulation/paper behavior from live-write behavior.

Check that each domain inventory covers or explicitly marks absent/not applicable:

- Exact filesystem and package paths.
- Feature/module boundaries.
- Public exports.
- Models, protocols, DTOs, enums, events, and exceptions.
- State machines.
- Persistence and migrations.
- Tests and coverage.
- Usage examples and workflows.
- Upstream dependencies and downstream consumers.
- UI/API connections.
- Telemetry and observability.
- Safety and environment guards.
- Duplicated, dead, orphaned, conflicting, or incorrectly owned behavior.
- Documentation-to-code mismatches.

Assign an independent evidence confidence to each domain:

```text
HIGH
MEDIUM
LOW
UNTRUSTWORTHY
```

Do not reclassify the implementation in the artifact. Report discrepancies for correction.

---

### `P0-REV-07` — Contract Registry and Canonical Ownership

Review `trading-cockpit-contract-registry.md`.

Verify for every required contract:

- Required canonical name.
- Required owner domain.
- Current candidate name, if any.
- Exact path and symbol.
- Contract kind.
- Current fields and semantics.
- Producer and consumers.
- Public export path.
- Versioning and serialization behavior.
- Persistence relationship.
- Tests.
- Duplicate or collision status.
- Current status.
- Future action.
- Work-package mapping.

Verify the provider-owned model rule:

```text
The domain that owns a concept owns its canonical model.
An earlier consumer may define a narrow port but may not implement the later provider's business logic.
```

Pay special attention to:

| Concern                                                                             | Expected canonical owner |
| ----------------------------------------------------------------------------------- | ------------------------ |
| Generic identity, versioning, validation, event metadata, generic state transitions | Utils                    |
| Instrument/venue capabilities and broker snapshots                                  | Brokers                  |
| Point-in-time market observations and dataset integrity                             | Data                     |
| Market and cockpit analytical snapshots                                             | Indicators               |
| Strategy profile, setup evaluation, and trade plan                                  | Strategy                 |
| Policy, risk decision, emergency directive, and lock state                          | Risk                     |
| Order intent, execution state, fill events, protection, and reconciliation          | Trading                  |
| Simulation clock, replay, scenario, checklist, and alert state                      | Simulator                |
| Journal, score, debrief, and qualifications                                         | Analytics                |
| Study and calibration contracts                                                     | Optimization             |
| Research evidence and expectancy approval                                           | Research                 |
| Ledger, valuation, account, margin, exposure, and portfolio state                   | Portfolio                |
| Advisory recommendations and coaching                                               | Agentic                  |
| External API DTOs and cockpit read models                                           | UI-API                   |

The actual Phase 0 evidence may reveal current ownership elsewhere. The registry must distinguish **current owner** from **required canonical owner** and record the migration concern rather than pretending the move has already occurred.

Verify that Phase 1 `Utils` does not absorb:

- Broker-specific instrument rules.
- Market-data semantics.
- Indicator calculations.
- Strategy rules.
- Risk policies.
- Order lifecycle business rules.
- Portfolio accounting.
- Simulator scenario rules.
- Agentic decisions.
- UI-specific contracts.

---

### `P0-REV-08` — Gap-Matrix Classification Reliability

Review both gap-matrix representations.

For every `REUSE` row, verify that evidence supports:

```text
Contract
+ behavior
+ required edge cases
+ workflow wiring
+ authoritative ownership
+ tests
```

If any element is missing, the `REUSE` classification is unsupported.

For every `EXTEND` row, verify that:

- A suitable authoritative implementation actually exists.
- The missing behavior is bounded and can be added without creating a competing authority.

For every `CREATE` row, verify that:

- No suitable current authoritative implementation was overlooked.
- Similar names were investigated rather than assumed unrelated.

For every `REFACTOR` row, verify that:

- A real conflict, duplication, incorrect ownership, or incompatible public contract exists.
- Affected consumers and compatibility risks are identified.

For every `DEFERRED_INTEGRATION` row, verify that:

- The consumer phase precedes the authoritative provider phase.
- The later provider is named.
- The interim port/fake does not silently implement provider business logic.

For every `NOT_APPLICABLE` row, verify that the rationale is legitimate rather than a way to omit an unresolved concern.

Verify that confidence levels reflect evidence quality. A low-evidence conclusion must not be marked `HIGH` confidence.

---

### `P0-REV-09` — Database and Persistent-State Ownership

Review `trading-cockpit-database-ownership.md` against models, repositories, migrations, event stores, files, caches, queues, and configuration.

Verify:

- Database engines and migration tooling.
- Current migration head or heads.
- Every current table, collection, stream, or durable file relevant to the fourteen domains.
- Current model and repository symbols.
- Primary and business keys.
- Unique constraints and idempotency keys.
- Transaction boundaries.
- Mutable versus append-only behavior.
- Outbox/inbox or event-publication behavior.
- Retention and recovery usage.
- Test-store isolation.
- Current owner and required owner.
- Shared or ambiguous ownership.

Fully verify ownership claims for:

- Order intents.
- Broker acknowledgements and events.
- Fills.
- Positions.
- Protective orders.
- Reconciliation state.
- Ledger entries.
- Account and portfolio snapshots.
- Margin and valuation state.
- Risk lockouts.
- Idempotency records.
- Simulation clocks.
- Replay identity.
- Scenario sessions.
- Checklist state.
- Alerts.
- Scores and qualifications.
- Research approvals.

Flag as material when:

- Two domains claim authoritative write ownership.
- A read model is mistaken for the financial source of truth.
- Trading is treated as a second portfolio ledger.
- Portfolio is treated as a second broker order store.
- Simulator state can overwrite broker or portfolio authority.
- A durable state has no owner or recovery contract.

Do not apply or generate migrations.

---

### `P0-REV-10` — Test and Quality Baseline Reproducibility

Review `trading-cockpit-test-baseline.md` against repository configuration, CI, task runners, and command history available to you.

Verify that each recorded command:

- Is the repository-authoritative command or is explicitly identified as supplemental.
- Used the correct working directory.
- Used a safe environment.
- Did not contain secrets.
- Recorded exit code, counts, coverage, and failure summaries accurately.
- Distinguished pre-existing failures from audit-caused failures.
- Recorded skipped unsafe commands with a valid reason.
- Verified file mutation after execution.

Re-run the exact command only when all of the following are true:

```text
Existing dependencies are already available
AND no installation or lockfile mutation is required
AND all caches/output can be redirected outside the repository
AND the command cannot contact or write to production/shared external systems
AND the command cannot apply migrations or broker actions
```

Where a command is safely rerun, compare:

- Exit code.
- Test counts.
- Failure identities.
- Coverage summary.
- Type/lint output category.

A changed result is not automatically an audit defect; determine whether repository drift, nondeterminism, environment variation, or inaccurate baseline reporting explains it.

Do not “fix” any failure.

---

### `P0-REV-11` — Safety Baseline Critical Assurance

Review `trading-cockpit-safety-baseline.md` with heightened scrutiny.

The review must not submit a broker command or contact a production trading endpoint.

Verify every listed write-capable:

- Broker adapter.
- Route or router method.
- Order command.
- Cancel/replace command.
- UI/API endpoint.
- CLI or usage script.
- Agentic tool.
- Background workflow.
- Test or example capable of real writes.

Verify:

- Simulation, historical replay, paper, demo, sandbox/testnet, and live selectors.
- Default environment behavior.
- Endpoint selection.
- Account checks.
- permission and policy gates.
- Kill switches and lockouts.
- Whether a live route is reachable by default.
- Whether a Trading Cockpit mode can be structurally limited to approved non-production routes.

Perform an independent bounded negative search for plausible unlisted write paths using repository terminology such as order submission, buy/sell, execute, place, send, amend, modify, cancel, close, flatten, and broker write. This search is a critical omission check, not a replacement audit.

Assess two separate questions:

```text
A. Is the Phase 0 safety classification accurate?
B. What is the current system safety classification?
```

Use the current-system values:

```text
PROVEN
PARTIAL
UNPROVEN
VIOLATED
```

A current system may be unsafe yet still have a trustworthy Phase 0 audit if the audit accurately identifies the unsafe route, marks it critical, and does not claim isolation is proven.

An unlisted reachable production write path, an overstated `PROVEN` classification, or a concealed default-live behavior is a `CRITICAL` review finding.

---

### `P0-REV-12` — Traceability Completeness

Review `trading-cockpit-traceability-matrix.md` against the complete Version 1.2 specification.

Verify that it includes:

- Instrument and cockpit-panel requirements.
- All normal checklist steps.
- All emergency checklist steps.
- All gameplay validation rules.
- Market and instrument baseline rules.
- Order, position, protective-order, and ledger state-machine rules.
- Clock, replay, deterministic-seed, and no-lookahead requirements.
- Accounting, valuation, units, currency, and precision rules.
- Scenario-definition and abnormal-operation rules.
- Persistence and crash-recovery rules.
- QA invariants and compound-failure tests.
- Latency, queue, fill, slippage, and cancel/fill-race rules.
- Human-factors and alarm-management rules.
- Training and progression rules.
- Stress-loss and gap-risk rules.
- Approved expectancy governance.
- Every final specification acceptance criterion.

Verify that each atomic requirement has:

- Stable requirement ID.
- Source section.
- Faithful normative statement.
- Primary owner.
- Consumers.
- Current evidence or explicit lack of evidence.
- Current status.
- Planned work-package mapping.
- Contract mapping.
- Persistence impact.
- Required test evidence.
- UI/API surface.
- Safety relevance.
- Acceptance target.
- Conflict or unknown where applicable.

Do not reward row volume. Duplicate or mechanically fragmented rows do not compensate for missing semantics.

---

### `P0-REV-13` — Change-Control and ADR Review

Review:

```text
trading-cockpit-change-control.md
ADR-0001-extend-existing-domains-for-trading-cockpit.md
```

Verify that the ADR records:

```text
Decision:
Implement the Trading Cockpit by expanding the fourteen existing HaruQuantAI domains.

Rejected alternative:
Create a separate top-level Trading Cockpit service tree that duplicates current domain responsibilities.
```

Verify that change control establishes at least:

1. Existing domains are extended rather than duplicated.
2. Canonical models remain with state-owning domains.
3. Earlier consumers may use narrow ports for later providers.
4. Unknown state fails visibly; there are no silent fallbacks.
5. Public API changes require compatibility analysis.
6. Breaking changes require approved migration or deprecation.
7. Existing tests and workflows remain valid or receive approved migration.
8. Database ownership is established before schema changes.
9. Every work package rechecks its Phase 0 classification before implementation.
10. Trading Cockpit modes do not authorize production live-money routing.
11. Deterministic accounting, risk, order, replay, and scoring authority is not delegated to an LLM.
12. Pre-existing owner changes remain protected.
13. Every change maps to requirements, workflows, contracts, tests, and acceptance evidence.
14. New public contracts are intentionally exported and versioned.
15. Duplicate authoritative implementations are prohibited.

Flag contradictions between the ADR, change-control document, gap matrix, and contract registry.

---

### `P0-REV-14` — Phase 1 `Utils` Readiness Review

Review all Phase 1 work packages in full:

```text
TC-IMP-UTIL-01  Identity and version references
TC-IMP-UTIL-02  Decimal unit primitives
TC-IMP-UTIL-03  Time primitives
TC-IMP-UTIL-04  State-machine primitives
TC-IMP-UTIL-05  Validation result model
TC-IMP-UTIL-06  Event envelope and sequencing
TC-IMP-UTIL-07  Idempotency primitives
TC-IMP-UTIL-08  Profile loading and schema validation
TC-IMP-UTIL-09  Error and health taxonomy
TC-IMP-UTIL-10  Structured audit and telemetry
TC-IMP-UTIL-11  Deterministic random streams
TC-IMP-UTIL-12  Persistence transaction helpers
```

For each work package, verify:

- Current status is evidence-backed.
- Future action is justified.
- Exact existing candidate modules and symbols are identified.
- Required public contracts are mapped.
- Current consumers and compatibility risks are identified.
- Test and usage evidence is identified.
- Persistence impact is bounded.
- No financial business logic is assigned to `Utils`.
- No unresolved canonical-owner conflict would force Phase 1 to invent a contract.
- `REUSE` claims are fully supported.
- `EXTEND`, `CREATE`, or `REFACTOR` scope is sufficiently precise for a later planning prompt.

Assign:

```text
Phase_1_Utils_Readiness = READY
                           | READY_WITH_CONDITIONS
                           | NOT_READY
```

List:

- Approved Phase 1 Utils work-package IDs and their reviewed action classifications.
- Blocked work-package IDs.
- Conditions that must be resolved before implementation.
- Explicit Phase 1 exclusions.

Do not create the Phase 1 planning package and do not implement any Utils feature.

---

## 8. Finding Severity

Use these severities.

### `CRITICAL`

A defect that invalidates trust in the audit or creates immediate safety/source-of-truth risk, including:

- Missing or mismatched baseline identity that prevents knowing what was audited.
- Evidence that Phase 0 modified or overwrote pre-existing owner code or repository state.
- Undisclosed production-live write path.
- Safety classified as `PROVEN` when evidence does not support it.
- Fabricated, nonexistent, or materially misrepresented repository evidence.
- Missing normative source document.
- Material secret exposure in audit artifacts.
- Duplicate authoritative ownership of financial state without being recorded.
- A core Phase 1 contract assigned to two authoritative domains without a recorded blocker.

### `MAJOR`

A defect that materially reduces completeness or could cause incorrect implementation, including:

- Missing work-package IDs.
- Markdown/CSV matrix divergence.
- Unsupported `REUSE` classification.
- Significant untraced requirements or acceptance criteria.
- Incorrect contract owner.
- Missing database owner for durable state.
- Test baseline claimed as passing but not supported by evidence.
- Important current status or future action based only on names or README claims.
- Phase 1 Utils scope cannot be derived without rediscovery.

### `MINOR`

A bounded documentation defect that does not change classification or architecture, including:

- Non-critical metadata omission.
- Broken internal link with otherwise clear evidence.
- Count presentation issue where canonical rows remain intact.
- Minor inconsistent wording that does not alter semantics.

### `OBSERVATION`

A non-blocking improvement or risk note that does not show the Phase 0 evidence is wrong.

Every finding must include:

```text
finding_id
severity
artifact_or_claim
exact_evidence
expected_state
observed_state
impact
required_correction
blocking_status
phase_1_impact
```

Use stable IDs:

```text
P0-REV-FIND-001
P0-REV-FIND-002
...
```

---

## 9. Decision Rules

### 9.1 `GO`

Issue `GO` only when all are true:

- No unresolved `CRITICAL` finding.
- No unresolved blocking `MAJOR` finding.
- Baseline identity and repository-protection evidence are trustworthy.
- Required artifacts are present and parseable.
- Cross-artifact structural checks pass.
- All fourteen domains are covered.
- All planned work packages are represented exactly once.
- Contract ownership is sufficiently explicit for implementation.
- Database and durable-state ambiguities are either resolved or correctly recorded as future blockers.
- Safety classification is accurately evidenced, including any current violation.
- No material unlisted broker/account write path is discovered.
- Phase 1 `Utils` is `READY`.
- The Phase 0 artifacts can serve as the implementation source of truth without rediscovery.

### 9.2 `CONDITIONAL_GO`

Issue `CONDITIONAL_GO` only when:

- No unresolved `CRITICAL` finding exists.
- Remaining `MAJOR` findings are bounded, explicitly listed, and do not compromise the approved Phase 1 `Utils` subset.
- Phase 1 `Utils` is `READY_WITH_CONDITIONS`.
- The exact work-package IDs allowed to proceed are listed.
- The exact conditions, owners, and prohibited work are listed.
- The audit is approved only for the explicitly stated subset; do not imply full Phase 0 trust.

Examples of possible bounded conditions:

- A later-domain non-critical evidence gap that does not affect Utils contracts.
- A documentation count mismatch with a clear canonical row set.
- A test command that cannot be reperformed in the review environment but has adequate immutable evidence and no contradiction.

### 9.3 `NO_GO`

Issue `NO_GO` when any of the following applies:

- Any unresolved `CRITICAL` finding exists.
- Baseline identity is missing, contradictory, or unverifiable.
- Required source documents or core artifacts are missing.
- Unexpected repository mutation occurs during review.
- Gap matrices materially disagree.
- Work packages or contracts are substantially missing.
- Evidence claims are fabricated or systematically overstated.
- An undisclosed production-write route is found.
- Phase 1 foundational contracts remain `UNKNOWN` or conflicting without an explicit blocking decision.
- Phase 1 `Utils` is `NOT_READY`.
- The artifacts would require material rediscovery before implementation.

`NO_GO` does not authorize you to repair the artifacts. Return an exact correction list for a separate write-authorized agent.

---

## 10. Required Final Response

Return one self-contained Markdown report. Do not create repository files.

Use this exact structure.

````markdown
# Phase 0 Independent Read-Only Review Result

## 1. Decision
- Review decision: GO | CONDITIONAL_GO | NO_GO
- Source-of-truth status: APPROVED | APPROVED_FOR_BOUNDED_SCOPE | NOT_APPROVED
- Phase 1 Utils readiness: READY | READY_WITH_CONDITIONS | NOT_READY
- One-paragraph rationale:

## 2. Review Identity
- Review timestamp UTC:
- Repository root:
- Current branch:
- Current HEAD SHA:
- Baseline ID:
- Audited baseline SHA:
- Review-time drift: NO_DRIFT | EXPLAINED_POST_AUDIT_DRIFT | UNEXPLAINED_DRIFT | UNVERIFIABLE_DRIFT
- Source document versions:

## 3. Read-Only Protection
- Initial repository status captured: YES/NO
- Final repository status captured: YES/NO
- Repository files modified by reviewer: YES/NO
- Dependencies installed or changed: YES/NO
- Migrations applied: YES/NO
- Broker/account write attempted: YES/NO
- Secret values disclosed: YES/NO
- Unexpected mutation:

## 4. Artifact Coverage
| Artifact | Present | Parseable | Required Content Complete | Key Finding |
| --- | --- | --- | --- | --- |

## 5. Baseline and Repository Integrity
- Baseline identity result:
- Pre-existing owner-change preservation result:
- Lockfile/config/source hash result:
- Migration-state result:
- Final-state comparison result:
- Supporting evidence:

## 6. Structural and Cross-Artifact Consistency
- Domains present: <count>/14
- Planned work packages represented: <count>/<expected>
- Duplicate or missing work-package IDs:
- Gap matrix Markdown/CSV parity:
- Required contracts represented: <count>/<expected>
- Traceability coverage:
- Database ownership coverage:
- Count reconciliation:

## 7. Evidence Verification
### Full-verification population
- IDs reviewed:
- Result:

### Deterministic sample
- Selection method:
- IDs reviewed by domain:
- Result:

### Unsupported or overstated claims
- Findings:

## 8. Domain Evidence Confidence
| Domain | Confidence | Verified Claims | Contradictions | Review Conclusion |
| --- | --- | ---: | ---: | --- |

## 9. Contract and Ownership Review
- Canonical ownership result:
- Duplicate authority findings:
- Provider/consumer boundary findings:
- Public-contract/versioning findings:
- Utils boundary findings:

## 10. Database and Persistence Review
- Authoritative-writer result:
- Ambiguous or duplicate ownership:
- Ledger/order/position separation:
- Recovery-state coverage:
- Migration evidence:

## 11. Test and Quality Baseline Review
| Command/Validation | Reperformed | Result Compared with Audit | Mutation-Safe | Finding |
| --- | --- | --- | --- | --- |

- Pre-existing failures accurately recorded:
- Reproducibility conclusion:

## 12. Safety Assurance Review
- Phase 0 safety classification accuracy: VERIFIED | PARTIAL | NOT_VERIFIED
- Current system safety classification: PROVEN | PARTIAL | UNPROVEN | VIOLATED
- Listed write paths verified: <count>/<count>
- Unlisted write paths discovered:
- Default-live or bypass risk:
- Trading Cockpit isolation conclusion:

## 13. Traceability Review
- Normal checklist coverage:
- Emergency checklist coverage:
- State-machine coverage:
- Accounting/replay/recovery coverage:
- Human-factors/training/stress/expectancy coverage:
- Final acceptance criteria coverage:
- Missing or weakened requirements:

## 14. Phase 1 Utils Authorization
| Work Package | Reviewed Current Status | Reviewed Future Action | Evidence Sufficient | Authorized | Condition/Blocker |
| --- | --- | --- | --- | --- | --- |
| TC-IMP-UTIL-01 | | | | | |
| TC-IMP-UTIL-02 | | | | | |
| TC-IMP-UTIL-03 | | | | | |
| TC-IMP-UTIL-04 | | | | | |
| TC-IMP-UTIL-05 | | | | | |
| TC-IMP-UTIL-06 | | | | | |
| TC-IMP-UTIL-07 | | | | | |
| TC-IMP-UTIL-08 | | | | | |
| TC-IMP-UTIL-09 | | | | | |
| TC-IMP-UTIL-10 | | | | | |
| TC-IMP-UTIL-11 | | | | | |
| TC-IMP-UTIL-12 | | | | | |

- Authorized Phase 1 IDs:
- Blocked Phase 1 IDs:
- Explicit Phase 1 exclusions:

## 15. Findings Register
| Finding ID | Severity | Artifact or Claim | Exact Evidence | Impact | Required Correction | Blocking | Phase 1 Impact |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 16. Conditions and Required Corrections
### Blocking before any implementation
1.

### Blocking only for specific Phase 1 work packages
1.

### Non-blocking corrections
1.

## 17. Proposed Phase 0 Closeout Record

Provide a complete Markdown block ready for a separate write-authorized agent or repository owner to save as:

`docs/trading-cockpit/phase-0/phase-0-closeout.md`

The proposed record must include:
- Review decision.
- Approved baseline identity.
- Source-of-truth scope.
- Approved architectural decisions.
- Blocking findings.
- Accepted non-blocking findings.
- Authorized Phase 1 Utils work-package IDs.
- Explicit Phase 1 exclusions.
- Conditions.
- Reviewer read-only confirmation.

Do not save the file yourself.

## 18. Machine-Readable Summary

```json
{
  "review_decision": "GO|CONDITIONAL_GO|NO_GO",
  "source_of_truth_status": "APPROVED|APPROVED_FOR_BOUNDED_SCOPE|NOT_APPROVED",
  "phase_1_utils_readiness": "READY|READY_WITH_CONDITIONS|NOT_READY",
  "baseline_id": "",
  "audited_head_sha": "",
  "reviewed_head_sha": "",
  "review_time_drift": "NO_DRIFT|EXPLAINED_POST_AUDIT_DRIFT|UNEXPLAINED_DRIFT|UNVERIFIABLE_DRIFT",
  "critical_findings": 0,
  "major_findings": 0,
  "minor_findings": 0,
  "authorized_phase_1_work_packages": [],
  "blocked_phase_1_work_packages": [],
  "repository_modified_by_reviewer": false,
  "broker_or_account_write_attempted": false
}
```

## 19. Explicit Scope Confirmation

State all of the following explicitly:

- No repository file was created or modified by this reviewer.
- No Trading Cockpit feature was implemented.
- No Phase 0 artifact was silently corrected.
- No dependency or lockfile was changed.
- No migration was applied.
- No broker or account write was attempted.
- The decision is based on evidence, not on the original audit agent's confidence statement.
````

---

## 11. Review Quality Standard

The review is complete only when the repository owner can tell, without reading hidden reasoning:

- exactly what was independently verified;
- which evidence was fully re-performed;
- which ordinary evidence was sampled and how;
- whether the recorded baseline matches the repository actually audited;
- whether owner changes were protected;
- whether the matrices agree;
- whether classifications are evidence-backed;
- whether contract and database authority are unambiguous or visibly blocked;
- whether the test baseline is reproducible;
- whether the safety baseline omitted any material write path;
- whether Phase 1 Utils may proceed and under which exact limits; and
- what a write-authorized agent must correct when the decision is not `GO`.

Accuracy is more important than optimism. A visible `UNKNOWN`, `CONFLICTING`, `PARTIAL`, or `VIOLATED` current state is acceptable when accurately supported. An unsupported claim of completeness is not.

End after the independent review report. Do not begin implementation planning or coding.
