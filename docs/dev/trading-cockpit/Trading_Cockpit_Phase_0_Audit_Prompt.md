# HaruQuantAI Trading Cockpit — Phase 0 Coding-Agent Prompt

## Current-State Inventory, Contract Registry, Gap Matrix, and Protected Implementation Baseline

**Prompt ID:** `HQA-TC-PHASE0-AUDIT-001`
**Version:** `1.0`
**Execution mode:** Repository audit and planning-artifact creation only
**Implementation status:** No Trading Cockpit feature implementation is authorized in this phase

---

## 1. Role

Act as a **Principal Software Architect, Senior Trading-Systems Engineer, Repository Auditor, and Change-Control Reviewer**.

You are auditing the existing **HaruQuantAI** application before implementation of the Trading Cockpit Simulator. Your responsibility is to establish a trustworthy, evidence-backed Phase 0 baseline from which all later domain phases can proceed without duplicating existing features, breaking owner changes, or inventing repository state.

You must inspect the repository directly, run only safe baseline validations, and create the required Phase 0 documentation artifacts. Do not implement Phase 1 or any Trading Cockpit runtime behavior.

---

## 2. Authoritative Context

The Trading Cockpit must be implemented by expanding the current HaruQuantAI domains in this exact order:

1. `Utils`
2. `Brokers`
3. `Data`
4. `Indicators`
5. `Strategy`
6. `Risk`
7. `Trading`
8. `Simulator`
9. `Analytics`
10. `Optimization`
11. `Research`
12. `Portfolio`
13. `Agentic`
14. `UI-API`

A later cross-domain integration phase follows these domain phases, but Phase 0 must inventory and classify the complete target scope now.

### 2.1 Required source documents

Use these documents as the intended target baseline:

1. `Trading_Cockpit_Game_Specification_v1.2.md`

   - This is the **normative end-state specification**.
   - It defines the required cockpit behavior, checklists, emergency behavior, financial rules, state machines, contracts, simulation integrity, persistence, QA, training, stress testing, expectancy governance, and acceptance criteria.
2. `Trading_Cockpit_Phased_Implementation_Plan_v1.0.md`

   - This is the **implementation-order and domain-ownership plan**.
   - It defines Phase 0 work packages, later domain work packages, contract ownership, dependencies, classifications, and integration checkpoints.
3. The current HaruQuantAI repository

   - Repository code, tests, migrations, configuration, public exports, and runtime wiring are the **source of truth for what currently exists**.
4. Existing HaruQuantAI READMEs and design documents

   - These are evidence of intended behavior, but they do not override contradictory code, tests, migrations, or runtime wiring.

### 2.2 Source precedence and conflict handling

Use the following rules:

```text
Desired end state:
Trading Cockpit Specification v1.2

Implementation order and planned ownership:
Trading Cockpit Phased Implementation Plan v1.0

Current implemented reality:
Repository code + tests + migrations + runtime wiring

Current documented intent:
Repository READMEs and design documents
```

When sources disagree:

- Do not silently choose one.
- Record the conflict precisely.
- Cite the exact file path, symbol, test, migration, or document section supporting each side.
- Classify the current state as `CONFLICTING` where appropriate.
- Recommend a future action classification, but do not resolve the conflict through implementation in Phase 0.

If either Trading Cockpit source document is unavailable, continue the repository baseline and current-state inventory, mark specification decomposition and complete traceability as `BLOCKED_BY_MISSING_SOURCE`, and do not invent the missing requirements.

---

## 3. Phase 0 Mission

Create a protected, reproducible implementation baseline and answer these questions with repository evidence:

1. What does HaruQuantAI currently contain in each of its fourteen domains?
2. Which current contracts, models, enums, protocols, events, database structures, workflows, tests, and UI/API consumers already satisfy Trading Cockpit requirements?
3. Which capabilities are partial, absent, duplicated, conflicting, incorrectly owned, or unsafe?
4. Which planned work packages should be `REUSE`, `EXTEND`, `CREATE`, `REFACTOR`, `DEFERRED_INTEGRATION`, or `NOT_APPLICABLE`?
5. Which domain owns each required contract and persistent state?
6. What is the exact pre-implementation repository, dependency, migration, test, and safety baseline?
7. Can future implementation begin without modifying or overwriting pre-existing owner changes?

Phase 0 must produce evidence and planning artifacts, not production implementation.

---

## 4. Hard Scope Boundary

### 4.1 Allowed work

You may:

