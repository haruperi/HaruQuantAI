# HaruQuantAI V3 — Development Throughput Remediation Plan

**Date:** 9 September 2026
**Status:** PROPOSED — implementation and configuration changes have not been performed.
**Repository baseline checked:** `a32a46ad5c3407bdb7b68bf8dc270d327b6e7625` on remote `main`.
**Repository location:** `docs/dev/HaruQuantAI_Development_Throughput_Remediation_Plan.md`
**Basis:** The three supplied agent analyses, supplemented by targeted read-only repository checks and official tool documentation. Source references appear in §12.

## 1. Decision and objective

Keep HaruQuantAI V3, its focused feature architecture, and the complete registered product scope. Change the delivery process around that architecture. Do not restart the product, defer all tests, remove lifecycle guarantees, or make `git push --no-verify` the development policy.

The target is **more correctly accepted functionality per working hour and per unit of allowance**, not merely more generated code. The four-to-eight-hour ambition remains a throughput objective to evaluate, not a supported promise that the entire remaining acceptance contract will be finished within that time.

This plan attacks four different costs separately:

| Cost | Intervention |
|---|---|
| Repeated broad validation | Fast default tests; change-aware routing; one comprehensive integration qualification per candidate/batch. |
| Repeated reasoning and handoffs | Prepared task packets; risk-tiered planning; direct bounded corrections; deterministic administrative close-out. |
| Repetitive authoring | Reuse existing implementations; generate structural boilerplate and evidence projections; shared conformance harnesses. |
| Sequential delivery | Small coherent batches, then bounded existing parallel lanes with isolated writes and one integrator. |

**Preserve:** feature identities, owning requirements, public contracts, strict typing, applicable coverage floors, numerical correctness, authorization and account isolation, persistence safety, lifecycle/removal behavior, independent review, owner authorization, and honest distinction between component evidence and real-provider qualification.

**Do not add:** another orchestrator, a new general-purpose agent framework, a separate project-management database, a dashboard, or a second source of feature status. Extend existing scripts and records.

## 2. What the evidence establishes—and what it does not

| Finding | Evidence and interpretation |
|---|---|
| Python coverage and HTML reporting are default pytest options. | Verified in `pyproject.toml`. A focused command requires an override today. [R2] |
| A UI-only change can trigger full Python validation on push. | Verified: the pytest hook matches `app/`, ignores filenames, and runs whole-app coverage; mypy is also broadly triggered. [R1] |
| Ordinary checked-in pre-commit hooks do not run pytest. | Verified: formatting, lint, hygiene and secret scanning are pre-commit; pytest/mypy are pre-push. Local IDE or hook behavior still needs local inspection. [R1] |
| Complete validation always includes workflow-controller checks. | Verified in `scripts/ci_check.py`; its nested `uv run` also lacks a lock-preservation option. [R3] |
| The checked-in CI workflow does not run the UI's npm checks. | Verified in `.github/workflows/ci.yml`; UI typecheck, test and build scripts exist separately. [R4, R5] |
| Remote `main` reports no enabled branch protection. | The branch response at inspection reports `protected: false` and required checks off. Do not assume CI is an enforced acceptance gate. [R9] |
| Small corrections currently return through Planner. | Verified in `AGENTS.md`. Owner gates and reviewed-byte identity are intentional protections, not things to silently bypass. [R6] |
| The plan requires whole-feature scope and extensive evidence. | Verified in the plan's execution contract and Definition of Done. Feature count is not a uniform effort measure. [R7] |
| Evidence-generation tooling already exists. | `scripts/generate_phase0_evidence.py` parses the ratified plan/register and has pinned historical references. Reuse appropriate parsing/validation; do not rewrite historical Phase 0 truth. [R8] |
| Task 1.16 reportedly suffered five iterations, genuine UI defects and administrative failures. | Reported by the supplied local-agent analyses. These local logs and exact timings were not independently re-executed here. [S1] |

The following claims are **not** planning assumptions: “75% was the AI debating,” a guaranteed 5–10-minute duration for every feature, a guaranteed allowance reduction, or an architectural proof that any particular completion time is impossible. The supplied analyses do not establish those conclusions. Their counts of requirements also use differing descriptions; this plan does not combine them into a new metric.

Use Agent 1's useful suggestions about hooks, batching and automation; retain Agents 2 and 3's distinctions about real defects, risk, test selection and integration enforcement. Do not adopt blanket Quick-Fix-on-main, a universal one-to-two-test limit, or status generation from file existence.

## 3. Rollout structure

These are **eleven top-level work orders within four remediation change sets**. Until an explicitly reviewed workflow amendment replaces the current atomic Task contract, each independently reviewable work order must follow the workflow required by `AGENTS.md`. In particular, DT-01, DT-02 and DT-03 are three separate Tasks; their different responsibilities, write paths, validation and rollback boundaries must not be combined into one Change Set A implementation Task. Workflow/approval changes themselves receive strong review.

| Change set | Work orders | Exit condition |
|---|---|---|
| A — Stop avoidable waiting | DT-01 through DT-03 | Mechanical regressions covered; fast test defaults; verified local integration protection before hook relaxation; remote enforcement handled separately. |
| B — Stop repeated reasoning | DT-04 through DT-06 | Risk-tiered packets, bounded direct corrections, trustworthy validation records and deterministic close-out. |
| C — Stop repetitive authoring | DT-07 and DT-08 | Evidence projection and one useful scaffolding/conformance path demonstrated without false acceptance. |
| D — Increase useful delivery throughput | DT-09 through DT-11 | Conservative batching and bounded parallel lanes validated using accepted outcomes; a strategy-ready milestone is frozen and measured separately from full V3 completion. |

Implement A before spending effort on a universal scaffolder or parallel scheduling improvements. Production development can resume on the improved path after A and B; completing every optional automation is not a new prerequisite for working on strategies.

### Dependency order

