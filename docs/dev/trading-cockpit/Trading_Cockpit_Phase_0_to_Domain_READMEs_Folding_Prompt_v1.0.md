# HaruQuantAI Trading Cockpit — Phase 0 Findings to Domain READMEs Folding Prompt

## 1. Role

Act as a **Senior Software Architect, Brownfield Requirements Engineer, and Domain Documentation Reconciliation Agent** for the existing HaruQuantAI repository.

You are performing a **documentation-first brownfield update**. HaruQuantAI already exists and already has implemented features, functional requirements, contracts, workflows, tests, persistence, and public APIs. Your task is to expand and correct the existing domain specifications before any production code is changed.

You are **not** designing a parallel greenfield `trading_cockpit/` application.

---

## 2. Mission

Use the approved Trading Cockpit Phase 0 audit and its independent review to fold every approved finding into the authoritative README of its owning HaruQuantAI domain.

The fourteen domain READMEs are the final and only domain-level sources of truth:

1. Utils
2. Brokers
3. Data
4. Indicators
5. Strategy
6. Risk
7. Trading
8. Simulator
9. Analytics
10. Optimization
11. Research
12. Portfolio
13. Agentic
14. UI-API

After this step, each domain README must stand alone. A future coding agent must be able to implement that domain's Trading Cockpit additions by reading the domain README without needing any file under `docs/dev/trading-cockpit/`.

The Phase 0 documents are temporary evidence and routing aids. They are not permanent requirement authorities.

---

## 3. Required Outcome

Modify the existing README for every affected domain so that it fully contains:

- The approved domain boundary.
- Existing capabilities that will be reused.
- Existing features and functional requirements that must be extended or refactored.
- New features and functional requirements that must be created.
- Canonical owned and consumed contracts.
- Persisted-state ownership.
- Configuration and limits.
- Workflows.
- Failure behavior and side effects.
- Required public API targets.
- Usage-example targets.
- Unit, component, structural, integration, workflow, and acceptance-test targets.
- Non-functional requirements.
- Explicit exclusions and deferred integrations.
- Open decisions that cannot be resolved from approved evidence.
- Accurate current implementation status.

Do **not** implement production code in this task.

---

## 4. Authoritative Inputs

Read the following inputs.

### 4.1 Current repository

Inspect:

- All fourteen current domain READMEs.
- Only the source files, tests, public exports, migrations, and configuration paths needed to preserve existing identifiers, symbols, ownership, and current status.

Do not repeat the full Phase 0 audit.

### 4.2 Phase 0 approved evidence

Use the approved contents of:

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
```


### 4.3 Supporting product documents

Use these only when a Phase 0 traceability row points to them or when approved evidence needs its full normative behavior:

```text
docs/dev/trading-cockpit/SPECIFICATION.md
# or the approved Trading_Cockpit_Game_Specification_v1.2.md

docs/dev/trading-cockpit/PHASED-IMPLEMENTATION-PLAN.md
# or the approved HaruQuantAI phased implementation plan
```

The implementation plan provides sequence and domain intent. It is not the final backlog and must not override the reviewed gap matrix.

### 4.4 Structural reference

Use the supplied Data domain README as the structural standard. All domain READMEs follow the same documentation philosophy:

```text
Package
└── Module folder = one Feature / cohesive capability
    └── File = one use case / focused responsibility
        └── Class / function / method / constant = one Functional Requirement behavior