- Inspect all repository files relevant to the audit.
- Run safe, read-only repository and toolchain discovery commands.
- Run existing lint, formatting-check, typing, unit, integration, and coverage commands when they are safe and non-mutating.
- Inspect database models and migration history without applying migrations to production or shared environments.
- Create new Phase 0 documentation and machine-readable audit artifacts under the approved documentation directory.
- Create one architecture decision record confirming the existing-domain extension model.
- Record findings, gaps, conflicts, unknowns, dependencies, and recommended classifications.

### 4.2 Prohibited work

Do not:

- Implement any Trading Cockpit feature.
- Modify application source code, tests, migrations, configuration, dependency files, lockfiles, schemas, or existing domain READMEs.
- Rename, move, delete, format, or refactor existing code.
- Add dependencies.
- run auto-fix commands.
- Apply database migrations.
- Submit, cancel, replace, or otherwise transmit any broker order.
- Connect to a production live-money account for validation.
- Modify `.env` files or expose secret values.
- Commit, amend, push, force-push, tag, merge, rebase, stash, reset, clean, checkout over changes, or create a replacement branch unless the repository owner explicitly asks for that action separately.
- Treat a similarly named class or function as proof that a requirement is complete.
- Infer missing behavior from naming alone.
- mark a work package complete without code, workflow, and test evidence.

### 4.3 Allowed write boundary

The only repository writes permitted in this phase are new or deliberately versioned Phase 0 audit artifacts under:

```text
docs/trading-cockpit/phase-0/
```

If the repository has an established equivalent documentation convention, use that convention and record the chosen path in the baseline report.

Before writing anything, capture the initial repository baseline. If a target Phase 0 file already exists or has owner changes, do not overwrite it. Create a versioned successor or record the collision.

---

## 5. Change Protection and Repository Safety

### 5.1 Preserve all owner changes

A dirty worktree is not permission to clean it.

At the beginning, classify every existing changed path as one of:

```text
PRE_EXISTING_STAGED_CHANGE
PRE_EXISTING_TRACKED_CHANGE
PRE_EXISTING_UNTRACKED_FILE
PRE_EXISTING_IGNORED_ARTIFACT
```

At the end, distinguish newly created Phase 0 files as:

```text
PHASE_0_CREATED_ARTIFACT
PHASE_0_UPDATED_ARTIFACT
```

No pre-existing changed path may be modified, deleted, staged, reverted, or incorporated into another edit.

### 5.2 Commands that must never be used in this audit

Do not run destructive or state-rewriting commands such as:

```text
git reset
git clean
git checkout -- <path>
git restore <path>
git stash
git rebase
git commit
git push
```

Do not run a formatter or linter with automatic fixes. Do not run a pre-commit configuration blindly if any hook can modify files; invoke non-mutating validation commands directly instead.

### 5.3 Secret handling

- Never copy secret values into reports.
- For `.env` or secret stores, record variable names, environment categories, and guard behavior only.
- Redact credentials embedded in remote URLs, logs, configuration, or error messages.
- Do not include account IDs unless already non-sensitive and required for an evidence reference.

---

## 6. Required Work Packages

Execute all Phase 0 work packages below.

---

### `TC-IMP-BASE-01` — Protected Repository Baseline

Capture the baseline **before any Phase 0 file is created**.

Record at minimum:

- Repository root.
- Repository remote name and sanitized URL.
- Current branch or detached-HEAD state.
- Current commit SHA.
- Upstream branch and ahead/behind state where available.
- Initial `git status` in a machine-readable or porcelain form.
- Staged, tracked-modified, deleted, renamed, and untracked paths.
- Submodule state, if applicable.
- Git LFS state, if applicable.
- Operating system, architecture, and shell.
- Python executable and version.
- Dependency manager and version.
- Package metadata files.
- Lockfile path, status, and SHA-256 hash.
- Relevant configuration files and hashes.
- Database engine(s), migration tool(s), and migration head(s), where safely discoverable.
- Current application version, if defined.
- Exact audit timestamp in UTC.
- Source-document paths, versions, and SHA-256 hashes.

Create a stable baseline identifier using a form such as:

```text
HQA-TC-P0-<UTC_TIMESTAMP>-<SHORT_SHA>
```

Do not assume that the working tree is clean. Record its actual state.

#### Machine-readable baseline manifest

Create:

```text
baseline-manifest.json
```

It must include at least:

```text
baseline_id
captured_at_utc
repository_root
branch
head_sha
upstream
worktree_state
pre_existing_changes
toolchain
lockfiles
migration_state
source_documents
validation_commands
safety_environment_summary
```

Do not include secrets.

---

### `TC-IMP-BASE-02` — Fourteen-Domain Current-State Inventory

Inventory every domain in the exact implementation order:

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

Discover the actual repository paths. Do not assume `UI-API` is one physical folder; identify the real API and web/UI locations and their relationship.

For each domain, inspect and record:

1. Exact package and filesystem paths.
2. Domain README and feature registry, if present.
3. Stated responsibilities.
4. Actual implementation responsibilities.
5. Feature/module folders.
6. Public exports and supported import paths.
7. Public classes, functions, protocols, DTOs, enums, exceptions, and events.
8. Internal state machines and lifecycle states.
9. Database models, repositories, migrations, and persistence ownership.
10. Unit, boundary, property, integration, contract, usage, and end-to-end tests.
11. Current test coverage where measurable.
12. Usage examples, scripts, demonstrations, or executable workflows.
13. Upstream dependencies and downstream consumers.
14. API routes, WebSocket/event consumers, UI consumers, and external connectors.
15. Telemetry, logs, audit events, and failure observability.
16. Safety and environment guards.
17. Duplicate, dead, orphaned, conflicting, or incorrectly owned behavior.
18. README-to-code and code-to-test inconsistencies.
19. Current maturity and confidence level.

Use exact evidence references such as:

```text
app/services/risk/<feature>/<file>.py::<ClassOrFunction>
tests/risk/<test_file>.py::<test_name>
app/api/<route_file>.py::<route_name>
migrations/<revision_file>.py::<revision>
```

A directory name or class name alone is not sufficient evidence.

#### Domain audit summary matrix

Include this summary table:

| Domain | README | Database | Unit Tests | FR Usage | Workflow | UI/API Connection | Telemetry | Persistence | Safety | Overall Evidence Status |
| ------ | ------ | -------- | ---------- | -------- | -------- | ----------------- | --------- | ----------- | ------ | ----------------------- |

Use evidence states:

```text
VERIFIED
PARTIAL
ABSENT
CONFLICTING
UNKNOWN
NOT_APPLICABLE
```

---

### `TC-IMP-BASE-03` — Specification Decomposition and Traceability

Decompose the complete Trading Cockpit Specification v1.2 into atomic, traceable requirements.

Include:

- Instrument and cockpit-panel requirements.
- All checklist steps and state logic.
- Emergency checklist requirements.
- Gameplay validation rules.
- Market and instrument baseline rules.
- Order, position, protective-order, and ledger state-machine rules.
- Clock, replay, and no-lookahead requirements.
- Accounting, valuation, precision, and currency rules.
- Scenario contracts and abnormal operations.
- Persistence and recovery requirements.
- QA invariants and compound-failure requirements.
- Latency, queue, fill, slippage, and cancel-race requirements.
- Human-factors and alarm rules.
- Training and progression requirements.
- Stress-loss and gap-risk rules.
- Approved expectancy requirements.
- All forty final specification acceptance criteria.

For requirements that already have source IDs, preserve them. For an atomic normative statement without an explicit ID, create a stable derived identifier such as:

```text
TCS-S<SECTION>-REQ-<NNN>
```

Do not rewrite or weaken the source requirement.

For every atomic requirement, record:

- Requirement ID.
- Source section and exact source wording or faithful concise statement.
- Primary owner domain.
- Supporting/consumer domains.
- Current evidence paths and symbols.
- Current implementation status.
- Planned work-package IDs.
- Required contracts.
- Persistence impact.
- Test evidence type required.
- UI/API read or command surface.
- Safety relevance.
- Acceptance evidence target.
- Open conflict or unknown.

#### Current implementation status values

Use these values for what exists now:

```text
FULL
PARTIAL
ABSENT
CONFLICTING
UNKNOWN
NOT_APPLICABLE
```

Do not use a future action classification in place of current status.

---

### `TC-IMP-BASE-04` — Complete Trading Cockpit Gap Matrix

Extract every planned work-package ID from the phased implementation plan, including all domain phases and final integration/release work.

For each planned work package, assign exactly one future action classification:

| Classification           | Meaning                                                                                     | Required future action                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `REUSE`                | Existing behavior already satisfies the required contract, edge cases, workflows, and tests | Preserve it; add only traceability or integration evidence where needed                                     |
| `EXTEND`               | Existing behavior is correct but incomplete                                                 | Add missing states, fields, rules, tests, persistence, exports, or integrations within the existing feature |
| `CREATE`               | No suitable authoritative behavior exists                                                   | Add one cohesive feature in the owning current domain                                                       |
| `REFACTOR`             | Existing behavior conflicts, is duplicated, or is owned incorrectly                         | Consolidate to one authoritative implementation and migrate callers safely                                  |
| `DEFERRED_INTEGRATION` | A consumer phase precedes a later authoritative provider                                    | Define or retain a narrow consumer port/fake, then integrate when the provider phase is reached             |
| `NOT_APPLICABLE`       | A particular database, UI, persistence, or other concern legitimately does not apply        | Record the explicit rationale                                                                               |

Keep this separate from current implementation status.

For every work package, include:

- Work-package ID.
- Phase and domain.
- Capability and responsibility.
- Specification requirement IDs.
- Current candidate modules/symbols.
- Current implementation status.
- Future action classification.
- Evidence-backed rationale.
- Confidence: `HIGH`, `MEDIUM`, or `LOW`.
- Canonical owner domain.
- Supporting domains.
- Dependencies and deferred providers.
- Contract impact.
- Database/persistence impact.
- Test gaps.
- Workflow/usage gap.
- UI/API contract gap.
- Telemetry gap.
- Security/safety gap.
- Backward-compatibility concern.
- Acceptance evidence target.
- Blocking decision, if any.

Rules:

```text
A similarly named symbol is not sufficient for REUSE.

REUSE requires behavior + edge cases + workflow wiring + tests.

If behavior exists but is not authoritative or has conflicting duplicates,
classify REFACTOR rather than REUSE.

If evidence is insufficient, use current status UNKNOWN and do not guess.
```

Produce both:

```text
trading-cockpit-gap-matrix.md
trading-cockpit-gap-matrix.csv
```

The Markdown and CSV must contain the same canonical rows.

---

### `TC-IMP-BASE-05` — Current and Required Contract Registry

Inventory the current repository contracts and compare them with the required cross-domain contracts.

At minimum, evaluate these planned contracts:

#### Utils-owned

- `ProfileRef`
- `VersionRef`
- `EventEnvelope`
- `ValidationResult`
- `ValidationIssue`
- `StateTransition`
- `HealthState`
- `IdempotencyKey`
- `ClockPort`
- `DeterministicRandomPort`

#### Brokers-owned

- `InstrumentVenueProfile`
- `BrokerHealth`
- `BrokerOrderSnapshot`
- `BrokerPositionSnapshot`
- normalized account, fill, capability, and command contracts

#### Data-owned

- `MarketEvent`
- `MarketSnapshot`
- `OrderBookSnapshot`
- `EconomicEvent`
- point-in-time metadata and dataset-integrity contracts

#### Indicators-owned

- `IndicatorSnapshot`
- `MarketRegimeSnapshot`
- `LiquiditySnapshot`
- cockpit-gauge outputs

#### Strategy-owned

- `StrategyProfile`
- `SetupEvaluation`
- `TradePlan`
- strategy operating-envelope and exit-rule contracts

#### Risk-owned

- `TradingPolicyProfile`
- `RiskDecision`
- `EmergencyDirective`
- `AccountLockState`
- stress and gate result contracts

#### Trading-owned

- `OrderIntent`
- `OrderState`
- `ExecutionEvent`
- `ExecutionPositionState`
- protective-order and reconciliation contracts

#### Simulator-owned

- `SimulationClock`
- `ReplayIdentity`
- `ScenarioDefinition`
- `InjectedEvent`
- `ChecklistState`
- `AlertEvent`
- durable scenario/session state contracts

#### Analytics-owned

- `Scorecard`
- `Debrief`
- `JournalEntry`
- `PlayerQualification`

#### Optimization-owned

- `OptimizationStudy`
- `CalibrationProfile`

#### Research-owned

- `ResearchEvidence`
- `ApprovedExpectancyProfile`
- `ScenarioEvidence`

#### Portfolio-owned

- `PortfolioState`
- `LedgerEntry`
- `ValuationPolicy`
- `FXConversionRate`
- margin, exposure, drawdown, and accounting read models

#### Agentic-owned

- `AgentRecommendation`
- `AgentToolDecision`
- `CoachingMessage`

#### UI-API-owned

- API DTOs.
- Cockpit read models.
- Command DTOs.
- Event/WebSocket payloads.
- Versioned external schemas.