```text
DT-01 → DT-02 (combined DT-02A + DT-02B) → DT-03 → DT-04 → DT-05 → DT-06 → POST-DT-06 PILOT

POST-DT-06 PILOT → DT-07 → DT-08 (optional evidence/scaffolding path)
POST-DT-06 PILOT → DT-09 → DT-10 (optional batching/parallelism path)
POST-DT-06 PILOT → DT-11         (strategy-ready milestone path)
```

The owner authorized DT-02A and DT-02B as one combined DT-02 delivery on 9 September 2026. Implementation still establishes and measures the DT-02A fast default before enabling DT-02B routing so the incremental benefit remains observable. DT-08 is not a prerequisite for DT-09. DT-11 depends on the post-DT-06 pilot, not on completing optional scaffolding or parallelism. Defer later automation whose measured benefit is weak. All change sets must preserve previously passing safeguards.

## 4. Change set A — Stop avoidable waiting

### DT-01 — Capture a bounded baseline and fix recurring mechanical failures

**Primary paths:** existing `.agents/` controller and tests; `.pre-commit-config.yaml`; `.github/.secrets.baseline`; new scoped `.gitattributes`; existing runtime logs. Inspect the local ignored run configuration, Git hooks and run records without publishing credentials or private logs.

**Actions**

1. Record local HEAD, upstream HEAD, ahead/behind state, active workflow state, dirty paths, Python/Node versions and actual hook configuration. The checked repository targets Python 3.14; do not substitute older project-memory settings. Preserve active work and user changes. No reset, automatic stash, force-push or recreation of an active task.
2. Extract available stage/command timings from Task 1.16 and other existing accepted-run records. Record unknown values as unknown; do not rerun historical product tasks merely to manufacture a baseline.
3. Reproduce the reported administrative problems with small controller/Git fixtures: legitimate commit-hash secret-scanner findings, omitted generated paths, staged/unstaged normalization and approval fingerprint drift.
4. Resolve a verified scanner false positive without requiring every feature Task to edit `.github/.secrets.baseline`. Prefer a schema-aware, field-specific treatment for `baseline_commit` combined with deterministic verification that the value resolves to a real repository commit. An equivalent design is acceptable only when it avoids per-feature shared-baseline churn and retains the same narrow security boundary. Do not exclude the evidence directory, disable a detector globally, or allow every 40-character hexadecimal value everywhere. Keep ordinary new-secret detection effective.
5. Define UTF-8/LF writing for coordination documents and deterministic JSON. Add attributes for the precise relevant paths, starting with `.agents/task/*.md` and `.agents/*.toml`; do not renormalize the entire repository. Normalize an inactive/new document before approval, not by silently changing approved bytes afterward.
6. Run mutating formatting and generation **before** freezing the reviewed candidate. After approval, use check-only validation. A product edit or unexplained byte change still invalidates the appropriate approval; retry logic must not simply ignore mismatches.
7. Make the generator's complete output inventory available before execution, so known generated paths are not discovered as unauthorized writes during close-out.

**Acceptance**

- A legitimate schema-valid `baseline_commit` that resolves to a repository commit can complete normal close-out without disabling secret scanning and without a per-feature `.github/.secrets.baseline` modification.
- Synthetic secret-detection regression cases remain detectable; no actual credential is used as a fixture.
- An arbitrary hexadecimal value in any unapproved field remains subject to secret detection.
- A Windows-style staged/unstaged normalization fixture cannot silently change the approved tree.
- Changing product code after approval still blocks acceptance.
- Known generated outputs are listed before the executor starts.
- Local branch divergence is reported before an expensive delivery attempt, without modifying user work.

**Rollback:** Revert only the focused fix that regresses behavior. Preserve run evidence; never recover by weakening byte identity or deleting tests.

### DT-02 — Make normal validation fast and comprehensive validation explicit

**Primary paths:** `pyproject.toml`, `scripts/ci_check.py`, tests for the validation router. Add at most one small routing helper if needed; retain `ci_check.py` as the public entry point.

DT-02A and DT-02B are delivered as one owner-authorized change set. DT-02A remains the first internal implementation and measurement checkpoint; DT-02B then adds bounded advanced impact routing without a separate commit or approval cycle. The combined delivery does not waive either stage's acceptance criteria.

#### DT-02A — Fast defaults and explicit validation profiles

**Actions**

Remove these four entries from `[tool.pytest.ini_options].addopts`:

```toml
"--cov=app",
"--cov-report=term-missing",
"--cov-report=html",
"--cov-fail-under=80",
```

Retain import mode, strict configuration/markers, reporting, warning policy and cache configuration. Retain `[tool.coverage.run]` branch coverage, `[tool.coverage.report] fail_under = 80`, and any stronger owner-specific coverage obligation. Coverage becomes opt-in, not optional at its required boundary. [R2, W1]

Introduce these **proposed** profiles; they are new interfaces to implement, not existing commands:

| Profile | Meaning |
|---|---|
| `affected` | Explicit changed scope, owner/consumer tests, relevant static/contract checks; no global coverage or default full build. |
| `python` | Comprehensive Python/product checks, strict mypy, architectural/documentation checks and full applicable coverage. |
| `ui` | UI typecheck, Vitest and production build; applicable browser qualification remains separately required. |
| `workflow` | Workflow-controller tests, self-test and applicable lint/type checks. |
| `integration` | Select the necessary comprehensive profiles for the candidate against its integration base. |
| `full` | All applicable profiles, including workflow and UI; conservative default when no profile is supplied. |

In DT-02A, implement the explicit profiles with straightforward conservative UI, Python, workflow, documentation and mixed-scope routing. Existing no-argument invocation remains conservative. A simple path-to-profile mapping is sufficient for this stage; unknown, shared or mixed scope widens to `full`.

#### DT-02B — Advanced candidate and dependency-aware routing

After measuring DT-02A, add `--base`, `--head`, `--explain` and `--report` only when their expected benefit justifies the added implementation and maintenance cost. The two refs must resolve to commits. `--explain` outputs selected commands and routing reasons without executing them.