```

Preserve each current domain README's exact established structure, terminology, table columns, numbering conventions, status vocabulary, and level of detail. Do not replace an existing README with a shorter generic template.

---

## 5. Source Precedence During This Task

When evidence conflicts, use this order:

1. This prompt and explicit owner instructions.
2. Approved Phase 0 closeout decision and independent review corrections.
3. Reviewed `trading-cockpit-gap-matrix.csv`.
4. Reviewed contract registry, database ownership, traceability matrix, findings, and safety baseline.
5. Current domain README and current code/test evidence for identifiers and actual current implementation.
6. Trading Cockpit specification sections linked by traceability.
7. Original phased implementation plan.

Do not silently choose between unresolved conflicting sources. Record an Open Decision in the owning README when approved evidence does not settle the conflict.

---

## 6. Non-Negotiable Brownfield Rules

### 6.1 Expand before creating

For every approved gap, first attempt to place the behavior inside the existing feature that already owns the same actor outcome or cohesive capability.

Create a new feature only when the behavior cannot fit an existing feature without violating focused feature ownership.

### 6.2 Preserve identity

Do not renumber, rename, or reuse existing active, retired, removed, withdrawn, superseded, or reserved identifiers unless the Phase 0 closeout explicitly authorizes it.

Preserve:

- `FEAT-<DOMAIN>-NN`
- `FR-<DOMAIN>-NNN`
- `NFR-<DOMAIN>-NNN`
- `WF-<DOMAIN>-...`
- `CAP-<DOMAIN>-...`
- Contract names and versions
- Schema identifiers
- Error codes
- Public symbols
- Existing usage-program numbering

Retired numbers remain retired and are never reused.

### 6.3 One canonical owner

Every capability, contract, state machine, calculation, persisted record, and policy decision must have exactly one canonical owning domain.

A consuming domain may document that it consumes a contract, but it must not redefine it.

### 6.4 No parallel Trading Cockpit architecture

Do not introduce a top-level `trading_cockpit/` package or duplicate the existing fourteen-domain architecture.

Trading Cockpit behavior must be distributed into the existing domain owners.

### 6.5 No code in this task

You may modify only the fourteen domain README files.

Do not modify:

- Production source.
- Tests or usage programs.
- Database migrations.
- Configuration files.
- Dependency files or lockfiles.
- API schemas.
- Generated artifacts.
- Phase 0 evidence.
- Project-wide architecture documents.

Do not create code stubs or empty folders.

### 6.6 No unsupported claims

Do not mark a feature or requirement `Completed` unless implementation and verification evidence already exist.

Do not invent source paths, public functions, database tables, test files, or contract fields merely to fill a README table.

Reuse current symbols and paths wherever possible. Define a new target symbol only when the approved requirement needs one and no existing symbol can own the behavior cleanly.

### 6.7 Standalone deletion readiness

Do not make any updated domain README depend normatively on a file under `docs/dev/trading-cockpit/`.

The updated README must restate the complete requirement, behavior, ownership, inputs, outputs, validation, failures, side effects, workflow role, and test expectations.

Do not write:

```text
See the Phase 0 gap matrix for details.
See the Trading Cockpit specification for behavior.
Implementation is defined in docs/dev/trading-cockpit/...
```

Temporary Phase 0 gap IDs may appear in the final response mapping, but they should not become permanent domain requirement identifiers unless the project already treats them as permanent.

---

## 7. Domain Processing Order

Process and update domains in this exact order:

```text
1. Utils
2. Brokers
3. Data
4. Indicators
5. Strategy
6. Risk
7. Trading
8. Simulator
9. Analytics
10. Optimization
11. Research
12. Portfolio
13. Agentic
14. UI-API
```

Use the canonical README paths recorded by the Phase 0 inventory. Do not assume a path from the domain name.

Before editing a domain, load:

1. That domain's current README.
2. Gap rows canonically owned by that domain.
3. Traceability rows connected to those gaps.
4. Contract-registry entries owned or consumed by that domain.
5. Database-ownership entries relevant to that domain.
6. Safety rules relevant to that domain.
7. Current code/test evidence only where needed to preserve existing identity and status.

---

## 8. Gap Classification to README Action

Treat the reviewed Phase 0 classifications as binding unless the closeout explicitly changed them.

### 8.1 `FULL` + `REUSE`

- Keep the existing feature and requirement identity.
- Do not create duplicate requirements.
- Correct or complete README wording only when the audit found a documentation omission.
- Keep `Completed` only when code, usage, and tests already prove the complete required behavior.
- Add consumer references, cockpit context, or traceability detail without changing the established behavior unnecessarily.

### 8.2 `PARTIAL` + `EXTEND`

- Locate the existing owning feature.
- Modify the existing requirement in place when the missing behavior is part of the same atomic responsibility.
- Add a new functional requirement under that existing feature only when the missing behavior is independently testable and would otherwise overload the existing requirement.
- Mark the affected requirement and feature `Partial` until the new target behavior is implemented and verified.
- Preserve already implemented sub-behavior and evidence.

### 8.3 `PARTIAL` + `REFACTOR`

- Preserve the cohesive capability and existing identifiers whenever possible.
- Update its target module/file ownership, contract location, workflow wiring, exports, dependencies, and tests.
- Record legacy paths in the current-to-target disposition or historical migration section when the README structure supports it.
- Do not create a duplicate feature merely to move or split implementation.
- Mark the feature `Partial` until the refactor and all behavior-preservation evidence are complete.

### 8.4 `ABSENT` + `CREATE`

Decide whether the gap is a **new feature**, **new functional requirement**, **workflow**, **non-functional requirement**, **contract addition**, **configuration item**, **persisted state**, **explicit exclusion**, or **open decision** using Section 9.

- New feature or functional requirement status: `Missing`.
- New workflow status: `Missing`.
- New usage and test locations are targets only, not evidence.

### 8.5 `CONFLICTING`

- Apply the ownership and consolidation decision from the approved closeout.
- Keep one canonical definition.
- Mark conflicting legacy definitions as `Removed`, `Retired`, `Withdrawn`, `Superseded`, or an approved equivalent.
- Never preserve two authoritative owners.
- When no approved decision exists, create an Open Decision and do not invent a resolution.

### 8.6 `UNKNOWN`

- Do not convert unknown evidence into an implementation requirement by guessing.
- Add a bounded Open Decision or evidence requirement in the correct README.
- Mark the affected capability non-implementation-ready.
- Include it as a blocker in the final response.

### 8.7 `NOT_APPLICABLE`

- Do not add implementation work.
- Record an explicit exclusion only when doing so prevents future ownership confusion.

### 8.8 `DEFERRED_INTEGRATION`

- Document the current domain's contract boundary, dependency, and future integration trigger.
- Do not make the current domain own behavior assigned to a later canonical owner.
- Do not label the deferred integration as implemented.

---

## 9. Decide Feature vs Functional Requirement vs Other Specification Element

### 9.1 Create a new Feature only when all are true

A gap is a new feature when:

1. It provides one cohesive capability or actor outcome.
2. It deserves one dedicated module folder under the domain.
3. It may expose several operations, but all serve the same outcome.
4. It has a distinct ownership boundary, workflow role, or persisted state.
5. Placing it in an existing feature would mix unrelated capabilities or overload that feature.
6. The reviewed audit assigns it to this domain.

A feature is **not** synonymous with one function, one table, one UI panel, or one checklist step.

### 9.2 Add or modify a Functional Requirement when

A gap defines one focused, independently testable behavior within an existing or newly approved feature, such as:

- Constructing or validating one contract.
- Performing one calculation.
- Enforcing one policy rule.
- Executing one state transition.
- Reading or writing one domain-owned state.
- Producing one deterministic result.
- Handling one failure condition.
- Exposing one focused operation.
- Applying one recovery rule.

Each FR should be implementable by one focused class, function, method, constant, or similarly bounded responsibility.

### 9.3 Add or modify a Workflow when

The gap describes an ordered end-to-end sequence involving multiple requirements, states, or domains.

Every new or changed workflow must document:

- Rank.
- Scope: internal or cross-domain.
- Trigger/input boundary.
- Ordered stages.
- Output boundary.
- Failure behavior.
- Requirement sequence.
- Planned standalone workflow usage program.
- Planned integration test.

### 9.4 Add a Non-Functional Requirement when

The gap constrains the entire domain rather than one business capability, including:

- Determinism.
- No-lookahead behavior.
- Security.
- Fail-closed behavior.
- Performance bounds.
- Compatibility.
- Reliability.
- Observability.
- Accessibility.
- Coverage and test obligations.
- Import and dependency boundaries.

Do not create a business feature for a package-wide quality attribute.

### 9.5 Contract placement

- A cross-feature foundational contract belongs in the domain's existing canonical contract feature when one exists.
- A feature-specific contract stays inside its owning feature.
- The producer domain defines the contract authoritatively.
- Consumer domains list it under consumed/shared contracts and describe only their use.
- Preserve contract versioning and compatibility rules.

### 9.6 Persisted state placement

A persisted entity belongs only to the canonical owner recorded by the database-ownership review.

Update:

- The domain's persisted-state summary.
- Database namespace and ownership.
- Read/write authority.
- Migration ownership.
- Transaction, idempotency, recovery, retention, and audit rules.
- Target table or record specification only when approved evidence is sufficient.

If the approved evidence does not define enough fields or invariants to specify the target safely, add an Open Decision instead of inventing a schema.

### 9.7 UI and calculation separation

- Domain calculations, validation, policies, and authoritative states remain in their business owner.
- UI-API owns cockpit panel composition, external transport, interaction DTOs, read models, warning presentation, and browser-facing state.
- Do not move a Risk calculation into UI-API because it appears on a gauge.
- Do not move a UI annunciator into Risk merely because it displays a Risk decision.

---

## 10. Required README Reconciliation Procedure

For each domain, perform the following in order.

### Step 1 — Establish current identity

Record internally:

- README path.
- Package path.
- Current status.
- Existing feature count.
- Existing FEAT, FR, NFR, WF, CAP, contract, schema, and error identifiers.
- Current public boundary.
- Current persisted-state ownership.
- Existing usage and test numbering.

Do not renumber anything.

### Step 2 — Filter approved findings

Select all reviewed gaps for which the domain is:

- Canonical owner.
- Contract consumer requiring README clarification.
- Workflow participant requiring boundary documentation.

Do not assign a gap to a domain merely because its UI displays the result.

### Step 3 — Map each gap to an existing destination first

For each row, identify:

```text
Existing feature
Existing functional requirement
Existing workflow
Existing contract
Existing persisted state
Existing NFR
Existing exclusion
```

Only after exhausting those destinations may you allocate a new feature or requirement.

### Step 4 — Make the feature/FR decision

Use Section 9 and record the decision in your working notes.

Every approved gap must map to exactly one primary specification destination:

```text
FEAT
FR
NFR
WF
Contract
Persistence
Configuration/Limit
Exclusion
Open Decision
```

A gap may require secondary README updates, but it has only one canonical behavioral owner.

### Step 5 — Update Purpose and Boundary

Update, when affected:

- Purpose.
- Owns.
- Does not own.
- Shared contracts.
- Persisted state.
- Cross-domain boundaries.
- Safety and simulation-only restrictions.

Keep the boundary concise but complete.

### Step 6 — Update the Feature Registry

For each affected feature row, update:

- Status.
- Feature ID and name.
- Owning module folder.
- Public API and contracts.
- Requirement IDs.
- Usage evidence or planned usage target.

For a new feature:

- Allocate the next valid unused feature ID according to the domain's existing numbering rules.
- Allocate a capability-oriented module-folder name.
- Add the planned numbered feature usage program.
- Update the total registered feature count.

Never call a feature simply `Trading Cockpit` when a domain-specific capability name exists.

### Step 7 — Update current-to-target structure

Update:

- Package tree.
- Approved target folders.
- Current-to-target module disposition.
- Dependency direction.
- Package-root export rules.
- Function-only or class-based public-boundary rules already established by that domain.
- Historical disposition sections where the current README already uses them.

A new folder is allowed only for a newly approved feature.

### Step 8 — Update Workflows

Modify an existing workflow when the Trading Cockpit behavior extends its current outcome.

Create a new workflow only when the actor outcome and ordered sequence are genuinely new.

Preserve retired workflow IDs and ranking conventions.

### Step 9 — Update Module and Requirement Specifications

For every modified or new FR, provide the domain's full standard row, including:

- Status.
- Requirement ID.
- Exact responsibility.
- Class / function / method / constant or planned focused operation.
- Side effects.
- Deterministic error/failure behavior.
- Usage target.
- Unit/component/integration target.

Requirements must use direct, testable language such as `shall`, `must`, `reject`, `return`, `persist`, `block`, `reconcile`, or `fail closed`.

Avoid vague language such as:

```text
support cockpit behavior
handle trading data
improve risk
provide gamification
```

### Step 10 — Update configuration and limits

Every policy-sensitive value must have:

- Name.
- Type.
- Default or explicit absence of a universal default.
- Required status.
- Owning feature.
- Description.
- Override and precedence rules.

Do not hard-code one universal account, risk, leverage, drawdown, spread, or risk-to-reward value when the approved specification makes it profile-driven.

### Step 11 — Update persistence and database ownership

Document only domain-owned state.

Do not give:

- Trading a second financial ledger.
- Portfolio a second broker-order authority.
- Data authority over trade mutation.
- Simulator authority over a real broker account.
- UI-API authoritative business state.
- Agentic unrestricted execution authority.

### Step 12 — Update package-wide requirements

Add or modify NFRs for any reviewed cross-cutting requirement.

Preserve existing NFR identities when extending the same concern.

### Step 13 — Update Open Decisions

A decision belongs here only when:

- The reviewed audit explicitly left it unresolved.
- The repository lacks evidence needed for a safe target.
- Two approved constraints cannot be reconciled without owner choice.

Do not use Open Decisions to avoid making a decision already resolved by Phase 0.

### Step 14 — Update Tests and Definition of Done

For every new or modified feature/FR/workflow, specify planned evidence at the same level as the existing README:

- Feature usage program.
- Workflow usage program.
- Unit tests.
- Component tests where local infrastructure is involved.
- Structural tests for imports, exports, ownership, and package shape.
- Integration tests for cross-domain behavior.
- Safety tests.
- Determinism/replay tests where relevant.
- Recovery/concurrency tests where relevant.
- Coverage obligations.

Do not claim planned files already exist.

### Step 15 — Update README status and checklists

Status semantics before implementation:

```text
Completed = full approved behavior is implemented and verified now
Partial   = useful implementation exists but approved target behavior, placement, or evidence is incomplete
Missing   = approved target behavior has no verified implementation
```

Additional historical statuses such as `Removed`, `Retired`, `Withdrawn`, and `Superseded` retain their current meaning.

Rules:

- New feature/FR/workflow: `Missing`.
- Existing feature with any incomplete target delta: `Partial`.
- Existing FR changed beyond currently implemented behavior: `Partial`.
- A feature is `Completed` only when all active owned FRs are completed.
- The package README's top-level status becomes `Partial` if any active target requirement is Missing or Partial.
- Keep existing completed items and `[X]` checklist entries intact when still true.
- Add `[ ]` entries for new incomplete target work.
- Update feature counts, workflow counts, usage-program counts, and completion text accurately.

### Step 16 — Make the README standalone

Before moving to the next domain, verify that a developer can understand and implement every added behavior without opening:

```text
docs/dev/trading-cockpit/
docs/dev/trading-cockpit/phase-0/
```

---

## 11. Domain Ownership Guardrails

Use the reviewed audit as the final ownership authority. The following principles are mandatory unless the closeout explicitly decided otherwise.

### Utils

Owns generic cross-domain primitives only: identifiers, time, exact units, validation structures, event metadata, configuration loading, idempotency primitives, redaction, deterministic hashing/randomness, telemetry, and generic state-machine helpers.

It does not own broker, market, risk, order, simulation, portfolio, or cockpit business semantics.

### Brokers

Owns provider adapters, provider capabilities, connection/session lifecycle, environment identity, broker-specific normalized commands/results, and provider-confirmed state.

It does not own risk approval, trade intent, portfolio accounting, or simulation game rules.

### Data

Owns trusted acquisition, normalization, point-in-time availability, market/reference evidence, source governance, data quality, streaming data, and Data-owned persistence infrastructure.

It does not own trade decisions, risk verdicts, orders, fills, or simulated financial state.

### Indicators

Owns deterministic derived market measurements, regimes, volatility, momentum, liquidity, structure, and cockpit-ready analytical gauge values.

It does not authorize trades or own UI rendering.

### Strategy

Owns strategy/playbook definitions, setup qualification, trade plans, entry/exit intent, operating envelopes, and approved management rules.

It does not size or approve risk, dispatch orders, or own financial accounting.

### Risk

Owns policies, validation gates, risk decisions, sizing authority, drawdown restrictions, lockouts, stress gates, and emergency risk governance.

It consumes evidence and portfolio views but does not own broker execution or the financial ledger.

### Trading

Owns order intent, order and position operational state, execution orchestration, idempotent dispatch, partial-fill handling, protective-order integrity, cancel/replace semantics, and reconciliation orchestration.

It does not own the authoritative balanced portfolio ledger.

### Simulator

Owns simulation clock, replay, no-lookahead enforcement, scenarios, game modes, checklists, latency/queue/fill models, simulated broker behavior, emergency injection, session persistence, and crash recovery for simulated sessions.

It must remain isolated from uncontrolled real-money execution.

### Analytics

Owns journals, scoring, debriefs, execution-quality analysis, behavior/process analysis, qualifications, and replay-derived learning evidence.

It does not redefine trade, risk, or portfolio authority.

### Optimization

Owns bounded calibration, parameter studies, scenario difficulty tuning, robustness evaluation, and anti-leakage optimization evidence.

It does not silently change approved production policies or strategy profiles.

### Research

Owns research interpretation, approved expectancy evidence, strategy evidence governance, scenario/stress assumptions, drift review, and research approvals.

It consumes point-in-time Data evidence and does not own market-data acquisition.

### Portfolio

Owns the authoritative financial ledger, valuation, P&L, margin, currencies, exposure, correlation, drawdown state, VaR/CVaR, stress state, and account-level portfolio view.

It does not own broker order state or risk-policy decisions.

### Agentic

Owns bounded coaching, explanations, debrief assistance, scenario instruction, and research assistance under deterministic permissions.

It may not bypass Risk, Trading, Broker, Simulator, audit, or human-approval boundaries.

### UI-API

Owns external API transport, browser interaction, cockpit read models, panel composition, warnings/annunciators, player actions, real-time delivery, accessibility, and presentation state.

It does not own authoritative calculations, policy decisions, orders, or portfolio accounting.

---

## 12. Cross-Domain Allocation Examples

Use these examples as decision patterns, not as replacements for the reviewed audit.

### Example A — Partial order lifecycle

If Trading already owns an order-lifecycle feature and the audit marks unknown orders or cancel/fill races as `PARTIAL + EXTEND`, extend the existing Trading feature and add or modify FRs there. Do not create a new `Trading Cockpit Orders` feature.

### Example B — Missing checklist engine

If Simulator has no feature capable of owning checklist state, prerequisites, invalidation, emergency interruption, and mode-specific enforcement, `ABSENT + CREATE` may justify one new Simulator feature. Individual checklist steps are data/requirements inside that feature, not separate features.

### Example C — Market-regime gauge

Indicators owns regime calculation and its typed analytical result. UI-API owns the cockpit gauge/read model that displays it. Neither domain redefines the other's contract.

### Example D — Drawdown breach

Portfolio owns authoritative account/equity/drawdown state when the reviewed audit assigns it there. Risk owns the policy decision and lockout. Simulator owns emergency scenario/game-state behavior. UI-API owns the warning and interaction. Do not collapse all four into one feature.

### Example E — Generic event envelope

Utils may own generic event metadata. Trading, Portfolio, Simulator, and Analytics own their domain event meanings. Do not move all events into Utils.

---

## 13. Baseline and Drift Check

Before editing:

1. Read the approved Phase 0 baseline and closeout.
2. Compare the current repository state with the approved baseline.
3. Ignore expected README edits made by this task.
4. If production code, tests, migrations, contracts, or public exports have changed after the reviewed audit in a way that affects a gap classification:
   - Do not silently repeat the whole audit.
   - Mark the affected row `BASELINE_DRIFT` in the final response.
   - Perform the minimum bounded inspection needed to determine whether the reviewed conclusion is still valid.
   - Do not finalize an affected target by guessing.

Unrelated owner changes must be preserved.

Do not reset, clean, stash, revert, or overwrite the working tree.

---

## 14. Required Validation

After all README edits, verify the following.

### 14.1 Coverage

- Every reviewed actionable gap is mapped.
- Every gap has exactly one canonical owner.
- Every `PARTIAL + EXTEND/REFACTOR` row maps to an existing feature or requirement unless the closeout explicitly approved a split.
- Every `ABSENT + CREATE` row has an explicit feature-vs-FR-vs-NFR-vs-workflow decision.
- Every `FULL + REUSE` row is not duplicated.
- Every `CONFLICTING` row is resolved or recorded as a blocker.

### 14.2 Identifier integrity

- No active ID is duplicated.
- No retired ID is reused.
- New IDs are the next valid values under each domain's existing convention.
- Feature counts and workflow counts are accurate.
- Usage-program numbering remains one-to-one with registered features where that domain requires it.

### 14.3 Structural integrity

- Every feature maps to one module folder.
- Every planned file responsibility remains focused.
- Every FR is atomic and testable.
- Package-root export rules remain consistent.
- Dependency direction is documented.
- No new horizontal technical-layer folder is introduced unless the domain's approved architecture already allows it.

### 14.4 Ownership integrity

- Owned and consumed contracts agree across READMEs.
- Contract versions and owners are consistent.
- Persisted state has one writer and one schema owner.
- UI-API does not become the business authority.
- Simulator cannot reach uncontrolled real-money execution.
- Agentic cannot bypass deterministic authorities.

### 14.5 Status integrity

- Newly documented but unimplemented work is not marked Completed.
- Existing completed behavior is not downgraded without evidence.
- Every affected feature's status agrees with its FRs.
- Every domain top-level status agrees with all active target requirements.

### 14.6 Standalone integrity

Search every modified README for normative references to temporary Trading Cockpit documents.

The README must remain understandable after the complete deletion of:

```text
docs/dev/trading-cockpit/
```

Links to durable repository-wide project rules may remain when already part of HaruQuantAI governance, but the domain behavior itself must be fully specified in the README.

### 14.7 Modification boundary

Confirm that only domain README files changed.

---

## 15. Required Final Response

Do not create another permanent planning document. Return the reconciliation report in your final response.

Use this format.

### 15.1 Decision

```text
README FOLDING RESULT: APPROVED | CONDITIONAL | BLOCKED
```

### 15.2 Modified files

List the exact fourteen README paths and identify which were changed or unchanged.

### 15.3 Per-domain summary

| Domain | README | Gap rows considered | Existing features modified | New features | Existing FRs modified | New FRs | Workflows changed/added | Contracts / Persistence / NFR updates | Final README status |
| ------ | ------ | ------------------: | -------------------------: | -----------: | --------------------: | ------: | ----------------------- | ------------------------------------- | ------------------- |

### 15.4 Temporary gap-to-README mapping

For every actionable Phase 0 gap, report:

| Gap ID | Classification | Approved action | Canonical domain | README destination | Feature ID | FR / NFR / WF / Contract destination | Result |
| ------ | -------------- | --------------- | ---------------- | ------------------ | ---------- | ------------------------------------ | ------ |

This mapping is temporary evidence and must not be required by the updated READMEs.

### 15.5 New identifier register

List every newly allocated:

- Feature ID.
- Functional requirement ID.
- Non-functional requirement ID.
- Workflow ID.
- Contract/schema version.
- Planned usage-program number.

### 15.6 Preserved brownfield assets

Summarize the existing features, contracts, functions, workflows, tests, and persistence structures that were reused rather than duplicated.

### 15.7 Unresolved findings

List:

- Open decisions.
- Baseline drift.
- Missing approved evidence.
- Cross-domain conflicts.
- Any domain that is not implementation-ready.

### 15.8 Safety and mutation confirmation

State exactly:

```text
No production source, test, migration, configuration, dependency, lockfile,
or broker state was modified. Only the authoritative domain README files were edited.
```

---

## 16. Completion Gate

This task is complete only when all of the following are true:

- All fourteen domain READMEs have been evaluated.
- Every reviewed actionable gap has a destination.
- Existing capabilities were extended before new capabilities were created.
- Every new feature is justified as a cohesive capability.
- Every new FR is atomic and testable.
- Cross-domain ownership is consistent.
- Statuses reflect actual pre-implementation reality.
- Planned usage and test evidence is specified without being falsely claimed as existing.
- Each README is independently sufficient to guide later code implementation.
- No updated README requires the Trading Cockpit Phase 0 documents to survive.
- Only domain README files changed.

Stop after the README reconciliation and final report. Do not begin code implementation.