For every contract, record:

- Required canonical name.
- Required authoritative owner.
- Current candidate name(s).
- Exact path and symbol.
- Contract kind: model, DTO, protocol, enum, event, state machine, command, query, or read model.
- Current fields and semantics.
- Required fields and semantics at a gap-summary level.
- Serialization format.
- Schema/versioning behavior.
- Mutability.
- Persistence relationship.
- Producer(s).
- Consumer(s).
- Public export path.
- Validation rules.
- Tests.
- Duplicate or collision status.
- Authority conflict.
- Backward-compatibility risk.
- Current implementation status.
- Future action classification.
- Planned work-package mapping.

Do not create implementation contracts in this phase. Produce the registry and collision analysis only.

---

### `TC-IMP-BASE-06` — Data-Store and Persistence Ownership Inventory

Inspect all current persistence mechanisms.

Record:

- Database engines and connection patterns.
- ORM or query layers.
- Migration tooling and migration heads.
- Tables, collections, streams, files, caches, and queues.
- Owning domain for each durable record.
- Current model and repository symbols.
- Primary keys and business keys.
- Unique constraints and idempotency keys.
- Foreign-key or reference relationships.
- Append-only or mutable behavior.
- Transaction boundaries.
- Outbox/inbox or event-publication behavior.
- Audit history.
- Retention and archival rules.
- Recovery usage.
- Test-database behavior.
- Shared tables or ambiguous ownership.
- Schema collisions with planned Trading Cockpit contracts.

Do not apply migrations or repair schemas.

Flag any durable state that lacks an authoritative owner, especially:

- Order intents.
- Broker events.
- Fills.
- Positions.
- Protective orders.
- Ledger entries.
- Account snapshots.
- Portfolio state.
- Risk lockouts.
- Simulation clocks.
- Replay identity.
- Scenario state.
- Checklist state.
- Alerts.
- Scores and qualifications.
- Research approvals.
- Idempotency records.

---

### `TC-IMP-BASE-07` — Non-Mutating Test and Quality Baseline

Discover the authoritative validation commands from repository evidence, including:

- `pyproject.toml`.
- Lockfiles.
- CI workflows.
- task runners.
- test configuration.
- coverage configuration.
- `.pre-commit-config.yaml`.
- developer documentation.

Where the repository uses `uv run --frozen`, Ruff, strict mypy, pytest, and coverage, preserve that route. Do not assume commands that the repository does not support.

Run the safe non-mutating baseline where possible:

- Dependency/lock consistency check.
- Ruff lint check without `--fix`.
- Ruff format check without rewriting.
- Mypy or the repository's type checker.
- Unit tests.
- Integration tests that are proven not to perform external writes.
- Coverage using the repository's configured source paths.
- Existing architecture/contract tests.
- Existing documentation or schema validation tests.

Before running any test that touches a broker, network, database, or external service, inspect its configuration and prove that it is isolated to mocks, local test infrastructure, paper, demo, sandbox, or testnet. Skip unsafe commands and record exactly why.

For every command, record:

- Exact command.
- Working directory.
- Relevant safe environment mode, with secret values omitted.
- Start and end timestamp.
- Exit code.
- Passed/failed/skipped counts.
- Coverage summary.
- Failure summary.
- Whether the failure was pre-existing.
- Whether the command modified any file.

Do not fix baseline failures.

After each major validation group, verify that no unexpected repository file changed.

---

### `TC-IMP-BASE-08` — Trading and Broker Safety Baseline

Prove the current environment boundaries without sending an order.

Inspect and document:

- Broker adapters and routes.
- Simulation, paper, demo, testnet, and live environment selectors.
- Default environment behavior.
- Live-write methods and call paths.
- UI/API routes that can cause writes.
- Agentic tools that can cause writes.
- permissions, policies, and risk governors.
- environment and account checks.
- production endpoint selection.
- kill switches and lockouts.
- test fixtures and usage examples that perform broker writes.
- whether a Trading Cockpit session can be structurally restricted to simulation, replay, paper, or approved sandbox/testnet routes.

Classify the current safety boundary as one of:

```text
PROVEN
PARTIAL
UNPROVEN
VIOLATED
```

A safety boundary is `PROVEN` only when code and tests demonstrate it. Configuration intent alone is not proof.

If any default or reachable path can send production live-money orders without an explicit non-bypassable guard, classify it as `VIOLATED` and make it a critical Phase 0 finding. Do not test the path by submitting an order.