Use the merge-base-to-candidate delta for committed changes, including deletions, renames and both names of renamed paths. During local development, union staged, unstaged and relevant untracked paths. For integration acceptance, require a clean materialized candidate and include changes introduced while combining it with the current base. A missing base, unknown path, incomplete ownership mapping or inconclusive dependency relationship widens validation rather than returning a misleading empty selection.

**Initial routing policy**

| Change | Iterative checks | Integration checks |
|---|---|---|
| UI presentation and local UI behavior | Selected UI tests and relevant type/contract checks | Full UI checks and applicable browser regression; no unrelated Python suite. |
| Python feature internals | Owner tests plus affected public consumers | Comprehensive Python profile. |
| Shared public contracts, generation, composition, kernel, cross-stack boundary | Relevant consumers, including UI consumers | Python and UI profiles; expand to full when impact is uncertain. |
| Workflow controller, role prompts, approval rules | Focused workflow tests and self-test | Workflow profile plus every product profile affected by the change. |
| Dependency locks, root tool configuration, validation/CI or routing code | All affected tooling checks | Full profile by default. |
| Pure prose or generated status projection | Syntax/schema, links/bindings and deterministic projection checks | Relevant documentation/evidence checks; no automatic product test rerun solely for nonsemantic bookkeeping. |
| Ambiguous or mixed scope | Union of all applicable checks | Conservative full profile. |

A capability dependency graph alone is not a complete test-impact graph. Include public import/contract consumers, integration fixtures, `conftest.py` scope, generators and UI/API consumers. Do not build a speculative whole-program dependency engine: begin with conservative domain routing and existing bindings.

Use locked dependencies for the runner and all nested commands. `uv run --locked` errors rather than silently rewriting an outdated lock; this distinction is documented by uv. Do not change dependencies merely to perform validation. [W4]

Deduplicate identical command invocations within a profile combination. Remove the standalone provider-disable matrix invocation only after confirming it is collected and covered in the relevant comprehensive run; otherwise keep one explicit `--no-cov` invocation. Do not accidentally drop the matrix.

**DT-02A acceptance**

- Focused default pytest produces no coverage report and does not alter coverage artifacts.
- Comprehensive Python validation retains the coverage floor and fails on test failure or inadequate required coverage.
- UI-only routing selects no unrelated Python test/mypy run; unknown impact never silently selects nothing.
- The full profile executes every required family once, including UI and workflow checks.
- Dependency files are unchanged by validation.

**DT-02B acceptance**

- Explain-mode routing tests cover UI-only, Python-only, contracts, root fixtures, lock changes, workflow changes, mixed changes, deleted/renamed files, untracked files and unknown scope.
- Candidate selection uses the exact resolved base/head identities and invalidates stale results.
- Public-contract and dependency-aware routing includes known consumers without pretending to be a complete whole-program dependency engine.
- Measurement shows that DT-02B improves accepted throughput or diagnostic clarity enough to justify retaining it; otherwise DT-02A remains the supported path.

### DT-03 — Establish local acceptance protection, then add remote enforcement

**Primary paths:** `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `scripts/ci_check.py`, `.agents/` close-out/integration behavior, `AGENTS.md`, `.agents/PROCEDURE.md`, and repository protection settings.

**Target flow**

```text
Task/batch candidate branch
  → independent review and scoped tests
  → explicit commit/publish authorization
  → required integration checks against current main
  → authorized merge
  → ACCEPTED
