# HaruQuantAI V3 — Agile, Bottom-up Feature Implementation Plan

**Plan v1.0 · 6 September 2026 · 205 feature tasks + 8 Phase 0 preparation tasks**

## 1. Execution contract

This plan answers **what to implement and when**. The Feature–Requirement Traceability Register v1.0 supplies the 205 feature identities and owned scope. Authoritative domain READMEs supply public contracts, dependency declarations, configuration, file ownership, algorithms, catalogue entries, shared NFR applicability and detailed design. The feature pipeline remains mandatory.

**A feature is one task.** Every one of the 205 features appears exactly once in Phases 1–16. No second feature task is created for a UI hookup, test suite, release gate, performance task, algorithm variant, original DAG node, role or workflow. Existing implementation is reused inside that same feature slot. Phase 0 contains only the eight separately identified prerequisite tasks below.

**Delivery is Agile and vertically integrated.** Each phase produces a user-visible workflow through actual providers, its Interfaces boundary and the UI. Data is not considered delivered merely because its Python providers exist: Phase 2 includes Data Manager and chart behaviour plus real end-to-end verification. The same pattern repeats for strategy authoring, simulation/results, Chat Bot, research, retesting, Builder, optimization, portfolios and projects.

**Readiness, not a missing provider, controls sequencing.** The register contains 476 required edges and 233 operation-time dependencies. All 476 required edges are preserved. The schedule adds real-provider sequencing where the necessary provider is available in or before the same phase. Thirty-eight dependencies intentionally await later optional providers; their guard and contract adapter are implemented once in the consuming feature, and the later provider task supplies actual integration evidence. An unavailable optional operation must fail explicitly. It is never replaced with fabricated data or a fixture-labelled-as-production.

**One open feature task has one accepted implementation commit** under the existing Planner → Executor → Reviewer workflow, plus the normal explicit merge record required by repository governance. A verified already-complete feature retains its task slot and links its existing acceptance commit; do not force a rewrite or an empty commit. Phase 0/phase checkpoint evidence does not authorize any live-trading action.

### 1.1 A whole feature versus later provider availability

Some source features include more than one release milestone: native multi-entity exchange, notification channels, Studio modes and advanced numerical variants are examples. To keep the requested 205-task model, each task implements its **entire registered owner behaviour and adapter surface** once, including later-release variants owned by that feature. A later milestone can qualify or activate that already implemented variant; it does not hide unfinished implementation behind “optional”. Missing actual provider evidence is recorded as `OPERATION_NOT_QUALIFIED`, never as an end-to-end pass.

Contract-fixture evidence may prove a generic adapter's validation, routing and fail-closed behaviour. It does not prove actual cross-domain compatibility. The later provider task must supply that evidence through the already implemented public surface, update the earlier operation's qualification record, and run the relevant browser regression. If an earlier owner would need new behaviour rather than ordinary compatibility verification, stop and correct the same scope/schedule before acceptance; do not silently invent an additional task or weaken the one-feature boundary.

### 1.2 P phases are not U release milestones

Phases 0–16 are **execution increments**. Specification milestones U0–U13 remain **release acceptance gates**, with their original precedence. Building a reusable provider earlier is allowed; advertising an extension earlier is not. The 135 original DAG nodes are preserved as capability/test/readiness gates, not mistaken for feature identities. Their 604 hard edges and 13 release-precedence edges remain in `Dependency_Schedule.json` with task/evidence mappings. A mapped gate can pass only after both its producing tasks and all original predecessor gates have evidence.

Phase 0 is preparation, not proof that the specification's U0 runtime gate has passed. U0-labelled Workspace/Interfaces features remain in Phase 1. U0 can close after their real runtime/security/storage evidence is available; U1 closes no earlier than the end of Phase 2 and U2 no earlier than Phase 5.

### 1.3 Scope and state at the inspected baseline


| Measure | Count |
| --- | --- |
| Feature tasks | 205 |
| Phase 0 prerequisite tasks | 8 |
| Execution phases after Phase 0 | 16 |
| Owned functional requirements | 575 |
| Feature-specific NFRs | 276 |
| Shared NFRs retained in domain scope | 66 |
| Catalogue entries retained in domain scope | 646 |
| Original requirement-ID entries retained | 389 |
| Cross-feature workflows retained | 20 |


The source register was created from specification commit `c06456fe2c03bc89f52edad1a0a8428118287377`, blob `7b592a2c25276ceae7cf7011f0a4f98eabe9c7fd`. This plan inspected repository commit `a3c81dff4e5b903e749259ff463b8d9280d6fc26`; that checkout reports specification blob `d69bef59cb981350cd6f2ebdccc31b231a4e0950`. The header still says v2.1, so **the file hash, not the header date, establishes the drift**. Phase 0 must reconcile the clause-level difference while retaining the supplied 205-feature scope unless the owner explicitly changes it.

The baseline review is read-only and does not certify production code. No application test suite, live connector, LLM evaluation, native benchmark or Playwright acceptance flow was run in this planning session. Source directory presence and historical “Completed” labels are not equivalent to full register-scope acceptance.


| Plan status | Features | Meaning |
| --- | --- | --- |
| PARTIAL | 16 | Existing code with concrete registration, CI or documented incompleteness requiring closure. |
| EXISTING_UNVERIFIED | 37 | Existing implementation found; full normalized requirement coverage still needs verification. |
| NOT_STARTED_IN_TARGET | 152 | No matching target provider/registered feature was confirmed in the inspected current inventory; reuse candidates are not certified parity. |
| COMPLETE | 0 | None was independently proven complete against all new register obligations during this planning pass. |


The complete per-feature baseline, current-path aliases and remaining-work notes are in `Baseline_Audit.md`. CI run `34051983427` at this pinned HEAD failed: Ruff reported 36 findings and stopped the pipeline before later checks. The source of that fact is the CI job log, not a local run. This does not prove all features are broken; it prevents a blanket acceptance claim. Phase 0 triages prerequisite hygiene, while semantic feature changes remain in their existing task slots.

## 2. How to execute a feature task

Read the task card, the exact owning domain README entry, the feature's source register card and `docs/dev/feature_implementation_pipeline.md`. Implement or adapt only this feature's complete scope. Reuse passing behaviour, preserve existing public identities, and do not create a second owner because the register's target spelling differs from the current package.

Task order is the order printed below. A task can start only after its required predecessor evidence is available. Ready-wave data is included for reasoning about independent work, but the current Task/Goal workflow permits one active child Task at a time; it is not authorization for concurrent writes or a new orchestration engine.

### 2.1 Required evidence bundle — every feature

Persist `docs/dev/evidence/features/<FEAT-ID>/acceptance.json`, linked test reports and the feature acceptance commit. The manifest records feature/task/source/README hashes, baseline and tested commit, each FR/local-NFR/shared-NFR/catalogue/acceptance mapping, exact commands and exit codes, fixture hashes, environment, review outcome, coverage, usage transcript or browser trace, lifecycle/removal results, and operation qualification status. Do not place credentials or private raw data in evidence.

To avoid a self-referential Git hash, evidence committed with the feature pins its tested tree/parent and report hashes. The Reviewer/Task close-out receipt records the final accepted commit SHA after creation; link it in the normal tracker/evidence index without creating another implementation task or an empty commit. Keep the planned scope immutable and record execution progress in the tracker and acceptance receipts.

Maintain distinct contract, provider, composition, Interfaces, UI and end-to-end evidence states. “Not applicable” must explain why. Feature-local tests cannot be substituted for actual real-provider integration evidence; screenshots cannot substitute for interaction assertions. A selected test path in this plan is an intended delivery location, not a claim the file already exists. Phase 0 path bindings may map it to a compatible existing test owner without changing its requirement or oracle.

### 2.2 Usage examples — not pytest examples

Backend feature usage belongs in its designated primary domain-logic module, through the pipeline's bounded offline executable demonstration. The canonical README supplies the exact runnable command and expected output. It must exercise a useful public operation, a failure/unavailable case and cleanup; it must not depend on a real account, private market files or network availability by default.

An Interfaces feature additionally documents exact authenticated request/response examples. A UI feature documents a reachable interactive workflow in its README and is verified separately by browser tests. Tests may check examples, but a file under `tests/` is not the feature's public usage documentation.

### 2.3 Verification and Definition of Done — DOD-F

DOD-F applies to each feature card without being a separate task. All listed FRs and local NFRs must be implemented and mapped to passing acceptance evidence; all applicable shared NFRs and catalogue/source obligations in the canonical README remain binding. An absent future provider is allowed only under an explicit operation gate with tested complete adapter behaviour and no false runtime-support claim.

The feature has its mandatory README, immutable manifest, strict configuration and lifecycle entry point (or the TypeScript/React variant). Provided/required/optional capabilities, accepted configuration and state declarations agree. No private cross-feature imports, import-time effects, UI business calculations or Interfaces persistence appear. Mount failure, provider removal/replacement, repeated cleanup, retention and physical removal are proved. Numerical providers include causal/golden/native equivalence and relevant bounded-resource evidence.

The documented usage runs successfully; affected real-provider integration and current phase/browser regressions pass. Commit/review/CI gates pass through the repository workflow. Scope and evidence are reviewed independently, the accepted commit is recorded, and the next feature starts from clean accepted `main`. Outstanding unimplemented owned behaviour or fabricated/missing mandatory evidence prevents acceptance.

Use change-scoped commands during development, with the actual owner paths bound in Phase 0:

```powershell
uv run --frozen pytest --no-cov <affected_test_path>
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy
uv run --frozen lint-imports
uv run --frozen python scripts/architecture_check.py
uv run --frozen python scripts/validate_feature_docs.py
uv run --frozen python scripts/verify_feature_removal.py --feature <FEAT-ID> --report <report.json>
```

UI commands use the existing `app/ui/package.json` scripts and its lockfile: scoped Vitest (`npm run test -- <selected-path>`), typecheck (`npm run typecheck`), build (`npm run build`) and scoped Playwright (`npm run e2e -- <selected-path>`). Phase 0 verifies the runner's test discovery and package-manager binding before these examples are executed. Use the existing D-UI removal harness, not the Python entry-point remover, for UI features.

The full `scripts/ci_check.py` / coverage gate runs only at the approved pre-commit/CI/release boundary, not during iterative feature implementation. The pipeline's branch-coverage floor and any stronger applicable owner requirements remain unchanged.

### 2.4 One phase checkpoint, inside a feature task

The last feature task in each phase owns the cross-feature browser checkpoint for that phase. Every preceding task still has its own acceptance tests, usage and commit. The phase checkpoint adds integration evidence, not another task or another product owner. Later providers also own the regression evidence that activates previously unavailable paths in existing widgets/gateways. The semantic owner of a calculation or workflow never changes merely because another task runs its integration suite.

## 3. Phase overview


| Phase | Feature tasks | User-visible completion |
| --- | --- | --- |
| 1 | 30 | Workspace, access, resource control and visible operational shell |
| 2 | 32 | Data Manager end to end |
| 3 | 18 | Strategy authoring and numerical building blocks in the UI |
| 4 | 27 | Native tick backtest, results and databanks end to end |
| 5 | 11 | Contextual Chat Bot and inspectable Agentic evidence |
| 6 | 11 | Research protocols and reviewed AI strategy creation |
| 7 | 7 | Retesting, robustness and independent challenge |
| 8 | 5 | Builder generation, ranking and evolution |
| 9 | 6 | Optimization and walk-forward evidence |
| 10 | 12 | Portfolio construction and correlation in the UI |
| 11 | 9 | Research projects, notifications, memory and calibration |
| 12 | 13 | Safe extension development, source generation and indicator testing |
| 13 | 4 | Advanced analysis, market profiles and research extensions |
| 14 | 7 | Neural research from dataset to qualified inference |
| 15 | 1 | Remote workers with the existing operational UI |
| 16 | 12 | Qualified external exchange, packaging and distribution |


Navigation: [Phase 1](#phase-1) · [Phase 2](#phase-2) · [Phase 3](#phase-3) · [Phase 4](#phase-4) · [Phase 5](#phase-5) · [Phase 6](#phase-6) · [Phase 7](#phase-7) · [Phase 8](#phase-8) · [Phase 9](#phase-9) · [Phase 10](#phase-10) · [Phase 11](#phase-11) · [Phase 12](#phase-12) · [Phase 13](#phase-13) · [Phase 14](#phase-14) · [Phase 15](#phase-15) · [Phase 16](#phase-16)

## 4. Phase 0 — Preconditions, contracts and evidence readiness

**Eight prerequisite tasks; no feature task is consumed here.** All Phase 0 task statuses start `NOT_EXECUTED`.

### - [ ] Preparation 0.01 — Freeze the source and the 205-feature scope

Record immutable copies/hashes of the supplied register Markdown/JSON, the earlier capability DAG and the live repository baseline. Compare the register source blob 7b592a2c25276ceae7cf7011f0a4f98eabe9c7fd against the current specification blob d69bef59cb981350cd6f2ebdccc31b231a4e0950. Inspect the exact diff; classify every changed clause as retained, already covered, changed, or scope-impacting. Do not infer freshness from timestamps or silently change the 205-feature set.

**Acceptance:** The baseline manifest has the exact feature ID set, hashes, source-drift disposition and approved ownership resolutions. A true added/removed feature requires explicit scope change and regeneration, not an invented 206th task.

**Evidence:** baseline-manifest.json; specification-drift.md.

**Commit message:** `docs(sqx): pin the feature-plan baseline and source reconciliation`

### - [ ] Preparation 0.02 — Audit existing feature evidence and current paths

Inspect all 205 target owners and their public contracts. Reconcile the target spellings with existing paths, including workspace_lifecycle, local_access_health, diagnostic_bundle and the Plugins semantic folders. Record current contracts, code, entry points, UI registries, tests, usage, dependencies and known gaps separately. Check the exact current entry-point set directly; do not use stale master counts. Confirm exact current baseline findings rather than assuming a missing target spelling means missing behaviour.

**Acceptance:** Every feature has a per-requirement disposition: proved-complete, implement, adapt, verify, or blocked with reason. COMPLETE requires mapped passing evidence and a feature acceptance commit. PARTIAL records specific remaining obligations; unknown coverage is not marked complete. All 205 slots remain, including reused completed features.

**Evidence:** feature-baseline.json; requirement-status.json; path-bindings.json.

**Commit message:** `docs(sqx): record feature reuse status and evidence gaps`

### - [ ] Preparation 0.03 — Publish the authoritative domain README bindings

Merge all selected boundaries, exact identities, FR/local-NFR lists, shared NFR applicability, catalogue entries, contract signatures/DTOs/errors, state, paths, source aliases, fixtures and removal rules into the 18 owning domain READMEs. Preserve unrelated domain scope and permanent numeric UI IDs. Existing public contracts win where compatible; resolve mismatches explicitly, including Data storage/browse overlap, Workspace versus Orchestration authority and public schema examples. Provide feature-local README content required by the pipeline as each feature is implemented; domain READMEs do not replace those files.

**Acceptance:** All 205 feature cards resolve to one canonical domain README entry; all 575 FRs, 276 local NFRs, 66 shared NFRs, 646 catalogue entries, 389 source-ID mappings and 20 workflows remain accounted for. No executor needs to invent contract signatures, algorithm semantics, accepted config or ownership.

**Evidence:** 18 domain README updates; contract-binding register; schema/fixture plan.

**Commit message:** `docs(sqx): bind all 205 features to authoritative domain specifications`

### - [ ] Preparation 0.04 — Freeze the DAG, operation gates and Agile checkpoints

Ratify the required graph, operation-time readiness matrix and added real-provider sequencing constraints in the supplied schedule. Preserve the original DAG as a capability-acceptance graph, not a one-node/one-feature task list. Approve every later-operation gate and assign its real integration evidence to the later provider task. Freeze the capability, route and widget contribution interfaces so future providers do not require a second implementation task for an earlier owner.

**Acceptance:** Exactly one scheduled task exists for each registered feature, every required predecessor is earlier, every deferred operation has a provider/consumer/guard/test owner, and each phase has a real UI checkpoint. U0–U13 release precedence remains separate and acyclic.

**Evidence:** dependency-schedule.json; operation-readiness.json; phase/UI acceptance matrix.

**Commit message:** `docs(sqx): freeze the bottom-up Agile feature schedule`

### - [ ] Preparation 0.05 — Specify the numerical, external-evidence and security prerequisites

Resolve the numerical policy, production generated-tick algorithm, scaled arithmetic/overflow, native state and checkpoint contracts. Create hash-pinned small/medium/large fixtures, security/isolation policies and source/provider/target compatibility matrices. Address the register’s eight EVD dependencies with named evidence owners and due gates. Never invent unavailable donor classes, source licences, binary offsets or toolchain success. Missing optional external evidence blocks that affected claim, not unrelated core development.

**Acceptance:** Phase 1 fixtures/inputs and security requirements are available. EVD-TICKS-01 is closed before its Phase 4 task; EVD-CONTRACT-01 is closed before each production consumer; other evidence is linked to an explicit due phase and fail-closed operation. The complete donor parity label remains unavailable until the full authorised inventory is reconciled.

**Evidence:** fixture manifest; numerical/security policy; external-evidence calendar.

**Commit message:** `docs(sqx): pin numerical fixtures and external qualification gates`

### - [ ] Preparation 0.06 — Establish a reproducible quality and performance baseline

Record Windows/Python/Node/package/toolchain versions from the lockfiles and runtime probes; record reference hardware and finite workload budgets before scale qualification. Triage CI run 34051983427/job 101537114162 at a3c81df: Ruff reports 36 findings, then the gate stops. Repair only prerequisite baseline hygiene through this Phase 0 readiness task with owner-scoped changes; substantive feature gaps remain in their existing feature task. Run the full gate only at the approved commit/CI baseline boundary, not during iterative implementation.

**Acceptance:** Baseline quality failures are resolved or explicitly owner-classified and no affected acceptance is fabricated. Before starting a dependent feature, all required baseline/security checks are green. Capture one named hardware/runtime baseline and real measurements; “target” and “measured” remain distinct. Do not weaken lint, type, security or coverage checks to manufacture a pass.

**Evidence:** quality-baseline.md; CI evidence; reference-hardware.json; performance-baseline.json.

**Commit message:** `chore(sqx): establish the reproducible implementation baseline`

### - [ ] Preparation 0.07 — Prepare evidence, usage and browser-test harnesses

Prepare the common evidence schema and locations used below. Define synthetic, deterministic no-live-order fixtures and per-feature primary usage-module bindings. Add schema checks for feature/FR/NFR/catalogue/acceptance/commit links and the browser slice harness. Ensure real-provider browser tests are distinguishable from contract stubs and screenshots. Reuse existing repository runners rather than introduce another framework.

**Acceptance:** Every task has a deterministic usage recipe, test target and evidence destination. The browser harness can open a blank/template workspace, authenticate, exercise a real available capability and record accessibility/performance/recovery evidence. Harness code is testing infrastructure, not untracked feature implementation.

**Evidence:** evidence schema; usage-bindings.json; browser fixture/test harness.

**Commit message:** `test(sqx): prepare feature and UI acceptance evidence harnesses`

### - [ ] Preparation 0.08 — Ratify Phase 1 entry and freeze the execution tracker

Review source reconciliation, 205 one-to-one task slots, canonical README entries, baseline findings, generated schedule and external gates. Freeze the tracker used by the Task/Goal workflow. Preserve one active feature Task at a time and one feature implementation commit plus its normal merge record. Phase 0 preparation is not the specification U0 runtime acceptance milestone; the six U0-labelled product features are still implemented or reused in Phase 1.

**Acceptance:** Phase 1 may start only when its contracts, fixtures, permissions, substrate and quality prerequisites have evidence. All feature slots are present and correctly classified; no feature task was hidden inside Phase 0. Publish the source and plan hashes and pass the supplied plan validator.

**Evidence:** phase-0-exit.md; approved tracker and execution configuration.

**Commit message:** `docs(sqx): ratify Phase 1 entry and the 205-feature tracker`

<a id="phase-1"></a>

## Phase 1 — Workspace, access, resource control and visible operational shell

**Feature tasks: 30.** Workspace → account/settings/job providers → identity/settings/jobs gateways → workspace/settings/run-monitor/debug UI. Agentic mandate/role/tool/model foundations are also prepared, but no successful Chat Bot route is advertised yet.

**Visible completion:** Open a real workspace, sign in, change a setting, submit a bounded demonstration job, observe and cancel it in the Jobs widget, then reopen the layout.

**Phase evidence:** `tests/ui/e2e/research/phase_01.spec.ts` and `docs/dev/evidence/phases/phase-01.json`, owned by Task 1.30. All prior affected UI/data/recovery regressions remain required.

<a id="task-1-01"></a>

### - [ ] Task 1.01 — FEAT-UI-01 — Compose and restore the research workspace

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

The user can add, remove, dock, tab, resize and restore independently registered tools without corrupting business state.

**Reuse:** `app/ui/src/widgets/workspaces`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-01-001 | Register widget type/version, feature/capabilities, placement/dimensions, commands, subscriptions, config migration and exact disposer in one lazy registry. |
| FR-TRC-UI-01-002 | Serialize safe stable resource IDs and display preferences only; restore layout topology with per-panel unknown/unavailable recovery. |
| FR-TRC-UI-01-003 | Deliver research and existing workspace templates, tab/split/float/tear-off/reposition controls, empty state and keyboard focus recovery. |
| FR-TRC-UI-01-004 | Keep closing an observer distinct from cancelling its accepted owner job. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-01-001 | Each widget and registration proves exact cleanup and isolated layout failure. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-01-001 | Host/sidebar/type validation/templates all consume the same registry; a removed widget cannot be rediscovered by a stale static mapping. |
| AT-UI-01-002 | One invalid/missing widget does not discard valid siblings; secrets, strategies, raw rows and provider objects never enter saved layout. |
| AT-UI-01-003 | Persist/restore round-trips panel topology and stable identity; unsupported cross-window behavior is explicitly disabled rather than falsely advertised. |
| AT-UI-01-004 | Unmount releases timers/listeners/workers/requests but a running backtest continues unless the explicit owner cancellation command is issued. |
| ATN-UI-01-001 | 100 enable/disable cycles, physical widget removal and partially corrupt persisted layouts leave no leaked effect or lost valid sibling. |


**Acceptance test targets:** `app/ui/src/widgets/workspaces/__tests__/traceability.test.tsx`; `app/ui/src/widgets/workspaces/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Compose and restore the research workspace). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Host/sidebar/type validation/templates all consume the same registry; a removed widget cannot be rediscovered by a stale static mapping. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-01/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-01`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-02"></a>

### - [ ] Task 1.02 — FEAT-UI-14 — Call the typed backend and resume observation

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

Widgets share compatible authenticated requests, typed errors and reconnect behavior without duplicating transport semantics.

**Reuse:** `app/ui/src/clients`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-14-001 | Validate generated/approved wire DTOs and preserve existing ApiResponse/ApiError/ApiMetadata/StreamEvent contracts. |
| FR-TRC-UI-14-002 | Manage cookie/CSRF headers, bounded safe-read retries, stream cursors, abort, stale request cancellation and deduplicated subscriptions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-14-001 | Removing FEAT-UI-14 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-14-001 | Schema drift and wrong response shapes fail visibly; no unchecked any/object fallback supplies a business value. |
| AT-UI-14-002 | Mutations are retried only by their original idempotency identity and reconciliation policy; navigation aborts stale observations. |
| ATN-UI-14-001 | Disable and physically remove clients; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/clients/__tests__/traceability.test.tsx`; `app/ui/src/clients/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Call the typed backend and resume observation). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Schema drift and wrong response shapes fail visibly; no unchecked any/object fallback supplies a business value. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-14/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-14`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-03"></a>

### - [ ] Task 1.03 — FEAT-WS-MANAGE_WORKSPACES — Open, recover and back up a workspace

**Status:** `PARTIAL` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U0.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

A user can reopen the same workspace after a crash without losing committed metadata or artifact references.

**Reuse:** `app/services/workspace/workspace_lifecycle`. The current workspace_lifecycle package exists with the four delivery files, but it is not listed in the inspected feature entry-point group. Preserve its recovery logic; reconcile target path/key and provide registration, resource-aware backup/publication and complete traceability evidence.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-MANAGE_WORKSPACES-001 | Initialize/open a workspace with one active writer fence and explicit read-only recovery mode. |
| FR-TRC-WS-MANAGE_WORKSPACES-002 | Back up metadata and referenced immutable artifacts as one verified manifest and restore into empty staging before switching the active workspace. |
| FR-TRC-WS-MANAGE_WORKSPACES-003 | Reconcile incomplete migration/publication records after a crash without deleting committed domain evidence. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-MANAGE_WORKSPACES-001 | Removing FEAT-WS-MANAGE_WORKSPACES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-MANAGE_WORKSPACES-001 | Two concurrent writers yield one owner and one denied/read-only session; reopening preserves the same workspace ID. |
| AT-WS-MANAGE_WORKSPACES-002 | Corrupt one member: restore is rejected before switch; a valid restore reconciles all counts, hashes and references. |
| AT-WS-MANAGE_WORKSPACES-003 | Inject crashes before promotion and after promotion/before catalogue commit; no committed row points at partial bytes and orphan custody is reported. |
| ATN-WS-MANAGE_WORKSPACES-001 | Disable and physically remove manage_workspaces; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/manage_workspaces/test_traceability.py`; `tests/services/workspace/manage_workspaces/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Initialize/open a workspace with one active writer fence and explicit read-only recovery mode. Expected: Two concurrent writers yield one owner and one denied/read-only session; reopening preserves the same workspace ID. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-MANAGE_WORKSPACES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(workspace): complete FEAT-WS-MANAGE_WORKSPACES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-04"></a>

### - [ ] Task 1.04 — FEAT-WS-MANAGE_ACCOUNTS — Verify accounts, principals and sessions

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U0.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

A request carries a real authenticated principal and workspace/account scope rather than browser-asserted identity.

**Reuse:** `app/services/workspace/manage_accounts`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-MANAGE_ACCOUNTS-001 | Verify session expiry, revocation, principal and authorized account/workspace before returning a bounded identity projection. |
| FR-TRC-WS-MANAGE_ACCOUNTS-002 | Revalidate identity on resumed work and evidence access rather than trusting a previously captured UI context. |
| FR-TRC-WS-MANAGE_ACCOUNTS-003 | Retain redacted authentication/audit references and keep credential material out of public session records. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-MANAGE_ACCOUNTS-001 | Removing FEAT-WS-MANAGE_ACCOUNTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-MANAGE_ACCOUNTS-001 | Expired, revoked and wrong-account sessions produce denial before any receiver mutation. |
| AT-WS-MANAGE_ACCOUNTS-002 | Revoke access between capture and use: the next read/handoff fails despite an otherwise valid snapshot. |
| AT-WS-MANAGE_ACCOUNTS-003 | Wire/log/export fixtures contain no password, raw token or broker credential. |
| ATN-WS-MANAGE_ACCOUNTS-001 | Disable and physically remove manage_accounts; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/manage_accounts/test_traceability.py`; `tests/services/workspace/manage_accounts/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Verify session expiry, revocation, principal and authorized account/workspace before returning a bounded identity projection. Expected: Expired, revoked and wrong-account sessions produce denial before any receiver mutation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-MANAGE_ACCOUNTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(workspace): complete FEAT-WS-MANAGE_ACCOUNTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-05"></a>

### - [ ] Task 1.05 — FEAT-PLUG-DECLARE_MANIFESTS — Inspect and validate extension manifests

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U1.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

A package declares what it contributes, needs and is allowed to do before any code or panel is activated.

**Reuse:** `app/services/plugins/manifests`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-DECLARE_MANIFESTS-001 | Validate extension identity/version, contributions, dependencies, compatible contracts, resources/hashes, permission/egress/resource requests and migration declarations. |
| FR-TRC-PLUG-DECLARE_MANIFESTS-002 | Return a bounded compatibility/permission/ownership preview with exact versioned metadata. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-DECLARE_MANIFESTS-001 | Removing FEAT-PLUG-DECLARE_MANIFESTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-DECLARE_MANIFESTS-001 | Unknown/overbroad permissions or incompatible majors fail before activation; manifest inspection executes no package code. |
| AT-PLUG-DECLARE_MANIFESTS-002 | A display name cannot grant authority or replace another contribution identity. |
| ATN-PLUG-DECLARE_MANIFESTS-001 | Disable and physically remove declare_manifests; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/declare_manifests/test_traceability.py`; `tests/services/plugins/declare_manifests/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate extension identity/version, contributions, dependencies, compatible contracts, resources/hashes, permission/egress/resource requests and migration declarations. Expected: Unknown/overbroad permissions or incompatible majors fail before activation; manifest inspection executes no package code. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-DECLARE_MANIFESTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-DECLARE_MANIFESTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-06"></a>

### - [ ] Task 1.06 — FEAT-UI-VIEW_COLLECTIONS — Navigate large typed collections accessibly

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01, 1.02.

#### i. Feature and remaining work

Any workbench collection supports predictable sorting, selection and inspection without loading its entire dataset.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-VIEW_COLLECTIONS-001 | Render stable-ID typed columns with server-side cursor sorting/filtering, pin/reorder/resize/hide/group and explicit null/undefined states. |
| FR-TRC-UI-VIEW_COLLECTIONS-002 | Support single/range/toggle/select-all-except snapshot selection, context menus, keyboard focus and query-backed bulk previews. |
| FR-TRC-UI-VIEW_COLLECTIONS-003 | Deliver loading/empty/partial/stale/error/denied states and bounded update coalescing for every CAT-GRIDS family. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-VIEW_COLLECTIONS-001 | The grid holds only the virtualized window and bounded selection/query metadata. |
| NFR-TRC-UI-VIEW_COLLECTIONS-002 | Unmount cancels all timers/listeners/observers/queries and releases workers/buffers. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-VIEW_COLLECTIONS-001 | Numeric/date/null sorts preserve owner semantics; unknown/missing plugin columns have a recoverable unavailable state. |
| AT-UI-VIEW_COLLECTIONS-002 | Selecting 1M logical rows retains a bounded token/window, not a million browser objects. |
| AT-UI-VIEW_COLLECTIONS-003 | First useful page p95 ≤1 s, indexed filter p95 ≤750 ms, typical scrolling 55+ FPS and ≤10 visual batches/s on the pinned fixture/hardware. |
| ATN-UI-VIEW_COLLECTIONS-001 | 10k/100k/1M logical-row fixtures prove resident-row/DOM/memory bounds and selection correctness during churn. |
| ATN-UI-VIEW_COLLECTIONS-002 | Repeated mount/unmount plus heap/native/browser profiles show no continuing growth beyond declared caches. |


**Acceptance test targets:** `app/ui/src/widgets/collection-grid/__tests__/traceability.test.tsx`; `app/ui/src/widgets/collection-grid/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Navigate large typed collections accessibly). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Numeric/date/null sorts preserve owner semantics; unknown/missing plugin columns have a recoverable unavailable state. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-VIEW_COLLECTIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-VIEW_COLLECTIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-07"></a>

### - [ ] Task 1.07 — FEAT-UI-REVIEW_DRAFTS — Review typed edits and consequential action scope

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01.

#### i. Feature and remaining work

The user can safely finish or abandon a form and understand exactly what a destructive or reviewed operation will affect.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-REVIEW_DRAFTS-001 | Provide one accessible overlay foundation with focus trap/restore, labelled title/description, escape/scroll policy and restrained announcements. |
| FR-TRC-UI-REVIEW_DRAFTS-002 | Preserve typed dirty draft state and show both client hints and authoritative field/summary errors. |
| FR-TRC-UI-REVIEW_DRAFTS-003 | Bind confirmation/review to exact object, count, dependencies, reversibility, retained state, candidate hash and expected revision. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-REVIEW_DRAFTS-001 | Removing FEAT-UI-REVIEW_DRAFTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-REVIEW_DRAFTS-001 | Keyboard/screen-reader fixtures reach confirm/cancel and restore focus; nested-modal traps are replaced with drawer/route/back navigation. |
| AT-UI-REVIEW_DRAFTS-002 | Cancelling a harmless chooser discards no unrelated draft; abandoning a destructive/long form warns on unsaved changes. |
| AT-UI-REVIEW_DRAFTS-003 | A changed scope/hash invalidates the review; model prose cannot manufacture a clickable server action. |
| ATN-UI-REVIEW_DRAFTS-001 | Disable and physically remove draft-review; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/widgets/draft-review/__tests__/traceability.test.tsx`; `app/ui/src/widgets/draft-review/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Review typed edits and consequential action scope). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Keyboard/screen-reader fixtures reach confirm/cancel and restore focus; nested-modal traps are replaced with drawer/route/back navigation. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-REVIEW_DRAFTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-REVIEW_DRAFTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-08"></a>

### - [ ] Task 1.08 — FEAT-IFACE-SERVE_API_EVENTS — Serve compatible API envelopes and resumable events

**Status:** `PARTIAL` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U0.

**Order prerequisites:** 1.04.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

**Reuse:** `app/services/interfaces/serve_api_events`. The current transport is registered. CI reports complexity/return-count failures in _dispatch_data_reference at asgi.py:2116. Preserve envelope/auth/SSE behaviour, resolve those findings and prove the register-required replay, fail-closed and resource bounds.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-SERVE_API_EVENTS-001 | Version and validate the existing API envelope, request/trace/idempotency metadata, side-effect classification and bounded errors. |
| FR-TRC-IFACE-SERVE_API_EVENTS-002 | Stream monotonic bounded owner events with heartbeat, replay cursor, deduplication/gap/expiry/resync and abort cleanup. |
| FR-TRC-IFACE-SERVE_API_EVENTS-003 | Apply cookie/session/CSRF transport, bounded query pages and artifact download validation without owning domain data. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-SERVE_API_EVENTS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-SERVE_API_EVENTS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-SERVE_API_EVENTS-001 | Wire compatibility goldens pass; a long command returns its actual owner job reference, not fabricated completion. |
| AT-IFACE-SERVE_API_EVENTS-002 | Disconnect/reconnect yields no duplicated command or missed terminal outcome; expired cursors force a snapshot. |
| AT-IFACE-SERVE_API_EVENTS-003 | Unauthorized/CSRF-invalid writes and unsafe downloads fail before receiver invocation; no SQL/file parser is present. |
| ATN-IFACE-SERVE_API_EVENTS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-SERVE_API_EVENTS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/serve_api_events/test_traceability.py`; `tests/services/interfaces/serve_api_events/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Version and validate the existing API envelope, request/trace/idempotency metadata, side-effect classification and bounded errors. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Wire compatibility goldens pass; a long command returns its actual owner job reference, not fabricated completion. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-SERVE_API_EVENTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(interfaces): complete FEAT-IFACE-SERVE_API_EVENTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-09"></a>

### - [ ] Task 1.09 — FEAT-WS-EXECUTE_PERSISTENCE — Execute bounded feature-owned transactions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U0.

**Order prerequisites:** 1.03.

#### i. Feature and remaining work

Stateful features can commit and recover their own records without receiving an unrestricted database connection.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-EXECUTE_PERSISTENCE-001 | Execute registered namespace-bound transactions with idempotency and expected revision; reject undeclared table/namespace access. |
| FR-TRC-WS-EXECUTE_PERSISTENCE-002 | Apply ordered additive feature migration manifests with checksum verification and transactional rollback. |
| FR-TRC-WS-EXECUTE_PERSISTENCE-003 | Keep append-only evidence immutable and provide bounded owner-scoped reads/export operations. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-EXECUTE_PERSISTENCE-001 | Removing FEAT-WS-EXECUTE_PERSISTENCE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-EXECUTE_PERSISTENCE-001 | A workflow writer cannot update claim tables; two competing expected-revision writes accept exactly one. |
| AT-WS-EXECUTE_PERSISTENCE-002 | Reapplying the same manifest changes nothing; changed checksum fails; a failed migration does not partially advance the schema version. |
| AT-WS-EXECUTE_PERSISTENCE-003 | An attempted overwrite/delete of retained evidence is denied; paged export has stable order and cannot cross workspace scope. |
| ATN-WS-EXECUTE_PERSISTENCE-001 | Disable and physically remove execute_persistence; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/execute_persistence/test_traceability.py`; `tests/services/workspace/execute_persistence/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Execute registered namespace-bound transactions with idempotency and expected revision; reject undeclared table/namespace access. Expected: A workflow writer cannot update claim tables; two competing expected-revision writes accept exactly one. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-EXECUTE_PERSISTENCE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(workspace): complete FEAT-WS-EXECUTE_PERSISTENCE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-10"></a>

### - [ ] Task 1.10 — FEAT-WS-SECURE_LOCAL_ACCESS — Resolve secrets and protect host access

**Status:** `PARTIAL` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U0.

**Order prerequisites:** 1.04.

#### i. Feature and remaining work

Configured connectors and providers can authenticate without exposing credentials to agents, widgets or exported artifacts.

**Reuse:** `app/services/workspace/local_access_health`. Reuse local_access_health. Its package is not present in the inspected entry-point group; prove scoped secret references, session/host access and required lifecycle/configuration evidence before acceptance.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-SECURE_LOCAL_ACCESS-001 | Create and resolve opaque secret references only for an authorized selected adapter generation and purpose. |
| FR-TRC-WS-SECURE_LOCAL_ACCESS-002 | Validate loopback/nonlocal host access configuration and require authenticated policy before exposing remote access. |
| FR-TRC-WS-SECURE_LOCAL_ACCESS-003 | Rotate/revoke a secret reference without rewriting historic provenance or enabling silent provider fallback. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-SECURE_LOCAL_ACCESS-001 | Removing FEAT-WS-SECURE_LOCAL_ACCESS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-SECURE_LOCAL_ACCESS-001 | A UI, Agentic role or unrelated provider cannot resolve a secret; the approved adapter receives it only inside its isolated boundary. |
| AT-WS-SECURE_LOCAL_ACCESS-002 | An unauthenticated nonloopback configuration is rejected before listener startup; status reports no secret values. |
| AT-WS-SECURE_LOCAL_ACCESS-003 | An old generation loses future resolution, while historical records retain only the old opaque reference. |
| ATN-WS-SECURE_LOCAL_ACCESS-001 | Disable and physically remove secure_local_access; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/secure_local_access/test_traceability.py`; `tests/services/workspace/secure_local_access/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create and resolve opaque secret references only for an authorized selected adapter generation and purpose. Expected: A UI, Agentic role or unrelated provider cannot resolve a secret; the approved adapter receives it only inside its isolated boundary. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-SECURE_LOCAL_ACCESS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(workspace): complete FEAT-WS-SECURE_LOCAL_ACCESS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-11"></a>

### - [ ] Task 1.11 — FEAT-WS-ADMINISTER_SETTINGS — Version user-visible system settings

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.04.

#### i. Feature and remaining work

The user sees and changes the effective configuration through its real owner with an explicit impact preview.

**Reuse:** `app/services/workspace/administer_settings`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-ADMINISTER_SETTINGS-001 | Read and update schema-validated setting revisions using expected revision; reject unknown keys and incompatible combinations. |
| FR-TRC-WS-ADMINISTER_SETTINGS-002 | Expose owner, effective default, narrower policy, remount/restart effect and secret-reference slots for each setting. |
| FR-TRC-WS-ADMINISTER_SETTINGS-003 | Preserve user-visible units, locale, theme, sound, picker/view defaults and report header/footer without placing business data in layout state. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-ADMINISTER_SETTINGS-001 | Removing FEAT-WS-ADMINISTER_SETTINGS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-ADMINISTER_SETTINGS-001 | A stale update conflicts; invalid values do not increment the version or partially apply. |
| AT-WS-ADMINISTER_SETTINGS-002 | Selecting a larger UI CPU value cannot override the effective Orchestration envelope; the UI shows the stricter value and reason. |
| AT-WS-ADMINISTER_SETTINGS-003 | Changing locale changes display only; stored capability IDs, numerical values and source hashes stay unchanged. |
| ATN-WS-ADMINISTER_SETTINGS-001 | Disable and physically remove administer_settings; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/administer_settings/test_traceability.py`; `tests/services/workspace/administer_settings/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Read and update schema-validated setting revisions using expected revision; reject unknown keys and incompatible combinations. Expected: A stale update conflicts; invalid values do not increment the version or partially apply. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-ADMINISTER_SETTINGS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(workspace): complete FEAT-WS-ADMINISTER_SETTINGS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-12"></a>

### - [ ] Task 1.12 — FEAT-PLUG-REGISTER_CONTRIBUTIONS — Register and dispose exact extension contributions

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.05.

#### i. Feature and remaining work

Installed providers can add blocks, roles, panels, templates, methods or channels without static imports or leaked registrations.

**Reuse:** `app/services/plugins/contributions`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-001 | Register immutable owner-scoped contributions with exact ID/version/generation and return a disposer handle. |
| FR-TRC-PLUG-REGISTER_CONTRIBUTIONS-002 | Expose compatible contributions deterministically and withdraw them on removal/replacement. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-REGISTER_CONTRIBUTIONS-001 | Removing FEAT-PLUG-REGISTER_CONTRIBUTIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-REGISTER_CONTRIBUTIONS-001 | Duplicate/conflicting registration is rejected; disposal removes only its own generation, not all matching names. |
| AT-PLUG-REGISTER_CONTRIBUTIONS-002 | An unmounted widget/role/provider cannot reappear in a later lookup through stale global state. |
| ATN-PLUG-REGISTER_CONTRIBUTIONS-001 | Disable and physically remove register_contributions; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/register_contributions/test_traceability.py`; `tests/services/plugins/register_contributions/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register immutable owner-scoped contributions with exact ID/version/generation and return a disposer handle. Expected: Duplicate/conflicting registration is rejected; disposal removes only its own generation, not all matching names. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-REGISTER_CONTRIBUTIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-REGISTER_CONTRIBUTIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-13"></a>

### - [ ] Task 1.13 — FEAT-IFACE-OPERATE_IDENTITY — Translate identity and session operations

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U0.

**Order prerequisites:** 1.04, 1.08.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

**Reuse:** `app/services/interfaces/operate_identity`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_IDENTITY-001 | Translate authenticated account/session operations into the Workspace identity contract with current cookie/CSRF semantics. |
| FR-TRC-IFACE-OPERATE_IDENTITY-002 | Return truthful current identity and permission metadata for UI context and owner requests. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_IDENTITY-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_IDENTITY-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_IDENTITY-001 | Forgery/expiry/revocation/cross-account fixtures deny before mutation and never expose secret tokens. |
| AT-IFACE-OPERATE_IDENTITY-002 | A browser-supplied principal cannot replace the verified session principal. |
| ATN-IFACE-OPERATE_IDENTITY-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_IDENTITY-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_identity/test_traceability.py`; `tests/services/interfaces/operate_identity/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate authenticated account/session operations into the Workspace identity contract with current cookie/CSRF semantics. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Forgery/expiry/revocation/cross-account fixtures deny before mutation and never expose secret tokens. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_IDENTITY/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_IDENTITY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-14"></a>

### - [ ] Task 1.14 — FEAT-ORCH-RESERVE_RESOURCES — Admit finite work under one resource ledger

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.09, 1.11.

#### i. Feature and remaining work

Heavy work shares host capacity without starving controls, exhausting memory or bypassing parent budgets.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-RESERVE_RESOURCES-001 | Reserve a finite hierarchical resource profile for every heavy operation and reject/queue impossible requests before allocation. |
| FR-TRC-ORCH-RESERVE_RESOURCES-002 | Enforce the source workstation defaults: 70% memory envelope, 85%/95% pressure actions, reserved control CPUs, 256 ready descriptors, two prefetch chunks, 64 MiB buffers, 20% cache ceiling and one compile job. |
| FR-TRC-ORCH-RESERVE_RESOURCES-003 | Budget temporary disk as min(16 GiB,25% free) at initialization and preserve at least 10% free space; reconcile actual native/shared/device use. |
| FR-TRC-ORCH-RESERVE_RESOURCES-004 | Provide fair queues with bounded aging and reserved interactive/cancellation capacity; existing safety-critical execution keeps priority. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-RESERVE_RESOURCES-001 | Resource accounting covers native allocations, unique resident shared pages, mappings, caches, decode/output buffers and VRAM, not only Python allocations. |
| NFR-TRC-ORCH-RESERVE_RESOURCES-002 | Control latency and cancellation capacity remain reserved while bulk work is admitted. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-RESERVE_RESOURCES-001 | A child job cannot reserve its parent’s capacity again; missing or negative caps do not mean unlimited permission. |
| AT-ORCH-RESERVE_RESOURCES-002 | Mixed-load fixtures cannot exceed combined runnable-thread or memory reservations; unknown estimates carry hard caps and visible capacity outcomes. |
| AT-ORCH-RESERVE_RESOURCES-003 | A new write is denied before violating disk headroom; shared resident pages are not double-counted and Python heap alone is not treated as total memory. |
| AT-ORCH-RESERVE_RESOURCES-004 | Under BM-APP-01 bulk work cannot suppress control acknowledgement or disable risk/broker serialization checks. |
| ATN-ORCH-RESERVE_RESOURCES-001 | Larger-than-RAM and mixed-load measurements stay inside the effective global and per-operation caps. |
| ATN-ORCH-RESERVE_RESOURCES-002 | BM-APP-01 meets warm local metadata/control p95 ≤250 ms and p99 ≤1 s; over-capacity bulk work is visibly queued/refused. |


**Acceptance test targets:** `tests/services/orchestration/reserve_resources/test_traceability.py`; `tests/services/orchestration/reserve_resources/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Reserve a finite hierarchical resource profile for every heavy operation and reject/queue impossible requests before allocation. Expected: A child job cannot reserve its parent’s capacity again; missing or negative caps do not mean unlimited permission. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-RESERVE_RESOURCES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-RESERVE_RESOURCES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-15"></a>

### - [ ] Task 1.15 — FEAT-AGT-ENFORCE_MANDATE — Mandate Enforcement

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.04, 1.11.

#### i. Feature and remaining work

Validate immutable mandate identity/integrity, effective interval, objectives, enabled roles/features, environment/account/asset scope and finite budgets.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-VALIDATE_MANDATE | Validate immutable mandate identity/integrity, effective interval, objectives, enabled roles/features, environment/account/asset scope and finite budgets. |
| FR-AGT-ENFORCE_AUTHORITY_BOUNDARY | Reject any Agentic grant of broker credentials, order construction, Risk approval, kill-switch clearing, deployment or receiver authority. |
| FR-AGT-FAIL_CLOSED_ON_MANDATE | Publish unavailable/refusal when mandate validity or scope cannot be proven. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-ENFORCE_MANDATE-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-ENFORCE_MANDATE-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-ENFORCE_MANDATE-001 | Tampered, absent, future or expired mandate fails; the narrowest applicable owner/system rule wins. |
| AT-AGT-ENFORCE_MANDATE-002 | Forbidden fields are unrepresentable/rejected and no prohibited receiver is invoked. |
| AT-AGT-ENFORCE_MANDATE-003 | Missing configuration never selects a permissive default; removing mandate stops Agentic only. |
| ATN-AGT-ENFORCE_MANDATE-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-ENFORCE_MANDATE-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/enforce_mandate/test_traceability.py`; `tests/services/agentic/enforce_mandate/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate immutable mandate identity/integrity, effective interval, objectives, enabled roles/features, environment/account/asset scope and finite budgets. Expected: Tampered, absent, future or expired mandate fails; the narrowest applicable owner/system rule wins. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-ENFORCE_MANDATE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-ENFORCE_MANDATE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-16"></a>

### - [ ] Task 1.16 — FEAT-UI-17 — Present session access and scope changes

**Status:** `PARTIAL` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.02, 1.13.

#### i. Feature and remaining work

The user sees why a page or action is unavailable without browser logic becoming the permission authority.

**Reuse:** `app/ui/src/app`. The UI domain README labels Protected Routing and Access Gate Pending. Complete session/CSRF/scope-change and fail-closed UI behaviour against the actual identity gateway.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-17-001 | Load verified identity/scope before presenting protected workspace resources and clear stale projections on logout/account change. |
| FR-TRC-UI-17-002 | Represent unauthenticated, unauthorized, expired and unavailable states separately and route through the existing application framework. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-17-001 | Removing FEAT-UI-17 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-17-001 | Cross-account cached selections and requests are cleared/aborted; unauthorized content is not briefly displayed. |
| AT-UI-17-002 | A browser toggle cannot authorize a server request; no replacement SPA/authentication system is introduced. |
| ATN-UI-17-001 | Disable and physically remove app; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/app/__tests__/traceability.test.tsx`; `app/ui/src/app/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Present session access and scope changes). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Cross-account cached selections and requests are cleared/aborted; unauthorized content is not briefly displayed. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-17/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(ui): complete FEAT-UI-17`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-17"></a>

### - [ ] Task 1.17 — FEAT-WS-MANAGE_ARTIFACTS — Publish and retain immutable artifact bytes

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.09, 1.14.

#### i. Feature and remaining work

Every accepted domain reference resolves verified, authorized bytes, and failed publication never masquerades as a complete result.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-MANAGE_ARTIFACTS-001 | Stage, flush and validate byte count/schema declaration/content hash before atomic publication; issue a custody receipt. |
| FR-TRC-WS-MANAGE_ARTIFACTS-002 | Resolve authorized artifact IDs and bounded download grants; reject host paths, cross-account access and expired grants. |
| FR-TRC-WS-MANAGE_ARTIFACTS-003 | Retain referenced artifacts and legal holds; clean eligible staging/orphans through admitted maintenance with an audit receipt. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-MANAGE_ARTIFACTS-001 | Removing FEAT-WS-MANAGE_ARTIFACTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-MANAGE_ARTIFACTS-001 | A bad hash or truncated write yields no published artifact reference; retry of the same publication is idempotent. |
| AT-WS-MANAGE_ARTIFACTS-002 | Traversal/UNC/drive paths and a grant for another principal fail; valid downloads match the immutable checksum. |
| AT-WS-MANAGE_ARTIFACTS-003 | Deleting a databank membership leaves its referenced strategy/result bytes intact; expired unreferenced staging is removed and recorded. |
| ATN-WS-MANAGE_ARTIFACTS-001 | Disable and physically remove manage_artifacts; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/manage_artifacts/test_traceability.py`; `tests/services/workspace/manage_artifacts/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Stage, flush and validate byte count/schema declaration/content hash before atomic publication; issue a custody receipt. Expected: A bad hash or truncated write yields no published artifact reference; retry of the same publication is idempotent. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-MANAGE_ARTIFACTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(workspace): complete FEAT-WS-MANAGE_ARTIFACTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-18"></a>

### - [ ] Task 1.18 — FEAT-ORCH-MANAGE_JOBS — Persist and control shared jobs and attempts

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.09, 1.14.

#### i. Feature and remaining work

Accepted work survives browser closure and process restart with one authoritative lifecycle and explainable attempts.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-MANAGE_JOBS-001 | Persist accepted immutable job/input identity and enqueue intent atomically before reporting acceptance. |
| FR-TRC-ORCH-MANAGE_JOBS-002 | Apply expected-version lifecycle transitions and provider-declared checkpoint pause/resume; terminal retry creates a linked new attempt/run. |
| FR-TRC-ORCH-MANAGE_JOBS-003 | Record domain outcome separately from worker status, including Agentic REFUSED over successful worker completion and human waits without held worker slots. |
| FR-TRC-ORCH-MANAGE_JOBS-004 | Reconcile uncertain receiver effects by original idempotency key before retry and bound nesting/ancestry. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-MANAGE_JOBS-001 | Removing FEAT-ORCH-MANAGE_JOBS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-MANAGE_JOBS-001 | A crash after the response but before dispatch still leaves one resolvable job; replaying the same logical request does not enqueue another. |
| AT-ORCH-MANAGE_JOBS-002 | Completion-versus-stop races yield one terminal result; unsupported pause is rejected rather than inferred from silence. |
| AT-ORCH-MANAGE_JOBS-003 | UI inspection can distinguish successful refusal from successful research; an expired wait does not fabricate an active worker. |
| AT-ORCH-MANAGE_JOBS-004 | Crash after receiver commit produces one accepted logical effect; recursive ancestor submission is denied. |
| ATN-ORCH-MANAGE_JOBS-001 | Disable and physically remove manage_jobs; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/manage_jobs/test_traceability.py`; `tests/services/orchestration/manage_jobs/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Persist accepted immutable job/input identity and enqueue intent atomically before reporting acceptance. Expected: A crash after the response but before dispatch still leaves one resolvable job; replaying the same logical request does not enqueue another. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-MANAGE_JOBS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-MANAGE_JOBS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-19"></a>

### - [ ] Task 1.19 — FEAT-AGT-OPERATE_RUNS — Operations, Incidents and Replay Validation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.09, 1.15.

#### i. Feature and remaining work

Append correlated redacted role/model/tool/lease/handoff/policy/state/cost/refusal/failure/cleanup records.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-RECORD_OPERATIONS | Append correlated redacted role/model/tool/lease/handoff/policy/state/cost/refusal/failure/cleanup records. |
| FR-AGT-CONTAIN_INCIDENTS | Classify incidents and publish durable containment/readiness decisions for owning consumers to revoke/cancel/quarantine. |
| FR-AGT-VALIDATE_REPLAY | Validate exact references, versions, generations and side-effect prohibition for historical replay eligibility. |
| FR-AGT-PUBLISH_AGENTIC_READINESS | Expose feature-level readiness/degradation and containment reasons without private provider internals. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-OPERATE_RUNS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-OPERATE_RUNS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-OPERATE_RUNS-001 | Secrets/unrestricted private text are redacted before persistence; bounded export preserves sequence and immutable artifact references. |
| AT-AGT-OPERATE_RUNS-002 | Kill the event consumer between decision and acknowledgement: restart cannot lose containment or reauthorize revoked work. |
| AT-AGT-OPERATE_RUNS-003 | Tampered/missing/drifted references fail; replay validation invokes no external side effect. |
| AT-AGT-OPERATE_RUNS-004 | A missed event cannot bypass the mandatory current readiness check before invocation. |
| ATN-AGT-OPERATE_RUNS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-OPERATE_RUNS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/operate_runs/test_traceability.py`; `tests/services/agentic/operate_runs/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Append correlated redacted role/model/tool/lease/handoff/policy/state/cost/refusal/failure/cleanup records. Expected: Secrets/unrestricted private text are redacted before persistence; bounded export preserves sequence and immutable artifact references. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-OPERATE_RUNS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-OPERATE_RUNS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-20"></a>

### - [ ] Task 1.20 — FEAT-AGT-REGISTER_ROLES — Role Contribution Registry

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.12, 1.15.

#### i. Feature and remaining work

Register immutable role/version, prompt, schemas, tools, model policy, limits, conflicts, refusals and evaluation references.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-REGISTER_ROLE_CONTRIBUTIONS | Register immutable role/version, prompt, schemas, tools, model policy, limits, conflicts, refusals and evaluation references. |
| FR-AGT-VERIFY_ROLE_ARTIFACTS | Normalize prompt encoding/line endings and recompute manifest/prompt/composite hashes; reject floating model identity and undeclared tools. |
| FR-AGT-RESOLVE_ELIGIBLE_ROLES | Resolve only enabled, permitted, in-scope, nonconflicted roles with current independent eligibility. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-REGISTER_ROLES-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-REGISTER_ROLES-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-REGISTER_ROLES-001 | Duplicate identity/version or unknown fields fail; registration returns one exact disposer handle. |
| AT-AGT-REGISTER_ROLES-002 | Tamper fails before model construction; role title grants no authority. |
| AT-AGT-REGISTER_ROLES-003 | Expired/revoked/missing eligibility or wrong-account scope denies invocation; evaluation-only is not user research. |
| ATN-AGT-REGISTER_ROLES-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-REGISTER_ROLES-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/register_roles/test_traceability.py`; `tests/services/agentic/register_roles/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register immutable role/version, prompt, schemas, tools, model policy, limits, conflicts, refusals and evaluation references. Expected: Duplicate identity/version or unknown fields fail; registration returns one exact disposer handle. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-REGISTER_ROLES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-REGISTER_ROLES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-21"></a>

### - [ ] Task 1.21 — FEAT-WS-BUILD_DIAGNOSTICS — Explain runtime health and export safe diagnostics

**Status:** `PARTIAL` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.04, 1.17, 1.18.

#### i. Feature and remaining work

An operator can diagnose unavailable capabilities, resource contention and failures without receiving private payloads or credentials.

**Reuse:** `app/services/workspace/diagnostic_bundle`. Reuse diagnostic_bundle. The inspected entry-point group omits this provider; add the register-required matched benchmark indexing, process/native memory and bounded job/resource projections without a second diagnostic owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-BUILD_DIAGNOSTICS-001 | Assemble scoped capability, build, runtime, trace and failure metadata with explicit unknown/unavailable states. |
| FR-TRC-WS-BUILD_DIAGNOSTICS-002 | Export bounded redacted diagnostics with stage timing, queue delay and native/process-group memory references. |
| FR-TRC-WS-BUILD_DIAGNOSTICS-003 | Index versioned benchmark reports and compare only matched fixture/runtime/resource identities; expose targets separately from measurements. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-BUILD_DIAGNOSTICS-001 | Removing FEAT-WS-BUILD_DIAGNOSTICS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-BUILD_DIAGNOSTICS-001 | A removed provider yields its owner’s readiness reason, not an invented healthy status. |
| AT-WS-BUILD_DIAGNOSTICS-002 | Secret-bearing provider messages are redacted before persistence/export; byte and record limits hold under a flood. |
| AT-WS-BUILD_DIAGNOSTICS-003 | An unmeasured target remains PENDING; a mismatched hardware or tick-method report cannot produce a parity/pass badge. |
| ATN-WS-BUILD_DIAGNOSTICS-001 | Disable and physically remove build_diagnostics; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/build_diagnostics/test_traceability.py`; `tests/services/workspace/build_diagnostics/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Assemble scoped capability, build, runtime, trace and failure metadata with explicit unknown/unavailable states. Expected: A removed provider yields its owner’s readiness reason, not an invented healthy status. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-BUILD_DIAGNOSTICS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(workspace): complete FEAT-WS-BUILD_DIAGNOSTICS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-22"></a>

### - [ ] Task 1.22 — FEAT-ORCH-EXECUTE_LOCAL_WORK — Execute isolated spawn-safe local work units

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.17, 1.18.

#### i. Feature and remaining work

Native simulations, builds and training run in bounded workers while the application remains responsive.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-EXECUTE_LOCAL_WORK-001 | Dispatch small immutable work descriptors with pinned inputs/provider/runtime/seed/output schema and share read-only handles instead of pickling full histories. |
| FR-TRC-ORCH-EXECUTE_LOCAL_WORK-002 | Poll control between bounded native slices and fence completion after effective cancellation or lease revocation. |
| FR-TRC-ORCH-EXECUTE_LOCAL_WORK-003 | Dispose mappings/handles before deletion and recycle workers under declared native-code/cache memory limits. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-EXECUTE_LOCAL_WORK-001 | Removing FEAT-ORCH-EXECUTE_LOCAL_WORK withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-EXECUTE_LOCAL_WORK-001 | Windows spawn fixtures perform no import-time work; every worker verifies hashes and compatible generations before execution. |
| AT-ORCH-EXECUTE_LOCAL_WORK-002 | Core local numerical cancellation reaches quiescence p95 ≤2 s; late results are not accepted. |
| AT-ORCH-EXECUTE_LOCAL_WORK-003 | Repeated activation/removal and worker failures return handles/reservations to baseline without losing accepted output receipts. |
| ATN-ORCH-EXECUTE_LOCAL_WORK-001 | Disable and physically remove execute_local_work; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/execute_local_work/test_traceability.py`; `tests/services/orchestration/execute_local_work/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Dispatch small immutable work descriptors with pinned inputs/provider/runtime/seed/output schema and share read-only handles instead of pickling full histories. Expected: Windows spawn fixtures perform no import-time work; every worker verifies hashes and compatible generations before execution. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-EXECUTE_LOCAL_WORK/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-EXECUTE_LOCAL_WORK`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-23"></a>

### - [ ] Task 1.23 — FEAT-AGT-GOVERN_TOOL_CALLS — Tool Governance and Human Actions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.04, 1.09, 1.14, 1.15, 1.19, 1.20.

#### i. Feature and remaining work

Register declared receiver capability/schema/permission/side-effect/environment/idempotency/cost/timeout/result-trust descriptors.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-REGISTER_AGENTIC_TOOLS | Register declared receiver capability/schema/permission/side-effect/environment/idempotency/cost/timeout/result-trust descriptors. |
| FR-AGT-ISSUE_CAPABILITY_LEASES | Issue immutable invocation-bound leases with principal/role/run/request hash/receiver generation/scope/egress/ceiling/expiry/nonce/policy/action identity. |
| FR-AGT-ENFORCE_TOOL_INVOCATIONS | Reauthorize immediately before every invocation, retry and resume and reconcile uncertain owner effects by the original idempotency key. |
| FR-AGT-FILTER_TOOL_RESULTS | Validate and bound schema, scope, provenance, redaction, injection classification and observed cost before model exposure. |
| FR-AGT-BIND_TYPED_HUMAN_ACTIONS | Bind clarification, scope, tool/compute/holdout/staging/handoff approval, rejection and cancellation to exact expiring objects. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-GOVERN_TOOL_CALLS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-GOVERN_TOOL_CALLS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-GOVERN_TOOL_CALLS-001 | Broker/order/approval/unrestricted shell/deployment tools are structurally unregistrable. |
| AT-AGT-GOVERN_TOOL_CALLS-002 | Forgery, replay, mutation, wrong scope and budget exhaustion deny authorization. |
| AT-AGT-GOVERN_TOOL_CALLS-003 | A denied call never reaches the receiver; a crash after receiver commit does not duplicate the logical effect. |
| AT-AGT-GOVERN_TOOL_CALLS-004 | Wrong-account, secret-bearing, oversized or malformed results never enter trusted context. |
| AT-AGT-GOVERN_TOOL_CALLS-005 | Changing the candidate or action invalidates approval; a used nonce cannot approve another request. |
| ATN-AGT-GOVERN_TOOL_CALLS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-GOVERN_TOOL_CALLS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/govern_tool_calls/test_traceability.py`; `tests/services/agentic/govern_tool_calls/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register declared receiver capability/schema/permission/side-effect/environment/idempotency/cost/timeout/result-trust descriptors. Expected: Broker/order/approval/unrestricted shell/deployment tools are structurally unregistrable. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-GOVERN_TOOL_CALLS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-GOVERN_TOOL_CALLS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-24"></a>

### - [ ] Task 1.24 — FEAT-AGT-INVOKE_MODELS — Provider-Neutral Model Invocation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.12, 1.14, 1.15, 1.19, 1.20.

#### i. Feature and remaining work

Pin provider/model/profile/role/prompt/composite/schema/context/tools/privacy/region/retention before a structured call.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-PIN_MODEL_INVOCATIONS | Pin provider/model/profile/role/prompt/composite/schema/context/tools/privacy/region/retention before a structured call. |
| FR-AGT-ENFORCE_MODEL_BUDGETS | Enforce input/output tokens, time, retries and finite cost before and after each call and reconcile missing usage conservatively. |
| FR-AGT-REFUSE_SILENT_MODEL_SUBSTITUTION | Allow fallback only to explicitly declared independently eligible profiles for the same task/risk scope. |
| FR-AGT-CONTAIN_MODEL_OUTPUT | Parse only the strict declared output union and map malformed/truncated/unsafe content to typed refusal/failure. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-INVOKE_MODELS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-INVOKE_MODELS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-INVOKE_MODELS-001 | The returned provider/model identity must match the selected eligible profile; private SDK objects never cross the boundary. |
| AT-AGT-INVOKE_MODELS-002 | Overrun/nonfinite/missing usage cannot be reported as zero cost or enlarge the caller’s ceiling. |
| AT-AGT-INVOKE_MODELS-003 | A floating alias, changed provider or unevaluated fallback fails closed. |
| AT-AGT-INVOKE_MODELS-004 | Extraneous fields, provider objects and hidden reasoning are excluded from canonical output. |
| ATN-AGT-INVOKE_MODELS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-INVOKE_MODELS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/invoke_models/test_traceability.py`; `tests/services/agentic/invoke_models/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Pin provider/model/profile/role/prompt/composite/schema/context/tools/privacy/region/retention before a structured call. Expected: The returned provider/model identity must match the selected eligible profile; private SDK objects never cross the boundary. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-INVOKE_MODELS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-INVOKE_MODELS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-25"></a>

### - [ ] Task 1.25 — FEAT-IFACE-OPERATE_SETTINGS — Translate system settings and diagnostics

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.08, 1.11, 1.21.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

**Reuse:** `app/services/interfaces/operate_settings`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_SETTINGS-001 | Translate versioned settings queries/updates using expected revision and owner validation. |
| FR-TRC-IFACE-OPERATE_SETTINGS-002 | Expose secret-reference slots and bounded diagnostics, never credential values or unrestricted host paths. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_SETTINGS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_SETTINGS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_SETTINGS-001 | Unknown keys/conflicts/narrower effective policy survive mapping unchanged. |
| AT-IFACE-OPERATE_SETTINGS-002 | Wire fixtures redact secrets and require exact scope for exports/test sends. |
| ATN-IFACE-OPERATE_SETTINGS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_SETTINGS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_settings/test_traceability.py`; `tests/services/interfaces/operate_settings/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate versioned settings queries/updates using expected revision and owner validation. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Unknown keys/conflicts/narrower effective policy survive mapping unchanged. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_SETTINGS/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-ORCH-DELIVER_NOTIFICATIONS (Task 11.04, Phase 11). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_SETTINGS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-26"></a>

### - [ ] Task 1.26 — FEAT-IFACE-OPERATE_JOBS — Expose shared jobs and worker control

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.08, 1.14, 1.18, 1.22.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_JOBS-001 | Expose authenticated job/resource/worker projections and supported owner control commands. |
| FR-TRC-IFACE-OPERATE_JOBS-002 | Translate versioned worker registration/lease/heartbeat/completion/status over HTTP and SSE/snapshots. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_JOBS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_JOBS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_JOBS-001 | Unsupported pause, wrong scope and quarantine release without authority fail closed. |
| AT-IFACE-OPERATE_JOBS-002 | Browser-to-worker channels and duplicate independent WebSocket job truth are absent; fencing fields are preserved. |
| ATN-IFACE-OPERATE_JOBS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_JOBS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_jobs/test_traceability.py`; `tests/services/interfaces/operate_jobs/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Expose authenticated job/resource/worker projections and supported owner control commands. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Unsupported pause, wrong scope and quarantine release without authority fail closed. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_JOBS/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-ORCH-MANAGE_REMOTE_WORKERS (Task 15.01, Phase 15). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_JOBS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-27"></a>

### - [ ] Task 1.27 — FEAT-UI-16 — Navigate capabilities and explain workspace controls

**Status:** `PARTIAL` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01, 1.02, 1.25, 1.26.

#### i. Feature and remaining work

The user finds available tools, recent resources, help and health without entering a dead or misleading screen.

**Reuse:** `app/ui/src/components/layout`. The UI domain README labels the Application Shell and Navigation Pending. Complete manifest-driven discovery and gating, contextual help, job/settings integration and keyboard/removal evidence.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-16-001 | Present compact research navigation, global job indicators, recent items and commands from actual registered capability/widget metadata. |
| FR-TRC-UI-16-002 | Provide contextual control help, readiness checklist, original examples and links to authorized reports/settings. |
| FR-TRC-UI-16-003 | Preserve keyboard navigation, selected workspace/account orientation and safe focus after panel changes. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-16-001 | Removing FEAT-UI-16 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-16-001 | Missing providers disable only affected actions with a reason; no menu item is declared operational from documentation alone. |
| AT-UI-16-002 | Help describes declared semantics and never invents a live value or qualification state. |
| AT-UI-16-003 | Keyboard-only flows reach every available command and restore focus to a valid visible control. |
| ATN-UI-16-001 | Disable and physically remove layout; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/components/layout/__tests__/traceability.test.tsx`; `app/ui/src/components/layout/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Navigate capabilities and explain workspace controls). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Missing providers disable only affected actions with a reason; no menu item is declared operational from documentation alone. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-16/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(ui): complete FEAT-UI-16`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-28"></a>

### - [ ] Task 1.28 — FEAT-UI-13 — Review effective settings and safe configuration changes

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01, 1.02, 1.25.

#### i. Feature and remaining work

The user edits settings with typed validation, explicit defaults, impacts and secret-reference controls.

**Reuse:** `app/ui/src/widgets/system-settings`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-13-001 | Render all CAT-SETTINGS categories, effective defaults/overrides, narrower policy, supported values and restart/remount impact. |
| FR-TRC-UI-13-002 | Support load/save/reset/diff/presets with dirty-state protection and field/summary owner errors. |
| FR-TRC-UI-13-003 | Render SMTP test and remote/MCP status through permission-gated typed actions with no credential values. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-13-001 | Removing FEAT-UI-13 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-13-001 | A CPU/memory/tick setting cannot silently change historical runs or override a stricter owner policy. |
| AT-UI-13-002 | A failed update leaves the prior configuration intact; stale expected revisions require explicit conflict handling. |
| AT-UI-13-003 | Test send names recipient/scope and has its own action; an unconfigured service remains unavailable. |
| ATN-UI-13-001 | Disable and physically remove system-settings; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/widgets/system-settings/__tests__/traceability.test.tsx`; `app/ui/src/widgets/system-settings/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Review effective settings and safe configuration changes). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A CPU/memory/tick setting cannot silently change historical runs or override a stricter owner policy. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-13/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-13`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-29"></a>

### - [ ] Task 1.29 — FEAT-UI-RUN_MONITOR — Inspect and control jobs and workers

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01, 1.02, 1.06, 1.18, 1.26.

#### i. Feature and remaining work

Understand what is queued, working, waiting, cancelled or complete and which controls the owner supports.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-RUN_MONITOR-001 | Render unknown totals distinctly, domain outcome separately from infrastructure status and desired control separately from acknowledgement. |
| FR-TRC-UI-RUN_MONITOR-002 | Issue only permission-gated supported controls and follow actual terminal/result receipts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-RUN_MONITOR-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-RUN_MONITOR-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-RUN_MONITOR-001 | A correctly produced refusal is not a successful research badge; waiting for a person holds no fabricated worker slot. |
| AT-UI-RUN_MONITOR-002 | Unsupported pause and stale control revisions fail visibly; a late fenced result is not shown as accepted. |
| ATN-UI-RUN_MONITOR-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-RUN_MONITOR-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/run-monitor/__tests__/traceability.test.tsx`; `app/ui/src/widgets/run-monitor/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect and control jobs and workers). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A correctly produced refusal is not a successful research badge; waiting for a person holds no fabricated worker slot. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-RUN_MONITOR/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-RUN_MONITOR`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-1-30"></a>

### - [ ] Task 1.30 — FEAT-UI-DEBUG_CONSOLE — Inspect bounded redacted diagnostic logs

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01, 1.02, 1.25.

#### i. Feature and remaining work

Trace a failure with correlations and owner evidence without exposing sensitive content.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-DEBUG_CONSOLE-001 | Display paged/redacted structured logs with exact timestamps/identity and explicit truncated-window indicators. |
| FR-TRC-UI-DEBUG_CONSOLE-002 | Show developer diagnostics only under the declared permission/enablement policy and dispose subscriptions on close. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-DEBUG_CONSOLE-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-DEBUG_CONSOLE-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-DEBUG_CONSOLE-001 | Clear display does not delete retained audit; attacker-controlled log text cannot execute markup. |
| AT-UI-DEBUG_CONSOLE-002 | A disabled/unauthorized console receives no sensitive payload and leaves no observer behind. |
| ATN-UI-DEBUG_CONSOLE-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-DEBUG_CONSOLE-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/debug-console/__tests__/traceability.test.tsx`; `app/ui/src/widgets/debug-console/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect bounded redacted diagnostic logs). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Clear display does not delete retained audit; attacker-controlled log text cannot execute markup. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-DEBUG_CONSOLE/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P01 — Open a real workspace, sign in, change a setting, submit a bounded demonstration job, observe and cancel it in the Jobs widget, then reopen the layout. Publish `docs/dev/evidence/phases/phase-01.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-DEBUG_CONSOLE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-2"></a>

## Phase 2 — Data Manager end to end

**Feature tasks: 32.** Catalogue + configured broker/data channels → immutable Data storage/ingestion/quality/retention → existing reference gateway → Data Manager and market chart. Profile/scenario/news data providers are prepared here; their later consumers remain separately gated.

**Visible completion:** Import a small authorized CSV or pinned provider fixture, inspect counts and chart data, diagnose a gap, apply a non-destructive repair, export the selected version, and reopen the same version after restart.

**Phase evidence:** `tests/ui/e2e/research/phase_02.spec.ts` and `docs/dev/evidence/phases/phase-02.json`, owned by Task 2.32. All prior affected UI/data/recovery regressions remain required.

<a id="task-2-01"></a>

### - [ ] Task 2.01 — FEAT-CAT-CATALOG_INSTRUMENTS — Version instrument identities and tradable units

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U1.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

A strategy or dataset resolves an unambiguous instrument and legal price/quantity units.

**Reuse:** `app/services/catalogue/instrument_catalogue`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-CATALOG_INSTRUMENTS-001 | Create/clone/edit/search/page instruments and preview mass edits and referenced-object deletion impact. |
| FR-TRC-CAT-CATALOG_INSTRUMENTS-002 | Publish point value, tick/pip size/step, quantity multiplier/step and finite units with explicit revisions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-CATALOG_INSTRUMENTS-001 | Removing FEAT-CAT-CATALOG_INSTRUMENTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-CATALOG_INSTRUMENTS-001 | A mass edit identifies exact affected IDs; referenced historical revisions remain readable after a new version is published. |
| AT-CAT-CATALOG_INSTRUMENTS-002 | Zero/negative step or incompatible unit inputs fail; a run continues using its original instrument revision. |
| ATN-CAT-CATALOG_INSTRUMENTS-001 | Disable and physically remove instrument_catalogue; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/instrument_catalogue/test_traceability.py`; `tests/services/catalogue/instrument_catalogue/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/clone/edit/search/page instruments and preview mass edits and referenced-object deletion impact. Expected: A mass edit identifies exact affected IDs; referenced historical revisions remain readable after a new version is published. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-CATALOG_INSTRUMENTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-CATALOG_INSTRUMENTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-02"></a>

### - [ ] Task 2.02 — FEAT-CAT-DEFINE_SESSIONS — Define market sessions and calendar availability

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U1.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

Bars, labels, fills and charts share a pinned session/calendar interpretation including DST and holidays.

**Reuse:** `app/services/catalogue/session_calendar`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-DEFINE_SESSIONS-001 | Create/clone/edit ordered day/time session elements, SEOC flags and weekday templates in a named timezone/calendar version. |
| FR-TRC-CAT-DEFINE_SESSIONS-002 | Resolve market boundaries across DST, holidays, gaps and half-open intervals without inventing a tradable quote. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-DEFINE_SESSIONS-001 | Removing FEAT-CAT-DEFINE_SESSIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-DEFINE_SESSIONS-001 | Overlapping/invalid intervals are rejected; a weekday shortcut expands to the exact stored ordered elements. |
| AT-CAT-DEFINE_SESSIONS-002 | Boundary fixtures classify an event at the close in the next interval; missing market observations remain missing. |
| ATN-CAT-DEFINE_SESSIONS-001 | Disable and physically remove session_calendar; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/session_calendar/test_traceability.py`; `tests/services/catalogue/session_calendar/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/clone/edit ordered day/time session elements, SEOC flags and weekday templates in a named timezone/calendar version. Expected: Overlapping/invalid intervals are rejected; a weekday shortcut expands to the exact stored ordered elements. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-DEFINE_SESSIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-DEFINE_SESSIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-03"></a>

### - [ ] Task 2.03 — FEAT-BRK-METATRADER — Connect the MetaTrader 5 data channel

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected MetaTrader 5 adapter, with explicit availability and failure results.

**Reuse:** `app/services/brokers/metatrader`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-METATRADER-001 | Validate the MetaTrader 5 provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-METATRADER-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-METATRADER-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-METATRADER-001 | Removing FEAT-BRK-METATRADER withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-METATRADER-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-METATRADER-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-METATRADER-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-METATRADER-001 | Disable and physically remove metatrader; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/metatrader/test_traceability.py`; `tests/services/brokers/metatrader/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the MetaTrader 5 provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-METATRADER/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-METATRADER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-04"></a>

### - [ ] Task 2.04 — FEAT-BRK-CTRADER — Connect the cTrader data channel

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected cTrader adapter, with explicit availability and failure results.

**Reuse:** `app/services/brokers/ctrader`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-CTRADER-001 | Validate the cTrader provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-CTRADER-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-CTRADER-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-CTRADER-001 | Removing FEAT-BRK-CTRADER withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-CTRADER-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-CTRADER-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-CTRADER-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-CTRADER-001 | Disable and physically remove ctrader; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/ctrader/test_traceability.py`; `tests/services/brokers/ctrader/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the cTrader provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-CTRADER/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-CTRADER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-05"></a>

### - [ ] Task 2.05 — FEAT-BRK-BINANCE — Connect the Binance data channel

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Binance adapter, with explicit availability and failure results.

**Reuse:** `app/services/brokers/binance`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-BINANCE-001 | Validate the Binance provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-BINANCE-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-BINANCE-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-BINANCE-001 | Removing FEAT-BRK-BINANCE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-BINANCE-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-BINANCE-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-BINANCE-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-BINANCE-001 | Disable and physically remove binance; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/binance/test_traceability.py`; `tests/services/brokers/binance/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Binance provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-BINANCE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-BINANCE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-06"></a>

### - [ ] Task 2.06 — FEAT-BRK-DUKASCOPY — Connect the Dukascopy data channel

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Dukascopy adapter, with explicit availability and failure results.

**Reuse:** `app/services/brokers/dukascopy`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-DUKASCOPY-001 | Validate the Dukascopy provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-DUKASCOPY-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-DUKASCOPY-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-DUKASCOPY-001 | Removing FEAT-BRK-DUKASCOPY withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-DUKASCOPY-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-DUKASCOPY-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-DUKASCOPY-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-DUKASCOPY-001 | Disable and physically remove dukascopy; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/dukascopy/test_traceability.py`; `tests/services/brokers/dukascopy/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Dukascopy provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-DUKASCOPY/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-DUKASCOPY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-07"></a>

### - [ ] Task 2.07 — FEAT-BRK-YAHOO — Connect the Yahoo data channel

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Yahoo adapter, with explicit availability and failure results.

**Reuse:** `app/services/brokers/yahoo`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-YAHOO-001 | Validate the Yahoo provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-YAHOO-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-YAHOO-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-YAHOO-001 | Removing FEAT-BRK-YAHOO withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-YAHOO-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-YAHOO-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-YAHOO-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-YAHOO-001 | Disable and physically remove yahoo; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/yahoo/test_traceability.py`; `tests/services/brokers/yahoo/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Yahoo provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-YAHOO/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-YAHOO`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-08"></a>

### - [ ] Task 2.08 — FEAT-BRK-RESOLVE — Resolve an explicitly selected broker/data provider

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U1.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

A client gets a compatible configured provider or a truthful unavailable result without hidden cross-provider substitution.

**Reuse:** `app/services/brokers/resolve`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-RESOLVE-001 | Resolve an explicit configured provider against its public supported-operation and current readiness declarations. |
| FR-TRC-BRK-RESOLVE-002 | Preserve selected provider identity/generation across a request and fail closed on loss or incompatibility. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-RESOLVE-001 | Removing FEAT-BRK-RESOLVE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-RESOLVE-001 | Multiple compatible providers without explicit selection do not lead to nondeterministic choice. |
| AT-BRK-RESOLVE-002 | Remove the selected provider before dispatch: no other provider receives the request and no synthetic response is returned. |
| ATN-BRK-RESOLVE-001 | Disable and physically remove resolve; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/resolve/test_traceability.py`; `tests/services/brokers/resolve/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve an explicit configured provider against its public supported-operation and current readiness declarations. Expected: Multiple compatible providers without explicit selection do not lead to nondeterministic choice. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-RESOLVE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-RESOLVE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-09"></a>

### - [ ] Task 2.09 — FEAT-DATA-MARKET_DATA_STORE — Append and query immutable partitioned market data

**Status:** `PARTIAL` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.14, 1.17.

#### i. Feature and remaining work

Twenty years of history can grow by appending new parts while bounded readers retrieve only the requested columns and time range.

**Reuse:** `app/services/data/market_data_store`. Current manifest advertises a DuckDB ingestion manifest and publishes both MARKET_DATA_STORE_CAPABILITY and BROWSE_REFERENCE_CAPABILITY with no required/optional dependencies. Reconcile SQLite metadata authority, the separate Browse Reference owner, artifact custody and resource admission; preserve useful Parquet/ZSTD paths. The current CI also reports lint findings in mt4_exporter.py and reference_repository.py.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-MARKET_DATA_STORE-001 | Write closed Parquet parts using the initial Zstandard level 3 and approximately 128 MiB uncompressed row-group profile, bounded by admission. |
| FR-TRC-DATA-MARKET_DATA_STORE-002 | Project columns and prune by symbol/time/row-group statistics into bounded decode buffers. |
| FR-TRC-DATA-MARKET_DATA_STORE-003 | Compact or correct through new manifests and atomic publication, preserving active readers of old versions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-MARKET_DATA_STORE-001 | Removing FEAT-DATA-MARKET_DATA_STORE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-MARKET_DATA_STORE-001 | Appending a new period leaves all prior part hashes unchanged; no file-per-row/tick write path exists. |
| AT-DATA-MARKET_DATA_STORE-002 | A one-symbol interval query does not materialize all symbols/years; data larger than RAM completes within its reservation. |
| AT-DATA-MARKET_DATA_STORE-003 | Interrupt compaction: old readers remain valid; successful publication has complete count/hash reconciliation. |
| ATN-DATA-MARKET_DATA_STORE-001 | Disable and physically remove market_data_store; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/market_data_store/test_traceability.py`; `tests/services/data/market_data_store/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Write closed Parquet parts using the initial Zstandard level 3 and approximately 128 MiB uncompressed row-group profile, bounded by admission. Expected: Appending a new period leaves all prior part hashes unchanged; no file-per-row/tick write path exists. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-MARKET_DATA_STORE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(data): complete FEAT-DATA-MARKET_DATA_STORE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-10"></a>

### - [ ] Task 2.10 — FEAT-CAT-MAP_PROVIDERS — Resolve provider symbols and broker profiles

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.01.

#### i. Feature and remaining work

A data or execution request reaches the configured provider symbol without silent rewriting or historical profile drift.

**Reuse:** `app/services/catalogue/provider_mapping`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-MAP_PROVIDERS-001 | Version exact provider symbols, postfix/mapping rules, timezone and customized instrument/session associations. |
| FR-TRC-CAT-MAP_PROVIDERS-002 | Clone/import/export supported profiles and protect system profiles and incompatible timezone changes. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-MAP_PROVIDERS-001 | Removing FEAT-CAT-MAP_PROVIDERS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-MAP_PROVIDERS-001 | The selected provider_symbol is passed unchanged to the adapter; a profile edit creates a new version. |
| AT-CAT-MAP_PROVIDERS-002 | Deleting a protected profile fails; changing timezone while referenced data exists yields an impact report rather than relabeling old observations. |
| ATN-CAT-MAP_PROVIDERS-001 | Disable and physically remove provider_mapping; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/provider_mapping/test_traceability.py`; `tests/services/catalogue/provider_mapping/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version exact provider symbols, postfix/mapping rules, timezone and customized instrument/session associations. Expected: The selected provider_symbol is passed unchanged to the adapter; a profile edit creates a new version. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-MAP_PROVIDERS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-MAP_PROVIDERS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-11"></a>

### - [ ] Task 2.11 — FEAT-CAT-DEFINE_TRADING_RULES — Version trading costs and venue constraints

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.01, 2.02.

#### i. Feature and remaining work

A run can reproduce fees, swap, spread assumptions and size/price restrictions from the historical profile it accepted.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-DEFINE_TRADING_RULES-001 | Publish typed commission, swap, spread/slippage, minimum-distance, lot/size and netting/hedging profile descriptors with revision and units. |
| FR-TRC-CAT-DEFINE_TRADING_RULES-002 | Resolve effective overrides with explicit precedence and report incompatible instrument/session combinations. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-DEFINE_TRADING_RULES-001 | Removing FEAT-CAT-DEFINE_TRADING_RULES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-DEFINE_TRADING_RULES-001 | Mixed/unknown units or invalid bounds fail validation; current profile changes do not alter a pinned run. |
| AT-CAT-DEFINE_TRADING_RULES-002 | A Retester override is recorded on its run and leaves the source Strategy/profile hashes unchanged. |
| ATN-CAT-DEFINE_TRADING_RULES-001 | Disable and physically remove define_trading_rules; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/define_trading_rules/test_traceability.py`; `tests/services/catalogue/define_trading_rules/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Publish typed commission, swap, spread/slippage, minimum-distance, lot/size and netting/hedging profile descriptors with revision and units. Expected: Mixed/unknown units or invalid bounds fail validation; current profile changes do not alter a pinned run. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-DEFINE_TRADING_RULES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-DEFINE_TRADING_RULES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-12"></a>

### - [ ] Task 2.12 — FEAT-CAT-CONVERT_CURRENCIES — Resolve causal currency conversion paths

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.01.

#### i. Feature and remaining work

Costs, equity and portfolios are expressed in the intended currency using a reproducible conversion path.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-CONVERT_CURRENCIES-001 | Resolve currency paths using only rates available by the pinned observation cutoff and expose rate/path provenance. |
| FR-TRC-CAT-CONVERT_CURRENCIES-002 | Apply declared scale, rounding and intermediate-range policies to conversions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-CONVERT_CURRENCIES-001 | Removing FEAT-CAT-CONVERT_CURRENCIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-CONVERT_CURRENCIES-001 | A future quote cannot complete a historical path; missing or stale paths return typed unavailability. |
| AT-CAT-CONVERT_CURRENCIES-002 | Boundary and large-notional fixtures agree with the exact Decimal oracle; overflow fails rather than wrapping or switching to float. |
| ATN-CAT-CONVERT_CURRENCIES-001 | Disable and physically remove convert_currencies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/convert_currencies/test_traceability.py`; `tests/services/catalogue/convert_currencies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve currency paths using only rates available by the pinned observation cutoff and expose rate/path provenance. Expected: A future quote cannot complete a historical path; missing or stale paths return typed unavailability. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-CONVERT_CURRENCIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-CONVERT_CURRENCIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-13"></a>

### - [ ] Task 2.13 — FEAT-DATA-RESOLVE_QUALITY — Inspect and repair data through new versions

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.02, 2.09.

#### i. Feature and remaining work

A user can explain and resolve data defects without rewriting the observations used by an earlier experiment.

**Reuse:** `app/services/data/data_quality_resolution`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-RESOLVE_QUALITY-001 | Detect gaps, duplicates, ordering faults, spikes, nonfinite/negative/zero-volume concerns, invalid OHLC and out-of-session observations under versioned thresholds. |
| FR-TRC-DATA-RESOLVE_QUALITY-002 | Preview and accept/reject findings or create a derived repaired version with exact source-to-output lineage. |
| FR-TRC-DATA-RESOLVE_QUALITY-003 | Page findings and timeline summaries with bounded diagnostics and explicit partial analysis. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-RESOLVE_QUALITY-001 | Removing FEAT-DATA-RESOLVE_QUALITY withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-RESOLVE_QUALITY-001 | Boundary fixtures produce stable rule IDs, observation IDs and severity; zero volume is flagged by its feed policy, not universally fabricated or dropped. |
| AT-DATA-RESOLVE_QUALITY-002 | Repair preserves the original hash and records each transformed observation; concurrent stale decisions conflict. |
| AT-DATA-RESOLVE_QUALITY-003 | A million findings never become one browser payload; incomplete scans cannot claim a clean dataset. |
| ATN-DATA-RESOLVE_QUALITY-001 | Disable and physically remove data_quality_resolution; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/data_quality_resolution/test_traceability.py`; `tests/services/data/data_quality_resolution/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Detect gaps, duplicates, ordering faults, spikes, nonfinite/negative/zero-volume concerns, invalid OHLC and out-of-session observations under versioned thresholds. Expected: Boundary fixtures produce stable rule IDs, observation IDs and severity; zero volume is flagged by its feed policy, not universally fabricated or dropped. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-RESOLVE_QUALITY/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-RESOLVE_QUALITY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-14"></a>

### - [ ] Task 2.14 — FEAT-DATA-AGGREGATE_BARS — Aggregate causal bars on declared clocks

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.02, 2.09.

#### i. Feature and remaining work

Strategies and charts receive reproducible timeframe bars with explicit warm-up, gaps and session boundaries.

**Reuse:** `app/services/data/bar_aggregation`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-AGGREGATE_BARS-001 | Aggregate observations into half-open intervals with pinned origin, timezone/session/calendar and gap policy. |
| FR-TRC-DATA-AGGREGATE_BARS-002 | Publish only complete/available bars and carry partial aggregation state across source partitions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-AGGREGATE_BARS-001 | Removing FEAT-DATA-AGGREGATE_BARS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-AGGREGATE_BARS-001 | An event exactly on the boundary enters the next interval; DST fixtures preserve the declared interval semantics. |
| AT-DATA-AGGREGATE_BARS-002 | Changing chunk size yields identical completed bars; future high/low values are not exposed before bar closure. |
| ATN-DATA-AGGREGATE_BARS-001 | Disable and physically remove bar_aggregation; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/bar_aggregation/test_traceability.py`; `tests/services/data/bar_aggregation/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Aggregate observations into half-open intervals with pinned origin, timezone/session/calendar and gap policy. Expected: An event exactly on the boundary enters the next interval; DST fixtures preserve the declared interval semantics. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-AGGREGATE_BARS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-AGGREGATE_BARS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-15"></a>

### - [ ] Task 2.15 — FEAT-DATA-MANAGE_RETENTION — Inspect, export and retire market data safely

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.09.

#### i. Feature and remaining work

A user can browse/export or retire data while seeing exactly which research and shared artifacts depend on it.

**Reuse:** `app/services/data/data_inspection_retention`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-MANAGE_RETENTION-001 | Return paged observation previews, statistics, coverage and explicit chart LOD with version and sample. |
| FR-TRC-DATA-MANAGE_RETENTION-002 | Export selected data to supported CSV/Arrow/Parquet formats with schema, timezone, filter, counts, checksum and warnings. |
| FR-TRC-DATA-MANAGE_RETENTION-003 | Preview dependencies before clone-timezone, lineage-aware merge, guarded deletion or retirement; create new versions for transformations. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-MANAGE_RETENTION-001 | Removing FEAT-DATA-MANAGE_RETENTION withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-MANAGE_RETENTION-001 | Preview respects requested projection and limits; missing series is unavailable rather than substituted. |
| AT-DATA-MANAGE_RETENTION-002 | Export includes the server-resolved population beyond visible rows and matches its manifest counts. |
| AT-DATA-MANAGE_RETENTION-003 | A referenced series cannot be destructively removed; timezone cloning preserves source bytes and pins the transformation. |
| ATN-DATA-MANAGE_RETENTION-001 | Disable and physically remove data_inspection_retention; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/data_inspection_retention/test_traceability.py`; `tests/services/data/data_inspection_retention/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Return paged observation previews, statistics, coverage and explicit chart LOD with version and sample. Expected: Preview respects requested projection and limits; missing series is unavailable rather than substituted. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-MANAGE_RETENTION/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-MANAGE_RETENTION`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-16"></a>

### - [ ] Task 2.16 — FEAT-DATA-NORMALIZE_TICKS — Normalize recorded ticks while retaining source evidence

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.01.

#### i. Feature and remaining work

Recorded observations preserve executable sides, ordering, flags and gaps instead of being flattened into misleading bars.

**Reuse:** `app/services/data/tick_normalization`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-NORMALIZE_TICKS-001 | Normalize timestamp resolution, source sequence, bid/ask/last atoms, volume meaning and masks without deduplicating equal-time updates. |
| FR-TRC-DATA-NORMALIZE_TICKS-002 | Reject nonfinite/invalid prices and report source gaps and normalization policy in the immutable manifest. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-NORMALIZE_TICKS-001 | Removing FEAT-DATA-NORMALIZE_TICKS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-NORMALIZE_TICKS-001 | Equal-time quote changes remain in source order; last-only data never gains fabricated bid/ask quotes. |
| AT-DATA-NORMALIZE_TICKS-002 | Two runs over the same fixture and policy yield equal count/hash/order, including across chunk boundaries. |
| ATN-DATA-NORMALIZE_TICKS-001 | Disable and physically remove tick_normalization; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/tick_normalization/test_traceability.py`; `tests/services/data/tick_normalization/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Normalize timestamp resolution, source sequence, bid/ask/last atoms, volume meaning and masks without deduplicating equal-time updates. Expected: Equal-time quote changes remain in source order; last-only data never gains fabricated bid/ask quotes. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-NORMALIZE_TICKS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-NORMALIZE_TICKS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-17"></a>

### - [ ] Task 2.17 — FEAT-DATA-GENERATE_SCENARIOS — Publish synthetic market-data scenarios

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U4.

**Order prerequisites:** 2.09.

#### i. Feature and remaining work

Deterministic tests and stress research receive reproducible synthetic observations clearly distinguished from recorded markets.

**Reuse:** `app/services/data/synthetic_scenario_series`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-GENERATE_SCENARIOS-001 | Generate bounded scenario series from explicit method/version/seed/units/gap parameters. |
| FR-TRC-DATA-GENERATE_SCENARIOS-002 | Mark source/evidence class as synthetic and preserve full construction metadata through Data binding and exports. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-GENERATE_SCENARIOS-001 | Removing FEAT-DATA-GENERATE_SCENARIOS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-GENERATE_SCENARIOS-001 | The same seed/configuration yields the same series hash; changing a parameter creates a new version. |
| AT-DATA-GENERATE_SCENARIOS-002 | A synthetic fixture cannot be displayed or qualified as recorded market history. |
| ATN-DATA-GENERATE_SCENARIOS-001 | Disable and physically remove synthetic_scenario_series; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/synthetic_scenario_series/test_traceability.py`; `tests/services/data/synthetic_scenario_series/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Generate bounded scenario series from explicit method/version/seed/units/gap parameters. Expected: The same seed/configuration yields the same series hash; changing a parameter creates a new version. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-GENERATE_SCENARIOS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-GENERATE_SCENARIOS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-18"></a>

### - [ ] Task 2.18 — FEAT-DATA-TRACK_MARKET_NEWS — Supply governed point-in-time document evidence

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U4.

**Order prerequisites:** 2.09.

#### i. Feature and remaining work

Analysts receive relevant source documents, revisions and availability times rather than model-invented market facts.

**Reuse:** `app/services/data/economic_news_evidence`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-TRACK_MARKET_NEWS-001 | Register allowed source classes and retain observation, publication/availability, revision, licensing, trust, asset applicability and content hashes. |
| FR-TRC-DATA-TRACK_MARKET_NEWS-002 | Return bounded authorized evidence projections without secrets, executable instructions or cross-account material. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-TRACK_MARKET_NEWS-001 | Removing FEAT-DATA-TRACK_MARKET_NEWS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-TRACK_MARKET_NEWS-001 | A revised document unavailable at the requested cutoff is excluded; absent/inapplicable evidence returns typed coverage reasons. |
| AT-DATA-TRACK_MARKET_NEWS-002 | Injected source text stays untrusted evidence; unauthorized sources cannot be fetched by a role naming a URL. |
| ATN-DATA-TRACK_MARKET_NEWS-001 | Disable and physically remove economic_news_evidence; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/economic_news_evidence/test_traceability.py`; `tests/services/data/economic_news_evidence/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register allowed source classes and retain observation, publication/availability, revision, licensing, trust, asset applicability and content hashes. Expected: A revised document unavailable at the requested cutoff is excluded; absent/inapplicable evidence returns typed coverage reasons. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-TRACK_MARKET_NEWS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-TRACK_MARKET_NEWS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-19"></a>

### - [ ] Task 2.19 — FEAT-DATA-INGEST_HISTORY — Import historical observations with a conserved receipt

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.08, 2.09, 2.10.

#### i. Feature and remaining work

A user obtains an immutable, inspectable historical dataset from an authorized file or source without losing import provenance.

**Reuse:** `app/services/data/historical_data_ingestion`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-INGEST_HISTORY-001 | Import bounded delimited/CSV, Arrow/Parquet and registered tick/bar formats using an explicit column, encoding, timezone and malformed-row policy. |
| FR-TRC-DATA-INGEST_HISTORY-002 | Conserve input, accepted, rejected, duplicate, transformed and published observation accounting with immutable source and output hashes. |
| FR-TRC-DATA-INGEST_HISTORY-003 | Publish a new dataset version only after validation and verified storage publication; expose cancel/partial inspection separately from committed data. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-INGEST_HISTORY-001 | Removing FEAT-DATA-INGEST_HISTORY withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-INGEST_HISTORY-001 | Wrong type/version or timestamp mapping fails with row/path reasons; no format is inferred solely from its extension. |
| AT-DATA-INGEST_HISTORY-002 | Reimport an identical fixture: the receipt is idempotent and the selected dedup policy produces the same ordering/count/hash. |
| AT-DATA-INGEST_HISTORY-003 | A crash before commit leaves no available partial series; cancellation retains a truthful incomplete receipt. |
| ATN-DATA-INGEST_HISTORY-001 | Disable and physically remove historical_data_ingestion; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/historical_data_ingestion/test_traceability.py`; `tests/services/data/historical_data_ingestion/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Import bounded delimited/CSV, Arrow/Parquet and registered tick/bar formats using an explicit column, encoding, timezone and malformed-row policy. Expected: Wrong type/version or timestamp mapping fails with row/path reasons; no format is inferred solely from its extension. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-INGEST_HISTORY/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-INGEST_HISTORY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-20"></a>

### - [ ] Task 2.20 — FEAT-DATA-BIND_RUN_DATA — Bind exact eligible inputs to a run

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.01, 2.02, 2.09, 2.10.

#### i. Feature and remaining work

Every accepted experiment resolves the same instrument, profile, calendar, sample and immutable data versions after later data updates.

**Reuse:** `app/services/data/run_data_binding`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-BIND_RUN_DATA-001 | Resolve all primary/additional chart requirements into immutable observation/profile/calendar hashes and explicit coverage. |
| FR-TRC-DATA-BIND_RUN_DATA-002 | Enforce observation/availability cutoff, warm-up and sample boundaries and report eligible recorded/generated source inputs. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-BIND_RUN_DATA-001 | Removing FEAT-DATA-BIND_RUN_DATA withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-BIND_RUN_DATA-001 | Removing a required partition blocks admission; a current profile cannot silently replace the pinned historical version. |
| AT-DATA-BIND_RUN_DATA-002 | A later source correction or future observation is excluded; lack of warm-up/coverage is a typed failure. |
| ATN-DATA-BIND_RUN_DATA-001 | Disable and physically remove run_data_binding; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/run_data_binding/test_traceability.py`; `tests/services/data/run_data_binding/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve all primary/additional chart requirements into immutable observation/profile/calendar hashes and explicit coverage. Expected: Removing a required partition blocks admission; a current profile cannot silently replace the pinned historical version. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-BIND_RUN_DATA/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-BIND_RUN_DATA`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-21"></a>

### - [ ] Task 2.21 — FEAT-DATA-STREAM_MARKET_EVENTS — Expose bounded normalized real-time observations

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.08, 2.16.

#### i. Feature and remaining work

A market view or owner consumes ordered current observations with explicit staleness and reconnect behavior.

**Reuse:** `app/services/data/realtime_market_events`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-STREAM_MARKET_EVENTS-001 | Stream normalized source events with stable identity/sequence, observed time, source and freshness status. |
| FR-TRC-DATA-STREAM_MARKET_EVENTS-002 | Bound subscribers and coalesce presentation updates without thinning the authoritative execution stream. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-STREAM_MARKET_EVENTS-001 | Removing FEAT-DATA-STREAM_MARKET_EVENTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-STREAM_MARKET_EVENTS-001 | Out-of-order/gap/reconnect fixtures preserve ordering diagnostics; a disconnected source becomes stale/unavailable, not frozen-live. |
| AT-DATA-STREAM_MARKET_EVENTS-002 | A slow widget receives bounded updates; removing it disposes its subscription without stopping other consumers. |
| ATN-DATA-STREAM_MARKET_EVENTS-001 | Disable and physically remove realtime_market_events; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/realtime_market_events/test_traceability.py`; `tests/services/data/realtime_market_events/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Stream normalized source events with stable identity/sequence, observed time, source and freshness status. Expected: Out-of-order/gap/reconnect fixtures preserve ordering diagnostics; a disconnected source becomes stale/unavailable, not frozen-live. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-STREAM_MARKET_EVENTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-STREAM_MARKET_EVENTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-22"></a>

### - [ ] Task 2.22 — FEAT-CAT-MANAGE_UNIVERSES — Version instrument groups and equity universes

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.01, 2.20.

#### i. Feature and remaining work

Research and stock selection operate on an explicit universe with membership and coverage, not a mutable display list.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-MANAGE_UNIVERSES-001 | Create/edit/import/export/search groups and page their members with counts and protected-system status. |
| FR-TRC-CAT-MANAGE_UNIVERSES-002 | Resolve an as-of universe and link data readiness/coverage without hiding delisted or unavailable members. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-MANAGE_UNIVERSES-001 | Removing FEAT-CAT-MANAGE_UNIVERSES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-MANAGE_UNIVERSES-001 | CSV/XML membership exchange round-trips stable instrument IDs; protected group deletion is rejected. |
| AT-CAT-MANAGE_UNIVERSES-002 | A historical snapshot does not acquire a later-added instrument; missing coverage is itemized, not treated as a zero return. |
| ATN-CAT-MANAGE_UNIVERSES-001 | Disable and physically remove manage_universes; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/manage_universes/test_traceability.py`; `tests/services/catalogue/manage_universes/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/edit/import/export/search groups and page their members with counts and protected-system status. Expected: CSV/XML membership exchange round-trips stable instrument IDs; protected group deletion is rejected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-MANAGE_UNIVERSES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-MANAGE_UNIVERSES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-23"></a>

### - [ ] Task 2.23 — FEAT-DATA-ALIGN_SERIES — Align external series without look-ahead

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.02, 2.20.

#### i. Feature and remaining work

A multi-timeframe or auxiliary-series node sees only values available at its decision time, with explicit missingness.

**Reuse:** `app/services/data/external_series_alignment`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-ALIGN_SERIES-001 | Align by declared observation/availability timestamps, calendar, units and as-of join policy. |
| FR-TRC-DATA-ALIGN_SERIES-002 | Preserve missing/stale/unsupported values and version every resampling or fill convention. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-ALIGN_SERIES-001 | Removing FEAT-DATA-ALIGN_SERIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-ALIGN_SERIES-001 | A higher-timeframe bar that has not closed cannot be joined into a lower-timeframe decision. |
| AT-DATA-ALIGN_SERIES-002 | Gap fixtures never become valid zeroes; different alignment policies produce distinct artifact identities. |
| ATN-DATA-ALIGN_SERIES-001 | Disable and physically remove external_series_alignment; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/external_series_alignment/test_traceability.py`; `tests/services/data/external_series_alignment/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Align by declared observation/availability timestamps, calendar, units and as-of join policy. Expected: A higher-timeframe bar that has not closed cannot be joined into a lower-timeframe decision. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-ALIGN_SERIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-ALIGN_SERIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-24"></a>

### - [ ] Task 2.24 — FEAT-DATA-SYNC_CONNECTORS — Resume bounded source synchronization

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.18, 2.08, 2.19.

#### i. Feature and remaining work

Historical downloads and updates can be paused, resumed or cancelled with truthful per-source progress and no duplicate publication.

**Reuse:** `app/services/data/connector_synchronization`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-SYNC_CONNECTORS-001 | Plan source-specific date/instrument updates using exact provider support and finite resource/rate budgets. |
| FR-TRC-DATA-SYNC_CONNECTORS-002 | Checkpoint at declared provider boundaries and reconcile already published partitions before retry. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-SYNC_CONNECTORS-001 | Removing FEAT-DATA-SYNC_CONNECTORS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-SYNC_CONNECTORS-001 | An unsupported pause or range returns a per-item outcome; bulk commands resolve the authorized job set. |
| AT-DATA-SYNC_CONNECTORS-002 | Disconnect after publication then resume: no partition or accepted observation is published twice. |
| ATN-DATA-SYNC_CONNECTORS-001 | Disable and physically remove connector_synchronization; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/connector_synchronization/test_traceability.py`; `tests/services/data/connector_synchronization/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Plan source-specific date/instrument updates using exact provider support and finite resource/rate budgets. Expected: An unsupported pause or range returns a per-item outcome; bulk commands resolve the authorized job set. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-SYNC_CONNECTORS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-SYNC_CONNECTORS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-25"></a>

### - [ ] Task 2.25 — FEAT-DATA-PREPARE_PROFILES — Prepare eligible inputs for market profiles

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U10.

**Order prerequisites:** 2.02, 2.20.

#### i. Feature and remaining work

Profile calculations receive explicit source volume, session and bin inputs instead of mistaking tick counts for exchange volume.

**Reuse:** `app/services/data/profile_source_preparation`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-PREPARE_PROFILES-001 | Bind source type, quantity/volume meaning, sessions, price scale and bin-input coverage. |
| FR-TRC-DATA-PREPARE_PROFILES-002 | Prepare bounded eligible session slices and identify gaps or incomplete support. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-PREPARE_PROFILES-001 | Removing FEAT-DATA-PREPARE_PROFILES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-PREPARE_PROFILES-001 | Tick-volume and exchange-volume fixtures remain differently labelled and cannot be compared as identical evidence. |
| AT-DATA-PREPARE_PROFILES-002 | Empty or partial sessions are reported explicitly; no invented volume enters the downstream calculation. |
| ATN-DATA-PREPARE_PROFILES-001 | Disable and physically remove profile_source_preparation; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/profile_source_preparation/test_traceability.py`; `tests/services/data/profile_source_preparation/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Bind source type, quantity/volume meaning, sessions, price scale and bin-input coverage. Expected: Tick-volume and exchange-volume fixtures remain differently labelled and cannot be compared as identical evidence. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-PREPARE_PROFILES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-PREPARE_PROFILES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-26"></a>

### - [ ] Task 2.26 — FEAT-DATA-IMPORT_QUANTDATA — Import QuantDataManager source artifacts

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.16, 2.19.

#### i. Feature and remaining work

Existing QDM data can be reused through a verified format/version adapter and the same Data publication path.

**Reuse:** `app/services/data/quantdata_manager_source`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-IMPORT_QUANTDATA-001 | Inspect supported QDM tick/bar artifacts with explicit version, symbol, timezone, precision and coverage mapping. |
| FR-TRC-DATA-IMPORT_QUANTDATA-002 | Delegate normalized publication to Data ingestion/store and retain a complete conversion receipt. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-IMPORT_QUANTDATA-001 | Removing FEAT-DATA-IMPORT_QUANTDATA withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-IMPORT_QUANTDATA-001 | Unknown layouts are unavailable/opaque; a supported fixture preserves count, timestamp and price/volume semantics. |
| AT-DATA-IMPORT_QUANTDATA-002 | Reimport is idempotent; cancellation/corruption produces no partially available dataset. |
| ATN-DATA-IMPORT_QUANTDATA-001 | Disable and physically remove quantdata_manager_source; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/quantdata_manager_source/test_traceability.py`; `tests/services/data/quantdata_manager_source/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Inspect supported QDM tick/bar artifacts with explicit version, symbol, timezone, precision and coverage mapping. Expected: Unknown layouts are unavailable/opaque; a supported fixture preserves count, timestamp and price/volume semantics. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-IMPORT_QUANTDATA/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-IMPORT_QUANTDATA`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-27"></a>

### - [ ] Task 2.27 — FEAT-CAT-EXCHANGE_CATALOGUE — Exchange catalogue definitions safely

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Catalogue · **Owner specification:** `app/services/catalogue/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.17, 2.01, 2.02, 2.10, 2.22.

#### i. Feature and remaining work

Instrument, session, profile and group definitions can be transferred with explicit conflicts and no name-based overwrite.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-CAT-EXCHANGE_CATALOGUE-001 | Inspect supported CSV/XML catalogue schemas in a bounded parser and map to typed owner revisions. |
| FR-TRC-CAT-EXCHANGE_CATALOGUE-002 | Preview reuse/fork/new-version/reject outcomes and publish accepted definitions with an immutable conversion report. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-CAT-EXCHANGE_CATALOGUE-001 | Removing FEAT-CAT-EXCHANGE_CATALOGUE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-CAT-EXCHANGE_CATALOGUE-001 | XXE/DTD/network resolution and duplicate identities fail; supported fixtures preserve units, timezone and mapping semantics. |
| AT-CAT-EXCHANGE_CATALOGUE-002 | A colliding display name never replaces another object; retry preserves a single receipt and identical output references. |
| ATN-CAT-EXCHANGE_CATALOGUE-001 | Disable and physically remove exchange_catalogue; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/catalogue/exchange_catalogue/test_traceability.py`; `tests/services/catalogue/exchange_catalogue/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Inspect supported CSV/XML catalogue schemas in a bounded parser and map to typed owner revisions. Expected: XXE/DTD/network resolution and duplicate identities fail; supported fixtures preserve units, timezone and mapping semantics. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-CAT-EXCHANGE_CATALOGUE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(catalogue): complete FEAT-CAT-EXCHANGE_CATALOGUE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-28"></a>

### - [ ] Task 2.28 — FEAT-DATA-IMPORT_INDICATORS — Import non-executable external indicator series

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.19, 2.23.

#### i. Feature and remaining work

An external indicator file becomes a versioned typed data series with a compatibility report, not code trusted by the browser.

**Reuse:** `app/services/data/external_indicator_series`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-IMPORT_INDICATORS-001 | Define/recognize a bounded external-series format and preview timestamp/value/unit/schema mappings. |
| FR-TRC-DATA-IMPORT_INDICATORS-002 | Import/edit-by-new-version/view/delete through Data policy and retain the original artifact and conversion report. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-IMPORT_INDICATORS-001 | Removing FEAT-DATA-IMPORT_INDICATORS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-IMPORT_INDICATORS-001 | Malformed or incompatible formats return diagnostic rows before publication; recognition does not execute embedded content. |
| AT-DATA-IMPORT_INDICATORS-002 | An imported script payload stays opaque/rejected; source/version references and missing values survive round trip. |
| ATN-DATA-IMPORT_INDICATORS-001 | Disable and physically remove external_indicator_series; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/external_indicator_series/test_traceability.py`; `tests/services/data/external_indicator_series/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Define/recognize a bounded external-series format and preview timestamp/value/unit/schema mappings. Expected: Malformed or incompatible formats return diagnostic rows before publication; recognition does not execute embedded content. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-IMPORT_INDICATORS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(data): complete FEAT-DATA-IMPORT_INDICATORS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-29"></a>

### - [ ] Task 2.29 — FEAT-DATA-BROWSE_REFERENCE — Browse one coherent data/reference projection

**Status:** `PARTIAL` · **Domain:** Data · **Owner specification:** `app/services/data/README.md` · **Register first slice:** U1.

**Order prerequisites:** 2.01, 2.02, 2.09, 2.10, 2.13, 2.24.

#### i. Feature and remaining work

The Data Manager discovers existing series, profiles, instruments and readiness through one bounded public query boundary.

**Reuse:** `app/services/data/browse_reference`. The current Browse Reference package exists; the market-data-store manifest also advertises its capability. Resolve one selected provider/owner without a shadow store, preserve compatible routes, implement operation-time quality/transfer checks and clear the recorded browse_reference.py lint finding.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-DATA-BROWSE_REFERENCE-001 | Return cursor-paged series metadata and Catalogue references with all §12.2 grid fields and explicit unavailable/partial states. |
| FR-TRC-DATA-BROWSE_REFERENCE-002 | Expose only supported import/download/quality/clone/export/batch operations and their owner schemas. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-DATA-BROWSE_REFERENCE-001 | Removing FEAT-DATA-BROWSE_REFERENCE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-DATA-BROWSE_REFERENCE-001 | Changing page/sort preserves row identity and snapshot; missing downstream providers are named. |
| AT-DATA-BROWSE_REFERENCE-002 | No offered action bypasses owner validation or manufactures a successful receipt when the provider is absent. |
| ATN-DATA-BROWSE_REFERENCE-001 | Disable and physically remove browse_reference; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/data/browse_reference/test_traceability.py`; `tests/services/data/browse_reference/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Return cursor-paged series metadata and Catalogue references with all §12.2 grid fields and explicit unavailable/partial states. Expected: Changing page/sort preserves row identity and snapshot; missing downstream providers are named. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-DATA-BROWSE_REFERENCE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(data): complete FEAT-DATA-BROWSE_REFERENCE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-30"></a>

### - [ ] Task 2.30 — FEAT-IFACE-OBSERVE_MARKET_REFERENCE — Expose Data Manager and reference operations

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.08, 2.13, 2.15, 2.19, 2.24, 2.29.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

**Reuse:** `app/services/interfaces/observe_market_reference`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OBSERVE_MARKET_REFERENCE-001 | Reuse the current Data/reference boundary and translate supported owner schema/actions without creating another data catalogue. |
| FR-TRC-IFACE-OBSERVE_MARKET_REFERENCE-002 | Accept authorized artifact IDs and owner command references for imports, transformations and downloads. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OBSERVE_MARKET_REFERENCE-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OBSERVE_MARKET_REFERENCE-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OBSERVE_MARKET_REFERENCE-001 | Page/snapshot/size/permission errors are preserved; unsupported actions return CAPABILITY_UNAVAILABLE. |
| AT-IFACE-OBSERVE_MARKET_REFERENCE-002 | Interfaces never opens CSV/XML/SQX/Parquet files or writes a Data table. |
| ATN-IFACE-OBSERVE_MARKET_REFERENCE-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OBSERVE_MARKET_REFERENCE-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/observe_market_reference/test_traceability.py`; `tests/services/interfaces/observe_market_reference/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Reuse the current Data/reference boundary and translate supported owner schema/actions without creating another data catalogue. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Page/snapshot/size/permission errors are preserved; unsupported actions return CAPABILITY_UNAVAILABLE. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OBSERVE_MARKET_REFERENCE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OBSERVE_MARKET_REFERENCE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-31"></a>

### - [ ] Task 2.31 — FEAT-UI-18 — Operate the Data Manager workspace

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U1.

**Order prerequisites:** 1.01, 1.02, 1.06, 2.30.

#### i. Feature and remaining work

The user discovers, imports, inspects, fixes, exports and updates historical data through the existing QDM workflow.

**Reuse:** `app/ui/src/components/workflow`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-18-001 | Render series/reference grids with all CAT-DATA fields and supported source/profile/instrument/session/group/external-series controls. |
| FR-TRC-UI-18-002 | Preview owner import mappings/counts, quality findings/repairs, timezone clone/merge/export and dependency-aware deletion. |
| FR-TRC-UI-18-003 | Observe download/import/update jobs with supported pause/resume/stop and authorized bounded raw-data/chart previews. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-18-001 | Removing FEAT-UI-18 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-18-001 | Filtering/selection/batch actions preserve stable IDs; missing capabilities are explicit and system/protected items cannot be edited locally. |
| AT-UI-18-002 | A confirmation names exact object/count/dependencies/reversibility/retained artifacts; browser previews never imply backend success. |
| AT-UI-18-003 | Closing the Data view leaves accepted downloads running; explicit cancellation uses the owner and incomplete coverage stays labelled. |
| ATN-UI-18-001 | Disable and physically remove workflow; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/components/workflow/__tests__/traceability.test.tsx`; `app/ui/src/components/workflow/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Operate the Data Manager workspace). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Filtering/selection/batch actions preserve stable IDs; missing capabilities are explicit and system/protected items cannot be edited locally. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-18/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-18`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-2-32"></a>

### - [ ] Task 2.32 — FEAT-UI-04 — Inspect market charts and typed overlays

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 2.30.

#### i. Feature and remaining work

The user navigates actual market history with sessions, gaps and linked selections without treating drawn pixels as numerical truth.

**Reuse:** `app/ui/src/widgets/chart`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-04-001 | Render declared market-series windows, price/volume/layer units, timezone/calendar, gaps and indicator/entry/exit overlays. |
| FR-TRC-UI-04-002 | Support crosshair/zoom/selection with typed timestamps/series/trade references and bounded LOD/decoding. |
| FR-TRC-UI-04-003 | Offer keyboard/table equivalents and no-WebGL fallback where applicable. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-04-001 | Removing FEAT-UI-04 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-04-001 | Unavailable/wrong-series market data is not substituted; source version and synthetic/recorded labels remain visible. |
| AT-UI-04-002 | Changing zoom changes display sampling only; numeric calculations remain unchanged and past selections retain their identity. |
| AT-UI-04-003 | GPU-off and color-blind/keyboard fixtures preserve access to equivalent values and labels. |
| ATN-UI-04-001 | Disable and physically remove chart; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/widgets/chart/__tests__/traceability.test.tsx`; `app/ui/src/widgets/chart/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect market charts and typed overlays). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Unavailable/wrong-series market data is not substituted; source version and synthetic/recorded labels remain visible. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-04/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-IFACE-OPERATE_RESULTS (Task 4.19, Phase 4). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

**Phase checkpoint owner:** Run E2E-P02 — Import a small authorized CSV or pinned provider fixture, inspect counts and chart data, diagnose a gap, apply a non-destructive repair, export the selected version, and reopen the same version after restart. Publish `docs/dev/evidence/phases/phase-02.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-04`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-3"></a>

## Phase 3 — Strategy authoring and numerical building blocks in the UI

**Feature tasks: 18.** Numerical indicators + HSL/catalogue/chart/ATM/template/version/compiler providers → Strategy gateway → Strategy Studio. Backtest and AI actions show an explicit unavailable state until their later real providers are accepted.

**Visible completion:** Open Strategy Studio, construct an EMA crossover using real catalogue descriptors, validate, save/reopen an immutable revision, export/import native HSL and inspect pseudocode.

**Phase evidence:** `tests/ui/e2e/research/phase_03.spec.ts` and `docs/dev/evidence/phases/phase-03.json`, owned by Task 3.18. All prior affected UI/data/recovery regressions remain required.

<a id="task-3-01"></a>

### - [ ] Task 3.01 — FEAT-IND-CALCULATE_TREND — Calculate causal trend and moving-average series

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.23.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-CALCULATE_TREND-001 | Use declared price/source inputs, periods, seed, warm-up, session and availability policy; preserve multi-output component identity. |
| FR-TRC-IND-CALCULATE_TREND-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-CALCULATE_TREND-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-CALCULATE_TREND-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-CALCULATE_TREND-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-CALCULATE_TREND-001 | EMA uses the simple mean of the first N valid closed values, then alpha=2/(N+1); no pre-seed output is usable. Future-value perturbations cannot alter already available outputs. |
| AT-IND-CALCULATE_TREND-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-CALCULATE_TREND-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-CALCULATE_TREND-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-CALCULATE_TREND-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/calculate_trend/test_traceability.py`; `tests/services/indicators/calculate_trend/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Use declared price/source inputs, periods, seed, warm-up, session and availability policy; preserve multi-output component identity. Expected: EMA uses the simple mean of the first N valid closed values, then alpha=2/(N+1); no pre-seed output is usable. Future-value perturbations cannot alter already available outputs. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-CALCULATE_TREND/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-CALCULATE_TREND`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-02"></a>

### - [ ] Task 3.02 — FEAT-IND-CALCULATE_MOMENTUM — Calculate causal oscillators and momentum series

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.23.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-CALCULATE_MOMENTUM-001 | Version oscillator units, bounds where applicable, smoothing, missingness and symmetry metadata; CCI is not declared bounded merely because it has a midpoint. |
| FR-TRC-IND-CALCULATE_MOMENTUM-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-CALCULATE_MOMENTUM-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-CALCULATE_MOMENTUM-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-CALCULATE_MOMENTUM-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-CALCULATE_MOMENTUM-001 | Wilder RSI returns 50 for zero gain and zero loss, 100 for zero loss only and 0 for zero gain only; comparison/equality-boundary fixtures agree with the reference. |
| AT-IND-CALCULATE_MOMENTUM-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-CALCULATE_MOMENTUM-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-CALCULATE_MOMENTUM-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-CALCULATE_MOMENTUM-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/calculate_momentum/test_traceability.py`; `tests/services/indicators/calculate_momentum/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version oscillator units, bounds where applicable, smoothing, missingness and symmetry metadata; CCI is not declared bounded merely because it has a midpoint. Expected: Wilder RSI returns 50 for zero gain and zero loss, 100 for zero loss only and 0 for zero gain only; comparison/equality-boundary fixtures agree with the reference. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-CALCULATE_MOMENTUM/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-CALCULATE_MOMENTUM`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-03"></a>

### - [ ] Task 3.03 — FEAT-IND-CALCULATE_VOLATILITY — Calculate causal volatility and channel series

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.23.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-CALCULATE_VOLATILITY-001 | Bind estimator definition, window, annualization/session/OHLC assumptions, seed and unavailable conditions rather than treating all volatility measures as interchangeable. |
| FR-TRC-IND-CALCULATE_VOLATILITY-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-CALCULATE_VOLATILITY-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-CALCULATE_VOLATILITY-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-CALCULATE_VOLATILITY-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-CALCULATE_VOLATILITY-001 | ATR seeds the mean of N valid true ranges using the prior available close and then Wilder smoothing; zero/invalid denominators and inadequate history are unavailable. |
| AT-IND-CALCULATE_VOLATILITY-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-CALCULATE_VOLATILITY-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-CALCULATE_VOLATILITY-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-CALCULATE_VOLATILITY-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/calculate_volatility/test_traceability.py`; `tests/services/indicators/calculate_volatility/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Bind estimator definition, window, annualization/session/OHLC assumptions, seed and unavailable conditions rather than treating all volatility measures as interchangeable. Expected: ATR seeds the mean of N valid true ranges using the prior available close and then Wilder smoothing; zero/invalid denominators and inadequate history are unavailable. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-CALCULATE_VOLATILITY/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-CALCULATE_VOLATILITY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-04"></a>

### - [ ] Task 3.04 — FEAT-IND-CALCULATE_VOLUME_FLOW — Calculate source-aware volume and flow series

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U5.

**Order prerequisites:** 2.23.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-CALCULATE_VOLUME_FLOW-001 | Require declared feed volume meaning, price/volume alignment and missingness; bind adjusted-data and session assumptions. |
| FR-TRC-IND-CALCULATE_VOLUME_FLOW-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-CALCULATE_VOLUME_FLOW-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-CALCULATE_VOLUME_FLOW-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-CALCULATE_VOLUME_FLOW-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-CALCULATE_VOLUME_FLOW-001 | Exchange-volume and tick-count inputs retain different provenance; a missing quantity cannot be silently interpreted as zero traded volume. |
| AT-IND-CALCULATE_VOLUME_FLOW-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-CALCULATE_VOLUME_FLOW-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-CALCULATE_VOLUME_FLOW-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-CALCULATE_VOLUME_FLOW-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/calculate_volume_flow/test_traceability.py`; `tests/services/indicators/calculate_volume_flow/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Require declared feed volume meaning, price/volume alignment and missingness; bind adjusted-data and session assumptions. Expected: Exchange-volume and tick-count inputs retain different provenance; a missing quantity cannot be silently interpreted as zero traded volume. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-CALCULATE_VOLUME_FLOW/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-CALCULATE_VOLUME_FLOW`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-05"></a>

### - [ ] Task 3.05 — FEAT-IND-DETECT_CANDLE_PATTERNS — Recognize declared candle-pattern predicates

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U5.

**Order prerequisites:** 2.23.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-DETECT_CANDLE_PATTERNS-001 | Define each pattern with explicit body/shadow ratios, comparison policy, lookback and closed-bar availability before registration. |
| FR-TRC-IND-DETECT_CANDLE_PATTERNS-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-DETECT_CANDLE_PATTERNS-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-DETECT_CANDLE_PATTERNS-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-DETECT_CANDLE_PATTERNS-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-DETECT_CANDLE_PATTERNS-001 | Boundary and gap fixtures return true/false/unknown according to the registered definition; a forming or missing bar cannot produce a confirmed pattern. |
| AT-IND-DETECT_CANDLE_PATTERNS-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-DETECT_CANDLE_PATTERNS-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-DETECT_CANDLE_PATTERNS-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-DETECT_CANDLE_PATTERNS-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/detect_candle_patterns/test_traceability.py`; `tests/services/indicators/detect_candle_patterns/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Define each pattern with explicit body/shadow ratios, comparison policy, lookback and closed-bar availability before registration. Expected: Boundary and gap fixtures return true/false/unknown according to the registered definition; a forming or missing bar cannot produce a confirmed pattern. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-DETECT_CANDLE_PATTERNS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-DETECT_CANDLE_PATTERNS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-06"></a>

### - [ ] Task 3.06 — FEAT-IND-TRANSFORM_SERIES — Calculate typed rolling and fitted series transforms

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.23.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-TRANSFORM_SERIES-001 | Apply typed units, finite numerical domains, rolling state, fit-window metadata and explicit zero-variance/invalid arithmetic policies. |
| FR-TRC-IND-TRANSFORM_SERIES-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-TRANSFORM_SERIES-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-TRANSFORM_SERIES-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-TRANSFORM_SERIES-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-TRANSFORM_SERIES-001 | Divide-by-zero and invalid log/root inputs are unavailable; fitted transforms reject evaluation timestamps and reuse training-fitted state on validation/test. |
| AT-IND-TRANSFORM_SERIES-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-TRANSFORM_SERIES-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-TRANSFORM_SERIES-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-TRANSFORM_SERIES-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/transform_series/test_traceability.py`; `tests/services/indicators/transform_series/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Apply typed units, finite numerical domains, rolling state, fit-window metadata and explicit zero-variance/invalid arithmetic policies. Expected: Divide-by-zero and invalid log/root inputs are unavailable; fitted transforms reject evaluation timestamps and reuse training-fitted state on validation/test. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-TRANSFORM_SERIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-TRANSFORM_SERIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-07"></a>

### - [ ] Task 3.07 — FEAT-STRAT-DEFINE_AST — Validate and normalize the canonical HSL document

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

Humans and agents can express the same strategy in one typed language with deterministic diagnostics.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-DEFINE_AST-001 | Validate HSL language hsl version 2.0.0, schema hsl://schema/strategy/2.0.0, root records, ordered rules and node-store discriminators. |
| FR-TRC-STRAT-DEFINE_AST-002 | Normalize content and compute separate canonical content and semantic hashes without reordering short-circuit expressions. |
| FR-TRC-STRAT-DEFINE_AST-003 | Apply ordered true/false/unknown logic, strict comparison/crossover and typed invalid arithmetic semantics. |
| FR-TRC-STRAT-DEFINE_AST-004 | Convert the §37.2 compact EMA fixture and §37.9 adapter intermediate into the single canonical node-store form. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-DEFINE_AST-001 | Float64 comparison uses atol=1e-10 and rtol=1e-9 in hqa_numeric_clock_v1; exact money types use declared Decimal/atom quantization instead. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-DEFINE_AST-001 | Unknown executable fields/nodes, duplicate IDs, cycles, invalid references and unit/type mismatches produce stable node/path diagnostics; invalid drafts remain inspectable but unrunnable. |
| AT-STRAT-DEFINE_AST-002 | Metadata-only edits preserve semantic hash; a rule-order or parameter change does not; neither hash is treated as a new research family. |
| AT-STRAT-DEFINE_AST-003 | False AND unknown is false; true OR unknown is true; NOT unknown stays unknown; equality on either crossover sample does not trigger a strict cross. |
| AT-STRAT-DEFINE_AST-004 | Converted entry, exit, parameters, bindings and clock meanings match the source fixture; no alternative production schema is registered. |
| ATN-STRAT-DEFINE_AST-001 | Boundary goldens on opposite signs, large/small magnitudes and equality-band edges match the documented comparison policy. |


**Acceptance test targets:** `tests/services/strategy/define_ast/test_traceability.py`; `tests/services/strategy/define_ast/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate HSL language hsl version 2.0.0, schema hsl://schema/strategy/2.0.0, root records, ordered rules and node-store discriminators. Expected: Unknown executable fields/nodes, duplicate IDs, cycles, invalid references and unit/type mismatches produce stable node/path diagnostics; invalid drafts remain inspectable but unrunnable. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-DEFINE_AST/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-DEFINE_AST`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-08"></a>

### - [ ] Task 3.08 — FEAT-STRAT-CATALOG_BLOCKS — Discover compatible declarative strategy blocks

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.12, 3.01, 3.02, 3.03, 3.04, 3.05, 3.06, 3.07.

#### i. Feature and remaining work

Editors and generators insert only blocks whose types, clocks, parameters and providers are compatible with the current strategy.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-CATALOG_BLOCKS-001 | Register immutable block descriptors with type/unit/clock/lookback/parameter/missingness/symmetry/target support and exact contribution disposal. |
| FR-TRC-STRAT-CATALOG_BLOCKS-002 | Keep IndicatorBlock continuous values separate from ConditionBlock Boolean predicates and compose prebuilt conditions through declared numerical references. |
| FR-TRC-STRAT-CATALOG_BLOCKS-003 | Support search/category/provider/compatibility filters, weights, allowed values, external timeframes, parameter calibration previews and versioned presets. |
| FR-TRC-STRAT-CATALOG_BLOCKS-004 | Maintain the ten-category donor-to-native inventory and close every qualified donor entry with a named supported replacement or explicit unavailability. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-CATALOG_BLOCKS-001 | Removing FEAT-STRAT-CATALOG_BLOCKS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-CATALOG_BLOCKS-001 | Two conflicting block ID/version definitions are rejected; removing a contribution removes only that descriptor and makes affected drafts explicitly incompatible. |
| AT-STRAT-CATALOG_BLOCKS-002 | RSI and RSI-cross-up have distinct result types; an unavailable numerical input never becomes a true condition. |
| AT-STRAT-CATALOG_BLOCKS-003 | An incompatible block has a reason; accepting a calibration/preset produces a versioned configuration diff, not a silent strategy mutation. |
| AT-STRAT-CATALOG_BLOCKS-004 | All named entries in CAT-BLOCKS are traceable; a category count alone never becomes 572 verified implementations or fabricated class IDs. |
| ATN-STRAT-CATALOG_BLOCKS-001 | Disable and physically remove catalog_blocks; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/catalog_blocks/test_traceability.py`; `tests/services/strategy/catalog_blocks/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register immutable block descriptors with type/unit/clock/lookback/parameter/missingness/symmetry/target support and exact contribution disposal. Expected: Two conflicting block ID/version definitions are rejected; removing a contribution removes only that descriptor and makes affected drafts explicitly incompatible. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-CATALOG_BLOCKS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-CATALOG_BLOCKS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-09"></a>

### - [ ] Task 3.09 — FEAT-STRAT-CONFIGURE_CHARTS — Validate strategy chart and clock bindings

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.01, 2.02, 3.07.

#### i. Feature and remaining work

A strategy has one unambiguous primary decision context and explicit secondary/order-target bindings.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-CONFIGURE_CHARTS-001 | Validate exactly one PRIMARY plus ordered SECONDARY/ORDER_TARGET bindings, instrument/timeframe/session references and nonnegative shifts. |
| FR-TRC-STRAT-CONFIGURE_CHARTS-002 | Define ON_INIT, ON_BAR_CLOSE, ON_BAR_OPEN, ON_TICK, position callbacks and ON_DEINIT with explicit availability and side-effect constraints. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-CONFIGURE_CHARTS-001 | Removing FEAT-STRAT-CONFIGURE_CHARTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-CONFIGURE_CHARTS-001 | A second PRIMARY or negative shift fails at its path; reordering secondary bindings changes the appropriate canonical identity. |
| AT-STRAT-CONFIGURE_CHARTS-002 | Shift 0 at bar close sees the completed bar; init/deinit cannot create orders; a node requiring recorded microstructure rejects incompatible generated-method support. |
| ATN-STRAT-CONFIGURE_CHARTS-001 | Disable and physically remove configure_charts; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/configure_charts/test_traceability.py`; `tests/services/strategy/configure_charts/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate exactly one PRIMARY plus ordered SECONDARY/ORDER_TARGET bindings, instrument/timeframe/session references and nonnegative shifts. Expected: A second PRIMARY or negative shift fails at its path; reordering secondary bindings changes the appropriate canonical identity. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-CONFIGURE_CHARTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-CONFIGURE_CHARTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-10"></a>

### - [ ] Task 3.10 — FEAT-STRAT-MODEL_ATM_EXITS — Define reusable protective and trade-management policies

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.11, 3.07.

#### i. Feature and remaining work

A strategy can describe stop, target, trailing and time exits with explicit units and timing that every execution target must preserve.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-MODEL_ATM_EXITS-001 | Version disabled/fixed/percent/ATR/formula/absolute SL/PT, break-even, trailing, holding-bar and session/Friday exit definitions. |
| FR-TRC-STRAT-MODEL_ATM_EXITS-002 | Declare activation, trigger side, scope, ratchet, clock and rounding; require new bar-close levels to apply no earlier than the next eligible event. |
| FR-TRC-STRAT-MODEL_ATM_EXITS-003 | Expose partial close, scale-in/out and reversal only when the selected action provider/target supports them. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-MODEL_ATM_EXITS-001 | Removing FEAT-STRAT-MODEL_ATM_EXITS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-MODEL_ATM_EXITS-001 | Missing distance, illegal units, unsupported provider or a widening protective update fails validation. |
| AT-STRAT-MODEL_ATM_EXITS-002 | A trailing long stop never widens; a new protective level cannot fill against an earlier consumed tick. |
| AT-STRAT-MODEL_ATM_EXITS-003 | U10 partial quantity rounds down to the legal step and rejects zero/over-close; an unsupported target cannot advertise executable success. |
| ATN-STRAT-MODEL_ATM_EXITS-001 | Disable and physically remove model_atm_exits; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/model_atm_exits/test_traceability.py`; `tests/services/strategy/model_atm_exits/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version disabled/fixed/percent/ATR/formula/absolute SL/PT, break-even, trailing, holding-bar and session/Friday exit definitions. Expected: Missing distance, illegal units, unsupported provider or a widening protective update fails validation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-MODEL_ATM_EXITS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-MODEL_ATM_EXITS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-11"></a>

### - [ ] Task 3.11 — FEAT-STRAT-EDIT_TEMPLATES — Expand constrained strategy templates and symmetry

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 3.07, 3.08.

#### i. Feature and remaining work

A user or generator can reuse a tested structure, lock parts and preview the exact opposite branch before accepting it.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-EDIT_TEMPLATES-001 | Version template slots and retain/replace/extend/randomize/lock rules for long/short entry, exit and order subgraphs. |
| FR-TRC-STRAT-EDIT_TEMPLATES-002 | Apply descriptor-declared symmetry to comparisons, directions, bands and offsets and preview the generated branch. |
| FR-TRC-STRAT-EDIT_TEMPLATES-003 | Deliver original versioned EMA, inside-bar, range-breakout, divergence, trailing-stop, buy-the-dip and mean-reversion examples. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-EDIT_TEMPLATES-001 | Removing FEAT-STRAT-EDIT_TEMPLATES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-EDIT_TEMPLATES-001 | Crossover, mutation and mirroring leave locked subgraphs unchanged; an incompatible template opens read-only with a report. |
| AT-STRAT-EDIT_TEMPLATES-002 | RSI 30 reflects to 70 only with its declared midpoint; CCI -100 reflects to +100 under its own descriptor; no universal negation is applied. |
| AT-STRAT-EDIT_TEMPLATES-003 | Each example declares data/clock/cost/provider assumptions, converts to HSL and has a bounded executable behavior fixture; none implies profitable or live-approved use. |
| ATN-STRAT-EDIT_TEMPLATES-001 | Disable and physically remove edit_templates; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/edit_templates/test_traceability.py`; `tests/services/strategy/edit_templates/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version template slots and retain/replace/extend/randomize/lock rules for long/short entry, exit and order subgraphs. Expected: Crossover, mutation and mirroring leave locked subgraphs unchanged; an incompatible template opens read-only with a report. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-EDIT_TEMPLATES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-EDIT_TEMPLATES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-12"></a>

### - [ ] Task 3.12 — FEAT-STRAT-DEFINE_INDICATORS — Accept declarative custom indicator definitions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.09, 3.07, 3.08.

#### i. Feature and remaining work

A user or DSL specialist can submit a typed indicator definition for deterministic owner validation instead of arbitrary source execution.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-DEFINE_INDICATORS-001 | Validate typed indicator expressions, inputs, units, output shapes, causal history and supported operations. |
| FR-TRC-STRAT-DEFINE_INDICATORS-002 | Accept reviewed immutable definitions through the same idempotent owner intake and expose a structured unsupported-expression report. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-DEFINE_INDICATORS-001 | Removing FEAT-STRAT-DEFINE_INDICATORS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-DEFINE_INDICATORS-001 | Unknown calls, cycles, future access or arbitrary source strings are rejected; supported definitions have deterministic test vectors. |
| AT-STRAT-DEFINE_INDICATORS-002 | A rejected definition cannot become a registered numerical provider; unsupported semantics never trigger silent source-code fallback. |
| ATN-STRAT-DEFINE_INDICATORS-001 | Disable and physically remove define_indicators; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/define_indicators/test_traceability.py`; `tests/services/strategy/define_indicators/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate typed indicator expressions, inputs, units, output shapes, causal history and supported operations. Expected: Unknown calls, cycles, future access or arbitrary source strings are rejected; supported definitions have deterministic test vectors. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-DEFINE_INDICATORS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-DEFINE_INDICATORS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-13"></a>

### - [ ] Task 3.13 — FEAT-STRAT-COMPILE_STRATEGIES — Compile HSL to reusable target-neutral execution plans

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 3.07, 3.08, 3.09.

#### i. Feature and remaining work

Every simulator and exporter consumes the same validated strategy meaning without compiling source for ordinary parameter trials.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-COMPILE_STRATEGIES-001 | Bind HSL content/semantic hash, node/provider versions, typed constants/operands/parameters/state, clock subscriptions and numerical policy. |
| FR-TRC-STRAT-COMPILE_STRATEGIES-002 | Preserve ordered branches, short-circuit/unknown semantics and units in an immutable compiled plan. |
| FR-TRC-STRAT-COMPILE_STRATEGIES-003 | Reuse compiled topology for ordinary parameter changes and invalidate only affected keys on topology/type/layout/provider changes. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-COMPILE_STRATEGIES-001 | A validated program is typed data, not arbitrary executable source; no private numerical-owner import is permitted. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-COMPILE_STRATEGIES-001 | Unsupported nodes, types, clocks or provider generations produce source-mapped diagnostics before execution. |
| AT-STRAT-COMPILE_STRATEGIES-002 | Reference HSL and plan traces agree on branch order, emitted intents and unavailable values. |
| AT-STRAT-COMPILE_STRATEGIES-003 | A 1,000-tuple parameter campaign does not JIT-compile once per tuple; the result identity still includes every effective parameter value. |
| ATN-STRAT-COMPILE_STRATEGIES-001 | Architecture scans and hostile-node fixtures prove public descriptor binding only; compile-cache invalidation includes cross-file/provider fingerprints. |


**Acceptance test targets:** `tests/services/strategy/compile_strategies/test_traceability.py`; `tests/services/strategy/compile_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Bind HSL content/semantic hash, node/provider versions, typed constants/operands/parameters/state, clock subscriptions and numerical policy. Expected: Unsupported nodes, types, clocks or provider generations produce source-mapped diagnostics before execution. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-COMPILE_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-COMPILE_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-14"></a>

### - [ ] Task 3.14 — FEAT-STRAT-VERSION_STRATEGIES — Accept immutable strategy revisions and reviewed patches

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.09, 3.07, 3.08, 3.09, 3.10, 3.11.

#### i. Feature and remaining work

A saved or AI-assisted edit becomes exactly the revision the user reviewed, while historical strategies and results remain unchanged.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-VERSION_STRATEGIES-001 | Create/load/clone/archive immutable strategy revisions with typed metadata, parameters, variables and lineage. |
| FR-TRC-STRAT-VERSION_STRATEGIES-002 | Preview and accept an ordered patch bound to base revision/hash, changed paths, semantic versions and candidate hash. |
| FR-TRC-STRAT-VERSION_STRATEGIES-003 | Compute the dependency closure of granular accepted edits and validate the entire resulting HSL document before commit. |
| FR-TRC-STRAT-VERSION_STRATEGIES-004 | Keep save/qualification/export/backtest as separate owner actions with exact receipt-derived UI states. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-VERSION_STRATEGIES-001 | Removing FEAT-STRAT-VERSION_STRATEGIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-VERSION_STRATEGIES-001 | Changing a display name follows metadata revision policy; previous run references still resolve the exact prior content hash. |
| AT-STRAT-VERSION_STRATEGIES-002 | A stale base conflicts; changing the selection changes the review hash; a replayed acceptance returns one revision receipt. |
| AT-STRAT-VERSION_STRATEGIES-003 | Accepting an action whose new node was rejected is blocked or expands an explicitly reviewed closure; no dangling node is saved. |
| AT-STRAT-VERSION_STRATEGIES-004 | Saving yields Draft saved only after its receipt; it never queues a backtest, changes Risk approval or activates trading. |
| ATN-STRAT-VERSION_STRATEGIES-001 | Disable and physically remove version_strategies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/version_strategies/test_traceability.py`; `tests/services/strategy/version_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/load/clone/archive immutable strategy revisions with typed metadata, parameters, variables and lineage. Expected: Changing a display name follows metadata revision policy; previous run references still resolve the exact prior content hash. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-VERSION_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-VERSION_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-15"></a>

### - [ ] Task 3.15 — FEAT-STRAT-GENERATE_CODE — Produce pseudocode and route compatible source generation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.17, 3.13.

#### i. Feature and remaining work

A user can inspect the strategy’s behavior and select only generators capable of preserving it.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-GENERATE_CODE-001 | Generate ordered pseudocode from the compiled plan with node/source mapping, units, clocks and warnings. |
| FR-TRC-STRAT-GENERATE_CODE-002 | Resolve a target/version/options schema and return exact unsupported-node/operator/clock diagnostics before dispatch. |
| FR-TRC-STRAT-GENERATE_CODE-003 | Retain generation options, provider/toolchain, parameter mapping, validation level and immutable output hash. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-GENERATE_CODE-001 | Removing FEAT-STRAT-GENERATE_CODE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-GENERATE_CODE-001 | The same branch/order/exit semantics are visible as in the plan; unavailable nodes cannot become executable-looking success. |
| AT-STRAT-GENERATE_CODE-002 | Removing a target removes only its menu option/capability; core simulation remains available. |
| AT-STRAT-GENERATE_CODE-003 | A missing compiler yields UNVERIFIED_TARGET, not a supported target badge. |
| ATN-STRAT-GENERATE_CODE-001 | Disable and physically remove generate_code; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/generate_code/test_traceability.py`; `tests/services/strategy/generate_code/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Generate ordered pseudocode from the compiled plan with node/source mapping, units, clocks and warnings. Expected: The same branch/order/exit semantics are visible as in the plan; unavailable nodes cannot become executable-looking success. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-GENERATE_CODE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-GENERATE_CODE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-16"></a>

### - [ ] Task 3.16 — FEAT-STRAT-EXCHANGE_STRATEGIES — Exchange native strategy and multi-entity bundles

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.17, 3.14.

#### i. Feature and remaining work

A user can move strategies and related research artifacts between workspaces with explicit compatibility and conflict reports.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-EXCHANGE_STRATEGIES-001 | Inspect .hsl.json and typed .hqa.zip manifests with member hashes, schema/dependencies, bounded hostile-input validation and opaque-member policy. |
| FR-TRC-STRAT-EXCHANGE_STRATEGIES-002 | Preview reuse-by-hash/fork/new-revision/reject decisions and coordinate idempotent staged owner commits. |
| FR-TRC-STRAT-EXCHANGE_STRATEGIES-003 | Preserve semantic native round trips for strategy/result/portfolio/project/model/package bundle kinds and issue a per-member truthful conversion report. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-EXCHANGE_STRATEGIES-001 | Removing FEAT-STRAT-EXCHANGE_STRATEGIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-EXCHANGE_STRATEGIES-001 | Bad hash, traversal, case collision, zip bomb, deep JSON/XML or unsupported framing yields no accepted executable entity. |
| AT-STRAT-EXCHANGE_STRATEGIES-002 | A colliding display name never overwrites; crash between owners leaves no active reference to uncommitted bytes and reconciliation retains a coordinator receipt. |
| AT-STRAT-EXCHANGE_STRATEGIES-003 | Definition-only export fabricates no results; lossy/partial/unknown content remains labelled and source bytes are preserved. |
| ATN-STRAT-EXCHANGE_STRATEGIES-001 | Disable and physically remove exchange_strategies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/exchange_strategies/test_traceability.py`; `tests/services/strategy/exchange_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Inspect .hsl.json and typed .hqa.zip manifests with member hashes, schema/dependencies, bounded hostile-input validation and opaque-member policy. Expected: Bad hash, traversal, case collision, zip bomb, deep JSON/XML or unsupported framing yields no accepted executable entity. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-EXCHANGE_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-ANA-EXCHANGE_RESULTS (Task 4.18, Phase 4); FEAT-POR-COMPOSE_PORTFOLIOS (Task 10.01, Phase 10); FEAT-ORCH-DEFINE_PROJECTS (Task 11.02, Phase 11); FEAT-RES-VALIDATE_MODELS (Task 14.05, Phase 14); FEAT-PLUG-MANAGE_LIFECYCLE (Task 12.08, Phase 12). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-EXCHANGE_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-17"></a>

### - [ ] Task 3.17 — FEAT-IFACE-OPERATE_STRATEGIES — Expose strategy authoring and exchange

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.08, 3.08, 3.11, 3.14, 3.15, 3.16.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_STRATEGIES-001 | Translate strategy authoring/revision/patch/exchange requests with exact candidate hash and expected revision. |
| FR-TRC-IFACE-OPERATE_STRATEGIES-002 | Expose compatible block/generator discovery and asynchronous owner export receipts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_STRATEGIES-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_STRATEGIES-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_STRATEGIES-001 | Changed base/selection conflicts remain visible; a save cannot implicitly start a backtest. |
| AT-IFACE-OPERATE_STRATEGIES-002 | No generator/compiler/AST mutation logic exists in the gateway; removing an owner fails closed. |
| ATN-IFACE-OPERATE_STRATEGIES-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_STRATEGIES-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_strategies/test_traceability.py`; `tests/services/interfaces/operate_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate strategy authoring/revision/patch/exchange requests with exact candidate hash and expected revision. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Changed base/selection conflicts remain visible; a save cannot implicitly start a backtest. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-STRAT-ACCEPT_PROPOSALS (Task 6.01, Phase 6); FEAT-STRAT-PACKAGE_STRATEGIES (Task 16.11, Phase 16); FEAT-STRAT-IMPORT_SQX (Task 16.10, Phase 16); FEAT-STRAT-DEFINE_SEARCH_SPACES (Task 8.01, Phase 8). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-3-18"></a>

### - [ ] Task 3.18 — FEAT-UI-STRATEGY_STUDIO — Edit and review a strategy

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 3.14, 3.15, 3.16, 3.17.

#### i. Feature and remaining work

Author one HSL definition through equivalent visual/tree/form views, with safe immutable revision acceptance.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-STRATEGY_STUDIO-001 | Keep canvas, keyboard tree/forms and HSL projections semantically equivalent with stable node IDs and incremental path diagnostics. |
| FR-TRC-UI-STRATEGY_STUDIO-002 | Preview new definitions and base-bound granular AI patches with assumptions, affected paths, diagnostics, hashes and compatible operation closure. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-STRATEGY_STUDIO-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-STRATEGY_STUDIO-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-STRATEGY_STUDIO-001 | Round-trip edits and undo/redo preserve all supported nodes, order, parameters and bindings; invalid/unknown nodes remain inspectable but unrunnable. |
| AT-UI-STRATEGY_STUDIO-002 | A stale revision or changed selection requires new review; accepting a draft saves only after the Strategy receipt, without starting a run. |
| ATN-UI-STRATEGY_STUDIO-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-STRATEGY_STUDIO-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/strategy-editor/__tests__/traceability.test.tsx`; `app/ui/src/widgets/strategy-editor/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Edit and review a strategy). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Round-trip edits and undo/redo preserve all supported nodes, order, parameters and bindings; invalid/unknown nodes remain inspectable but unrunnable. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-STRATEGY_STUDIO/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-IFACE-AGENTIC_GATEWAY (Task 5.09, Phase 5); FEAT-IFACE-OPERATE_SIMULATIONS (Task 4.11, Phase 4). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

**Phase checkpoint owner:** Run E2E-P03 — Open Strategy Studio, construct an EMA crossover using real catalogue descriptors, validate, save/reopen an immutable revision, export/import native HSL and inspect pseudocode. Publish `docs/dev/evidence/phases/phase-03.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-STRATEGY_STUDIO`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-4"></a>

## Phase 4 — Native tick backtest, results and databanks end to end

**Feature tasks: 27.** Risk/Trading pure policies + tick-method/native engine/result publication + Analytics → Simulation/Results gateways → Simulator, Results, Databank, trade/equity widgets and Performance Lab.

**Visible completion:** Select the saved EMA strategy and versioned data, run an explicit recorded/generated tick backtest, reconnect during execution, inspect metrics/trades/equity, move selected databank members and export a provenance-complete result.

**Phase evidence:** `tests/ui/e2e/research/phase_04.spec.ts` and `docs/dev/evidence/phases/phase-04.json`, owned by Task 4.27. All prior affected UI/data/recovery regressions remain required.

<a id="task-4-01"></a>

### - [ ] Task 4.01 — FEAT-UI-PERFORMANCE_LAB — Inspect reproducible performance and lifecycle evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U10.

**Order prerequisites:** 1.01, 1.02, 1.25.

#### i. Feature and remaining work

A developer can compare measured workloads and UI churn without mistaking targets or cache hits for real speed evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-PERFORMANCE_LAB-001 | Run the developer-only deterministic grid operation stream with insert 20 ms/remove 30 ms/update 40 ms and at most ten visual batches per second. |
| FR-TRC-UI-PERFORMANCE_LAB-002 | Inspect matched benchmark reports with source/emitted/consumed ticks, tick-strategy evaluations, outputs, cache/cold/warm and stage time/memory/copy/I/O distinctions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-PERFORMANCE_LAB-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-PERFORMANCE_LAB-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-PERFORMANCE_LAB-001 | Simulated-clock replay gives identical selection/operation order; stop/unmount leaves no timer/listener/worker/request. |
| AT-UI-PERFORMANCE_LAB-002 | A target without a measurement or a mismatched fixture cannot be marked passed; throughput excludes exact result-cache hits. |
| ATN-UI-PERFORMANCE_LAB-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-PERFORMANCE_LAB-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/performance-lab/__tests__/traceability.test.tsx`; `app/ui/src/widgets/performance-lab/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect reproducible performance and lifecycle evidence). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Simulated-clock replay gives identical selection/operation order; stop/unmount leaves no timer/listener/worker/request. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-PERFORMANCE_LAB/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-PERFORMANCE_LAB`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-02"></a>

### - [ ] Task 4.02 — FEAT-RSK-SIZE_POSITIONS — Calculate legal size from a pinned risk basis

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Risk · **Owner specification:** `app/services/risk/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.11, 2.12.

#### i. Feature and remaining work

A simulation uses the configured risk/capital basis and legal size lattice rather than a hidden lot-size shortcut.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RSK-SIZE_POSITIONS-001 | Calculate fixed units, fixed currency risk, balance-percent risk, equity-percent risk and equity-price allocation from explicit finite inputs. |
| FR-TRC-RSK-SIZE_POSITIONS-002 | Round to the legal quantity lattice and record clamps/rejections, fees and currency/point-value dependencies. |
| FR-TRC-RSK-SIZE_POSITIONS-003 | Add volatility-target sizing with training-fitted volatility, leverage/size caps and rebalance clock as a versioned U10 provider. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RSK-SIZE_POSITIONS-001 | Removing FEAT-RSK-SIZE_POSITIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RSK-SIZE_POSITIONS-001 | Missing stop distance, conversion, price or illegal constraints fails; balance and equity bases cannot be interchanged silently. |
| AT-RSK-SIZE_POSITIONS-002 | Large-notional/intermediate-overflow fixtures fail safely or use a separately qualified wider implementation; exact results match Decimal. |
| AT-RSK-SIZE_POSITIONS-003 | Future/evaluation data cannot fit its volatility model; an unavailable provider blocks only that method. |
| ATN-RSK-SIZE_POSITIONS-001 | Disable and physically remove size_positions; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/risk/size_positions/test_traceability.py`; `tests/services/risk/size_positions/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Calculate fixed units, fixed currency risk, balance-percent risk, equity-percent risk and equity-price allocation from explicit finite inputs. Expected: Missing stop distance, conversion, price or illegal constraints fails; balance and equity bases cannot be interchanged silently. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RSK-SIZE_POSITIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(risk): complete FEAT-RSK-SIZE_POSITIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-03"></a>

### - [ ] Task 4.03 — FEAT-RSK-ASSESS_RESEARCH_RISK — Expose risk evidence and owner-controlled review

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Risk · **Owner specification:** `app/services/risk/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.04.

#### i. Feature and remaining work

Research and advisory clients can ask risk questions against current owner evidence without acquiring economic approval authority.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RSK-ASSESS_RESEARCH_RISK-001 | Return authorized versioned risk/limit/admissibility projections with observation time, scope, expiry and provenance. |
| FR-TRC-RSK-ASSESS_RESEARCH_RISK-002 | Evaluate permitted review requests through existing deterministic policy and retain exact decision/receipt semantics. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RSK-ASSESS_RESEARCH_RISK-001 | Removing FEAT-RSK-ASSESS_RESEARCH_RISK withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RSK-ASSESS_RESEARCH_RISK-001 | Wrong-account or stale evidence is denied/unavailable; a model cannot replace missing risk truth. |
| AT-RSK-ASSESS_RESEARCH_RISK-002 | Absence of criticism or an Agentic advisory is never interpreted as approval; the owner can reject unchanged suggestions. |
| ATN-RSK-ASSESS_RESEARCH_RISK-001 | Disable and physically remove assess_research_risk; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/risk/assess_research_risk/test_traceability.py`; `tests/services/risk/assess_research_risk/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Return authorized versioned risk/limit/admissibility projections with observation time, scope, expiry and provenance. Expected: Wrong-account or stale evidence is denied/unavailable; a model cannot replace missing risk truth. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RSK-ASSESS_RESEARCH_RISK/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(risk): complete FEAT-RSK-ASSESS_RESEARCH_RISK`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-04"></a>

### - [ ] Task 4.04 — FEAT-TRD-MANAGE_EXECUTION_SESSIONS — Preserve governed live/simulation session boundaries

**Status:** `EXISTING_UNVERIFIED` · **Domain:** Trading · **Owner specification:** `app/services/trading/README.md` · **Register first slice:** U2.

**Order prerequisites:** Phase 0 entry gate; no feature-task predecessor.

#### i. Feature and remaining work

A research evaluation uses the correct simulation account/session policy without changing a live route or duplicating Trading authority.

**Reuse:** `app/services/trading/manage_execution_sessions`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-TRD-MANAGE_EXECUTION_SESSIONS-001 | Expose immutable simulation-compatible account/mode/position-policy references for governed evaluations. |
| FR-TRC-TRD-MANAGE_EXECUTION_SESSIONS-002 | Keep deterministic controls usable when Agentic or the research UI is removed. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-TRD-MANAGE_EXECUTION_SESSIONS-001 | Removing FEAT-TRD-MANAGE_EXECUTION_SESSIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-TRD-MANAGE_EXECUTION_SESSIONS-001 | A live session cannot be selected through a simulation-only request; missing policy prerequisites fail before execution. |
| AT-TRD-MANAGE_EXECUTION_SESSIONS-002 | Disable the entire Agentic domain: existing Trading risk checks, session controls and broker serialization remain unchanged. |
| ATN-TRD-MANAGE_EXECUTION_SESSIONS-001 | Disable and physically remove manage_execution_sessions; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/trading/manage_execution_sessions/test_traceability.py`; `tests/services/trading/manage_execution_sessions/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Expose immutable simulation-compatible account/mode/position-policy references for governed evaluations. Expected: A live session cannot be selected through a simulation-only request; missing policy prerequisites fail before execution. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-TRD-MANAGE_EXECUTION_SESSIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(trading): complete FEAT-TRD-MANAGE_EXECUTION_SESSIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-05"></a>

### - [ ] Task 4.05 — FEAT-TRD-MODEL_EXECUTION_POLICIES — Provide pure shared execution-policy descriptors

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Trading · **Owner specification:** `app/services/trading/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.11.

#### i. Feature and remaining work

Simulation and existing execution consumers agree on legal position ownership, intent transitions and scope without sharing a live broker client.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-TRD-MODEL_EXECUTION_POLICIES-001 | Expose versioned netting/hedging, ownership, duplicate/replace/reversal and permitted transition semantics as typed pure descriptors. |
| FR-TRC-TRD-MODEL_EXECUTION_POLICIES-002 | Qualify native-compatible pure helpers with exact arithmetic and explicit input/state bounds. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-TRD-MODEL_EXECUTION_POLICIES-001 | Removing FEAT-TRD-MODEL_EXECUTION_POLICIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-TRD-MODEL_EXECUTION_POLICIES-001 | A simulator request cannot widen strategy/account scope; duplicate and replacement fixtures use the same owner-declared policy. |
| AT-TRD-MODEL_EXECUTION_POLICIES-002 | Reference/native fixtures agree without network calls, broker credentials or per-tick capability resolution. |
| ATN-TRD-MODEL_EXECUTION_POLICIES-001 | Disable and physically remove model_execution_policies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/trading/model_execution_policies/test_traceability.py`; `tests/services/trading/model_execution_policies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Expose versioned netting/hedging, ownership, duplicate/replace/reversal and permitted transition semantics as typed pure descriptors. Expected: A simulator request cannot widen strategy/account scope; duplicate and replacement fixtures use the same owner-declared policy. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-TRD-MODEL_EXECUTION_POLICIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(trading): complete FEAT-TRD-MODEL_EXECUTION_POLICIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-06"></a>

### - [ ] Task 4.06 — FEAT-SIM-MODEL_TICKS — Produce ordered recorded or generated execution ticks

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.02, 2.16, 2.20.

#### i. Feature and remaining work

Every simulation consumes the selected method’s complete event stream with truthful evidence class and ordering.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-MODEL_TICKS-001 | Implement recorded replay and generated replay as registered methods with versioned algorithm/configuration, source, seed, density/timing/path/spread/gap/quantization policy. |
| FR-TRC-SIM-MODEL_TICKS-002 | Preserve source sequence and use a pinned equal-time cross-source/timer ordering; finalize half-open bars before the next interval’s observations. |
| FR-TRC-SIM-MODEL_TICKS-003 | Count/hash actual emitted and consumed observations and expose partial coverage on cancellation. |
| FR-TRC-SIM-MODEL_TICKS-004 | Expose only the generated path prefix to strategy state and reject recorded-microstructure nodes on incompatible methods. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-MODEL_TICKS-001 | Streams are bounded by event, byte and time limits and carry complete cursor/PRNG/event-subphase state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-MODEL_TICKS-001 | Generated methods cannot activate without a complete algorithm artifact and goldens; no unrequested method is selected by default. |
| AT-SIM-MODEL_TICKS-002 | Equal-time groups split across chunks and multi-timeframe close boundaries produce identical event order and available-bar snapshots. |
| AT-SIM-MODEL_TICKS-003 | Source/emitted/consumed counters reconcile; thinning ticks, shortening history or substituting an OHLC collision rule fails acceptance. |
| AT-SIM-MODEL_TICKS-004 | A strategy cannot read the future source bar’s final high/low before simulated closure; last-only feeds never gain fabricated bid/ask evidence. |
| ATN-SIM-MODEL_TICKS-001 | Chunk sizes 1,17,65,536 and output-buffer exhaustion produce identical order/count/hash with no event loss or duplication. |


**Acceptance test targets:** `tests/services/simulator/model_ticks/test_traceability.py`; `tests/services/simulator/model_ticks/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Implement recorded replay and generated replay as registered methods with versioned algorithm/configuration, source, seed, density/timing/path/spread/gap/quantization policy. Expected: Generated methods cannot activate without a complete algorithm artifact and goldens; no unrequested method is selected by default. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-MODEL_TICKS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-MODEL_TICKS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-07"></a>

### - [ ] Task 4.07 — FEAT-ANA-COMPUTE_METRICS — Compute versioned canonical performance and risk metrics

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.12.

#### i. Feature and remaining work

Every decision-grade number has a reproducible formula, sample, unit and undefined reason.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-COMPUTE_METRICS-001 | Register each metric’s formula/version, units, sample, denominator, required inputs, rounding and typed undefined cases before enabling its column. |
| FR-TRC-ANA-COMPUTE_METRICS-002 | Compute the entire CAT-METRICS baseline with costs counted once and open P&L/external cashflows distinguished. |
| FR-TRC-ANA-COMPUTE_METRICS-003 | Expose owner-qualified incremental reducers where exact, and admitted artifact-backed calculations where sorting/history is required. |
| FR-TRC-ANA-COMPUTE_METRICS-004 | Bind all values to result/input/definition/runtime hashes and compare reference/native implementations. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-COMPUTE_METRICS-001 | Removing FEAT-ANA-COMPUTE_METRICS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-COMPUTE_METRICS-001 | No-loss Profit Factor, fewer-than-two-period Sharpe, zero-variance SQN and invalid/nonpositive CAGR inputs are undefined, never invented finite values. |
| AT-ANA-COMPUTE_METRICS-002 | Net profit does not subtract already-filled slippage twice; money/percent/pips/R and balance/equity drawdown remain distinct. |
| AT-ANA-COMPUTE_METRICS-003 | Tick-path extrema are not calculated from display-downsampled equity; summary retention cannot omit inputs required by a mandatory metric. |
| AT-ANA-COMPUTE_METRICS-004 | Exact fields match exactly and only declared float fields use tolerances; a formula change receives a new identity. |
| ATN-ANA-COMPUTE_METRICS-001 | Disable and physically remove compute_metrics; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/compute_metrics/test_traceability.py`; `tests/services/analytics/compute_metrics/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register each metric’s formula/version, units, sample, denominator, required inputs, rounding and typed undefined cases before enabling its column. Expected: No-loss Profit Factor, fewer-than-two-period Sharpe, zero-variance SQN and invalid/nonpositive CAGR inputs are undefined, never invented finite values. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-COMPUTE_METRICS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-COMPUTE_METRICS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-08"></a>

### - [ ] Task 4.08 — FEAT-SIM-CONFIGURE_ENGINE — Validate immutable simulation profiles

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.11, 2.20, 3.13, 4.02, 4.05, 4.06, 4.07.

#### i. Feature and remaining work

A backtest starts with an explicit tick method, costs, sample, account state, output profile and resource estimate.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-CONFIGURE_ENGINE-001 | Require a registered recorded/generated tick method or an explicitly selected saved profile that supplies it. |
| FR-TRC-SIM-CONFIGURE_ENGINE-002 | Pin Strategy plan, Data binding, instrument/calendar/cost/risk/account/numerical/runtime versions, seed and initial state. |
| FR-TRC-SIM-CONFIGURE_ENGINE-003 | Validate output retention against required metrics/qualification evidence and estimate finite work, memory, disk and cancellation boundaries. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-CONFIGURE_ENGINE-001 | Removing FEAT-SIM-CONFIGURE_ENGINE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-CONFIGURE_ENGINE-001 | Omitting the method is a validation error; M1/H1 chart timeframes never silently choose a bar-only engine. |
| AT-SIM-CONFIGURE_ENGINE-002 | A later data/profile/provider change is reported as a different evaluation identity and cannot modify an accepted run. |
| AT-SIM-CONFIGURE_ENGINE-003 | A summary profile missing required MAE/MFE evidence is rejected or produces an explicitly authorized linked replay plan, never fabricated metrics. |
| ATN-SIM-CONFIGURE_ENGINE-001 | Disable and physically remove configure_engine; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/simulator/configure_engine/test_traceability.py`; `tests/services/simulator/configure_engine/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Require a registered recorded/generated tick method or an explicitly selected saved profile that supplies it. Expected: Omitting the method is a validation error; M1/H1 chart timeframes never silently choose a bar-only engine. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-CONFIGURE_ENGINE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-CONFIGURE_ENGINE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-09"></a>

### - [ ] Task 4.09 — FEAT-SIM-EXECUTE_TICKS — Execute the native chronological backtest

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.22, 2.12, 3.01, 3.02, 3.03, 3.04, 3.05, 3.06, 4.02, 4.05, 4.06, 4.07, 4.08.

#### i. Feature and remaining work

A saved strategy is evaluated with tick-level fills, protective exits, cash, positions and valuation without interpreter-loop bottlenecks or changed semantics.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-EXECUTE_TICKS-001 | Lower the target-neutral plan into typed instruction/operand/parameter/state buffers and execute all eligible events in a compiled nopython loop. |
| FR-TRC-SIM-EXECUTE_TICKS-002 | Process quote update → previously active orders/exits → accounting/causal indicators → subscribed rules → future eligible intents in the pinned order. |
| FR-TRC-SIM-EXECUTE_TICKS-003 | Preserve exact money/quantity atoms, checked intermediates and declared Float64 tolerances with fastmath=False. |
| FR-TRC-SIM-EXECUTE_TICKS-004 | Carry full positions/orders/cash/exposure/rolling bars/quotes/timers/callbacks/PRNG/cursors/subphase and committed output parts across slices/checkpoints. |
| FR-TRC-SIM-EXECUTE_TICKS-005 | Execute all single/Builder/Retester/parameter/WF/portfolio/AI simulation callers through this same selected-method contract. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-EXECUTE_TICKS-001 | Use at most 65,536 events per native slice, further bounded by bytes and adaptation toward a 100 ms slice budget. |
| NFR-TRC-SIM-EXECUTE_TICKS-002 | Meet qualified native comparator and scale gates without changing workload or output obligations. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-EXECUTE_TICKS-001 | Compiled-signature/profile checks show no per-tick Pydantic, dictionary traversal, pandas row iteration, capability resolution, SQL, SSE or model call. |
| AT-SIM-EXECUTE_TICKS-002 | A new intent cannot fill on its decision tick; market/stop gaps/limit-or-better/pending expiry/replace/netting/hedging/trailing/time-exit fixtures match the reference. |
| AT-SIM-EXECUTE_TICKS-003 | Overflow and nonrepresentable scales produce typed diagnostics or preselected qualified wider arithmetic; no wrapping or binary-float money fallback occurs. |
| AT-SIM-EXECUTE_TICKS-004 | Restart and OUTPUT_FULL replay neither duplicate fills nor warm up/reset the strategy per chunk; incompatible hashes/runtime checkpoints fail. |
| AT-SIM-EXECUTE_TICKS-005 | Caller integration fixtures expose no separate reduced-fidelity engine, private sibling import or unaccounted trial. |
| ATN-SIM-EXECUTE_TICKS-001 | Complex-plan cancellation reaches quiescence p95 ≤2 s and retains the exact next event/subphase. |
| ATN-SIM-EXECUTE_TICKS-002 | PERF-G01–G04: exact/tolerance equivalence; warm compute ≤1.5× and same-harness full run ≤2× C++ comparator; 10× fixed-state input costs ≤12× compute; every 20-year method meets its pre-frozen absolute budget. |


**Acceptance test targets:** `tests/services/simulator/execute_ticks/test_traceability.py`; `tests/services/simulator/execute_ticks/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Lower the target-neutral plan into typed instruction/operand/parameter/state buffers and execute all eligible events in a compiled nopython loop. Expected: Compiled-signature/profile checks show no per-tick Pydantic, dictionary traversal, pandas row iteration, capability resolution, SQL, SSE or model call. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-EXECUTE_TICKS/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-IND-CALCULATE_MARKET_PROFILES (Task 13.01, Phase 13); FEAT-RES-INFER_MODELS (Task 14.03, Phase 14). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-EXECUTE_TICKS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-10"></a>

### - [ ] Task 4.10 — FEAT-SIM-COMMIT_RESULTS — Publish complete simulation result evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.17, 1.18, 4.07, 4.09.

#### i. Feature and remaining work

A completed result has verified counts, artifacts and provenance, while partial work cannot masquerade as qualification evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-COMMIT_RESULTS-001 | Stream required ledgers/series/reducers into staged immutable parts and verify schema/count/hash before result metadata commitment. |
| FR-TRC-SIM-COMMIT_RESULTS-002 | Publish research-summary/review/diagnostic output profiles with retained/derivable/unavailable fields and exact consumed work counts. |
| FR-TRC-SIM-COMMIT_RESULTS-003 | Keep source Strategy/Data/config/seed/provider hashes, completeness, warnings, event and trade counts and owner metric versions in every result. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-COMMIT_RESULTS-001 | Removing FEAT-SIM-COMMIT_RESULTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-COMMIT_RESULTS-001 | Failure after byte promotion but before metadata commit leaves a reconcilable orphan, never an active result pointing at partial bytes. |
| AT-SIM-COMMIT_RESULTS-002 | Summary mode does not change fills or required metrics; absent excursion/series data is unavailable, not zero. |
| AT-SIM-COMMIT_RESULTS-003 | A cancelled/fenced attempt cannot publish an accepted final result; partial outputs remain explicitly separate from final qualification. |
| ATN-SIM-COMMIT_RESULTS-001 | Disable and physically remove commit_results; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/simulator/commit_results/test_traceability.py`; `tests/services/simulator/commit_results/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Stream required ledgers/series/reducers into staged immutable parts and verify schema/count/hash before result metadata commitment. Expected: Failure after byte promotion but before metadata commit leaves a reconcilable orphan, never an active result pointing at partial bytes. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-COMMIT_RESULTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-COMMIT_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-11"></a>

### - [ ] Task 4.11 — FEAT-IFACE-OPERATE_SIMULATIONS — Expose explicit simulation configuration and run commands

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.08, 4.08, 4.09, 4.10.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_SIMULATIONS-001 | Validate/translate pinned simulation inputs and return the owner’s actual job/run handle. |
| FR-TRC-IFACE-OPERATE_SIMULATIONS-002 | Expose run/result/partial/cancel diagnostics and bounded progress unchanged. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_SIMULATIONS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_SIMULATIONS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_SIMULATIONS-001 | An omitted method is rejected by the owner and not replaced by a gateway default. |
| AT-IFACE-OPERATE_SIMULATIONS-002 | No fill/cost/indicator/metric calculation or hidden precision reduction occurs in transport. |
| ATN-IFACE-OPERATE_SIMULATIONS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_SIMULATIONS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_simulations/test_traceability.py`; `tests/services/interfaces/operate_simulations/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Validate/translate pinned simulation inputs and return the owner’s actual job/run handle. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: An omitted method is rejected by the owner and not replaced by a gateway default. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_SIMULATIONS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.18 (FEAT-UI-STRATEGY_STUDIO). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_SIMULATIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-12"></a>

### - [ ] Task 4.12 — FEAT-SIM-CACHE_EVALUATIONS — Reuse exact evaluations without creating false evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.04, 1.14, 4.10.

#### i. Feature and remaining work

Repeated identical evaluation requests can reuse a verified result while retaining authorization, sample and trial accounting.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-CACHE_EVALUATIONS-001 | Key cached results by strategy semantics/effective parameters, data/tick method/configuration/seed, costs, initial state, numerical/runtime, metrics and output profile. |
| FR-TRC-SIM-CACHE_EVALUATIONS-002 | Reauthorize cache reads and record cache-hit accounting separately from fresh computation and holdout access. |
| FR-TRC-SIM-CACHE_EVALUATIONS-003 | Evict only unpinned entries under finite byte/count limits and generation-aware invalidation. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-CACHE_EVALUATIONS-001 | Removing FEAT-SIM-CACHE_EVALUATIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-CACHE_EVALUATIONS-001 | Changing any semantic field misses the cache; unrelated display metadata does not falsely create independent evidence. |
| AT-SIM-CACHE_EVALUATIONS-002 | A cached result from another account or withdrawn data license is denied; a hit cannot reset a campaign or become a new completed simulation. |
| AT-SIM-CACHE_EVALUATIONS-003 | An active result reader remains valid during eviction; corrupt/incompatible entries are rejected and safely recomputed only under fresh admission. |
| ATN-SIM-CACHE_EVALUATIONS-001 | Disable and physically remove cache_evaluations; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/simulator/cache_evaluations/test_traceability.py`; `tests/services/simulator/cache_evaluations/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Key cached results by strategy semantics/effective parameters, data/tick method/configuration/seed, costs, initial state, numerical/runtime, metrics and output profile. Expected: Changing any semantic field misses the cache; unrelated display metadata does not falsely create independent evidence. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-CACHE_EVALUATIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-CACHE_EVALUATIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-13"></a>

### - [ ] Task 4.13 — FEAT-ANA-QUERY_RESULTS — Query bounded result and trade collections

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.04, 1.14, 1.17, 4.10.

#### i. Feature and remaining work

A user can inspect very large result populations without full download or page drift.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-QUERY_RESULTS-001 | Validate typed filter AST, stable identity tie-break sort, projection and snapshot cursor with page_size ≤200. |
| FR-TRC-ANA-QUERY_RESULTS-002 | Query only requested columns/ranges with declared null semantics, schema versions and authorized result references. |
| FR-TRC-ANA-QUERY_RESULTS-003 | Resolve bulk population tokens plus inclusions/exclusions on the server and report exact count/identity. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-QUERY_RESULTS-001 | Removing FEAT-ANA-QUERY_RESULTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-QUERY_RESULTS-001 | Unknown columns/operators or raw SQL are rejected; expired tokens return typed resync rather than unstable continuation. |
| AT-ANA-QUERY_RESULTS-002 | A 1M-result/10M-trade fixture keeps query memory bounded by page/spill reservation and never materializes the whole collection in the browser. |
| AT-ANA-QUERY_RESULTS-003 | Select-all across pages operates on the pinned snapshot and does not require a client array of a million IDs. |
| ATN-ANA-QUERY_RESULTS-001 | Disable and physically remove query_results; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/query_results/test_traceability.py`; `tests/services/analytics/query_results/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate typed filter AST, stable identity tie-break sort, projection and snapshot cursor with page_size ≤200. Expected: Unknown columns/operators or raw SQL are rejected; expired tokens return typed resync rather than unstable continuation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-QUERY_RESULTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-QUERY_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-14"></a>

### - [ ] Task 4.14 — FEAT-ANA-DATABANK_MEMBERSHIP — Manage databank membership and bulk changes

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.09, 4.13.

#### i. Feature and remaining work

Research results can be organized, selected and moved without confusing collection membership with ownership of the underlying evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-DATABANK_MEMBERSHIP-001 | Create/rename/clone/archive/delete databanks and version saved column/sort/filter/pin/visibility views. |
| FR-TRC-ANA-DATABANK_MEMBERSHIP-002 | Resolve and preview move/copy/remove/rename/tag/note operations against immutable selection tokens and apply the declared atomic/per-item policy. |
| FR-TRC-ANA-DATABANK_MEMBERSHIP-003 | Commit accepted result membership once, keeping intermediate/rejected results and underlying artifact retention separate. |
| FR-TRC-ANA-DATABANK_MEMBERSHIP-004 | Delegate retest/optimize/strategy edit/merge/portfolio split/export actions through typed owner handoffs. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-DATABANK_MEMBERSHIP-001 | Removing FEAT-ANA-DATABANK_MEMBERSHIP withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-DATABANK_MEMBERSHIP-001 | Missing plugin columns degrade explicitly; name collisions and stale revisions produce an actionable conflict. |
| AT-ANA-DATABANK_MEMBERSHIP-002 | Default all-or-nothing failures leave membership unchanged; even in per-item mode each move is atomic and audited. |
| AT-ANA-DATABANK_MEMBERSHIP-003 | Retry after commitment adds no duplicate member; deleting a bank leaves independently referenced results intact. |
| AT-ANA-DATABANK_MEMBERSHIP-004 | A ribbon command never copies hidden mutable state or implements another domain’s business rule. |
| ATN-ANA-DATABANK_MEMBERSHIP-001 | Disable and physically remove databank_membership; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/databank_membership/test_traceability.py`; `tests/services/analytics/databank_membership/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/rename/clone/archive/delete databanks and version saved column/sort/filter/pin/visibility views. Expected: Missing plugin columns degrade explicitly; name collisions and stale revisions produce an actionable conflict. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-DATABANK_MEMBERSHIP/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-DATABANK_MEMBERSHIP`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-15"></a>

### - [ ] Task 4.15 — FEAT-ANA-ANALYZE_TRADES — Project trade details and grouped behavior

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.20, 4.07, 4.13.

#### i. Feature and remaining work

A user can explain trade outcomes by the same stable trade identities, periods and dimensions across all panels.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-ANALYZE_TRADES-001 | Provide trade/order/position/signal references, timestamp/direction/size/price/cost/outcome/exit/MAE/MFE/R/sample fields with explicit availability. |
| FR-TRC-ANA-ANALYZE_TRADES-002 | Aggregate by open/close period, weekday/hour/session/month/year/duration/direction/size/rule/close type/streak/symbol/timeframe/parameter bucket. |
| FR-TRC-ANA-ANALYZE_TRADES-003 | Return linked trade/market/equity selections and previous/next navigation through stable domain IDs. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-ANALYZE_TRADES-001 | Removing FEAT-ANA-ANALYZE_TRADES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-ANALYZE_TRADES-001 | Missing initial risk yields unavailable R; absent tick excursions are not zero; expired orders retain their distinct record type. |
| AT-ANA-ANALYZE_TRADES-002 | Changing open-time to close-time basis changes a named projection, not source records; timezone/calendar is pinned. |
| AT-ANA-ANALYZE_TRADES-003 | The selected ticket refers to the same trade in each view; missing backing market data produces an authorized resolution action, not a similar substituted series. |
| ATN-ANA-ANALYZE_TRADES-001 | Disable and physically remove analyze_trades; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/analyze_trades/test_traceability.py`; `tests/services/analytics/analyze_trades/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Provide trade/order/position/signal references, timestamp/direction/size/price/cost/outcome/exit/MAE/MFE/R/sample fields with explicit availability. Expected: Missing initial risk yields unavailable R; absent tick excursions are not zero; expired orders retain their distinct record type. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-ANALYZE_TRADES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-ANALYZE_TRADES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-16"></a>

### - [ ] Task 4.16 — FEAT-ANA-PROJECT_SERIES — Provide exact and bounded visual result series

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 2.23, 4.07, 4.13.

#### i. Feature and remaining work

Charts receive correctly labelled equity, drawdown, benchmark and overlay windows without recomputing trading math.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-PROJECT_SERIES-001 | Expose equity/balance/drawdown/benchmark/long-short/sample/periodic-return/rolling metric series with unit, currency, calendar, sample, count and provenance. |
| FR-TRC-ANA-PROJECT_SERIES-002 | Produce bounded levels/chunks with declared extrema/aggregation/sampling semantics and exact source references. |
| FR-TRC-ANA-PROJECT_SERIES-003 | Align overlays and typed time/trade-index/parameter coordinates without silent conversion. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-PROJECT_SERIES-001 | Removing FEAT-ANA-PROJECT_SERIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-PROJECT_SERIES-001 | No benchmark is hard-coded; incompatible currencies/calendars or missing data are explicit. |
| AT-ANA-PROJECT_SERIES-002 | Peak/trough-preserving LOD fixtures match the declared rule; metrics computed from exact source are unchanged by chart zoom. |
| AT-ANA-PROJECT_SERIES-003 | Trade-index and timestamp selections cannot be interchanged; session gaps and synthetic intervals remain labelled. |
| ATN-ANA-PROJECT_SERIES-001 | Disable and physically remove project_series; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/project_series/test_traceability.py`; `tests/services/analytics/project_series/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Expose equity/balance/drawdown/benchmark/long-short/sample/periodic-return/rolling metric series with unit, currency, calendar, sample, count and provenance. Expected: No benchmark is hard-coded; incompatible currencies/calendars or missing data are explicit. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-PROJECT_SERIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-PROJECT_SERIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-17"></a>

### - [ ] Task 4.17 — FEAT-ANA-COMPARE_RESULTS — Compare compatible result evidence and configurations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 4.07, 4.13.

#### i. Feature and remaining work

A user can see real changes between runs while distinguishing strategy, data, cost, sample and metric differences.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-COMPARE_RESULTS-001 | Align two or more results by typed metric/sample/currency/calendar/definition and expose missing or incompatible fields. |
| FR-TRC-ANA-COMPARE_RESULTS-002 | Compare run-time configuration with current Strategy/profile settings and return a typed revision diff. |
| FR-TRC-ANA-COMPARE_RESULTS-003 | Compare baseline/retest/WF/optimization outcomes with preserved failed/partial/undefined cases. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-COMPARE_RESULTS-001 | Removing FEAT-ANA-COMPARE_RESULTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-COMPARE_RESULTS-001 | No implicit currency conversion or incompatible-definition equality is reported; original values remain visible. |
| AT-ANA-COMPARE_RESULTS-002 | Applying the diff delegates to Strategy with expected revision and cannot overwrite either compared result. |
| AT-ANA-COMPARE_RESULTS-003 | A missing metric is not zero and an incomplete scenario cannot be relabelled passed. |
| ATN-ANA-COMPARE_RESULTS-001 | Disable and physically remove compare_results; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/compare_results/test_traceability.py`; `tests/services/analytics/compare_results/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Align two or more results by typed metric/sample/currency/calendar/definition and expose missing or incompatible fields. Expected: No implicit currency conversion or incompatible-definition equality is reported; original values remain visible. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-COMPARE_RESULTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-COMPARE_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-18"></a>

### - [ ] Task 4.18 — FEAT-ANA-EXCHANGE_RESULTS — Export and import attributed research results and reports

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.17, 4.07, 4.13.

#### i. Feature and remaining work

Results can be inspected outside the application with their exact source, metric and sampling context intact.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-EXCHANGE_RESULTS-001 | Export server-resolved result/trade projections and versioned HTML/PDF/CSV/Parquet/Arrow/native report artifacts with filters, units, timezone and hashes. |
| FR-TRC-ANA-EXCHANGE_RESULTS-002 | Import typed result metadata/ledgers through explicit schema/units/sample validation and preserve source metrics separately from newly calculated native metrics. |
| FR-TRC-ANA-EXCHANGE_RESULTS-003 | Register report templates and preserve fallback/compatibility behavior without changing underlying result content. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-EXCHANGE_RESULTS-001 | Removing FEAT-ANA-EXCHANGE_RESULTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-EXCHANGE_RESULTS-001 | Output includes the requested population beyond the viewport; CSV formula injection and unsafe markup are contained. |
| AT-ANA-EXCHANGE_RESULTS-002 | An external Sharpe convention is never relabelled as the native definition without proof; missing columns remain unavailable. |
| AT-ANA-EXCHANGE_RESULTS-003 | Removing a template still permits a safe built-in report; the original result hash remains unchanged. |
| ATN-ANA-EXCHANGE_RESULTS-001 | Disable and physically remove exchange_results; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/exchange_results/test_traceability.py`; `tests/services/analytics/exchange_results/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Export server-resolved result/trade projections and versioned HTML/PDF/CSV/Parquet/Arrow/native report artifacts with filters, units, timezone and hashes. Expected: Output includes the requested population beyond the viewport; CSV formula injection and unsafe markup are contained. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-EXCHANGE_RESULTS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.16 (FEAT-STRAT-EXCHANGE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-EXCHANGE_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-19"></a>

### - [ ] Task 4.19 — FEAT-IFACE-OPERATE_RESULTS — Expose databanks, results and analysis

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.08, 4.13, 4.14, 4.15, 4.16, 4.17, 4.18.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_RESULTS-001 | Translate typed snapshot/cursor/filter/projection/selection-token queries and governed bulk commands. |
| FR-TRC-IFACE-OPERATE_RESULTS-002 | Expose metric/series/template/compatibility descriptors, immutable exports and plugin projections. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_RESULTS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_RESULTS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_RESULTS-001 | page_size >200 and raw SQL are denied; server selection semantics survive transport. |
| AT-IFACE-OPERATE_RESULTS-002 | Imported/unverified/partial/sampled provenance remains visible; no gateway metric recomputation occurs. |
| ATN-IFACE-OPERATE_RESULTS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_RESULTS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_results/test_traceability.py`; `tests/services/interfaces/operate_results/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate typed snapshot/cursor/filter/projection/selection-token queries and governed bulk commands. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: page_size >200 and raw SQL are denied; server selection semantics survive transport. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_RESULTS/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-ANA-FILTER_CORRELATION (Task 10.03, Phase 10); FEAT-ANA-PROVIDE_CUSTOM_ANALYSIS (Task 12.07, Phase 12). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

**This provider also qualifies earlier consumers:** Task 2.32 (FEAT-UI-04). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-20"></a>

### - [ ] Task 4.20 — FEAT-UI-27 — Configure and observe a canonical backtest

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 1.07, 4.09, 4.11, 4.19.

#### i. Feature and remaining work

A user can backtest the selected strategy with explicit execution fidelity and see the real run/result outcome.

**Reuse:** `app/ui/src/widgets/simulator`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-27-001 | Present strategy revision/parameters, primary/additional data, tick-method evidence class/coverage, costs, account, sample, output and resource preview. |
| FR-TRC-UI-27-002 | Submit one governed owner request, observe progress/log/warnings and expose supported cancel/pause/retry. |
| FR-TRC-UI-27-003 | Open the committed Analytics result by stable ID and retain partial/unavailable/failed states. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-27-001 | Removing FEAT-UI-27 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-27-001 | No method is silently selected; actual source/emitted/estimated tick counts are labelled correctly. |
| AT-UI-27-002 | Double-click Start returns one run; pause waits for acknowledgement/checkpoint; retry creates the owner’s linked identity. |
| AT-UI-27-003 | A browser timeout or closed panel cannot be relabelled a failed/completed simulation without owner evidence. |
| ATN-UI-27-001 | Disable and physically remove simulator; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/widgets/simulator/__tests__/traceability.test.tsx`; `app/ui/src/widgets/simulator/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Configure and observe a canonical backtest). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: No method is silently selected; actual source/emitted/estimated tick counts are labelled correctly. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-27/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-27`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-21"></a>

### - [ ] Task 4.21 — FEAT-UI-32 — Compose the result inspection workspace

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 4.19.

#### i. Feature and remaining work

A selected result opens only compatible registered views with clear completeness and provenance.

**Reuse:** `app/ui/src/widgets/analytics`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-32-001 | Discover compatible result views by result kind/schema/capability and restore safe per-view layout/selection. |
| FR-TRC-UI-32-002 | Expose result/config/data/metric/method/sample/precision/partial/imported provenance and deep links. |
| FR-TRC-UI-32-003 | Coordinate typed stable selections among independent panels without shared mutable domain state. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-32-001 | Removing FEAT-UI-32 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-32-001 | Removing one panel/provider produces a named unavailable view without breaking other result views. |
| AT-UI-32-002 | Current Strategy settings cannot silently replace the run-time snapshot; imported results keep source attribution. |
| AT-UI-32-003 | A trade/result/window selection retains the same owner identity across views and is cleared safely when inaccessible. |
| ATN-UI-32-001 | Disable and physically remove analytics; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/widgets/analytics/__tests__/traceability.test.tsx`; `app/ui/src/widgets/analytics/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Compose the result inspection workspace). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Removing one panel/provider produces a named unavailable view without breaking other result views. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-32/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-32`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-22"></a>

### - [ ] Task 4.22 — FEAT-UI-DATABANK_GRID — Organize and act on a databank

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 1.06, 4.19.

#### i. Feature and remaining work

Browse huge result sets and perform exact, reviewable bulk actions without destructive ambiguity.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-DATABANK_GRID-001 | Render the typed metric/metadata catalogue and persisted views with server query tokens and all supported ribbon/context-menu controls. |
| FR-TRC-UI-DATABANK_GRID-002 | Preview bulk object/count/conflict/atomicity/dependency effects and bind confirmation to the exact resolved population. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-DATABANK_GRID-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-DATABANK_GRID-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-DATABANK_GRID-001 | Removing a contributed column does not discard other view settings or change data; visible-row count is never substituted for selected population count. |
| AT-UI-DATABANK_GRID-002 | A move is atomic per item and default transaction-wide policy is preserved; row removal is not underlying result deletion. |
| ATN-UI-DATABANK_GRID-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-DATABANK_GRID-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/databank-grid/__tests__/traceability.test.tsx`; `app/ui/src/widgets/databank-grid/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Organize and act on a databank). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Removing a contributed column does not discard other view settings or change data; visible-row count is never substituted for selected population count. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-DATABANK_GRID/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-DATABANK_GRID`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-23"></a>

### - [ ] Task 4.23 — FEAT-UI-RESULT_OVERVIEW — Read a provenance-rich result summary

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 4.19.

#### i. Feature and remaining work

Understand performance with units, samples, undefined cases and template fallback visible.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-RESULT_OVERVIEW-001 | Render canonical/derived/presentation-only fields distinctly with source definition/version, units, precision and null reasons. |
| FR-TRC-UI-RESULT_OVERVIEW-002 | Select versioned report/view templates and preserve a safe built-in fallback. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-RESULT_OVERVIEW-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-RESULT_OVERVIEW-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-RESULT_OVERVIEW-001 | No-loss Profit Factor and undefined Sharpe remain unavailable; imported or incomplete data cannot appear natively qualified. |
| AT-UI-RESULT_OVERVIEW-002 | A missing template/provider changes presentation availability only, not the result’s values or hash. |
| ATN-UI-RESULT_OVERVIEW-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-RESULT_OVERVIEW-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/result-overview/__tests__/traceability.test.tsx`; `app/ui/src/widgets/result-overview/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Read a provenance-rich result summary). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: No-loss Profit Factor and undefined Sharpe remain unavailable; imported or incomplete data cannot appear natively qualified. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-RESULT_OVERVIEW/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-RESULT_OVERVIEW`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-24"></a>

### - [ ] Task 4.24 — FEAT-UI-TRADE_LIST — Inspect and select individual trades

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 1.06, 4.15, 4.19.

#### i. Feature and remaining work

Follow one trade consistently from pageable ledger through detail, equity and market views.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-TRADE_LIST-001 | Use stable trade IDs and typed sample/time/column filters with bounded paging. |
| FR-TRC-UI-TRADE_LIST-002 | Publish typed selections and export the server-resolved projection, not just visible rows. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-TRADE_LIST-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-TRADE_LIST-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-TRADE_LIST-001 | Cross-page selection opens the exact ticket; missing R/MAE/MFE is not displayed as zero. |
| AT-UI-TRADE_LIST-002 | Linked panels receive the same trade identity; CSV output respects formula-injection protection and manifest counts. |
| ATN-UI-TRADE_LIST-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-TRADE_LIST-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/trade-list/__tests__/traceability.test.tsx`; `app/ui/src/widgets/trade-list/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect and select individual trades). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Cross-page selection opens the exact ticket; missing R/MAE/MFE is not displayed as zero. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-TRADE_LIST/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-TRADE_LIST`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-25"></a>

### - [ ] Task 4.25 — FEAT-UI-EQUITY_CHART — Inspect equity, drawdown and benchmark paths

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 4.16, 4.19.

#### i. Feature and remaining work

Explore a result’s time path while knowing which series, aggregation and units are displayed.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-EQUITY_CHART-001 | Render owner-projected equity/balance/benchmark/drawdown/volume layers with source/sampling/precision labels. |
| FR-TRC-UI-EQUITY_CHART-002 | Synchronize cursor/range/trade selections with bounded buffers and accessible equivalent table. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-EQUITY_CHART-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-EQUITY_CHART-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-EQUITY_CHART-001 | Zoom/downsampling cannot alter risk metrics; time and trade-index axes are not silently interchanged. |
| AT-UI-EQUITY_CHART-002 | Keyboard and non-GPU paths expose the same selected values; unmount releases decoding workers and listeners. |
| ATN-UI-EQUITY_CHART-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-EQUITY_CHART-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/equity-chart/__tests__/traceability.test.tsx`; `app/ui/src/widgets/equity-chart/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect equity, drawdown and benchmark paths). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Zoom/downsampling cannot alter risk metrics; time and trade-index axes are not silently interchanged. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-EQUITY_CHART/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-EQUITY_CHART`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-26"></a>

### - [ ] Task 4.26 — FEAT-UI-TRADE_ANALYSIS — Compare trade behavior across dimensions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 4.15, 4.19.

#### i. Feature and remaining work

Inspect grouped trade behavior using an explicit time basis and canonical metrics.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-TRADE_ANALYSIS-001 | Configure bounded analysis slots from compatible owner dimensions/metrics, showing selected sample/currency/calendar/time basis. |
| FR-TRC-UI-TRADE_ANALYSIS-002 | Drill through a group to its exact trade population and compare period/distribution panels. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-TRADE_ANALYSIS-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-TRADE_ANALYSIS-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-TRADE_ANALYSIS-001 | Open/close-time changes request a new projection and do not move source trades; missing categories are explicit. |
| AT-UI-TRADE_ANALYSIS-002 | A group selection resolves the same server snapshot; display sorting does not recompute the statistic. |
| ATN-UI-TRADE_ANALYSIS-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-TRADE_ANALYSIS-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/trade-analysis/__tests__/traceability.test.tsx`; `app/ui/src/widgets/trade-analysis/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Compare trade behavior across dimensions). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Open/close-time changes request a new projection and do not move source trades; missing categories are explicit. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-TRADE_ANALYSIS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-TRADE_ANALYSIS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-4-27"></a>

### - [ ] Task 4.27 — FEAT-UI-TRADES_ON_CHART — Inspect fills against their actual market context

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 2.20, 4.19.

#### i. Feature and remaining work

See how a chosen trade aligns with the exact price history, indicators and execution evidence used by its run.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-TRADES_ON_CHART-001 | Resolve the exact run-bound market series and selected trade/position references before rendering overlays. |
| FR-TRC-UI-TRADES_ON_CHART-002 | Display generated/recorded method evidence and supported overlays without browser execution reconstruction. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-TRADES_ON_CHART-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-TRADES_ON_CHART-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-TRADES_ON_CHART-001 | Missing data produces an authorized resolution action; a similarly named series is never substituted. |
| AT-UI-TRADES_ON_CHART-002 | A generated path stays labelled modeled evidence; unretained excursions remain unavailable. |
| ATN-UI-TRADES_ON_CHART-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-TRADES_ON_CHART-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/trades-on-chart/__tests__/traceability.test.tsx`; `app/ui/src/widgets/trades-on-chart/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect fills against their actual market context). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Missing data produces an authorized resolution action; a similarly named series is never substituted. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-TRADES_ON_CHART/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P04 — Select the saved EMA strategy and versioned data, run an explicit recorded/generated tick backtest, reconnect during execution, inspect metrics/trades/equity, move selected databank members and export a provenance-complete result. Publish `docs/dev/evidence/phases/phase-04.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-TRADES_ON_CHART`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-5"></a>

## Phase 5 — Contextual Chat Bot and inspectable Agentic evidence

**Feature tasks: 11.** Conversation storage + governed workflow/context/evaluation/claim/synthesis/assistant providers → Agentic gateway + page context → Chat Bot and run inspector. Model unavailability is a tested degraded case, not a simulated successful reply.

**Visible completion:** Ask Chat Bot about a selected real result; show refreshed authorized evidence, specialist attribution, claim references, and run-inspector detail in the same conversation.

**Phase evidence:** `tests/ui/e2e/research/phase_05.spec.ts` and `docs/dev/evidence/phases/phase-05.json`, owned by Task 5.11. All prior affected UI/data/recovery regressions remain required.

<a id="task-5-01"></a>

### - [ ] Task 5.01 — FEAT-UI-15 — Capture current authorized widget context

**Status:** `PARTIAL` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02.

#### i. Feature and remaining work

Chat and governed previews refer to exactly what the user selected on the current page, not stale or private component state.

**Reuse:** `app/ui/src/context`. The UI domain README labels Session and Page Context Pending. Complete fresh bounded authorized context capture and revocation/stale-response/cleanup evidence; do not equate the existing context folder with acceptance.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-15-001 | Register exact widget/version/generation contributions containing stable public refs, selection, filters, safe labels/errors, focus, capture/expiry/hash and schema. |
| FR-TRC-UI-15-002 | Capture a new bounded WorkspaceContextSnapshot for every message and drop unmounted/expired contributions. |
| FR-TRC-UI-15-003 | Keep account/permission projection and stable typed cross-widget selection distinct from authoritative market/result facts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-15-001 | Removing FEAT-UI-15 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-15-001 | Raw DOM, screenshots, credentials, private state and executable instruction fields are rejected. |
| AT-UI-15-002 | A removed widget never contributes to the next turn; navigation cannot rewrite a turn’s already-pinned snapshot. |
| AT-UI-15-003 | A manipulated browser metric cannot override an owner-refreshed value; cross-account context is denied. |
| ATN-UI-15-001 | Disable and physically remove context; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/context/__tests__/traceability.test.tsx`; `app/ui/src/context/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Capture current authorized widget context). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Raw DOM, screenshots, credentials, private state and executable instruction fields are rejected. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-15/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(ui): complete FEAT-UI-15`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-02"></a>

### - [ ] Task 5.02 — FEAT-WS-MANAGE_CONVERSATIONS — Retain scoped conversations without losing canonical evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.04, 1.09.

#### i. Feature and remaining work

Chat history can expire or be deleted without erasing accepted research, claims, receipts or audit records.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-MANAGE_CONVERSATIONS-001 | Accept one idempotent turn identity and monotonic sequence under verified conversation/workspace/account scope. |
| FR-TRC-WS-MANAGE_CONVERSATIONS-002 | Expire unpinned redacted conversation content after 30 days or a stricter configured period, subject to authorized holds. |
| FR-TRC-WS-MANAGE_CONVERSATIONS-003 | Export/delete conversation text separately from workflow outputs and receiver-owned records. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-MANAGE_CONVERSATIONS-001 | Removing FEAT-WS-MANAGE_CONVERSATIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-MANAGE_CONVERSATIONS-001 | Replaying a submitted turn returns the same accepted turn; a concurrent stale writer is rejected. |
| AT-WS-MANAGE_CONVERSATIONS-002 | At the exact expiry boundary content becomes unavailable; a shorter policy wins and a valid hold is respected. |
| AT-WS-MANAGE_CONVERSATIONS-003 | Transcript deletion leaves claim graphs, holdout receipts, strategy revisions and operational audit resolvable through their own authorized owners. |
| ATN-WS-MANAGE_CONVERSATIONS-001 | Disable and physically remove manage_conversations; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/manage_conversations/test_traceability.py`; `tests/services/workspace/manage_conversations/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Accept one idempotent turn identity and monotonic sequence under verified conversation/workspace/account scope. Expected: Replaying a submitted turn returns the same accepted turn; a concurrent stale writer is rejected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-MANAGE_CONVERSATIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(workspace): complete FEAT-WS-MANAGE_CONVERSATIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-03"></a>

### - [ ] Task 5.03 — FEAT-AGT-ASSEMBLE_CONTEXT — Point-in-Time Context Assembly

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.15, 1.19, 1.23, 2.18, 2.20, 4.13.

#### i. Feature and remaining work

Select owner evidence by scope, schema, availability cutoff, licensing, trust, freshness, revision and integrity.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-ASSEMBLE_POINT_IN_TIME_CONTEXT | Select owner evidence by scope, schema, availability cutoff, licensing, trust, freshness, revision and integrity. |
| FR-AGT-SEPARATE_EVIDENCE_FROM_INSTRUCTIONS | Keep system/role instructions, trusted task input, retrieved evidence, peers and memory in distinct fields. |
| FR-AGT-REPORT_CONTEXT_EXCLUSIONS | Report ordered deterministic exclusions for stale, incompatible, duplicate, irrelevant, poisoned and over-budget items with explicit optional partial coverage. |
| FR-AGT-BOUND_CONTEXT_SIZE | Enforce stable item/byte/token/per-source/priority budgets and refresh material UI-projected facts from their owners. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-ASSEMBLE_CONTEXT-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-ASSEMBLE_CONTEXT-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-ASSEMBLE_CONTEXT-001 | Future/revised/unlicensed/wrong-scope evidence is excluded with a reason; required missing evidence refuses. |
| AT-AGT-ASSEMBLE_CONTEXT-002 | Page/tool/memory/peer injection cannot occupy an instruction slot. |
| AT-AGT-ASSEMBLE_CONTEXT-003 | Same inputs yield same ordering/reasons; a partial result does not claim complete support. |
| AT-AGT-ASSEMBLE_CONTEXT-004 | A large or high-priority injected item cannot widen limits; stale browser values never override actual result evidence. |
| ATN-AGT-ASSEMBLE_CONTEXT-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-ASSEMBLE_CONTEXT-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/assemble_context/test_traceability.py`; `tests/services/agentic/assemble_context/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Select owner evidence by scope, schema, availability cutoff, licensing, trust, freshness, revision and integrity. Expected: Future/revised/unlicensed/wrong-scope evidence is excluded with a reason; required missing evidence refuses. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-ASSEMBLE_CONTEXT/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-ASSEMBLE_CONTEXT`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-04"></a>

### - [ ] Task 5.04 — FEAT-AGT-RUN_WORKFLOWS — Durable Agentic Workflow Runtime

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.09, 1.15, 1.18, 1.19, 1.20, 1.23, 1.24, 5.03.

#### i. Feature and remaining work

Validate identity/mandate/idempotency/definition/input/readiness/budget and persist the initial run/checkpoint before shared-job execution.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-SUBMIT_WORKFLOWS | Validate identity/mandate/idempotency/definition/input/readiness/budget and persist the initial run/checkpoint before shared-job execution. |
| FR-AGT-CHECKPOINT_WORKFLOWS | Persist expected-version checkpoints, pause/waits and immutable outputs; resume only compatible workflow/node/provider/input versions with reconciled reservations. |
| FR-AGT-BOUND_ADAPTIVE_ESCALATION | Use deterministic evidence first, one specialist when needed, independent challenge for material uncertainty and councils only when policy/value justify them. |
| FR-AGT-TERMINATE_WORKFLOWS | Record one SUCCEEDED/REFUSED/FAILED/CANCELLED/EXPIRED semantic outcome with separate shared-job projection. |
| FR-AGT-APPLY_BACKPRESSURE | Bound queues, active runs, node steps, loops, fanout, retries, waits and child budgets using shared admission. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-RUN_WORKFLOWS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-RUN_WORKFLOWS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-RUN_WORKFLOWS-001 | Duplicate submit returns one run; a missing required operation capability yields a typed refusal. |
| AT-AGT-RUN_WORKFLOWS-002 | Stale CAS, terminal resume and incompatible checkpoint fail; a human wait holds no worker slot and retains its deadline. |
| AT-AGT-RUN_WORKFLOWS-003 | Model suggestions cannot select an undeclared topology or enlarge fanout/budget; simpler eligible routes remain usable. |
| AT-AGT-RUN_WORKFLOWS-004 | Terminal identities never resume; successful refusal is not displayed as successful research. |
| AT-AGT-RUN_WORKFLOWS-005 | Overload is visible and no child can mint an additional parent budget; cancellation propagates and reconciles accepted child receipts. |
| ATN-AGT-RUN_WORKFLOWS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-RUN_WORKFLOWS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/run_workflows/test_traceability.py`; `tests/services/agentic/run_workflows/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate identity/mandate/idempotency/definition/input/readiness/budget and persist the initial run/checkpoint before shared-job execution. Expected: Duplicate submit returns one run; a missing required operation capability yields a typed refusal. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-RUN_WORKFLOWS/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-AGT-MANAGE_MEMORY (Task 11.05, Phase 11). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-RUN_WORKFLOWS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-05"></a>

### - [ ] Task 5.05 — FEAT-AGT-EVALUATE_PROFILES — Profile and Topology Evaluation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.09, 1.15, 1.19, 1.20, 1.23, 1.24, 5.04.

#### i. Feature and remaining work

Evaluate version-pinned roles/prompts/models/tools/workflows on strict output, grounding, safety, tool, reproducibility, economic and operational evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-EVALUATE_PROFILES | Evaluate version-pinned roles/prompts/models/tools/workflows on strict output, grounding, safety, tool, reproducibility, economic and operational evidence. |
| FR-AGT-ABLATE_TOPOLOGIES | Compare deterministic-only, best-single-agent, full council, each-role-removed and no-peer-visibility under the same inputs/budgets. |
| FR-AGT-DETERMINE_PROFILE_ELIGIBILITY | Compute enable/continue/restrict/disable/retire decisions deterministically from explicit thresholds, evidence, expiry and safety vetoes. |
| FR-AGT-CALIBRATE_GRADERS | Bind deterministic/human graders and calibrated model graders to independent versions/rubrics. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-EVALUATE_PROFILES-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-EVALUATE_PROFILES-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-EVALUATE_PROFILES-001 | Golden/ambiguous/refusal/leakage/injection/null/stress/OOD corpus is retained; zero forbidden calls/leaks/promotion is a hard corpus gate. |
| AT-AGT-EVALUATE_PROFILES-002 | Council remains disabled unless uncertainty-adjusted utility exceeds cost/latency/failure surface; distinct titles alone are not independence. |
| AT-AGT-EVALUATE_PROFILES-003 | Missing evidence or material subject change invalidates eligibility; a model cannot approve itself or edit thresholds. |
| AT-AGT-EVALUATE_PROFILES-004 | Self-grading alone cannot promote the subject; deterministic evaluation-only bootstrap cannot serve user research. |
| ATN-AGT-EVALUATE_PROFILES-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-EVALUATE_PROFILES-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/evaluate_profiles/test_traceability.py`; `tests/services/agentic/evaluate_profiles/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Evaluate version-pinned roles/prompts/models/tools/workflows on strict output, grounding, safety, tool, reproducibility, economic and operational evidence. Expected: Golden/ambiguous/refusal/leakage/injection/null/stress/OOD corpus is retained; zero forbidden calls/leaks/promotion is a hard corpus gate. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-EVALUATE_PROFILES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-EVALUATE_PROFILES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-06"></a>

### - [ ] Task 5.06 — FEAT-AGT-MANAGE_CLAIMS — Claim-and-Evidence Graph

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.09, 1.15, 1.19, 1.20, 1.24, 5.03, 5.04.

#### i. Feature and remaining work

Create separately typed observed fact, deterministic derivation, model inference, forecast and recommendation with scope/horizon/assumptions/falsifier/uncertainty/provenance.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-CREATE_TYPED_CLAIMS | Create separately typed observed fact, deterministic derivation, model inference, forecast and recommendation with scope/horizon/assumptions/falsifier/uncertainty/provenance. |
| FR-AGT-LINK_CLAIM_EVIDENCE | Bind material claims and relations to exact owner records/revisions/digests and immutable graph revisions. |
| FR-AGT-PROPAGATE_CLAIM_STATUS | Append SUPPORTED/CONTESTED/REFUTED/UNKNOWN/EXPIRED status transitions and propagate evidence expiry/revision/invalidation through dependencies. |
| FR-AGT-ASSESS_CLAIM_RELIABILITY | Compute evidence/statistical/epistemic/operational/calibrated dimensions from deterministic evidence rules. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-MANAGE_CLAIMS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-MANAGE_CLAIMS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-MANAGE_CLAIMS-001 | A model cannot promote its narrative into an observed fact by choosing a label; unsupported empirical claims remain UNKNOWN. |
| AT-AGT-MANAGE_CLAIMS-002 | Wrong-owner, missing/tampered/future evidence fails or remains explicitly unsupported; no invented citation is accepted. |
| AT-AGT-MANAGE_CLAIMS-003 | History is not overwritten; content hashes exclude mutable status; cycles violating dependency semantics fail. |
| AT-AGT-MANAGE_CLAIMS-004 | Model self-confidence is not authority; missing/conflicting dimensions remain explicit and repeated calculation is deterministic. |
| ATN-AGT-MANAGE_CLAIMS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-MANAGE_CLAIMS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/manage_claims/test_traceability.py`; `tests/services/agentic/manage_claims/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create separately typed observed fact, deterministic derivation, model inference, forecast and recommendation with scope/horizon/assumptions/falsifier/uncertainty/provenance. Expected: A model cannot promote its narrative into an observed fact by choosing a label; unsupported empirical claims remain UNKNOWN. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-MANAGE_CLAIMS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-MANAGE_CLAIMS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-07"></a>

### - [ ] Task 5.07 — FEAT-AGT-SYNTHESIZE_RESEARCH — Evidence-Preserving Research Synthesis

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.15, 1.19, 1.20, 1.24, 5.06.

#### i. Feature and remaining work

Produce a typed summary only from supplied version-pinned claims/evidence and optional deliberation records.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-SYNTHESIZE_CLAIM_GRAPHS | Produce a typed summary only from supplied version-pinned claims/evidence and optional deliberation records. |
| FR-AGT-PRESERVE_SYNTHESIS_UNCERTAINTY | Preserve supported/contested/refuted/unknown/expired distinctions, dissent, limitations, questions and uncertainty dimensions. |
| FR-AGT-REFUSE_UNSUPPORTED_SYNTHESIS | Refuse or return insufficient evidence when minimum support/freshness/trust or required challenge is missing. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-SYNTHESIZE_RESEARCH-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-SYNTHESIZE_RESEARCH-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-SYNTHESIZE_RESEARCH-001 | Invented/omitted material evidence and recomputed receiver results fail validation. |
| AT-AGT-SYNTHESIZE_RESEARCH-002 | A material unresolved dissent forces contested/insufficient disposition and cannot disappear from the final summary. |
| AT-AGT-SYNTHESIZE_RESEARCH-003 | No deliberation is needed for a policy that does not require it; absence never satisfies a challenge-required policy. |
| ATN-AGT-SYNTHESIZE_RESEARCH-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-SYNTHESIZE_RESEARCH-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/synthesize_research/test_traceability.py`; `tests/services/agentic/synthesize_research/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Produce a typed summary only from supplied version-pinned claims/evidence and optional deliberation records. Expected: Invented/omitted material evidence and recomputed receiver results fail validation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-SYNTHESIZE_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-AGT-DELIBERATE_RESEARCH (Task 7.03, Phase 7). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-SYNTHESIZE_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-08"></a>

### - [ ] Task 5.08 — FEAT-AGT-ASSIST_OPERATOR — Chat Bot and Specialist Delegation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.04, 1.15, 1.19, 1.20, 1.23, 1.24, 5.02, 5.03, 5.04, 5.05, 5.07.

#### i. Feature and remaining work

Accept a fresh bounded Interfaces-validated workspace snapshot and verify principal/account/widget/generation/time/hash/redaction.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-READ_WORKSPACE_CONTEXT | Accept a fresh bounded Interfaces-validated workspace snapshot and verify principal/account/widget/generation/time/hash/redaction. |
| FR-AGT-ANSWER_CONTEXTUAL_QUESTIONS | Answer safe UI meaning, definitions, navigation and already grounded summaries without domain mutation. |
| FR-AGT-ROUTE_SPECIALIST_QUESTIONS | Let the model propose routing but deterministically verify registration/eligibility/scope/conflict/readiness/permission/budget. |
| FR-AGT-PRESERVE_CHAT_HANDOFF_LINEAGE | Return specialist output in the same conversation with role/version, claims/evidence, uncertainty/refusal/dissent and causation. |
| FR-AGT-RESTRICT_CHAT_ACTIONS | Limit direct verbs to read, answer, explain, delegate, summarize and suggest navigation; reviewed DSL changes are specialist/owner operations. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-ASSIST_OPERATOR-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-ASSIST_OPERATOR-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |
| NFR-TRC-AGT-ASSIST_OPERATOR-003 | Initial local profile bounds: 16,000 message characters, 32 contributions, 128 KiB snapshot, 30 s TTL, four delegations and two DSL repair attempts; stricter provider/mandate limits win. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-ASSIST_OPERATOR-001 | Cross-user/account, expired, unknown/removed widget, oversized or secret-bearing context fails; every message gets a new snapshot. |
| AT-AGT-ASSIST_OPERATOR-002 | A material price/metric/run claim requires owner refresh and a suitable specialist, not browser text or model invention. |
| AT-AGT-ASSIST_OPERATOR-003 | A denied/unavailable specialist is named; no silent substitution or generic mutation tool is invoked. |
| AT-AGT-ASSIST_OPERATOR-004 | Cancellation, stream reconnect and specialist failure preserve one turn identity and actual outcome attribution. |
| AT-AGT-ASSIST_OPERATOR-005 | Prose cannot mutate widgets, settings, strategies, runs, holdouts, portfolios, Risk, Trading, Brokers or deployment. |
| ATN-AGT-ASSIST_OPERATOR-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-ASSIST_OPERATOR-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |
| ATN-AGT-ASSIST_OPERATOR-003 | Boundary +1 input/byte/contribution/delegation/repair cases refuse; expired or changed context never authorizes stale actions. |


**Acceptance test targets:** `tests/services/agentic/assist_operator/test_traceability.py`; `tests/services/agentic/assist_operator/test_lifecycle.py`; `tests/services/agentic/assist_operator/test_limits.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Accept a fresh bounded Interfaces-validated workspace snapshot and verify principal/account/widget/generation/time/hash/redaction. Expected: Cross-user/account, expired, unknown/removed widget, oversized or secret-bearing context fails; every message gets a new snapshot. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-ASSIST_OPERATOR/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-AGT-MANAGE_MEMORY (Task 11.05, Phase 11). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-ASSIST_OPERATOR`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-09"></a>

### - [ ] Task 5.09 — FEAT-IFACE-AGENTIC_GATEWAY — Expose Chat Bot and governed Agentic operations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.08, 1.19, 1.23, 5.02, 5.04, 5.08.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-AGENTIC_GATEWAY-001 | Rebuild/validate authenticated per-turn WorkspaceContextSnapshot from current typed widget contributions and enforce size/TTL/redaction. |
| FR-TRC-IFACE-AGENTIC_GATEWAY-002 | Translate chat/workflow/cancel/human-action requests and preserve separate semantic outcome, worker status and receiver receipts. |
| FR-TRC-IFACE-AGENTIC_GATEWAY-003 | Keep conversation storage Workspace-owned and transport observation cleanup separate from domain cancellation. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-AGENTIC_GATEWAY-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-AGENTIC_GATEWAY-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-AGENTIC_GATEWAY-001 | Wrong-session/account, unregistered/removed widget and stale snapshot fail before Agentic invocation. |
| AT-IFACE-AGENTIC_GATEWAY-002 | Only validated terminal artifacts are canonical; streamed text cannot invoke commands. |
| AT-IFACE-AGENTIC_GATEWAY-003 | Closing Chat Bot aborts subscriptions but does not cancel accepted research work; explicit cancellation uses owner commands. |
| ATN-IFACE-AGENTIC_GATEWAY-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-AGENTIC_GATEWAY-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/agentic_gateway/test_traceability.py`; `tests/services/interfaces/agentic_gateway/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Rebuild/validate authenticated per-turn WorkspaceContextSnapshot from current typed widget contributions and enforce size/TTL/redaction. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Wrong-session/account, unregistered/removed widget and stale snapshot fail before Agentic invocation. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-AGENTIC_GATEWAY/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.18 (FEAT-UI-STRATEGY_STUDIO). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-AGENTIC_GATEWAY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-10"></a>

### - [ ] Task 5.10 — FEAT-UI-CHAT_BOT — Ask context-aware questions and review specialist output

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 1.07, 5.01, 5.05, 5.07, 5.09.

#### i. Feature and remaining work

Talk to the named Chat Bot and receive attributed specialist answers or reviewable HSL candidates in the same conversation.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-CHAT_BOT-001 | Capture fresh typed context for each turn and render all idle/submitting/validating/routing/queued/working/waiting/streaming/partial/completed/refused/unavailable/unauthorized/stale/cancelled/failed states. |
| FR-TRC-UI-CHAT_BOT-002 | Render exact role/evidence/uncertainty/dissent and receipt-backed Draft ready/Draft saved/Backtest queued/completed states. |
| FR-TRC-UI-CHAT_BOT-003 | Use accessible keyboard composer and restrained live announcements, sanitize Markdown/links and resume streams or fetch snapshots. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-CHAT_BOT-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-CHAT_BOT-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-CHAT_BOT-001 | Removed widgets do not appear next turn; provisional deltas cannot trigger commands or become canonical artifacts. |
| AT-UI-CHAT_BOT-002 | A changed patch selection/base requires new review; saving and backtesting remain separate authorized actions. |
| AT-UI-CHAT_BOT-003 | Screen readers are not flooded per token; evidence links reauthorize on open; closing the widget only closes its observers. |
| ATN-UI-CHAT_BOT-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-CHAT_BOT-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/chat-bot/__tests__/traceability.test.tsx`; `app/ui/src/widgets/chat-bot/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Ask context-aware questions and review specialist output). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Removed widgets do not appear next turn; provisional deltas cannot trigger commands or become canonical artifacts. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-CHAT_BOT/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-CHAT_BOT`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-5-11"></a>

### - [ ] Task 5.11 — FEAT-UI-AGENTIC_RUN_INSPECTOR — Inspect Agentic evidence and governed work

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U2.

**Order prerequisites:** 1.01, 1.02, 1.06, 5.06, 5.09.

#### i. Feature and remaining work

Audit claims, permissions, costs, waits and receiver outcomes without exposing hidden reasoning.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-AGENTIC_RUN_INSPECTOR-001 | Render canonical graph/status/history and separate semantic outcome/job infrastructure with exact evidence references. |
| FR-TRC-UI-AGENTIC_RUN_INSPECTOR-002 | Expose permitted inspect/cancel/human-action/evidence-export controls bound to exact owner actions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-AGENTIC_RUN_INSPECTOR-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-AGENTIC_RUN_INSPECTOR-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-AGENTIC_RUN_INSPECTOR-001 | A transcript or model confidence never replaces claim/evidence truth; status changes preserve immutable content identity. |
| AT-UI-AGENTIC_RUN_INSPECTOR-002 | Hidden chain-of-thought and secrets are not displayed; replay validation never replays receiver side effects. |
| ATN-UI-AGENTIC_RUN_INSPECTOR-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-AGENTIC_RUN_INSPECTOR-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/agentic-run-inspector/__tests__/traceability.test.tsx`; `app/ui/src/widgets/agentic-run-inspector/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect Agentic evidence and governed work). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A transcript or model confidence never replaces claim/evidence truth; status changes preserve immutable content identity. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-AGENTIC_RUN_INSPECTOR/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P05 — Ask Chat Bot about a selected real result; show refreshed authorized evidence, specialist attribution, claim references, and run-inspector detail in the same conversation. Publish `docs/dev/evidence/phases/phase-05.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-AGENTIC_RUN_INSPECTOR`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-6"></a>

## Phase 6 — Research protocols and reviewed AI strategy creation

**Feature tasks: 11.** Deterministic research governance and receivers + Agentic design/authoring/proposal handoffs → Research gateway/workbench + existing Studio/Chat Bot. AI output never authorizes execution by itself.

**Visible completion:** Describe an idea, register campaign/protocol/holdout policy, review an HSL draft or base-bound patch, accept the exact candidate, then separately authorize a bounded backtest from the existing UI.

**Phase evidence:** `tests/ui/e2e/research/phase_06.spec.ts` and `docs/dev/evidence/phases/phase-06.json`, owned by Task 6.11. All prior affected UI/data/recovery regressions remain required.

<a id="task-6-01"></a>

### - [ ] Task 6.01 — FEAT-STRAT-ACCEPT_PROPOSALS — Receive non-executable strategy proposals

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.04, 1.09.

#### i. Feature and remaining work

A candidate thesis reaches Strategy as an auditable intake request without being confused with a trade or accepted strategy.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-ACCEPT_PROPOSALS-001 | Validate proposed scope/behavior, thesis, horizon, invalidation, evidence, requested evaluation and expiry under current identity/permission. |
| FR-TRC-STRAT-ACCEPT_PROPOSALS-002 | Return idempotent ACCEPTED/REJECTED/PENDING/EXPIRED intake receipts naming the actual resulting lifecycle state. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-ACCEPT_PROPOSALS-001 | Removing FEAT-STRAT-ACCEPT_PROPOSALS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-ACCEPT_PROPOSALS-001 | A stale/invalid/forbidden execution field fails; quantity/order/approval fields are not accepted as proposal authority. |
| AT-STRAT-ACCEPT_PROPOSALS-002 | An accepted intake never claims an order, fill, Risk approval or completed research qualification. |
| ATN-STRAT-ACCEPT_PROPOSALS-001 | Disable and physically remove accept_proposals; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/accept_proposals/test_traceability.py`; `tests/services/strategy/accept_proposals/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate proposed scope/behavior, thesis, horizon, invalidation, evidence, requested evaluation and expiry under current identity/permission. Expected: A stale/invalid/forbidden execution field fails; quantity/order/approval fields are not accepted as proposal authority. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-ACCEPT_PROPOSALS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.17 (FEAT-IFACE-OPERATE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-ACCEPT_PROPOSALS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-02"></a>

### - [ ] Task 6.02 — FEAT-RES-GOVERN_CAMPAIGNS — Account for research campaigns and hypothesis families

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.04, 1.09.

#### i. Feature and remaining work

Human, Builder and Agentic exploration share one research history and cannot reset scrutiny by renaming or rehashing a candidate.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-GOVERN_CAMPAIGNS-001 | Register immutable campaign purpose, hypothesis families, dataset families, search/compute budget and preregistration before generated variants run. |
| FR-TRC-RES-GOVERN_CAMPAIGNS-002 | Classify exact/near duplicates from mechanism, scope/horizon/universe, lineage, HSL semantic fingerprint and parameter/feature changes under versioned deterministic policy. |
| FR-TRC-RES-GOVERN_CAMPAIGNS-003 | Conserve accepted_attempts = active + completed + failed + cancelled + invalid + refused and retain pre-admission denials/repairs/retries separately. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-GOVERN_CAMPAIGNS-001 | Removing FEAT-RES-GOVERN_CAMPAIGNS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-GOVERN_CAMPAIGNS-001 | A generated candidate without a canonical owner receipt is refused; a new chat/model/name does not create a fresh budget. |
| AT-RES-GOVERN_CAMPAIGNS-002 | Unproven independence conservatively shares the existing family; reclassification preserves already charged usage and exposure. |
| AT-RES-GOVERN_CAMPAIGNS-003 | At closure active is zero; negative/null outcomes remain completed evidence and actual retry cost is not erased. |
| ATN-RES-GOVERN_CAMPAIGNS-001 | Disable and physically remove govern_campaigns; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/govern_campaigns/test_traceability.py`; `tests/services/research/govern_campaigns/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register immutable campaign purpose, hypothesis families, dataset families, search/compute budget and preregistration before generated variants run. Expected: A generated candidate without a canonical owner receipt is refused; a new chat/model/name does not create a fresh budget. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-GOVERN_CAMPAIGNS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-GOVERN_CAMPAIGNS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-03"></a>

### - [ ] Task 6.03 — FEAT-RES-DEFINE_PROTOCOLS — Preregister research samples and evaluation protocols

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U3.

**Order prerequisites:** 2.20, 6.02.

#### i. Feature and remaining work

A research question becomes a reproducible test with an explicit baseline, falsifier, sample policy and stop rules.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-DEFINE_PROTOCOLS-001 | Version hypothesis/mechanism/confounders/falsifier/rejection criterion plus data, costs, seed, baseline, metrics and finite budgets. |
| FR-TRC-RES-DEFINE_PROTOCOLS-002 | Define nonoverlapping half-open training/development/final-test intervals with exact timestamps, timezone, warm-up and exposure policy. |
| FR-TRC-RES-DEFINE_PROTOCOLS-003 | Allow research_draft hypotheses with explicit unvalidated assumptions while preventing them from claiming supported performance or qualification. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-DEFINE_PROTOCOLS-001 | Removing FEAT-RES-DEFINE_PROTOCOLS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-DEFINE_PROTOCOLS-001 | Missing material sample/cost/baseline/stop fields produces validation diagnostics, not permissive defaults. |
| AT-RES-DEFINE_PROTOCOLS-002 | Insufficient history cannot create overlapping partitions; final OOS never enters fit, parent selection or threshold tuning. |
| AT-RES-DEFINE_PROTOCOLS-003 | A draft can be authored/tested without prior profitability; an unknown claim cannot pass a stronger downstream gate. |
| ATN-RES-DEFINE_PROTOCOLS-001 | Disable and physically remove define_protocols; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/define_protocols/test_traceability.py`; `tests/services/research/define_protocols/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version hypothesis/mechanism/confounders/falsifier/rejection criterion plus data, costs, seed, baseline, metrics and finite budgets. Expected: Missing material sample/cost/baseline/stop fields produces validation diagnostics, not permissive defaults. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-DEFINE_PROTOCOLS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-DEFINE_PROTOCOLS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-04"></a>

### - [ ] Task 6.04 — FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS — Strategy Proposal Composition and Handoff

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.15, 1.19, 1.20, 1.23, 1.24, 5.03, 5.06, 5.07, 6.01.

#### i. Feature and remaining work

Compose expiring thesis/scope/direction-or-behavior/horizon/invalidation/evidence/uncertainty/evaluation candidates.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-COMPOSE_STRATEGY_PROPOSALS | Compose expiring thesis/scope/direction-or-behavior/horizon/invalidation/evidence/uncertainty/evaluation candidates. |
| FR-AGT-SUBMIT_STRATEGY_PROPOSALS | Submit unchanged through Strategy proposal intake with current identity/scope/freshness/idempotency and exact capability lease. |
| FR-AGT-RECORD_STRATEGY_RECEIPTS | Retain exact accepted/rejected/expired/pending intake receipts and resulting lifecycle state. |
| FR-AGT-PRESERVE_STRATEGY_AUTHORITY | Keep evaluation into intents, registration, Risk approval and Trading/Brokers commands outside Agentic. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-COMPOSE_STRATEGY_PROPOSALS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-COMPOSE_STRATEGY_PROPOSALS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-COMPOSE_STRATEGY_PROPOSALS-001 | Broker/order/fill/approval/price/quantity/lot/notional/size fields are rejected. |
| AT-AGT-COMPOSE_STRATEGY_PROPOSALS-002 | A denied lease reaches no receiver; retry after uncertain commit reconciles the original key. |
| AT-AGT-COMPOSE_STRATEGY_PROPOSALS-003 | Accepted intake cannot be displayed as accepted strategy, TradeIntent, order or fill. |
| AT-AGT-COMPOSE_STRATEGY_PROPOSALS-004 | Import/capability/schema negative tests prove no privileged route. |
| ATN-AGT-COMPOSE_STRATEGY_PROPOSALS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-COMPOSE_STRATEGY_PROPOSALS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/compose_strategy_proposals/test_traceability.py`; `tests/services/agentic/compose_strategy_proposals/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Compose expiring thesis/scope/direction-or-behavior/horizon/invalidation/evidence/uncertainty/evaluation candidates. Expected: Broker/order/fill/approval/price/quantity/lot/notional/size fields are rejected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-05"></a>

### - [ ] Task 6.05 — FEAT-RES-GOVERN_HOLDOUTS — Reserve scarce holdout access atomically

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.09, 6.02, 6.03.

#### i. Feature and remaining work

All research clients consume the same holdout allowance even under concurrency, restart and uncertain receiver outcomes.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-GOVERN_HOLDOUTS-001 | Reserve exact campaign/family/dataset/holdout/protocol/request/principal/purpose/expiry against expected revision and idempotency. |
| FR-TRC-RES-GOVERN_HOLDOUTS-002 | Reconcile dispatch/receiver receipt before refunding unused reservations; consumed information and actual compute are never refunded by cancellation. |
| FR-TRC-RES-GOVERN_HOLDOUTS-003 | Record every exposure/amendment and invalidate untouched-OOS claims after adaptive inspection. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-GOVERN_HOLDOUTS-001 | Removing FEAT-RES-GOVERN_HOLDOUTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-GOVERN_HOLDOUTS-001 | Concurrent requests cannot both spend the final available look; retries return the same reservation. |
| AT-RES-GOVERN_HOLDOUTS-002 | A failed run that exposed holdout information consumes the applicable look; an uncertain call stays pending until reconciled. |
| AT-RES-GOVERN_HOLDOUTS-003 | Renaming, changing prompt/model or parameter hash cannot make observed test data untouched again. |
| ATN-RES-GOVERN_HOLDOUTS-001 | Disable and physically remove govern_holdouts; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/govern_holdouts/test_traceability.py`; `tests/services/research/govern_holdouts/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Reserve exact campaign/family/dataset/holdout/protocol/request/principal/purpose/expiry against expected revision and idempotency. Expected: Concurrent requests cannot both spend the final available look; retries return the same reservation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-GOVERN_HOLDOUTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-GOVERN_HOLDOUTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-06"></a>

### - [ ] Task 6.06 — FEAT-RES-RUN_RESEARCH — Execute authorized research and retest campaigns

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.18, 4.07, 4.09, 4.10, 4.12, 4.14, 6.03, 6.05.

#### i. Feature and remaining work

A bounded experiment or selected retest population runs reproducibly and retains every outcome without mutating its sources.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-RUN_RESEARCH-001 | Resolve immutable strategy/databank/query inputs, effective configuration, alternate contexts, output membership policy and budgets before idempotent start. |
| FR-TRC-RES-RUN_RESEARCH-002 | Submit lazily bounded simulation/retest work through public owners and reconcile every complete/failed/invalid/refused/cancelled/cache-hit outcome. |
| FR-TRC-RES-RUN_RESEARCH-003 | Route accepted/rejected results under explicit atomic membership policy and preserve originals, baseline comparisons and failure reasons. |
| FR-TRC-RES-RUN_RESEARCH-004 | Recover checkpoints using exact input/provider/policy versions and receiver idempotency before resubmission. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-RUN_RESEARCH-001 | Removing FEAT-RES-RUN_RESEARCH withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-RUN_RESEARCH-001 | A changed query cannot alter an active population; duplicate start returns one Research run. |
| AT-RES-RUN_RESEARCH-002 | A parameter space or genome population is not materialized as unbounded futures; no hidden winner-only result ledger exists. |
| AT-RES-RUN_RESEARCH-003 | Cancellation between stages labels partial evidence; moving passing members never overwrites source strategies/results. |
| AT-RES-RUN_RESEARCH-004 | Crash after receiver commitment yields one accepted trial/receipt and preserved actual usage. |
| ATN-RES-RUN_RESEARCH-001 | Disable and physically remove run_research; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/run_research/test_traceability.py`; `tests/services/research/run_research/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve immutable strategy/databank/query inputs, effective configuration, alternate contexts, output membership policy and budgets before idempotent start. Expected: A changed query cannot alter an active population; duplicate start returns one Research run. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-RUN_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-SIM-PERTURB_INPUTS (Task 7.01, Phase 7). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-RUN_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-07"></a>

### - [ ] Task 6.07 — FEAT-IFACE-OPERATE_RESEARCH — Expose research protocols, campaigns and runs

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.08, 6.02, 6.03, 6.05, 6.06.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_RESEARCH-001 | Translate Research-owned plan/run/campaign/holdout commands and preserve identity/budgets/receipts. |
| FR-TRC-IFACE-OPERATE_RESEARCH-002 | Expose run rejection funnels, pause/stop desired state and immutable qualification evidence. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_RESEARCH-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_RESEARCH-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_RESEARCH-001 | An interface retry cannot create a second accepted trial or holdout look. |
| AT-IFACE-OPERATE_RESEARCH-002 | A paused/qualified state is only shown when the owner attests it; no private research workflow is scheduled. |
| ATN-IFACE-OPERATE_RESEARCH-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_RESEARCH-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_research/test_traceability.py`; `tests/services/interfaces/operate_research/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate Research-owned plan/run/campaign/holdout commands and preserve identity/budgets/receipts. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: An interface retry cannot create a second accepted trial or holdout look. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-RES-TEST_ROBUSTNESS (Task 7.04, Phase 7); FEAT-RES-QUALIFY_RESEARCH (Task 7.06, Phase 7); FEAT-RES-PREPARE_NEURAL_DATASETS (Task 14.01, Phase 14); FEAT-RES-LABEL_NEURAL_DATA (Task 14.02, Phase 14); FEAT-RES-TRAIN_MODELS (Task 14.04, Phase 14); FEAT-RES-VALIDATE_MODELS (Task 14.05, Phase 14); FEAT-RES-EXPLAIN_MODELS (Task 14.06, Phase 14). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-08"></a>

### - [ ] Task 6.08 — FEAT-AGT-GOVERN_RESEARCH_SEARCH — Agentic Research Request Accounting

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.09, 1.15, 1.19, 1.23, 5.04, 6.02, 6.05, 6.06.

#### i. Feature and remaining work

Obtain canonical Research campaign/family/dataset/search identities before generated research and retain mandatory owner references/receipts.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-REGISTER_RESEARCH_CAMPAIGNS | Obtain canonical Research campaign/family/dataset/search identities before generated research and retain mandatory owner references/receipts. |
| FR-AGT-ACCOUNT_RESEARCH_VARIANTS | Record parameter/feature/prompt/model variants, amendments and degrees of freedom against owner-classified families and actual budgets. |
| FR-AGT-PRESERVE_FAILED_ATTEMPTS | Retain every accepted active and terminal attempt plus pre-admission denials and linked retries/repairs. |
| FR-AGT-GOVERN_HOLDOUT_REQUESTS | Request owner-authoritative reservations/consumption through governed leases and reconcile unknown receiver effects. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-GOVERN_RESEARCH_SEARCH-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-GOVERN_RESEARCH_SEARCH-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-GOVERN_RESEARCH_SEARCH-001 | Local authored strings cannot create an independent Research campaign or holdout allocation. |
| AT-AGT-GOVERN_RESEARCH_SEARCH-002 | Trivial renaming/rehashing cannot reset consumed scarcity; similarity advice never overrides Research classification. |
| AT-AGT-GOVERN_RESEARCH_SEARCH-003 | Accepted = active+completed+failed+cancelled+invalid+refused, with active zero at closure; null/negative results stay completed. |
| AT-AGT-GOVERN_RESEARCH_SEARCH-004 | Concurrency/expiry/cancellation cannot refund exposed information or allocate a second look via a new local hash. |
| ATN-AGT-GOVERN_RESEARCH_SEARCH-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-GOVERN_RESEARCH_SEARCH-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/govern_research_search/test_traceability.py`; `tests/services/agentic/govern_research_search/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Obtain canonical Research campaign/family/dataset/search identities before generated research and retain mandatory owner references/receipts. Expected: Local authored strings cannot create an independent Research campaign or holdout allocation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-GOVERN_RESEARCH_SEARCH/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-OPT-SEARCH_PARAMETERS (Task 9.01, Phase 9). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-GOVERN_RESEARCH_SEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-09"></a>

### - [ ] Task 6.09 — FEAT-AGT-DESIGN_RESEARCH — Falsifiable Research Design

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.15, 1.19, 1.20, 1.23, 1.24, 5.04, 5.06, 5.07, 6.03, 6.08.

#### i. Feature and remaining work

Compose scope/horizon/mechanism/evidence/prerequisites/confounders/falsifier/rejection criterion under explicit research-draft or supported classification.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-DESIGN_FALSIFIABLE_HYPOTHESES | Compose scope/horizon/mechanism/evidence/prerequisites/confounders/falsifier/rejection criterion under explicit research-draft or supported classification. |
| FR-AGT-COMPOSE_EXPERIMENT_REQUESTS | Map reviewed hypotheses into the exact owner protocol with immutable inputs/splits/embargo/cost/seed/baseline/metrics/stop/evidence fields. |
| FR-AGT-COMPOSE_SEARCH_REQUESTS | Compose finite Optimization method/space/objective/trial/early-stop/robustness/holdout candidates only when that operation is ready. |
| FR-AGT-BIND_RESEARCH_PROTOCOLS | Retain claim/synthesis/campaign/family/data/policy/config/role/model/prompt and receiver-schema lineage. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-DESIGN_RESEARCH-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-DESIGN_RESEARCH-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-DESIGN_RESEARCH-001 | A draft may encode unvalidated assumptions but cannot claim empirical support or qualification. |
| AT-AGT-DESIGN_RESEARCH-002 | Missing or invented receiver fields fail schema validation; composing a candidate does not start computation. |
| AT-AGT-DESIGN_RESEARCH-003 | U3 hypothesis/experiment works without Optimization; DESIGN_SEARCH refuses until U6 receiver readiness. |
| AT-AGT-DESIGN_RESEARCH-004 | Changing inputs requires a new candidate/review identity; unchanged owner rejection/result remains authoritative. |
| ATN-AGT-DESIGN_RESEARCH-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-DESIGN_RESEARCH-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/design_research/test_traceability.py`; `tests/services/agentic/design_research/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Compose scope/horizon/mechanism/evidence/prerequisites/confounders/falsifier/rejection criterion under explicit research-draft or supported classification. Expected: A draft may encode unvalidated assumptions but cannot claim empirical support or qualification. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-DESIGN_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-OPT-SEARCH_PARAMETERS (Task 9.01, Phase 9). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-DESIGN_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-10"></a>

### - [ ] Task 6.10 — FEAT-AGT-COMPOSE_STRATEGY_SPECS — HSL Strategy and Indicator Composition

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.15, 1.19, 1.20, 1.23, 1.24, 3.12, 3.14, 5.06, 5.07, 6.08.

#### i. Feature and remaining work

Generate canonical HSL drafts or base-revision-bound typed patches using registered blocks, units, parameters, clocks, tests and displayed assumptions.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-COMPOSE_STRATEGY_DSL | Generate canonical HSL drafts or base-revision-bound typed patches using registered blocks, units, parameters, clocks, tests and displayed assumptions. |
| FR-AGT-VALIDATE_DSL_HANDOFF | Preview dependency-safe granular edits and invoke Strategy/Indicators intake only for the exact user-reviewed candidate. |
| FR-AGT-REPORT_UNSUPPORTED_EXPRESSIONS | Return a receiver-validated structured gap when current DSL cannot express the approved behavior. |
| FR-AGT-PRESERVE_DSL_PROVENANCE | Bind candidate to hypothesis/claims/campaign/search/role/model/prompt/schema/compiler/config/test vectors and receiver receipts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-COMPOSE_STRATEGY_SPECS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-COMPOSE_STRATEGY_SPECS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-COMPOSE_STRATEGY_SPECS-001 | Unknown blocks/arbitrary source fail; new drafts need not claim prior profitability; repairs stop after the permitted limit. |
| AT-AGT-COMPOSE_STRATEGY_SPECS-002 | A changed base/selection/hash conflicts or requires new review; saving never starts a backtest or grants live authority. |
| AT-AGT-COMPOSE_STRATEGY_SPECS-003 | No silent custom semantics or switch to source generation occurs. |
| AT-AGT-COMPOSE_STRATEGY_SPECS-004 | A new revision reports the real owner outcome; supplied canonical hashes are not trusted without recomputation. |
| ATN-AGT-COMPOSE_STRATEGY_SPECS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-COMPOSE_STRATEGY_SPECS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/compose_strategy_specs/test_traceability.py`; `tests/services/agentic/compose_strategy_specs/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Generate canonical HSL drafts or base-revision-bound typed patches using registered blocks, units, parameters, clocks, tests and displayed assumptions. Expected: Unknown blocks/arbitrary source fail; new drafts need not claim prior profitability; repairs stop after the permitted limit. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-COMPOSE_STRATEGY_SPECS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-COMPOSE_STRATEGY_SPECS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-6-11"></a>

### - [ ] Task 6.11 — FEAT-UI-28 — Inspect research campaigns, protocols and evidence

**Status:** `EXISTING_UNVERIFIED` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U3.

**Order prerequisites:** 1.01, 1.02, 1.06, 4.19, 6.04, 6.06, 6.07, 6.09, 6.10.

#### i. Feature and remaining work

The user can see a research question, its attempts and qualification evidence without confusing it with job infrastructure or a winning candidate.

**Reuse:** `app/ui/src/widgets/research`. Retain the existing implementation; map current tests/usage to every listed requirement, execute them on the pinned baseline, and implement only failed, missing or newly required behaviour. Complete required contract, registration, integration, performance and removal evidence; do not rewrite already-passing behaviour.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-28-001 | Display canonical campaign/family/protocol/sample/budget/holdout identities, attempt conservation and receiver lineage. |
| FR-TRC-UI-28-002 | Present research draft, supported evidence and qualified outcomes as different states, with exact owner reasons and limitations. |
| FR-TRC-UI-28-003 | Expose compatible research navigation, comparison and immutable artifact history through registered contributions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-28-001 | Removing FEAT-UI-28 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-28-001 | Failed/null/refused/invalid/pruned and cache-hit evidence is not hidden by winner-only filters. |
| AT-UI-28-002 | A draft or successful worker job cannot look like research qualification or live approval. |
| AT-UI-28-003 | Removing Builder/Retester or Agentic leaves the Research evidence browser usable for existing records. |
| ATN-UI-28-001 | Disable and physically remove research; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `app/ui/src/widgets/research/__tests__/traceability.test.tsx`; `app/ui/src/widgets/research/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect research campaigns, protocols and evidence). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Failed/null/refused/invalid/pruned and cache-hit evidence is not hidden by winner-only filters. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-28/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P06 — Describe an idea, register campaign/protocol/holdout policy, review an HSL draft or base-bound patch, accept the exact candidate, then separately authorize a bounded backtest from the existing UI. Publish `docs/dev/evidence/phases/phase-06.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-28`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-7"></a>

## Phase 7 — Retesting, robustness and independent challenge

**Feature tasks: 7.** Simulator perturbations + Analytics distributions + Research robustness/qualification + Agentic deliberation → existing gateways → Retester and robustness results widgets.

**Visible completion:** Choose stable result IDs, run an ordered perturbation/robustness pipeline, cancel one scenario, inspect truthful partial results and baseline deltas, and obtain evidence-bound qualification/challenge.

**Phase evidence:** `tests/ui/e2e/research/phase_07.spec.ts` and `docs/dev/evidence/phases/phase-07.json`, owned by Task 7.07. All prior affected UI/data/recovery regressions remain required.

<a id="task-7-01"></a>

### - [ ] Task 7.01 — FEAT-SIM-PERTURB_INPUTS — Evaluate explicitly modeled execution perturbations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U4.

**Order prerequisites:** 1.14, 4.09, 4.10.

#### i. Feature and remaining work

A Retester can measure sensitivity to data, parameters, spread, slippage and execution degradation using a recorded method and seed.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-PERTURB_INPUTS-001 | Version parameter jitter, price/data perturbation, spread/slippage stress, skipped/degraded execution and alternate-method contexts with explicit seed and units. |
| FR-TRC-SIM-PERTURB_INPUTS-002 | Execute each rerun through the selected tick engine with the same no-lookahead/accounting obligations. |
| FR-TRC-SIM-PERTURB_INPUTS-003 | Return bounded scenario outcomes, failures, counts and exact baseline/perturbation references. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-PERTURB_INPUTS-001 | Removing FEAT-SIM-PERTURB_INPUTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-PERTURB_INPUTS-001 | A changed perturbation or tick method produces a distinct evaluation identity and cannot overwrite the baseline. |
| AT-SIM-PERTURB_INPUTS-002 | A statistical ledger operation is never reported as a new tick backtest; a rerun cannot thin events to fit its budget. |
| AT-SIM-PERTURB_INPUTS-003 | Cancelled/invalid/null scenarios remain accounted for; only complete eligible outcomes enter qualification. |
| ATN-SIM-PERTURB_INPUTS-001 | Disable and physically remove perturb_inputs; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/simulator/perturb_inputs/test_traceability.py`; `tests/services/simulator/perturb_inputs/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version parameter jitter, price/data perturbation, spread/slippage stress, skipped/degraded execution and alternate-method contexts with explicit seed and units. Expected: A changed perturbation or tick method produces a distinct evaluation identity and cannot overwrite the baseline. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-PERTURB_INPUTS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 6.06 (FEAT-RES-RUN_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-PERTURB_INPUTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-7-02"></a>

### - [ ] Task 7.02 — FEAT-ANA-ANALYZE_DISTRIBUTIONS — Calculate statistical and ledger-based robustness evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U4.

**Order prerequisites:** 1.18, 4.07, 4.13.

#### i. Feature and remaining work

A user can inspect distributions, percentiles and post-hoc robustness with explicit population, method and uncertainty.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-ANALYZE_DISTRIBUTIONS-001 | Run seeded ledger reshuffling, block resampling and skipped-trade methods with finite samples and explicit assumptions. |
| FR-TRC-ANA-ANALYZE_DISTRIBUTIONS-002 | Report method/population/sample count, confidence/percentile direction and undefined/small-sample limitations. |
| FR-TRC-ANA-ANALYZE_DISTRIBUTIONS-003 | Add U10 box/violin/percentile-fan/sensitivity/risk-of-ruin and advanced risk metrics through explicit versioned estimators. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-ANALYZE_DISTRIBUTIONS-001 | Removing FEAT-ANA-ANALYZE_DISTRIBUTIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-ANALYZE_DISTRIBUTIONS-001 | Same input/seed/method yields reproducible distributions; results are labelled ledger/statistical evidence, not tick backtests. |
| AT-ANA-ANALYZE_DISTRIBUTIONS-002 | A high percentile is not universally labelled conservative; nonfinite or insufficient support produces a typed reason. |
| AT-ANA-ANALYZE_DISTRIBUTIONS-003 | Display sampling and model assumptions survive export; an unavailable advanced method leaves core metrics usable. |
| ATN-ANA-ANALYZE_DISTRIBUTIONS-001 | Disable and physically remove analyze_distributions; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/analyze_distributions/test_traceability.py`; `tests/services/analytics/analyze_distributions/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Run seeded ledger reshuffling, block resampling and skipped-trade methods with finite samples and explicit assumptions. Expected: Same input/seed/method yields reproducible distributions; results are labelled ledger/statistical evidence, not tick backtests. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-ANALYZE_DISTRIBUTIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-ANALYZE_DISTRIBUTIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-7-03"></a>

### - [ ] Task 7.03 — FEAT-AGT-DELIBERATE_RESEARCH — Independent Challenge and Deliberation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U4.

**Order prerequisites:** 1.15, 1.19, 1.20, 1.23, 1.24, 5.04, 5.06.

#### i. Feature and remaining work

Commit challenger first-pass assessments before proposer narrative and record provider/model/prompt/evidence/context correlation.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-COLLECT_INDEPENDENT_CHALLENGES | Commit challenger first-pass assessments before proposer narrative and record provider/model/prompt/evidence/context correlation. |
| FR-AGT-PRESERVE_DELIBERATION_DISSENT | Retain counterclaims, insufficient evidence, minority dissent and unresolved material disagreement. |
| FR-AGT-BOUND_DELIBERATION | Enforce participant/role/round/fanout/time/token/tool/cost limits from deterministic profiles. |
| FR-AGT-STOP_LOW_VALUE_DELIBERATION | Stop on completion, inadequate evidence, material conflict, low incremental value, limits, incident, removal or cancellation. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-DELIBERATE_RESEARCH-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-DELIBERATE_RESEARCH-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-DELIBERATE_RESEARCH-001 | Blind-first-pass ordering is provable; weak independence is disclosed or refused under policy. |
| AT-AGT-DELIBERATE_RESEARCH-002 | Majority agreement cannot erase dissent, authorize risk or select executable size. |
| AT-AGT-DELIBERATE_RESEARCH-003 | A caller/model cannot enlarge limits; no unbounded debate/retry survives budget exhaustion. |
| AT-AGT-DELIBERATE_RESEARCH-004 | Each stop produces a typed reason and preserves committed evidence; more discussion is not automatic escalation. |
| ATN-AGT-DELIBERATE_RESEARCH-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-DELIBERATE_RESEARCH-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/deliberate_research/test_traceability.py`; `tests/services/agentic/deliberate_research/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Commit challenger first-pass assessments before proposer narrative and record provider/model/prompt/evidence/context correlation. Expected: Blind-first-pass ordering is provable; weak independence is disclosed or refused under policy. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-DELIBERATE_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 5.07 (FEAT-AGT-SYNTHESIZE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-DELIBERATE_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-7-04"></a>

### - [ ] Task 7.04 — FEAT-RES-TEST_ROBUSTNESS — Define and run ordered robustness pipelines

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U4.

**Order prerequisites:** 6.06, 7.01, 7.02.

#### i. Feature and remaining work

A Retester applies the exact chosen cross-check stages with reproducible evidence and explicit provider readiness.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-TEST_ROBUSTNESS-001 | Version ordered Monte Carlo ledger/retest, what-if, additional-markets, higher-fidelity, WFO/WFM, SPP and sequential stages with budgets/sample/seed/pass rules. |
| FR-TRC-RES-TEST_ROBUSTNESS-002 | Delegate each stage to its semantic owner and preserve the evidence class, baseline, actual trial count and partial/refusal status. |
| FR-TRC-RES-TEST_ROBUSTNESS-003 | Stop/checkpoint at declared stage boundaries and preserve failures and incomplete stages for the qualification owner. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-TEST_ROBUSTNESS-001 | Removing FEAT-RES-TEST_ROBUSTNESS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-TEST_ROBUSTNESS-001 | Reorder/save/load preserves semantics; a U6-only missing provider blocks only the selected dependent operation rather than producing mock evidence. |
| AT-RES-TEST_ROBUSTNESS-002 | A reshuffled ledger is not called a backtest; higher-fidelity means an explicitly selected method, not a hidden replacement. |
| AT-RES-TEST_ROBUSTNESS-003 | Cancellation cannot label unexecuted stages passed; exact output membership policy is retained. |
| ATN-RES-TEST_ROBUSTNESS-001 | Disable and physically remove test_robustness; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/test_robustness/test_traceability.py`; `tests/services/research/test_robustness/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version ordered Monte Carlo ledger/retest, what-if, additional-markets, higher-fidelity, WFO/WFM, SPP and sequential stages with budgets/sample/seed/pass rules. Expected: Reorder/save/load preserves semantics; a U6-only missing provider blocks only the selected dependent operation rather than producing mock evidence. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-TEST_ROBUSTNESS/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-OPT-VALIDATE_WALK_FORWARD (Task 9.02, Phase 9); FEAT-OPT-PERMUTE_PARAMETERS (Task 9.03, Phase 9); FEAT-OPT-SEARCH_PARAMETERS (Task 9.01, Phase 9). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

**This provider also qualifies earlier consumers:** Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-TEST_ROBUSTNESS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-7-05"></a>

### - [ ] Task 7.05 — FEAT-UI-ROBUSTNESS_RESULTS — Inspect robustness and scenario evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U4.

**Order prerequisites:** 1.01, 1.02, 4.19, 7.02, 7.03, 7.04.

#### i. Feature and remaining work

Understand stage outcomes, distributions and limitations without treating every Monte Carlo operation as a simulation.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-ROBUSTNESS_RESULTS-001 | Render each stage’s method, evidence class, seed/count/sample, pass rule and partial/failure status. |
| FR-TRC-UI-ROBUSTNESS_RESULTS-002 | Show percentile direction, assumptions and compatible distribution/scenario drilldowns. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-ROBUSTNESS_RESULTS-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-ROBUSTNESS_RESULTS-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-ROBUSTNESS_RESULTS-001 | A reshuffled ledger is labelled statistical and a cancelled stage cannot appear passed. |
| AT-UI-ROBUSTNESS_RESULTS-002 | The UI never assumes a high percentile is conservative or invents a missing distribution. |
| ATN-UI-ROBUSTNESS_RESULTS-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-ROBUSTNESS_RESULTS-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/robustness-results/__tests__/traceability.test.tsx`; `app/ui/src/widgets/robustness-results/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect robustness and scenario evidence). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A reshuffled ledger is labelled statistical and a cancelled stage cannot appear passed. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-ROBUSTNESS_RESULTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-ROBUSTNESS_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-7-06"></a>

### - [ ] Task 7.06 — FEAT-RES-QUALIFY_RESEARCH — Issue evidence-bound research qualification

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U4.

**Order prerequisites:** 4.07, 6.03, 6.05, 7.04.

#### i. Feature and remaining work

A candidate passes only its recorded research policy, with full limitations and no implied live approval.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-QUALIFY_RESEARCH-001 | Evaluate complete baseline/robustness/sample/holdout/metric evidence under the pinned acceptance policy. |
| FR-TRC-RES-QUALIFY_RESEARCH-002 | Classify walk-forward stability using explicit neighborhood/threshold/overlap and metric definitions; retain all windows and rejected trials. |
| FR-TRC-RES-QUALIFY_RESEARCH-003 | Return a research decision artifact and reviewed promotion recommendation to Strategy/Portfolio without economic execution authority. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-QUALIFY_RESEARCH-001 | Removing FEAT-RES-QUALIFY_RESEARCH withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-QUALIFY_RESEARCH-001 | Missing mandatory stages, sealed-sample violations, undefined metrics or stale evidence produce failed/insufficient outcomes rather than implied consent. |
| AT-RES-QUALIFY_RESEARCH-002 | A visible plateau or best cell alone cannot satisfy qualification; chosen/unused windows remain inspectable. |
| AT-RES-QUALIFY_RESEARCH-003 | A passing research result cannot create an order, Risk approval or live strategy activation. |
| ATN-RES-QUALIFY_RESEARCH-001 | Disable and physically remove qualify_research; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/qualify_research/test_traceability.py`; `tests/services/research/qualify_research/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Evaluate complete baseline/robustness/sample/holdout/metric evidence under the pinned acceptance policy. Expected: Missing mandatory stages, sealed-sample violations, undefined metrics or stale evidence produce failed/insufficient outcomes rather than implied consent. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-QUALIFY_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-OPT-VALIDATE_WALK_FORWARD (Task 9.02, Phase 9). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

**This provider also qualifies earlier consumers:** Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-QUALIFY_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-7-07"></a>

### - [ ] Task 7.07 — FEAT-UI-STRATEGY_RETESTER — Retest a fixed strategy population

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U4.

**Order prerequisites:** 1.01, 1.02, 6.07, 7.04, 7.06.

#### i. Feature and remaining work

Re-evaluate immutable source strategies under explicitly changed contexts and ordered robustness stages.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-STRATEGY_RETESTER-001 | Resolve and preview the exact immutable population and effective override diff, warning about source and method/sample incompatibility. |
| FR-TRC-UI-STRATEGY_RETESTER-002 | Show per-stage results/failures/partial states and typed baseline deltas with atomic output routing preview. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-STRATEGY_RETESTER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-STRATEGY_RETESTER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-STRATEGY_RETESTER-001 | A query changing later cannot alter an active retest set; originals remain unchanged. |
| AT-UI-STRATEGY_RETESTER-002 | Unexecuted stages are not passed; a ledger statistic cannot be labelled a new backtest. |
| ATN-UI-STRATEGY_RETESTER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-STRATEGY_RETESTER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/research-settings/__tests__/traceability.test.tsx`; `app/ui/src/widgets/research-settings/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Retest a fixed strategy population). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A query changing later cannot alter an active retest set; originals remain unchanged. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-STRATEGY_RETESTER/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P07 — Choose stable result IDs, run an ordered perturbation/robustness pipeline, cancel one scenario, inspect truthful partial results and baseline deltas, and obtain evidence-bound qualification/challenge. Publish `docs/dev/evidence/phases/phase-07.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-STRATEGY_RETESTER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-8"></a>

## Phase 8 — Builder generation, ranking and evolution

**Feature tasks: 5.** Strategy spaces + random/seeded generation + Research ranking/evolution → existing Research gateway → Builder. Full registered operator scope is implemented in this feature task; U10-only support remains release-gated.

**Visible completion:** Create a strategy space in Builder, run a seeded random/island search, inspect acceptance/rejection reasons, and open committed candidates in the existing Databank and Results.

**Phase evidence:** `tests/ui/e2e/research/phase_08.spec.ts` and `docs/dev/evidence/phases/phase-08.json`, owned by Task 8.05. All prior affected UI/data/recovery regressions remain required.

<a id="task-8-01"></a>

### - [ ] Task 8.01 — FEAT-STRAT-DEFINE_SEARCH_SPACES — Define legal strategy construction spaces

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U5.

**Order prerequisites:** 3.07, 3.08, 3.11.

#### i. Feature and remaining work

Builder can save and preview a finite, typed space before allocating expensive candidate evaluations.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-DEFINE_SEARCH_SPACES-001 | Version strategy mode, direction/symmetry, architecture, condition count, depth/node/lookback limits and required/optional/disabled exits. |
| FR-TRC-STRAT-DEFINE_SEARCH_SPACES-002 | Resolve presets, explicit constraints, block distributions, sizing/exit references and overrides into one immutable effective space. |
| FR-TRC-STRAT-DEFINE_SEARCH_SPACES-003 | Preview combinatorial scale and excluded/conflicting choices using exact counts where calculable and labelled estimates otherwise. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-DEFINE_SEARCH_SPACES-001 | Removing FEAT-STRAT-DEFINE_SEARCH_SPACES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-DEFINE_SEARCH_SPACES-001 | A grammar that cannot satisfy the requested bounds fails with a reason rather than generating indefinitely. |
| AT-STRAT-DEFINE_SEARCH_SPACES-002 | Save/load/clone/diff preserves effective meaning; invalid dependent parameters cannot be silently coerced. |
| AT-STRAT-DEFINE_SEARCH_SPACES-003 | Explosive cardinality is reported before allocation; an estimate is never presented as an exact runtime forecast. |
| ATN-STRAT-DEFINE_SEARCH_SPACES-001 | Disable and physically remove define_search_spaces; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/define_search_spaces/test_traceability.py`; `tests/services/strategy/define_search_spaces/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version strategy mode, direction/symmetry, architecture, condition count, depth/node/lookback limits and required/optional/disabled exits. Expected: A grammar that cannot satisfy the requested bounds fails with a reason rather than generating indefinitely. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-DEFINE_SEARCH_SPACES/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.17 (FEAT-IFACE-OPERATE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-DEFINE_SEARCH_SPACES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-8-02"></a>

### - [ ] Task 8.02 — FEAT-RES-RANK_CANDIDATES — Apply hard eligibility and versioned fitness selection

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U5.

**Order prerequisites:** 4.07, 6.03.

#### i. Feature and remaining work

A high score cannot hide a failed rule, undefined metric or contaminated sample, and every selection decision is explainable.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-RANK_CANDIDATES-001 | Apply versioned metric/sample/operator/threshold/unit/null hard rules before fitness and retain every dismissal reason. |
| FR-TRC-RES-RANK_CANDIDATES-002 | Rank scalar or weighted normalized metrics with nonnegative weights summing to one and development-fitted transforms. |
| FR-TRC-RES-RANK_CANDIDATES-003 | Implement U10 Pareto/NSGA-II fronts and crowding with direction normalization, undefined exclusion and stable hash ties. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-RANK_CANDIDATES-001 | Removing FEAT-RES-RANK_CANDIDATES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-RANK_CANDIDATES-001 | An undefined required metric fails eligibility even when another objective is high; zero-trade candidates are rejected where the declared protocol requires it. |
| AT-RES-RANK_CANDIDATES-002 | Raw currency profit, Sharpe and drawdown percent are not added without normalization; final OOS cannot fit a transform. |
| AT-RES-RANK_CANDIDATES-003 | Dominance is no-worse in every objective and strictly-better in one; equal/zero-range columns contribute zero crowding span. |
| ATN-RES-RANK_CANDIDATES-001 | Disable and physically remove rank_candidates; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/rank_candidates/test_traceability.py`; `tests/services/research/rank_candidates/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Apply versioned metric/sample/operator/threshold/unit/null hard rules before fitness and retain every dismissal reason. Expected: An undefined required metric fails eligibility even when another objective is high; zero-trade candidates are rejected where the declared protocol requires it. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-RANK_CANDIDATES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-RANK_CANDIDATES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-8-03"></a>

### - [ ] Task 8.03 — FEAT-RES-GENERATE_STRATEGIES — Construct random and seeded valid candidates

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U5.

**Order prerequisites:** 3.13, 6.02, 8.01.

#### i. Feature and remaining work

Builder produces reproducible typed strategies from an accepted space without modifying parents or generating illegal programs.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-GENERATE_STRATEGIES-001 | Generate bounded candidates from weighted enabled blocks and typed depth/node/lookback/parameter/lock constraints using pinned PRNG streams. |
| FR-TRC-RES-GENERATE_STRATEGIES-002 | Implement Full/Grow/ramped-half-and-half and explicit seeded retain/replace/extend behavior with immutable parent provenance. |
| FR-TRC-RES-GENERATE_STRATEGIES-003 | Apply static validation and safe identity dedup before evaluation, retaining separate AST-attempt and fully evaluated counters. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-GENERATE_STRATEGIES-001 | Removing FEAT-RES-GENERATE_STRATEGIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-GENERATE_STRATEGIES-001 | Impossible grammar/depth returns unsatisfied constraints within the attempt budget; no circular or invalid accepted tree is generated. |
| AT-RES-GENERATE_STRATEGIES-002 | Fixed seed yields the same population/lineage; locked subtrees and parent bytes remain unchanged. |
| AT-RES-GENERATE_STRATEGIES-003 | A rejected duplicate or invalid AST does not masquerade as a completed simulation or a passing decimation candidate. |
| ATN-RES-GENERATE_STRATEGIES-001 | Disable and physically remove generate_strategies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/generate_strategies/test_traceability.py`; `tests/services/research/generate_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Generate bounded candidates from weighted enabled blocks and typed depth/node/lookback/parameter/lock constraints using pinned PRNG streams. Expected: Impossible grammar/depth returns unsatisfied constraints within the attempt budget; no circular or invalid accepted tree is generated. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-GENERATE_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-GENERATE_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-8-04"></a>

### - [ ] Task 8.04 — FEAT-RES-EVOLVE_STRATEGIES — Evolve bounded island populations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U5.

**Order prerequisites:** 6.06, 8.02, 8.03.

#### i. Feature and remaining work

Builder searches structural strategy variants with deterministic operators, migration and restarts whose costs remain visible.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-EVOLVE_STRATEGIES-001 | Initialize K×M×N unique filter-passing fully evaluated candidates, rank them and allocate M×N survivors by deterministic round-robin. |
| FR-TRC-RES-EVOLVE_STRATEGIES-002 | Apply tournament-without-replacement selection, immutable elites, type/unit/clock-compatible one/two-point crossover and bounded mutation respecting locks. |
| FR-TRC-RES-EVOLVE_STRATEGIES-003 | Run elite → offspring/evaluation → rank → simultaneous directed-ring migration → duplicate/refill → fresh blood → checkpoint/termination. |
| FR-TRC-RES-EVOLVE_STRATEGIES-004 | Use versioned Mersenne Twister state and SHA-256 length-prefixed seed derivation over purpose/generation/island/candidate/operator/attempt. |
| FR-TRC-RES-EVOLVE_STRATEGIES-005 | Add U10 rank/roulette, real crossover/Gaussian/polynomial/SBX and structure/phenotype diversity as registered operators with explicit equations/parameters. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-EVOLVE_STRATEGIES-001 | Removing FEAT-RES-EVOLVE_STRATEGIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-EVOLVE_STRATEGIES-001 | Insufficient eligible candidates returns INSUFFICIENT_ELIGIBLE_CANDIDATES with counts; raw AST attempts and duplicates do not satisfy the target. |
| AT-RES-EVOLVE_STRATEGIES-002 | Two crossover points are disjoint; a missing compatible swap yields a recorded bounded no-op/retry, never an invalid child. |
| AT-RES-EVOLVE_STRATEGIES-003 | Migration takes floor(N×rate), including zero; arrival order cannot alter replacements, and elite/finite budget constraints survive restarts. |
| AT-RES-EVOLVE_STRATEGIES-004 | Changing worker count/schedule does not change candidate identity, operator stream or tie-breaks; restart restores the exact PRNG state. |
| AT-RES-EVOLVE_STRATEGIES-005 | All-zero roulette scores use a recorded uniform warning; Gaussian snapping ties go to the lower legal lattice index; undefined operators are unavailable, not substituted. |
| ATN-RES-EVOLVE_STRATEGIES-001 | Disable and physically remove evolve_strategies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/evolve_strategies/test_traceability.py`; `tests/services/research/evolve_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Initialize K×M×N unique filter-passing fully evaluated candidates, rank them and allocate M×N survivors by deterministic round-robin. Expected: Insufficient eligible candidates returns INSUFFICIENT_ELIGIBLE_CANDIDATES with counts; raw AST attempts and duplicates do not satisfy the target. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-EVOLVE_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-EVOLVE_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-8-05"></a>

### - [ ] Task 8.05 — FEAT-UI-STRATEGY_BUILDER — Configure and run strategy generation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U5.

**Order prerequisites:** 1.01, 1.02, 6.07, 8.02, 8.04.

#### i. Feature and remaining work

Construct a bounded effective search plan and inspect why candidates were accepted or dismissed.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-STRATEGY_BUILDER-001 | Render every CAT-BUILDER control from owner schemas, showing effective overrides, scale, compatibility and finite budgets before start. |
| FR-TRC-UI-STRATEGY_BUILDER-002 | Save/load/clone/diff/preset plans and observe actual generation/island/evaluation/rejection/progress/results. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-STRATEGY_BUILDER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-STRATEGY_BUILDER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-STRATEGY_BUILDER-001 | Impossible constraints, missing blocks and denied resource estimates remain visible; UI never creates executable strategy source or private sampling logic. |
| AT-UI-STRATEGY_BUILDER-002 | Counter meanings distinguish AST attempts, evaluated candidates and committed results; pause/stop follows owner acknowledgement. |
| ATN-UI-STRATEGY_BUILDER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-STRATEGY_BUILDER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/strategy-search-space/__tests__/traceability.test.tsx`; `app/ui/src/widgets/strategy-search-space/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Configure and run strategy generation). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Impossible constraints, missing blocks and denied resource estimates remain visible; UI never creates executable strategy source or private sampling logic. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-STRATEGY_BUILDER/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P08 — Create a strategy space in Builder, run a seeded random/island search, inspect acceptance/rejection reasons, and open committed candidates in the existing Databank and Results. Publish `docs/dev/evidence/phases/phase-08.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-STRATEGY_BUILDER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-9"></a>

## Phase 9 — Optimization and walk-forward evidence

**Feature tasks: 6.** Optimization providers → Optimization gateway → optimizer and optimization-results widgets; existing robustness and Chat Bot contracts gain actual provider-backed operation readiness without duplicate tasks.

**Visible completion:** Select a saved strategy, validate a finite legal parameter lattice, execute search/WFO/WFM/permutation, inspect complete 2D evidence and explicitly promote a new revision.

**Phase evidence:** `tests/ui/e2e/research/phase_09.spec.ts` and `docs/dev/evidence/phases/phase-09.json`, owned by Task 9.06. All prior affected UI/data/recovery regressions remain required.

<a id="task-9-01"></a>

### - [ ] Task 9.01 — FEAT-OPT-SEARCH_PARAMETERS — Search typed parameter spaces and preserve every trial

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Optimization · **Owner specification:** `app/services/optimization/README.md` · **Register first slice:** U6.

**Order prerequisites:** 1.18, 4.07, 4.09, 4.10, 4.12, 6.03, 6.05.

#### i. Feature and remaining work

A user can run exact-grid, discrete-genetic or sequential-coordinate optimization with transparent scale and complete accounting.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-OPT-SEARCH_PARAMETERS-001 | Build legal parameter lattices from typed bounds/step/options/dependencies and count Cartesian combinations with arbitrary-precision integers before allocation. |
| FR-TRC-OPT-SEARCH_PARAMETERS-002 | Execute grid, discrete evolutionary and ordered coordinate-search providers through the same immutable simulation request contract. |
| FR-TRC-OPT-SEARCH_PARAMETERS-003 | Generate work lazily, reuse compiled topology/immutable data, and retain active/completed/failed/cancelled/invalid/refused/pruned/cache-hit trial outcomes with actual costs. |
| FR-TRC-OPT-SEARCH_PARAMETERS-004 | Persist complete parameter/metric/sample/state surfaces under declared retention and promote selected tuples only through a new Strategy revision. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-OPT-SEARCH_PARAMETERS-001 | Removing FEAT-OPT-SEARCH_PARAMETERS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-OPT-SEARCH_PARAMETERS-001 | Floating cardinality errors do not add/drop a legal value; invalid dependent parameters fail instead of coercing. |
| AT-OPT-SEARCH_PARAMETERS-002 | Sequential search records parameter order, fixed values, passes/tolerance and hash ties; mutation resamples legal indexes only. |
| AT-OPT-SEARCH_PARAMETERS-003 | At least 1,000 requests do not allocate a whole Cartesian product or JIT per tuple; pruning is incomplete evidence with a protocol reason. |
| AT-OPT-SEARCH_PARAMETERS-004 | A best point does not overwrite its source strategy; sampled display surfaces disclose omitted/retained counts. |
| ATN-OPT-SEARCH_PARAMETERS-001 | Disable and physically remove search_parameters; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/optimization/search_parameters/test_traceability.py`; `tests/services/optimization/search_parameters/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Build legal parameter lattices from typed bounds/step/options/dependencies and count Cartesian combinations with arbitrary-precision integers before allocation. Expected: Floating cardinality errors do not add/drop a legal value; invalid dependent parameters fail instead of coercing. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-OPT-SEARCH_PARAMETERS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 7.04 (FEAT-RES-TEST_ROBUSTNESS), Task 6.08 (FEAT-AGT-GOVERN_RESEARCH_SEARCH), Task 6.09 (FEAT-AGT-DESIGN_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(optimization): complete FEAT-OPT-SEARCH_PARAMETERS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-9-02"></a>

### - [ ] Task 9.02 — FEAT-OPT-VALIDATE_WALK_FORWARD — Execute bounded walk-forward windows and matrices

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Optimization · **Owner specification:** `app/services/optimization/README.md` · **Register first slice:** U6.

**Order prerequisites:** 2.20, 9.01.

#### i. Feature and remaining work

A strategy is selected on one interval and evaluated on succeeding data with explicit overlap and warm-up rules.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-OPT-VALIDATE_WALK_FORWARD-001 | Version training/test lengths, step, anchored/rolling mode, parameter search, warm-up, costs, seed and bounded matrix cells. |
| FR-TRC-OPT-VALIDATE_WALK_FORWARD-002 | Evaluate succeeding OOS intervals and resolve overlapping predictions using earliest eligible OOS prediction per timestamp in the baseline. |
| FR-TRC-OPT-VALIDATE_WALK_FORWARD-003 | Publish per-fold chosen revisions/parameters, aggregate/worst-window/efficiency evidence and all failure/partial states. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-OPT-VALIDATE_WALK_FORWARD-001 | Removing FEAT-OPT-VALIDATE_WALK_FORWARD withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-OPT-VALIDATE_WALK_FORWARD-001 | An invalid/overlapping fit window or unbounded matrix fails preflight; each fold fits/selects only within its development interval. |
| AT-OPT-VALIDATE_WALK_FORWARD-002 | The same timestamp is not counted twice; alternate overlap policy requires a distinct version/identity. |
| AT-OPT-VALIDATE_WALK_FORWARD-003 | A missing window or undefined efficiency is not filled with a passing value; Research receives full evidence for its own stability decision. |
| ATN-OPT-VALIDATE_WALK_FORWARD-001 | Disable and physically remove validate_walk_forward; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/optimization/validate_walk_forward/test_traceability.py`; `tests/services/optimization/validate_walk_forward/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version training/test lengths, step, anchored/rolling mode, parameter search, warm-up, costs, seed and bounded matrix cells. Expected: An invalid/overlapping fit window or unbounded matrix fails preflight; each fold fits/selects only within its development interval. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-OPT-VALIDATE_WALK_FORWARD/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 7.04 (FEAT-RES-TEST_ROBUSTNESS), Task 7.06 (FEAT-RES-QUALIFY_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(optimization): complete FEAT-OPT-VALIDATE_WALK_FORWARD`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-9-03"></a>

### - [ ] Task 9.03 — FEAT-OPT-PERMUTE_PARAMETERS — Measure parameter-population sensitivity

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Optimization · **Owner specification:** `app/services/optimization/README.md` · **Register first slice:** U6.

**Order prerequisites:** 7.02, 9.01.

#### i. Feature and remaining work

A user can inspect the distribution of outcomes across a declared parameter population instead of only its best point.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-OPT-PERMUTE_PARAMETERS-001 | Resolve finite parameter population, exact or sampled coverage, seed and retention before execution. |
| FR-TRC-OPT-PERMUTE_PARAMETERS-002 | Retain each evaluation outcome and publish median/statistic/distribution references with original strategy and search provenance. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-OPT-PERMUTE_PARAMETERS-001 | Removing FEAT-OPT-PERMUTE_PARAMETERS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-OPT-PERMUTE_PARAMETERS-001 | A sampled population records rule/size/omissions and is not represented as exhaustive enumeration. |
| AT-OPT-PERMUTE_PARAMETERS-002 | Negative, zero and failed outcomes remain visible; changing sample policy creates a distinct result identity. |
| ATN-OPT-PERMUTE_PARAMETERS-001 | Disable and physically remove permute_parameters; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/optimization/permute_parameters/test_traceability.py`; `tests/services/optimization/permute_parameters/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve finite parameter population, exact or sampled coverage, seed and retention before execution. Expected: A sampled population records rule/size/omissions and is not represented as exhaustive enumeration. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-OPT-PERMUTE_PARAMETERS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 7.04 (FEAT-RES-TEST_ROBUSTNESS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(optimization): complete FEAT-OPT-PERMUTE_PARAMETERS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-9-04"></a>

### - [ ] Task 9.04 — FEAT-IFACE-OPERATE_OPTIMIZATION — Expose bounded search and walk-forward operations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U6.

**Order prerequisites:** 1.08, 9.01, 9.02, 9.03.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_OPTIMIZATION-001 | Translate typed parameter/WFO/WFM/SPP plans and exact output retention/method/budget choices. |
| FR-TRC-IFACE-OPERATE_OPTIMIZATION-002 | Return bounded surfaces, trial failures and selected-revision handoff references. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_OPTIMIZATION-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_OPTIMIZATION-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_OPTIMIZATION-001 | An infeasible/excessive space fails visibly; the gateway never enumerates the Cartesian product. |
| AT-IFACE-OPERATE_OPTIMIZATION-002 | A displayed best point cannot silently overwrite a Strategy revision or disappear failed trials. |
| ATN-IFACE-OPERATE_OPTIMIZATION-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_OPTIMIZATION-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_optimization/test_traceability.py`; `tests/services/interfaces/operate_optimization/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate typed parameter/WFO/WFM/SPP plans and exact output retention/method/budget choices. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: An infeasible/excessive space fails visibly; the gateway never enumerates the Cartesian product. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_OPTIMIZATION/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_OPTIMIZATION`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-9-05"></a>

### - [ ] Task 9.05 — FEAT-UI-PARAMETER_OPTIMIZER — Plan and inspect parameter optimization

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U6.

**Order prerequisites:** 1.01, 1.02, 1.06, 9.04.

#### i. Feature and remaining work

Explore a finite legal parameter space with exact work estimates and honest search/fold evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-PARAMETER_OPTIMIZER-001 | Display legal parameter domains, exact Cartesian count, constraints, method/seed/resource/output estimates and validation diagnostics. |
| FR-TRC-UI-PARAMETER_OPTIMIZER-002 | Inspect trials, best/selected point, stability and OOS evidence and hand off a selected tuple for a reviewed new Strategy revision. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-PARAMETER_OPTIMIZER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-PARAMETER_OPTIMIZER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-PARAMETER_OPTIMIZER-001 | No hidden parameter coercion, full browser Cartesian expansion or gateway-side optimization occurs. |
| AT-UI-PARAMETER_OPTIMIZER-002 | Selecting a point does not mutate the original; failed/undefined/pruned trials and sampled surfaces remain labelled. |
| ATN-UI-PARAMETER_OPTIMIZER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-PARAMETER_OPTIMIZER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/optimization-settings/__tests__/traceability.test.tsx`; `app/ui/src/widgets/optimization-settings/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Plan and inspect parameter optimization). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: No hidden parameter coercion, full browser Cartesian expansion or gateway-side optimization occurs. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-PARAMETER_OPTIMIZER/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-PARAMETER_OPTIMIZER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-9-06"></a>

### - [ ] Task 9.06 — FEAT-UI-OPTIMIZATION_RESULTS — Inspect parameter surfaces and walk-forward evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U6.

**Order prerequisites:** 1.01, 1.02, 1.06, 9.02, 9.03, 9.04.

#### i. Feature and remaining work

Compare parameter, sequential, SPP and WFO/WFM results with honest sampling and stable selection.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-OPTIMIZATION_RESULTS-001 | Render typed parameter/fold/window coordinates, all failures/undefined values and exact-versus-sampled surface coverage. |
| FR-TRC-UI-OPTIMIZATION_RESULTS-002 | Expose stability/plateau and OOS evidence as owner projections and route promotion to Strategy review. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-OPTIMIZATION_RESULTS-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-OPTIMIZATION_RESULTS-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-OPTIMIZATION_RESULTS-001 | An omitted cell is not zero; selecting a point retains exact parameter and result IDs. |
| AT-UI-OPTIMIZATION_RESULTS-002 | A visible plateau is not a qualification decision; U10 3D is optional with equivalent 2D/table access. |
| ATN-UI-OPTIMIZATION_RESULTS-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-OPTIMIZATION_RESULTS-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/optimization-results/__tests__/traceability.test.tsx`; `app/ui/src/widgets/optimization-results/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Inspect parameter surfaces and walk-forward evidence). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: An omitted cell is not zero; selecting a point retains exact parameter and result IDs. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-OPTIMIZATION_RESULTS/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P09 — Select a saved strategy, validate a finite legal parameter lattice, execute search/WFO/WFM/permutation, inspect complete 2D evidence and explicitly promote a new revision. Publish `docs/dev/evidence/phases/phase-09.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-OPTIMIZATION_RESULTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-10"></a>

## Phase 10 — Portfolio construction and correlation in the UI

**Feature tasks: 12.** Portfolio numerical/composition/search/simulation/risk providers + Analytics correlation filtering + Agentic advisory → Portfolio gateway → Composer and Builder; original Results/Databank widgets are included in regression evidence.

**Visible completion:** Send databank results to Portfolio Composer, inspect alignment and currency warnings, allocate weights, simulate shared capital, search combinations, save a portfolio and inspect advisory/correlation decisions.

**Phase evidence:** `tests/ui/e2e/research/phase_10.spec.ts` and `docs/dev/evidence/phases/phase-10.json`, owned by Task 10.12. All prior affected UI/data/recovery regressions remain required.

<a id="task-10-01"></a>

### - [ ] Task 10.01 — FEAT-POR-COMPOSE_PORTFOLIOS — Version portfolio composition and capital policy

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.09, 2.02, 2.12, 4.13.

#### i. Feature and remaining work

A user can save a weighted portfolio whose constituents and capital/sizing conventions are unambiguous.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-COMPOSE_PORTFOLIOS-001 | Add/remove/reorder stable Strategy/result references, exposing duplicate/missing/sample/currency/shared-capital incompatibilities. |
| FR-TRC-POR-COMPOSE_PORTFOLIOS-002 | Validate raw and normalized weights, cash, capital/leverage, sizing consistency, fees, calendar and rebalance policy. |
| FR-TRC-POR-COMPOSE_PORTFOLIOS-003 | Save immutable portfolio revisions and separately version an explicitly labelled Buy & Hold benchmark. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-COMPOSE_PORTFOLIOS-001 | Removing FEAT-POR-COMPOSE_PORTFOLIOS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-COMPOSE_PORTFOLIOS-001 | Reordering changes presentation only unless a named model declares order sensitivity; missing constituents block computation. |
| AT-POR-COMPOSE_PORTFOLIOS-002 | Both raw/normalized values remain visible; invalid sums or ambiguous mixed sizing fail instead of silent normalization/relaxation. |
| AT-POR-COMPOSE_PORTFOLIOS-003 | Benchmark series/instrument/sample/currency/fees are pinned; saving never overwrites an existing result. |
| ATN-POR-COMPOSE_PORTFOLIOS-001 | Disable and physically remove compose_portfolios; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/compose_portfolios/test_traceability.py`; `tests/services/portfolio/compose_portfolios/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Add/remove/reorder stable Strategy/result references, exposing duplicate/missing/sample/currency/shared-capital incompatibilities. Expected: Reordering changes presentation only unless a named model declares order sensitivity; missing constituents block computation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-COMPOSE_PORTFOLIOS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.16 (FEAT-STRAT-EXCHANGE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-COMPOSE_PORTFOLIOS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-02"></a>

### - [ ] Task 10.02 — FEAT-POR-ANALYZE_CORRELATION — Compute aligned correlation and covariance

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.14, 2.23, 4.16.

#### i. Feature and remaining work

Portfolio and databank decisions share one explicit measure of dependence with inspectable pair evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-ANALYZE_CORRELATION-001 | Pin return frequency, currency, calendar, weighting, missing/zero-period policy, minimum overlap and method. |
| FR-TRC-POR-ANALYZE_CORRELATION-002 | Compute blocked/tiled matrices and bounded pair drilldowns without changing the population or precision policy. |
| FR-TRC-POR-ANALYZE_CORRELATION-003 | Expose negative-correlation handling and overlapping-trade rules as explicit policies rather than display shortcuts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-ANALYZE_CORRELATION-001 | Removing FEAT-POR-ANALYZE_CORRELATION withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-ANALYZE_CORRELATION-001 | Core Pearson requires at least two pairs and nonzero variance; undefined coefficients remain typed unavailable. |
| AT-POR-ANALYZE_CORRELATION-002 | 100/1,000-strategy fixtures respect matrix/solver memory reservations; a cell detail uses the same aligned sample as the matrix. |
| AT-POR-ANALYZE_CORRELATION-003 | Changing negative/missing handling changes a named analysis identity; no silent zero fill creates artificial diversification. |
| ATN-POR-ANALYZE_CORRELATION-001 | Disable and physically remove analyze_correlation; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/analyze_correlation/test_traceability.py`; `tests/services/portfolio/analyze_correlation/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Pin return frequency, currency, calendar, weighting, missing/zero-period policy, minimum overlap and method. Expected: Core Pearson requires at least two pairs and nonzero variance; undefined coefficients remain typed unavailable. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-ANALYZE_CORRELATION/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-ANALYZE_CORRELATION`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-03"></a>

### - [ ] Task 10.03 — FEAT-ANA-FILTER_CORRELATION — Explain correlation-based result selection

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U7.

**Order prerequisites:** 4.14, 10.02.

#### i. Feature and remaining work

A databank can reduce redundant candidates with an auditable policy and explicit retained/removed pair evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-FILTER_CORRELATION-001 | Resolve the exact candidate population and request Portfolio correlation with frequency/sample/calendar/currency/missing/negative handling. |
| FR-TRC-ANA-FILTER_CORRELATION-002 | Apply versioned threshold, quality ordering and deterministic tie-breaks and preview retained/removed candidates with pair detail. |
| FR-TRC-ANA-FILTER_CORRELATION-003 | Commit membership changes only after exact preview acceptance under the selected atomicity policy. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-FILTER_CORRELATION-001 | Removing FEAT-ANA-FILTER_CORRELATION withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-FILTER_CORRELATION-001 | An undefined coefficient or insufficient overlap remains a typed exclusion/decision reason, not zero correlation. |
| AT-ANA-FILTER_CORRELATION-002 | Reordering input rows cannot change a policy declared order-insensitive; every removed candidate has its decision evidence. |
| AT-ANA-FILTER_CORRELATION-003 | A changed population or stale revision invalidates the preview and cannot silently remove a different set. |
| ATN-ANA-FILTER_CORRELATION-001 | Disable and physically remove filter_correlation; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/filter_correlation/test_traceability.py`; `tests/services/analytics/filter_correlation/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve the exact candidate population and request Portfolio correlation with frequency/sample/calendar/currency/missing/negative handling. Expected: An undefined coefficient or insufficient overlap remains a typed exclusion/decision reason, not zero correlation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-FILTER_CORRELATION/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 4.19 (FEAT-IFACE-OPERATE_RESULTS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-FILTER_CORRELATION`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-04"></a>

### - [ ] Task 10.04 — FEAT-POR-OPTIMIZE_WEIGHTS — Allocate portfolio weights with declared objectives

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.18, 10.01, 10.02.

#### i. Feature and remaining work

A user can choose a weighting method whose inputs, constraints and infeasibility are visible.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-OPTIMIZE_WEIGHTS-001 | Implement core weighting with explicit cash, normalization, metric nonnegative transform and zero-total-score fallback. |
| FR-TRC-POR-OPTIMIZE_WEIGHTS-002 | Implement U10 constrained methods with pinned covariance/estimation window/risk-free/currency, weight/exposure/turnover/leverage/group caps and rebalance costs. |
| FR-TRC-POR-OPTIMIZE_WEIGHTS-003 | Publish before/after weights, objective and contribution evidence against the same input snapshot. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-OPTIMIZE_WEIGHTS-001 | Removing FEAT-POR-OPTIMIZE_WEIGHTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-OPTIMIZE_WEIGHTS-001 | A zero-score population follows the recorded fallback; negative raw scores are not treated as valid weights without a transform. |
| AT-POR-OPTIMIZE_WEIGHTS-002 | Infeasible constraints return diagnostics, not silent relaxation; solver convergence status and provider version remain visible. |
| AT-POR-OPTIMIZE_WEIGHTS-003 | An optimized result cannot mutate the saved portfolio until a separate revision acceptance succeeds. |
| ATN-POR-OPTIMIZE_WEIGHTS-001 | Disable and physically remove optimize_weights; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/optimize_weights/test_traceability.py`; `tests/services/portfolio/optimize_weights/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Implement core weighting with explicit cash, normalization, metric nonnegative transform and zero-total-score fallback. Expected: A zero-score population follows the recorded fallback; negative raw scores are not treated as valid weights without a transform. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-OPTIMIZE_WEIGHTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-OPTIMIZE_WEIGHTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-05"></a>

### - [ ] Task 10.05 — FEAT-POR-SIMULATE_PORTFOLIOS — Evaluate combined portfolio capital and execution

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 4.07, 4.09, 4.10, 10.01.

#### i. Feature and remaining work

Combined performance reflects the selected aggregation mode and actual capital interactions.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-SIMULATE_PORTFOLIOS-001 | Require an explicit fixed-ledger aggregation or interacting-capital tick-resimulation mode with capital, leverage, sizing, fees and rebalance policy. |
| FR-TRC-POR-SIMULATE_PORTFOLIOS-002 | Execute shared-capital simulations through the same native tick engine and retain all constituent versions and accepted result references. |
| FR-TRC-POR-SIMULATE_PORTFOLIOS-003 | Publish asynchronous result/progress/warnings and per-strategy/combined metrics without changing portfolio definitions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-SIMULATE_PORTFOLIOS-001 | Removing FEAT-POR-SIMULATE_PORTFOLIOS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-SIMULATE_PORTFOLIOS-001 | Independent ledger summation cannot be labelled equivalent when cross-symbol signals/cash/risk alter fills. |
| AT-POR-SIMULATE_PORTFOLIOS-002 | Cross-symbol equal-time/gap/cash fixtures match the chronological reference; worker scheduling does not change allocation or results. |
| AT-POR-SIMULATE_PORTFOLIOS-003 | Cancelled runs retain partial evidence; recomputation produces a new immutable result. |
| ATN-POR-SIMULATE_PORTFOLIOS-001 | Disable and physically remove simulate_portfolios; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/simulate_portfolios/test_traceability.py`; `tests/services/portfolio/simulate_portfolios/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Require an explicit fixed-ledger aggregation or interacting-capital tick-resimulation mode with capital, leverage, sizing, fees and rebalance policy. Expected: Independent ledger summation cannot be labelled equivalent when cross-symbol signals/cash/risk alter fills. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-SIMULATE_PORTFOLIOS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-SIMULATE_PORTFOLIOS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-06"></a>

### - [ ] Task 10.06 — FEAT-POR-ANALYZE_PORTFOLIO_RISK — Explain diversification, exposure and portfolio scenarios

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 4.07, 10.01, 10.02.

#### i. Feature and remaining work

An allocation can be reviewed for concentration, covariance, tail/scenario and cost assumptions rather than judged by profit alone.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-ANALYZE_PORTFOLIO_RISK-001 | Project contribution, concentration, gross/net exposure, currency/group risks and declared scenarios from pinned constituents/weights. |
| FR-TRC-POR-ANALYZE_PORTFOLIO_RISK-002 | Compute diversification ratio separately from Sharpe change using sum(w_i*sigma_i)/sqrt(w^T*cov*w) for the declared long-only convention. |
| FR-TRC-POR-ANALYZE_PORTFOLIO_RISK-003 | Return scoped expiring evidence/review projections for Portfolio/Risk/Agentic consumers without order or approval fields. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-ANALYZE_PORTFOLIO_RISK-001 | Removing FEAT-POR-ANALYZE_PORTFOLIO_RISK withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-ANALYZE_PORTFOLIO_RISK-001 | Missing or stale inputs yield explicit incomplete evidence rather than a clean risk verdict. |
| AT-POR-ANALYZE_PORTFOLIO_RISK-002 | Zero portfolio volatility is undefined; short/cash variants require a separately named definition. |
| AT-POR-ANALYZE_PORTFOLIO_RISK-003 | A model advisory cannot mutate this evidence or authorize a portfolio allocation. |
| ATN-POR-ANALYZE_PORTFOLIO_RISK-001 | Disable and physically remove analyze_portfolio_risk; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/analyze_portfolio_risk/test_traceability.py`; `tests/services/portfolio/analyze_portfolio_risk/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Project contribution, concentration, gross/net exposure, currency/group risks and declared scenarios from pinned constituents/weights. Expected: Missing or stale inputs yield explicit incomplete evidence rather than a clean risk verdict. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-ANALYZE_PORTFOLIO_RISK/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-ANALYZE_PORTFOLIO_RISK`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-07"></a>

### - [ ] Task 10.07 — FEAT-POR-MERGE_PORTFOLIOS — Merge and split portfolio definitions with lineage

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 10.01.

#### i. Feature and remaining work

A user can reorganize compatible compositions without losing constituent identity or double-counting capital.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-MERGE_PORTFOLIOS-001 | Preview exact constituent/weight/capital/currency/sample conflicts for merge/split operations. |
| FR-TRC-POR-MERGE_PORTFOLIOS-002 | Commit accepted operations as new immutable portfolio revisions with source lineage. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-MERGE_PORTFOLIOS-001 | Removing FEAT-POR-MERGE_PORTFOLIOS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-MERGE_PORTFOLIOS-001 | Overlapping capital or duplicate strategy references are explicit and cannot be silently combined. |
| AT-POR-MERGE_PORTFOLIOS-002 | Old portfolios/results remain unchanged; native exchange round-trips the merged/split references and weighting semantics. |
| ATN-POR-MERGE_PORTFOLIOS-001 | Disable and physically remove merge_portfolios; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/merge_portfolios/test_traceability.py`; `tests/services/portfolio/merge_portfolios/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Preview exact constituent/weight/capital/currency/sample conflicts for merge/split operations. Expected: Overlapping capital or duplicate strategy references are explicit and cannot be silently combined. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-MERGE_PORTFOLIOS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-MERGE_PORTFOLIOS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-08"></a>

### - [ ] Task 10.08 — FEAT-POR-SEARCH_PORTFOLIOS — Search constrained portfolio combinations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Portfolio · **Owner specification:** `app/services/portfolio/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.18, 4.07, 4.14, 10.01, 10.02, 10.04, 10.05.

#### i. Feature and remaining work

Portfolio Builder explores a bounded candidate universe and commits only selected combinations with complete constituent evidence.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-POR-SEARCH_PORTFOLIOS-001 | Resolve an immutable databank/query universe and validate min/max constituent count, symbols/sectors/groups/sample/currency/capital/correlation constraints. |
| FR-TRC-POR-SEARCH_PORTFOLIOS-002 | Estimate and lazily execute finite brute-force/evolutionary work under candidate/result/evaluation/time budgets and seeds. |
| FR-TRC-POR-SEARCH_PORTFOLIOS-003 | Rank using registered portfolio metrics and atomically commit selected candidates to a target set/bank with all lineage. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-POR-SEARCH_PORTFOLIOS-001 | Removing FEAT-POR-SEARCH_PORTFOLIOS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-POR-SEARCH_PORTFOLIOS-001 | The accepted population is explicit; impossible eligibility yields reasons before combinatorial allocation. |
| AT-POR-SEARCH_PORTFOLIOS-002 | Maximum portfolio count and stop rules are enforced; no full power set is held in memory. |
| AT-POR-SEARCH_PORTFOLIOS-003 | Intermediate candidates are distinguishable from committed membership; retry publishes no duplicate accepted candidate. |
| ATN-POR-SEARCH_PORTFOLIOS-001 | Disable and physically remove search_portfolios; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/portfolio/search_portfolios/test_traceability.py`; `tests/services/portfolio/search_portfolios/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve an immutable databank/query universe and validate min/max constituent count, symbols/sectors/groups/sample/currency/capital/correlation constraints. Expected: The accepted population is explicit; impossible eligibility yields reasons before combinatorial allocation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-POR-SEARCH_PORTFOLIOS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(portfolio): complete FEAT-POR-SEARCH_PORTFOLIOS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-09"></a>

### - [ ] Task 10.09 — FEAT-AGT-ADVISE_PORTFOLIO — Expiring Portfolio and Risk Advisory

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.15, 1.19, 1.20, 1.23, 1.24, 4.03, 5.03, 5.06, 5.07, 7.03, 10.01, 10.06.

#### i. Feature and remaining work

Use current account/allocation/analytics/mandate/risk evidence for nonbinding weights/ranges/questions/uncertainty and strict expiry.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-ADVISE_PORTFOLIO_ALLOCATION | Use current account/allocation/analytics/mandate/risk evidence for nonbinding weights/ranges/questions/uncertainty and strict expiry. |
| FR-AGT-CHALLENGE_PORTFOLIO_RISK | Require independent review of mandate/barrier/tail/concentration/liquidity/correlation/leverage/operations/model/compliance/data concerns. |
| FR-AGT-EXPIRE_PORTFOLIO_ADVICE | Prevent reuse/submission when advisory expiry or source freshness has elapsed. |
| FR-AGT-PRESERVE_PORTFOLIO_AUTHORITY | Use normal Portfolio/Risk review contracts and respect their independent denial/decision. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-ADVISE_PORTFOLIO-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-ADVISE_PORTFOLIO-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-ADVISE_PORTFOLIO-001 | No lot/quantity/notional/order/approval field is accepted; wrong or stale account evidence refuses. |
| AT-AGT-ADVISE_PORTFOLIO-002 | Required risk-kind set and dissent remain visible; absence of objection is not consent. |
| AT-AGT-ADVISE_PORTFOLIO-003 | At the exact expiry boundary the advice is unavailable for handoff; an already-expired input is rejected. |
| AT-AGT-ADVISE_PORTFOLIO-004 | No direct Portfolio mutation, live allocation or Risk approval can originate from the advisory. |
| ATN-AGT-ADVISE_PORTFOLIO-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-ADVISE_PORTFOLIO-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/advise_portfolio/test_traceability.py`; `tests/services/agentic/advise_portfolio/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Use current account/allocation/analytics/mandate/risk evidence for nonbinding weights/ranges/questions/uncertainty and strict expiry. Expected: No lot/quantity/notional/order/approval field is accepted; wrong or stale account evidence refuses. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-ADVISE_PORTFOLIO/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-ADVISE_PORTFOLIO`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-10"></a>

### - [ ] Task 10.10 — FEAT-IFACE-OPERATE_PORTFOLIOS — Expose portfolio composition, search and analysis

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.08, 10.01, 10.02, 10.04, 10.05, 10.06, 10.07, 10.08.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-OPERATE_PORTFOLIOS-001 | Translate versioned portfolio definitions, weighting/search constraints and explicit aggregation/resimulation modes. |
| FR-TRC-IFACE-OPERATE_PORTFOLIOS-002 | Page matrices/candidates/constituents and preserve null/partial/infeasible evidence. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-OPERATE_PORTFOLIOS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-OPERATE_PORTFOLIOS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-OPERATE_PORTFOLIOS-001 | A stale revision conflicts; live approval is never inferred from a successful research request. |
| AT-IFACE-OPERATE_PORTFOLIOS-002 | Transport never calculates covariance, optimization or combined cashflows. |
| ATN-IFACE-OPERATE_PORTFOLIOS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-OPERATE_PORTFOLIOS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/operate_portfolios/test_traceability.py`; `tests/services/interfaces/operate_portfolios/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate versioned portfolio definitions, weighting/search constraints and explicit aggregation/resimulation modes. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: A stale revision conflicts; live approval is never inferred from a successful research request. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-OPERATE_PORTFOLIOS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-OPERATE_PORTFOLIOS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-11"></a>

### - [ ] Task 10.11 — FEAT-UI-PORTFOLIO_COMPOSER — Compose and compare a portfolio

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.01, 1.02, 1.06, 10.05, 10.10.

#### i. Feature and remaining work

Build a versioned composition with explicit weights, capital, compatibility and evaluation mode.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-PORTFOLIO_COMPOSER-001 | Display exact constituent sources, compatibility issues and weight/capital policy, including solver infeasibility. |
| FR-TRC-UI-PORTFOLIO_COMPOSER-002 | Save definitions and request ledger aggregation or interacting tick simulation as separate owner actions. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-PORTFOLIO_COMPOSER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-PORTFOLIO_COMPOSER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-PORTFOLIO_COMPOSER-001 | No silent weight normalization, constraint relaxation or hidden Buy & Hold series occurs. |
| AT-UI-PORTFOLIO_COMPOSER-002 | Closing/reordering the widget does not change business results; accepted output includes real run receipts. |
| ATN-UI-PORTFOLIO_COMPOSER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-PORTFOLIO_COMPOSER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/portfolio-composer/__tests__/traceability.test.tsx`; `app/ui/src/widgets/portfolio-composer/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Compose and compare a portfolio). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: No silent weight normalization, constraint relaxation or hidden Buy & Hold series occurs. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-PORTFOLIO_COMPOSER/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-PORTFOLIO_COMPOSER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-10-12"></a>

### - [ ] Task 10.12 — FEAT-UI-PORTFOLIO_BUILDER — Search a bounded portfolio universe

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U7.

**Order prerequisites:** 1.01, 1.02, 1.06, 10.03, 10.08, 10.09, 10.10.

#### i. Feature and remaining work

Search compatible combinations and inspect why candidates met or failed the selected constraints.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-PORTFOLIO_BUILDER-001 | Preview the resolved population, combination estimate and finite work/retention constraints. |
| FR-TRC-UI-PORTFOLIO_BUILDER-002 | Observe candidate/attempt progress and preview atomic selected membership publication. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-PORTFOLIO_BUILDER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-PORTFOLIO_BUILDER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-PORTFOLIO_BUILDER-001 | The browser does not materialize a power set or calculate correlation. |
| AT-UI-PORTFOLIO_BUILDER-002 | Intermediate results are not confused with committed portfolios; every candidate retains constituent lineage. |
| ATN-UI-PORTFOLIO_BUILDER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-PORTFOLIO_BUILDER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/portfolio-builder/__tests__/traceability.test.tsx`; `app/ui/src/widgets/portfolio-builder/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Search a bounded portfolio universe). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: The browser does not materialize a power set or calculate correlation. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-PORTFOLIO_BUILDER/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P10 — Send databank results to Portfolio Composer, inspect alignment and currency warnings, allocate weights, simulate shared capital, search combinations, save a portfolio and inspect advisory/correlation decisions. Publish `docs/dev/evidence/phases/phase-10.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-PORTFOLIO_BUILDER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-11"></a>

## Phase 11 — Research projects, notifications, memory and calibration

**Feature tasks: 9.** Project definitions/runner/utilities/notifications + matured outcome observations + Agentic memory/calibration → Project gateway → project editor and existing Jobs/Chat Bot surfaces.

**Visible completion:** Publish a finite Data → research → retest → optimize → portfolio → notification project, restart during a node attempt, then inspect receiver receipts, recovered history and bounded Agentic memory/calibration.

**Phase evidence:** `tests/ui/e2e/research/phase_11.spec.ts` and `docs/dev/evidence/phases/phase-11.json`, owned by Task 11.09. All prior affected UI/data/recovery regressions remain required.

<a id="task-11-01"></a>

### - [ ] Task 11.01 — FEAT-TRD-OBSERVE_OUTCOMES — Expose matured execution outcomes read-only

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Trading · **Owner specification:** `app/services/trading/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.04.

#### i. Feature and remaining work

Calibration can compare an earlier claim with real owner-authored outcomes after its horizon has closed.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-TRD-OBSERVE_OUTCOMES-001 | Resolve execution outcome references with account scope, horizon maturity, costs, revisions and integrity metadata. |
| FR-TRC-TRD-OBSERVE_OUTCOMES-002 | Expose no mutation, order, credential, kill-switch or deployment operation to an Agentic consumer. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-TRD-OBSERVE_OUTCOMES-001 | Removing FEAT-TRD-OBSERVE_OUTCOMES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-TRD-OBSERVE_OUTCOMES-001 | An open horizon, ambiguous match or unauthorized account cannot produce a mature outcome. |
| AT-TRD-OBSERVE_OUTCOMES-002 | Capability/schema negative tests show read projections only; removing this feature leaves non-Trading calibration routes available. |
| ATN-TRD-OBSERVE_OUTCOMES-001 | Disable and physically remove observe_outcomes; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/trading/observe_outcomes/test_traceability.py`; `tests/services/trading/observe_outcomes/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Resolve execution outcome references with account scope, horizon maturity, costs, revisions and integrity metadata. Expected: An open horizon, ambiguous match or unauthorized account cannot produce a mature outcome. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-TRD-OBSERVE_OUTCOMES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(trading): complete FEAT-TRD-OBSERVE_OUTCOMES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-02"></a>

### - [ ] Task 11.02 — FEAT-ORCH-DEFINE_PROJECTS — Publish typed research project graphs

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.09.

#### i. Feature and remaining work

A user can compose reusable owner operations into a valid finite project with clear inputs and outputs.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-DEFINE_PROJECTS-001 | Create/open/clone/rename/edit/reorder/disable tasks and publish a typed graph with versioned capability and input/output schemas. |
| FR-TRC-ORCH-DEFINE_PROJECTS-002 | Validate missing capabilities, schema mismatches, unreachable nodes and finite control flow before publication/run planning. |
| FR-TRC-ORCH-DEFINE_PROJECTS-003 | Preview schema-compatible copy/mass-configuration/symbol changes and list incompatible fields rather than dropping them. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-DEFINE_PROJECTS-001 | Removing FEAT-ORCH-DEFINE_PROJECTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-DEFINE_PROJECTS-001 | A post-publish edit creates a new revision and cannot change an active run. |
| AT-ORCH-DEFINE_PROJECTS-002 | An unbounded Go To loop or recursive Agentic/Research ancestry is rejected; an explicitly budget-bounded loop retains its bound in the plan. |
| AT-ORCH-DEFINE_PROJECTS-003 | Mass apply affects only the accepted compatible field set; source and target revisions are recorded. |
| ATN-ORCH-DEFINE_PROJECTS-001 | Disable and physically remove define_projects; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/define_projects/test_traceability.py`; `tests/services/orchestration/define_projects/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/open/clone/rename/edit/reorder/disable tasks and publish a typed graph with versioned capability and input/output schemas. Expected: A post-publish edit creates a new revision and cannot change an active run. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-DEFINE_PROJECTS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.16 (FEAT-STRAT-EXCHANGE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-DEFINE_PROJECTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-03"></a>

### - [ ] Task 11.03 — FEAT-ORCH-EXECUTE_UTILITIES — Execute authorized project utility actions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.04, 1.17, 1.18, 4.13.

#### i. Feature and remaining work

Projects can wait, perform scoped file/resource actions, log statistics or request sandbox scripts without unrestricted shell/filesystem authority.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-EXECUTE_UTILITIES-001 | Validate typed wait, stop/start, scoped load/save/delete, log-statistics and script task inputs with finite deadlines and permissions. |
| FR-TRC-ORCH-EXECUTE_UTILITIES-002 | Delegate irreversible effects through the owning capability and retain idempotency/reconciliation receipts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-EXECUTE_UTILITIES-001 | Removing FEAT-ORCH-EXECUTE_UTILITIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-EXECUTE_UTILITIES-001 | A host path, arbitrary browser expression or undeclared operation is rejected before side effects. |
| AT-ORCH-EXECUTE_UTILITIES-002 | An uncertain delete/save/script retry checks the owner receipt; logs are bounded/redacted and never execute markup. |
| ATN-ORCH-EXECUTE_UTILITIES-001 | Disable and physically remove execute_utilities; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/execute_utilities/test_traceability.py`; `tests/services/orchestration/execute_utilities/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate typed wait, stop/start, scoped load/save/delete, log-statistics and script task inputs with finite deadlines and permissions. Expected: A host path, arbitrary browser expression or undeclared operation is rejected before side effects. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-EXECUTE_UTILITIES/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-PLUG-ISOLATE_ANALYSIS (Task 12.03, Phase 12). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-EXECUTE_UTILITIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-04"></a>

### - [ ] Task 11.04 — FEAT-ORCH-DELIVER_NOTIFICATIONS — Deliver scoped notifications through a durable outbox

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.04, 1.10, 1.12, 1.18.

#### i. Feature and remaining work

A project can notify the intended recipient without leaking credentials or silently duplicating a message after retry.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-DELIVER_NOTIFICATIONS-001 | Version in-app/SMTP channel, recipient references, condition, template and explicit authorized test-send settings. |
| FR-TRC-ORCH-DELIVER_NOTIFICATIONS-002 | Persist a delivery intent and idempotency identity before dispatch; reconcile attempts and disclose uncertain external delivery. |
| FR-TRC-ORCH-DELIVER_NOTIFICATIONS-003 | Add webhook/message-channel adapters under the same permissions, finite egress/rate limits and redaction policy in U13. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-DELIVER_NOTIFICATIONS-001 | Removing FEAT-ORCH-DELIVER_NOTIFICATIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-DELIVER_NOTIFICATIONS-001 | Server/port/TLS/sender/test-recipient inputs validate before send; the test has its own audited user action. |
| AT-ORCH-DELIVER_NOTIFICATIONS-002 | A restart cannot silently resend an already acknowledged message; unknown delivery remains visible rather than claiming exactly-once external effects. |
| AT-ORCH-DELIVER_NOTIFICATIONS-003 | An unregistered destination or secret-bearing payload is denied; one channel’s removal leaves others usable. |
| ATN-ORCH-DELIVER_NOTIFICATIONS-001 | Disable and physically remove deliver_notifications; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/deliver_notifications/test_traceability.py`; `tests/services/orchestration/deliver_notifications/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version in-app/SMTP channel, recipient references, condition, template and explicit authorized test-send settings. Expected: Server/port/TLS/sender/test-recipient inputs validate before send; the test has its own audited user action. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-DELIVER_NOTIFICATIONS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 1.25 (FEAT-IFACE-OPERATE_SETTINGS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-DELIVER_NOTIFICATIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-05"></a>

### - [ ] Task 11.05 — FEAT-AGT-MANAGE_MEMORY — Governed Memory

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.09, 1.15, 1.19, 5.03.

#### i. Feature and remaining work

Separate task working context, episodic outcomes, validated semantic memory and audit classes with explicit scope/retention.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-CLASSIFY_MEMORY | Separate task working context, episodic outcomes, validated semantic memory and audit classes with explicit scope/retention. |
| FR-AGT-PROMOTE_MEMORY | Validate provenance, evidence, trust, redaction, sensitivity, freshness, poisoning, dedup/supersession, retention and required approval before promotion. |
| FR-AGT-RETRIEVE_MEMORY | Retrieve only bounded authorized task/user/account records and revalidate freshness at use time. |
| FR-AGT-RETAIN_AND_PURGE_MEMORY | Apply class TTL/export/legal hold and append-only correction/supersession within a supported RETAIN namespace. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-MANAGE_MEMORY-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-MANAGE_MEMORY-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-MANAGE_MEMORY-001 | Unknown/cross-class operations fail and workflow progress remains the workflow owner’s truth. |
| AT-AGT-MANAGE_MEMORY-002 | Secret, stale, forged, duplicate or poisoned content cannot become reusable semantic memory. |
| AT-AGT-MANAGE_MEMORY-003 | Memory cannot substitute for a material current owner fact or grant permission/approval. |
| AT-AGT-MANAGE_MEMORY-004 | TTL cleanup respects holds; corrections preserve historical records; removal deletes only eligible ephemeral content. |
| ATN-AGT-MANAGE_MEMORY-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-MANAGE_MEMORY-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/manage_memory/test_traceability.py`; `tests/services/agentic/manage_memory/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Separate task working context, episodic outcomes, validated semantic memory and audit classes with explicit scope/retention. Expected: Unknown/cross-class operations fail and workflow progress remains the workflow owner’s truth. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-MANAGE_MEMORY/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 5.04 (FEAT-AGT-RUN_WORKFLOWS), Task 5.08 (FEAT-AGT-ASSIST_OPERATOR). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-MANAGE_MEMORY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-06"></a>

### - [ ] Task 11.06 — FEAT-ORCH-RUN_PROJECTS — Run and recover selected project scopes

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.18, 2.24, 3.16, 5.04, 6.06, 9.01, 10.08, 11.02, 11.03, 11.04.

#### i. Feature and remaining work

A project can run wholly, from a chosen task or only one task with transparent reused inputs and durable attempt history.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-RUN_PROJECTS-001 | Preview exact whole/from-here/only node sets and resolve required inputs, reused outputs and skipped work against a pinned graph. |
| FR-TRC-ORCH-RUN_PROJECTS-002 | Evaluate cycle/duration/evaluated/result/runtime conditions deterministically from stored snapshots and enforce all loop/resource limits. |
| FR-TRC-ORCH-RUN_PROJECTS-003 | Record project → run → node attempt → domain run → artifact/receipt lineage, preserve retries and resume only compatible checkpoints. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-RUN_PROJECTS-001 | Removing FEAT-ORCH-RUN_PROJECTS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-RUN_PROJECTS-001 | Missing or stale upstream output blocks the planned scope; selection never silently uses current mutable state. |
| AT-ORCH-RUN_PROJECTS-002 | Boundary fixtures follow the same branch after replay; a budget exhaustion yields a typed terminal reason, not an endless loop. |
| AT-ORCH-RUN_PROJECTS-003 | Restart reconstructs the same completed nodes and reconciles uncertain receiver calls before further dispatch. |
| ATN-ORCH-RUN_PROJECTS-001 | Disable and physically remove run_projects; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/run_projects/test_traceability.py`; `tests/services/orchestration/run_projects/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Preview exact whole/from-here/only node sets and resolve required inputs, reused outputs and skipped work against a pinned graph. Expected: Missing or stale upstream output blocks the planned scope; selection never silently uses current mutable state. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-RUN_PROJECTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-RUN_PROJECTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-07"></a>

### - [ ] Task 11.07 — FEAT-AGT-CALIBRATE_OUTCOMES — Post-Horizon Outcome Calibration

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.09, 1.15, 1.19, 1.23, 4.07, 4.10, 5.05, 5.06, 10.05, 11.01.

#### i. Feature and remaining work

Match immutable forecast/recommendation target/horizon/observation rules to later authoritative outcomes without rewriting the original.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-MATCH_OUTCOMES | Match immutable forecast/recommendation target/horizon/observation rules to later authoritative outcomes without rewriting the original. |
| FR-AGT-SCORE_CALIBRATION | Compute declared probability/direction/magnitude/invalidation/rejection/latency/cost scores with finite deterministic arithmetic. |
| FR-AGT-ATTRIBUTE_INCREMENTAL_VALUE | Compare deterministic/single-agent baselines and role/round/prompt/model/tool/topology value after cost and uncertainty. |
| FR-AGT-PROPOSE_PROFILE_CHANGES | Emit an immutable candidate change with evidence and required independent review/evaluation. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-CALIBRATE_OUTCOMES-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-CALIBRATE_OUTCOMES-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-CALIBRATE_OUTCOMES-001 | Open/ambiguous/revised/unmatched horizons remain unavailable or explicitly amended; no hindsight mutation occurs. |
| AT-AGT-CALIBRATE_OUTCOMES-002 | Brier/log-loss/other selected scoring fixtures handle missing/nonfinite outcomes explicitly and repeat deterministically. |
| AT-AGT-CALIBRATE_OUTCOMES-003 | Raw P&L alone cannot establish value; ablation and luck/cost counterexamples prevent unsupported attribution. |
| AT-AGT-CALIBRATE_OUTCOMES-004 | No prompt/mandate/permission/threshold/model/eligibility can change directly from calibration output. |
| ATN-AGT-CALIBRATE_OUTCOMES-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-CALIBRATE_OUTCOMES-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/calibrate_outcomes/test_traceability.py`; `tests/services/agentic/calibrate_outcomes/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Match immutable forecast/recommendation target/horizon/observation rules to later authoritative outcomes without rewriting the original. Expected: Open/ambiguous/revised/unmatched horizons remain unavailable or explicitly amended; no hindsight mutation occurs. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-CALIBRATE_OUTCOMES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-CALIBRATE_OUTCOMES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-08"></a>

### - [ ] Task 11.08 — FEAT-IFACE-EDIT_PROJECTS — Expose project graph editing and run scopes

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.08, 11.02, 11.06.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-EDIT_PROJECTS-001 | Translate graph revision and whole/from-here/only commands to the Orchestration owner. |
| FR-TRC-IFACE-EDIT_PROJECTS-002 | Stream/inspect node attempt, condition and receiver lineage with permission-gated controls. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-EDIT_PROJECTS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-EDIT_PROJECTS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-EDIT_PROJECTS-001 | No UI coordinate or current mutable setting replaces the pinned graph/input plan. |
| AT-IFACE-EDIT_PROJECTS-002 | Interfaces does not schedule multi-step domain work or resolve loop conditions privately. |
| ATN-IFACE-EDIT_PROJECTS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-EDIT_PROJECTS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/edit_projects/test_traceability.py`; `tests/services/interfaces/edit_projects/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate graph revision and whole/from-here/only commands to the Orchestration owner. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: No UI coordinate or current mutable setting replaces the pinned graph/input plan. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-EDIT_PROJECTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-EDIT_PROJECTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-11-09"></a>

### - [ ] Task 11.09 — FEAT-UI-PROJECT_EDITOR — Compose and control a research project

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U8.

**Order prerequisites:** 1.01, 1.02, 1.06, 11.04, 11.05, 11.06, 11.07, 11.08.

#### i. Feature and remaining work

Build a typed graph and execute a reviewed scope without scripting hidden cross-domain behavior in the browser.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-PROJECT_EDITOR-001 | Render graph and accessible ordered-list forms with owner diagnostics and separate layout coordinates. |
| FR-TRC-UI-PROJECT_EDITOR-002 | Preview reused inputs/skips/exact selected nodes and display condition/attempt/receiver/artifact lineage. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-PROJECT_EDITOR-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-PROJECT_EDITOR-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-PROJECT_EDITOR-001 | Graph cycles/unbounded loops/incompatible inputs are owner errors; dragging a node cannot alter a running graph revision. |
| AT-UI-PROJECT_EDITOR-002 | Retry/pause/stop follows owner state; UI never privately calls a sequence of domain commands. |
| ATN-UI-PROJECT_EDITOR-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-PROJECT_EDITOR-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/project-editor/__tests__/traceability.test.tsx`; `app/ui/src/widgets/project-editor/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Compose and control a research project). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Graph cycles/unbounded loops/incompatible inputs are owner errors; dragging a node cannot alter a running graph revision. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-PROJECT_EDITOR/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P11 — Publish a finite Data → research → retest → optimize → portfolio → notification project, restart during a node attempt, then inspect receiver receipts, recovered history and bounded Agentic memory/calibration. Publish `docs/dev/evidence/phases/phase-11.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-PROJECT_EDITOR`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-12"></a>

## Phase 12 — Safe extension development, source generation and indicator testing

**Feature tasks: 13.** Plugin sandbox/build/lifecycle/resources/compatibility + governed custom analysis + MQL5/Python generators + Agentic sandbox fallback → capability-administration gateway → Code Editor and Indicator Tester.

**Visible completion:** Fork a scoped plugin resource, edit it in Code Editor, build/test in an attested sandbox, inspect Indicator Tester discrepancies, preview a read-only result panel, then install and remove the extension explicitly.

**Phase evidence:** `tests/ui/e2e/research/phase_12.spec.ts` and `docs/dev/evidence/phases/phase-12.json`, owned by Task 12.13. All prior affected UI/data/recovery regressions remain required.

<a id="task-12-01"></a>

### - [ ] Task 12.01 — FEAT-PLUG-SANDBOX_PERMISSIONS — Attest bounded plugin permissions and sandbox leases

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.04, 1.14.

#### i. Feature and remaining work

An untrusted build or panel runs only within explicit resource, path, credential and network limits.

**Reuse:** `app/services/plugins/permissions_sandbox`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-SANDBOX_PERMISSIONS-001 | Issue purpose/object/generation-bound isolation leases with CPU/memory/storage/process/time/egress limits and credential absence. |
| FR-TRC-PLUG-SANDBOX_PERMISSIONS-002 | Validate raw and resolved paths against traversal, absolute/drive/UNC/device/reserved-name/symlink escape and revoke exact leases. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-SANDBOX_PERMISSIONS-001 | Removing FEAT-PLUG-SANDBOX_PERMISSIONS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-SANDBOX_PERMISSIONS-001 | Missing attestation or requested unrestricted host access fails before model invocation or staging writes. |
| AT-PLUG-SANDBOX_PERMISSIONS-002 | Adversarial path fixtures cannot escape staging; expired/revoked leases deny new effects even after restart. |
| ATN-PLUG-SANDBOX_PERMISSIONS-001 | Disable and physically remove sandbox_permissions; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/sandbox_permissions/test_traceability.py`; `tests/services/plugins/sandbox_permissions/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Issue purpose/object/generation-bound isolation leases with CPU/memory/storage/process/time/egress limits and credential absence. Expected: Missing attestation or requested unrestricted host access fails before model invocation or staging writes. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-SANDBOX_PERMISSIONS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-SANDBOX_PERMISSIONS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-02"></a>

### - [ ] Task 12.02 — FEAT-PLUG-AUTHOR_PACKAGES — Edit versioned extension resources

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.05, 1.09, 1.17.

#### i. Feature and remaining work

A developer can create, fork, search and save a plugin package without unrestricted filesystem access or losing edits.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-AUTHOR_PACKAGES-001 | Create/fork/clone/rename/delete package-scoped resources, protecting standard sources until explicitly forked. |
| FR-TRC-PLUG-AUTHOR_PACKAGES-002 | Save/save-as/save-all with expected revision and three-way conflict evidence. |
| FR-TRC-PLUG-AUTHOR_PACKAGES-003 | Search within authorized package/file scopes with bounded results and preserve source/dependency/resource manifests for export. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-AUTHOR_PACKAGES-001 | Removing FEAT-PLUG-AUTHOR_PACKAGES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-AUTHOR_PACKAGES-001 | A host path or another package’s resource is inaccessible; builtin source edits produce a new user fork. |
| AT-PLUG-AUTHOR_PACKAGES-002 | Concurrent external edits never silently overwrite dirty state; accepted resolution creates immutable revisions. |
| AT-PLUG-AUTHOR_PACKAGES-003 | Cross-plugin text is not leaked; export excludes secrets and names exact resources and hashes. |
| ATN-PLUG-AUTHOR_PACKAGES-001 | Disable and physically remove author_packages; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/author_packages/test_traceability.py`; `tests/services/plugins/author_packages/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create/fork/clone/rename/delete package-scoped resources, protecting standard sources until explicitly forked. Expected: A host path or another package’s resource is inaccessible; builtin source edits produce a new user fork. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-AUTHOR_PACKAGES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(plugins): complete FEAT-PLUG-AUTHOR_PACKAGES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-03"></a>

### - [ ] Task 12.03 — FEAT-PLUG-ISOLATE_ANALYSIS — Build and test untrusted code in isolation

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.17, 1.22, 12.01.

#### i. Feature and remaining work

Code compilation, indicator tests and ML/toolchain execution produce evidence without running untrusted source in the application process.

**Reuse:** `app/services/plugins/analysis_boundary`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-ISOLATE_ANALYSIS-001 | Run selected pinned toolchains against authorized immutable source/test artifacts only after sandbox/resource admission. |
| FR-TRC-PLUG-ISOLATE_ANALYSIS-002 | Capture file/range diagnostics, dependency sources/SBOM, tests, hashes and bounded redacted logs. |
| FR-TRC-PLUG-ISOLATE_ANALYSIS-003 | Cancel/timeout/revoke and clean resources/staging according to retention while preserving immutable metadata. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-ISOLATE_ANALYSIS-001 | Removing FEAT-PLUG-ISOLATE_ANALYSIS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-ISOLATE_ANALYSIS-001 | No arbitrary host path, inherited production credential or undeclared network destination is reachable. |
| AT-PLUG-ISOLATE_ANALYSIS-002 | Compile errors cannot inject host markup; a successful test does not install/import/deploy its output. |
| AT-PLUG-ISOLATE_ANALYSIS-003 | Failure and repeated cleanup leave no process, mapping, worker, listener or staged byte beyond its policy. |
| ATN-PLUG-ISOLATE_ANALYSIS-001 | Disable and physically remove isolate_analysis; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/isolate_analysis/test_traceability.py`; `tests/services/plugins/isolate_analysis/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Run selected pinned toolchains against authorized immutable source/test artifacts only after sandbox/resource admission. Expected: No arbitrary host path, inherited production credential or undeclared network destination is reachable. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-ISOLATE_ANALYSIS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 11.03 (FEAT-ORCH-EXECUTE_UTILITIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-ISOLATE_ANALYSIS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-04"></a>

### - [ ] Task 12.04 — FEAT-PLUG-RENDER_RESULT_PANELS — Host isolated read-only result panels

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.12, 12.01.

#### i. Feature and remaining work

Custom HTML/JavaScript analysis panels can be useful without acquiring host origin, database or credential privileges.

**Reuse:** `app/services/plugins/result_panels`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-RENDER_RESULT_PANELS-001 | Create a sandboxed non-host-privileged frame/renderer with explicit result-schema compatibility and default-deny network/navigation/download policy. |
| FR-TRC-PLUG-RENDER_RESULT_PANELS-002 | Validate allowlisted bridge messages and bound CPU/time/memory/event rate and payload size. |
| FR-TRC-PLUG-RENDER_RESULT_PANELS-003 | Contain crash/reset/removal and dispose exact subscriptions/frames/resources. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-RENDER_RESULT_PANELS-001 | Removing FEAT-PLUG-RENDER_RESULT_PANELS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-RENDER_RESULT_PANELS-001 | A hostile panel cannot access host globals, cookies, tokens, SQL, files or another result. |
| AT-PLUG-RENDER_RESULT_PANELS-002 | Unknown message commands and schema-smuggled actions are rejected; panel output never invokes a host command by parsing prose. |
| AT-PLUG-RENDER_RESULT_PANELS-003 | A crashed panel does not block built-in Results or alter its data; repeated mount/unmount leaves no listener/timer leaks. |
| ATN-PLUG-RENDER_RESULT_PANELS-001 | Disable and physically remove render_result_panels; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/render_result_panels/test_traceability.py`; `tests/services/plugins/render_result_panels/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Create a sandboxed non-host-privileged frame/renderer with explicit result-schema compatibility and default-deny network/navigation/download policy. Expected: A hostile panel cannot access host globals, cookies, tokens, SQL, files or another result. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-RENDER_RESULT_PANELS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-RENDER_RESULT_PANELS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-05"></a>

### - [ ] Task 12.05 — FEAT-STRAT-GENERATE_MQL5 — Generate verified MQL5 artifacts

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.17, 3.13, 12.03.

#### i. Feature and remaining work

A compatible HSL strategy can be exported as MQL5 without silently changing its trading or numerical behavior.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-GENERATE_MQL5-001 | Lower the same target-neutral plan to each advertised target using pinned operator, numerical, clock and position-policy mappings. |
| FR-TRC-STRAT-GENERATE_MQL5-002 | Run target parsing/compilation and golden indicator/signal/inference vectors on normal, boundary, missing and sequence-reset cases. |
| FR-TRC-STRAT-GENERATE_MQL5-003 | Publish reproducible artifacts with target/version/options, resources, hashes and restriction support matrix. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-GENERATE_MQL5-001 | Removing FEAT-STRAT-GENERATE_MQL5 withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-GENERATE_MQL5-001 | Unsupported constructs fail before executable-success publication; source snapshots retain source-node diagnostics. |
| AT-STRAT-GENERATE_MQL5-002 | A target lacking a compatible toolchain remains UNVERIFIED_TARGET; accepted discrete fields match exactly and floats stay within declared tolerances. |
| AT-STRAT-GENERATE_MQL5-003 | Rebuilds under the same qualified toolchain meet the declared reproducibility policy and never activate trading. |
| ATN-STRAT-GENERATE_MQL5-001 | Disable and physically remove generate_mql5; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/generate_mql5/test_traceability.py`; `tests/services/strategy/generate_mql5/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Lower the same target-neutral plan to each advertised target using pinned operator, numerical, clock and position-policy mappings. Expected: Unsupported constructs fail before executable-success publication; source snapshots retain source-node diagnostics. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-GENERATE_MQL5/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-RES-VALIDATE_MODELS (Task 14.05, Phase 14). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-GENERATE_MQL5`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-06"></a>

### - [ ] Task 12.06 — FEAT-STRAT-GENERATE_PYTHON — Generate verified Python research artifacts

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.17, 3.13, 12.03.

#### i. Feature and remaining work

A compatible HSL strategy can be exported as Python research without silently changing its trading or numerical behavior.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-GENERATE_PYTHON-001 | Lower the same target-neutral plan to each advertised target using pinned operator, numerical, clock and position-policy mappings. |
| FR-TRC-STRAT-GENERATE_PYTHON-002 | Run target parsing/compilation and golden indicator/signal/inference vectors on normal, boundary, missing and sequence-reset cases. |
| FR-TRC-STRAT-GENERATE_PYTHON-003 | Publish reproducible artifacts with target/version/options, resources, hashes and restriction support matrix. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-GENERATE_PYTHON-001 | Removing FEAT-STRAT-GENERATE_PYTHON withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-GENERATE_PYTHON-001 | Unsupported constructs fail before executable-success publication; source snapshots retain source-node diagnostics. |
| AT-STRAT-GENERATE_PYTHON-002 | A target lacking a compatible toolchain remains UNVERIFIED_TARGET; accepted discrete fields match exactly and floats stay within declared tolerances. |
| AT-STRAT-GENERATE_PYTHON-003 | Rebuilds under the same qualified toolchain meet the declared reproducibility policy and never activate trading. |
| ATN-STRAT-GENERATE_PYTHON-001 | Disable and physically remove generate_python; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/generate_python/test_traceability.py`; `tests/services/strategy/generate_python/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Lower the same target-neutral plan to each advertised target using pinned operator, numerical, clock and position-policy mappings. Expected: Unsupported constructs fail before executable-success publication; source snapshots retain source-node diagnostics. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-GENERATE_PYTHON/acceptance.json`. Record results; no pass is prefilled.

**Later-provider qualification:** FEAT-RES-VALIDATE_MODELS (Task 14.05, Phase 14). Complete this adapter now, prove its explicit unavailable path, and do not claim the future operation works until the provider task publishes real integration evidence. The exact conditions are in the owning README and `Operation_Readiness.md`.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-GENERATE_PYTHON`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-07"></a>

### - [ ] Task 12.07 — FEAT-ANA-PROVIDE_CUSTOM_ANALYSIS — Serve governed custom analysis projections

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.18, 4.13, 12.03, 12.04.

#### i. Feature and remaining work

A compatible extension receives only the result data and computed columns it is authorized to analyze.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-PROVIDE_CUSTOM_ANALYSIS-001 | Validate analysis provider/version, result schema, options, population, resource estimate and allowed read projection. |
| FR-TRC-ANA-PROVIDE_CUSTOM_ANALYSIS-002 | Run bounded analysis jobs and publish derived columns/artifacts with provider/definition/version/provenance and explicit unavailable states. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-PROVIDE_CUSTOM_ANALYSIS-001 | Removing FEAT-ANA-PROVIDE_CUSTOM_ANALYSIS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-PROVIDE_CUSTOM_ANALYSIS-001 | Wrong-schema or unauthorized columns fail before dispatch; no provider gets the raw database/filesystem/session token. |
| AT-ANA-PROVIDE_CUSTOM_ANALYSIS-002 | A plugin crash or removal leaves base metrics/databank content unchanged; outputs are never silently treated as canonical owner metrics. |
| ATN-ANA-PROVIDE_CUSTOM_ANALYSIS-001 | Disable and physically remove provide_custom_analysis; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/provide_custom_analysis/test_traceability.py`; `tests/services/analytics/provide_custom_analysis/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate analysis provider/version, result schema, options, population, resource estimate and allowed read projection. Expected: Wrong-schema or unauthorized columns fail before dispatch; no provider gets the raw database/filesystem/session token. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-PROVIDE_CUSTOM_ANALYSIS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 4.19 (FEAT-IFACE-OPERATE_RESULTS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-PROVIDE_CUSTOM_ANALYSIS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-08"></a>

### - [ ] Task 12.08 — FEAT-PLUG-MANAGE_LIFECYCLE — Quarantine, install and remove extension versions

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.05, 1.12, 1.17, 12.03.

#### i. Feature and remaining work

An extension can be installed or replaced without bypassing trust checks or corrupting retained domain artifacts.

**Reuse:** `app/services/plugins/lifecycle`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-MANAGE_LIFECYCLE-001 | Quarantine imported packages and verify manifest/schema/signature/permissions/resources/compatibility before separate install and enable actions. |
| FR-TRC-PLUG-MANAGE_LIFECYCLE-002 | Replace via generation-aware staging and exact contribution disposal; preserve old generation on precommit failure and report postcommit degradation truthfully. |
| FR-TRC-PLUG-MANAGE_LIFECYCLE-003 | Uninstall contributions without deleting unrelated or retained owner evidence. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-MANAGE_LIFECYCLE-001 | Removing FEAT-PLUG-MANAGE_LIFECYCLE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-MANAGE_LIFECYCLE-001 | A malicious or unverified package cannot run during preview; compile success is not installation approval. |
| AT-PLUG-MANAGE_LIFECYCLE-002 | Shadow failure leaves the old provider usable; cleanup failure after switch is not falsely described as a complete rollback. |
| AT-PLUG-MANAGE_LIFECYCLE-003 | Historic plugin artifacts remain typed opaque/unavailable when the provider disappears and can be recovered through authorized reinstall. |
| ATN-PLUG-MANAGE_LIFECYCLE-001 | Disable and physically remove manage_lifecycle; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/manage_lifecycle/test_traceability.py`; `tests/services/plugins/manage_lifecycle/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Quarantine imported packages and verify manifest/schema/signature/permissions/resources/compatibility before separate install and enable actions. Expected: A malicious or unverified package cannot run during preview; compile success is not installation approval. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-MANAGE_LIFECYCLE/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.16 (FEAT-STRAT-EXCHANGE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-MANAGE_LIFECYCLE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-09"></a>

### - [ ] Task 12.09 — FEAT-PLUG-MAINTAIN_COMPATIBILITY — Qualify extension and provider compatibility

**Status:** `PARTIAL` · **Domain:** Plugins · **Owner specification:** `app/services/plugins/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.05, 1.17, 12.03.

#### i. Feature and remaining work

A supported capability claim is backed by versioned tests rather than an installable package name.

**Reuse:** `app/services/plugins/development_compatibility`. The current Plugins package exists under its legacy semantic folder but is absent from the inspected Python feature entry-point group. Adapt it to the registered public target and the full bounded permission/lifecycle/compatibility scope; no duplicate plugin framework or domain algorithm owner.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-PLUG-MAINTAIN_COMPATIBILITY-001 | Bind conformance evidence to package/provider/contract/runtime versions and exact supported operations/targets. |
| FR-TRC-PLUG-MAINTAIN_COMPATIBILITY-002 | Run bounded compatibility/removal/upgrade suites through the approved isolation and evidence pipeline. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-PLUG-MAINTAIN_COMPATIBILITY-001 | Removing FEAT-PLUG-MAINTAIN_COMPATIBILITY withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-PLUG-MAINTAIN_COMPATIBILITY-001 | Changing a material version invalidates inherited compatibility; missing test evidence leaves the cell unverified. |
| AT-PLUG-MAINTAIN_COMPATIBILITY-002 | A provider cannot self-promote from its own declaration; stale/failed evidence blocks the affected support claim. |
| ATN-PLUG-MAINTAIN_COMPATIBILITY-001 | Disable and physically remove maintain_compatibility; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/plugins/maintain_compatibility/test_traceability.py`; `tests/services/plugins/maintain_compatibility/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Bind conformance evidence to package/provider/contract/runtime versions and exact supported operations/targets. Expected: Changing a material version invalidates inherited compatibility; missing test evidence leaves the cell unverified. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-PLUG-MAINTAIN_COMPATIBILITY/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `fix(plugins): complete FEAT-PLUG-MAINTAIN_COMPATIBILITY`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-10"></a>

### - [ ] Task 12.10 — FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS — Sandboxed Source Artifact Fallback

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Agentic · **Owner specification:** `app/services/agentic/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.09, 1.15, 1.17, 1.19, 1.20, 1.23, 1.24, 5.04, 6.10, 12.01, 12.03.

#### i. Feature and remaining work

Require the exact approved requirement and receiver-validated unsupported-expression report before source generation.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-AGT-PROVE_DSL_GAP | Require the exact approved requirement and receiver-validated unsupported-expression report before source generation. |
| FR-AGT-AUTHOR_SANDBOX_ARTIFACTS | Require authenticated specification and attested isolated credential-free staging lease with finite resource and egress policy. |
| FR-AGT-RECORD_ARTIFACT_MANIFEST | Capture every path/hash/size, dependency/source/SBOM, test/static-analysis result, provenance and full search history. |
| FR-AGT-ENFORCE_STAGING_ONLY | Never import generated code in the application, hot-load/register/deploy it or mutate the production repository directly. |
| FR-AGT-CLEANUP_SANDBOX_ARTIFACTS | Revoke leases and clean eligible staged/ephemeral bytes while retaining required metadata and cleanup receipts. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-AGT-AUTHOR_SANDBOX_ARTIFACTS-001 | All direct tool/model/receiver work obeys the feature’s exact configuration, mandate, current readiness/generation and unspent parent budgets. |
| NFR-TRC-AGT-AUTHOR_SANDBOX_ARTIFACTS-002 | Prove exact scope cleanup, strict contract/config compatibility and executable offline usage without paid providers or live credentials. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-AGT-AUTHOR_SANDBOX_ARTIFACTS-001 | Missing/changed/forged/expired/overbroad gap refuses before model call or file write. |
| AT-AGT-AUTHOR_SANDBOX_ARTIFACTS-002 | No valid lease means no generation/write; traversal/symlink/device paths and inherited credentials are denied. |
| AT-AGT-AUTHOR_SANDBOX_ARTIFACTS-003 | Unlisted files/dependencies or mutated hashes fail aggregate validation. |
| AT-AGT-AUTHOR_SANDBOX_ARTIFACTS-004 | Only sandbox execution and staged receiver intake are possible; own tests do not grant acceptance. |
| AT-AGT-AUTHOR_SANDBOX_ARTIFACTS-005 | Failure/cancel/removal/replacement produce idempotent cleanup and no surviving unauthorized resources. |
| ATN-AGT-AUTHOR_SANDBOX_ARTIFACTS-001 | Denied/expired/over-budget/resumed/removed-provider fixtures prove fail-closed behavior with no unauthorized receiver invocation. |
| ATN-AGT-AUTHOR_SANDBOX_ARTIFACTS-002 | 100 enable/disable cycles plus physical removal leave no leaked task/listener/lease/role/client/staging resource; implemented code meets the source coverage/quality gate. |


**Acceptance test targets:** `tests/services/agentic/author_sandbox_artifacts/test_traceability.py`; `tests/services/agentic/author_sandbox_artifacts/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Require the exact approved requirement and receiver-validated unsupported-expression report before source generation. Expected: Missing/changed/forged/expired/overbroad gap refuses before model call or file write. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(agentic): complete FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-11"></a>

### - [ ] Task 12.11 — FEAT-IFACE-ADMINISTER_CAPABILITIES — Expose extension lifecycle and development operations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.05, 1.08, 12.02, 12.03, 12.04, 12.08, 12.09.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-ADMINISTER_CAPABILITIES-001 | Translate exact package/resource identities and scoped lifecycle/build/permission commands. |
| FR-TRC-IFACE-ADMINISTER_CAPABILITIES-002 | Expose bounded diagnostics and actual generation/readiness/conformance results. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-ADMINISTER_CAPABILITIES-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-ADMINISTER_CAPABILITIES-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-ADMINISTER_CAPABILITIES-001 | Upload/inspection does not execute code or grant installation; all file/path parsing stays with owners. |
| AT-IFACE-ADMINISTER_CAPABILITIES-002 | A build success is never rewritten as deployed/eligible provider status. |
| ATN-IFACE-ADMINISTER_CAPABILITIES-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-ADMINISTER_CAPABILITIES-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/administer_capabilities/test_traceability.py`; `tests/services/interfaces/administer_capabilities/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Translate exact package/resource identities and scoped lifecycle/build/permission commands. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: Upload/inspection does not execute code or grant installation; all file/path parsing stays with owners. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-ADMINISTER_CAPABILITIES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-ADMINISTER_CAPABILITIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-12"></a>

### - [ ] Task 12.12 — FEAT-UI-CODE_EDITOR — Edit scoped code and inspect build evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.01, 1.02, 12.03, 12.04, 12.05, 12.06, 12.08, 12.11.

#### i. Feature and remaining work

Create or fork package resources and run isolated compilation/tests without unrestricted filesystem access.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-CODE_EDITOR-001 | Edit only authorized package resource IDs and show dirty/protected/fork/three-way revision conflict states. |
| FR-TRC-UI-CODE_EDITOR-002 | Submit bounded build/test requests and show exact file/range/code diagnostics with sanitized logs. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-CODE_EDITOR-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-CODE_EDITOR-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-CODE_EDITOR-001 | Builtin source is not overwritten; unsaved edits survive failed compile/save and conflicting revisions require review. |
| AT-UI-CODE_EDITOR-002 | No generated/imported code executes in the browser/app process; compile success does not install or deploy it. |
| ATN-UI-CODE_EDITOR-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-CODE_EDITOR-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/code-editor/__tests__/traceability.test.tsx`; `app/ui/src/widgets/code-editor/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Edit scoped code and inspect build evidence). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Builtin source is not overwritten; unsaved edits survive failed compile/save and conflicting revisions require review. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-CODE_EDITOR/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-CODE_EDITOR`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-12-13"></a>

### - [ ] Task 12.13 — FEAT-UI-INDICATOR_TESTER — Compare indicator providers and previews

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U9.

**Order prerequisites:** 1.01, 1.02, 1.06, 12.03, 12.07, 12.09, 12.10, 12.11.

#### i. Feature and remaining work

Verify an indicator’s actual values against a selected reference before treating it as compatible.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-INDICATOR_TESTER-001 | Configure explicit source data, provider/version/parameters, reference and numerical tolerance and show per-case results. |
| FR-TRC-UI-INDICATOR_TESTER-002 | Run tests/preview only in the declared isolated owner runtime and release it on cancellation/removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-INDICATOR_TESTER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-INDICATOR_TESTER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-INDICATOR_TESTER-001 | A missing file/provider or unsupported reference is unavailable; the UI does not compute the indicator itself. |
| AT-UI-INDICATOR_TESTER-002 | Expected/actual boundary and constant-series results remain visible; replay/live preview cannot inherit production credentials. |
| ATN-UI-INDICATOR_TESTER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-INDICATOR_TESTER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/indicator-tester/__tests__/traceability.test.tsx`; `app/ui/src/widgets/indicator-tester/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Compare indicator providers and previews). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A missing file/provider or unsupported reference is unavailable; the UI does not compute the indicator itself. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-INDICATOR_TESTER/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P12 — Fork a scoped plugin resource, edit it in Code Editor, build/test in an attested sandbox, inspect Indicator Tester discrepancies, preview a read-only result panel, then install and remove the extension explicitly. Publish `docs/dev/evidence/phases/phase-12.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-INDICATOR_TESTER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-13"></a>

## Phase 13 — Advanced analysis, market profiles and research extensions

**Feature tasks: 4.** Market-profile indicators + alternative Strategy architectures + stock-picker simulation → advanced-analysis UI and existing gateways. Validate advanced operators/weights/actions already owned by earlier feature tasks; these are release checks, not second implementation tasks.

**Visible completion:** Inspect Volume Profile/TPO and stock-picker results, open advanced statistical/3D analysis, disable GPU or the extension, and confirm that core 2D results remain intact.

**Phase evidence:** `tests/ui/e2e/research/phase_13.spec.ts` and `docs/dev/evidence/phases/phase-13.json`, owned by Task 13.04. All prior affected UI/data/recovery regressions remain required.

<a id="task-13-01"></a>

### - [ ] Task 13.01 — FEAT-IND-CALCULATE_MARKET_PROFILES — Calculate Volume Profile and TPO

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Indicators · **Owner specification:** `app/services/indicators/README.md` · **Register first slice:** U10.

**Order prerequisites:** 2.25.

#### i. Feature and remaining work

A Strategy, Research or Analytics client obtains one versioned deterministic numerical result with causal availability and explicit invalid states.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IND-CALCULATE_MARKET_PROFILES-001 | Compute profiles from eligible Data-prepared source slices with pinned volume meaning, bin size, session and tie/expansion policies. |
| FR-TRC-IND-CALCULATE_MARKET_PROFILES-002 | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. |
| FR-TRC-IND-CALCULATE_MARKET_PROFILES-003 | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IND-CALCULATE_MARKET_PROFILES-001 | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. |
| NFR-TRC-IND-CALCULATE_MARKET_PROFILES-002 | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IND-CALCULATE_MARKET_PROFILES-001 | Empty sessions, equal-volume POC ties, gaps and exact bin boundaries match goldens; bin totals conserve the eligible input volume/TPO counts. |
| AT-IND-CALCULATE_MARKET_PROFILES-002 | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| AT-IND-CALCULATE_MARKET_PROFILES-003 | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |
| ATN-IND-CALCULATE_MARKET_PROFILES-001 | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| ATN-IND-CALCULATE_MARKET_PROFILES-002 | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |


**Acceptance test targets:** `tests/services/indicators/calculate_market_profiles/test_traceability.py`; `tests/services/indicators/calculate_market_profiles/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Compute profiles from eligible Data-prepared source slices with pinned volume meaning, bin size, session and tie/expansion policies. Expected: Empty sessions, equal-volume POC ties, gaps and exact bin boundaries match goldens; bin totals conserve the eligible input volume/TPO counts. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IND-CALCULATE_MARKET_PROFILES/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 4.09 (FEAT-SIM-EXECUTE_TICKS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(indicators): complete FEAT-IND-CALCULATE_MARKET_PROFILES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-13-02"></a>

### - [ ] Task 13.02 — FEAT-STRAT-DEFINE_ARCHITECTURES — Validate alternative strategy architectures

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U10.

**Order prerequisites:** 3.07, 3.08.

#### i. Feature and remaining work

Rule, fuzzy-score and pattern-template strategies have explicit registered evaluation meaning rather than ad hoc model code.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-DEFINE_ARCHITECTURES-001 | Register deterministic rule/signal architecture as the core baseline and separately version fuzzy membership/aggregation/threshold and pattern-template extensions. |
| FR-TRC-STRAT-DEFINE_ARCHITECTURES-002 | Validate architecture-specific node, parameter, clock and resource constraints through the common HSL pipeline. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-DEFINE_ARCHITECTURES-001 | Removing FEAT-STRAT-DEFINE_ARCHITECTURES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-DEFINE_ARCHITECTURES-001 | An unknown architecture is inspectable but cannot execute; fuzzy score units and threshold ties are defined before activation. |
| AT-STRAT-DEFINE_ARCHITECTURES-002 | The same unsupported node fails in both manual and AI authoring; removing the extension leaves core rule strategies valid. |
| ATN-STRAT-DEFINE_ARCHITECTURES-001 | Disable and physically remove define_architectures; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/define_architectures/test_traceability.py`; `tests/services/strategy/define_architectures/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register deterministic rule/signal architecture as the core baseline and separately version fuzzy membership/aggregation/threshold and pattern-template extensions. Expected: An unknown architecture is inspectable but cannot execute; fuzzy score units and threshold ties are defined before activation. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-DEFINE_ARCHITECTURES/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-DEFINE_ARCHITECTURES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-13-03"></a>

### - [ ] Task 13.03 — FEAT-SIM-SIMULATE_STOCKPICKERS — Evaluate universe-based stock-selection strategies

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Simulator · **Owner specification:** `app/services/simulator/README.md` · **Register first slice:** U10.

**Order prerequisites:** 2.22, 4.09, 4.10.

#### i. Feature and remaining work

A strategy selecting among instruments is evaluated against an as-of universe and shared capital, not a survivorship-biased independent-symbol shortcut.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-SIM-SIMULATE_STOCKPICKERS-001 | Bind the observable universe, corporate/adjustment policy, rebalance clock, selection/ranking rules and capital constraints. |
| FR-TRC-SIM-SIMULATE_STOCKPICKERS-002 | Execute interacting capital, cross-symbol signals and order state in one chronological tick run. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-SIM-SIMULATE_STOCKPICKERS-001 | Removing FEAT-SIM-SIMULATE_STOCKPICKERS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-SIM-SIMULATE_STOCKPICKERS-001 | A future-added or unavailable instrument cannot enter a historical selection silently; coverage exclusions are explicit. |
| AT-SIM-SIMULATE_STOCKPICKERS-002 | Independent-symbol summation is rejected when shared cash/risk/positions alter execution; constituent and combined lineage is retained. |
| ATN-SIM-SIMULATE_STOCKPICKERS-001 | Disable and physically remove simulate_stockpickers; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/simulator/simulate_stockpickers/test_traceability.py`; `tests/services/simulator/simulate_stockpickers/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Bind the observable universe, corporate/adjustment policy, rebalance clock, selection/ranking rules and capital constraints. Expected: A future-added or unavailable instrument cannot enter a historical selection silently; coverage exclusions are explicit. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-SIM-SIMULATE_STOCKPICKERS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(simulator): complete FEAT-SIM-SIMULATE_STOCKPICKERS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-13-04"></a>

### - [ ] Task 13.04 — FEAT-UI-ADVANCED_ANALYSIS — Explore advanced statistical and profile visualizations

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U10.

**Order prerequisites:** 1.01, 1.02, 4.19, 13.01, 13.02, 13.03.

#### i. Feature and remaining work

Inspect higher-dimensional evidence without losing source semantics or accessible alternatives.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-ADVANCED_ANALYSIS-001 | Render only owner-projected statistical/3D/profile data with exact/aggregated/sampled/partial labels and units. |
| FR-TRC-UI-ADVANCED_ANALYSIS-002 | Bound GPU buffers, decoding and panel memory and release all resources when closed. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-ADVANCED_ANALYSIS-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-ADVANCED_ANALYSIS-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-ADVANCED_ANALYSIS-001 | GPU-off and unsupported WebGL paths expose complete 2D/table values; the visual engine computes no trading metric. |
| AT-UI-ADVANCED_ANALYSIS-002 | Large surfaces use admitted/tiled/LOD data; repeated mount/unmount returns buffers/listeners/workers to baseline. |
| ATN-UI-ADVANCED_ANALYSIS-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-ADVANCED_ANALYSIS-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/advanced-analysis/__tests__/traceability.test.tsx`; `app/ui/src/widgets/advanced-analysis/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Explore advanced statistical and profile visualizations). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: GPU-off and unsupported WebGL paths expose complete 2D/table values; the visual engine computes no trading metric. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-ADVANCED_ANALYSIS/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P13 — Inspect Volume Profile/TPO and stock-picker results, open advanced statistical/3D analysis, disable GPU or the extension, and confirm that core 2D results remain intact. Publish `docs/dev/evidence/phases/phase-13.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-ADVANCED_ANALYSIS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-14"></a>

## Phase 14 — Neural research from dataset to qualified inference

**Feature tasks: 7.** Neural preparation/labels/training/validation/explanation/inference → existing Research and result/generation boundaries → Neural Research widget. No performance, predictive usefulness or model qualification is assumed.

**Visible completion:** Define causal features and labels, train a bounded model, inspect leakage checks and baseline comparison, publish a model card, run qualified inference and view its evidence in Neural Research.

**Phase evidence:** `tests/ui/e2e/research/phase_14.spec.ts` and `docs/dev/evidence/phases/phase-14.json`, owned by Task 14.07. All prior affected UI/data/recovery regressions remain required.

<a id="task-14-01"></a>

### - [ ] Task 14.01 — FEAT-RES-PREPARE_NEURAL_DATASETS — Fit causal neural feature pipelines

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U11.

**Order prerequisites:** 2.20, 2.23, 3.02, 3.03, 3.06, 13.01.

#### i. Feature and remaining work

A model receives reproducible ordered inputs fitted only on its training history.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-PREPARE_NEURAL_DATASETS-001 | Version ordered features, units, input shapes, missing/zero-variance policy, categorical mappings and exact fit window. |
| FR-TRC-RES-PREPARE_NEURAL_DATASETS-002 | Deliver price/stationarity, oscillator, trend, volatility, volume/profile and observable context feature families. |
| FR-TRC-RES-PREPARE_NEURAL_DATASETS-003 | Provide finite fractional-differencing truncation/weight tolerance with d=0.4 template and bounded 0.35–0.65 search interval. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-PREPARE_NEURAL_DATASETS-001 | Removing FEAT-RES-PREPARE_NEURAL_DATASETS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-PREPARE_NEURAL_DATASETS-001 | A validation/test timestamp in a fit request is rejected; validation reuses the original fitted scaler/imputer/encoder/selector. |
| AT-RES-PREPARE_NEURAL_DATASETS-002 | Each feature exposes provider/version/availability; absent feed volume or profile support is unavailable rather than imputed by a model. |
| AT-RES-PREPARE_NEURAL_DATASETS-003 | The transform excludes future observations; stationarity diagnostics do not claim predictive usefulness. |
| ATN-RES-PREPARE_NEURAL_DATASETS-001 | Disable and physically remove prepare_neural_datasets; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/prepare_neural_datasets/test_traceability.py`; `tests/services/research/prepare_neural_datasets/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version ordered features, units, input shapes, missing/zero-variance policy, categorical mappings and exact fit window. Expected: A validation/test timestamp in a fit request is rejected; validation reuses the original fitted scaler/imputer/encoder/selector. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-PREPARE_NEURAL_DATASETS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-PREPARE_NEURAL_DATASETS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-14-02"></a>

### - [ ] Task 14.02 — FEAT-RES-LABEL_NEURAL_DATA — Construct directional and forward-return labels

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U11.

**Order prerequisites:** 2.20, 3.03.

#### i. Feature and remaining work

Training examples have explicit future target definitions and cannot confuse absent or ambiguous outcomes with neutral labels.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-LABEL_NEURAL_DATA-001 | Implement ATR-at-t0 additive triple barriers, forward-return regression and a separately named return-volatility multiplicative barrier variant. |
| FR-TRC-RES-LABEL_NEURAL_DATA-002 | Pin price side, horizon clock/inclusivity, session/gaps/costs/missing policy and class order; require positive explicit multipliers and record H=24 template. |
| FR-TRC-RES-LABEL_NEURAL_DATA-003 | Use tick ordering only when a registered tick-resolved labeler can prove first touch and preserve target-only future access. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-LABEL_NEURAL_DATA-001 | Removing FEAT-RES-LABEL_NEURAL_DATA withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-LABEL_NEURAL_DATA-001 | The variants retain different method IDs/units; p0±k×ATR is never silently substituted for p0×(1±k×sigma). |
| AT-RES-LABEL_NEURAL_DATA-002 | Both barriers inside an unresolved OHLC bar yields ambiguous exclusion; missing horizon coverage yields unavailable, not neutral. |
| AT-RES-LABEL_NEURAL_DATA-003 | Future input perturbations may change labels but cannot change the feature vector at t0. |
| ATN-RES-LABEL_NEURAL_DATA-001 | Disable and physically remove label_neural_data; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/label_neural_data/test_traceability.py`; `tests/services/research/label_neural_data/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Implement ATR-at-t0 additive triple barriers, forward-return regression and a separately named return-volatility multiplicative barrier variant. Expected: The variants retain different method IDs/units; p0±k×ATR is never silently substituted for p0×(1±k×sigma). Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-LABEL_NEURAL_DATA/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-LABEL_NEURAL_DATA`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-14-03"></a>

### - [ ] Task 14.03 — FEAT-RES-INFER_MODELS — Execute qualified lightweight model inference

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U11.

**Order prerequisites:** 1.17.

#### i. Feature and remaining work

A strategy evaluates a pinned model without loading a heavyweight training framework in each tick loop.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-INFER_MODELS-001 | Load only safe declared graph/tensor formats with immutable model/preprocessing hashes, ordered inputs and supported operators. |
| FR-TRC-RES-INFER_MODELS-002 | Implement qualified feedforward NumPy/native inference and compatible causal sequence kernels with explicit reset, normalization, activation and output semantics. |
| FR-TRC-RES-INFER_MODELS-003 | Apply the versioned classification decision policy: initial directional max probability must exceed 0.55, otherwise neutral; ties are neutral. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-INFER_MODELS-001 | Removing FEAT-RES-INFER_MODELS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-INFER_MODELS-001 | Unknown operator/dtype or malformed weights fail preflight; arbitrary Python/Java object deserialization is impossible. |
| AT-RES-INFER_MODELS-002 | Golden predictions on normal/boundary/missing/sequence-reset vectors match authoritative inference within recorded tolerances; no unconditional ReLU/class-order substitution occurs. |
| AT-RES-INFER_MODELS-003 | A tied maximum or probability exactly 0.55 yields neutral; changing threshold/class order creates a new policy/package revision. |
| ATN-RES-INFER_MODELS-001 | Disable and physically remove infer_models; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/infer_models/test_traceability.py`; `tests/services/research/infer_models/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Load only safe declared graph/tensor formats with immutable model/preprocessing hashes, ordered inputs and supported operators. Expected: Unknown operator/dtype or malformed weights fail preflight; arbitrary Python/Java object deserialization is impossible. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-INFER_MODELS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 4.09 (FEAT-SIM-EXECUTE_TICKS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-INFER_MODELS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-14-04"></a>

### - [ ] Task 14.04 — FEAT-RES-TRAIN_MODELS — Train bounded causal model providers

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U11.

**Order prerequisites:** 1.22, 12.03, 14.01, 14.02.

#### i. Feature and remaining work

A user can train, compare and resume a model under explicit numerical and resource limits instead of opaque uncontrolled training.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-TRAIN_MODELS-001 | Deliver MLP first, causal TCN second, then LSTM/GRU under declared task, shape/dtype, sequence length, receptive field, device and resource contracts. |
| FR-TRC-RES-TRAIN_MODELS-002 | Provide reproducible CPU MLP template: Leaky-ReLU 0.01, dropout 0.2, AdamW learning rate 1e-3, weight decay 1e-4, max 100 epochs, patience 15; optional focal gamma 2. |
| FR-TRC-RES-TRAIN_MODELS-003 | Checkpoint optimizer/schedule/weights/preprocessing/runtime identity and terminate/resume within the declared compatibility policy. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-TRAIN_MODELS-001 | Removing FEAT-RES-TRAIN_MODELS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-TRAIN_MODELS-001 | Future padding is rejected; actual TCN graph/repeats determine receptive field; sequence reset/truncation/state persistence are explicit. |
| AT-RES-TRAIN_MODELS-002 | Architecture widths, sequence/batch size, seed and finite budget must be supplied; the template makes no expected-performance claim. |
| AT-RES-TRAIN_MODELS-003 | Interrupted training resumes only compatible state; cancellation releases CPU/GPU/memory reservations and no arbitrary pickle loader executes. |
| ATN-RES-TRAIN_MODELS-001 | Disable and physically remove train_models; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/train_models/test_traceability.py`; `tests/services/research/train_models/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Deliver MLP first, causal TCN second, then LSTM/GRU under declared task, shape/dtype, sequence length, receptive field, device and resource contracts. Expected: Future padding is rejected; actual TCN graph/repeats determine receptive field; sequence reset/truncation/state persistence are explicit. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-TRAIN_MODELS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-TRAIN_MODELS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-14-05"></a>

### - [ ] Task 14.05 — FEAT-RES-VALIDATE_MODELS — Qualify models and publish model cards

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U11.

**Order prerequisites:** 4.07, 4.09, 6.03, 6.05, 14.04.

#### i. Feature and remaining work

A model’s statistical evidence, strategy behavior, limitations and repeatability can be inspected before it becomes an eligible strategy node.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-VALIDATE_MODELS-001 | Use time-ordered folds, overlap purging and embargo derived from actual information horizons, with final OOS sealed. |
| FR-TRC-RES-VALIDATE_MODELS-002 | Compare against class-frequency/neutral, prior/zero-return and deterministic Strategy baselines; report predictive and net simulated performance separately. |
| FR-TRC-RES-VALIDATE_MODELS-003 | Publish a safe immutable graph/operator/weights/preprocessing/class-order/threshold/runtime bundle and model card with coverage, exposures, limitations and golden vectors. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-VALIDATE_MODELS-001 | Removing FEAT-RES-VALIDATE_MODELS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-VALIDATE_MODELS-001 | Any training feature/label interval overlapping evaluation is excluded under the recorded rule; tuning never sees the final test interval. |
| AT-RES-VALIDATE_MODELS-002 | Unsupported class metrics or small samples are unavailable; a good training score alone cannot qualify a strategy. |
| AT-RES-VALIDATE_MODELS-003 | Arbitrary object deserialization is refused; nondeterministic devices are labelled under a repeatability protocol, not advertised as exact replay. |
| ATN-RES-VALIDATE_MODELS-001 | Disable and physically remove validate_models; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/validate_models/test_traceability.py`; `tests/services/research/validate_models/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Use time-ordered folds, overlap purging and embargo derived from actual information horizons, with final OOS sealed. Expected: Any training feature/label interval overlapping evaluation is excluded under the recorded rule; tuning never sees the final test interval. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-VALIDATE_MODELS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.16 (FEAT-STRAT-EXCHANGE_STRATEGIES), Task 12.05 (FEAT-STRAT-GENERATE_MQL5), Task 12.06 (FEAT-STRAT-GENERATE_PYTHON), Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-VALIDATE_MODELS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-14-06"></a>

### - [ ] Task 14.06 — FEAT-RES-EXPLAIN_MODELS — Explain bounded model behavior without causal overclaims

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Research · **Owner specification:** `app/services/research/README.md` · **Register first slice:** U11.

**Order prerequisites:** 1.18, 14.05.

#### i. Feature and remaining work

A user can inspect why a model changes predictions while seeing the explanation’s assumptions and sample limits.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-RES-EXPLAIN_MODELS-001 | Run permutation importance and separately registered SHAP providers with bounded samples/background chosen from training-only reference data. |
| FR-TRC-RES-EXPLAIN_MODELS-002 | Report applicable ROC/PR/AUC, confusion, calibration, sensitivity and sample support alongside explanation metadata. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-RES-EXPLAIN_MODELS-001 | Removing FEAT-RES-EXPLAIN_MODELS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-RES-EXPLAIN_MODELS-001 | A validation/test-selected background is rejected; unsupported model/provider combinations return unavailable. |
| AT-RES-EXPLAIN_MODELS-002 | Missing classes or inadequate support never produce a fabricated AUC; model importance is not labelled a causal effect. |
| ATN-RES-EXPLAIN_MODELS-001 | Disable and physically remove explain_models; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/research/explain_models/test_traceability.py`; `tests/services/research/explain_models/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Run permutation importance and separately registered SHAP providers with bounded samples/background chosen from training-only reference data. Expected: A validation/test-selected background is rejected; unsupported model/provider combinations return unavailable. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-RES-EXPLAIN_MODELS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 6.07 (FEAT-IFACE-OPERATE_RESEARCH). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(research): complete FEAT-RES-EXPLAIN_MODELS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-14-07"></a>

### - [ ] Task 14.07 — FEAT-UI-NEURAL_RESEARCH — Design, train and validate neural research

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U11.

**Order prerequisites:** 1.01, 1.02, 6.07, 14.03, 14.05, 14.06.

#### i. Feature and remaining work

Define causal features/labels and inspect training/validation/inference support before integrating a model.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-NEURAL_RESEARCH-001 | Render explicit fit windows, label ambiguity/missing counts, model shapes/causality, budgets and provider support. |
| FR-TRC-UI-NEURAL_RESEARCH-002 | Display prediction metrics separately from net strategy performance and show repeatability/limitations/model-card provenance. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-NEURAL_RESEARCH-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-NEURAL_RESEARCH-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-NEURAL_RESEARCH-001 | A preprocessing fit cannot use final OOS; unsupported class/metric/model/target states remain unavailable. |
| AT-UI-NEURAL_RESEARCH-002 | Training success cannot become strategy qualification; browser graphics do not run authoritative training or inference. |
| ATN-UI-NEURAL_RESEARCH-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-NEURAL_RESEARCH-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/neural-research/__tests__/traceability.test.tsx`; `app/ui/src/widgets/neural-research/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Design, train and validate neural research). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: A preprocessing fit cannot use final OOS; unsupported class/metric/model/target states remain unavailable. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-NEURAL_RESEARCH/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P14 — Define causal features and labels, train a bounded model, inspect leakage checks and baseline comparison, publish a model card, run qualified inference and view its evidence in Neural Research. Publish `docs/dev/evidence/phases/phase-14.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-NEURAL_RESEARCH`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-15"></a>

## Phase 15 — Remote workers with the existing operational UI

**Feature tasks: 1.** Remote worker provider extends the same work-unit protocol. Its one feature task includes the existing jobs gateway and Jobs/Performance Lab browser regression tests; it does not create replacement UIs or another scheduler.

**Visible completion:** Register an authenticated worker, submit bounded work, lose its lease, suppress stale/duplicate completion, drain or quarantine it, and inspect all transitions in the existing Jobs widget.

**Phase evidence:** `tests/ui/e2e/research/phase_15.spec.ts` and `docs/dev/evidence/phases/phase-15.json`, owned by Task 15.01. All prior affected UI/data/recovery regressions remain required.

<a id="task-15-01"></a>

### - [ ] Task 15.01 — FEAT-ORCH-MANAGE_REMOTE_WORKERS — Lease and reconcile authenticated remote work

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Orchestration · **Owner specification:** `app/services/orchestration/README.md` · **Register first slice:** U12.

**Order prerequisites:** 1.04, 1.17, 1.18.

#### i. Feature and remaining work

A distributed pool can retry computation after partitions without accepting duplicate results or changing deterministic reduction order.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ORCH-MANAGE_REMOTE_WORKERS-001 | Register authenticated workers with capacity, operations and runtime/numerical compatibility; admit only healthy compatible providers. |
| FR-TRC-ORCH-MANAGE_REMOTE_WORKERS-002 | Issue monotonically fenced leases with initial heartbeat 5 s, lease 30 s and at most two retries after the initial attempt. |
| FR-TRC-ORCH-MANAGE_REMOTE_WORKERS-003 | Verify transferred input/output hashes, publish artifacts before domain acceptance, and reduce accepted results in logical order. |
| FR-TRC-ORCH-MANAGE_REMOTE_WORKERS-004 | Expose typed registration/acquire/heartbeat/complete/status and three-grid task telemetry through Interfaces; keep health and lease clocks distinct. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ORCH-MANAGE_REMOTE_WORKERS-001 | Removing FEAT-ORCH-MANAGE_REMOTE_WORKERS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ORCH-MANAGE_REMOTE_WORKERS-001 | Unknown/revoked identities or incompatible numerical fingerprints receive no lease; draining/offline/quarantined nodes get no new work. |
| AT-ORCH-MANAGE_REMOTE_WORKERS-002 | A partition can duplicate computation but only one current logical completion is accepted; stale tokens cannot replace it. |
| AT-ORCH-MANAGE_REMOTE_WORKERS-003 | Reordered arrivals, cache hits and retries produce the same qualified output identity; corrupt payloads never become committed results. |
| AT-ORCH-MANAGE_REMOTE_WORKERS-004 | Three missed heartbeats may quarantine admission under a versioned policy but cannot independently rewrite accepted results or bypass fencing. |
| ATN-ORCH-MANAGE_REMOTE_WORKERS-001 | Disable and physically remove manage_remote_workers; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/orchestration/manage_remote_workers/test_traceability.py`; `tests/services/orchestration/manage_remote_workers/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Register authenticated workers with capacity, operations and runtime/numerical compatibility; admit only healthy compatible providers. Expected: Unknown/revoked identities or incompatible numerical fingerprints receive no lease; draining/offline/quarantined nodes get no new work. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ORCH-MANAGE_REMOTE_WORKERS/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 1.26 (FEAT-IFACE-OPERATE_JOBS). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

**Phase checkpoint owner:** Run E2E-P15 — Register an authenticated worker, submit bounded work, lose its lease, suppress stale/duplicate completion, drain or quarantine it, and inspect all transitions in the existing Jobs widget. Publish `docs/dev/evidence/phases/phase-15.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(orchestration): complete FEAT-ORCH-MANAGE_REMOTE_WORKERS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="phase-16"></a>

## Phase 16 — Qualified external exchange, packaging and distribution

**Feature tasks: 12.** Additional connector and external-ledger/strategy adapters + target generation/package + automation + application distribution → existing Data/Strategy/Jobs UIs and Strategy Packager. Advertising support requires rights, format, compiler and install evidence.

**Visible completion:** Use a verified external data/strategy format, inspect conversion losses, produce a target-verified strategy package, exercise scoped CLI/MCP commands, and verify desktop/headless installation and cleanup.

**Phase evidence:** `tests/ui/e2e/research/phase_16.spec.ts` and `docs/dev/evidence/phases/phase-16.json`, owned by Task 16.12. All prior affected UI/data/recovery regressions remain required.

<a id="task-16-01"></a>

### - [ ] Task 16.01 — FEAT-IFACE-AUTOMATE_COMMANDS — Expose permission-scoped CLI and MCP automation

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Interfaces · **Owner specification:** `app/services/interfaces/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.08, 3.14, 6.06, 11.06.

#### i. Feature and remaining work

External clients invoke the same governed owner capabilities and receive truthful typed outcomes without recreating business logic.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-IFACE-AUTOMATE_COMMANDS-001 | Register only explicitly scoped public owner commands with the same identity/schema/budget/idempotency/approval requirements as HTTP. |
| FR-TRC-IFACE-AUTOMATE_COMMANDS-002 | Expose disabled/unavailable status until a compatible authenticated client/provider is configured. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-IFACE-AUTOMATE_COMMANDS-001 | Heavy CPU/serialization/export work is delegated as admitted jobs; transport keeps bounded pages/events and remains responsive. |
| NFR-TRC-IFACE-AUTOMATE_COMMANDS-002 | Provider loss or scope revocation returns CAPABILITY_UNAVAILABLE/typed denial without selecting a substitute. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-IFACE-AUTOMATE_COMMANDS-001 | An automation/MCP client cannot bypass holdout, sandbox, receiver or live authority boundaries. |
| AT-IFACE-AUTOMATE_COMMANDS-002 | An unconfigured MCP endpoint is not advertised as active and never executes arbitrary commands. |
| ATN-IFACE-AUTOMATE_COMMANDS-001 | BM-APP-01 control/metadata p95 ≤250 ms and p99 ≤1 s; long commands return an owner job handle and no event-loop CPU blockage. |
| ATN-IFACE-AUTOMATE_COMMANDS-002 | Remove each operation owner in turn; only its operations degrade and no unauthorized receiver gets invoked. |


**Acceptance test targets:** `tests/services/interfaces/automate_commands/test_traceability.py`; `tests/services/interfaces/automate_commands/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Through the real mounted gateway, authenticate the scoped fixture user and submit the smallest request for: Register only explicitly scoped public owner commands with the same identity/schema/budget/idempotency/approval requirements as HTTP. Repeat a safe/idempotent request and then repeat without its provider or authority. Expected: An automation/MCP client cannot bypass holdout, sandbox, receiver or live authority boundaries. The owning README supplies the exact request JSON, route and expected envelope.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-IFACE-AUTOMATE_COMMANDS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(interfaces): complete FEAT-IFACE-AUTOMATE_COMMANDS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-02"></a>

### - [ ] Task 16.02 — FEAT-WS-DISTRIBUTE_APPLICATION — Build installable desktop and headless application distributions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Workspace · **Owner specification:** `app/services/workspace/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.03, 1.22.

#### i. Feature and remaining work

The same qualified application can be installed as a desktop wrapper or a headless server without a second business implementation.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-WS-DISTRIBUTE_APPLICATION-001 | Produce a thin desktop wrapper around the existing application and a headless Docker image from pinned source and lockfiles. |
| FR-TRC-WS-DISTRIBUTE_APPLICATION-002 | Verify installation, first launch, native runtime support, shutdown, upgrade and rollback on the supported Windows/server profiles. |
| FR-TRC-WS-DISTRIBUTE_APPLICATION-003 | Record target, toolchain, dependency/integrity metadata and exactly which release gates passed; never infer trading approval from installation. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-WS-DISTRIBUTE_APPLICATION-001 | Removing FEAT-WS-DISTRIBUTE_APPLICATION withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-WS-DISTRIBUTE_APPLICATION-001 | Clean CI builds both outputs; their embedded application/contract versions and source commit match the distribution manifest. |
| AT-WS-DISTRIBUTE_APPLICATION-002 | A missing native runtime produces an explicit pre-admission error; uninstall leaves retained user evidence untouched. |
| AT-WS-DISTRIBUTE_APPLICATION-003 | The installer report links test artifacts and hashes; no distribution action activates a live strategy or embeds credentials. |
| ATN-WS-DISTRIBUTE_APPLICATION-001 | Disable and physically remove distribute_application; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/workspace/distribute_application/test_traceability.py`; `tests/services/workspace/distribute_application/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Produce a thin desktop wrapper around the existing application and a headless Docker image from pinned source and lockfiles. Expected: Clean CI builds both outputs; their embedded application/contract versions and source commit match the distribution manifest. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-WS-DISTRIBUTE_APPLICATION/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(workspace): complete FEAT-WS-DISTRIBUTE_APPLICATION`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-03"></a>

### - [ ] Task 16.03 — FEAT-BRK-DARWINEX — Connect the Darwinex data channel

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Darwinex adapter, with explicit availability and failure results.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-DARWINEX-001 | Validate the Darwinex provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-DARWINEX-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-DARWINEX-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-DARWINEX-001 | Removing FEAT-BRK-DARWINEX withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-DARWINEX-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-DARWINEX-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-DARWINEX-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-DARWINEX-001 | Disable and physically remove darwinex; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/darwinex/test_traceability.py`; `tests/services/brokers/darwinex/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Darwinex provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-DARWINEX/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-DARWINEX`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-04"></a>

### - [ ] Task 16.04 — FEAT-BRK-COINBASE — Connect the Coinbase data channel

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Coinbase adapter, with explicit availability and failure results.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-COINBASE-001 | Validate the Coinbase provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-COINBASE-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-COINBASE-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-COINBASE-001 | Removing FEAT-BRK-COINBASE withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-COINBASE-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-COINBASE-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-COINBASE-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-COINBASE-001 | Disable and physically remove coinbase; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/coinbase/test_traceability.py`; `tests/services/brokers/coinbase/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Coinbase provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-COINBASE/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-COINBASE`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-05"></a>

### - [ ] Task 16.05 — FEAT-BRK-BITFINEX — Connect the Bitfinex data channel

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Bitfinex adapter, with explicit availability and failure results.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-BITFINEX-001 | Validate the Bitfinex provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-BITFINEX-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-BITFINEX-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-BITFINEX-001 | Removing FEAT-BRK-BITFINEX withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-BITFINEX-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-BITFINEX-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-BITFINEX-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-BITFINEX-001 | Disable and physically remove bitfinex; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/bitfinex/test_traceability.py`; `tests/services/brokers/bitfinex/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Bitfinex provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-BITFINEX/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-BITFINEX`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-06"></a>

### - [ ] Task 16.06 — FEAT-BRK-POLONIEX — Connect the Poloniex data channel

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.14.

#### i. Feature and remaining work

Authorized clients can obtain the observations actually supported by the selected Poloniex adapter, with explicit availability and failure results.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-POLONIEX-001 | Validate the Poloniex provider/version, credential references, instrument/history support and permitted-use configuration before connection. |
| FR-TRC-BRK-POLONIEX-002 | Return bounded source observations preserving provider symbol, timestamps, sequence, price sides and volume meaning. |
| FR-TRC-BRK-POLONIEX-003 | Enforce source rate/concurrency limits and release requests/sessions on cancellation or provider removal. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-POLONIEX-001 | Removing FEAT-BRK-POLONIEX withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-POLONIEX-001 | Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. |
| AT-BRK-POLONIEX-002 | A source fixture round-trips those fields into the Data intake; unsupported bid/ask or volume remains absent, not fabricated. |
| AT-BRK-POLONIEX-003 | Timeout/rate-limit/removal fixtures leave no active session/task and do not switch to another source silently. |
| ATN-BRK-POLONIEX-001 | Disable and physically remove poloniex; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/poloniex/test_traceability.py`; `tests/services/brokers/poloniex/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate the Poloniex provider/version, credential references, instrument/history support and permitted-use configuration before connection. Expected: Unsupported history/schema/permission returns an explicit refusal; planned support is never displayed as connected. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-POLONIEX/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-POLONIEX`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-07"></a>

### - [ ] Task 16.07 — FEAT-BRK-CONNECT_MARKET_FEEDS — Connect declared equity and futures feed adapters

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Brokers · **Owner specification:** `app/services/brokers/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.12, 2.08.

#### i. Feature and remaining work

An installed feed adapter exposes licensed equity/futures observations through the same bounded provider contract.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-BRK-CONNECT_MARKET_FEEDS-001 | Accept only explicitly installed feed contributions with a finite vendor/version/instrument/schema/rights matrix. |
| FR-TRC-BRK-CONNECT_MARKET_FEEDS-002 | Pin adjusted/unadjusted, contract/roll, timestamp and volume conventions on each output. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-BRK-CONNECT_MARKET_FEEDS-001 | Removing FEAT-BRK-CONNECT_MARKET_FEEDS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-BRK-CONNECT_MARKET_FEEDS-001 | An empty contribution set is unavailable, not a connected equity or futures service. |
| AT-BRK-CONNECT_MARKET_FEEDS-002 | A roll/adjustment change yields a new declared source version; old research references remain unchanged. |
| ATN-BRK-CONNECT_MARKET_FEEDS-001 | Disable and physically remove connect_market_feeds; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/brokers/connect_market_feeds/test_traceability.py`; `tests/services/brokers/connect_market_feeds/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Accept only explicitly installed feed contributions with a finite vendor/version/instrument/schema/rights matrix. Expected: An empty contribution set is unavailable, not a connected equity or futures service. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-BRK-CONNECT_MARKET_FEEDS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(brokers): complete FEAT-BRK-CONNECT_MARKET_FEEDS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-08"></a>

### - [ ] Task 16.08 — FEAT-STRAT-GENERATE_TARGETS — Generate verified additional target languages artifacts

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.17, 3.13, 12.03, 14.05.

#### i. Feature and remaining work

A compatible HSL strategy can be exported as additional target languages without silently changing its trading or numerical behavior.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-GENERATE_TARGETS-001 | Lower the same target-neutral plan to each advertised target using pinned operator, numerical, clock and position-policy mappings. |
| FR-TRC-STRAT-GENERATE_TARGETS-002 | Run target parsing/compilation and golden indicator/signal/inference vectors on normal, boundary, missing and sequence-reset cases. |
| FR-TRC-STRAT-GENERATE_TARGETS-003 | Publish reproducible artifacts with target/version/options, resources, hashes and restriction support matrix. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-GENERATE_TARGETS-001 | Removing FEAT-STRAT-GENERATE_TARGETS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-GENERATE_TARGETS-001 | Unsupported constructs fail before executable-success publication; source snapshots retain source-node diagnostics. |
| AT-STRAT-GENERATE_TARGETS-002 | A target lacking a compatible toolchain remains UNVERIFIED_TARGET; accepted discrete fields match exactly and floats stay within declared tolerances. |
| AT-STRAT-GENERATE_TARGETS-003 | Rebuilds under the same qualified toolchain meet the declared reproducibility policy and never activate trading. |
| ATN-STRAT-GENERATE_TARGETS-001 | Disable and physically remove generate_targets; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/generate_targets/test_traceability.py`; `tests/services/strategy/generate_targets/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Lower the same target-neutral plan to each advertised target using pinned operator, numerical, clock and position-policy mappings. Expected: Unsupported constructs fail before executable-success publication; source snapshots retain source-node diagnostics. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-GENERATE_TARGETS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-GENERATE_TARGETS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-09"></a>

### - [ ] Task 16.09 — FEAT-ANA-IMPORT_EXTERNAL_LEDGERS — Validate external binary trades and equity evidence

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Analytics · **Owner specification:** `app/services/analytics/README.md` · **Register first slice:** U13.

**Order prerequisites:** 4.18.

#### i. Feature and remaining work

A supported external ledger is converted with verified framing and clearly attributed execution/metric semantics.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-ANA-IMPORT_EXTERNAL_LEDGERS-001 | Validate declared orders.bin/dailyEquity.bin framing, record count, field layout, string encoding, units and epoch before conversion. |
| FR-TRC-ANA-IMPORT_EXTERNAL_LEDGERS-002 | Stream verified records into bounded Arrow/Parquet batches and preserve the immutable original and conversion report. |
| FR-TRC-ANA-IMPORT_EXTERNAL_LEDGERS-003 | Treat SQStats/Base64 as a restricted typed format only after version-specific verification; otherwise retain permitted opaque bytes and report unavailable metrics. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-ANA-IMPORT_EXTERNAL_LEDGERS-001 | Removing FEAT-ANA-IMPORT_EXTERNAL_LEDGERS withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-ANA-IMPORT_EXTERNAL_LEDGERS-001 | A mismatched format tag, truncated record/comment, impossible count or nonfinite/overflow value rejects the affected import, never silently truncates it. |
| AT-ANA-IMPORT_EXTERNAL_LEDGERS-002 | Output count equals verified accepted records; memory remains within admission for large ledgers. |
| AT-ANA-IMPORT_EXTERNAL_LEDGERS-003 | No general Java object loader runs and no imported value is presented as verified native computation. |
| ATN-ANA-IMPORT_EXTERNAL_LEDGERS-001 | Disable and physically remove import_external_ledgers; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/analytics/import_external_ledgers/test_traceability.py`; `tests/services/analytics/import_external_ledgers/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Validate declared orders.bin/dailyEquity.bin framing, record count, field layout, string encoding, units and epoch before conversion. Expected: A mismatched format tag, truncated record/comment, impossible count or nonfinite/overflow value rejects the affected import, never silently truncates it. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-ANA-IMPORT_EXTERNAL_LEDGERS/acceptance.json`. Record results; no pass is prefilled.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(analytics): complete FEAT-ANA-IMPORT_EXTERNAL_LEDGERS`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-10"></a>

### - [ ] Task 16.10 — FEAT-STRAT-IMPORT_SQX — Convert verified SQX strategy/archive variants

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U13.

**Order prerequisites:** 3.16, 16.09.

#### i. Feature and remaining work

Supported SQX strategies and source settings can be imported with a precise statement of preserved, unsupported and unverified semantics.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-IMPORT_SQX-001 | Dispatch only on a verified format/version descriptor; inspect strategy.xml, orders.bin, dailyEquity.bin and settings.xml with bounded framing. |
| FR-TRC-STRAT-IMPORT_SQX-002 | Map every listed XML field through typed conversion to canonical HSL 2.0.0, preserving order, variables, sizing, exits, chart macros and data bindings. |
| FR-TRC-STRAT-IMPORT_SQX-003 | Require independently verified binary grammar/goldens before enabling binary import/export and report source-metric attribution separately from native metrics. |
| FR-TRC-STRAT-IMPORT_SQX-004 | Qualify compatibility per format/version/entity/target cell and require a new native simulation before native research qualification. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-IMPORT_SQX-001 | Removing FEAT-STRAT-IMPORT_SQX withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-IMPORT_SQX-001 | An unknown variant remains opaque/unavailable and cannot be labelled full fidelity; missing/truncated members are explicit. |
| AT-STRAT-IMPORT_SQX-002 | All sixteen source mapping rows in CAT-SQX-MAPPING have native fixtures; the flat example is not registered as a second production HSL schema. |
| AT-STRAT-IMPORT_SQX-003 | The supplied 116-byte claim/117-byte table/105-byte code discrepancy is detected; no parser uses guessed offsets or silently stops at a truncated record. |
| AT-STRAT-IMPORT_SQX-004 | A supported definition import is not advertised as verified imported execution or as a live-approved strategy. |
| ATN-STRAT-IMPORT_SQX-001 | Disable and physically remove import_sqx; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/import_sqx/test_traceability.py`; `tests/services/strategy/import_sqx/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Dispatch only on a verified format/version descriptor; inspect strategy.xml, orders.bin, dailyEquity.bin and settings.xml with bounded framing. Expected: An unknown variant remains opaque/unavailable and cannot be labelled full fidelity; missing/truncated members are explicit. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-IMPORT_SQX/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.17 (FEAT-IFACE-OPERATE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-IMPORT_SQX`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-11"></a>

### - [ ] Task 16.11 — FEAT-STRAT-PACKAGE_STRATEGIES — Build distributable strategy packages with proven restrictions

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** Strategy · **Owner specification:** `app/services/strategy/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.10, 1.17, 3.15, 12.03, 12.05, 16.08.

#### i. Feature and remaining work

A user can deliver a versioned strategy package with resources and only the restrictions the selected target actually enforces.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-STRAT-PACKAGE_STRATEGIES-001 | Version general metadata, parameters/categories/defaults/ranges, trading options and authorized resources against a strategy revision. |
| FR-TRC-STRAT-PACKAGE_STRATEGIES-002 | Build unrestricted/demo/fixed-size/expiry/account-restricted outputs only for target-supported enforcement combinations. |
| FR-TRC-STRAT-PACKAGE_STRATEGIES-003 | Record bounded build progress, output integrity/signature and toolchain/resource manifests through shared jobs. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-STRAT-PACKAGE_STRATEGIES-001 | Removing FEAT-STRAT-PACKAGE_STRATEGIES withdraws only its declared contribution; no dependent operation may silently select a substitute provider. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-STRAT-PACKAGE_STRATEGIES-001 | Hidden parameters are not represented as a security guarantee; incompatible target/resource mappings fail preflight. |
| AT-STRAT-PACKAGE_STRATEGIES-002 | Each advertised restriction has a negative execution fixture; unsupported combinations cannot produce a restricted-success package. |
| AT-STRAT-PACKAGE_STRATEGIES-003 | Cancellation preserves committed evidence and cleans staging; no signing secret or deployment authority enters the package. |
| ATN-STRAT-PACKAGE_STRATEGIES-001 | Disable and physically remove package_strategies; its operation is unavailable, unrelated capabilities remain usable, and retained source objects are unchanged. |


**Acceptance test targets:** `tests/services/strategy/package_strategies/test_traceability.py`; `tests/services/strategy/package_strategies/test_lifecycle.py`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** Run the feature's bounded, offline primary-module demonstration using a temporary workspace and the pinned fixture for: Version general metadata, parameters/categories/defaults/ranges, trading options and authorized resources against a strategy revision. Expected: Hidden parameters are not represented as a security guarantee; incompatible target/resource mappings fail preflight. Repeat its declared invalid/unavailable case, close the feature scope and show retained-state/cleanup results. No credentials, network or live orders are implicit.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-STRAT-PACKAGE_STRATEGIES/acceptance.json`. Record results; no pass is prefilled.

**This provider also qualifies earlier consumers:** Task 3.17 (FEAT-IFACE-OPERATE_STRATEGIES). Run those owner-bound integration checks through unchanged public contracts and update their operation evidence; these are not new feature tasks.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(strategy): complete FEAT-STRAT-PACKAGE_STRATEGIES`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

<a id="task-16-12"></a>

### - [ ] Task 16.12 — FEAT-UI-STRATEGY_PACKAGER — Review and build strategy distribution packages

**Status:** `NOT_STARTED_IN_TARGET` · **Domain:** UI · **Owner specification:** `app/ui/README.md` · **Register first slice:** U13.

**Order prerequisites:** 1.01, 1.02, 3.17, 16.01, 16.02, 16.08, 16.10, 16.11.

#### i. Feature and remaining work

Configure a package and see exactly which target restrictions and resources are verified.

Implement the full listed FR/local-NFR scope in its ratified owner, with all applicable shared constraints, catalogue obligations, tests and usage. Reuse matching contract/support code only after the Phase 0 audit; do not resurrect an old whole domain.

#### ii. Functional and non-functional requirements

| FR ID | Required behaviour |
| --- | --- |
| FR-TRC-UI-STRATEGY_PACKAGER-001 | Render target-supported package/restriction schemas and compatibility diagnostics before build. |
| FR-TRC-UI-STRATEGY_PACKAGER-002 | Observe bounded isolated build and receipt-backed output/signature verification. |


| Local NFR ID | Required quality or boundary |
| --- | --- |
| NFR-TRC-UI-STRATEGY_PACKAGER-001 | Support keyboard/focus/labelled error/empty/partial/stale/unavailable/denied states and scoped removal without cancelling unrelated accepted work. |
| NFR-TRC-UI-STRATEGY_PACKAGER-002 | Keep view state, event queues and render buffers bounded and label exact versus sampled/derived content. |


Applicable shared NFRs, original source refinements and catalogue obligations are mandatory through the owning README; they are not new tasks.

#### iii. Acceptance tests, evidence and usage

| Acceptance ID | Expected result / oracle |
| --- | --- |
| AT-UI-STRATEGY_PACKAGER-001 | Hidden parameters are not described as secrecy; unsupported restriction combinations remain unavailable. |
| AT-UI-STRATEGY_PACKAGER-002 | No secret enters UI/logs and no package action installs or activates a live strategy. |
| ATN-UI-STRATEGY_PACKAGER-001 | Component/Playwright accessibility and lifecycle fixtures exercise provider absence, reconnect, cancellation, navigation and physical widget deletion. |
| ATN-UI-STRATEGY_PACKAGER-002 | Large-data/mixed-load fixtures use only viewport/projection windows, preserve §18.3 targets and release observers/workers/buffers on unmount. |


**Acceptance test targets:** `app/ui/src/widgets/strategy-packager/__tests__/traceability.test.tsx`; `app/ui/src/widgets/strategy-packager/__tests__/lifecycle.test.tsx`. Retain the register test symbols and record any audited path binding.

**Usage example to document and run:** In a blank or Research-template workspace, open this feature's owned surface (Review and build strategy distribution packages). Exercise its first listed FR with the Phase 0 pinned resource/role fixture, then repeat with the resource or capability unavailable. Expected: Hidden parameters are not described as secrecy; unsupported restriction combinations remain unavailable. Save/reopen presentation state and close the widget; the domain job/data must remain unchanged.

**Evidence manifest:** `docs/dev/evidence/features/FEAT-UI-STRATEGY_PACKAGER/acceptance.json`. Record results; no pass is prefilled.

**Phase checkpoint owner:** Run E2E-P16 — Use a verified external data/strategy format, inspect conversion losses, produce a target-verified strategy package, exercise scoped CLI/MCP commands, and verify desktop/headless installation and cleanup. Publish `docs/dev/evidence/phases/phase-16.json` before closing this task/phase; use real providers, retained outputs and browser interaction assertions.

#### iv. Definition of Done and commit

**Done when:** DOD-F is satisfied for this feature; every listed acceptance oracle and applicable README/shared/catalogue obligation has evidence; reuse gaps are closed; its documented usage and affected UI workflow pass; no unimplemented owner behaviour remains behind a disabled control. The review and accepted feature commit are linked in the evidence manifest.

**Commit message:** `feat(ui): complete FEAT-UI-STRATEGY_PACKAGER`

**Accepted commit:** Not recorded — this is a plan. A Phase 0 proof of existing completion may bind an earlier acceptance commit instead of forcing new production code.

---

## 5. Release gate and dependency reconciliation

The register-level build graph and the earlier capability-level gate DAG are different views of the same delivery. For example, a canonical metric calculator can be built and golden-tested before the complete native engine is accepted, but the original native reducer/comparator gate still waits for real engine evidence. A generic project runner or native bundle adapter can be implemented before every optional receiver exists, but it cannot claim a successful missing receiver operation.

`Dependency_Schedule.json` retains all original nodes/edges and maps each capability gate to producing feature tasks or Phase 0 preparation. The gate's earliest acceptance phase is computed from the maximum of its mapped task phases and predecessor-gate phases; release gates also keep U0–U13 order. No original edge is erased to make the task graph fit.

The following are earliest planned gate phases, not achieved releases. Source-specific runtime, compatibility and performance evidence remains mandatory.

| Source release | No earlier than execution phase | Evidence status |
| --- | --- | --- |
| U0 | 1 | PENDING |
| U1 | 2 | PENDING |
| U2 | 5 | PENDING |
| U3 | 6 | PENDING |
| U4 | 7 | PENDING |
| U5 | 8 | PENDING |
| U6 | 9 | PENDING |
| U7 | 10 | PENDING |
| U8 | 11 | PENDING |
| U9 | 12 | PENDING |
| U10 | 13 | PENDING |
| U11 | 14 | PENDING |
| U12 | 15 | PENDING |
| U13 | 16 | PENDING |


## 6. Change, acceptance and scope controls

Changing task order requires regenerating and passing the schedule validator, updating the owner README where dependency semantics change, and refreezing any active Goal tracker. Required capability edges cannot be weakened to meet a date. An operation-gated relationship is not an unconditional runtime dependency.

Existing feature work, source changes and bug fixes do not create hidden feature identities. Track each change against the one assigned feature task. A discovery that genuinely changes the atomic feature set requires an explicit scope revision; preserving the number 205 is not permission to merge unrelated behaviours or omit requirements.

This plan does not overwrite domain READMEs, mutate the specification, implement production features, authorize externally consequential operations, activate the repository Task/Goal workflow, or commit to GitHub. Phase 0 must publish the authoritative detailed bindings before an executor consumes these concise task cards.

## 7. Sources and companion files

Primary scope: `HaruQuantAI_Feature_Requirement_Traceability_Register.md` and `inputs/traceability_register.json` (same 205-feature source). Required execution procedure: `docs/dev/feature_implementation_pipeline.md` at pinned blob `40c5cb2ebc1647655dd9f7e0417e2ffa631f6c3d`. Repository governance: `AGENTS.md` at the inspected commit. Baseline facts are itemized with source URLs in `Baseline_Audit.md`; no static “Completed” entry is silently promoted to verified acceptance.

Companions: `Implementation_Tracker.md` (exactly 205 feature checklist entries plus the separate eight prerequisites); `implementation_plan.json`; `Dependency_Schedule.json`; `Operation_Readiness.md`; `Workflow_Acceptance.md`; `Domain_Readme_Handoff.md`; `Plan_Browser.html`; `validate_plan.py` and its validation reports. These are representations and evidence aids for the same tasks, not additional implementation backlogs.