---

### `TC-IMP-BASE-09` — Phase 0 Documentation Set

Create the following artifact set under the approved Phase 0 documentation directory:

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
└── ADR-0001-extend-existing-domains-for-trading-cockpit.md
```

If the repository already uses another ADR numbering convention, follow it and record the final filename.

`README.md` must provide:

- Phase 0 purpose.
- Baseline ID.
- Source documents.
- Artifact index.
- Audit scope.
- Known limitations.
- Exit-gate status.

Do not copy secrets or uncontrolled raw logs into the repository.

---

### `TC-IMP-BASE-10` — Protected Change-Control Rule

Create a change-control policy for all later phases.

It must establish these rules:

1. **Extend existing domains; do not create a parallel top-level `trading_cockpit/` service tree.**
2. **The domain that owns a concept owns its canonical model and state.**
3. **Earlier consumers may define narrow ports for later providers, but may not implement the later provider's business logic.**
4. **No silent fallbacks for unknown profile, state, timestamp, conversion, order, or broker results.**
5. **Public API changes require explicit compatibility analysis.**
6. **Breaking changes require deprecation or controlled migration unless the repository owner explicitly approves a clean break.**
7. **Existing tests and workflows must remain valid or receive an explicit, approved migration.**
8. **Database ownership and migration responsibility must be assigned before schema changes.**
9. **Every later work package must begin by rechecking its Phase 0 classification against the then-current repository state.**
10. **No production live-money route is authorized for Trading Cockpit modes.**
11. **Deterministic state, accounting, risk, execution, replay, and scoring cannot be delegated to an LLM.**
12. **No phase may overwrite pre-existing owner changes.**
13. **Every implementation change must map to a requirement, workflow, contract, test, and acceptance-evidence target.**
14. **New public contracts must be intentionally exported and versioned.**
15. **Duplicate authoritative implementations are prohibited.**

The ADR must record:

```text
Decision:
Implement the Trading Cockpit by expanding the fourteen existing HaruQuantAI domains.

Rejected alternative:
Creating a separate top-level Trading Cockpit service tree that duplicates current domain responsibilities.
```

---

## 7. Required Analysis Standards

### 7.1 Evidence standard

Every substantive finding must cite exact repository evidence.

Acceptable evidence:

- Exact file and symbol.
- Exact test and assertion.
- Exact migration and schema object.
- Exact API route or event consumer.
- Exact public export.
- Exact configuration rule.
- Exact command result.

Insufficient evidence:

- Folder name only.
- Class name only.
- README claim without code or test support.
- Assumption based on common architecture.
- “Looks implemented.”

### 7.2 No silent gap filling

If evidence is missing or ambiguous:

```text
Current status = UNKNOWN
Confidence = LOW
Reason = explicit missing evidence
```

Do not convert uncertainty into `ABSENT` or `REUSE` without investigation.

### 7.3 Separate current state from future action

Every matrix must keep these as separate fields:

```text
Current implementation status:
FULL | PARTIAL | ABSENT | CONFLICTING | UNKNOWN | NOT_APPLICABLE

Future action classification:
REUSE | EXTEND | CREATE | REFACTOR | DEFERRED_INTEGRATION | NOT_APPLICABLE
```

Examples:

```text
Current status = PARTIAL
Future action = EXTEND
```

```text
Current status = FULL but duplicated by another domain
Future action = REFACTOR
```

### 7.4 Domain ownership standard

Use the phased plan's ownership model as the target. If the repository currently places behavior elsewhere, record:

- Current owner.
- Required canonical owner.
- Current consumers.
- Migration/compatibility concern.
- Recommended future classification.

Do not relocate it in Phase 0.

### 7.5 Functional usage standard

A feature is not considered fully implemented merely because it has a model or helper.

Verify:

```text
Contract
  + implementation
  + public/export path
  + tests
  + real domain workflow or usage
  + failure behavior
  + telemetry/observability where required