```

**Actions**

1. Establish one local integration-candidate gate using the DT-02 profiles and locked environments. It must evaluate every profile required by the classifier, including the applicable UI `typecheck`, `test` and `build` commands, and fail on a missing, failed or unexpectedly skipped prerequisite. Use the repository's package lock; do not update packages as part of validation setup.
2. Keep applicable real-provider/browser checks at their existing required phase/operation gates. Mocked Vitest success is not browser or provider qualification.
3. Repair actual baseline failures exposed by the local checks in bounded changes. Do not change floors, blanket-ignore errors or declare the baseline green because selected checks passed.
4. Prove that the local integration-candidate gate rejects a deliberately failing or stale candidate. This local replacement permits the first hook-speed improvements without waiting for repository-administration work.
5. Once the local replacement gate is proven, keep pre-commit formatting, lint, hygiene and secret detection. Replace the broad pre-push full-suite hooks with lightweight scope/consistency checks. Focused behavioral tests run during execution; comprehensive suites run at the local integration-candidate boundary rather than on every push.
6. As a separate repository-administration step within DT-03, make CI invoke the same integration profiles and install the locked UI dependencies needed for the existing UI commands.
7. Add one stable final remote status named `acceptance`; it must always report and must reject missing, failed or unexpectedly skipped prerequisite profiles. Workflow-level path filtering must not prevent this required status from reporting. [W3]
8. Configure and verify required checks/PR protection only with the owner's explicit repository-administration authority. An unavailable permission is a remote-enforcement blocker, not permission to assume protection exists and not a blocker to retaining the proven local integration gate.
9. Amend acceptance semantics only after choosing and documenting the governing model: local-first acceptance with remote confirmation, or PR-first acceptance enforced remotely. Preserve `APPROVED: EXECUTE` and `APPROVED: COMMIT`, or the existing legitimately frozen equivalents. Existing local commit/merge permissions do **not** authorize publishing or remote merging; any remote-action permission must be explicit and default off.
10. Never remove the existing broad protection before the local replacement is operational. After remote enforcement is proven, measure whether the local comprehensive gate can be reduced further without creating an acceptance gap.

**Acceptance**

- A deliberately failing candidate cannot be accepted or merged through the selected governed path.
- A newly pushed untested candidate is not marked complete.
- A UI-only candidate runs UI validation without unrelated Python coverage.
- A Python-changing batch receives comprehensive Python coverage before acceptance.
- A stale local or remote successful check does not approve a different candidate/base combination.
- Fast local checks preserve secret detection and do not start full pytest or HTML coverage.
- Remote-action authorization cannot be inferred from local-only permission.
- The first local speed gains do not depend on GitHub-administration access; when remote enforcement is unavailable, the proven local integration gate remains authoritative under the documented local-first model.

**Rollback:** Keep or restore the conservative local integration gate until remote enforcement is healthy. Never solve a broken CI migration with routine `--no-verify` or administrative bypass.

## 5. Change set B — Stop repeated reasoning

### DT-04 — Classify failures and introduce bounded direct correction

**Primary paths:** `AGENTS.md`, `.agents/protocol.toml`, `.agents/orchestrator.py`, the actual controller transition/validation modules, canonical role/close-out prompts, `.agents/PROCEDURE.md`, controller tests.

**Decided routing**

| Finding | Route | Boundary |
|---|---|---|
| `IMPLEMENTATION_FIX` | Reviewer → Executor → Reviewer | Expected behavior, ownership and authorized scope are unchanged. |
| `DESIGN_CHANGE` | Reviewer/Executor → Planner | Requires a new contract, scope, requirement interpretation, security decision or architectural choice. |
| `ADMINISTRATIVE_RETRY` | Deterministic controller repair/retry | Exact allowlisted operation over unchanged reviewed inputs; no product-policy decision. |
| `ENVIRONMENT_FAILURE` | Preserve state; bounded environment recovery | No product replan solely because a process, runner or dependency installation failed. |

Allow at most two direct implementation-correction rounds before targeted Planner escalation. Allow at most one automatic retry of the same administrative/environment operation. Persistent failure must stop with a concrete diagnosis, not produce another indistinguishable loop.

Every reasoning invocation still receives a valid standalone handoff. A correction references the current approved task packet and exact failing expectation; it does not recreate all prior analysis. Administrative repair cannot edit product source, contracts, approved requirements or security policies. Secret-baseline policy changes are not a permanently self-authorized administrative action.

**Acceptance:** Tests cover each route, retry bounds, preserved work, stale approval rejection, scope-change escalation and refusal of an administrative attempt to change production code.

### DT-05 — Prepare compact task packets and use risk-tiered planning

**Primary paths:** existing plan/register/evidence parsing utilities, one new bounded task-packet generator, `docs/templates/prompt/`, `AGENTS.md`, relevant controller config/schema/tests. Generated packets belong in runtime task/run storage, not a second canonical plan.

**Required packet contents**

- Task and feature IDs; source commit; exact source locations/hashes; current baseline and authorized write footprint, including generated outputs.
- Complete owning FR/NFR obligations, applicable shared NFRs and catalogue obligations; no truncation to satisfy a token budget.
- Exact public contracts and dependencies; actual accepted predecessor evidence; existing provider/test/usage paths and aliases.
- Requirement-specific expected behavior, failure cases, numerical examples when applicable, lifecycle/cleanup obligations and qualification boundaries.
- One compatible accepted implementation example when available; explicit reuse decision; relevant generation/template instructions.
- Test selections, validation profiles, expected evidence, risk tier and remaining unresolved decisions.

Extraction is deterministic where sources are structured. Engineering choices are made once by Planner when genuinely unresolved, then frozen. A packet with a missing contract, ambiguous oracle or unbound required path is not executor-ready. A packet is an index and bounded extract of authority, not permission to ignore that authority. The reviewer can check original source spans directly.

**Risk tiers**

| Tier | Examples | Workflow |
|---|---|---|
| Routine | Nonsemantic prose, an isolated presentation adjustment, deterministic mechanical generation | Prepared packet → Executor → focused independent review. No fresh exploratory planning when nothing needs deciding. |
| Standard | A well-specified bounded service or UI interaction using stable contracts | Prepared packet → Executor → independent review; Planner only for an unresolved decision. |
| Critical | Authorization/session scope, cross-account or cross-workspace operations, trading/risk, numerical correctness, persistence/recovery, resource ownership/concurrency, external providers and network integrations, destructive actions, workflow approval/validation policy | Targeted explicit planning/risk analysis → Executor → stronger independent/adversarial review. |

Risk follows behavior, not file type or change size. A manifest that changes mandatory dependencies is not low-risk metadata; a session-access widget is not merely presentation; a shared DTO changes a contract. Ambiguous classification selects the stronger tier.

Keep the full policy available but reduce root `AGENTS.md` to binding invariants and precise routing. Do not replace a large file with a list of links that still forces every role to load everything. Load only the relevant role/transport/risk instructions, while retaining all applicable rules.

Reuse task-local context during a bounded correction. Do not carry hundreds of tasks through one ever-growing session, or reset a role mid-correction without a complete current packet and state handoff. Do not attribute specific token costs to an unobserved provider implementation.

**Acceptance:** A normal prepared task begins without a new exploratory Planner invocation; a contract ambiguity blocks rather than being invented; a stale source fingerprint invalidates the packet; critical classifications retain stronger review; no requirement disappears from extraction.

### DT-06 — Reuse trustworthy validation and make close-out deterministic

**Primary paths:** `scripts/ci_check.py`, existing run evidence/logging, `.agents/` controller and close-out path, role prompts and tests.

The runner, not the LLM, records commands, working directories, exit codes and durations. Store full logs outside the conversation and return bounded summaries plus log references. Reviewers still independently judge behavior, verify source/oracles and run selected adversarial checks. An executor's statement that tests passed is not a validation receipt.

A reusable receipt records the candidate/base identity; source/input manifest; validation policy and runner identity; contract/test/config/lock hashes; command/arguments/working directory; relevant environment and fixture/seed identities; timestamps/duration/exit code; and log/report hashes. A hash is integrity metadata, not proof of trusted origin: consume controller/CI-produced records from a known channel, not agent-authored JSON masquerading as a test result.

Start with conservative exact-input reuse **within the same candidate**. Do not build cross-commit cache reuse or a signing service in the first version. Changes to tests, contracts, fixtures, environment, runner, policy or relevant source invalidate the receipt. Runtime logs/receipts cannot self-reference their own hashes; define their exact nonsemantic exclusion boundary. Do not broadly exclude documentation or evidence that affects requirements or acceptance.

Move deterministic path checks, formatting verification, receipt validation, authorized commit/merge mechanics, journal archival and final receipt creation into the existing controller. Review conclusions remain authored by the reviewer. No controller decision invents an approval, interprets an unresolved requirement or grants an operation privilege.

Retain the existing self-reference avoidance: committed evidence pins the tested tree/parent and report hashes; final accepted commit is written in close-out evidence after creation. Do not manufacture an empty implementation commit to record its own hash. [R7]

**Acceptance:** Valid same-input results can be reused across a handoff; changing an input rejects them; forged/edited records are not accepted; a reviewer-selected new check runs; close-out needs no LLM invocation when no engineering decision remains; actual byte drift still blocks acceptance.

### Post-DT-06 pilot and continuation gate

Before implementing optional evidence/scaffolding/batching/parallelism work, exercise the remediated A+B path on three newly accepted representative features:

1. one UI interaction or presentation feature;
2. one ordinary stateless service feature;
3. one critical stateful, security-sensitive, concurrency or numerical feature.

Task 1.18 (`FEAT-ORCH-MANAGE_JOBS`) may serve only as the critical stateful/concurrency sample. Its persistent shared jobs and attempts, restart survival, authoritative lifecycle and resource-coordination behavior classify it as Critical under DT-05. It must not be treated as the routine Quick-Fix/direct-execution benchmark or used to justify weakening the critical workflow.

Compare each feature only with reasonably similar historical work. Record planning, execution, validation, review, close-out, correction causes, accepted outcome and available allowance observations. Decide explicitly whether DT-07 through DT-10 are justified, need revision or should be deferred. DT-11 may proceed from this checkpoint because it defines the product milestone needed to return attention to strategy development.

**Acceptance:** The three features are genuinely accepted rather than replayed historical work; administrative replanning is zero for repaired cases; no required safeguard or evidence mapping is lost; and the continuation decision cites measured results instead of assumed speedups. The ten-feature sample in DT-10 remains a later confirmation sample, not the first effectiveness measurement.

## 6. Change set C — Stop repetitive authoring

### DT-07 — Project evidence deterministically without inventing completion

**Primary paths:** `scripts/generate_phase0_evidence.py` for reusable parsing/validation only, the existing live evidence update path, `docs/dev/evidence/` schemas/bindings/tests, controller integration.

Inspect and reuse the existing live updater before adding another command. Preserve pinned historical Phase 0 source snapshots. Where there is no reusable live projection operation, add a small dedicated current-progress operation rather than rerunning historical generation indiscriminately.

Inputs are authoritative feature metadata, explicit requirement-to-check mappings, controller-produced validation records and reviewed acceptance decisions. Outputs are the existing feature acceptance record and current contract/path/usage/requirement/progress projections. The model supplies only new engineering mappings/findings—not repetitive JSON synchronization.

The operation must support output-path discovery, a preview, check-only validation and application of an exact reviewed projection. Outputs must be stable and idempotent. Validate all new records before replacing existing ones. Preserve existing aliases, statuses and the distinction between implemented adapters and `OPERATION_NOT_QUALIFIED` real-provider behavior.

Do not scan files, see a function or test name and declare its requirement passed. Do not delete failure evidence, upgrade unavailable operations to qualified, rewrite historical accepted facts, or treat copied examples as successful execution. Generate projections during the accepted delivery cycle, not only at the end of the phase.

Only the integrator writes shared aggregate ledgers during parallel work. Workers provide feature-local draft mappings/results. Integration regenerates and validates aggregate projections before final candidate qualification.

**Acceptance:** A repeated run changes no bytes; missing/failed evidence prevents completion; historical Phase 0 snapshots remain unchanged; an unavailable real provider remains unqualified; a changed binding cannot silently orphan a requirement; generated-path inventory is complete.

### DT-08 — Reuse code, scaffold structural files and share conformance tests

**Primary paths:** canonical feature templates under `docs/templates/`, a small proposed scaffolding command under `scripts/`, existing feature tests/conformance infrastructure and usage examples.

Start with **one** recurring stateless backend feature shape based on a compatible accepted V3 implementation. Generate only the agreed structural shell: README, immutable manifest, strict configuration, lifecycle entry point, necessary contract placeholders, offline `_usage.py` shell and registration/evidence draft. Do not automatically invent business defaults, durable state or authorization policy.

Generate or propose the exact `pyproject.toml` feature entry-point registration when the feature shape requires one. Because `pyproject.toml` is a shared composition file, only the serialized integrator may apply that change during parallel delivery; draft workers record the required entry without concurrently editing the shared file.

Scaffolding must refuse overwrites and never mark a feature accepted. A generated shell is explicitly incomplete until real behavior, examples and acceptance assertions exist. Do not create passing placeholder tests or conceal missing implementations with `pass`, permissive mocks or “not applicable”.

Parameterize common manifest/configuration, mount/unmount, failure cleanup, provider removal/replacement and physical-removal checks using the existing harnesses. Keep owner-specific behavioral tests, especially session cleanup, cancellation, persistence, numerical causality and fail-closed behavior. Test count is determined by obligations—not a universal cap.

Before greenfield implementation, make a bounded reuse decision: retain correct current V3 behavior, adapt an approved normalized V2 donor when genuinely applicable, or implement what is missing. V3 contracts remain authoritative. Raw V2 copying or a new broad legacy audit is not authorized, and missing donor evidence alone is not a blocker. [R6]

For numerical tests, specify small independent golden values and boundary/causality cases; do not calculate expected values by reusing the same algorithm under test. For UI, preserve interaction/lifecycle tests rather than maximizing brittle snapshots.

**Acceptance:** Generated structure conforms to existing contracts; rerunning cannot overwrite work; incomplete behavior cannot gain a completed status; injected lifecycle/resource defects fail the shared harness; feature-specific invariants remain covered. Expand to stateful/UI shapes only after the first shape proves useful.

## 7. Change set D — Increase delivery throughput

### DT-09 — Experiment with conservative batching without merging feature ownership

**Primary paths:** execution-policy sections of `docs/dev/Phased_Feature_Implementation_Plan.md`, `AGENTS.md`, `.agents/GOALS.md`, goal/integration controllers and tests. Preserve feature cards and requirements.

The initial DT-09 implementation batches only preparation, reusable context, integration validation and operator pushes for **two or three** routine/standard features with stable contracts and a coherent integration boundary. It does not batch their implementation authority or acceptance. Do not batch authorization, resource accounting, persistence recovery or other critical features merely because they are adjacent in the plan.

Each feature retains its own folder, identity, requirement mapping, Task branch, review, tests, acceptance record, exactly one implementation commit and its required merge record. Preparation, reusable task-packet inputs, broader integration validation and pushes may be grouped where the current protocol permits. Any final deterministic aggregate-evidence commit must be separately authorized bookkeeping and must not masquerade as a feature implementation. Record every constituent commit and the tested batch/integration identity.

Do not amend the current clean-accepted-`main`, one-child-Task, branch, review, implementation-commit or acceptance rules in the initial experiment. Required predecessors remain accepted and contract-stable. Select batch members whose shared preparation or validation work can be reused without consuming an unaccepted internal predecessor.

A later provisional multi-feature candidate mode may be considered only as a separate versioned protocol proposal after DT-09 measurement. That proposal must independently specify authorization, path ownership, predecessor semantics, failure isolation, per-feature commits, evidence and rollback. It is not implicitly authorized by this plan.

Each constituent feature is reviewed and accepted through the current Task protocol. The grouped integration candidate then qualifies the combined accepted set before push or the next declared integration boundary. Shared aggregate evidence remains single-writer and deterministic. Scope cannot grow merely to fill a batch. A failed grouped integration gate blocks the batch action and creates a bounded correction obligation; it does not erase truthful prior Task evidence or relabel an unaccepted feature as complete.

Keep all 205 feature identities and registered scope. Do not rewrite the master plan into 30 giant untraceable tickets. Annotate a strategy-ready scheduling priority within the existing dependency graph, without deleting prerequisites or claiming the remaining platform is complete. The aim is earlier useful strategy work while the full roadmap remains intact.

**Acceptance:** Two/three features share reusable preparation and one broader integration/push cycle while retaining separate Task branches, reviews, implementation commits and acceptance records; integration failure blocks the grouped action; required edges are preserved; shared files have one writer; already correct behavior is not rewritten merely to create another acceptance commit.

### DT-10 — Benchmark bounded parallelism and adopt the measured path

**Primary paths:** existing opt-in parallel/goal/integration-queue behavior, local run configuration, existing run summaries; no new orchestration engine.

Enable two genuinely independent lanes first, then evaluate the existing three-lane capability. Use separate branches/worktrees and task packets with complete write footprints. Reserve shared files for the integrator. Predecessor eligibility must include accepted evidence, not merely a folder's existence or a draft promise.

On integration, refresh against the current base, regenerate shared projections, inspect the resulting delta and qualify the exact combined candidate. Retain independent review of changed behavior. Do not grandfather stale approval solely because Git applied a patch cleanly.

Budget machine resources across **all** lanes, test workers and UI builds. Do not multiply three agents by unrestricted `pytest -n auto` and assume more processes imply more throughput. Keep small focused suites serial when worker startup costs more than it saves.

Profile representative suites with whole-command timing and pytest durations. Benchmark one, two and four workers only on parallel-safe selections. Use isolated temporary databases, ports and filesystem paths; keep unsafe tests serial until corrected. `worksteal` balances uneven durations; `xdist_group` placement requires the appropriate `loadgroup` scheduling mode and is not automatic isolation. [W2, W5]

After profiling and verifying resource isolation, evaluate domain-based CI shards behind the single required aggregate `acceptance` status from DT-03. The aggregate must fail when any required shard is missing, cancelled, skipped unexpectedly or failed. Retain a serial or broader fallback for tests whose cross-domain dependencies make safe sharding inconclusive.

Use the first ten **accepted** pilot features, spanning UI interaction, ordinary service behavior and a critical stateful/security/numerical case. Compare within risk/complexity classes, not by treating every feature as identical. Do not retest an already accepted critical implementation as a made-up “new feature” just to fill the sample.

Record these fields in existing runtime summaries:

```text
task_or_batch_id, feature_ids, risk_tier, baseline, candidate
planning_elapsed, execution_elapsed, review_elapsed, closeout_elapsed
command_wall_time, integration_wait, correction_count, correction_causes
acceptance_result, escaped_regression_or_reopen
provider_reported_usage_if_available
allowance_before, allowance_after, other_concurrent_usage_known
```

Use nonoverlapping stage durations for totals; nested subprocess timings are diagnostic breakdowns, not extra elapsed time to add twice. Allowance percentage points are not tokens or a per-task billing measure when other work shares the allowance.

**Initial operating targets, not guaranteed results**

| Measure | Target / adoption rule |
|---|---|
| Warm targeted feature feedback | p95 at or below 30 seconds for an ordinary unit/component selection, excluding dependency installation and full builds. Profile and classify slower selections rather than hiding them behind a universal target. |
| Warm ordinary pre-commit | p95 at or below 20 seconds. |
| Warm ordinary pre-push | p95 at or below 60 seconds; no hidden comprehensive suite. |
| Administrative failure causing full product replanning | Zero after known cases are repaired. |
| Identical validation rerun only because the role changed | Zero on the standard path when a valid runner receipt exists. |
| Routine/standard planning + review + close-out share | Aim below 25% of elapsed time; investigate the residual, do not compromise critical review to hit a ratio. |
| Accepted behavior per hour and allowance | Must improve for comparable scope; actual measured values replace claims. |
| Safety/quality | No bypass of required acceptance, lost requirement mappings or regression evidence. A small clean pilot is not proof of zero long-term defects. |

Measure model choices only after the process changes. Compare allowance per accepted change, first-pass correctness and correction loops at the same risk tier; no model or effort setting is prescribed from unsupported names/performance claims.

**Adoption:** Keep improvements that increase accepted throughput without weakening evidence. Disable a slower/flakier parallel configuration rather than discarding the product architecture. Do not build a dashboard to answer what a small run-summary report can show.

### DT-11 — Freeze and deliver the strategy-ready milestone

**Primary paths:** `docs/dev/Phased_Feature_Implementation_Plan.md`, `docs/dev/evidence/dependency-schedule.json`, applicable owning READMEs, Goal selection/runtime inputs and a bounded milestone evidence record. Preserve the complete 205-feature roadmap and all existing feature identities.

Define the first useful strategy-development outcome as this reproducible vertical slice:

```text
Load historical data
  → define a strategy
  → run a deterministic backtest with explicit execution assumptions
  → inspect trades and performance
  → save and reproduce the experiment
```

Use the following as a candidate capability checklist, not as a second feature registry or a predetermined implementation list:

- local historical-data ingestion and retained bar/feed access;
- only the indicators required by the selected first strategy, rather than a mandatory generic indicator catalogue;
- strategy definition covering entry, exit and risk rules;
- deterministic bar or tick backtesting with documented execution assumptions;
- an inspectable trade ledger, P&L, drawdown and core performance metrics;
- a minimal results/equity inspection UI; and
- saved experiment identity and reproducible replay.

The derived dependency closure and owning contracts determine the actual participating features and operations. Omit a checklist item only when the frozen milestone contract proves it unnecessary; do not add unrelated indicators or platform extensions merely because they appear in this illustrative list.

Derive the smallest valid dependency closure from the frozen dependency schedule and owning contracts. Classify every required feature as already accepted, remaining implementation, operation-gated qualification or externally blocked. Freeze an explicit Goal selection for only the remaining necessary entries; do not delete prerequisites, weaken capability edges, expand the selection silently or mark unrelated V3 features complete.

State the milestone's exact inputs, supported offline/provider assumptions, expected outputs, deterministic replay identity, UI or public usage path, failure behavior and acceptance commands. Separate the desired four-to-eight-hour timebox from the evidence: estimate only after the closure and prepared task packets reveal the actual remaining scope. If the closure cannot fit the timebox, report the smallest honest runnable subset and the missing obligations rather than redefining V3 completion.

**Acceptance:** One bounded workflow loads retained historical data, executes a saved strategy through a deterministic backtest, exposes inspectable trades and performance, and reproduces the same experiment under its documented identity and assumptions. Every participating requirement and feature remains traceable; all deferred V3 work remains visibly open; no mocked or component-only evidence is claimed as real-provider qualification.

**Rollback:** Remove only the milestone annotation/Goal selection when its dependency derivation is wrong. Do not revert accepted product features or rewrite the master feature registry.

## 8. Testing cadence after remediation

| Boundary | Required work | Not the default |
|---|---|---|
| Editing | Behavior-specific tests, relevant consumers, small failure/golden/lifecycle cases | Full coverage, full UI build after each edit, unrelated workflow tests. |
| Pre-commit | Formatting, lint, hygiene and secret detection | Full pytest/mypy or full app build. |
| Pre-push | Lightweight submission/scope consistency checks | Automatic comprehensive coverage on each eligible path. |
| Candidate/batch acceptance | Independent review; comprehensive profiles selected conservatively; applicable owner/phase checks; required status before merge | Repeating an identical gate merely because another role starts. |
| Full regression/phase/release | Entire applicable suite, coverage, browser/cross-domain and required real-provider/performance/fault qualification | Claiming mocked component tests certify live/provider behavior. |

A later dedicated test session expands stress, robustness and system scenarios. It is not the first time core behavior receives assertions. Preserve mandated lifecycle/removal evidence through shared harnesses instead of deleting it. Faster execution and less repetitive test authoring are separate optimizations.

## 9. Concrete command reference

These commands use existing tools/scripts unless explicitly labeled proposed. They have not been run on the user's machine as part of preparing this plan. Substitute only paths resolved in the relevant packet.

### Local preflight and authorized remote refresh

```powershell
git status --short --branch
git rev-parse HEAD
git config --show-origin --get core.hooksPath
git config --show-origin --get core.autocrlf
git rev-list --left-right --count HEAD...origin/main
```

A missing Git configuration key normally reports no configured value; that alone is not a workflow failure. The divergence command uses the currently available remote-tracking ref and must report when its freshness is unknown.

When a current remote ref is required, only an authorized operator/controller outside an active Planner, Executor or Reviewer invocation may run:

```powershell
git fetch origin
```

`fetch` does not modify product files, but it performs network I/O and mutates remote-tracking refs. It is therefore not a reasoning-role read-only command or implicit permission for reset, rebase, merge, stash or push.

### Focused Python validation and deliberate profiling

```powershell
# Current configuration: retain --no-cov until DT-02 is deployed.
uv run --locked pytest --no-cov <resolved-test-path> -q