```

If one or more are absent, classify accordingly.

---

## 8. Required Artifact Content

### 8.1 `repository-baseline.md`

Must contain:

- Baseline ID.
- Timestamp.
- branch/SHA/upstream.
- Sanitized remote.
- Initial worktree inventory.
- Toolchain.
- lockfile and configuration hashes.
- migration state.
- source-document hashes.
- pre-existing changes table.
- allowed Phase 0 write boundary.
- final worktree comparison.

### 8.2 `current-state-domain-inventory.md`

Must contain:

- One section per domain in exact phase order.
- Domain summary matrix.
- Feature/module inventory.
- Public export inventory.
- database/persistence inventory.
- test/usage/workflow inventory.
- dependency and consumer map.
- documentation mismatch findings.
- domain-specific current-state conclusion.

### 8.3 `trading-cockpit-traceability-matrix.md`

Minimum columns:

| Requirement ID | Source Section | Normative Requirement | Primary Owner | Consumers | Current Evidence | Current Status | Work Package | Contract | Persistence | Required Test Evidence | UI/API Surface | Safety | Acceptance Target | Conflict/Unknown |
| -------------- | -------------- | --------------------- | ------------- | --------- | ---------------- | -------------- | ------------ | -------- | ----------- | ---------------------- | -------------- | ------ | ----------------- | ---------------- |

### 8.4 `trading-cockpit-contract-registry.md`

Minimum columns:

| Required Contract | Required Owner | Current Candidate | Path/Symbol | Kind | Authority | Producer | Consumers | Versioning | Persistence | Tests | Collision | Current Status | Future Action | Work Package |
| ----------------- | -------------- | ----------------- | ----------- | ---- | --------- | -------- | --------- | ---------- | ----------- | ----- | --------- | -------------- | ------------- | ------------ |

### 8.5 `trading-cockpit-gap-matrix.md` and `.csv`

Minimum columns:

| Work Package | Phase | Domain | Capability | Specification IDs | Current Evidence | Current Status | Future Action | Confidence | Rationale | Dependencies | Contract Impact | DB/Persistence | Test Gap | Workflow Gap | UI/API Gap | Telemetry Gap | Safety Gap | Compatibility Risk | Acceptance Evidence | Blocker |
| ------------ | ----- | ------ | ---------- | ----------------- | ---------------- | -------------- | ------------- | ---------- | --------- | ------------ | --------------- | -------------- | -------- | ------------ | ---------- | ------------- | ---------- | ------------------ | ------------------- | ------- |

### 8.6 `trading-cockpit-database-ownership.md`

Minimum columns:

| Store/Object | Type | Current Model/Path | Migration | Current Owner | Required Owner | Key/Uniqueness | Mutability | Transaction Boundary | Retention | Consumers | Collision/Gap | Future Action |
| ------------ | ---- | ------------------ | --------- | ------------- | -------------- | -------------- | ---------- | -------------------- | --------- | --------- | ------------- | ------------- |

### 8.7 `trading-cockpit-test-baseline.md`

Minimum columns:

| Validation | Exact Command | Safety Mode | Exit Code | Result | Counts/Coverage | Existing Failure | File Mutation Check | Evidence |
| ---------- | ------------- | ----------- | --------- | ------ | --------------- | ---------------- | ------------------- | -------- |

### 8.8 `trading-cockpit-safety-baseline.md`

Must include:

- All write-capable adapters and methods.
- All entry points that can reach them.
- Environment-selection rules.
- default behavior.
- non-bypassable guards.
- test evidence.
- current safety classification.
- unresolved critical risks.

### 8.9 `phase-0-findings-and-decisions.md`

Must include:

- Executive current-state summary.
- Counts by current status.
- Counts by future action classification.
- Top contract collisions.
- Top ownership conflicts.
- Top persistence risks.
- Top test gaps.
- Top safety risks.
- Decisions that are already determined by source documents.
- Decisions still required from the repository owner.
- Phase 1 readiness statement.

Do not use this file to implement or redesign features. It is an audit conclusion.

---

## 9. Validation and Consistency Checks

Before declaring Phase 0 complete, verify all of the following:

### 9.1 Coverage checks

- All fourteen domains have an inventory section.
- Every planned work-package ID in the phased plan appears once in the gap matrix.
- Every required cross-domain contract appears in the contract registry.
- Every explicit checklist step and emergency step in the specification appears in traceability.
- All forty final acceptance criteria appear in traceability.
- Every current database object has an owner or an explicit ambiguous-owner finding.
- Every current broker write path appears in the safety baseline.
- Every baseline validation command is recorded, including skipped unsafe commands.

### 9.2 Matrix integrity checks

- No work package has more than one future action classification.
- No `REUSE` row lacks implementation, workflow, and test evidence.
- No `NOT_APPLICABLE` row lacks a written reason.
- Every `DEFERRED_INTEGRATION` row identifies the later authoritative provider.
- Every `REFACTOR` row identifies the conflict or duplicate authority.
- Every `UNKNOWN` row explains what evidence is missing.
- Contract owner and work-package owner are consistent or explicitly flagged.
- Markdown and CSV gap matrices contain the same row set.

### 9.3 Repository protection checks

- Re-run repository status at the end.
- Compare final state with the initial manifest.
- Confirm that no pre-existing changed file was modified.
- Confirm that no code, test, migration, configuration, dependency, or lockfile changed.
- Confirm that only permitted Phase 0 artifacts were created or deliberately versioned.
- Record any unexpected mutation as a Phase 0 failure.

### 9.4 Safety checks

- Confirm no production order was sent.
- Confirm no live account write was attempted.
- Confirm no migration was applied.
- Confirm no secret was written to an artifact.
- Confirm test commands were either isolated or explicitly skipped.

---

## 10. Phase 0 Exit Gate

Phase 0 is complete only when all conditions below are true:

1. A protected repository baseline exists with branch, SHA, dirty-state, toolchain, lockfile, migration, source-document, test, and safety evidence.
2. Every one of the fourteen domains has been inventoried from code, documentation, tests, persistence, workflows, and consumers.
3. Every planned work package has a primary owner, dependency, current status, future action classification, and acceptance-evidence target.
4. Every required contract has a current-state finding, canonical owner, collision analysis, consumer map, and planned action.
5. Every normative Trading Cockpit requirement and all forty acceptance criteria are traceable.
6. Current database and persistent-state ownership is documented.
7. The existing quality baseline has been run safely or explicitly recorded as blocked.
8. Trading Cockpit live-write isolation is classified with evidence.
9. The ADR confirms expansion of existing domains rather than a duplicate top-level service tree.
10. No Trading Cockpit implementation code was added.
11. No owner change was overwritten or reverted.
12. Final repository state contains only permitted Phase 0 artifacts in addition to the pre-existing baseline.

If any condition is incomplete, mark the Phase 0 exit gate as:

```text
NOT_READY
```

and list the exact missing evidence. Do not claim completion based on partial inspection.

---

## 11. Final Response Format

After creating the artifacts, return a concise execution report using this exact structure:

```text
# Phase 0 Execution Result