# Deliberate baseline profiling, not the per-feature default.
uv run --locked pytest --no-cov --durations=30 --durations-min=0.1

# Comprehensive coverage at its designated gate.
uv run --locked pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The comprehensive command shown will still inherit HTML reporting until default addopts are changed. Do not pass a focused subset to this global-coverage command and interpret the result as whole-application qualification.

### Existing UI scripts

```powershell
Push-Location app/ui
# Install from the existing package lock when setup/lock state requires it.
npm ci
npm run test -- <resolved-test-path>
npm run typecheck
# Full UI validation/build only at the appropriate broader boundary.
npm run test
npm run build
Pop-Location
```

In automation, check and propagate each native process exit code; PowerShell does not make a failed native command halt a whole script automatically. A validator running npm from Python must resolve the platform-appropriate executable and use the UI working directory. Do not reinstall npm dependencies after every source edit.

### Proposed validation interface—implement before using

```powershell
uv run --locked python scripts/ci_check.py --profile integration --base origin/main --head HEAD --explain
uv run --locked python scripts/ci_check.py --profile affected --base origin/main --head HEAD
uv run --locked python scripts/ci_check.py --profile integration --base origin/main --head HEAD
uv run --locked python scripts/ci_check.py --profile full
```

These proposed flags do not exist in the inspected `ci_check.py`. Missing/unknown scope must fail or widen conservatively, never silently certify an empty test selection.

## 10. Exit criteria for the remediation

The remediation is successful when routine changes no longer perform whole-repository tests on every push; the same validation is not repeated solely for handoff; known administrative failures do not cause product replanning; the standard path does not perform fresh exploratory planning for a fully bound packet; and shared bookkeeping is generated from real evidence.

At the same time, a failing, unreviewed, unauthorized, stale or unqualified candidate must still be rejected. Representative features must show improved accepted throughput and honest usage measurements. Keeping the full scope means no feature is relabeled complete merely to meet a schedule.

There is no universal feature-time promise. After the pilot, forecast the remaining work by observed risk/complexity classes, dependency bottlenecks, effective concurrency and integration costs that do not overlap. Do not extrapolate from one 70-minute feature, from a three-worker theoretical maximum, or from generated line counts.

## 11. Implementation handoff

Use the following Task descriptions sequentially within the existing authorized workflow. These texts are work orders, not execution or remote-write approval. Do not combine them into one Task before an accepted workflow amendment permits such packaging:

> **DT-01:** Implement DT-01 of `docs/dev/HaruQuantAI_Development_Throughput_Remediation_Plan.md`. Preserve HaruQuantAI V3 architecture, active/user work, secret detection, reviewed-byte identity and product behavior. Reproduce and repair only the evidenced mechanical close-out failures, publish generated-output discovery before execution, and ensure legitimate schema-validated Git identities do not require per-feature shared secret-baseline edits. Run focused controller/Git/security regressions and report actual timings and rollback.