## Baseline
- Baseline ID:
- Branch:
- Commit SHA:
- Initial worktree state:
- Final worktree state:
- Audit timestamp UTC:

## Repository Protection
- Pre-existing owner changes preserved: YES/NO
- Production code changed: YES/NO
- Tests changed: YES/NO
- Migrations changed/applied: YES/NO
- Dependencies or lockfiles changed: YES/NO

## Inventory Coverage
- Domains inventoried: <count>/14
- Planned work packages classified: <count>/<total>
- Required contracts inventoried: <count>/<total>
- Normative requirements traced: <count>/<total>
- Final acceptance criteria traced: <count>/40

## Classification Summary
- FULL:
- PARTIAL:
- ABSENT:
- CONFLICTING:
- UNKNOWN:
- NOT_APPLICABLE:

- REUSE:
- EXTEND:
- CREATE:
- REFACTOR:
- DEFERRED_INTEGRATION:
- NOT_APPLICABLE:

## Quality Baseline
- Lock/dependency check:
- Ruff lint:
- Ruff format check:
- Mypy/type check:
- Tests:
- Coverage:
- Known pre-existing failures:

## Safety Baseline
- Safety classification: PROVEN/PARTIAL/UNPROVEN/VIOLATED
- Production write attempted: NO
- Critical findings:

## Highest-Priority Findings
1.
2.
3.
4.
5.

## Artifacts Created
- <exact paths>

## Exit Gate
- READY / NOT_READY
- Missing evidence or blockers:

## Explicit Scope Confirmation
No Trading Cockpit production feature was implemented during Phase 0.
```

Do not provide a Phase 1 implementation patch. Do not start Phase 1. End after reporting Phase 0 evidence and readiness.

---

## 12. Quality Standard

The final Phase 0 output must be sufficiently precise that the next coding agent can begin the `Utils` phase without needing to rediscover:

- what already exists;
- what is authoritative;
- what is duplicated or conflicting;
- which contracts must be reused or extended;
- which gaps are real;
- which owner changes must be protected;
- which tests already fail;
- which safety boundaries are proven or missing; and
- how every future change maps back to the Trading Cockpit specification.

Accuracy and evidence are more important than optimistic completion. Unknowns must remain visible until proven.