> **DT-02:** After DT-01 is accepted, implement DT-02A and DT-02B of `docs/dev/HaruQuantAI_Development_Throughput_Remediation_Plan.md` as one owner-authorized change set. Make ordinary pytest fast, retain explicit comprehensive coverage, add conservative validation profiles and straightforward UI/Python/workflow routing, measure the DT-02A checkpoint, then add candidate/dependency-aware routing with exact Git identities and fail-closed unknown scope.

> **DT-03:** After the combined DT-02 is accepted, implement the local integration-protection portion of DT-03 of `docs/dev/HaruQuantAI_Development_Throughput_Remediation_Plan.md` as a separate Task. Prove the replacement gate before relaxing broad pre-push hooks. Treat CI status, branch protection, publishing and remote acceptance as a separately authorized repository-administration step. Keep owner approvals, coverage, UI validation, provider-matrix evidence and stale-candidate rejection.

Proceed to B after the three Change Set A Tasks are accepted. Run the mandatory three-feature checkpoint after DT-06. C and the DT-09/DT-10 portions of D are incremental extensions, not prerequisites for collecting the first gains. DT-11 may proceed after that checkpoint to prioritize the strategy-ready outcome.

## 12. Sources and audit boundaries

### Supplied analysis

**[S1]** `Pasted markdown(8).md`, supplied in this conversation: original performance complaint and the three agent analyses. Agent 1 and Agent 2 report local inspection; Agent 3 reports remote inspection. Their quoted local timing and defect findings are preserved as reported evidence, not represented as newly measured here.

### Repository sources

All repository files below were read at commit `a32a46ad5c3407bdb7b68bf8dc270d327b6e7625`, except the live branch metadata check. Public citation base:

```text
https://github.com/haruperi/HaruQuantAI/blob/a32a46ad5c3407bdb7b68bf8dc270d327b6e7625/
```

| Reference | Repository path / relevant section |
|---|---|
| R1 | `.pre-commit-config.yaml`: pre-commit/pre-push stages, broad trigger regexes, secret baseline. |
| R2 | `pyproject.toml`: pytest defaults, branch coverage and 80% floor, mypy scope/cache, Python 3.14 and installed development dependencies. |
| R3 | `scripts/ci_check.py`: serial command list, unconditional workflow checks, nested uv invocation and elapsed timing. |
| R4 | `.github/workflows/ci.yml`: Windows runner, Python gates, separate provider-disable matrix, absence of npm checks. |
| R5 | `app/ui/package.json`: typecheck, Vitest, build and Playwright scripts. |
| R6 | `AGENTS.md`, §§1–2.7: authority, architectural boundaries, donor policy, task state machine, exact owner gates and role contracts. |
| R7 | `docs/dev/Phased_Feature_Implementation_Plan.md`, §§1–2.4: complete scope, sequencing, evidence, DOD-F and self-referential-hash avoidance. |
| R8 | `scripts/generate_phase0_evidence.py`, inspected opening/parsing section: existing deterministic generator and pinned source constants. |
| R9 | GitHub branch response for `main`, read 9 September 2026: baseline SHA; `protected: false`; required-check enforcement off. |

The `.agents/` directory listing confirmed existing controller/goal/integration infrastructure. Fetching a root `.gitattributes` at the baseline returned Not Found; the targeted attributes file is therefore a proposed addition. This was not a complete code or runtime audit. No production implementation, test suite, local ignored runtime log, or local performance experiment was executed here. Existing CI success/failure must be re-established during rollout; a historical failed run is not automatically today's failure.

### Official tool documentation checked

```text
[W1] pytest-cov configuration
https://pytest-cov.readthedocs.io/en/latest/config.html

[W2] pytest-xdist distribution modes
https://pytest-xdist.readthedocs.io/en/stable/distribution.html

[W3] GitHub required status checks and skip behavior
https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks

[W4] uv locking and syncing
https://docs.astral.sh/uv/concepts/projects/sync/

[W5] pytest invocation and duration reporting
https://docs.pytest.org/en/stable/how-to/usage.html

[W6] pre-commit stages and filename handling
https://pre-commit.com/
```

The recommendations, work-order identifiers, profiles, routing taxonomy, operating targets and rollout design are the proposed synthesis in this document, not claims that those interfaces already exist.
